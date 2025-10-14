from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import pytz
from beanie import PydanticObjectId

from app.models.database import (
    Campaign,
    CampaignMetrics,
    Brand,
    Post,
    Comment,
    CampaignStatus,
    PlatformType
)
from app.services.analysis_service_v2 import analysis_service_v2
from app.services.scraper_service import ScraperService

class CampaignService:
    """Service for campaign analysis and metrics tracking"""
    
    async def analyze_campaign(self, campaign: Campaign) -> Dict[str, Any]:
        """
        Execute comprehensive campaign analysis following the established workflow:
        1. Platform Selection → Apify Actor Runtime → Data Scraping
        2. Data Extraction & Transformation → Teorema Standard Format
        3. Data Cleansing → NLP Processing & Inference
        """
        try:
            brand = await campaign.brand.fetch()
            
            print(f"\n{'='*80}")
            print(f"🎯 Analyzing Campaign: {campaign.campaign_name}")
            print(f"{'='*80}")
            
            # Initialize scraper service
            scraper_service = ScraperService()
            
            # Step 1: Data Scraping using Apify Actor Runtime
            platforms_data = {}
            
            # Check if campaign has keywords
            if not campaign.keywords:
                print("⚠️  Campaign has no keywords configured")
                print("💡 Please add keywords to the campaign for scraping to work")
                return {"error": "No keywords configured for campaign"}
            
            for platform in campaign.platforms:
                print(f"\n{'='*80}")
                print(f"Processing platform: {platform.value.upper()} ({campaign.platforms.index(platform) + 1}/{len(campaign.platforms)})")
                print(f"{'='*80}")
                
                try:
                    # Execute platform-specific scraping
                    # Use thread executor to prevent event loop blocking
                    import asyncio
                    from concurrent.futures import ThreadPoolExecutor
                    
                    async def run_scraping():
                        with ThreadPoolExecutor(max_workers=1) as executor:
                            if platform == PlatformType.TIKTOK:
                                loop = asyncio.get_event_loop()
                                scraped_data = await loop.run_in_executor(
                                    executor, 
                                    scraper_service.scrape_tiktok,
                                    campaign.keywords,
                                    100,
                                    campaign.start_date.isoformat() if campaign.start_date else None,
                                    campaign.end_date.isoformat() if campaign.end_date else None,
                                    brand.name
                                )
                            elif platform == PlatformType.INSTAGRAM:
                                loop = asyncio.get_event_loop()
                                scraped_data = await loop.run_in_executor(
                                    executor,
                                    scraper_service.scrape_instagram,
                                    campaign.keywords,
                                    100,
                                    campaign.start_date.isoformat() if campaign.start_date else None,
                                    campaign.end_date.isoformat() if campaign.end_date else None,
                                    brand.name
                                )
                            elif platform == PlatformType.TWITTER:
                                loop = asyncio.get_event_loop()
                                scraped_data = await loop.run_in_executor(
                                    executor,
                                    scraper_service.scrape_twitter,
                                    campaign.keywords,
                                    100,
                                    campaign.start_date.isoformat() if campaign.start_date else None,
                                    campaign.end_date.isoformat() if campaign.end_date else None,
                                    brand.name
                                )
                            elif platform == PlatformType.YOUTUBE:
                                loop = asyncio.get_event_loop()
                                scraped_data = await loop.run_in_executor(
                                    executor,
                                    scraper_service.scrape_youtube,
                                    campaign.keywords,
                                    100,
                                    campaign.start_date.isoformat() if campaign.start_date else None,
                                    campaign.end_date.isoformat() if campaign.end_date else None,
                                    brand.name
                                )
                            else:
                                scraped_data = None
                            return scraped_data
                    
                    scraped_data = await run_scraping()
                    
                    if scraped_data is None:
                        print(f"⚠️  Unsupported platform: {platform.value}")
                        continue
                    
                    # Check if scraped_data is valid and not empty
                    if scraped_data is not None and not scraped_data.empty:
                        # Step 2: Data Extraction & Transformation to Teorema Format
                        file_path = f"data/scraped_data/dataset_{platform.value}-scraper_{brand.name}.json"
                        platforms_data[platform.value] = file_path
                        print(f"✅ Scraping completed for {platform.value} - {len(scraped_data)} posts found")
                    else:
                        print(f"❌ No data scraped for {platform.value} - empty or invalid data")
                        
                except Exception as e:
                    print(f"✗ Error processing {platform.value}: {str(e)}")
                    continue
            
            if not platforms_data:
                print("⚠️  No platform data available after scraping")
                return {"error": "No data available after scraping"}
            
            # Step 3: Data Cleansing and NLP Processing
            results = await analysis_service_v2.process_multiple_platforms(
                platforms_data=platforms_data,
                brand_name=brand.name,
                keywords=campaign.keywords,
                save_to_db=True
            )
            
            # Aggregate results
            total_posts = sum(r.total_analyzed for r in results)
            sentiment_counts = {"Positive": 0, "Negative": 0, "Neutral": 0}
            all_topics = []
            
            for result in results:
                for sentiment, count in result.sentiment_distribution.items():
                    sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + count
                all_topics.extend(result.topics_found)
            
            # Calculate sentiment score (0-100)
            total_with_sentiment = sum(sentiment_counts.values())
            sentiment_score = 0.0
            if total_with_sentiment > 0:
                sentiment_score = (sentiment_counts.get("Positive", 0) / total_with_sentiment) * 100
            
            # Calculate engagement metrics from posts
            posts = await Post.find(
                Post.brand.id == brand.id
            ).to_list()
            
            total_likes = sum(p.like_count for p in posts)
            total_comments = sum(p.comment_count for p in posts)
            total_shares = sum(p.share_count for p in posts)
            total_views = sum(p.view_count for p in posts)
            
            engagement_rate = 0.0
            if total_views > 0:
                engagement_rate = ((total_likes + total_comments + total_shares) / total_views) * 100
            
            # Get unique authors for reach
            unique_authors = len(set(p.author_id for p in posts if p.author_id))
            
            # Get previous metric for trend calculation
            previous_metric = await CampaignMetrics.find(
                CampaignMetrics.campaign.id == campaign.id
            ).sort("-metric_date").limit(1).first_or_none()
            
            sentiment_change = 0.0
            mentions_change = 0.0
            engagement_change = 0.0
            
            if previous_metric:
                if previous_metric.sentiment_score > 0:
                    sentiment_change = ((sentiment_score - previous_metric.sentiment_score) / previous_metric.sentiment_score) * 100
                if previous_metric.total_mentions > 0:
                    mentions_change = ((total_posts - previous_metric.total_mentions) / previous_metric.total_mentions) * 100
                if previous_metric.engagement_rate > 0:
                    engagement_change = ((engagement_rate - previous_metric.engagement_rate) / previous_metric.engagement_rate) * 100
            
            # Create new metrics snapshot
            now = datetime.now(pytz.UTC)
            metric = CampaignMetrics(
                campaign=campaign,
                brand=brand,
                metric_date=now,
                sentiment_score=sentiment_score,
                positive_count=sentiment_counts.get("Positive", 0),
                negative_count=sentiment_counts.get("Negative", 0),
                neutral_count=sentiment_counts.get("Neutral", 0),
                total_mentions=total_posts,
                new_mentions=total_posts - (previous_metric.total_mentions if previous_metric else 0),
                total_likes=total_likes,
                total_comments=total_comments,
                total_shares=total_shares,
                total_views=total_views,
                engagement_rate=engagement_rate,
                reach=unique_authors,
                unique_users=unique_authors,
                top_topics=list(set(all_topics))[:10],
                sentiment_change=sentiment_change,
                mentions_change=mentions_change,
                engagement_change=engagement_change,
                posts_analyzed=total_posts
            )
            
            await metric.insert()
            
            # Update campaign with latest metrics
            campaign.total_mentions = total_posts
            campaign.overall_sentiment = sentiment_score
            campaign.engagement_rate = engagement_rate
            campaign.reach = unique_authors
            campaign.sentiment_trend = sentiment_change
            campaign.mentions_trend = mentions_change
            campaign.engagement_trend = engagement_change
            campaign.last_analysis_at = now
            
            # Schedule next analysis
            if campaign.auto_analysis_enabled:
                campaign.next_analysis_at = now + timedelta(days=1)
                campaign.next_analysis_at = campaign.next_analysis_at.replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
            
            await campaign.save()
            
            print(f"✅ Campaign analysis completed")
            print(f"   - Total mentions: {total_posts}")
            print(f"   - Sentiment score: {sentiment_score:.1f}%")
            print(f"   - Engagement rate: {engagement_rate:.2f}%")
            print(f"   - Reach: {unique_authors}")
            
            return {
                "success": True,
                "campaign_name": campaign.campaign_name,
                "metrics": {
                    "total_mentions": total_posts,
                    "sentiment_score": sentiment_score,
                    "engagement_rate": engagement_rate,
                    "reach": unique_authors,
                    "sentiment_trend": sentiment_change,
                    "mentions_trend": mentions_change,
                    "engagement_trend": engagement_change
                }
            }
            
        except Exception as e:
            print(f"❌ Error analyzing campaign: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_active_campaigns(self) -> List[Campaign]:
        """
        Get all campaigns that should be analyzed today
        
        Returns campaigns where:
        - status = ACTIVE
        - start_date <= today <= end_date
        - auto_analysis_enabled = True
        - next_analysis_at <= now (or None)
        """
        now = datetime.now(pytz.UTC)
        
        campaigns = await Campaign.find(
            Campaign.status == CampaignStatus.ACTIVE,
            Campaign.start_date <= now,
            Campaign.end_date >= now,
            Campaign.auto_analysis_enabled == True
        ).to_list()
        
        # Filter by next_analysis_at
        campaigns_to_analyze = []
        for campaign in campaigns:
            if campaign.next_analysis_at is None or campaign.next_analysis_at <= now:
                campaigns_to_analyze.append(campaign)
        
        return campaigns_to_analyze
    
    async def run_scheduled_analysis(self) -> Dict[str, Any]:
        """
        Run analysis for all active campaigns
        
        Called by the scheduler daily.
        """
        print(f"\n{'='*80}")
        print(f"🔄 Running Scheduled Campaign Analysis")
        print(f"{'='*80}")
        
        campaigns = await self.get_active_campaigns()
        
        print(f"Found {len(campaigns)} campaigns to analyze")
        
        results = []
        for campaign in campaigns:
            result = await self.analyze_campaign(campaign)
            results.append({
                "campaign_name": campaign.campaign_name,
                "result": result
            })
        
        print(f"\n✅ Scheduled analysis completed: {len(results)} campaigns processed")
        
        return {
            "timestamp": datetime.now(pytz.UTC),
            "campaigns_processed": len(results),
            "results": results
        }
    
    async def check_and_update_campaign_status(self):
        """
        Check all campaigns and update their status based on dates
        
        - DRAFT -> ACTIVE if start_date reached
        - ACTIVE -> COMPLETED if end_date passed
        """
        now = datetime.now(pytz.UTC)
        
        # Activate draft campaigns that have started
        draft_campaigns = await Campaign.find(
            Campaign.status == CampaignStatus.DRAFT,
            Campaign.start_date <= now
        ).to_list()
        
        for campaign in draft_campaigns:
            campaign.status = CampaignStatus.ACTIVE
            if campaign.auto_analysis_enabled and campaign.next_analysis_at is None:
                campaign.next_analysis_at = now
            await campaign.save()
            print(f"✅ Activated campaign: {campaign.campaign_name}")
        
        # Complete active campaigns that have ended
        active_campaigns = await Campaign.find(
            Campaign.status == CampaignStatus.ACTIVE,
            Campaign.end_date < now
        ).to_list()
        
        for campaign in active_campaigns:
            campaign.status = CampaignStatus.COMPLETED
            campaign.auto_analysis_enabled = False
            campaign.next_analysis_at = None
            await campaign.save()
            print(f"✅ Completed campaign: {campaign.campaign_name}")

# Singleton instance
campaign_service = CampaignService()

