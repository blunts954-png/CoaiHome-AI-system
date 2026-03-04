import asyncio
import os
import sys
from auto_build_shopify_store import AutomaticShopifyBuilder

async def test_theme_update():
    print("🏗️ Testing Shopify Theme Template Update (HTML Stripping Fix)...")
    builder = AutomaticShopifyBuilder()
    
    # We need to manually initialize or get token for the test
    print("   Authenticating...")
    if not await builder._get_access_token():
        print("❌ Authentication failed. Check settings.py credentials.")
        return

    print("   Running template configuration...")
    success = await builder._configure_homepage_template()
    if success:
        print("✅ Theme template updated successfully! No 422 errors.")
    else:
        print("❌ Theme template update failed.")

if __name__ == "__main__":
    asyncio.run(test_theme_update())
