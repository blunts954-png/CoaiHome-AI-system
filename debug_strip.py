import asyncio
import os
import json
from auto_build_shopify_store import AutomaticShopifyBuilder

async def test_theme_update_debug():
    print("🏗️ Testing Shopify Theme Template Update (Debug Mode)...")
    builder = AutomaticShopifyBuilder()
    
    if not await builder._get_access_token():
        print("❌ Authentication failed.")
        return

    # Mocking the _configure_homepage_template to see clean_tmpl
    import httpx
    verify_ssl = os.getenv("SHOPIFY_SSL_VERIFY", "true").lower() == "true"
    headers = {
        "X-Shopify-Access-Token": builder.access_token,
        "Content-Type": "application/json",
    }
    
    async with httpx.AsyncClient(verify=False) as client:
        resp = await client.get(f"https://{builder.shop_domain}/admin/api/{builder.api_version}/themes.json", headers=headers)
        themes = resp.json().get("themes", [])
        active = next((t for t in themes if t.get("role") == "main"), None)
        theme_id = active["id"]
        
        idx_resp = await client.get(
            f"https://{builder.shop_domain}/admin/api/{builder.api_version}/themes/{theme_id}/assets.json?asset[key]=templates/index.json",
            headers=headers
        )
        tmpl = json.loads(idx_resp.json().get("asset", {}).get("value", "{}"))
        
        # Apply the logic
        clean_tmpl = builder._strip_html(tmpl)
        
        # Find if anything still has HTML
        def find_html(obj, path=""):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    find_html(v, f"{path}.{k}")
            elif isinstance(obj, list):
                for i, v in enumerate(obj):
                    find_html(v, f"{path}[{i}]")
            elif isinstance(obj, str):
                if "<" in obj:
                    print(f"FAILED TO STRIP: {path} -> {obj}")
        
        find_html(clean_tmpl)
        print("   Logic check complete.")

if __name__ == "__main__":
    asyncio.run(test_theme_update_debug())
