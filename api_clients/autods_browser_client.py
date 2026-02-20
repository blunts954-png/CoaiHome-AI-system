"""
AutoDS Browser Automation Client - NO API REQUIRED
Uses Playwright to automate AutoDS dashboard actions
This is a workaround until you get official API access
"""
import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
import re

try:
    from playwright.async_api import async_playwright, Page, Browser
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("⚠️ Playwright not installed. Run: pip install playwright && playwright install")

from config.settings import settings


class AutoDSBrowserClient:
    """
    AutoDS Browser Automation - No API Key Needed!
    
    This client automates the AutoDS web dashboard using browser automation.
    It can:
    - Log into AutoDS
    - Import products from supplier URLs
    - Monitor orders
    - Update pricing
    - Sync inventory
    
    NOTE: You need to log in manually the first time to handle 2FA
    """
    
    def __init__(self):
        self.autods_email = None  # Set from env: AUTODS_EMAIL
        self.autods_password = None  # Set from env: AUTODS_PASSWORD
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.logged_in = False
        self._load_credentials()
    
    def _load_credentials(self):
        """Load credentials from environment"""
        import os
        self.autods_email = os.getenv("AUTODS_EMAIL", "")
        self.autods_password = os.getenv("AUTODS_PASSWORD", "")
        self.shopify_store = os.getenv("SHOPIFY_SHOP_URL", "")
    
    async def start(self, headless: bool = False):
        """Start browser session"""
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError("Playwright not installed. Run: pip install playwright && playwright install")
        
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=headless)
        context = await self.browser.new_context(viewport={"width": 1920, "height": 1080})
        self.page = await context.new_page()
        print("🌐 Browser started")
    
    async def login(self) -> bool:
        """Login to AutoDS (may require manual 2FA first time)"""
        if not self.page:
            await self.start()
        
        if not self.autods_email or not self.autods_password:
            print("❌ Set AUTODS_EMAIL and AUTODS_PASSWORD environment variables")
            return False
        
        try:
            print("🔐 Logging into AutoDS...")
            await self.page.goto("https://www.autods.com/login/")
            await self.page.wait_for_load_state("networkidle")
            
            # Fill login form
            await self.page.fill('input[type="email"]', self.autods_email)
            await self.page.fill('input[type="password"]', self.autods_password)
            await self.page.click('button[type="submit"]')
            
            # Wait for dashboard or 2FA
            await asyncio.sleep(3)
            
            # Check if we're logged in
            if "dashboard" in self.page.url or "app.autods" in self.page.url:
                self.logged_in = True
                print("✅ Logged into AutoDS")
                return True
            else:
                print("⚠️ May need manual 2FA - check browser")
                # Wait for manual intervention
                input("Press Enter after completing 2FA...")
                self.logged_in = True
                return True
                
        except Exception as e:
            print(f"❌ Login failed: {e}")
            return False
    
    async def import_product_from_url(self, supplier_url: str, 
                                       product_data: Dict) -> Dict:
        """
        Import a product from supplier URL (AliExpress, Amazon, etc.)
        
        Args:
            supplier_url: URL of the product to import
            product_data: Dict with title, description, price, etc.
        
        Returns:
            Dict with import status and product IDs
        """
        if not self.logged_in:
            await self.login()
        
        try:
            print(f"📦 Importing product from: {supplier_url}")
            
            # Navigate to Add Products page
            await self.page.goto("https://app.autods.com/products/add")
            await self.page.wait_for_load_state("networkidle")
            await asyncio.sleep(2)
            
            # Select single product import
            await self.page.click('text=Single Product')
            await asyncio.sleep(1)
            
            # Paste supplier URL
            await self.page.fill('input[placeholder*="URL"]', supplier_url)
            await asyncio.sleep(1)
            
            # Click import
            await self.page.click('button:has-text("Import")')
            
            # Wait for product editor to load
            await self.page.wait_for_selector('.product-editor', timeout=30000)
            await asyncio.sleep(3)
            
            # Fill in product details if provided
            if product_data.get('title'):
                await self.page.fill('input[name="title"]', product_data['title'])
            
            if product_data.get('description'):
                # Switch to HTML mode and add description
                await self.page.click('text=HTML')
                await self.page.fill('textarea[name="description"]', 
                                     product_data['description'])
            
            if product_data.get('price'):
                await self.page.fill('input[name="price"]', str(product_data['price']))
            
            # Publish to Shopify
            await self.page.click('button:has-text("Publish to Store")')
            await asyncio.sleep(5)
            
            # Get product ID from success message or URL
            # This is simplified - actual implementation would parse the response
            return {
                "success": True,
                "supplier_url": supplier_url,
                "message": "Product imported via browser automation",
                "note": "Check AutoDS dashboard for product ID"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Import failed - check screenshots"
            }
    
    async def bulk_import_from_urls(self, urls_with_data: List[Dict]) -> Dict:
        """
        Import multiple products
        
        Args:
            urls_with_data: List of dicts with 'url' and 'data' keys
        """
        results = []
        for item in urls_with_data:
            result = await self.import_product_from_url(
                item['url'], 
                item.get('data', {})
            )
            results.append(result)
            await asyncio.sleep(3)  # Rate limiting
        
        successful = sum(1 for r in results if r.get('success'))
        return {
            "total": len(results),
            "successful": successful,
            "failed": len(results) - successful,
            "results": results
        }
    
    async def get_orders(self, status: str = "all") -> Dict:
        """Get orders from AutoDS dashboard"""
        if not self.logged_in:
            await self.login()
        
        try:
            await self.page.goto("https://app.autods.com/orders")
            await self.page.wait_for_load_state("networkidle")
            await asyncio.sleep(3)
            
            # Filter by status if needed
            if status != "all":
                await self.page.click(f'text={status.title()}')
                await asyncio.sleep(2)
            
            # Extract order data from the table
            # This is a simplified version - actual scraping would be more robust
            orders = await self.page.evaluate('''() => {
                const rows = document.querySelectorAll('.order-row');
                return Array.from(rows).map(row => ({
                    id: row.querySelector('.order-id')?.textContent?.trim(),
                    status: row.querySelector('.order-status')?.textContent?.trim(),
                    total: row.querySelector('.order-total')?.textContent?.trim()
                }));
            }''')
            
            return {
                "orders": orders,
                "count": len(orders),
                "status": status
            }
            
        except Exception as e:
            return {"error": str(e), "orders": []}
    
    async def update_product_price(self, autods_product_id: str, 
                                    new_price: float) -> Dict:
        """Update product price in AutoDS"""
        if not self.logged_in:
            await self.login()
        
        try:
            await self.page.goto(f"https://app.autods.com/products/edit/{autods_product_id}")
            await self.page.wait_for_load_state("networkidle")
            await asyncio.sleep(2)
            
            # Update price
            await self.page.fill('input[name="price"]', str(new_price))
            await self.page.click('button:has-text("Save")')
            await asyncio.sleep(2)
            
            return {
                "success": True,
                "product_id": autods_product_id,
                "new_price": new_price
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_inventory_status(self, autods_product_id: str) -> Dict:
        """Get product inventory status"""
        if not self.logged_in:
            await self.login()
        
        try:
            await self.page.goto(f"https://app.autods.com/products/edit/{autods_product_id}")
            await self.page.wait_for_load_state("networkidle")
            await asyncio.sleep(2)
            
            # Extract inventory info
            inventory = await self.page.evaluate('''() => ({
                quantity: document.querySelector('.inventory-quantity')?.textContent,
                status: document.querySelector('.stock-status')?.textContent
            })''')
            
            return {
                "product_id": autods_product_id,
                "available_quantity": int(inventory.get('quantity', 0)) if inventory.get('quantity') else 0,
                "status": inventory.get('status', 'unknown')
            }
            
        except Exception as e:
            return {"error": str(e), "available_quantity": 0}
    
    async def close(self):
        """Close browser session"""
        if self.browser:
            await self.browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.stop()
        print("🌐 Browser closed")
    
    async def take_screenshot(self, filename: str = "autods_screenshot.png"):
        """Take screenshot for debugging"""
        if self.page:
            await self.page.screenshot(path=filename)
            print(f"📸 Screenshot saved: {filename}")


# Singleton
_browser_client: Optional[AutoDSBrowserClient] = None


async def get_browser_client() -> AutoDSBrowserClient:
    """Get or create browser client"""
    global _browser_client
    if _browser_client is None:
        _browser_client = AutoDSBrowserClient()
    return _browser_client
