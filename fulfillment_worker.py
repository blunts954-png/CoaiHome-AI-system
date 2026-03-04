"""
Fulfillment Worker
Periodically polls CJ for tracking numbers and updates Shopify.
"""
import asyncio
import os
from datetime import datetime

from models.database import SessionLocal, ShopifyOrder, OrderStatus
from services.fulfillment_service import FulfillmentService

async def main():
    print("=" * 60)
    print("🚚 CJ FULFILLMENT WORKER - RUNNING")
    print("=" * 60)
    
    # Check credentials
    cj_token = os.getenv("CJ_API_TOKEN") or os.getenv("CJ_API_KEY")
    shopify_token = os.getenv("SHOPIFY_ACCESS_TOKEN")
    
    if not cj_token:
        print("⚠️  Warning: CJ API credentials missing. Fulfillment worker idle.")
    if not shopify_token:
        print("⚠️  Warning: Shopify access token missing. Fulfillment worker idle.")

    svc = FulfillmentService()
    
    while True:
        try:
            db = SessionLocal()
            # Find orders that were sent to CJ but haven't been completed yet
            # Also retry FAILED orders every few hours?
            pending = db.query(ShopifyOrder).filter(
                ShopifyOrder.status == OrderStatus.SENT_TO_CJ
            ).all()
            
            if pending:
                print(f"[{datetime.now().isoformat()}] Checking tracking for {len(pending)} orders...")
                for order in pending:
                    try:
                        print(f"   Checking Shopify {order.shopify_order_id} (CJ: {order.cj_order_id})...")
                        # Use the efficient single-check method
                        await svc.check_order_tracking(order.shopify_order_id)
                    except Exception as e:
                        print(f"   ❌ Error checking order {order.shopify_order_id}: {e}")
            
            db.close()
        except Exception as e:
            print(f"❌ Worker Error: {e}")
        
        # Poll every 30 minutes
        await asyncio.sleep(1800)

if __name__ == "__main__":
    # Ensure UTF-8 console for Windows
    if os.name == 'nt':
        import _locale
        _locale._getdefaultlocale = (lambda *args: ['en_US', 'utf8'])
        
    asyncio.run(main())
