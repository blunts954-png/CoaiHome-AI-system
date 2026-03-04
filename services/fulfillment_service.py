import os
import asyncio
import json
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from config.settings import settings
from models.database import SessionLocal, ShopifyOrder, VariantMap, OrderStatus, SystemLog
from api_clients.shopify_client import ShopifyClient
from api_clients.cj_dropshipping_client import get_cj_client


class FulfillmentService:
    """End-to-end fulfillment logic: Shopify -> CJ -> Shopify"""

    def __init__(self):
        self.cj = get_cj_client()
        self.shopify = ShopifyClient()

    async def process_new_order(self, shopify_payload: Dict) -> bool:
        """Entry point for a new paid order from Shopify"""
        order_id = str(shopify_payload.get("id"))
        order_name = str(shopify_payload.get("name", f"#{order_id}"))
        
        db = SessionLocal()
        try:
            # 1. Idempotently record order
            record = db.query(ShopifyOrder).filter(ShopifyOrder.shopify_order_id == order_id).first()
            if not record:
                record = ShopifyOrder(
                    shopify_order_id=order_id,
                    order_name=order_name,
                    customer_email=shopify_payload.get("email"),
                    total_price=float(shopify_payload.get("total_price", 0.0)),
                    currency=shopify_payload.get("currency", "USD"),
                    status=OrderStatus.RECEIVED
                )
                db.add(record)
                db.commit()
            
            if record.status not in (OrderStatus.RECEIVED, OrderStatus.FAILED):
                return True # Already in progress
            
            # 2. Build CJ Payload
            # We map Shopify variants to CJ variants before attempting fulfillment.
            cj_payload = await self._build_cj_payload(db, shopify_payload)
            if not cj_payload:
                record.status = OrderStatus.FAILED
                record.last_error = "Failed to map Shopify variants to CJ variants."
                db.commit()
                return False
            
            # 4. Create CJ Order
            if self.cj.shopify_mode:
                record.last_error = "CJ API not configured. Cannot fulfill orders."
                db.commit()
                return False

            # Risk check using centralized settings
            risk_max = settings.store.max_auto_fulfill_amount
            if record.total_price > risk_max:
                record.status = OrderStatus.ON_HOLD
                record.last_error = f"Order total ${record.total_price} exceeds auto-fulfill limit ${risk_max}"
                db.commit()
                return False

            resp = await self.cj.batch_create_order(cj_payload)
            if not resp.get("result"):
                record.status = OrderStatus.FAILED
                record.last_error = f"CJ Order Creation Failed: {resp.get('message')}"
                db.commit()
                return False
            
            # Extract CJ Order ID
            cj_order_id = None
            data = resp.get("data")
            if isinstance(data, list) and data:
                cj_order_id = data[0].get("orderId") or data[0].get("id")
            elif isinstance(data, dict):
                cj_order_id = data.get("orderId") or data.get("id")
            
            if not cj_order_id:
                record.status = OrderStatus.FAILED
                record.last_error = f"Could not extract CJ Order ID from response: {resp}"
                db.commit()
                return False
            
            record.cj_order_id = str(cj_order_id)
            record.status = OrderStatus.SENT_TO_CJ
            db.commit()

            # MARK: Ghost in the Machine Fix
            # We NO LONGER trigger a background task here.
            # fulfillment_worker.py handles periodic polling for SENT_TO_CJ orders.
            # This makes the system stateless and prevents race conditions after restarts.
            
            return True

        except Exception as e:
            record = db.query(ShopifyOrder).filter(ShopifyOrder.shopify_order_id == order_id).first()
            if record:
                record.status = OrderStatus.FAILED
                record.last_error = str(e)
            db.commit()
            return False
        finally:
            db.close()

    async def _build_cj_payload(self, db, shopify_order: Dict) -> Optional[Dict]:
        """Translate Shopify structure to CJ batchCreateOrder structure"""
        items = []
        for li in shopify_order.get("line_items", []):
            vid = str(li.get("variant_id"))
            qty = int(li.get("quantity", 1))
            
            # Find the mapping
            vm = db.query(VariantMap).filter(VariantMap.shopify_variant_id == vid).first()
            if not vm:
                print(f"   [!] Missing VariantMap for Shopify variant {vid}")
                return None # Fatal: missing mapping
            
            # Handle manual/AI-only products
            if vm.cj_variant_id == "MANUAL" or not vm.cj_variant_id:
                print(f"   [!] Variant {vid} is marked for MANUAL fulfillment. Skipping auto-order.")
                return None
            
            items.append({
                "variantId": vm.cj_variant_id,
                "quantity": qty
            })
        
        addr = shopify_order.get("shipping_address") or {}
        return {
            "orderNumber": str(shopify_order.get("name") or shopify_order["id"]),
            "shippingAddress": {
                "firstName": addr.get("first_name", ""),
                "lastName": addr.get("last_name", ""),
                "address1": addr.get("address1", ""),
                "address2": addr.get("address2", ""),
                "city": addr.get("city", ""),
                "province": addr.get("province", ""),
                "zip": addr.get("zip", ""),
                "country": addr.get("country", ""),
                "phone": addr.get("phone", "")
            },
            "products": items
        }

    async def poll_and_update_tracking(self, shopify_order_id: str):
        """Persistent polling loop for a specific order (up to 48h)"""
        for attempt in range(48):
            success = await self.check_order_tracking(shopify_order_id)
            if success:
                return
            await asyncio.sleep(3600)

    async def check_order_tracking(self, shopify_order_id: str) -> bool:
        """Perform a single check for tracking and update Shopify if found."""
        db = SessionLocal()
        try:
            record = db.query(ShopifyOrder).filter(ShopifyOrder.shopify_order_id == shopify_order_id).first()
            if not record or not record.cj_order_id:
                return False
            
            # Check CJ for tracking
            cj_details = await self.cj.get_order_details(record.cj_order_id)
            data = cj_details.get("data") or {}
            if isinstance(data, list) and data: data = data[0]

            tracking_no = data.get("trackingNumber") or data.get("trackingNo")
            logistics = data.get("logisticsCompany") or data.get("trackingCompany") or "Other"
            
            if tracking_no:
                record.tracking_number = tracking_no
                record.logistics_company = logistics
                db.commit()
                
                # Update Shopify via GraphQL
                success = await self._update_shopify_tracking_gql(shopify_order_id, tracking_no, logistics)
                if success:
                    record.status = OrderStatus.TRACKING_UPDATED
                    db.commit()
                    return True
            return False
        except Exception as e:
            print(f"Tracking check error for {shopify_order_id}: {e}")
            return False
        finally:
            db.close()

    async def _update_shopify_tracking_gql(self, shopify_order_id: str, tracking_number: str, company: str) -> bool:
        """
        Premium GraphQL update: Fulfill order and set tracking
        """
        try:
            # 1. Get Fulfillment Orders for this order
            query_fo = """
            query ($id: ID!) {
              order(id: $id) {
                fulfillmentOrders(first: 5, displayable: true) {
                  nodes { id status }
                }
              }
            }
            """
            oid = f"gid://shopify/Order/{shopify_order_id}"
            res = await self.shopify.gql(query_fo, {"id": oid})
            nodes = res.get("order", {}).get("fulfillmentOrders", {}).get("nodes", [])
            
            if not nodes:
                return False
            
            active_fo = next((n for n in nodes if n["status"] in ("OPEN", "IN_PROGRESS")), None)
            if not active_fo:
                return True # Maybe already fulfilled
            
            # 2. Create Fulfillment
            mutation = """
            mutation fulfillmentCreate($fulfillment: FulfillmentInput!) {
              fulfillmentCreate(fulfillment: $fulfillment) {
                fulfillment { id }
                userErrors { field message }
              }
            }
            """
            vars = {
                "fulfillment": {
                    "lineItemsByFulfillmentOrder": [
                        { "fulfillmentOrderId": active_fo["id"] }
                    ],
                    "trackingInfo": {
                        "number": tracking_number,
                        "company": company
                    },
                    "notifyCustomer": True
                }
            }
            
            res_mut = await self.shopify.gql(mutation, vars)
            errors = res_mut.get("fulfillmentCreate", {}).get("userErrors", [])
            if errors:
                print(f"Shopify Fulfillment Error: {errors}")
                return False
            
            return True
        except Exception as e:
            print(f"GraphQL update failed: {e}")
            return False

import os
