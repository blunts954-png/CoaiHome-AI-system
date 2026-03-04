import asyncio
import json
import httpx
import os
from config.settings import settings

async def debug_index_json():
    print("🔍 Debugging templates/index.json content...")
    headers = {
        "X-Shopify-Access-Token": settings.shopify.access_token,
        "Content-Type": "application/json",
    }
    shop = settings.shopify.shop_url
    api_version = "2024-01"
    
    async with httpx.AsyncClient(verify=False) as client:
        resp = await client.get(f"https://{shop}/admin/api/{api_version}/themes.json", headers=headers)
        themes = resp.json().get("themes", [])
        active = next((t for t in themes if t.get("role") == "main"), None)
        theme_id = active["id"]
        
        idx_resp = await client.get(
            f"https://{shop}/admin/api/{api_version}/themes/{theme_id}/assets.json?asset[key]=templates/index.json",
            headers=headers
        )
        val = idx_resp.json().get("asset", {}).get("value", "{}")
        tmpl = json.loads(val)
        
        # Look for the 'text' setting specifically anywhere
        def find_text(obj, path=""):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    find_text(v, f"{path}.{k}")
            elif isinstance(obj, list):
                for i, v in enumerate(obj):
                    find_text(v, f"{path}[{i}]")
            elif isinstance(obj, str):
                if "<" in obj:
                    print(f"Found HTML in {path}: {obj}")

        find_text(tmpl)

if __name__ == "__main__":
    asyncio.run(debug_index_json())
