"""
CJ Dropshipping API Client
Handles all CJ Dropshipping API interactions for product research, import, and order fulfillment.
API Docs: https://developers.cjdropshipping.com/
"""
import asyncio
import aiohttp
import ssl
import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from config.settings import settings


class CJDropshippingClient:
    """Client for CJ Dropshipping API 2.0"""
    
    def __init__(self):
        # Read token directly from env var first (most reliable on Railway)
        raw_token = (
            os.getenv("CJ_API_TOKEN", "").strip()
            or settings.cj.api_token.strip()
        )
        self.api_token = raw_token
        self.api_email = (os.getenv("CJ_API_EMAIL", "") or settings.cj.api_email or "").strip()
        self.api_key = (os.getenv("CJ_API_KEY", "") or settings.cj.api_key or "").strip()
        
        # If combined token contains @api@, parse it
        if self.api_token and "@api@" in self.api_token:
            parts = self.api_token.split("@api@")
            if len(parts) == 2:
                if not self.api_email:
                    self.api_email = parts[0].strip()
                if not self.api_key:
                    self.api_key = parts[1].strip()
        
        # Debug print so we can see in Railway logs whether credentials loaded
        masked_key = (self.api_key[:6] + "...") if self.api_key and len(self.api_key) > 6 else "(empty)"
        print(f"CJ Client Init: email={self.api_email or '(empty)'}, key={masked_key}")
        
        self.base_url = (os.getenv("CJ_BASE_URL") or settings.cj.base_url or "https://developers.cjdropshipping.com/api2.0/v1").rstrip("/")
        self.default_country = settings.cj.default_country
        self.access_token: Optional[str] = None
        self.token_expires: Optional[datetime] = None
        
        self.headers = {
            "Content-Type": "application/json"
        }
        self.session: Optional[aiohttp.ClientSession] = None
        self._ssl_context = None
        self._shopify_mode = not (self.api_email and self.api_key)
        self._ssl_error = False
    
    @property
    def shopify_mode(self) -> bool:
        """Returns True if CJ API is not configured (fallback to Shopify-only mode)"""
        return self._shopify_mode
    
    def _get_ssl_context(self):
        """Get SSL context for HTTPS requests.
        
        WARNING: Disabling SSL verification is SECURELY DISABLED for production safety.
        SSL certificate verification should always be enabled in production.
        """
        # SSL verification is always enabled for security
        # To re-enable testing options, set CJ_FORCE_SSL_VERIFY=false (not recommended for production)
        if self._ssl_context is None:
            self._ssl_context = ssl.create_default_context()
        return self._ssl_context
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            connector = aiohttp.TCPConnector(ssl=self._get_ssl_context())
            self.session = aiohttp.ClientSession(connector=connector)
        return self.session
    
    async def close(self):
        """Close the HTTP session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def _get_access_token(self) -> str:
        """Get or refresh CJ API access token"""
        # Check if we have a valid token
        if self.access_token and self.token_expires and datetime.utcnow() < self.token_expires:
            return self.access_token
        
        # Need to authenticate
        if not self.api_email or not self.api_key:
            raise ValueError("CJ API email and key not configured")
        
        session = await self._get_session()
        auth_url = f"{self.base_url}/authentication/getAccessToken"
        auth_payloads = [
            # Current CJ schema observed in production
            {"email": self.api_email, "password": self.api_key},
            # Backward compatibility fallback for older accounts
            {"email": self.api_email, "apikey": self.api_key},
        ]
        auth_errors = []

        try:
            for index, payload in enumerate(auth_payloads):
                async with session.post(auth_url, json=payload) as response:
                    try:
                        data = await response.json(content_type=None)
                    except Exception:
                        data = {"message": await response.text()}

                    if response.status == 200 and data.get("result"):
                        auth_data = data.get("data", {})
                        token = None
                        expires_in = 1296000

                        if isinstance(auth_data, dict):
                            token = auth_data.get("accessToken") or auth_data.get("access_token")
                            expires_in = auth_data.get("expiresIn", expires_in)
                        else:
                            token = data.get("accessToken") or data.get("access_token") or data.get("token")

                        if token:
                            self.access_token = token
                            # Token expires in 15 days, but we'll refresh after 14
                            self.token_expires = datetime.utcnow() + timedelta(seconds=max(int(expires_in) - 3600, 60))
                            return self.access_token

                        field_name = "apikey" if "apikey" in payload else "password"
                        auth_errors.append(f"{field_name}: authentication succeeded but no token was returned")
                        continue

                    field_name = "apikey" if "apikey" in payload else "password"
                    error_msg = data.get("message") or data.get("error") or f"HTTP {response.status}"
                    auth_errors.append(f"{field_name}: {error_msg}")

                    # Avoid unnecessary retries against strict QPS-limited auth endpoints.
                    if index == 0:
                        lower_msg = str(error_msg).lower()
                        should_try_legacy = (
                            "apikey" in lower_msg
                            or "api key" in lower_msg
                            or ("password" in lower_msg and "empty" in lower_msg)
                        )
                        if not should_try_legacy:
                            break

            if auth_errors:
                raise Exception(f"CJ Auth Error: {' | '.join(auth_errors)}")

            raise Exception("CJ Auth Error: Authentication failed")
        except aiohttp.ClientConnectorSSLError as e:
            self._ssl_error = True
            raise Exception(f"CJ SSL Error: Unable to verify SSL certificate. "
                          f"This may be due to outdated system certificates or CJ API SSL issues. "
                          f"Error: {e}")
    
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """Make authenticated API request to CJ Dropshipping"""
        session = await self._get_session()
        
        # Get access token (handles authentication)
        token = await self._get_access_token()
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = {
            "CJ-Access-Token": token,
            "Content-Type": "application/json"
        }
        
        # Merge headers if provided in kwargs
        if "headers" in kwargs:
            headers.update(kwargs.pop("headers"))
        
        try:
            async with session.request(method, url, headers=headers, **kwargs) as response:
                data = await response.json()
                return data
        except aiohttp.ClientConnectorSSLError as e:
            self._ssl_error = True
            return {
                "result": False,
                "message": f"SSL Certificate Error: {e}",
                "error_type": "ssl_error"
            }
    
    # ============================================================
    # AUTH & ACCOUNT
    # ============================================================
    
    async def validate_token(self) -> bool:
        """Validate CJ API credentials by attempting authentication"""
        try:
            token = await self._get_access_token()
            return bool(token)
        except Exception as e:
            print(f"CJ API validation failed: {e}")
            return False
    
    async def get_account_info(self) -> Dict:
        """Get CJ account information"""
        return await self._make_request("GET", "/user/getInfo")
    
    # ============================================================
    # PRODUCT RESEARCH
    # ============================================================
    
    async def get_trending_products(self, 
                                    niche: Optional[str] = None,
                                    limit: int = 50,
                                    country: str = "US") -> Dict:
        """
        Get trending products from CJ
        """
        params = {
            "pageNum": 1,
            "pageSize": min(limit, 100),
            "country": country
        }
        
        if niche:
            params["categoryName"] = niche
        
        return await self._make_request("GET", "/product/list", params=params)
    
    async def search_products(self,
                              keyword: str,
                              category: Optional[str] = None,
                              min_price: Optional[float] = None,
                              max_price: Optional[float] = None,
                              sort: str = "listTime",
                              limit: int = 50) -> Dict:
        """
        Search products by keyword
        """
        params = {
            "pageNum": 1,
            "pageSize": min(limit, 100),
            "keyword": keyword,
            "sort": sort
        }
        
        if category:
            params["categoryName"] = category
        if min_price is not None:
            params["minPrice"] = min_price
        if max_price is not None:
            params["maxPrice"] = max_price
        
        return await self._make_request("GET", "/product/search", params=params)
    
    async def get_product_details(self, product_id: str) -> Dict:
        """Get detailed product information"""
        return await self._make_request("GET", "/product/query", params={"pid": product_id})
    
    async def get_product_variants(self, product_id: str) -> Dict:
        """Get product variants/stock info"""
        return await self._make_request("GET", "/product/stock", params={"pid": product_id})
    
    async def get_shipping_costs(self, 
                                  product_id: str,
                                  country: str,
                                  quantity: int = 1,
                                  variant_id: Optional[str] = None) -> Dict:
        """Calculate shipping costs for a product"""
        params = {
            "pid": product_id,
            "countryCode": country,
            "num": quantity
        }
        
        if variant_id:
            params["vid"] = variant_id
        
        return await self._make_request("GET", "/product/shipping-cost", params=params)
    
    # ============================================================
    # PRODUCT IMPORT
    # ============================================================
    
    async def get_connection_list(self) -> Dict:
        """Get connected stores (Shopify, WooCommerce, etc.)"""
        return await self._make_request("GET", "/connection/list")
    
    async def import_to_shopify(self,
                                 product_id: str,
                                 shopify_store_id: str,
                                 price_markup: float = 2.5,
                                 custom_title: Optional[str] = None,
                                 custom_description: Optional[str] = None) -> Dict:
        """Import a CJ product to Shopify"""
        data = {
            "pid": product_id,
            "shopId": shopify_store_id,
            "priceMarkUp": price_markup
        }
        
        if custom_title:
            data["productName"] = custom_title
        if custom_description:
            data["productDescription"] = custom_description
        
        return await self._make_request("POST", "/product/create", json=data)
    
    # ============================================================
    # ORDER MANAGEMENT
    # ============================================================
    
    async def list_orders(self,
                          status: Optional[str] = None,
                          start_date: Optional[str] = None,
                          end_date: Optional[str] = None,
                          limit: int = 50) -> Dict:
        """List orders"""
        params = {
            "pageNum": 1,
            "pageSize": min(limit, 100)
        }
        
        if status:
            params["status"] = status
        if start_date:
            params["startDate"] = start_date
        if end_date:
            params["endDate"] = end_date
        
        return await self._make_request("GET", "/order/list", params=params)
    
    async def create_order(self, order_data: Dict) -> Dict:
        """Create a new order"""
        return await self._make_request("POST", "/order/create", json=order_data)

    async def batch_create_order(self, order_payload: Dict) -> Dict:
        """Create a batch order (recommended for dropshipping)"""
        return await self._make_request("POST", "/shopping/order/batchCreateOrder", json=order_payload)

    async def get_order_details(self, cj_order_id: str) -> Dict:
        """Get detailed order information by CJ order ID (queryById)"""
        return await self._make_request("POST", "/shopping/order/queryById", json={"id": cj_order_id})
    
    async def get_order_details_legacy(self, order_id: str) -> Dict:
        """Get detailed order information (legacy endpoint)"""
        return await self._make_request("GET", "/order/getOrderDetails", params={"orderId": order_id})
    
    async def cancel_order(self, order_id: str, reason: str = "") -> Dict:
        """Cancel an order"""
        data = {"orderId": order_id, "reason": reason}
        return await self._make_request("POST", "/order/cancelOrder", json=data)
    
    # ============================================================
    # INVENTORY SYNC
    # ============================================================
    
    async def get_inventory(self, product_ids: Optional[List[str]] = None) -> Dict:
        """Get inventory levels for products"""
        params = {"pageNum": 1, "pageSize": 100}
        
        if product_ids:
            params["pid"] = ",".join(product_ids)
        
        return await self._make_request("GET", "/product/stock", params=params)
    
    async def sync_inventory_batch(self, shopify_product_ids: List[str]) -> Dict:
        """Sync inventory for multiple Shopify products"""
        data = {"shopifyProductIds": shopify_product_ids}
        return await self._make_request("POST", "/inventory/sync", json=data)
    
    # ============================================================
    # CATEGORIES
    # ============================================================
    
    async def get_categories(self) -> Dict:
        """Get all product categories"""
        return await self._make_request("GET", "/product/getCategory")
    
    async def get_recommended_products(self, category: str, limit: int = 20) -> Dict:
        """Get recommended products for a category"""
        params = {
            "categoryName": category,
            "pageNum": 1,
            "pageSize": min(limit, 100)
        }
        return await self._make_request("GET", "/product/list", params=params)


# Singleton instance
_cj_client: Optional[CJDropshippingClient] = None


def get_cj_client() -> CJDropshippingClient:
    """Get or create CJ client instance"""
    global _cj_client
    if _cj_client is None:
        _cj_client = CJDropshippingClient()
    return _cj_client


# Convenience function for product research
async def research_cj_products(niche: str, 
                                limit: int = 50,
                                min_price: Optional[float] = None,
                                max_price: Optional[float] = None) -> List[Dict]:
    """
    Research products on CJ Dropshipping
    
    Returns list of products formatted for the research system
    """
    client = get_cj_client()
    
    if client.shopify_mode:
        raise Exception("CJ API not configured. Please set CJ_API_TOKEN in your .env file")
    
    # Search for products
    result = await client.search_products(keyword=niche, limit=limit)
    
    if not result.get("result"):
        error_msg = result.get("message", "Unknown error")
        if "ssl" in error_msg.lower():
            raise Exception(f"CJ API SSL Error: {error_msg}. Please check your system certificates or CJ API status.")
        raise Exception(f"CJ API Error: {error_msg}")
    
    products = result.get("data", {}).get("list", [])
    formatted_products = []
    
    for product in products:
        # Calculate potential pricing
        cost = float(product.get("sellPrice", 0))
        suggested_price = cost * settings.store.base_markup
        
        # Skip if outside price range
        if min_price and suggested_price < min_price:
            continue
        if max_price and suggested_price > max_price:
            continue
        
        formatted = {
            "id": product.get("pid"),
            "title": product.get("productName"),
            "description": product.get("description"),
            "cost_price": cost,
            "suggested_price": suggested_price,
            "images": [product.get("imageUrl")] if product.get("imageUrl") else [],
            "supplier_id": "cj_dropshipping",
            "supplier_name": "CJ Dropshipping",
            "supplier_rating": 4.5,
            "shipping_days": 7,
            "category": product.get("categoryName"),
            "source_url": f"https://cjdropshipping.com/product/{product.get('pid')}",
            "raw_data": product
        }
        
        formatted_products.append(formatted)
    
    return formatted_products
