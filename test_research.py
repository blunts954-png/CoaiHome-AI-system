import asyncio
import sys

def dprint(msg):
    with open("debug_log.txt", "a", encoding="utf-8") as f:
        f.write(msg + "\n")

dprint("Importing modules...")
from automation.product_research import get_product_research
from models.database import SessionLocal, Store
import traceback

async def test_research():
    dprint("Testing Product Research (Loose Constraints)...")
    try:
        dprint("Getting product research component...")
        research = get_product_research()
        dprint("Opening DB session...")
        db = SessionLocal()
        dprint("Querying Store...")
        store = db.query(Store).first()
        if not store:
            dprint("No store found in DB.")
            return

        dprint(f"Running research job for store {store.id}...")
        result = await research.run_research_job(store.id)
        dprint("Research job returned!")
        
        if not result:
            dprint("Result is None!")
            return
            
        dprint(f"Research Result: {result.get('status')}")
        dprint(f"Products Found: {result.get('products_found')}")
        dprint(f"Products Selected: {result.get('products_selected')}")
        
        if result.get("errors"):
            dprint(f"Errors: {result.get('errors')}")
    except Exception as e:
        dprint(f"FATAL ERROR: {e}")
        with open("debug_log.txt", "a", encoding="utf-8") as f:
            traceback.print_exc(file=f)
    except BaseException as e:
        dprint(f"BASE EXCEPTION: {e}")
        with open("debug_log.txt", "a", encoding="utf-8") as f:
            traceback.print_exc(file=f)

if __name__ == "__main__":
    with open("debug_log.txt", "w", encoding="utf-8") as f:
        f.write("--- STARTED ---\n")
    dprint("Starting asyncio run...")
    asyncio.run(test_research())
    dprint("Application finished.")
