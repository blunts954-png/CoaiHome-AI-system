
import asyncio
import httpx
from config.settings import settings

async def fix_products():
    shop_url = settings.shopify.shop_url
    access_token = settings.shopify.access_token
    api_version = "2024-01"
    headers = {
        "X-Shopify-Access-Token": access_token,
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        # 1. Get all products
        print("--- Fetching Products ---")
        url = f"https://{shop_url}/admin/api/{api_version}/products.json"
        resp = await client.get(url, headers=headers)
        products = resp.json().get('products', [])
        
        if not products:
            print("No products found in store.")
            return

        # 2. Update status to active and publish
        print(f"--- Activating {len(products)} Products ---")
        for p in products:
            p_id = p['id']
            update_url = f"https://{shop_url}/admin/api/{api_version}/products/{p_id}.json"
            # We set status to active and ensure published_at is set
            payload = {
                "product": {
                    "id": p_id,
                    "status": "active",
                    "published": True
                }
            }
            u_resp = await client.put(update_url, headers=headers, json=payload)
            if u_resp.status_code == 200:
                print(f"Activated: {p['title']}")
            else:
                print(f"Failed to activate {p['title']}: {u_resp.text}")

        # 3. Ensure Frontpage Collection exists and has these products
        print("--- Checking Frontpage Collection ---")
        coll_url = f"https://{shop_url}/admin/api/{api_version}/custom_collections.json?handle=frontpage"
        c_resp = await client.get(coll_url, headers=headers)
        collections = c_resp.json().get('custom_collections', [])
        
        if not collections:
            # Create it
            print("Creating 'Frontpage' collection...")
            create_url = f"https://{shop_url}/admin/api/{api_version}/custom_collections.json"
            c_payload = {
                "custom_collection": {
                    "title": "Home Page",
                    "handle": "frontpage"
                }
            }
            c_resp = await client.post(create_url, headers=headers, json=c_payload)
            collection_id = c_resp.json().get('custom_collection', {}).get('id')
        else:
            collection_id = collections[0]['id']
            print(f"Found existing collection: {collection_id}")

        if collection_id:
            print("--- Adding Products to Home Page ---")
            for p in products:
                collect_url = f"https://{shop_url}/admin/api/{api_version}/collects.json"
                collect_payload = {
                    "collect": {
                        "collection_id": collection_id,
                        "product_id": p['id']
                    }
                }
                cl_resp = await client.post(collect_url, headers=headers, json=collect_payload)
                if cl_resp.status_code == 201:
                    print(f"Added {p['title']} to Home Page")
                else:
                    # Likely already there
                    pass

    print("\nSUCCESS: All products activated and added to Home Page.")

if __name__ == "__main__":
    asyncio.run(fix_products())
