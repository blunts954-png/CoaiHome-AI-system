
import time
import requests
import os
from config.settings import settings
from models.database import SessionLocal, Product, Store

# Recovery script: Pushes all products from DB to Shopify with rate limiting
def push_all_to_shopify():
    shop_url = settings.shopify.shop_url
    access_token = settings.shopify.access_token
    api_version = "2024-01"
    
    if not access_token:
        print("ERROR: No access token.")
        return

    headers = {
        "X-Shopify-Access-Token": access_token,
        "Content-Type": "application/json"
    }
    
    db = SessionLocal()
    # Find products that haven't been pushed to Shopify yet
    products = db.query(Product).filter(Product.shopify_product_id == None).all()
    print(f"Products to push from DB: {len(products)}")
    
    for p in products:
        # 1. Create product
        url = f"https://{shop_url}/admin/api/{api_version}/products.json"
        
        # Build payload from DB product
        payload = {
            "product": {
                "title": p.title,
                "body_html": p.description or f"Luxury Home Organization - {p.title}",
                "vendor": "CoaiHome",
                "product_type": "Home Organization",
                "status": "active",
                "published": True,
                "variants": [
                    {
                        "price": str(p.selling_price or 24.99),
                        "sku": p.sku or f"CH-{p.id}",
                        "inventory_management": "shopify",
                        "inventory_policy": "deny",
                        "fulfillment_service": "manual"
                    }
                ],
                "images": [{"src": p.ai_research_data.get('main_image')}] if (p.ai_research_data and p.ai_research_data.get('main_image')) else []
            }
        }
        
        try:
            # Use verify=False to ignore SSL issues on Windows
            r = requests.post(url, headers=headers, json=payload, verify=False)
            if r.status_code == 201:
                new_p = r.json().get('product', {})
                p.shopify_product_id = str(new_p.get('id'))
                # Update status to ACTIVE in our DB
                from models.database import ProductStatus
                p.status = ProductStatus.ACTIVE
                db.commit()
                print(f"CREATED: {p.title}")
            else:
                print(f"FAILED: {p.title} ({r.status_code}) - {r.text[:100]}")
            
            # Rate limiting: 1 call every 1 second
            time.sleep(1)
            
        except Exception as e:
            print(f"EXCEPTION: {e}")
            time.sleep(2)

    db.close()
    print("FINISHED PUSHING PRODUCTS.")

if __name__ == "__main__":
    # Suppress insecure request warnings for the logs
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    push_all_to_shopify()
