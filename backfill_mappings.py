from models.database import SessionLocal, Product, VariantMap

def backfill_mappings():
    db = SessionLocal()
    try:
        products = db.query(Product).all()
        created = 0
        print(f"Checking {len(products)} products for missing mappings...")
        
        for p in products:
            if not p.shopify_variant_id:
                continue
                
            exists = db.query(VariantMap).filter(VariantMap.shopify_variant_id == p.shopify_variant_id).first()
            if not exists:
                vm = VariantMap(
                    shopify_variant_id=p.shopify_variant_id,
                    cj_variant_id="MANUAL",
                    sku=p.sku,
                    store_id=1,
                    active=True
                )
                db.add(vm)
                created += 1
        
        db.commit()
        print(f"✅ Successfully backfilled {created} mappings.")
    except Exception as e:
        print(f"❌ Error backfilling: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    backfill_mappings()
