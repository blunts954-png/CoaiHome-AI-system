import asyncio
from automation.product_research import get_product_research
from models.database import SessionLocal, Store

async def test_research():
    print("🕵️ Testing Product Research (Loose Constraints)...")
    research = get_product_research()
    db = SessionLocal()
    store = db.query(Store).first()
    if not store:
        print("❌ No store found in DB.")
        return

    result = await research.run_research_job(store.id)
    print(f"📊 Research Result: {result.get('status')}")
    print(f"📦 Products Found: {result.get('products_found')}")
    print(f"✅ Products Selected: {result.get('products_selected')}")
    
    if result.get("errors"):
        print(f"⚠️ Errors: {result.get('errors')}")

if __name__ == "__main__":
    asyncio.run(test_research())
