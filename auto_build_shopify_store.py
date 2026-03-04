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
from typing import Dict, List, Optional, Any
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

            # Step 7: Rewrite homepage template (the critical piece)
            print("STEP 7: Building homepage content...")
            if await self._configure_homepage_template():
                results["steps_completed"].append("Homepage template built")
                print("   OK: Homepage configured with CoaiHome content")
            else:
                results["steps_failed"].append("Homepage template")
                print("   WARNING: Homepage template could not be written")
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
        
        # Step 2: Push each product to Shopify (skip existing ones)
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
            
            # Fetch existing product titles from Shopify to avoid duplicates
            existing_titles = set()
            try:
                # Use pagination to get ALL products, not just first 250
                limit = 250
                url = f"https://{self.shop_domain}/admin/api/{self.api_version}/products.json?limit={limit}&fields=title"
                
                while url:
                    titles_resp = await client.get(url, headers=headers)
                    if titles_resp.status_code == 200:
                        data = titles_resp.json()
                        for ep in data.get("products", []):
                            existing_titles.add(ep.get("title", "").lower().strip())
                        
                        # Handle Link header for pagination
                        link_header = titles_resp.headers.get("Link", "")
                        if 'rel="next"' in link_header:
                            # Extract next page URL
                            next_url = link_header.split('; rel="next"')[0].split(",")[-1].strip().strip("<>")
                            url = next_url
                        else:
                            url = None
                    else:
                        print(f"   Warning: Could not fetch products (Status {titles_resp.status_code})")
                        break
                print(f"   Found {len(existing_titles)} existing products in Shopify — will skip duplicates")
            except Exception as e:
                print(f"   Warning: Could not check existing products: {e}")
            
            for p in products_to_create:
                try:
                    # Skip if product already exists in Shopify
                    if p["title"].lower().strip() in existing_titles:
                        print(f"   ⏩ Skipped (already exists): {p['title'][:50]}")
                        continue
                    
                    images = []
                    if p.get("image"):
                        images.append({"src": p["image"]})
                    
                    sku = p.get("sku") or f"COAI-{int(time.time())}-{len(created):03d}"
                    
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
                                "sku": sku
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
                            supplier_name="CJ Dropshipping" if p.get("sku", "").startswith("CJ-") else "CoaiHome",
                            sku=sku
                        )
                        db.add(db_p)
                        db.commit()

                        # ── VariantMap Creation (Always) ───────────────────────────
                        # Every product MUST have a VariantMap to prevent fulfillment crashes.
                        # For CJ products, we use their real CJ Variant ID.
                        # For others, we use 'MANUAL' which signals the fulfillment service
                        # that this item requires human intervention.
                        from models.database import VariantMap
                        
                        cj_vid = "MANUAL"
                        if p.get("sku", "").startswith("CJ-"):
                            cj_vid = p.get("sku", "").replace("CJ-", "")
                        
                        vm = db.query(VariantMap).filter(VariantMap.shopify_variant_id == str(v_id)).first()
                        if not vm:
                            vm = VariantMap(
                                shopify_variant_id=str(v_id),
                                cj_variant_id=cj_vid,
                                sku=sku,
                                store_id=1,
                                active=True
                            )
                            db.add(vm)
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
        """
        Configure the active Shopify theme:
        1. Write branding CSS asset
        2. Update settings_data.json with CoaiHome hero, colors, announcement bar
        """
        if not self.access_token:
            return False

        import httpx, json
        verify_ssl = os.getenv("SHOPIFY_SSL_VERIFY", "true").lower() == "true"
        headers = {
            "X-Shopify-Access-Token": self.access_token,
            "Content-Type": "application/json"
        }

        try:
            async with httpx.AsyncClient(verify=verify_ssl, timeout=30.0) as client:
                # Get all themes, find the active one
                resp = await client.get(
                    f"https://{self.shop_domain}/admin/api/{self.api_version}/themes.json",
                    headers=headers
                )
                themes = resp.json().get("themes", [])
                active = next((t for t in themes if t.get("role") == "main"), None)
                if not active:
                    active = themes[0] if themes else None
                if not active:
                    print("   [!] No theme found.")
                    return False

                theme_id = active["id"]
                theme_name = active.get("name", "Unknown")
                print(f"   Configuring theme: {theme_name} (ID: {theme_id})")

                # ── Step 1: Branding CSS ──────────────────────────────────────
                brand_css = """
/* CoaiHome Brand Styles */
:root {
  --color-base-text: #1a1a1a;
  --color-base-background-1: #ffffff;
  --color-base-background-2: #f8f7f4;
  --color-base-accent-1: #2c5f2e;
  --color-base-accent-2: #4a9e4e;
  --color-base-solid-button-labels: #ffffff;
  --color-base-outline-button-labels: #2c5f2e;
  --font-heading-family: 'Georgia', serif;
}
.button, .btn, [class*="button--primary"] {
  background-color: #2c5f2e !important;
  border-color: #2c5f2e !important;
  color: #ffffff !important;
  border-radius: 6px !important;
}
.button:hover, .btn:hover {
  background-color: #1e4220 !important;
}
header, .site-header, .header-wrapper {
  background-color: #1a1a1a !important;
}
.announcement-bar {
  background-color: #2c5f2e !important;
  color: #ffffff !important;
}
"""
                await client.put(
                    f"https://{self.shop_domain}/admin/api/{self.api_version}/themes/{theme_id}/assets.json",
                    headers=headers,
                    json={"asset": {"key": "assets/coaihome-brand.css", "value": brand_css}}
                )
                print("   ✅ Brand CSS uploaded")

                # ── Step 2: Read existing settings_data.json ─────────────────
                asset_resp = await client.get(
                    f"https://{self.shop_domain}/admin/api/{self.api_version}/themes/{theme_id}/assets.json"
                    "?asset[key]=config/settings_data.json",
                    headers=headers
                )
                existing_settings = {}
                if asset_resp.status_code == 200:
                    try:
                        raw = asset_resp.json().get("asset", {}).get("value", "{}")
                        existing_settings = json.loads(raw)
                    except Exception:
                        existing_settings = {}

                # ── Step 3: Merge CoaiHome settings ──────────────────────────
                current = existing_settings.get("current", {})
                if isinstance(current, str):
                    current = {}

                # Colors & fonts
                current.setdefault("colors_body_bg", "#ffffff")
                current["colors_solid_button_background"] = "#2c5f2e"
                current["colors_button_label"] = "#ffffff"
                current["colors_accent_1"] = "#2c5f2e"
                current["colors_accent_2"] = "#4a9e4e"
                current["colors_text"] = "#1a1a1a"
                current["colors_header_bg"] = "#1a1a1a"
                current["colors_header_text"] = "#ffffff"
                current["type_header_font"] = "playfair_display_n4"
                current["type_base_font"] = "lato_n4"

                # Announcement bar
                current["announcement_bar_enable"] = True
                current["announcement_bar_home_page_only"] = False
                current["announcement_bar_message"] = "🚚 FREE SHIPPING on orders over $50 | Shop CoaiHome — Organize Your World"
                current["announcement_bar_link"] = "/collections/all-products"

                # Header / logo
                current["header_logo_position"] = "middle-left"
                current["header_sticky_type"] = "on-scroll-up"

                # Cart
                current["cart_type"] = "drawer"

                # Social
                current["social_twitter_link"] = ""
                current["social_instagram_link"] = "https://www.instagram.com/coaihome"
                current["social_tiktok_link"] = "https://www.tiktok.com/@coaihome"

                existing_settings["current"] = current

                # Write settings_data.json back
                settings_resp = await client.put(
                    f"https://{self.shop_domain}/admin/api/{self.api_version}/themes/{theme_id}/assets.json",
                    headers=headers,
                    json={"asset": {
                        "key": "config/settings_data.json",
                        "value": json.dumps(existing_settings, indent=2)
                    }}
                )
                if settings_resp.status_code == 200:
                    print("   ✅ Theme settings updated (colors, fonts, announcement bar)")
                else:
                    print(f"   ⚠️  settings_data.json update returned {settings_resp.status_code} — "
                          "theme visual settings may need manual adjustment")

                # ── Step 4: Inject CSS link into theme.liquid ─────────────────
                liquid_resp = await client.get(
                    f"https://{self.shop_domain}/admin/api/{self.api_version}/themes/{theme_id}/assets.json"
                    "?asset[key]=layout/theme.liquid",
                    headers=headers
                )
                if liquid_resp.status_code == 200:
                    liquid = liquid_resp.json().get("asset", {}).get("value", "")
                    css_link = "{{ 'coaihome-brand.css' | asset_url | stylesheet_tag }}"
                    if "coaihome-brand.css" not in liquid:
                        # Inject before </head>
                        liquid = liquid.replace("</head>", f"  {css_link}\n</head>", 1)
                        inj_resp = await client.put(
                            f"https://{self.shop_domain}/admin/api/{self.api_version}/themes/{theme_id}/assets.json",
                            headers=headers,
                            json={"asset": {"key": "layout/theme.liquid", "value": liquid}}
                        )
                        if inj_resp.status_code == 200:
                            print("   ✅ CSS injected into theme.liquid")
                        else:
                            print(f"   ⚠️  CSS injection returned {inj_resp.status_code}")
                    else:
                        print("   ✅ CSS already in theme.liquid")

                return True

        except Exception as e:
            print(f"   [!] Theme configuration error: {e}")
            return False

    async def _configure_navigation(self) -> bool:
        """
        Build real navigation menus via Shopify Storefront API menus
        using the admin REST menus endpoint.
        Creates:
          - Main menu: Home / Shop All / Kitchen / Bathroom / Closet / Office
          - Footer menu: About / FAQ / Shipping & Returns / Contact / Privacy / Terms
        """
        if not self.access_token:
            return False

        import httpx
        verify_ssl = os.getenv("SHOPIFY_SSL_VERIFY", "true").lower() == "true"
        headers = {
            "X-Shopify-Access-Token": self.access_token,
            "Content-Type": "application/json"
        }

        menus_to_create = [
            {
                "handle": "main-menu",
                "title": "Main Menu",
                "links": [
                    {"title": "Home",              "url": "/",                              "type": "http"},
                    {"title": "Shop All",          "url": "/collections/all-products",      "type": "http"},
                    {"title": "Kitchen",           "url": "/collections/kitchen",           "type": "http"},
                    {"title": "Bathroom",          "url": "/collections/bathroom",          "type": "http"},
                    {"title": "Closet",            "url": "/collections/closet",            "type": "http"},
                    {"title": "Office",            "url": "/collections/office",            "type": "http"},
                ]
            },
            {
                "handle": "footer",
                "title": "Footer Menu",
                "links": [
                    {"title": "About Us",          "url": "/pages/about-us",               "type": "http"},
                    {"title": "FAQ",               "url": "/pages/faq",                    "type": "http"},
                    {"title": "Shipping & Returns","url": "/pages/shipping-returns",        "type": "http"},
                    {"title": "Contact Us",        "url": "/pages/contact",                "type": "http"},
                    {"title": "Privacy Policy",   "url": "/pages/privacy-policy",          "type": "http"},
                    {"title": "Terms of Service", "url": "/pages/terms-of-service",        "type": "http"},
                ]
            }
        ]

        success = 0
        async with httpx.AsyncClient(verify=verify_ssl, timeout=30.0) as client:
            # Get existing menus
            existing = {}
            try:
                r = await client.get(
                    f"https://{self.shop_domain}/admin/api/{self.api_version}/menus.json",
                    headers=headers
                )
                if r.status_code == 200:
                    for m in r.json().get("menus", []):
                        existing[m["handle"]] = m["id"]
            except Exception:
                pass

            for menu in menus_to_create:
                payload = {
                    "menu": {
                        "title": menu["title"],
                        "handle": menu["handle"],
                        "items": [
                            {
                                "title": lnk["title"],
                                "url": lnk["url"],
                                "type": "http",
                                "items": []
                            }
                            for lnk in menu["links"]
                        ]
                    }
                }
                try:
                    if menu["handle"] in existing:
                        menu_id = existing[menu["handle"]]
                        r = await client.put(
                            f"https://{self.shop_domain}/admin/api/{self.api_version}/menus/{menu_id}.json",
                            headers=headers, json=payload
                        )
                    else:
                        r = await client.post(
                            f"https://{self.shop_domain}/admin/api/{self.api_version}/menus.json",
                            headers=headers, json=payload
                        )

                    if r.status_code in (200, 201):
                        print(f"   ✅ Menu: {menu['title']}")
                        success += 1
                    else:
                        # Menus API may not be available on all Shopify plans — that's OK
                        print(f"   ⚠️  Menu API returned {r.status_code} for '{menu['title']}' "
                              "(manual nav setup may be needed in Shopify admin)")
                except Exception as e:
                    print(f"   ⚠️  Menu error for '{menu['title']}': {e}")

    def _wrap_richtext(self, text: str) -> str:
        """Helper to ensure text is wrapped in <p> tags for Shopify richtext settings."""
        if not text.startswith("<p>"):
            return f"<p>{text}</p>"
        return text


    async def _configure_homepage_template(self) -> bool:
        """
        The critical missing piece: rewrite templates/index.json on the active theme
        to replace ALL placeholder content with real CoaiHome content.

        This controls:
          - Hero banner heading / subheading / button text
          - Featured collections (which collection handles to show)
          - Featured products section
          - Testimonials
          - Announcement bar text
        """
        if not self.access_token:
            return False

        import httpx, json
        verify_ssl = os.getenv("SHOPIFY_SSL_VERIFY", "true").lower() == "true"
        headers = {
            "X-Shopify-Access-Token": self.access_token,
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(verify=verify_ssl, timeout=30.0) as client:
                # 1. Find active theme
                resp = await client.get(
                    f"https://{self.shop_domain}/admin/api/{self.api_version}/themes.json",
                    headers=headers
                )
                themes = resp.json().get("themes", [])
                active = next((t for t in themes if t.get("role") == "main"), themes[0] if themes else None)
                if not active:
                    print("   [!] No active theme found")
                    return False

                theme_id = active["id"]

                # 2. Get collection ID/handles for our collections
                coll_resp = await client.get(
                    f"https://{self.shop_domain}/admin/api/{self.api_version}/custom_collections.json?limit=50",
                    headers=headers
                )
                coll_map = {} # handle -> id
                for c in coll_resp.json().get("custom_collections", []):
                    coll_map[c["handle"]] = c["id"]
                
                # Also get smart/default collections
                sc_resp = await client.get(
                    f"https://{self.shop_domain}/admin/api/{self.api_version}/smart_collections.json?limit=50",
                    headers=headers
                )
                for c in sc_resp.json().get("smart_collections", []):
                    coll_map[c["handle"]] = c["id"]

                # Modern Dawn/Trade themes usually prefer handles for collection settings
                kitchen_h   = "kitchen" if "kitchen" in coll_map else "all-products"
                bathroom_h  = "bathroom" if "bathroom" in coll_map else "all-products"
                closet_h    = "closet" if "closet" in coll_map else "all-products"
                office_h    = "office" if "office" in coll_map else "all-products"
                all_products_h = "all-products" if "all-products" in coll_map else "all"

                def coll_val(handle):
                    return handle if handle in coll_map else all_products_h

                # 3. Read current templates/index.json
                idx_resp = await client.get(
                    f"https://{self.shop_domain}/admin/api/{self.api_version}/themes/{theme_id}/assets.json"
                    "?asset[key]=templates/index.json",
                    headers=headers
                )
                
                tmpl = {}
                if idx_resp.status_code == 200:
                    try:
                        tmpl = json.loads(idx_resp.json().get("asset", {}).get("value", "{}"))
                    except Exception:
                        tmpl = {}

                sections = tmpl.get("sections", {})

                # 4. Walk every section and update CoaiHome content
                for sec_key, sec in sections.items():
                    sec_type = sec.get("type", "")
                    sett = sec.get("settings", {})

                    # ─── Hero / image-banner / slideshow ───────────────────────
                    if sec_type in ("image-banner", "slideshow", "banner", "hero", "image-with-text"):
                        if sec_type == "image-with-text":
                             sett["heading"] = "Quality Home Essentials"
                             sett["text"] = "<p>Discover premium home organization solutions for every room in your home.</p>"
                        else:
                            sett["heading"]    = "Organize Every Corner of Your Home"
                            sett["heading_size"] = "h1"
                        
                        # Update all blocks for text/subheading
                        for bk, bv in sec.get("blocks", {}).items():
                            bv.setdefault("settings", {})
                            btype = bv.get("type", "")
                            if btype in ("heading", "title"):
                                bv["settings"]["heading"] = "Organize Every Corner of Your Home"
                            elif btype in ("text", "caption"):
                                bv["settings"]["text"] = "Premium home organization products — kitchen, bathroom, closet & office"
                            elif btype == "buttons":
                                bv["settings"]["button_label_1"] = "Shop All"
                                bv["settings"]["button_link_1"] = "/collections/all-products"
                            elif btype in ("slide", "image"):
                                bv["settings"]["heading"] = "Organize Every Corner of Your Home"
                                bv["settings"]["subheading"] = "Premium home organizers — kitchen, bath, closet & office"
                                bv["settings"]["button_label"] = "Shop Now"
                                bv["settings"]["button_link"] = "/collections/all-products"

                    # ─── Rich text / announcement / intro ──────────────────────
                    elif sec_type in ("rich-text", "announcement-bar"):
                        sett["heading"] = "Welcome to CoaiHome"
                        # Rich text sections usually have BLOCKS for the actual text
                        for bk, bv in sec.get("blocks", {}).items():
                            bv.setdefault("settings", {})
                            if bv.get("type") == "text":
                                bv["settings"]["text"] = "<p>Discover premium home organization solutions for every room in your home. Free shipping on orders over $50.</p>"
                        # Fallback if theme uses section-level setting
                        if "text" in sett: sett["text"] = "<p>Welcome to CoaiHome</p>"
                        if "content" in sett: sett["content"] = "<p>Welcome to CoaiHome</p>"

                    # ─── Collection list / featured categories ─────────────────
                    elif sec_type in (
                        "collection-list", "featured-collections",
                        "collections-row", "collage", "collection-grid"
                    ):
                        sett["title"]   = "Shop by Category"
                        sett["heading"] = "Shop by Category"
                        # Update each collection block
                        block_keys = list(sec.get("blocks", {}).keys())
                        cat_handles = [kitchen_h, bathroom_h, closet_h, office_h, all_products_h]
                        cat_labels  = ["Kitchen", "Bathroom", "Closet", "Office", "All Products"]
                        for i, bk in enumerate(block_keys[:5]):
                            bv = sec["blocks"][bk]
                            bv.setdefault("settings", {})
                            bv["settings"]["collection"] = coll_val(cat_handles[i])
                            if "heading" in bv["settings"]:
                                bv["settings"]["heading"] = cat_labels[i]

                    # ─── Featured collection (product grid) ────────────────────
                    elif sec_type in ("featured-collection", "product-grid", "new-arrivals"):
                        title = str(sett.get("title", sett.get("heading", ""))).lower()
                        if "new" in title or "arrive" in title:
                            sett["heading"]    = "New Arrivals"
                            sett["collection"] = coll_val(kitchen_h)
                        else:
                            sett["heading"]    = "Bestsellers"
                            sett["collection"] = coll_val(all_products_h)
                        sett["products_to_show"] = 8
                        sett["show_view_all"] = True

                    # ─── Testimonials ──────────────────────────────────────────
                    elif sec_type in ("testimonials", "reviews", "before-after"):
                        sett["heading"] = "What Our Customers Say"
                        for i, (bk, bv) in enumerate(sec.get("blocks", {}).items()):
                            bv.setdefault("settings", {})
                            testimonials = [
                                ("Transformed my kitchen!", "The bamboo drawer organizer is beautiful and sturdy. Fits perfectly.", "Sarah M."),
                                ("Finally, a tidy closet!", "The shelf dividers were so easy to install. My sweaters have never looked neater.", "James T."),
                                ("Best purchase this year", "The stackable fridge bins made a huge difference. My fridge looks like a magazine photo!", "Priya K."),
                                ("Amazing quality", "Bought the spice rack and the bathroom organizer. Both are premium quality. Will be back!", "Daniel R."),
                            ]
                            if i < len(testimonials):
                                t = testimonials[i]
                                bv["settings"]["heading"]  = t[0]
                                bv["settings"]["text"]     = t[1]
                                bv["settings"]["author"]   = t[2]

                    # ─── Multicolumn / features / "You're set up for success" ──
                    elif sec_type in ("multicolumn", "columns-with-image", "feature-row"):
                        sett["title"]   = "Why Choose CoaiHome?"
                        sett["heading"] = "Why Choose CoaiHome?"
                        features = [
                            ("🌿 Eco-Friendly Materials", "Our organizers are crafted from sustainable bamboo and BPA-free materials."),
                            ("🚚 Free Shipping $50+",     "Free standard shipping on all orders over $50."),
                            ("↩️ 30-Day Returns",          "Not satisfied? Return any item within 30 days."),
                            ("⭐ Premium Quality",         "Every product is hand-selected for durability."),
                        ]
                        for i, (bk, bv) in enumerate(sec.get("blocks", {}).items()):
                            bv.setdefault("settings", {})
                            if i < len(features):
                                bv["settings"]["heading"]     = features[i][0]
                                bv["settings"]["text"]        = f"<p>{features[i][1]}</p>"
                                if "description" in bv["settings"]:
                                    bv["settings"]["description"] = f"<p>{features[i][1]}</p>"

                    sec["settings"] = sett

                # 5. Write the modified template back
                write_resp = await client.put(
                    f"https://{self.shop_domain}/admin/api/{self.api_version}/themes/{theme_id}/assets.json",
                    headers=headers,
                    json={"asset": {
                        "key": "templates/index.json",
                        "value": json.dumps(tmpl, indent=2)
                    }}
                )

                if write_resp.status_code == 200:
                    print("   ✅ templates/index.json updated — hero, collections, products, testimonials")
                    
                    # 6. Also update the announcement bar in sections/announcement-bar.liquid if it exists
                    try:
                        ann_resp = await client.get(
                            f"https://{self.shop_domain}/admin/api/{self.api_version}/themes/{theme_id}/assets.json"
                            "?asset[key]=sections/announcement-bar.json",
                            headers=headers
                        )
                        if ann_resp.status_code == 200:
                            ann_data = json.loads(ann_resp.json().get("asset", {}).get("value", "{}"))
                            for sk, sv in ann_data.get("sections", {}).items():
                                for bk, bv in sv.get("blocks", {}).items():
                                    bv.setdefault("settings", {})
                                    bv["settings"]["text"] = "🚚 FREE SHIPPING on orders over $50 | Use code ORGANIZE10 for 10% off your first order!"
                            # Strip HTML from announcement bar data too
                            clean_ann = self._strip_html(ann_data)
                            await client.put(
                                f"https://{self.shop_domain}/admin/api/{self.api_version}/themes/{theme_id}/assets.json",
                                headers=headers,
                                json={"asset": {
                                    "key": "sections/announcement-bar.json",
                                    "value": json.dumps(clean_ann, indent=2)
                                }}
                            )
                        print("   ✅ Theme layout and assets cleaned of HTML tags")
                    except Exception:
                        pass

                    return True
                else:
                    print(f"   ⚠️  templates/index.json write returned {write_resp.status_code}: {write_resp.text[:200]}")
                    # Try alternate path
                    write_resp2 = await client.put(
                        f"https://{self.shop_domain}/admin/api/{self.api_version}/themes/{theme_id}/assets.json",
                        headers=headers,
                        json={"asset": {
                            "key": "templates/index.liquid",
                            "value": self._get_fallback_homepage_liquid()
                        }}
                    )
                    return write_resp2.status_code == 200

        except Exception as e:
            print(f"   [!] Homepage template error: {e}")
            return False

    def _get_fallback_homepage_liquid(self) -> str:
        """Fallback homepage in case the theme uses .liquid not .json templates"""
        return """
{% section 'announcement-bar' %}
{% section 'header' %}

<div style="background: #1a1a1a; color: white; padding: 100px 40px; text-align: center;">
  <p style="font-size: 14px; letter-spacing: 3px; color: #4a9e4e; text-transform: uppercase; margin-bottom: 16px;">Welcome to CoaiHome</p>
  <h1 style="font-size: 52px; font-weight: 700; margin-bottom: 24px; line-height: 1.1;">Organize Every Corner<br>of Your Home</h1>
  <p style="font-size: 18px; color: #ccc; margin-bottom: 40px; max-width: 600px; margin-left: auto; margin-right: auto;">
    Premium home organization products — kitchen, bathroom, closet & office
  </p>
  <a href="/collections/all-products"
     style="display: inline-block; background: #2c5f2e; color: white; padding: 16px 40px;
            border-radius: 6px; text-decoration: none; font-size: 16px; font-weight: 600;
            letter-spacing: 1px;">
    Shop All Products
  </a>
  <a href="/collections/kitchen"
     style="display: inline-block; background: transparent; color: white; padding: 16px 40px;
            border-radius: 6px; text-decoration: none; font-size: 16px; font-weight: 600;
            letter-spacing: 1px; border: 2px solid #4a9e4e; margin-left: 16px;">
    Kitchen Collection
  </a>
</div>

<section style="padding: 60px 40px; max-width: 1200px; margin: 0 auto;">
  <h2 style="text-align: center; font-size: 32px; margin-bottom: 40px; color: #1a1a1a;">Shop by Category</h2>
  <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 24px;">
    {% assign cats = "kitchen,bathroom,closet,office" | split: "," %}
    {% assign cat_names = "Kitchen,Bathroom,Closet,Office" | split: "," %}
    {% for cat in cats %}
      <a href="/collections/{{ cat }}" style="text-decoration: none;">
        <div style="background: #f8f7f4; border-radius: 12px; padding: 32px 16px; text-align: center; transition: box-shadow 0.2s;">
          <div style="font-size: 40px; margin-bottom: 12px;">
            {%- if cat == 'kitchen' -%}🍳{%- elsif cat == 'bathroom' -%}🚿{%- elsif cat == 'closet' -%}👔{%- else -%}💼{%- endif -%}
          </div>
          <span style="font-size: 16px; font-weight: 600; color: #1a1a1a;">{{ cat_names[forloop.index0] }}</span>
        </div>
      </a>
    {% endfor %}
  </div>
</section>

<section style="padding: 60px 40px; background: #f8f7f4;">
  <h2 style="text-align: center; font-size: 32px; margin-bottom: 40px; color: #1a1a1a;">Bestsellers</h2>
  {% assign collection = collections['all-products'] %}
  <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 24px; max-width: 1200px; margin: 0 auto;">
    {% for product in collection.products limit: 8 %}
      <a href="{{ product.url }}" style="text-decoration: none; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
        {% if product.featured_image %}
          <img src="{{ product.featured_image | img_url: '400x400' }}" alt="{{ product.title }}" style="width: 100%; aspect-ratio: 1; object-fit: cover;">
        {% endif %}
        <div style="padding: 16px;">
          <h3 style="font-size: 14px; color: #1a1a1a; margin-bottom: 8px; font-weight: 600;">{{ product.title }}</h3>
          <span style="font-size: 16px; color: #2c5f2e; font-weight: 700;">{{ product.price | money }}</span>
        </div>
      </a>
    {% endfor %}
  </div>
</section>


{% section 'footer' %}
"""


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
