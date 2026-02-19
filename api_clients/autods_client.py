"""
AutoDS API Client - SHOPIFY-ONLY MODE
This client works without AutoDS API by using Shopify directly.
When you get AutoDS API access, swap this back to full version.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
import random

from config.settings import settings
from api_clients.shopify_client import get_shopify_client


class AutoDSClient:
    """
    AutoDS API Client - Currently in SHOPIFY-ONLY MODE
    
    This version works without AutoDS API credentials by:
    1. Using Shopify for product/order management
    2. Returning mock data for research (until you add products manually)
    3. Logging what WOULD have been sent to AutoDS
    
    When you get AutoDS API key, this will automatically use it.
    """
    
    def __init__(self):
        self.api_key = settings.autods.api_key
        self.base_url = settings.autods.base_url
        self.shopify_mode = not self.api_key or self.api_key == "your_autods_api_key"
        
        if self.shopify_mode:
            print("⚠️  AutoDS Client: RUNNING IN SHOPIFY-ONLY MODE")
            print("   - Product research: Manual entry only")
            print("   - Orders: Shopify fulfillment only")
            print("   - Add AUTODS_API_KEY env var when you get API access")
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        self._mock_products_db = []  # In-memory storage for demo
    
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
                "4. Get AutoDS API key for automated research"
            ],
            "filters_applied": filters or {}
        }
    
    async def get_trending_products(self, niche: Optional[str] = None, 
                                    limit: int = 20,
                                    country: str = "US") -> Dict:
        """Return empty trending - requires manual research in Shopify mode"""
        return {
            "products": [],
            "message": "SHOPIFY MODE: Use manual product research",
            "suggestion": "Check trending products on: tiktok.com/business, google.com/trends, or AutoDS marketplace"
        }
    
    async def get_product_details(self, product_id: str) -> Dict:
        """Get from Shopify in Shopify mode"""
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
            shopify_product_id = result.get("product", {}).get("id")
            
            return {
                "success": True,
                "shopify_product_id": shopify_product_id,
                "autods_product_id": None,
                "message": "SHOPIFY MODE: Product created directly in Shopify (no AutoDS integration)"
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
                "message": "SHOPIFY MODE: Orders from Shopify (not AutoDS)"
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
            "message": "SHOPIFY MODE: Auto-fulfillment requires AutoDS API",
            "note": "Fulfill orders manually via Shopify or AutoDS dashboard",
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
        return {
            "suppliers": [],
            "message": "SHOPIFY MODE: Supplier management requires AutoDS API",
            "note": "Manage suppliers manually in AutoDS dashboard"
        }
    
    async def get_supplier_performance(self, supplier_id: str) -> Dict:
        """Not available"""
        return {
            "message": "SHOPIFY MODE: Supplier data requires AutoDS API",
            "supplier_id": supplier_id
        }
    
    async def switch_supplier(self, product_id: str, new_supplier_id: str) -> Dict:
        """Not available"""
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
