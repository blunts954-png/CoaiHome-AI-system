"""
🚀 START YOUR CJ DROPSHIPPING BUSINESS
One-click startup with CJ Dropshipping API!
"""
import subprocess
import sys
import os
import time
import asyncio
import webbrowser


def _configure_utf8_console():
    """Avoid UnicodeEncodeError on Windows cp1252 consoles."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass


_configure_utf8_console()


# Change to script directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))


def print_banner():
    """Print startup banner"""
    print("=" * 70)
    print("   🚀 CJ DROPSHIPPING AI AUTOMATION SYSTEM")
    print("=" * 70)
    print()
    print("   💰 Features:")
    print("      • Automated product research with CJ API")
    print("      • AI-powered product import to Shopify")
    print("      • Smart pricing optimization")
    print("      • TikTok content generation")
    print("      • 24/7 automation scheduler")
    print()
    print("=" * 70)
    print()


def check_cj_configuration():
    """Check if CJ Dropshipping API is configured"""
    from config.settings import settings
    
    print("🔍 Checking CJ Dropshipping configuration...")
    print()
    
    # Check CJ API token
    if not settings.cj.api_token or settings.cj.api_token == "your_cj_api_token":
        print("❌ CJ_API_TOKEN not configured!")
        print()
        print("To get your CJ API token:")
        print("   1. Log into CJ Dropshipping: https://cjdropshipping.com/")
        print("   2. Go to Profile → API Authorization")
        print("   3. Generate an API token")
        print("   4. Add it to your .env file: CJ_API_TOKEN=your_token_here")
        print()
        return False
    
    # Check if CJ is set as supplier platform
    if settings.system.supplier_platform != "cj":
        print(f"⚠️  Supplier platform is set to: {settings.system.supplier_platform}")
        print("   To use CJ Dropshipping, set in your .env file:")
        print("   SYSTEM_SUPPLIER_PLATFORM=cj")
        print()
        return False
    
    print("✅ CJ API Token configured")
    print(f"   Base URL: {settings.cj.base_url}")
    print()
    return True


def check_shopify_configuration():
    """Check if Shopify is configured"""
    from config.settings import settings
    
    print("🔍 Checking Shopify configuration...")
    print()
    
    if not settings.shopify.shop_url or settings.shopify.shop_url == "your-store.myshopify.com":
        print("❌ Shopify not configured!")
        print()
        print("Add to your .env file:")
        print("   SHOPIFY_SHOP_URL=yourstore.myshopify.com")
        print("   SHOPIFY_ACCESS_TOKEN=your_admin_api_token")
        print()
        print("To get your access token:")
        print("   1. Shopify Admin → Settings → Apps and sales channels")
        print("   2. Develop apps → Create an app")
        print("   3. Configuration → Admin API access scopes")
        print("   4. Install app → Reveal token once")
        print()
        return False
    
    if not settings.shopify.access_token:
        print("❌ Shopify access token not configured!")
        return False
    
    print(f"✅ Shopify configured: {settings.shopify.shop_url}")
    print()
    return True


def check_ai_configuration():
    """Check if AI is configured"""
    from config.settings import settings
    
    print("🔍 Checking AI configuration...")
    print()
    
    if not settings.ai.api_key or "your" in settings.ai.api_key.lower():
        print("❌ AI API key not configured!")
        print()
        print("Add to your .env file:")
        print("   AI_API_KEY=your_openai_api_key")
        print("   Get from: https://platform.openai.com/api-keys")
        print()
        return False
    
    print(f"✅ AI configured: {settings.ai.provider} ({settings.ai.model})")
    print()
    return True


async def test_cj_connection():
    """Test CJ API connection"""
    from api_clients.cj_dropshipping_client import get_cj_client
    
    print("🌐 Testing CJ Dropshipping API connection...")
    print()
    
    try:
        client = get_cj_client()
        
        # Try to get account info
        account_info = await client.get_account_info()
        
        if account_info.get("result"):
            data = account_info.get("data", {})
            print("✅ CJ API connection successful!")
            print(f"   Account: {data.get('email', 'N/A')}")
            print()
            return True
        else:
            print("❌ CJ API authentication failed!")
            print(f"   Error: {account_info.get('message', 'Unknown error')}")
            print()
            return False
            
    except Exception as e:
        print(f"❌ CJ API connection error: {e}")
        print()
        return False


async def test_shopify_connection():
    """Test Shopify connection"""
    from api_clients.shopify_client import get_shopify_client
    
    print("🌐 Testing Shopify connection...")
    print()
    
    try:
        shopify = get_shopify_client()
        shop_info = await shopify.get_shop_info()
        
        shop = shop_info.get("shop", {})
        print("✅ Shopify connection successful!")
        print(f"   Store: {shop.get('name', 'N/A')}")
        print(f"   Domain: {shop.get('domain', 'N/A')}")
        print(f"   Plan: {shop.get('plan_name', 'N/A')}")
        print()
        return True
        
    except Exception as e:
        print(f"❌ Shopify connection error: {e}")
        print()
        return False


async def run_initial_setup():
    """Run initial business setup with CJ"""
    from automation.full_automation import get_full_automation
    
    print("🚀 Running initial business setup...")
    print()
    
    auto = get_full_automation()
    
    # Test Shopify connection
    try:
        shop_info = await auto.shopify.get_shop_info()
        print(f"✅ Shopify connected: {shop_info.get('shop', {}).get('name')}")
    except Exception as e:
        print(f"❌ Shopify connection failed: {e}")
        return False
    
    # Research initial products using CJ
    print()
    print("🔍 Researching products with CJ Dropshipping...")
    try:
        from api_clients.autods_client import get_autods_client
        autods = get_autods_client()
        
        # Search for trending products in the niche
        niche = settings.store.niche or "home organization"
        products = await autods.search_products(niche, {"limit": 20})
        
        product_list = products.get("products", [])
        print(f"✅ Found {len(product_list)} products from CJ Dropshipping")
        
        if product_list:
            print()
            print("   Top products found:")
            for i, p in enumerate(product_list[:5], 1):
                print(f"   {i}. {p.get('title', 'N/A')[:50]}...")
                print(f"      Cost: ${p.get('cost_price', 0):.2f}")
        
    except Exception as e:
        print(f"⚠️  Product research warning: {e}")
    
    # Create TikTok content calendar
    print()
    print("🎬 Creating TikTok content calendar...")
    try:
        result = await auto.content.auto_create_content_for_store()
        print(f"✅ Created {result.get('content_pieces', 0)} content pieces")
    except Exception as e:
        print(f"⚠️  Content calendar warning: {e}")
    
    print()
    print("✅ Setup complete!")
    return True


def start_server():
    """Start the web server"""
    print()
    print("=" * 70)
    print("🌐 STARTING WEB SERVER...")
    print("=" * 70)
    print()
    print("   Dashboard: http://localhost:8000")
    print("   API Docs:  http://localhost:8000/docs")
    print()
    print("   Press Ctrl+C to stop")
    print()
    print("=" * 70)
    print()
    
    # Start server
    try:
        subprocess.run([sys.executable, "main.py"])
    except KeyboardInterrupt:
        print()
        print("\n🛑 Server stopped")
        print()
        print("=" * 70)
        print("   Thanks for using CJ Dropshipping AI Automation!")
        print("=" * 70)


async def main_async():
    """Main async entry point"""
    print_banner()
    
    # Check configurations
    if not check_cj_configuration():
        print("\n❌ Please configure CJ Dropshipping and try again.")
        input("\nPress Enter to exit...")
        return
    
    if not check_shopify_configuration():
        print("\n❌ Please configure Shopify and try again.")
        input("\nPress Enter to exit...")
        return
    
    if not check_ai_configuration():
        print("\n❌ Please configure AI and try again.")
        input("\nPress Enter to exit...")
        return
    
    # Test connections
    cj_ok = await test_cj_connection()
    if not cj_ok:
        print("⚠️  CJ API test failed. Continuing in limited mode...")
        print()
    
    shopify_ok = await test_shopify_connection()
    if not shopify_ok:
        print("❌ Shopify connection failed. Please check your credentials.")
        input("\nPress Enter to exit...")
        return
    
    # Run setup
    await run_initial_setup()
    
    # Ask user what to do next
    print()
    print("=" * 70)
    print("   WHAT WOULD YOU LIKE TO DO?")
    print("=" * 70)
    print()
    print("   1. Start web dashboard (manage products, pricing, exceptions)")
    print("   2. Start 24/7 automation (runs in background)")
    print("   3. Run one-time product research")
    print("   4. Exit")
    print()
    
    choice = input("   Enter choice (1-4): ").strip()
    
    if choice == "1":
        # Open browser after 3 seconds
        def open_browser():
            time.sleep(3)
            webbrowser.open('http://localhost:8000')
        
        import threading
        browser_thread = threading.Thread(target=open_browser, daemon=True)
        browser_thread.start()
        
        start_server()
        
    elif choice == "2":
        print()
        print("🤖 Starting 24/7 automation...")
        print()
        
        from automation.full_automation import get_full_automation
        auto = get_full_automation()
        
        # Run all tasks now first
        results = await auto.run_all_now()
        
        print()
        print("✅ Initial run complete!")
        print()
        
        # Start scheduler
        auto.start_scheduler()
        
    elif choice == "3":
        print()
        print("🔍 Running product research...")
        print()
        
        from api_clients.autods_client import get_autods_client
        autods = get_autods_client()
        
        niche = input(f"   Enter niche (default: {settings.store.niche or 'home organization'}): ").strip()
        if not niche:
            niche = settings.store.niche or "home organization"
        
        try:
            products = await autods.search_products(niche, {"limit": 20})
            product_list = products.get("products", [])
            
            print()
            print(f"✅ Found {len(product_list)} products:")
            print()
            
            for i, p in enumerate(product_list, 1):
                cost = p.get('cost_price', 0)
                suggested = cost * 2.5
                margin = ((suggested - cost) / suggested * 100) if suggested else 0
                
                print(f"   {i}. {p.get('title', 'N/A')[:60]}")
                print(f"      Cost: ${cost:.2f} | Suggested: ${suggested:.2f} | Margin: {margin:.1f}%")
                print()
                
        except Exception as e:
            print(f"❌ Research failed: {e}")
        
        input("\nPress Enter to exit...")
        
    else:
        print()
        print("Goodbye! 👋")


def main():
    """Main entry point"""
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        print()
        print("\n🛑 Interrupted by user")
        print("Goodbye! 👋")


if __name__ == "__main__":
    # Add current directory to path for imports
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    # Load settings
    from config.settings import settings
    
    main()
