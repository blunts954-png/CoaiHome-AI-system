
import time
import requests
import os
from config.settings import settings

# Inflates inventory for all products to ensure visibility
def inflate_inventory():
    shop_url = settings.shopify.shop_url
    access_token = settings.shopify.access_token
    api_version = "2024-01"
    
    headers = {
        "X-Shopify-Access-Token": access_token,
        "Content-Type": "application/json"
    }
    
    # 1. Get products
    url = f"https://{shop_url}/admin/api/{api_version}/products.json?limit=250"
    r = requests.get(url, headers=headers, verify=False)
    products = r.json().get('products', [])
    print(f"Products to stock: {len(products)}")
    
    for p in products:
        for v in p['variants']:
            v_id = v['id']
            i_id = v['inventory_item_id']
            # We need to find the location ID first for updates
            l_url = f"https://{shop_url}/admin/api/{api_version}/locations.json"
            l_resp = requests.get(l_url, headers=headers, verify=False)
            locations = l_resp.json().get('locations', [])
            if not locations:
                print("No locations found.")
                return
            loc_id = locations[0]['id']
            
            # Set levels
            inv_url = f"https://{shop_url}/admin/api/{api_version}/inventory_levels/set.json"
            payload = {
                "location_id": loc_id,
                "inventory_item_id": i_id,
                "available": 10
            }
            resp = requests.post(inv_url, headers=headers, json=payload, verify=False)
            if resp.status_code == 200:
                print(f"STOCKED 10 units: {p['title']}")
            else:
                print(f"FAIL to stock {p['title']} ({resp.status_code})")
            
            # Rate limiting
            time.sleep(1)

if __name__ == "__main__":
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    inflate_inventory()
