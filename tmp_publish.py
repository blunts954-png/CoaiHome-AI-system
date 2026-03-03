
import requests
import os
from config.settings import settings

# Manual publish script using requests (simpler on Windows)
def publish():
    shop_url = settings.shopify.shop_url
    access_token = settings.shopify.access_token
    api_version = "2024-01"
    
    headers = {
        "X-Shopify-Access-Token": access_token,
        "Content-Type": "application/json"
    }
    
    # 1. Get products
    url = f"https://{shop_url}/admin/api/{api_version}/products.json?limit=50"
    try:
        r = requests.get(url, headers=headers, verify=False)
        products = r.json().get('products', [])
        print(f"Products to publish: {len(products)}")
        
        for p in products:
            p_id = p['id']
            # Only publish if not already active or if we want to force it
            p_url = f"https://{shop_url}/admin/api/{api_version}/products/{p_id}.json"
            p_payload = {
                "product": {
                    "id": p_id,
                    "published": True,
                    "status": "active"
                }
            }
            resp = requests.put(p_url, headers=headers, json=p_payload, verify=False)
            if resp.status_code == 200:
                print(f"DONE: {p['title']}")
            else:
                print(f"FAIL: {p['title']} ({resp.status_code})")
                
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    publish()
