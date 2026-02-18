"""
Phase 3.2 & 3.3: Inventory Sync and Order Fulfillment Monitoring
Tracks orders, handles exceptions, and monitors supplier performance
"""
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from api_clients.autods_client import get_autods_client
from api_clients.shopify_client import get_shopify_client
from services.ai_service import get_ai_service
from services.notification_service import get_notification_service
from config.settings import settings
from models.database import SessionLocal, Product, OrderException, SupplierPerformance, Store


class FulfillmentMonitor:
    """Monitors and manages order fulfillment and inventory"""
    
    def __init__(self):
        self.autods = get_autods_client()
        self.shopify = get_shopify_client()
        self.ai = get_ai_service()
        self.notifications = get_notification_service()
    
    async def run_inventory_sync(self, store_id: Optional[int] = None) -> Dict:
        """
        Sync inventory levels and detect issues
        """
        db = SessionLocal()
        
        query = db.query(Product).filter(Product.status == "active")
        if store_id:
            query = query.filter(Product.store_id == store_id)
        
        products = query.all()
        db.close()
        
        result = {
            "status": "started",
            "products_checked": len(products),
            "stock_updates": 0,
            "stockouts_detected": 0,
            "products_paused": 0,
            "errors": []
        }
        
        try:
            print(f"🔄 Syncing inventory for {len(products)} products...")
            
            for product in products:
                try:
                    if not product.autods_product_id:
                        continue
                    
                    # Get current inventory from AutoDS
                    inventory = await self.autods.get_inventory_status(
                        product.autods_product_id
                    )
                    
                    new_stock = inventory.get("available_quantity", 0)
                    old_stock = product.stock_quantity
                    
                    # Update if changed
                    if new_stock != old_stock:
                        product.stock_quantity = new_stock
                        product.last_synced_at = datetime.utcnow()
                        result["stock_updates"] += 1
                        
                        # Handle stockout
                        if new_stock == 0 and old_stock > 0:
                            result["stockouts_detected"] += 1
                            await self._handle_stockout(product)
                        
                        db = SessionLocal()
                        db.add(product)
                        db.commit()
                        db.close()
                
                except Exception as e:
                    result["errors"].append(f"Product {product.id}: {e}")
            
            result["status"] = "completed"
            print(f"✅ Inventory sync completed: {result['stock_updates']} updates, {result['stockouts_detected']} stockouts")
            
        except Exception as e:
            result["status"] = "failed"
            result["errors"].append(str(e))
        
        return result
    
    async def _handle_stockout(self, product: Product):
        """Handle a product stockout"""
        # Pause the product in Shopify
        try:
            if product.shopify_product_id:
                await self.shopify.update_product(
                    product.shopify_product_id,
                    {"published": False}
                )
            
            product.status = "out_of_stock"
            
            # Log exception
            db = SessionLocal()
            exception = OrderException(
                store_id=product.store_id,
                exception_type="stock_out",
                error_message=f"Product {product.title} is out of stock",
                status="open"
            )
            db.add(exception)
            db.commit()
            db.close()
            
        except Exception as e:
            print(f"Failed to handle stockout for product {product.id}: {e}")
    
    async def check_fulfillment_exceptions(self) -> Dict:
        """
        Check for orders that failed auto-fulfillment
        """
        db = SessionLocal()
        
        try:
            # Get recent orders from AutoDS
            recent_orders = await self.autods.get_orders(
                status="pending",
                limit=100
            )
            
            result = {
                "status": "completed",
                "orders_checked": len(recent_orders.get("orders", [])),
                "exceptions_found": 0,
                "auto_resolved": 0
            }
            
            for order in recent_orders.get("orders", []):
                order_id = order.get("id")
                shopify_order_id = order.get("shopify_order_id")
                
                # Check if this order has issues
                if order.get("fulfillment_status") == "failed":
                    # Check if already logged
                    existing = db.query(OrderException).filter(
                        OrderException.shopify_order_id == shopify_order_id
                    ).first()
                    
                    if not existing:
                        exception = OrderException(
                            store_id=order.get("store_id"),
                            shopify_order_id=shopify_order_id,
                            autods_order_id=order_id,
                            exception_type=order.get("failure_reason", "unknown"),
                            error_message=order.get("error_message", ""),
                            customer_email=order.get("customer_email"),
                            total_amount=order.get("total_price"),
                            product_ids=order.get("line_items", []),
                            status="open"
                        )
                        db.add(exception)
                        result["exceptions_found"] += 1
                        
                        # Try to auto-resolve
                        resolved = await self._attempt_auto_resolve(exception)
                        if resolved:
                            exception.status = "resolved"
                            result["auto_resolved"] += 1
            
            db.commit()
            
            # Send notification if there are exceptions
            if result["exceptions_found"] > 0:
                await self.notifications.send_exception_summary(
                    result["exceptions_found"],
                    result["auto_resolved"]
                )
            
            return result
            
        except Exception as e:
            return {"status": "failed", "error": str(e)}
        finally:
            db.close()
    
    async def _attempt_auto_resolve(self, exception: OrderException) -> bool:
        """Try to automatically resolve a fulfillment exception"""
        # Simple resolution strategies:
        
        # 1. If payment failed, retry with different payment method (if configured)
        if exception.exception_type == "payment_failed":
            # Would integrate with AutoDS to retry
            return False  # Requires manual intervention
        
        # 2. If stock issue, check for alternative supplier
        if exception.exception_type == "stock_out":
            # Would try to switch supplier
            return False
        
        # 3. If address issue, flag for customer contact
        if exception.exception_type == "invalid_address":
            return False
        
        return False
    
    async def update_supplier_performance(self) -> Dict:
        """
        Analyze and update supplier performance metrics
        """
        db = SessionLocal()
        
        try:
            # Get all suppliers
            suppliers = await self.autods.list_suppliers()
            
            result = {
                "status": "completed",
                "suppliers_analyzed": 0,
                "recommendations": []
            }
            
            for supplier in suppliers.get("suppliers", []):
                supplier_id = supplier.get("id")
                
                # Get performance data
                perf_data = await self.autods.get_supplier_performance(supplier_id)
                
                # Update or create performance record
                perf_record = db.query(SupplierPerformance).filter(
                    SupplierPerformance.supplier_id == supplier_id
                ).first()
                
                if not perf_record:
                    perf_record = SupplierPerformance(
                        supplier_id=supplier_id,
                        supplier_name=supplier.get("name")
                    )
                    db.add(perf_record)
                
                # Update metrics
                perf_record.total_orders = perf_data.get("total_orders", 0)
                perf_record.successful_fulfillments = perf_data.get("successful", 0)
                perf_record.failed_fulfillments = perf_data.get("failed", 0)
                perf_record.avg_fulfillment_days = perf_data.get("avg_fulfillment_days", 0)
                perf_record.refund_rate = perf_data.get("refund_rate", 0)
                perf_record.stockout_count = perf_data.get("stockout_count", 0)
                
                # Calculate reliability score
                total = perf_record.total_orders
                if total > 0:
                    success_rate = perf_record.successful_fulfillments / total
                    perf_record.reliability_score = (
                        success_rate * 0.4 +
                        (1 - perf_record.refund_rate) * 0.3 +
                        (1 - min(perf_record.avg_fulfillment_days / 30, 1)) * 0.3
                    ) * 100
                
                # AI analysis for recommendation
                ai_analysis = await self.ai.analyze_supplier_risk({
                    "supplier_id": supplier_id,
                    "name": supplier.get("name"),
                    "metrics": {
                        "total_orders": perf_record.total_orders,
                        "success_rate": perf_record.successful_fulfillments / max(perf_record.total_orders, 1),
                        "refund_rate": perf_record.refund_rate,
                        "avg_fulfillment_days": perf_record.avg_fulfillment_days,
                        "reliability_score": perf_record.reliability_score
                    }
                })
                
                perf_record.ai_recommendation = ai_analysis.get("recommendation", "monitor")
                perf_record.last_updated = datetime.utcnow()
                
                result["suppliers_analyzed"] += 1
                
                if perf_record.ai_recommendation in ["replace", "monitor"]:
                    result["recommendations"].append({
                        "supplier_id": supplier_id,
                        "name": supplier.get("name"),
                        "recommendation": perf_record.ai_recommendation,
                        "score": perf_record.reliability_score
                    })
            
            db.commit()
            
            # Send notification about concerning suppliers
            concerning = [r for r in result["recommendations"] if r["recommendation"] == "replace"]
            if concerning:
                await self.notifications.send_supplier_alert(concerning)
            
            return result
            
        except Exception as e:
            return {"status": "failed", "error": str(e)}
        finally:
            db.close()
    
    async def resolve_exception(self, exception_id: int, 
                                resolution: str,
                                resolved_by: str) -> Dict:
        """Manually resolve a fulfillment exception"""
        db = SessionLocal()
        
        try:
            exception = db.query(OrderException).filter(
                OrderException.id == exception_id
            ).first()
            
            if not exception:
                return {"status": "error", "message": "Exception not found"}
            
            exception.status = "resolved"
            exception.resolution_notes = resolution
            exception.resolved_by = resolved_by
            exception.resolved_at = datetime.utcnow()
            
            db.commit()
            
            return {"status": "success", "exception_id": exception_id}
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
        finally:
            db.close()
    
    async def get_exception_queue(self, status: str = "open") -> List[Dict]:
        """Get the current exception queue for dashboard"""
        db = SessionLocal()
        
        exceptions = db.query(OrderException).filter(
            OrderException.status == status
        ).order_by(OrderException.created_at.desc()).all()
        
        result = []
        for ex in exceptions:
            result.append({
                "id": ex.id,
                "shopify_order_id": ex.shopify_order_id,
                "exception_type": ex.exception_type,
                "error_message": ex.error_message,
                "customer_email": ex.customer_email,
                "total_amount": ex.total_amount,
                "created_at": ex.created_at.isoformat()
            })
        
        db.close()
        return result


# Dummy notification service for now (to be implemented)
class NotificationService:
    async def send_exception_summary(self, total: int, resolved: int):
        print(f"📧 Exception summary: {total} found, {resolved} auto-resolved")
    
    async def send_supplier_alert(self, concerning_suppliers: List[Dict]):
        print(f"📧 Supplier alerts: {len(concerning_suppliers)} concerning suppliers")


def get_fulfillment_monitor() -> FulfillmentMonitor:
    return FulfillmentMonitor()
