
import asyncio
import httpx
import os
from config.settings import settings
from models.database import SessionLocal, Product, ProductStatus, Store
from automation.logger import log_action

async def sync_products():
    """Pulls products from Shopify and updates the local database"""
    shop_url = settings.shopify.shop_url or os.getenv("SHOPIFY_SHOP_URL", "")
    access_token = settings.shopify.access_token or os.getenv("SHOPIFY_ACCESS_TOKEN", "")
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
        
        all_products = []
        url = f"https://{shop_url}/admin/api/{api_version}/products.json?limit=250"
        
        # Handle pagination
        while url:
            try:
                resp = await client.get(url, headers=headers)
                if resp.status_code != 200:
                    msg = f"Shopify API error: {resp.status_code} — {resp.text[:200]}"
                    log_action("sync_error", "store", shop_url, "failed", msg)
                    return {"status": "error", "message": msg}
                
                batch = resp.json().get('products', [])
                all_products.extend(batch)
                
                # Check for next page link
                link_header = resp.headers.get("Link", "")
                next_url = None
                if 'rel="next"' in link_header:
                    for part in link_header.split(","):
                        if 'rel="next"' in part:
                            next_url = part.split(";")[0].strip().strip("<>")
                url = next_url
                
            except Exception as e:
                log_action("sync_error", "store", shop_url, "failed", str(e))
                return {"status": "error", "message": str(e)}

        log_action("sync_data", "store", shop_url, "success", f"Processing {len(all_products)} products from Shopify...")

        db = SessionLocal()
        try:
            # Get or create the store record
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
            updated_count = 0
            
            for sp in all_products:
                p_id = str(sp['id'])
                db_p = db.query(Product).filter(Product.shopify_product_id == p_id).first()
                
                # Get image URL safely
                image_url = None
                if sp.get('image') and sp['image'].get('src'):
                    image_url = sp['image']['src']
                
                # Get variant price safely  
                price = 0.0
                sku = None
                if sp.get('variants'):
                    price = float(sp['variants'][0].get('price', 0) or 0)
                    sku = sp['variants'][0].get('sku')
                
                shopify_status = sp.get('status', 'draft')
                db_status = ProductStatus.ACTIVE if shopify_status == 'active' else ProductStatus.DRAFT
                
                if not db_p:
                    db_p = Product(
                        shopify_product_id=p_id,
                        store_id=store.id,
                        title=sp.get('title', 'Unknown Product'),
                        description=sp.get('body_html', ''),
                        status=db_status,
                        selling_price=price,
                        supplier_name=sp.get('vendor', 'Shopify'),  # vendor -> supplier_name
                        sku=sku,
                        tags=sp.get('tags', '').split(',') if sp.get('tags') else [],
                        ai_research_data={"main_image": image_url, "shopify_handle": sp.get('handle')}
                    )
                    db.add(db_p)
                    synced_count += 1
                else:
                    # Update existing record
                    db_p.title = sp.get('title', db_p.title)
                    db_p.status = db_status
                    db_p.selling_price = price if price > 0 else db_p.selling_price
                    db_p.supplier_name = sp.get('vendor') or db_p.supplier_name
                    if image_url and db_p.ai_research_data:
                        db_p.ai_research_data = {**(db_p.ai_research_data or {}), "main_image": image_url}
                    updated_count += 1
            
            db.commit()
            
            success_msg = f"Sync complete. {synced_count} new + {updated_count} updated. Total: {len(all_products)} products."
            log_action("sync_complete", "store", shop_url, "success", success_msg)
            return {"status": "success", "synced": synced_count, "updated": updated_count, "total": len(all_products)}

        except Exception as e:
            db.rollback()
            log_action("sync_error", "store", shop_url, "failed", str(e))
            return {"status": "error", "message": str(e)}
        finally:
            db.close()

if __name__ == "__main__":
    asyncio.run(sync_products())
