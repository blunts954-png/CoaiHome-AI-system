"""
Job Scheduler
Manages all automated tasks and their schedules
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime

from config.settings import settings
from automation.product_research import get_product_research
from automation.pricing_engine import get_pricing_engine
from automation.fulfillment_monitor import get_fulfillment_monitor
from services.notification_service import get_notification_service


class AutomationScheduler:
    """Manages scheduled automation jobs"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        try:
            self.product_research = get_product_research()
            self.pricing_engine = get_pricing_engine()
            self.fulfillment_monitor = get_fulfillment_monitor()
            self.notifications = get_notification_service()
            self.enabled = True
        except Exception as e:
            print(f"⚠️  Scheduler initialization warning: {e}")
            print("⚠️  Running in limited mode - some features disabled")
            self.enabled = False
    
    def setup_jobs(self):
        """Configure all scheduled jobs"""
        
        # Product Research - Daily
        if settings.autods.auto_import_enabled:
            self.scheduler.add_job(
                self._run_product_research,
                IntervalTrigger(hours=settings.system.product_research_interval_hours),
                id="product_research",
                name="AI Product Research",
                replace_existing=True
            )
            print(f"📅 Scheduled product research every {settings.system.product_research_interval_hours} hours")
        
        # Pricing Optimization - Daily
        if settings.autods.auto_pricing_enabled:
            self.scheduler.add_job(
                self._run_pricing_optimization,
                IntervalTrigger(hours=settings.system.pricing_check_interval_hours),
                id="pricing_optimization",
                name="AI Pricing Optimization",
                replace_existing=True
            )
            print(f"📅 Scheduled pricing optimization every {settings.system.pricing_check_interval_hours} hours")
        
        # Inventory Sync - Every 30 minutes
        self.scheduler.add_job(
            self._run_inventory_sync,
            IntervalTrigger(minutes=settings.system.inventory_check_interval_minutes),
            id="inventory_sync",
            name="Inventory Synchronization",
            replace_existing=True
        )
        print(f"📅 Scheduled inventory sync every {settings.system.inventory_check_interval_minutes} minutes")
        
        # Fulfillment Exception Check - Every 15 minutes
        self.scheduler.add_job(
            self._check_fulfillment_exceptions,
            IntervalTrigger(minutes=15),
            id="fulfillment_check",
            name="Fulfillment Exception Check",
            replace_existing=True
        )
        print("📅 Scheduled fulfillment exception check every 15 minutes")
        
        # Supplier Performance - Daily at 2 AM
        self.scheduler.add_job(
            self._update_supplier_performance,
            CronTrigger(hour=2, minute=0),
            id="supplier_performance",
            name="Supplier Performance Analysis",
            replace_existing=True
        )
        print("📅 Scheduled supplier performance check daily at 2:00 AM")
        
        # Daily Summary - Daily at 8 AM
        self.scheduler.add_job(
            self._send_daily_summary,
            CronTrigger(hour=8, minute=0),
            id="daily_summary",
            name="Daily Summary Report",
            replace_existing=True
        )
        print("📅 Scheduled daily summary at 8:00 AM")
    
    async def _run_product_research(self):
        """Run product research job"""
        print(f"🔍 Running scheduled product research at {datetime.now()}")
        # In production, you'd iterate through all active stores
        result = await self.product_research.run_research_job(store_id=1)
        print(f"Product research completed: {result}")
    
    async def _run_pricing_optimization(self):
        """Run pricing optimization job"""
        print(f"💰 Running scheduled pricing optimization at {datetime.now()}")
        result = await self.pricing_engine.run_pricing_optimization()
        print(f"Pricing optimization completed: {result}")
    
    async def _run_inventory_sync(self):
        """Run inventory synchronization"""
        print(f"🔄 Running inventory sync at {datetime.now()}")
        result = await self.fulfillment_monitor.run_inventory_sync()
        print(f"Inventory sync completed: {result}")
    
    async def _check_fulfillment_exceptions(self):
        """Check for fulfillment exceptions"""
        result = await self.fulfillment_monitor.check_fulfillment_exceptions()
        print(f"Fulfillment check completed: {result}")
    
    async def _update_supplier_performance(self):
        """Update supplier performance metrics"""
        print(f"📊 Running supplier performance analysis at {datetime.now()}")
        result = await self.fulfillment_monitor.update_supplier_performance()
        print(f"Supplier analysis completed: {result}")
    
    async def _send_daily_summary(self):
        """Send daily summary report"""
        # Gather stats from database
        stats = {
            "products_researched": 0,  # Query from DB
            "products_imported": 0,
            "price_changes": 0,
            "new_orders": 0,
            "exceptions": 0,
            "revenue": 0.0,
            "profit": 0.0
        }
        await self.notifications.send_daily_summary(stats)
    
    def start(self):
        """Start the scheduler"""
        if not self.enabled:
            print("⚠️  Scheduler disabled - running in limited mode")
            return
        try:
            self.setup_jobs()
            self.scheduler.start()
            print("✅ Automation scheduler started")
        except Exception as e:
            print(f"⚠️  Could not start scheduler: {e}")
    
    def stop(self):
        """Stop the scheduler"""
        if not self.enabled:
            return
        try:
            self.scheduler.shutdown()
            print("⏹️ Automation scheduler stopped")
        except:
            pass
    
    def get_jobs(self):
        """Get list of scheduled jobs"""
        return [
            {
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger)
            }
            for job in self.scheduler.get_jobs()
        ]


# Singleton
_scheduler: Optional[AutomationScheduler] = None


def get_scheduler() -> AutomationScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = AutomationScheduler()
    return _scheduler
