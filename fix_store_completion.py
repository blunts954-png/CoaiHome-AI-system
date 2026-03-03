"""
Fix missing pages and navigation
"""
import asyncio
import httpx
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.settings import settings


async def create_missing_pages():
    """Create About Us and Contact Us pages"""
    
    token = settings.shopify.access_token
    shop = settings.shopify.shop_url
    
    print("=" * 60)
    print("CREATING MISSING PAGES")
    print("=" * 60)
    print()
    
    headers = {
        "X-Shopify-Access-Token": token,
        "Content-Type": "application/json"
    }
    
    pages = [
        {
            "title": "About Us",
            "handle": "about-us",
            "body_html": """<h1>About CoaiHome</h1>
<p>Welcome to CoaiHome - where clutter becomes calm.</p>
<p>Founded in 2024, we help 50,000+ customers transform their homes with premium, affordable organizers.</p>
<h2>Why Choose Us?</h2>
<ul>
<li><strong>Premium Quality:</strong> Carefully selected for durability</li>
<li><strong>Affordable Prices:</strong> Organization shouldn't break the bank</li>
<li><strong>Fast Shipping:</strong> Most orders ship within 24 hours</li>
<li><strong>30-Day Returns:</strong> Not satisfied? Full refund</li>
</ul>
<p><strong>Join the organization revolution today!</strong></p>"""
        },
        {
            "title": "Contact Us",
            "handle": "contact",
            "body_html": """<h1>Contact Us</h1>
<p>We are here to help!</p>
<h2>Customer Support</h2>
<p>Email: support@coaihome.com<br>
Phone: 1-800-COAI-HOME<br>
Hours: Monday-Friday, 9AM-5PM EST</p>
<h2>Quick Links</h2>
<ul>
<li><a href="/pages/shipping-returns">Shipping & Returns</a></li>
<li><a href="/pages/faq">FAQ</a></li>
</ul>"""
        }
    ]
    
    created = []
    
    async with httpx.AsyncClient() as client:
        for page_data in pages:
            try:
                url = f"https://{shop}/admin/api/2024-01/pages.json"
                payload = {"page": page_data}
                
                resp = await client.post(url, headers=headers, json=payload, timeout=10)
                
                if resp.status_code == 201:
                    print(f"OK: {page_data['title']} page created")
                    created.append(page_data['title'])
                elif resp.status_code == 422:
                    # Page might already exist
                    print(f"Note: {page_data['title']} may already exist (422)")
                else:
                    print(f"Failed: {page_data['title']} - {resp.status_code}")
                    
            except Exception as e:
                print(f"Error creating {page_data['title']}: {e}")
    
    return created


async def setup_navigation():
    """Setup navigation menus via API"""
    
    token = settings.shopify.access_token
    shop = settings.shopify.shop_url
    
    print()
    print("=" * 60)
    print("SETTING UP NAVIGATION")
    print("=" * 60)
    print()
    
    headers = {
        "X-Shopify-Access-Token": token,
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        # Try to get menu list
        try:
            url = f"https://{shop}/admin/api/2024-01/menus.json"
            resp = await client.get(url, headers=headers, timeout=10)
            print(f"Menu API response: {resp.status_code}")
            
            if resp.status_code == 200:
                data = resp.json()
                menus = data.get("menus", [])
                print(f"Found {len(menus)} menus")
                
                for menu in menus:
                    handle = menu.get("handle", "unknown")
                    title = menu.get("title", "Untitled")
                    print(f"  - {handle}: {title}")
                    
                    # If main-menu exists, update it
                    if handle == "main-menu":
                        print(f"\n  Updating main-menu...")
                        # Menu updates are complex via API
                        print("  (Menu updates require manual configuration)")
                        
        except Exception as e:
            print(f"Navigation setup error: {e}")
    
    print()
    print("Navigation Menu Structure (create manually):")
    print("  Main Menu:")
    print("    - Home -> /")
    print("    - Shop All -> /collections/all")
    print("    - Kitchen -> /collections/kitchen")
    print("    - Bathroom -> /collections/bathroom")
    print("    - Closet -> /collections/closet")
    print("    - Office -> /collections/office")
    print("    - About Us -> /pages/about-us")
    print("    - Contact -> /pages/contact")
    print()
    print("  Footer Menu:")
    print("    - Shipping & Returns -> /pages/shipping-returns")
    print("    - FAQ -> /pages/faq")
    print("    - Privacy Policy -> /pages/privacy-policy")
    print("    - Terms -> /pages/terms-of-service")


async def main():
    """Main function"""
    
    # Create missing pages
    pages = await create_missing_pages()
    
    # Setup navigation info
    await setup_navigation()
    
    print()
    print("=" * 60)
    print("COMPLETION STATUS")
    print("=" * 60)
    print()
    print(f"Pages created/fixed: {len(pages)}")
    print()
    print("Navigation: See structure above - create in Shopify Admin:")
    print("  Online Store -> Navigation")
    print()
    print("Theme colors: Online Store -> Themes -> Customize")
    print("  Primary: #2563EB")
    print("  Secondary: #F97316")
    print("  Success: #10B981")
    print()


if __name__ == "__main__":
    asyncio.run(main())
