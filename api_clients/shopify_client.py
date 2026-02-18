"""
Shopify Admin API Client
Handles all interactions with Shopify for store management, products, orders, etc.
"""
import httpx
from typing import Optional, List, Dict, Any
from datetime import datetime
import json

from config.settings import settings
from models.database import SessionLocal, Product, OrderException


class ShopifyClient:
    """Shopify Admin API Client"""
    
    def __init__(self):
        self.shop_url = settings.shopify.shop_url
        self.access_token = settings.shopify.access_token
        self.api_version = settings.shopify.api_version
        self.base_url = f"https://{self.shop_url}/admin/api/{self.api_version}"
        self.headers = {
            "X-Shopify-Access-Token": self.access_token,
            "Content-Type": "application/json"
        }
    
    async def _request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """Make an authenticated request to Shopify API"""
        url = f"{self.base_url}/{endpoint}"
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method,
                url=url,
                headers=self.headers,
                json=data,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
    
    # ============ Store Management ============
    
    async def get_shop_info(self) -> Dict:
        """Get current shop information"""
        return await self._request("GET", "shop.json")
    
    async def update_shop_metafields(self, metafields: List[Dict]) -> Dict:
        """Update shop-level metafields"""
        return await self._request("POST", "metafields.json", {"metafields": metafields})
    
    # ============ Product Management ============
    
    async def create_product(self, product_data: Dict) -> Dict:
        """Create a new product in Shopify"""
        payload = {"product": product_data}
        return await self._request("POST", "products.json", payload)
    
    async def update_product(self, product_id: str, product_data: Dict) -> Dict:
        """Update an existing product"""
        payload = {"product": product_data}
        return await self._request("PUT", f"products/{product_id}.json", payload)
    
    async def delete_product(self, product_id: str) -> Dict:
        """Delete a product from Shopify"""
        return await self._request("DELETE", f"products/{product_id}.json")
    
    async def get_product(self, product_id: str) -> Dict:
        """Get a single product by ID"""
        return await self._request("GET", f"products/{product_id}.json")
    
    async def list_products(self, limit: int = 50, page_info: Optional[str] = None) -> Dict:
        """List products with pagination"""
        params = f"?limit={limit}"
        if page_info:
            params += f"&page_info={page_info}"
        return await self._request("GET", f"products.json{params}")
    
    async def update_product_price(self, product_id: str, variant_id: str, price: float) -> Dict:
        """Update product variant price"""
        payload = {
            "variant": {
                "id": variant_id,
                "price": str(price)
            }
        }
        return await self._request("PUT", f"variants/{variant_id}.json", payload)
    
    async def update_inventory(self, inventory_item_id: str, available: int) -> Dict:
        """Update inventory quantity"""
        payload = {
            "inventory_item": {
                "id": inventory_item_id,
                "available": available
            }
        }
        return await self._request("PUT", f"inventory_items/{inventory_item_id}.json", payload)
    
    # ============ Order Management ============
    
    async def get_order(self, order_id: str) -> Dict:
        """Get order details"""
        return await self._request("GET", f"orders/{order_id}.json")
    
    async def list_orders(self, status: str = "any", limit: int = 50, 
                         created_at_min: Optional[str] = None) -> Dict:
        """List orders with filters"""
        params = f"?status={status}&limit={limit}"
        if created_at_min:
            params += f"&created_at_min={created_at_min}"
        return await self._request("GET", f"orders.json{params}")
    
    async def update_order(self, order_id: str, order_data: Dict) -> Dict:
        """Update order details"""
        payload = {"order": order_data}
        return await self._request("PUT", f"orders/{order_id}.json", payload)
    
    async def add_order_note(self, order_id: str, note: str) -> Dict:
        """Add a note to an order"""
        return await self.update_order(order_id, {"note": note})
    
    async def get_order_fulfillments(self, order_id: str) -> Dict:
        """Get fulfillment data for an order"""
        return await self._request("GET", f"orders/{order_id}/fulfillments.json")
    
    async def create_fulfillment(self, order_id: str, fulfillment_data: Dict) -> Dict:
        """Create a fulfillment for an order"""
        payload = {"fulfillment": fulfillment_data}
        return await self._request("POST", f"orders/{order_id}/fulfillments.json", payload)
    
    async def update_fulfillment_tracking(self, order_id: str, fulfillment_id: str, 
                                         tracking_info: Dict) -> Dict:
        """Update tracking information"""
        payload = {"fulfillment": tracking_info}
        return await self._request(
            "PUT", 
            f"orders/{order_id}/fulfillments/{fulfillment_id}.json", 
            payload
        )
    
    # ============ Customer Management ============
    
    async def get_customer(self, customer_id: str) -> Dict:
        """Get customer details"""
        return await self._request("GET", f"customers/{customer_id}.json")
    
    async def list_customers(self, query: Optional[str] = None, limit: int = 50) -> Dict:
        """List customers"""
        params = f"?limit={limit}"
        if query:
            params += f"&query={query}"
        return await self._request("GET", f"customers.json{params}")
    
    async def send_customer_email(self, customer_id: str, subject: str, body: str) -> bool:
        """Send email to customer via Shopify (requires Email app)"""
        # This would integrate with Shopify Email or a third-party app
        # For now, return True as placeholder
        return True
    
    # ============ Analytics ============
    
    async def get_product_analytics(self, product_id: str, 
                                    start_date: Optional[str] = None,
                                    end_date: Optional[str] = None) -> Dict:
        """Get product performance metrics"""
        # Note: This uses Shopify Analytics API or reports
        params = "?"
        if start_date:
            params += f"started_at={start_date}&"
        if end_date:
            params += f"ended_at={end_date}"
        
        return await self._request("GET", f"products/{product_id}/metrics.json{params}")
    
    async def get_orders_count(self, created_at_min: Optional[str] = None) -> int:
        """Get total orders count"""
        params = ""
        if created_at_min:
            params = f"?created_at_min={created_at_min}"
        result = await self._request("GET", f"orders/count.json{params}")
        return result.get("count", 0)
    
    # ============ Webhooks ============
    
    async def create_webhook(self, topic: str, address: str) -> Dict:
        """Create a webhook subscription"""
        payload = {
            "webhook": {
                "topic": topic,
                "address": address,
                "format": "json"
            }
        }
        return await self._request("POST", "webhooks.json", payload)
    
    async def list_webhooks(self) -> List[Dict]:
        """List all webhooks"""
        result = await self._request("GET", "webhooks.json")
        return result.get("webhooks", [])
    
    async def delete_webhook(self, webhook_id: str) -> Dict:
        """Delete a webhook"""
        return await self._request("DELETE", f"webhooks/{webhook_id}.json")
    
    # ============ Theme/Pages ============
    
    async def list_themes(self) -> Dict:
        """List store themes"""
        return await self._request("GET", "themes.json")
    
    async def update_theme_asset(self, theme_id: str, key: str, value: str) -> Dict:
        """Update a theme asset"""
        payload = {
            "asset": {
                "key": key,
                "value": value
            }
        }
        return await self._request("PUT", f"themes/{theme_id}/assets.json", payload)
    
    async def create_page(self, title: str, body_html: str, 
                         handle: Optional[str] = None,
                         template_suffix: Optional[str] = None) -> Dict:
        """Create a new page"""
        payload = {
            "page": {
                "title": title,
                "body_html": body_html,
                "published": True
            }
        }
        if handle:
            payload["page"]["handle"] = handle
        if template_suffix:
            payload["page"]["template_suffix"] = template_suffix
            
        return await self._request("POST", "pages.json", payload)
    
    async def update_page(self, page_id: str, page_data: Dict) -> Dict:
        """Update an existing page"""
        payload = {"page": page_data}
        return await self._request("PUT", f"pages/{page_id}.json", payload)


# Singleton instance
_shopify_client: Optional[ShopifyClient] = None


def get_shopify_client() -> ShopifyClient:
    """Get or create Shopify client singleton"""
    global _shopify_client
    if _shopify_client is None:
        _shopify_client = ShopifyClient()
    return _shopify_client
