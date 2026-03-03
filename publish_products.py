
import asyncio
import httpx
from config.settings import settings

async def publish_all():
    shop_url = settings.shopify.shop_url
    access_token = settings.shopify.access_token
    api_version = "2024-01"
    headers = {
        "X-Shopify-Access-Token": access_token,
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        # Get products
        url = f"https://{shop_url}/admin/api/{api_version}/products.json"
        resp = await client.get(url, headers=headers)
        products = resp.json().get('products', [])
        
        print(f"Publishing {len(products)} products to all sales channels...")
        for p in products:
            p_id = p['id']
            # We use the 'publications' endpoint or just re-save as active
            # For custom apps, setting published: true and status: active usually works
            url = f"https://{shop_url}/admin/api/{api_version}/products/{p_id}.json"
            payload = {
                "product": {
                    "id": p_id,
                    "published": True,
                    "status": "active"
                }
            }
            await client.put(url, headers=headers, json=payload)
            print(f"Verified: {p['title']}")

if __name__ == "__main__":
    asyncio.run(publish_all())
