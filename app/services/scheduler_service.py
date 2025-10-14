from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import pytz
import asyncio

from app.services.campaign_service import campaign_service

class SchedulerService:
    """
    Scheduler service for automatic campaign analysis
    
    Runs daily at midnight UTC to analyze all active campaigns.
    """
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler(timezone=pytz.UTC)
        self.is_running = False
    
    async def analyze_active_campaigns(self):
        """
        Job function that runs scheduled campaign analysis
        """
        try:
            print(f"\n{'='*80}")
            print(f"⏰ SCHEDULER TRIGGERED - {datetime.now(pytz.UTC)}")
            print(f"{'='*80}")
            
            # Check and update campaign statuses first
            await campaign_service.check_and_update_campaign_status()
            
            # Run analysis for active campaigns
            result = await campaign_service.run_scheduled_analysis()
            
            print(f"\n✅ Scheduler job completed successfully")
            print(f"   Campaigns processed: {result['campaigns_processed']}")
            
        except Exception as e:
            print(f"❌ Scheduler job failed: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def start(self):
        """
        Start the scheduler
        
        Schedules:
        - Daily at 00:00 UTC - Run campaign analysis
        - Every 6 hours - Check and update campaign statuses
        """
        if self.is_running:
            print("⚠️  Scheduler is already running")
            return
        
        # Schedule daily analysis at midnight UTC
        self.scheduler.add_job(
            self.analyze_active_campaigns,
            trigger=CronTrigger(hour=0, minute=0, timezone=pytz.UTC),
            id="daily_campaign_analysis",
            name="Daily Campaign Analysis",
            replace_existing=True
        )
        
        # Schedule status check every 6 hours
        self.scheduler.add_job(
            campaign_service.check_and_update_campaign_status,
            trigger=CronTrigger(hour="*/6", timezone=pytz.UTC),
            id="campaign_status_check",
            name="Campaign Status Check",
            replace_existing=True
        )
        
        # Start scheduler
        self.scheduler.start()
        self.is_running = True
        
        print(f"\n{'='*80}")
        print(f"🕐 SCHEDULER STARTED")
        print(f"{'='*80}")
        print(f"✅ Daily analysis: Every day at 00:00 UTC")
        print(f"✅ Status check: Every 6 hours")
        print(f"{'='*80}\n")
    
    def stop(self):
        """Stop the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            self.is_running = False
            print("\n👋 Scheduler stopped")
    
    def get_jobs(self):
        """Get list of scheduled jobs"""
        return self.scheduler.get_jobs()
    
    async def run_now(self):
        """
        Manually trigger the scheduled job immediately
        
        Useful for testing.
        """
        print(f"\n🚀 Manually triggering campaign analysis...")
        await self.analyze_active_campaigns()

# Singleton instance
scheduler_service = SchedulerService()

