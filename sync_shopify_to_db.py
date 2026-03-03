
import asyncio
import httpx
import os
from config.settings import settings
from models.database import SessionLocal, Product, ProductStatus, Store
from automation.logger import log_action

async def sync_products():
    """Pulls products from Shopify and updates the local database"""
    shop_url = settings.shopify.shop_url
    access_token = settings.shopify.access_token
    api_version = "2024-01"
    verify_ssl = os.getenv("SHOPIFY_SSL_VERIFY", "true").lower() == "true"

    if not access_token:
        log_action("sync_error", "store", shop_url, "failed", "No Shopify Access Token found.")
        return {"status": "error", "message": "No access token"}

    headers = {
        "X-Shopify-Access-Token": access_token,
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient(verify=verify_ssl, timeout=60.0) as client:
        log_action("sync_start", "store", shop_url, "pending", "Synchronization with Shopify started.")
        url = f"https://{shop_url}/admin/api/{api_version}/products.json?limit=250"
        
        try:
            resp = await client.get(url, headers=headers)
            if resp.status_code != 200:
                msg = f"Shopify API error: {resp.status_code}"
                log_action("sync_error", "store", shop_url, "failed", msg)
                return {"status": "error", "message": msg}
            
            shopify_products = resp.json().get('products', [])
            log_action("sync_data", "store", shop_url, "success", f"Processing {len(shopify_products)} products from Shopify...")

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
                p_id = str(sp['id'])
                db_p = db.query(Product).filter(Product.shopify_product_id == p_id).first()
                
                if not db_p:
                    db_p = Product(
                        shopify_product_id=p_id,
                        store_id=store.id,
                        title=sp['title'],
                        description=sp['body_html'],
                        status=ProductStatus.ACTIVE if sp['status'] == 'active' else ProductStatus.DRAFT,
                        selling_price=float(sp['variants'][0]['price']) if sp['variants'] else 0.0,
                        vendor=sp['vendor'],
                        sku=sp['variants'][0]['sku'] if sp['variants'] else None,
                        ai_research_data={"main_image": sp['image']['src'] if sp.get('image') else None}
                    )
                    db.add(db_p)
                    synced_count += 1
                else:
                    db_p.title = sp['title']
                    db_p.status = ProductStatus.ACTIVE if sp['status'] == 'active' else ProductStatus.DRAFT
                    db_p.selling_price = float(sp['variants'][0]['price']) if sp['variants'] else db_p.selling_price
                
            db.commit()
            db.close()
            
            success_msg = f"Sync complete. {synced_count} new products identified. Total catalog: {len(shopify_products)}"
            log_action("sync_complete", "store", shop_url, "success", success_msg)
            return {"status": "success", "synced": synced_count, "total": len(shopify_products)}

        except Exception as e:
            log_action("sync_error", "store", shop_url, "failed", str(e))
            return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    asyncio.run(sync_products())
