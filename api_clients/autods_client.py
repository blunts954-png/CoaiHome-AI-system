"""
AutoDS API Client
Handles all interactions with AutoDS for product research, import, pricing, and fulfillment.
"""
import httpx
from typing import Optional, List, Dict, Any
from datetime import datetime
import json

from config.settings import settings


class AutoDSClient:
    """AutoDS API Client"""
    
    def __init__(self):
        self.api_key = settings.autods.api_key
        self.base_url = settings.autods.base_url
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    async def _request(self, method: str, endpoint: str, 
                      data: Optional[Dict] = None,
                      params: Optional[Dict] = None) -> Dict:
        """Make an authenticated request to AutoDS API"""
        url = f"{self.base_url}/{endpoint}"
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method,
                url=url,
                headers=self.headers,
                json=data,
                params=params,
                timeout=60.0
            )
            response.raise_for_status()
            return response.json()
    
    # ============ AI Store Builder ============
    
    async def create_ai_store(self, store_spec: Dict) -> Dict:
        """
        Trigger AutoDS AI Store Builder
        
        Args:
            store_spec: {
                "niche": str,
                "brand_name": str,
                "target_country": str,
                "brand_tone": str,
                "primary_color": str,
                "secondary_color": str,
                "price_range": {"min": float, "max": float},
                "shipping_preference": str
            }
        """
        payload = {
            "store_builder_request": {
                "niche": store_spec.get("niche"),
                "brand_name": store_spec.get("brand_name"),
                "target_country": store_spec.get("target_country", "US"),
                "brand_tone": store_spec.get("brand_tone", "professional"),
                "primary_color": store_spec.get("primary_color", "#000000"),
                "secondary_color": store_spec.get("secondary_color", "#ffffff"),
                "min_price": store_spec.get("price_range", {}).get("min", 15),
                "max_price": store_spec.get("price_range", {}).get("max", 500),
                "shipping_preference": store_spec.get("shipping_preference", "standard"),
                "auto_import_products": True,
                "num_products": store_spec.get("num_products", 10)
            }
        }
        return await self._request("POST", "api/v1/ai-store-builder/create", payload)
    
    async def get_store_builder_status(self, job_id: str) -> Dict:
        """Check status of AI store builder job"""
        return await self._request("GET", f"api/v1/ai-store-builder/status/{job_id}")
    
    # ============ Product Research ============
    
    async def search_products(self, query: str, filters: Optional[Dict] = None) -> Dict:
        """
        Search for products using AutoDS product research
        
        Args:
            query: Search query or niche
            filters: {
                "min_margin": float,
                "max_shipping_days": int,
                "min_rating": float,
                "supplier": str,
                "min_price": float,
                "max_price": float
            }
        """
        payload = {
            "search": {
                "query": query,
                "filters": filters or {}
            }
        }
        return await self._request("POST", "api/v1/product-research/search", payload)
    
    async def get_trending_products(self, niche: Optional[str] = None, 
                                    limit: int = 20,
                                    country: str = "US") -> Dict:
        """Get trending products from AutoDS marketplace"""
        params = {
            "limit": limit,
            "country": country
        }
        if niche:
            params["niche"] = niche
        return await self._request("GET", "api/v1/product-research/trending", params=params)
    
    async def get_product_details(self, product_id: str) -> Dict:
        """Get detailed product information"""
        return await self._request("GET", f"api/v1/product-research/products/{product_id}")
    
    async def analyze_product_potential(self, product_url: str) -> Dict:
        """Analyze a product's potential using AI"""
        payload = {"url": product_url}
        return await self._request("POST", "api/v1/product-research/analyze", payload)
    
    # ============ Product Import ============
    
    async def import_product(self, product_data: Dict, shopify_store_id: str) -> Dict:
        """
        Import a product to Shopify via AutoDS
        
        Args:
            product_data: Product information from research
            shopify_store_id: Target Shopify store
        """
        payload = {
            "import": {
                "source_product_id": product_data.get("source_id"),
                "source_url": product_data.get("source_url"),
                "shopify_store_id": shopify_store_id,
                "title": product_data.get("title"),
                "description": product_data.get("description"),
                "price_markup": product_data.get("markup", 2.5),
                "min_margin_percent": product_data.get("min_margin", 30),
                "tags": product_data.get("tags", []),
                "collections": product_data.get("collections", [])
            }
        }
        return await self._request("POST", "api/v1/products/import", payload)
    
    async def bulk_import_products(self, products: List[Dict], 
                                   shopify_store_id: str) -> Dict:
        """Import multiple products at once"""
        payload = {
            "bulk_import": {
                "shopify_store_id": shopify_store_id,
                "products": products,
                "auto_optimize": True
            }
        }
        return await self._request("POST", "api/v1/products/bulk-import", payload)
    
    async def get_import_status(self, import_job_id: str) -> Dict:
        """Check status of product import job"""
        return await self._request("GET", f"api/v1/products/import-status/{import_job_id}")
    
    # ============ Pricing & Inventory ============
    
    async def update_pricing_rules(self, product_ids: List[str], 
                                   rules: Dict) -> Dict:
        """
        Update pricing rules for products
        
        Args:
            rules: {
                "markup_multiplier": float,
                "min_margin_percent": float,
                "rounding": float,
                "min_price": float,
                "max_price": float
            }
        """
        payload = {
            "pricing_rules": {
                "product_ids": product_ids,
                "rules": rules
            }
        }
        return await self._request("POST", "api/v1/pricing/update-rules", payload)
    
    async def get_pricing_suggestions(self, product_ids: Optional[List[str]] = None,
                                      niche: Optional[str] = None) -> Dict:
        """Get AI pricing optimization suggestions"""
        payload = {}
        if product_ids:
            payload["product_ids"] = product_ids
        if niche:
            payload["niche"] = niche
        return await self._request("POST", "api/v1/pricing/ai-suggestions", payload)
    
    async def apply_price_changes(self, price_changes: List[Dict]) -> Dict:
        """
        Apply price changes to products
        
        Args:
            price_changes: List of {
                "product_id": str,
                "new_price": float,
                "reason": str
            }
        """
        payload = {"price_changes": price_changes}
        return await self._request("POST", "api/v1/pricing/apply", payload)
    
    async def sync_inventory(self, product_ids: Optional[List[str]] = None) -> Dict:
        """Trigger inventory sync for products"""
        payload = {}
        if product_ids:
            payload["product_ids"] = product_ids
        return await self._request("POST", "api/v1/inventory/sync", payload)
    
    async def get_inventory_status(self, product_id: str) -> Dict:
        """Get current inventory status for a product"""
        return await self._request("GET", f"api/v1/inventory/status/{product_id}")
    
    # ============ Order Fulfillment ============
    
    async def get_orders(self, status: Optional[str] = None,
                        limit: int = 50,
                        page: int = 1) -> Dict:
        """Get orders from AutoDS"""
        params = {"limit": limit, "page": page}
        if status:
            params["status"] = status
        return await self._request("GET", "api/v1/orders", params=params)
    
    async def get_order_details(self, order_id: str) -> Dict:
        """Get detailed order information"""
        return await self._request("GET", f"api/v1/orders/{order_id}")
    
    async def enable_auto_fulfillment(self, store_id: str, enabled: bool = True) -> Dict:
        """Enable/disable automatic order fulfillment"""
        payload = {
            "store_id": store_id,
            "auto_fulfillment_enabled": enabled
        }
        return await self._request("POST", "api/v1/fulfillment/settings", payload)
    
    async def fulfill_order(self, order_id: str, fulfillment_data: Optional[Dict] = None) -> Dict:
        """Manually trigger order fulfillment"""
        payload = {"order_id": order_id}
        if fulfillment_data:
            payload.update(fulfillment_data)
        return await self._request("POST", "api/v1/orders/fulfill", payload)
    
    async def get_tracking_info(self, order_id: str) -> Dict:
        """Get tracking information for an order"""
        return await self._request("GET", f"api/v1/orders/{order_id}/tracking")
    
    async def update_tracking(self, order_id: str, tracking_number: str, 
                             carrier: str) -> Dict:
        """Update tracking information"""
        payload = {
            "order_id": order_id,
            "tracking_number": tracking_number,
            "carrier": carrier
        }
        return await self._request("POST", "api/v1/orders/tracking", payload)
    
    # ============ Supplier Management ============
    
    async def list_suppliers(self) -> Dict:
        """List available suppliers"""
        return await self._request("GET", "api/v1/suppliers")
    
    async def get_supplier_performance(self, supplier_id: str) -> Dict:
        """Get supplier performance metrics"""
        return await self._request("GET", f"api/v1/suppliers/{supplier_id}/performance")
    
    async def switch_supplier(self, product_id: str, new_supplier_id: str) -> Dict:
        """Switch product to a different supplier"""
        payload = {
            "product_id": product_id,
            "new_supplier_id": new_supplier_id
        }
        return await self._request("POST", "api/v1/products/switch-supplier", payload)
    
    # ============ Analytics ============
    
    async def get_dashboard_stats(self, store_id: str, 
                                  start_date: Optional[str] = None,
                                  end_date: Optional[str] = None) -> Dict:
        """Get store performance dashboard"""
        params = {"store_id": store_id}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        return await self._request("GET", "api/v1/analytics/dashboard", params=params)
    
    async def get_product_performance(self, product_id: str,
                                     days: int = 30) -> Dict:
        """Get performance metrics for a product"""
        params = {"days": days}
        return await self._request(
            "GET", 
            f"api/v1/analytics/products/{product_id}", 
            params=params
        )
    
    async def get_profit_loss(self, store_id: str, 
                             period: str = "month") -> Dict:
        """Get profit/loss report"""
        params = {"store_id": store_id, "period": period}
        return await self._request("GET", "api/v1/analytics/profit-loss", params=params)


# Singleton instance
_autods_client: Optional[AutoDSClient] = None


def get_autods_client() -> AutoDSClient:
    """Get or create AutoDS client singleton"""
    global _autods_client
    if _autods_client is None:
        _autods_client = AutoDSClient()
    return _autods_client
