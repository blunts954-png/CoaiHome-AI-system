"""
FULL AUTOMATION ORCHESTRATOR
Runs your entire dropshipping business on autopilot
"""
import asyncio
import json
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import schedule
import time
import threading

from api_clients.shopify_client import get_shopify_client
from automation.product_research_no_api import get_product_research_no_api
from automation.pricing_engine import get_pricing_engine
from automation.fulfillment_monitor import get_fulfillment_monitor
from automation.utils import _safe_print, get_async_runner
from config.settings import settings


class FullAutomation:
    """
    Complete Business Automation - Shopify + CJ Mode
    
    Runs:
    1. Product Research (AI-based)
    2. Pricing Optimization
    3. Inventory Monitoring
    4. TikTok Content Creation
    5. Order Tracking
    """
    
    def __init__(self):
        self.shopify = get_shopify_client()
        self.research = get_product_research_no_api()
        self.pricing = get_pricing_engine()
        self.monitor = get_fulfillment_monitor()
        self.browser_client = None  # Optional - only if playwright installed
        
        # Try to load TikTok engine (soft dependency)
        try:
            from automation.tiktok_content_engine import get_tiktok_content_engine
            self.content = get_tiktok_content_engine()
        except Exception:
            self.content = None
        
        self.running = False
        self.logs = []
    
    def _log(self, message: str):
        """Log activity"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.logs.append(log_entry)
        try:
            print(log_entry)
        except UnicodeEncodeError:
            print(log_entry.encode("ascii", "replace").decode("ascii"))
    
    # ============================================================
    # SETUP & CONFIGURATION
    # ============================================================
    
    async def run_full_setup(self) -> Dict:
        """
        Complete setup for fully automated operation
        Run this once to initialize everything
        """
        self._log("🚀 Starting Full Automation Setup...")
        
        results = {
            "shopify_connected": False,
            "autods_browser_ready": False,
            "products_researched": 0,
            "content_calendar_created": False,
            "scheduler_ready": False
        }
        
        # 1. Verify Shopify connection
        try:
            shop_info = await self.shopify.get_shop_info()
            self._log(f"✅ Shopify connected: {shop_info.get('shop', {}).get('name')}")
            results["shopify_connected"] = True
        except Exception as e:
            self._log(f"❌ Shopify connection failed: {e}")
            return results
        
        # 2. Initialize AutoDS browser client
        try:
            self.browser_client = await get_browser_client()
            # Login (may require manual 2FA first time)
            login_success = await self.browser_client.login()
            if login_success:
                self._log("✅ AutoDS browser automation ready")
                results["autods_browser_ready"] = True
            else:
                self._log("⚠️ AutoDS login needs manual 2FA - complete this first")
        except Exception as e:
            self._log(f"⚠️ AutoDS browser not available: {e}")
            self._log("   You can still use manual import mode")
        
        # 3. Research initial products
        try:
            products = await self.research.research_trending_products(
                niche=settings.store.niche or "home organization",
                limit=10
            )
            results["products_researched"] = len(products)
            self._log(f"✅ Researched {len(products)} potential products")
            
            # Export report
            self.research.export_research_report(products)
        except Exception as e:
            self._log(f"⚠️ Product research issue: {e}")
        
        # 4. Create TikTok content calendar
        try:
            shopify_products = await self.shopify.list_products(limit=20)
            content_result = await self.content.auto_create_content_for_store(
                shopify_products.get('products', [])
            )
            results["content_calendar_created"] = True
            self._log(f"✅ Created {content_result['content_pieces']} content pieces for TikTok")
        except Exception as e:
            self._log(f"⚠️ Content calendar issue: {e}")
        
        self._log("✅ Setup complete! Run start_scheduler() to begin automation")
        results["scheduler_ready"] = True
        
        return results
    
    # ============================================================
    # AUTOMATED WORKFLOWS
    # ============================================================
    
    async def daily_product_research(self):
        """
        Daily: Research new products and identify opportunities
        """
        self._log("🔍 Running daily product research...")
        
        try:
            products = await self.research.research_trending_products(
                niche=settings.store.niche or "home organization",
                limit=20
            )
            
            # Filter high-scoring products
            winners = [p for p in products if p.ai_score >= 70]
            
            self._log(f"✅ Found {len(winners)} winning products (score >= 70)")
            
            # Save to file for review
            self.research.export_research_report(winners, 
                f"daily_research_{datetime.now().strftime('%Y%m%d')}.json")
            
            return {
                "products_researched": len(products),
                "winners_found": len(winners),
                "winners": [
                    {"title": p.title, "score": p.ai_score, "margin": p.suggested_price - p.cost_price}
                    for p in winners[:5]
                ]
            }
            
        except Exception as e:
            self._log(f"❌ Product research failed: {e}")
            return {"error": str(e)}
    
    async def import_winning_products(self, max_imports: int = 3):
        """
        Import top-scoring products to your store
        """
        self._log(f"📦 Importing up to {max_imports} winning products...")
        
        if not self.browser_client:
            self._log("❌ Browser client not available. Use manual import instead.")
            return {"error": "Browser client not available"}
        
        try:
            # Get winning products
            products = await self.research.get_import_ready_products(min_score=70)
            to_import = products[:max_imports]
            
            imported = []
            for product in to_import:
                self._log(f"📦 Importing: {product['title']}")
                
                result = await self.browser_client.import_product_from_url(
                    supplier_url=product['source_url'],
                    product_data={
                        'title': product['title'],
                        'price': product['suggested_price']
                    }
                )
                
                if result.get('success'):
                    imported.append(product['title'])
                    self._log(f"✅ Imported: {product['title']}")
                else:
                    self._log(f"❌ Failed: {result.get('error')}")
                
                await asyncio.sleep(3)  # Rate limiting
            
            self._log(f"✅ Imported {len(imported)} products")
            return {"imported": imported, "total": len(to_import)}
            
        except Exception as e:
            self._log(f"❌ Import failed: {e}")
            return {"error": str(e)}
    
    async def optimize_pricing(self):
        """
        Daily: Optimize prices based on competition and margins
        """
        self._log("💰 Running pricing optimization...")
        
        try:
            result = await self.pricing.run_pricing_optimization()
            
            changes = result.get('applied', 0) + result.get('pending_approval', 0)
            self._log(f"✅ Optimized pricing for {changes} products")
            
            return result
            
        except Exception as e:
            self._log(f"❌ Pricing optimization failed: {e}")
            return {"error": str(e)}
    
    async def sync_inventory(self):
        """
        Hourly: Sync inventory levels and pause out-of-stock items
        """
        self._log("🔄 Syncing inventory...")
        
        try:
            result = await self.monitor.run_inventory_sync()
            
            updates = result.get('stock_updates', 0)
            stockouts = result.get('stockouts_detected', 0)
            
            self._log(f"✅ Inventory synced: {updates} updates, {stockouts} stockouts")
            
            return result
            
        except Exception as e:
            self._log(f"❌ Inventory sync failed: {e}")
            return {"error": str(e)}
    
    async def check_orders(self):
        """
        Check for new orders and fulfillment issues
        """
        self._log("📋 Checking orders...")
        
        try:
            result = await self.monitor.check_fulfillment_exceptions()
            
            unfulfilled = result.get('unfulfilled_orders', 0)
            if unfulfilled > 0:
                self._log(f"⚠️ {unfulfilled} unfulfilled orders need attention")
            else:
                self._log("✅ All orders on track")
            
            return result
            
        except Exception as e:
            self._log(f"❌ Order check failed: {e}")
            return {"error": str(e)}
    
    async def generate_tiktok_content(self):
        """
        Weekly: Generate new TikTok content for products
        """
        self._log("🎬 Generating TikTok content...")
        
        try:
            result = await self.content.auto_create_content_for_store()
            
            pieces = result.get('content_pieces', 0)
            self._log(f"✅ Generated {pieces} content pieces")
            
            return result
            
        except Exception as e:
            self._log(f"❌ Content generation failed: {e}")
            return {"error": str(e)}
    
    # ============================================================
    # SCHEDULER
    # ============================================================
    
    def start_scheduler(self):
        """
        Start the automation scheduler in a background thread.
        Returns immediately — does NOT block.
        """
        if self.running:
            self._log("⚠️ Scheduler already running.")
            return
        
        self._log("⏰ Starting automation scheduler...")
        self.running = True
        
        # Schedule daily tasks
        schedule.every().day.at("09:00").do(self._run_async_task, self.daily_product_research)
        schedule.every().day.at("14:00").do(self._run_async_task, self.optimize_pricing)
        schedule.every().day.at("20:00").do(self._run_async_task, self.generate_tiktok_content)
        
        # Schedule hourly tasks
        schedule.every().hour.do(self._run_async_task, self.sync_inventory)
        schedule.every(2).hours.do(self._run_async_task, self.check_orders)
        
        self._log("📅 Scheduled tasks active:")
        self._log("   09:00 — Product Research")
        self._log("   14:00 — Pricing Optimization")
        self._log("   20:00 — TikTok Content")
        self._log("   Hourly — Inventory Sync")
        self._log("   Every 2 hours — Order Check")
        
        # Background loop — does NOT block
        def run_schedule():
            while self.running:
                schedule.run_pending()
                time.sleep(60)
        
        thread = threading.Thread(target=run_schedule, daemon=True)
        thread.start()
        
        self._log("✅ Scheduler running in background.")
    
    def _run_async_task(self, task):
        """Helper to run async tasks in scheduler using persistent event loop"""
        try:
            async_runner = get_async_runner()
            if not async_runner._running:
                async_runner.start()
            async_runner.run_task(task())
        except Exception as e:
            self._log(f"❌ Scheduled task failed: {e}")
    
    def stop_scheduler(self):
        """Stop the automation scheduler"""
        self.running = False
        self._log("🛑 Scheduler stopped")
    
    # ============================================================
    # MANUAL COMMANDS
    # ============================================================
    
    async def run_all_now(self) -> Dict:
        """
        Run all automation tasks immediately (for testing)
        """
        self._log("🚀 Running all automation tasks now...")
        
        results = {}
        
        results['research'] = await self.daily_product_research()
        results['pricing'] = await self.optimize_pricing()
        results['inventory'] = await self.sync_inventory()
        results['orders'] = await self.check_orders()
        
        self._log("✅ All tasks completed!")
        
        return results
    
    def get_status(self) -> Dict:
        """Get current automation status"""
        return {
            "running": self.running,
            "shopify_connected": True,  # Would check actual connection
            "autods_browser_ready": self.browser_client is not None,
            "last_logs": self.logs[-10:]  # Last 10 log entries
        }


# Singleton
_full_automation: Optional[FullAutomation] = None


def get_full_automation() -> FullAutomation:
    """Get or create automation instance"""
    global _full_automation
    if _full_automation is None:
        _full_automation = FullAutomation()
    return _full_automation
