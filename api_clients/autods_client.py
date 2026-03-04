"""
Supplier client compatibility layer.
Supports AutoDS (legacy mode), CJ Dropshipping, and Shopify-only fallback.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
import random
import httpx

from config.settings import settings
from api_clients.shopify_client import get_shopify_client
from automation.utils import parse_cj_credentials


class AutoDSClient:
    """
    CJ Dropshipping client (formerly AutoDS client).
    Uses CJ API for product research, import, and order fulfillment.
    SYSTEM_SUPPLIER_PLATFORM=cj (default) - uses CJ API
    """

    def __init__(self):
        self.provider_preference = (settings.system.supplier_platform or "cj").lower()
        self.autods_api_key = settings.autods.api_key  # Kept for backward compatibility
        
        # Use shared utility for CJ credential parsing
        cj_parsed = parse_cj_credentials(
            cj_token=settings.cj.api_token,
            cj_email=settings.cj.api_email,
            cj_key=settings.cj.api_key
        )
        self.cj_api_token = settings.cj.api_token
        self.cj_api_email = cj_parsed["email"]
        self.cj_api_key = cj_parsed["api_key"]
        
        self.cj_base_url = settings.cj.base_url.rstrip("/")
        self.base_url = settings.autods.base_url

        if self.provider_preference == "cj":
            self.provider = "cj"
        # Default to CJ if no valid credentials
        if self.provider_preference == "cj" or not cj_parsed["is_valid"]:
            self.provider = "cj"
        else:
            self.provider = "cj"  # CJ is the only supported provider now

        self.api_key = self.autods_api_key
        
        # Determine if we're in Shopify-only mode (no supplier API)
        self.shopify_mode = (
            not cj_parsed["is_valid"]
        )
        
        if self.provider == "cj" and not self.shopify_mode:
            print("Supplier Client: RUNNING IN CJ MODE")
            print("   - Product research: CJ API")
            print("   - Product import: Shopify direct")
            print("   - Supplier source: CJ Dropshipping")
        elif self.provider == "cj" and self.shopify_mode:
            print("Supplier Client: CJ selected but CJ credentials are missing or invalid")
            print("   - Falling back to SHOPIFY-ONLY MODE")
            print("   - Add valid CJ_API_TOKEN (email@api@key) or CJ_API_EMAIL + CJ_API_KEY")
        elif self.shopify_mode:
            print("AutoDS Client: RUNNING IN SHOPIFY-ONLY MODE")
            print("   - Product research: Manual entry only")
            print("   - Orders: Shopify fulfillment only")
            print("   - Add AUTODS_API_KEY env var when you get API access")
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        self.cj_headers = {
            "CJ-Access-Token": self.cj_api_token,
            "Content-Type": "application/json"
        }
        self._mock_products_db = []  # In-memory storage for demo

    async def _cj_request(self, method: str, endpoint: str,
                          params: Optional[Dict[str, Any]] = None,
                          payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Call CJ API and normalize error handling."""
        # Use the CJ client for proper authentication
        from api_clients.cj_dropshipping_client import get_cj_client
        cj_client = get_cj_client()
        
        if cj_client.shopify_mode:
            raise ValueError("CJ API credentials not configured")

        return await cj_client._make_request(
            method=method.upper(),
            endpoint=endpoint,
            params=params,
            json=payload
        )

    def _cj_extract_items(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract list payload from CJ responses with varying schemas."""
        if not isinstance(response, dict):
            return []
        data = response.get("data")
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            for key in ("list", "items", "records", "content", "productList"):
                if isinstance(data.get(key), list):
                    return data.get(key, [])
        for key in ("list", "items", "records", "content"):
            if isinstance(response.get(key), list):
                return response.get(key, [])
        return []

    def _to_float(self, value: Any, default: float = 0.0) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    def _normalize_cj_product(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """Map CJ product schema to the internal product schema used by automation."""
        product_id = (
            product.get("pid")
            or product.get("productId")
            or product.get("id")
            or product.get("vid")
            or ""
        )
        title = (
            product.get("productNameEn")
            or product.get("nameEn")
            or product.get("productName")
            or product.get("productNameCn")
            or "CJ Product"
        )
        cost_price = self._to_float(
            product.get("sellPrice")
            or product.get("price")
            or product.get("variantSellPrice")
            or product.get("variantPrice"),
            0.0
        )
        supplier_rating = self._to_float(product.get("score") or product.get("supplierScore"), 4.5)
        shipping_days = int(self._to_float(product.get("deliveryTime") or product.get("shippingDays"), 10))
        images = []
        for key in ("productImage", "image", "images"):
            value = product.get(key)
            if isinstance(value, list):
                images = [str(v) for v in value if v]
                break
            if isinstance(value, str) and value:
                images = [value]
                break

        # Try to get variants or a single variant ID
        variants = product.get("variants") or []
        first_vid = product.get("vid") or (variants[0].get("vid") if variants else "")

        return {
            "id": product_id,
            "vid": first_vid,
            "source_url": f"https://www.cjdropshipping.com/product/{product_id}.html" if product_id else "",
            "title": title,
            "description": product.get("description") or product.get("productDescription") or "",
            "cost_price": cost_price,
            "supplier_id": "cj",
            "supplier_name": "CJ Dropshipping",
            "supplier_rating": supplier_rating,
            "shipping_days": shipping_days,
            "images": images,
            "variants": variants
        }
    
    # ============ AI Store Builder (SHOPIFY MODE) ============
    
    async def create_ai_store(self, store_spec: Dict) -> Dict:
        """In Shopify mode: Create store structure via Shopify"""
        if not self.shopify_mode:
            # Would call real AutoDS API here
            pass
        
        # Shopify-only mode: Return mock job, actual store created via Shopify OAuth
        return {
            "job_id": f"mock_{datetime.utcnow().timestamp()}",
            "status": "completed",
            "message": "SHOPIFY MODE: Store created via Shopify. AutoDS features require API key.",
            "store_data": {
                "shopify_domain": settings.shopify.shop_url,
                "shopify_store_id": "manual_setup_required"
            }
        }
    
    async def get_store_builder_status(self, job_id: str) -> Dict:
        """Return completed status for Shopify mode"""
        return {
            "status": "completed",
            "store_data": {
                "shopify_domain": settings.shopify.shop_url,
                "shopify_store_id": "manual_setup"
            }
        }
    
    # ============ Product Research (MANUAL/SHOPIFY MODE) ============
    
    async def search_products(self, query: str, filters: Optional[Dict] = None) -> Dict:
        """
        In Shopify mode: Search your existing Shopify products
        or return instructions for manual research
        """
        if self.provider == "cj" and not self.shopify_mode:
            filters = filters or {}
            limit = int(filters.get("limit", 20))
            page = int(filters.get("page", 1))

            try:
                # CJ endpoint docs: product/listV2
                response = await self._cj_request(
                    "GET",
                    "product/listV2",
                    params={
                        "pageNum": page,
                        "pageSize": max(1, min(limit, 100)),
                        "categoryName": query or "",
                        "productNameEn": query or ""
                    }
                )
                products = [self._normalize_cj_product(p) for p in self._cj_extract_items(response)]
                if query:
                    q = query.lower().strip()
                    products = [p for p in products if q in p.get("title", "").lower()]

                return {
                    "products": products[:limit],
                    "filters_applied": filters,
                    "source": "cj",
                    "message": f"Found {len(products[:limit])} products from CJ"
                }
            except Exception as e:
                return {
                    "products": [],
                    "error": str(e),
                    "source": "cj",
                    "message": "CJ search failed. Verify CJ_API_TOKEN and CJ_BASE_URL."
                }

        if not self.shopify_mode:
            pass  # Would call real API
        
        # Return helpful message + empty results
        return {
            "products": [],
            "message": "SHOPIFY MODE: Manual product research required",
            "instructions": [
                "1. Find products on AliExpress, CJ Dropshipping, etc.",
                "2. Add them manually via /api/products/manual-add",
                "3. Or import via Shopify admin",
                "4. Set SYSTEM_SUPPLIER_PLATFORM=cj and add CJ_API_TOKEN (or use AutoDS API)"
            ],
            "filters_applied": filters or {}
        }
    
    async def get_trending_products(self, niche: Optional[str] = None, 
                                    limit: int = 20,
                                    country: str = "US") -> Dict:
        """Return empty trending - requires manual research in Shopify mode"""
        if self.provider == "cj" and not self.shopify_mode:
            filters = {"limit": limit, "country": country}
            return await self.search_products(niche or "", filters=filters)

        return {
            "products": [],
            "message": "SHOPIFY MODE: Use manual product research",
            "suggestion": "Check trending products on: tiktok.com/business, google.com/trends, or AutoDS marketplace"
        }
    
    async def get_product_details(self, product_id: str) -> Dict:
        """Get from Shopify in Shopify mode"""
        if self.provider == "cj" and not self.shopify_mode:
            try:
                response = await self._cj_request("GET", "product/query", params={"pid": product_id})
                data = response.get("data", response)
                if isinstance(data, list):
                    data = data[0] if data else {}
                if not isinstance(data, dict):
                    data = {}
                normalized = self._normalize_cj_product(data)
                normalized["source"] = "cj"
                return normalized
            except Exception as e:
                return {"error": str(e), "message": "Product not found in CJ"}

        try:
            shopify = get_shopify_client()
            product = await shopify.get_product(product_id)
            return {
                "id": product_id,
                "title": product.get("product", {}).get("title"),
                "source": "shopify",
                "message": "SHOPIFY MODE: Using Shopify product data"
            }
        except Exception as e:
            return {"error": str(e), "message": "Product not found in Shopify"}
    
    async def analyze_product_potential(self, product_url: str) -> Dict:
        """Can't analyze without AutoDS API - return message"""
        return {
            "message": "SHOPIFY MODE: Manual analysis required",
            "url": product_url,
            "suggestion": "Use AutoDS Chrome extension or get API key for automated analysis"
        }
    
    # ============ Product Import (SHOPIFY MODE = Direct to Shopify) ============
    
    async def import_product(self, product_data: Dict, shopify_store_id: str) -> Dict:
        """
        In Shopify mode: Create product directly in Shopify
        """
        try:
            shopify = get_shopify_client()
            
            # Build Shopify product payload
            shopify_product = {
                "title": product_data.get("title", "New Product"),
                "body_html": product_data.get("description", ""),
                "vendor": product_data.get("supplier_name", "My Store"),
                "product_type": product_data.get("category", ""),
                "tags": product_data.get("tags", []),
                "variants": [{
                    "price": str(product_data.get("suggested_price", 29.99)),
                    "inventory_quantity": 100,
                    "requires_shipping": True
                }],
                "images": [
                    {"src": url} for url in product_data.get("image_urls", [])
                ]
            }
            
            result = await shopify.create_product(shopify_product)
            shopify_product_rec = result.get("product", {})
            shopify_product_id = shopify_product_rec.get("id")
            shopify_variants = shopify_product_rec.get("variants", [])
            shopify_variant_id = shopify_variants[0].get("id") if shopify_variants else None
            
            supplier_product_id = product_data.get("source_id") or product_data.get("supplier_product_id")
            supplier_variant_id = product_data.get("source_vid") or product_data.get("vid")
            
            return {
                "success": True,
                "shopify_product_id": shopify_product_id,
                "shopify_variant_id": shopify_variant_id,
                "supplier_variant_id": supplier_variant_id,
                # Keep this field for compatibility with existing DB columns/workflows
                "autods_product_id": supplier_product_id or shopify_product_id,
                "message": (
                    "CJ MODE: Product created in Shopify from CJ source"
                    if self.provider == "cj"
                    else "SHOPIFY MODE: Product created directly in Shopify (no AutoDS integration)"
                )
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to create product in Shopify"
            }
    
    async def bulk_import_products(self, products: List[Dict], 
                                   shopify_store_id: str) -> Dict:
        """Import to Shopify one by one"""
        results = []
        for product in products:
            result = await self.import_product(product, shopify_store_id)
            results.append(result)
        
        successful = sum(1 for r in results if r.get("success"))
        return {
            "total": len(products),
            "successful": successful,
            "failed": len(products) - successful,
            "results": results,
            "message": "SHOPIFY MODE: Products imported directly to Shopify"
        }
    
    async def get_import_status(self, import_job_id: str) -> Dict:
        """Return completed for Shopify mode"""
        return {"status": "completed", "message": "SHOPIFY MODE: Import completed"}
    
    # ============ Pricing & Inventory (SHOPIFY MODE) ============
    
    async def update_pricing_rules(self, product_ids: List[str], 
                                   rules: Dict) -> Dict:
        """Log what would be updated - actual updates happen via pricing engine"""
        return {
            "message": "SHOPIFY MODE: Pricing rules logged only",
            "note": "Use pricing engine to update Shopify prices directly",
            "products": len(product_ids),
            "rules": rules
        }
    
    async def get_pricing_suggestions(self, product_ids: Optional[List[str]] = None,
                                      niche: Optional[str] = None) -> Dict:
        """Return message - AI pricing done via pricing engine"""
        return {
            "message": "SHOPIFY MODE: Use /api/pricing/optimize endpoint",
            "suggestion": "AI pricing optimization is available via the pricing engine"
        }
    
    async def apply_price_changes(self, price_changes: List[Dict]) -> Dict:
        """Apply directly to Shopify"""
        try:
            shopify = get_shopify_client()
            applied = []
            
            for change in price_changes:
                # Get product to find variant
                product_id = change.get("product_id")
                new_price = change.get("new_price")
                
                # Update in Shopify (requires variant ID - simplified here)
                # In practice, you'd look up the variant first
                applied.append({
                    "product_id": product_id,
                    "new_price": new_price,
                    "status": "logged"
                })
            
            return {
                "applied": len(applied),
                "changes": applied,
                "message": "SHOPIFY MODE: Price changes logged (use pricing engine for actual updates)"
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    async def sync_inventory(self, product_ids: Optional[List[str]] = None) -> Dict:
        """Sync from Shopify"""
        return {
            "message": "SHOPIFY MODE: Use /api/inventory/sync endpoint",
            "note": "Inventory sync is handled via fulfillment monitor using Shopify data"
        }
    
    async def get_inventory_status(self, product_id: str) -> Dict:
        """Get from Shopify"""
        try:
            shopify = get_shopify_client()
            product = await shopify.get_product(product_id)
            variants = product.get("product", {}).get("variants", [])
            
            if variants:
                return {
                    "product_id": product_id,
                    "available_quantity": variants[0].get("inventory_quantity", 0),
                    "source": "shopify"
                }
            return {"available_quantity": 0}
            
        except Exception as e:
            return {"error": str(e), "available_quantity": 0}
    
    # ============ Order Fulfillment (SHOPIFY MODE) ============
    
    async def get_orders(self, status: Optional[str] = None,
                        limit: int = 50,
                        page: int = 1) -> Dict:
        """Get from Shopify"""
        try:
            shopify = get_shopify_client()
            result = await shopify.list_orders(status=status or "any", limit=limit)
            
            # Transform to AutoDS-like format
            shopify_orders = result.get("orders", [])
            transformed = []
            
            for order in shopify_orders:
                transformed.append({
                    "id": order.get("id"),
                    "shopify_order_id": order.get("id"),
                    "status": order.get("financial_status", "unknown"),
                    "fulfillment_status": order.get("fulfillment_status", "unfulfilled"),
                    "total_price": order.get("total_price"),
                    "customer_email": order.get("customer", {}).get("email"),
                    "created_at": order.get("created_at"),
                    "line_items": order.get("line_items", [])
                })
            
            return {
                "orders": transformed,
                "message": (
                    "CJ MODE: Orders from Shopify (use CJ dashboard/API for supplier-side status)"
                    if self.provider == "cj"
                    else "SHOPIFY MODE: Orders from Shopify (not AutoDS)"
                )
            }
            
        except Exception as e:
            return {"orders": [], "error": str(e)}
    
    async def get_order_details(self, order_id: str) -> Dict:
        """Get from Shopify"""
        try:
            shopify = get_shopify_client()
            result = await shopify.get_order(order_id)
            order = result.get("order", {})
            
            return {
                "id": order_id,
                "shopify_order_id": order_id,
                "status": order.get("financial_status"),
                "fulfillment_status": order.get("fulfillment_status"),
                "total_price": order.get("total_price"),
                "customer": order.get("customer", {}),
                "line_items": order.get("line_items", []),
                "source": "shopify"
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    async def enable_auto_fulfillment(self, store_id: str, enabled: bool = True) -> Dict:
        """Not available in Shopify mode"""
        return {
            "message": (
                "CJ MODE: Use CJ API/dashboard for supplier fulfillment configuration"
                if self.provider == "cj"
                else "SHOPIFY MODE: Auto-fulfillment requires AutoDS API"
            ),
            "note": "Fulfill orders manually via Shopify or supplier dashboard",
            "enabled": False
        }
    
    async def fulfill_order(self, order_id: str, fulfillment_data: Optional[Dict] = None) -> Dict:
        """Create fulfillment in Shopify"""
        try:
            shopify = get_shopify_client()
            
            fulfillment = {
                "location_id": fulfillment_data.get("location_id") if fulfillment_data else None,
                "tracking_number": fulfillment_data.get("tracking_number") if fulfillment_data else None,
                "tracking_company": fulfillment_data.get("carrier") if fulfillment_data else None
            }
            
            result = await shopify.create_fulfillment(order_id, fulfillment)
            return {
                "success": True,
                "fulfillment": result,
                "message": "SHOPIFY MODE: Fulfillment created in Shopify"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_tracking_info(self, order_id: str) -> Dict:
        """Get from Shopify fulfillments"""
        try:
            shopify = get_shopify_client()
            result = await shopify.get_order_fulfillments(order_id)
            fulfillments = result.get("fulfillments", [])
            
            if fulfillments:
                tracking = fulfillments[0].get("tracking_numbers", [])
                return {
                    "order_id": order_id,
                    "tracking_numbers": tracking,
                    "source": "shopify"
                }
            
            return {"tracking_numbers": [], "message": "No tracking found"}
            
        except Exception as e:
            return {"error": str(e)}
    
    async def update_tracking(self, order_id: str, tracking_number: str, 
                             carrier: str) -> Dict:
        """Update in Shopify"""
        return {
            "message": "SHOPIFY MODE: Update tracking via Shopify admin or fulfillment endpoint",
            "note": "Use Shopify's fulfillment update API"
        }
    
    # ============ Supplier Management (NOT AVAILABLE) ============
    
    async def list_suppliers(self) -> Dict:
        """Not available without AutoDS API"""
        if self.provider == "cj":
            return {
                "suppliers": [{"id": "cj", "name": "CJ Dropshipping"}],
                "message": "CJ provider active"
            }
        return {
            "suppliers": [],
            "message": "SHOPIFY MODE: Supplier management requires AutoDS API",
            "note": "Manage suppliers manually in AutoDS dashboard"
        }
    
    async def get_supplier_performance(self, supplier_id: str) -> Dict:
        """Not available"""
        if self.provider == "cj":
            return {
                "supplier_id": supplier_id,
                "total_orders": 0,
                "successful": 0,
                "failed": 0,
                "avg_fulfillment_days": 0,
                "refund_rate": 0,
                "stockout_count": 0,
                "message": "CJ supplier performance placeholder (connect detailed CJ analytics as needed)"
            }
        return {
            "message": "SHOPIFY MODE: Supplier data requires AutoDS API",
            "supplier_id": supplier_id
        }
    
    async def switch_supplier(self, product_id: str, new_supplier_id: str) -> Dict:
        """Not available"""
        if self.provider == "cj":
            return {
                "message": "CJ MODE: Supplier switching should be done in CJ dashboard or via CJ product mapping APIs",
                "product_id": product_id,
                "new_supplier_id": new_supplier_id
            }
        return {
            "message": "SHOPIFY MODE: Supplier switching requires AutoDS API",
            "note": "Switch suppliers in AutoDS dashboard"
        }
    
    # ============ Analytics (SHOPIFY MODE = Limited) ============
    
    async def get_dashboard_stats(self, store_id: str, 
                                  start_date: Optional[str] = None,
                                  end_date: Optional[str] = None) -> Dict:
        """Get from Shopify orders"""
        try:
            shopify = get_shopify_client()
            
            # Get order counts
            orders_result = await shopify.list_orders(limit=250)
            orders = orders_result.get("orders", [])
            
            total_revenue = sum(
                float(o.get("total_price", 0)) for o in orders
            )
            
            return {
                "total_orders": len(orders),
                "total_revenue": total_revenue,
                "source": "shopify",
                "message": "SHOPIFY MODE: Basic stats from Shopify orders"
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    async def get_product_performance(self, product_id: str,
                                     days: int = 30) -> Dict:
        """Not available in Shopify mode without analytics"""
        return {
            "message": "SHOPIFY MODE: Product analytics require AutoDS or Shopify Plus",
            "product_id": product_id,
            "suggestion": "Track performance manually or upgrade to Shopify Plus for analytics"
        }
    
    async def get_profit_loss(self, store_id: str, 
                             period: str = "month") -> Dict:
        """Not available without cost data"""
        return {
            "message": "SHOPIFY MODE: P&L requires cost data from AutoDS",
            "note": "Track costs manually or use AutoDS dashboard for true P&L"
        }


# Singleton instance
_autods_client: Optional[AutoDSClient] = None


def get_autods_client() -> AutoDSClient:
    """Get or create AutoDS client singleton"""
    global _autods_client
    if _autods_client is None:
        _autods_client = AutoDSClient()
    return _autods_client
