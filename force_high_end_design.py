
import asyncio
import httpx
import json
from config.settings import settings

async def force_design():
    shop_url = settings.shopify.shop_url
    access_token = settings.shopify.access_token
    api_version = "2024-01"
    headers = {"X-Shopify-Access-Token": access_token, "Content-Type": "application/json"}
    
    async with httpx.AsyncClient() as client:
        # Get Collection ID for "Home Page"
        print("Getting Home Page collection...")
        c_resp = await client.get(f"https://{shop_url}/admin/api/{api_version}/custom_collections.json?handle=frontpage", headers=headers)
        collections = c_resp.json().get('custom_collections', [])
        if not collections:
            print("Frontpage collection missing - re-running fix script")
            return
        collection_gid = f"gid://shopify/Collection/{collections[0]['id']}"
        collection_handle = "frontpage"
        
        # Get Theme
        resp = await client.get(f"https://{shop_url}/admin/api/{api_version}/themes.json", headers=headers)
        themes = resp.json().get('themes', [])
        main_theme = next((t for t in themes if t.get('role') == 'main'), None)
        theme_id = main_theme['id']

        # Get index.json
        print("Updating index.json manually...")
        asset_url = f"https://{shop_url}/admin/api/{api_version}/themes/{theme_id}/assets.json?asset[key]=templates/index.json"
        i_resp = await client.get(asset_url, headers=headers)
        index_data = json.loads(i_resp.json()['asset']['value'])

        # Overwrite sections with a clean, high-end structure
        # We manually build the order to hide the 'garbage' placeholders
        
        # 1. Hero
        # 2. Featured Collection (Our Products)
        # 3. Rich Text (About)
        
        new_sections = {}
        new_order = []
        
        sections = index_data.get('sections', {})
        for sid, sval in sections.items():
            stype = sval.get('type', '')
            
            # Update Banner
            if 'banner' in stype or 'slideshow' in stype:
                sval['settings']['heading'] = "ORGANIZED LUXURY"
                sval['settings']['subheading'] = "Sustainable, Minimalist, Masterful Home Organization."
                new_sections[sid] = sval
                new_order.append(sid)
            
            # Update Collection
            elif 'collection' in stype or 'product_list' in stype:
                sval['settings']['title'] = "The Essentials Collection"
                # Some themes use handle, some use ID, some use GID. We try both.
                sval['settings']['collection'] = collection_handle
                sval['settings']['products_to_show'] = 12
                new_sections[sid] = sval
                new_order.append(sid)
                
            # Keep other non-trash
            elif stype not in ['multicolumn', 'collage']:
                new_sections[sid] = sval
                new_order.append(sid)

        index_data['sections'] = new_sections
        index_data['order'] = new_order
        
        # Push back
        payload = {"asset": {"key": "templates/index.json", "value": json.dumps(index_data)}}
        p_resp = await client.put(f"https://{shop_url}/admin/api/{api_version}/themes/{theme_id}/assets.json", headers=headers, json=payload)
        print(f"Update Result: {p_resp.status_code}")

if __name__ == "__main__":
    asyncio.run(force_design())
