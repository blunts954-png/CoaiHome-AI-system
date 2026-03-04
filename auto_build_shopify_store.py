"""
AUTOMATIC SHOPIFY STORE BUILDER
Uses your API credentials to actually build the store - no manual work!
"""
import asyncio
import json
import base64
import hashlib
import hmac
import time
from urllib.parse import urlencode, parse_qs, urlparse
from typing import Dict, List, Optional
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Your Shopify App credentials
# Load settings
from config.settings import settings

SHOPIFY_API_KEY = settings.shopify.api_key
SHOPIFY_API_SECRET = settings.shopify.api_secret
SHOP_DOMAIN = settings.shopify.shop_url


class AutomaticShopifyBuilder:
    """Actually builds the Shopify store using API"""
    
    def __init__(self):
        self.access_token = None
        self.shop_domain = SHOP_DOMAIN
        self.api_version = "2024-01"
        
    async def build_store(self) -> Dict:
        """Main builder - creates everything automatically"""
        print("=" * 70)
        print("AUTOMATIC SHOPIFY STORE BUILDER")
        print("=" * 70)
        print()
        print(f"Target Store: {self.shop_domain}")
        print()
        
        results = {
            "status": "starting",
            "steps_completed": [],
            "steps_failed": [],
            "products_created": 0,
            "pages_created": 0,
            "theme_customized": False
        }
        
        try:
            # Step 1: Get access token
            print("STEP 1: Getting API access...")
            if await self._get_access_token():
                results["steps_completed"].append("API access granted")
                print("   OK: Connected to Shopify")
            else:
                results["steps_failed"].append("API access")
                print("   WARNING: Need to complete OAuth flow")
                print()
                await self._show_oauth_instructions()
                return results
            print()
            
            # Step 2: Create products
            print("STEP 2: Creating 15 products...")
            products = await self._create_all_products()
            results["products_created"] = len(products)
            results["steps_completed"].append(f"{len(products)} products created")
            print(f"   OK: {len(products)} products created")
            print()
            
            # Step 3: Create pages
            print("STEP 3: Creating store pages...")
            pages = await self._create_all_pages()
            results["pages_created"] = len(pages)
            results["steps_completed"].append(f"{len(pages)} pages created")
            print(f"   OK: {len(pages)} pages created")
            print()
            
            # Step 4: Configure theme
            print("STEP 4: Configuring theme...")
            if await self._configure_theme():
                results["theme_customized"] = True
                results["steps_completed"].append("Theme configured")
                print("   OK: Theme configured")
            else:
                results["steps_failed"].append("Theme configuration")
                print("   WARNING: Theme requires manual setup")
            print()
            
            # Step 5: Create collections
            print("STEP 5: Creating collections...")
            collections = await self._create_collections()
            results["steps_completed"].append(f"{len(collections)} collections created")
            print(f"   OK: {len(collections)} collections created")
            print()
            
            # Step 6: Configure navigation
            print("STEP 6: Configuring navigation...")
            if await self._configure_navigation():
                results["steps_completed"].append("Navigation configured")
                print("   OK: Navigation configured")
            else:
                results["steps_failed"].append("Navigation")
                print("   WARNING: Navigation requires manual setup")
            print()
            
            results["status"] = "completed"
            
        except Exception as e:
            results["status"] = "failed"
            results["error"] = str(e)
            print(f"   ERROR: {e}")
        
        return results
    
    async def _get_access_token(self) -> bool:
        """Use the existing SHOPIFY_ACCESS_TOKEN — no OAuth flow needed."""
        from config.settings import settings
        import httpx
        
        verify_ssl = os.getenv("SHOPIFY_SSL_VERIFY", "true").lower() == "true"

        # Use the token from env/settings directly
        token = settings.shopify.access_token or os.getenv("SHOPIFY_ACCESS_TOKEN", "")
        if not token:
            print("   ERROR: SHOPIFY_ACCESS_TOKEN is not set in Railway environment variables.")
            print("   Go to Railway > Your Project > Variables and add SHOPIFY_ACCESS_TOKEN")
            return False

        self.access_token = token

        # Use shop_url from settings, fallback to env var directly
        shop = settings.shopify.shop_url or os.getenv("SHOPIFY_SHOP_URL", "")
        if not shop:
            print("   ERROR: SHOPIFY_SHOP_URL is not set in Railway environment variables.")
            return False
        
        self.shop_domain = shop

        # Verify the token works against the actual store
        try:
            url = f"https://{self.shop_domain}/admin/api/{self.api_version}/shop.json"
            headers = {"X-Shopify-Access-Token": self.access_token}
            async with httpx.AsyncClient(verify=verify_ssl, timeout=15.0) as client:
                response = await client.get(url, headers=headers)
                if response.status_code == 200:
                    shop_name = response.json().get("shop", {}).get("name", "Unknown")
                    print(f"   OK: Connected to Shopify store '{shop_name}'")
                    return True
                else:
                    print(f"   ERROR: Token rejected by Shopify — Status {response.status_code}")
                    print(f"   Response: {response.text[:200] if response.text else 'No response body'}")
                    print(f"   Check that SHOPIFY_ACCESS_TOKEN in Railway is still valid.")
                    return False
        except Exception as e:
            print(f"   ERROR: Could not reach Shopify — {e}")
            return False


    
    async def _show_oauth_instructions(self):
        """Show OAuth setup instructions"""
        print("=" * 70)
        print("OAUTH SETUP REQUIRED")
        print("=" * 70)
        print()
        print("To automatically build the store, you need to:")
        print()
        print("1. Install your Shopify App to the store:")
        print(f"   https://{self.shop_domain}/admin/oauth/authorize")
        print(f"   ?client_id={SHOPIFY_API_KEY}")
        print(f"   &scope=read_products,write_products,read_themes,write_themes")
        print(f"   &redirect_uri=https://your-app-url.com/auth/callback")
        print()
        print("2. After authorization, the app will receive an access token")
        print()
        print("3. Add this token to your .env file:")
        print("   SHOPIFY_ACCESS_TOKEN=your_new_token_here")
        print()
        print("ALTERNATIVE: Manual Deployment")
        print("-" * 70)
        print("Use the DEPLOY_PACKAGE/ folder:")
        print("- Upload shopify_import.csv to Products > Import")
        print("- Copy css.txt to Theme Settings > Custom CSS")
        print("- Copy pages/*.html to Online Store > Pages")
        print()
    
    async def _create_all_products(self) -> List[Dict]:
        """Research new products via CJ/AI and publish them directly to Shopify."""
        import httpx
        from models.database import SessionLocal, Product, ProductStatus
        
        if not self.access_token:
            print("   Cannot create products - no API access")
            return []

        verify_ssl = os.getenv("SHOPIFY_SSL_VERIFY", "true").lower() == "true"
        headers = {
            "X-Shopify-Access-Token": self.access_token,
            "Content-Type": "application/json"
        }
        
        # Step 1: Source products from CJ Dropshipping or AI fallback
        products_to_create = []
        
        try:
            print("   Sourcing products from CJ Dropshipping API...")
            from api_clients.cj_dropshipping_client import get_cj_client
            cj = get_cj_client()
            if not cj.shopify_mode:
                result = await cj.search_products(keyword="home organizer", limit=15)
                if result.get("result") and result.get("data", {}).get("list"):
                    for p in result["data"]["list"][:15]:
                        cost = float(p.get("sellPrice", 10.0) or 10.0)
                        price = max(round(cost * 2.5, 2), 19.99)
                        products_to_create.append({
                            "title": p.get("productName", "Home Organizer"),
                            "description": p.get("description") or f"Premium home organizer. Great for kitchens, bathrooms, and offices.",
                            "cost": cost,
                            "price": price,
                            "image": p.get("imageUrl"),
                            "sku": f"CJ-{p.get('pid', '')}"
                        })
                    print(f"   Found {len(products_to_create)} products from CJ API")
        except Exception as e:
            print(f"   CJ source attempt: {e}")
        
        # Fallback: Use AI-generated product catalog
        if len(products_to_create) < 5:
            print("   Using AI product catalog (CJ fallback)...")
            products_to_create = [
                {"title": "Bamboo Kitchen Drawer Organizer", "price": 34.99, "description": "Expandable bamboo drawer dividers. Keep your kitchen tools and utensils perfectly organized."},
                {"title": "Stackable Fridge Storage Bins (Set of 4)", "price": 42.99, "description": "Crystal-clear, stackable bins designed for refrigerators. Maximize your fridge space instantly."},
                {"title": "Rotating Makeup & Skincare Organizer", "price": 52.99, "description": "360° spinning tower with 20 storage sections. Keep your beauty products accessible and tidy."},
                {"title": "Magnetic Spice Rack (12 Jars Included)", "price": 45.99, "description": "Wall-mounted magnetic spice storage system. Saves counter space and keeps spices visible."},
                {"title": "Under-Sink Cabinet Organizer (2-Tier)", "price": 38.99, "description": "Adjustable 2-tier shelf maximizes under-sink space. Perfect for cleaning supplies."},
                {"title": "Floating Wall Shelf Set (Set of 3)", "price": 56.99, "description": "Minimalist floating shelves for any room. Display photos, plants, and decor with style."},
                {"title": "Closet Shelf Dividers (6 Pack)", "price": 24.99, "description": "Sturdy closet dividers for sweaters, jeans, and handbags. Install without tools."},
                {"title": "Desktop File & Document Organizer", "price": 32.99, "description": "5-tier mesh file organizer for offices and home desks. Keep paperwork sorted and accessible."},
                {"title": "Pantry Storage Container Set (10 Piece)", "price": 48.99, "description": "Airtight BPA-free containers for grains, pasta, and snacks. Includes labels and scoops."},
                {"title": "Over-The-Door Shoe Organizer (30 Pockets)", "price": 29.99, "description": "Space-saving door organizer for shoes, accessories, and household items. Fits any door."},
                {"title": "Cable Management Box & Cord Organizer", "price": 27.99, "description": "Hide power strips and tangled cables in this sleek organizer box. Clean, modern look."},
                {"title": "Handbag & Purse Organizer (Hanging)", "price": 36.99, "description": "Transparent hanging organizer for 12 bags. Clear pockets keep purses visible and accessible."},
                {"title": "Bathroom Counter Organizer (3-Tier)", "price": 31.99, "description": "3-tier rotating bathroom caddy for toiletries. Chrome finish looks premium in any bathroom."},
                {"title": "Stackable Storage Drawers (3-Drawer)", "price": 54.99, "description": "Clear stackable drawers perfect for makeup, office, or craft supplies. Smooth gliding drawers."},
                {"title": "Garage Wall Tool Organizer Panel", "price": 67.99, "description": "Pegboard panel system for garage tools. Includes 20 hooks and 5 baskets. Install in 30 min."},
            ]
        
        # Step 2: Push each product to Shopify
        created = []
        db = SessionLocal()
        
        async with httpx.AsyncClient(verify=verify_ssl, timeout=30.0) as client:
            # Get location ID for inventory
            loc_id = None
            try:
                loc_resp = await client.get(
                    f"https://{self.shop_domain}/admin/api/{self.api_version}/locations.json",
                    headers=headers
                )
                locations = loc_resp.json().get("locations", [])
                if locations:
                    loc_id = locations[0]["id"]
            except Exception as e:
                print(f"   [!] Could not get location for inventory: {e}")
            
            for p in products_to_create:
                try:
                    images = []
                    if p.get("image"):
                        images.append({"src": p["image"]})
                    
                    shopify_payload = {
                        "product": {
                            "title": p["title"],
                            "body_html": p.get("description", f"High-quality {p['title']} for your home."),
                            "vendor": "CoaiHome",
                            "product_type": self._get_product_type(p["title"]),
                            "tags": "organizer, home, storage, coaihome",
                            "images": images,
                            "variants": [{
                                "price": str(p.get("price", 29.99)),
                                "compare_at_price": str(round(p.get("price", 29.99) * 1.4, 2)),
                                "inventory_management": "shopify",
                                "sku": p.get("sku") or f"COAI-{len(created)+1:03d}"
                            }],
                            "status": "active",
                            "published": True
                        }
                    }
                    
                    resp = await client.post(
                        f"https://{self.shop_domain}/admin/api/{self.api_version}/products.json",
                        headers=headers, json=shopify_payload
                    )
                    
                    if resp.status_code == 201:
                        data = resp.json()
                        p_id = data["product"]["id"]
                        v_id = data["product"]["variants"][0]["id"]
                        inv_item_id = data["product"]["variants"][0]["inventory_item_id"]
                        
                        # Set inventory to 50 units
                        if loc_id:
                            await client.post(
                                f"https://{self.shop_domain}/admin/api/{self.api_version}/inventory_levels/set.json",
                                headers=headers,
                                json={"location_id": loc_id, "inventory_item_id": inv_item_id, "available": 50}
                            )
                        
                        # Save to database
                        db_p = Product(
                            shopify_product_id=str(p_id),
                            shopify_variant_id=str(v_id),
                            store_id=1,
                            title=p["title"],
                            description=p.get("description", ""),
                            selling_price=p.get("price", 29.99),
                            cost_price=p.get("cost", 0),
                            status=ProductStatus.ACTIVE,
                            supplier_name="CJ Dropshipping" if p.get("sku", "").startswith("CJ-") else "CoaiHome"
                        )
                        db.add(db_p)
                        db.commit()
                        
                        created.append(data["product"])
                        print(f"   ✅ Published: {p['title'][:50]}")
                        
                        await asyncio.sleep(0.5)  # Respect rate limits
                    else:
                        err = resp.text[:150] if resp.text else "No response"
                        print(f"   ❌ Failed: {p['title'][:40]} — {resp.status_code}: {err}")
                        
                except Exception as e:
                    print(f"   Error creating {p.get('title', '?')[:40]}: {e}")
        
        db.close()
        return created


    
    def _get_product_type(self, title: str) -> str:
        """Determine product type from title"""
        title_lower = title.lower()
        if any(x in title_lower for x in ["kitchen", "fridge", "pantry", "spice", "drawer", "cabinet", "pan"]):
            return "Kitchen Organization"
        elif any(x in title_lower for x in ["bathroom", "shower", "caddy"]):
            return "Bathroom Organization"
        elif any(x in title_lower for x in ["closet", "shoe", "jewelry"]):
            return "Closet Organization"
        elif any(x in title_lower for x in ["desk", "office", "cable"]):
            return "Office Organization"
        elif "laundry" in title_lower:
            return "Laundry Organization"
        elif "toy" in title_lower:
            return "Kids Organization"
        return "Home Organization"
    
    async def _create_all_pages(self) -> List[Dict]:
        """Create all store pages - updates existing pages if they exist"""
        if not self.access_token:
            print("   Cannot create pages - no API access")
            return []
        
        import httpx
        
        pages = [
            {
                "title": "About Us",
                "handle": "about-us",
                "body_html": self._get_about_page_content()
            },
            {
                "title": "Contact Us",
                "handle": "contact",
                "body_html": self._get_contact_page_content()
            },
            {
                "title": "Shipping & Returns",
                "handle": "shipping-returns",
                "body_html": self._get_shipping_page_content()
            },
            {
                "title": "FAQ",
                "handle": "faq",
                "body_html": self._get_faq_page_content()
            },
            {
                "title": "Privacy Policy",
                "handle": "privacy-policy",
                "body_html": self._get_privacy_page_content()
            },
            {
                "title": "Terms of Service",
                "handle": "terms-of-service",
                "body_html": self._get_terms_page_content()
            }
        ]
        
        created = []
        
        async with httpx.AsyncClient() as client:
            headers = {
                "X-Shopify-Access-Token": self.access_token,
                "Content-Type": "application/json"
            }
            
            # First, get all existing pages to check for duplicates
            existing_pages = {}
            try:
                list_url = f"https://{self.shop_domain}/admin/api/{self.api_version}/pages.json?limit=250"
                resp = await client.get(list_url, headers=headers)
                if resp.status_code == 200:
                    for p in resp.json().get('pages', []):
                        existing_pages[p.get('handle')] = p.get('id')
            except Exception as e:
                print(f"   Warning: Could not fetch existing pages: {e}")
            
            for page in pages:
                try:
                    # Check if page already exists
                    if page['handle'] in existing_pages:
                        # Update existing page
                        page_id = existing_pages[page['handle']]
                        update_url = f"https://{self.shop_domain}/admin/api/{self.api_version}/pages/{page_id}.json"
                        response = await client.put(update_url, headers=headers, json={"page": page})
                        
                        if response.status_code == 200:
                            created.append(page)
                            print(f"   Updated: {page['title']}")
                        else:
                            print(f"   Failed to update: {page['title']} - Status {response.status_code}")
                    else:
                        # Create new page
                        url = f"https://{self.shop_domain}/admin/api/{self.api_version}/pages.json"
                        response = await client.post(url, headers=headers, json={"page": page})
                        
                        if response.status_code == 201:
                            created.append(page)
                            print(f"   Created: {page['title']}")
                        elif response.status_code == 422 and "handle" in response.text:
                            # Handle race condition - fetch again and update
                            print(f"   Page exists, fetching ID...")
                            resp2 = await client.get(list_url, headers=headers)
                            if resp2.status_code == 200:
                                for p in resp2.json().get('pages', []):
                                    if p.get('handle') == page['handle']:
                                        update_url = f"https://{self.shop_domain}/admin/api/{self.api_version}/pages/{p['id']}.json"
                                        response = await client.put(update_url, headers=headers, json={"page": page})
                                        if response.status_code == 200:
                                            created.append(page)
                                            print(f"   Updated: {page['title']}")
                                        break
                        else:
                            print(f"   Failed: {page['title']} - Status {response.status_code}")
                            print(f"   Error: {response.text[:200] if response.text else 'No response body'}")
                            
                except Exception as e:
                    print(f"   Error: {page['title']} - {e}")
        
        return created
    
    def _get_about_page_content(self) -> str:
        return """<h1>About CoaiHome</h1>
<p>Welcome to CoaiHome - where clutter becomes calm.</p>
<h2>Our Story</h2>
<p>Founded in 2024, CoaiHome was born from a simple mission: to help people transform their living spaces into organized, peaceful sanctuaries. We believe that an organized home leads to an organized mind.</p>
<h2>Why Choose Us?</h2>
<ul>
<li><strong>Premium Quality:</strong> Every product is carefully selected for durability and functionality</li>
<li><strong>Affordable Prices:</strong> Organization shouldn't break the bank</li>
<li><strong>Fast Shipping:</strong> Most orders ship within 24 hours</li>
<li><strong>30-Day Returns:</strong> Not satisfied? Return it for a full refund</li>
</ul>
<h2>Our Promise</h2>
<p>We're not just selling organizers - we're selling peace of mind. When you shop with CoaiHome, you're joining 50,000+ happy customers who have transformed their homes.</p>"""
    
    def _get_contact_page_content(self) -> str:
        return """<h1>Contact Us</h1>
<p>We're here to help! Reach out to us anytime.</p>
<h2>Customer Support</h2>
<p>Email: support@coaihome.com<br>
Phone: 1-800-COAI-HOME<br>
Hours: Monday-Friday, 9AM-5PM EST</p>
<h2>Quick Links</h2>
<ul>
<li><a href="/pages/shipping-returns">Shipping &amp; Returns</a></li>
<li><a href="/pages/faq">Frequently Asked Questions</a></li>
</ul>"""
    
    def _get_shipping_page_content(self) -> str:
        return """<h1>Shipping &amp; Returns</h1>
<h2>Shipping Information</h2>
<p><strong>Free Shipping:</strong> On all orders over $50<br>
<strong>Standard Shipping:</strong> $5.99 (3-5 business days)<br>
<strong>Express Shipping:</strong> $12.99 (1-2 business days)</p>
<h2>Return Policy</h2>
<p>We offer a <strong>30-day money-back guarantee</strong> on all products.</p>
<h2>How to Return</h2>
<ol>
<li>Contact support@coaihome.com with your order number</li>
<li>We'll send you a prepaid return label</li>
<li>Ship the item back</li>
<li>Receive your refund within 5-7 business days</li>
</ol>"""
    
    def _get_faq_page_content(self) -> str:
        return """<h1>Frequently Asked Questions</h1>
<h2>Ordering</h2>
<p><strong>Q: How do I place an order?</strong><br>
A: Simply browse our products, add items to your cart, and checkout securely.</p>
<p><strong>Q: What payment methods do you accept?</strong><br>
A: We accept all major credit cards, PayPal, Apple Pay, and Google Pay.</p>
<h2>Shipping</h2>
<p><strong>Q: How long does shipping take?</strong><br>
A: Standard shipping is 3-5 business days. Express is 1-2 business days.</p>
<h2>Products</h2>
<p><strong>Q: Are your products durable?</strong><br>
A: Yes! We carefully select premium materials that last.</p>"""
    
    def _get_privacy_page_content(self) -> str:
        return """<h1>Privacy Policy</h1>
<p>At CoaiHome, we take your privacy seriously.</p>
<h2>Information We Collect</h2>
<ul>
<li>Name and contact information</li>
<li>Shipping and billing addresses</li>
<li>Payment information (processed securely)</li>
</ul>
<h2>How We Use Your Information</h2>
<p>We use your information to process orders, provide customer support, and send occasional promotional emails.</p>
<h2>Security</h2>
<p>We use industry-standard SSL encryption to protect your data.</p>"""
    
    def _get_terms_page_content(self) -> str:
        return """<h1>Terms of Service</h1>
<p>By using CoaiHome, you agree to these terms and conditions.</p>
<h2>Orders</h2>
<p>All orders are subject to availability and confirmation of payment.</p>
<h2>Products</h2>
<p>We strive to display accurate product information and images.</p>"""
    
    async def _configure_theme(self) -> bool:
        """Configure theme settings with branding (New in 2026)"""
        if not self.access_token:
            return False
            
        print("   Configuring theme branding...")
        import httpx
        headers = {"X-Shopify-Access-Token": self.access_token}
        
        try:
            async with httpx.AsyncClient() as client:
                # 1. Get themes
                resp = await client.get(f"https://{self.shop_domain}/admin/api/{self.api_version}/themes.json", headers=headers)
                themes = resp.json().get("themes", [])
                
                if not themes:
                    print("   [!] No themes found in store.")
                    return False
                
                # Try to brand all themes to be safe
                branded_count = 0
                for theme in themes:
                    theme_id = theme["id"]
                    
                    brand_css = f"""
                    :root {{
                        --color-base-text: #2d2d2d;
                        --color-base-background-1: #ffffff;
                        --color-base-accent-1: #000000;
                    }}
                    .button, .button--primary {{
                        background-color: #000000 !important;
                        color: #ffffff !important;
                    }}
                    """
                    
                    asset_payload = {
                        "asset": {
                            "key": "assets/brand-styles.css",
                            "value": brand_css
                        }
                    }
                    
                    asset_resp = await client.put(
                        f"https://{self.shop_domain}/admin/api/{self.api_version}/themes/{theme_id}/assets.json",
                        headers=headers,
                        json=asset_payload
                    )
                    
                    if asset_resp.status_code == 200:
                        branded_count += 1
                
                print(f"   OK: Applied CoaiHome branding to {branded_count} themes.")
                return True
        except Exception as e:
            print(f"   [!] Theme Branding Error: {e}")
            return False
    
    async def _create_collections(self) -> List[Dict]:
        """Create product collections - updates existing if they exist"""
        if not self.access_token:
            print("   Cannot create collections - no API access")
            return []
        
        import httpx
        
        collections = [
            {"title": "Kitchen Organization", "handle": "kitchen"},
            {"title": "Bathroom Organization", "handle": "bathroom"},
            {"title": "Closet Organization", "handle": "closet"},
            {"title": "Office Organization", "handle": "office"},
            {"title": "All Products", "handle": "all-products"}  # Changed 'all' to avoid conflict
        ]
        
        created = []
        
        async with httpx.AsyncClient() as client:
            headers = {
                "X-Shopify-Access-Token": self.access_token,
                "Content-Type": "application/json"
            }
            
            # First, get all existing collections to check for duplicates
            existing_collections = {}
            try:
                list_url = f"https://{self.shop_domain}/admin/api/{self.api_version}/custom_collections.json?limit=250"
                resp = await client.get(list_url, headers=headers)
                if resp.status_code == 200:
                    for c in resp.json().get('custom_collections', []):
                        existing_collections[c.get('handle')] = c.get('id')
            except Exception as e:
                print(f"   Warning: Could not fetch existing collections: {e}")
            
            for coll in collections:
                try:
                    # Check if collection already exists
                    if coll['handle'] in existing_collections:
                        # Update existing collection
                        coll_id = existing_collections[coll['handle']]
                        update_url = f"https://{self.shop_domain}/admin/api/{self.api_version}/custom_collections/{coll_id}.json"
                        response = await client.put(update_url, headers=headers, json={"custom_collection": coll})
                        
                        if response.status_code == 200:
                            created.append(coll)
                            print(f"   Updated: {coll['title']}")
                        else:
                            print(f"   Failed to update: {coll['title']} - Status {response.status_code}")
                    else:
                        # Create new collection
                        url = f"https://{self.shop_domain}/admin/api/{self.api_version}/custom_collections.json"
                        collection_data = {
                            "custom_collection": {
                                "title": coll["title"],
                                "handle": coll["handle"]
                            }
                        }
                        
                        response = await client.post(url, headers=headers, json=collection_data)
                        
                        if response.status_code == 201:
                            created.append(coll)
                            print(f"   Created: {coll['title']}")
                        elif response.status_code == 422 and "handle" in response.text:
                            # Handle race condition - just skip
                            print(f"   Skipped: {coll['title']} (already exists)")
                        else:
                            print(f"   Failed: {coll['title']} - Status {response.status_code}")
                            print(f"   Error: {response.text[:200] if response.text else 'No response body'}")
                            
                except Exception as e:
                    print(f"   Error: {coll['title']} - {e}")
        
        return created
    
    async def _configure_navigation(self) -> bool:
        """Configure store navigation"""
        if not self.access_token:
            return False
        
        # Navigation requires menu API which needs special setup
        return False


async def main():
    """Run the automatic builder"""
    builder = AutomaticShopifyBuilder()
    results = await builder.build_store()
    
    print()
    print("=" * 70)
    print("BUILD RESULTS")
    print("=" * 70)
    print()
    print(f"Status: {results['status'].upper()}")
    print(f"Products Created: {results['products_created']}")
    print(f"Pages Created: {results['pages_created']}")
    print(f"Theme Customized: {results['theme_customized']}")
    print()
    
    if results['steps_completed']:
        print("Completed:")
        for step in results['steps_completed']:
            print(f"   [OK] {step}")
    
    if results['steps_failed']:
        print()
        print("Failed/Skipped:")
        for step in results['steps_failed']:
            print(f"   [!] {step}")
    
    print()
    print("=" * 70)
    print("NEXT STEPS")
    print("=" * 70)
    print()
    
    if results['status'] == 'completed':
        print("Your store is built! Visit:")
        print(f"   https://{SHOP_DOMAIN}")
    else:
        print("To complete the build:")
        print("1. Use the OAuth flow to get API access")
        print("2. OR use DEPLOY_PACKAGE/ for manual upload")
        print()
        print("Files ready in DEPLOY_PACKAGE/ folder:")
        print("   - shopify_import.csv (upload to Products > Import)")
        print("   - css.txt (copy to Theme > Custom CSS)")
        print("   - pages/ (copy to Online Store > Pages)")


if __name__ == "__main__":
    asyncio.run(main())
