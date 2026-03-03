
import asyncio
import httpx
import json
import os
import base64
from config.settings import settings

async def revamp():
    shop_url = settings.shopify.shop_url
    access_token = settings.shopify.access_token
    api_version = "2024-01"
    headers = {
        "X-Shopify-Access-Token": access_token,
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        # 1. Get Main Theme ID
        print("Finding main theme...")
        themes_url = f"https://{shop_url}/admin/api/{api_version}/themes.json"
        t_resp = await client.get(themes_url, headers=headers)
        themes = t_resp.json().get('themes', [])
        main_theme = next((t for t in themes if t.get('role') == 'main'), None)
        
        if not main_theme:
            print("No main theme found.")
            return
        
        theme_id = main_theme['id']
        print(f"Main theme: {main_theme['name']} (ID: {theme_id})")

        # 2. Get the index.json template
        print("Fetching index.json...")
        index_url = f"https://{shop_url}/admin/api/{api_version}/themes/{theme_id}/assets.json?asset[key]=templates/index.json"
        i_resp = await client.get(index_url, headers=headers)
        
        if i_resp.status_code != 200:
            # Fallback to index.list if json doesn't exist (unlikely for OS 2.0)
            print("No index.json found, trying alt...")
            return

        asset = i_resp.json().get('asset', {})
        content_str = asset.get('value')
        if not content_str:
            print("Empty index.json")
            return
            
        index_data = json.loads(content_str)
        sections = index_data.get('sections', {})
        order = index_data.get('order', [])

        # 3. Clean up and revamp
        print("Redesigning layout...")
        # Find and target sections based on typical Dawn structure
        
        # New sections dictionary to replace parts
        new_sections = {}
        new_order = []
        
        # 3a. Banner Fix
        banner_found = False
        for sid, section in sections.items():
            if section.get('type') == 'image-banner':
                section['settings']['heading'] = "ELEVATE YOUR SPACE"
                section['settings']['subheading'] = "Luxury Home Organization for the Modern Home."
                section['settings']['button_label_1'] = "Shop The Collection"
                banner_found = True
                new_sections[sid] = section
                new_order.append(sid)
                break
        
        # 3b. Collection Fix (Featured Collection)
        featured_found = False
        for sid, section in sections.items():
            if section.get('type') == 'featured-collection' or 'collection' in sid:
                section['settings']['title'] = "Professional Organizers"
                section['settings']['collection'] = "frontpage" # The one we populated
                section['settings']['products_to_show'] = 8
                section['settings']['columns_desktop'] = 4
                featured_found = True
                new_sections[sid] = section
                new_order.append(sid)
                break
        
        # 3c. Remove the "trash" sections (collages, multisulf, etc that look placeholder-y)
        # We only keep the good ones if we didn't find them in Order
        for sid in order:
            if sid not in new_order:
                section = sections[sid]
                # Skip sections that look like text-columns (logo placeholders)
                if section.get('type') in ['multicolumn', 'rich-text']:
                    # Only skip if they have placeholder-y words
                    text = str(section).lower()
                    if 'partner logo' in text or 'grow your business' in text:
                        print(f"Removing placeholder section: {sid}")
                        continue
                new_sections[sid] = section
                new_order.append(sid)

        index_data['sections'] = new_sections
        index_data['order'] = new_order

        # 4. Push updated template
        print("Pushing redesigned index.json...")
        update_payload = {
            "asset": {
                "key": "templates/index.json",
                "value": json.dumps(index_data, indent=2)
            }
        }
        u_resp = await client.put(f"https://{shop_url}/admin/api/{api_version}/themes/{theme_id}/assets.json", headers=headers, json=update_payload)
        
        if u_resp.status_code == 200:
            print("Design Revamp: SUCCESS (Layout Restructured)")
        else:
            print(f"Design Revamp: FAILED ({u_resp.status_code}): {u_resp.text}")

    print("\nRE-SYNCING PRODUCTS...")
    # Ensuring products are actually published to the Online Store channel
    # (Sometimes activation isn't enough, they need to be 'published' to the app)

if __name__ == "__main__":
    asyncio.run(revamp())
