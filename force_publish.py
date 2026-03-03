
import asyncio
import httpx
import os
from config.settings import settings

async def force_publish():
    shop_url = settings.shopify.shop_url
    access_token = settings.shopify.access_token
    api_version = "2024-01"
    verify_ssl = False
    
    # Try multiple ways to get the token
    if not access_token:
        access_token = os.getenv("SHOPIFY_ACCESS_TOKEN")

    if not access_token:
        print("ERROR: No Shopify Access Token found.")
        return

    headers = {
        "X-Shopify-Access-Token": access_token,
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient(verify=verify_ssl) as client:
        print(f"Connecting to {shop_url}...")
        
        # 1. Get All Products (skip publications as it needs more scopes)
        p_url = f"https://{shop_url}/admin/api/{api_version}/products.json?limit=250"
        p_resp = await client.get(p_url, headers=headers)
        if p_resp.status_code != 200:
            print(f"ERROR: Products API failed (Status {p_resp.status_code}): {p_resp.text}")
            return

        products = p_resp.json().get('products', [])
        print(f"Found {len(products)} products in Admin.")

        # 2. Publish each one to the Online Store channel
        for p in products:
            p_id = p['id']
            # Update product status 
            u_url = f"https://{shop_url}/admin/api/{api_version}/products/{p_id}.json"
            
            # published: true handles publication to the legacy Web channel (Online Store)
            u_payload = {
                "product": {
                    "id": p_id,
                    "published": True,
                    "status": "active"
                }
            }
            resp = await client.put(u_url, headers=headers, json=u_payload)
            if resp.status_code == 200:
                print(f"SUCCESS: Published '{p['title']}'")
            else:
                print(f"FAILED to publish '{p['title']}': {resp.status_code}")

        print("Done!")

if __name__ == "__main__":
    asyncio.run(force_publish())
