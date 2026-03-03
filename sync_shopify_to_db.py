
import asyncio
import httpx
import os
from config.settings import settings
from models.database import SessionLocal, Product, ProductStatus, Store

async def sync_products():
    """Pulls products from Shopify and updates the local database"""
    shop_url = settings.shopify.shop_url
    access_token = settings.shopify.access_token
    api_version = "2024-01"
    verify_ssl = os.getenv("SHOPIFY_SSL_VERIFY", "true").lower() == "true"

    if not access_token:
        print("ERROR: No Shopify Access Token found.")
        return {"status": "error", "message": "No access token"}

    headers = {
        "X-Shopify-Access-Token": access_token,
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient(verify=verify_ssl) as client:
        print(f"Syncing from {shop_url}...")
        url = f"https://{shop_url}/admin/api/{api_version}/products.json?limit=250"
        
        try:
            resp = await client.get(url, headers=headers)
            if resp.status_code != 200:
                print(f"FAILED: {resp.status_code} - {resp.text}")
                return {"status": "error", "message": f"Shopify API error: {resp.status_code}"}
            
            shopify_products = resp.json().get('products', [])
            print(f"Found {len(shopify_products)} products on Shopify.")

            db = SessionLocal()
            
            # Get default store
            store = db.query(Store).filter(Store.shopify_domain == shop_url).first()
            if not store:
                store = Store(
                    shopify_domain=shop_url,
                    brand_name=settings.store.brand_name or "CoaiHome",
                    niche=settings.store.niche or "Home Organization"
                )
                db.add(store)
                db.commit()
                db.refresh(store)

            synced_count = 0
            for sp in shopify_products:
                # sp is a product from Shopify
                # Check if it's already in our DB
                p_id = str(sp['id'])
                db_p = db.query(Product).filter(Product.shopify_product_id == p_id).first()
                
                if not db_p:
                    # Create new product record
                    db_p = Product(
                        shopify_product_id=p_id,
                        store_id=store.id,
                        title=sp['title'],
                        description=sp['body_html'],
                        status=ProductStatus.ACTIVE if sp['status'] == 'active' else ProductStatus.DRAFT,
                        selling_price=float(sp['variants'][0]['price']) if sp['variants'] else 0.0,
                        vendor=sp['vendor'],
                        sku=sp['variants'][0]['sku'] if sp['variants'] else None
                    )
                    db.add(db_p)
                    synced_count += 1
                else:
                    # Update existing record
                    db_p.title = sp['title']
                    db_p.status = ProductStatus.ACTIVE if sp['status'] == 'active' else ProductStatus.DRAFT
                    db_p.selling_price = float(sp['variants'][0]['price']) if sp['variants'] else db_p.selling_price
                
            db.commit()
            db.close()
            print(f"Sync complete. {synced_count} new products added to DB.")
            return {"status": "success", "synced": synced_count, "total": len(shopify_products)}

        except Exception as e:
            print(f"ERROR: {e}")
            return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    asyncio.run(sync_products())
