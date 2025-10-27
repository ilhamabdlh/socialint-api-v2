from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import pytz
import os
import pandas as pd
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
from app.config.env_config import env_config

class CampaignService:
    """Service for campaign analysis and metrics tracking"""
    
    def get_platform_urls(self, campaign: Campaign, target_platform: PlatformType) -> List[str]:
        """
        Get URLs for a specific platform from campaign's platform_urls
        
        Args:
            campaign: Campaign object
            target_platform: Platform to get URLs for
            
        Returns:
            List of URLs for the specified platform
        """
        urls = []
        
        # Check new platform_urls structure first
        if hasattr(campaign, 'platform_urls') and campaign.platform_urls:
            for platform_url in campaign.platform_urls:
                if platform_url.platform == target_platform:
                    urls.append(platform_url.post_url)
        
        # Fallback to legacy post_urls structure
        elif hasattr(campaign, 'post_urls') and campaign.post_urls:
            # This will be handled by the existing logic below
            pass
            
        return urls
    
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
                    # Check if dataset file already exists for this brand and platform
                    file_path = f"data/scraped_data/dataset_{platform.value}-scraper_{brand.name}.json"
                    
                    if os.path.exists(file_path):
                        print(f"📁 Found existing dataset file: {file_path}")
                        
                        # Load and validate existing data
                        try:
                            existing_df = pd.read_json(file_path)
                            if not existing_df.empty:
                                platforms_data[platform.value] = file_path
                                print(f"✅ Using existing data for {platform.value} - {len(existing_df)} posts found")
                                print(f"💰 Token Apify saved! Using cached data instead of scraping")
                                continue
                            else:
                                print(f"⚠️  Existing file is empty, will scrape new data")
                        except Exception as e:
                            print(f"⚠️  Error reading existing file: {str(e)}, will scrape new data")
                    else:
                        print(f"📁 No existing dataset found for {brand.name} on {platform.value}")
                        print(f"🔄 Will proceed with scraping...")
                    
                    # Execute platform-specific scraping (only if no existing data or existing data is invalid)
                    print(f"🚀 Starting scraping for {platform.value}...")
                    print(f"💳 This will consume Apify tokens for data collection")
                    # Use thread executor to prevent event loop blocking
                    import asyncio
                    from concurrent.futures import ThreadPoolExecutor
                    
                    async def run_scraping():
                        with ThreadPoolExecutor(max_workers=1) as executor:
                            if platform == PlatformType.TIKTOK:
                                # Get post URLs for TikTok from campaign using new structure
                                tiktok_post_urls = self.get_platform_urls(campaign, PlatformType.TIKTOK)
                                
                                # Fallback to legacy post_urls structure if new structure is empty
                                if not tiktok_post_urls and campaign.post_urls:
                                    print(f"🔍 DEBUG: Using legacy post_urls structure for TikTok")
                                    for post_url in campaign.post_urls:
                                        # Initialize variables
                                        post_url_value = None
                                        post_platform = None
                                        
                                        # Handle Beanie Link objects
                                        if hasattr(post_url, 'url'):
                                            post_url_value = post_url.url
                                            post_platform = post_url.platform
                                        elif hasattr(post_url, 'ref'):
                                            try:
                                                actual_post_url = await post_url.fetch()
                                                post_url_value = actual_post_url.url
                                                post_platform = actual_post_url.platform
                                            except Exception as e:
                                                continue
                                        else:
                                            continue
                                        
                                        # Skip if url or platform is None
                                        if post_url_value is None or post_platform is None:
                                            continue
                                        
                                        # 🔧 FIX: Only use URL pattern, completely ignore platform field
                                        is_tiktok_url = 'tiktok.com' in post_url_value.lower() or 'vt.tiktok.com' in post_url_value.lower()
                                        
                                        # Only add if URL pattern matches TikTok (completely ignore platform field)
                                        if is_tiktok_url:
                                            tiktok_post_urls.append(post_url_value)
                                            print(f"✅ Added TikTok post URL: {post_url_value} (URL pattern: {is_tiktok_url})")
                                        else:
                                            print(f"⚠️  Skipping non-TikTok URL: {post_url_value} (URL pattern doesn't match TikTok)")
                                
                                print(f"📱 TikTok post URLs to scrape: {tiktok_post_urls}")
                                
                                loop = asyncio.get_event_loop()
                                scraped_data = await loop.run_in_executor(
                                    executor, 
                                    scraper_service.scrape_tiktok,
                                    campaign.keywords,
                                    None,  # Use environment configuration
                                    campaign.start_date.isoformat() if campaign.start_date else None,
                                    campaign.end_date.isoformat() if campaign.end_date else None,
                                    brand.name,
                                    tiktok_post_urls if tiktok_post_urls else None,
                                    "campaign"  # Campaign analysis: individual posts
                                )
                            elif platform == PlatformType.INSTAGRAM:
                                # Get post URLs for Instagram from campaign using new structure
                                instagram_post_urls = self.get_platform_urls(campaign, PlatformType.INSTAGRAM)
                                
                                # Fallback to legacy post_urls structure if new structure is empty
                                if not instagram_post_urls and campaign.post_urls:
                                    print(f"🔍 DEBUG: Using legacy post_urls structure for Instagram")
                                    print(f"🔍 DEBUG: Found {len(campaign.post_urls)} post URLs in campaign")
                                    for post_url in campaign.post_urls:
                                        print(f"🔍 DEBUG: Post URL object type: {type(post_url)}")
                                        print(f"🔍 DEBUG: Post URL object: {post_url}")
                                        
                                        # Initialize variables
                                        post_url_value = None
                                        post_platform = None
                                        
                                        # Handle Beanie Link objects
                                        if hasattr(post_url, 'url'):
                                            post_url_value = post_url.url
                                            post_platform = post_url.platform
                                        elif hasattr(post_url, 'ref'):
                                            # This is a Beanie Link object, need to fetch the actual document
                                            try:
                                                actual_post_url = await post_url.fetch()
                                                post_url_value = actual_post_url.url
                                                post_platform = actual_post_url.platform
                                                print(f"🔍 DEBUG: Fetched PostURL: {post_url_value}, Platform: {post_platform}")
                                            except Exception as e:
                                                print(f"⚠️  Error fetching PostURL: {e}")
                                                continue
                                        else:
                                            print(f"⚠️  Unknown post URL object structure: {post_url}")
                                            continue
                                        
                                        # Skip if url or platform is None
                                        if post_url_value is None or post_platform is None:
                                            print(f"⚠️  Skipping post URL due to missing data: url={post_url_value}, platform={post_platform}")
                                            continue
                                        
                                        print(f"🔍 DEBUG: Post URL: {post_url_value}, Platform: {post_platform}")
                                        
                                        # 🔧 FIX: Only use URL pattern, completely ignore platform field
                                        is_instagram_url = 'instagram.com' in post_url_value.lower()
                                        
                                        # Only add if URL pattern matches Instagram (completely ignore platform field)
                                        if is_instagram_url:
                                            instagram_post_urls.append(post_url_value)
                                            print(f"✅ Added Instagram post URL: {post_url_value} (URL pattern: {is_instagram_url})")
                                        else:
                                            print(f"⚠️  Skipping non-Instagram URL: {post_url_value} (URL pattern doesn't match Instagram)")
                                else:
                                    print(f"⚠️  No post URLs found in campaign")
                                
                                print(f"📱 Instagram post URLs to scrape: {instagram_post_urls}")
                                
                                loop = asyncio.get_event_loop()
                                scraped_data = await loop.run_in_executor(
                                    executor,
                                    scraper_service.scrape_instagram,
                                    campaign.keywords,
                                    None,  # Use environment configuration
                                    campaign.start_date.isoformat() if campaign.start_date else None,
                                    campaign.end_date.isoformat() if campaign.end_date else None,
                                    brand.name,
                                    instagram_post_urls if instagram_post_urls else None,
                                    "campaign"  # Campaign analysis: individual posts
                                )
                            elif platform == PlatformType.TWITTER:
                                # Get post URLs for Twitter from campaign using new structure
                                twitter_post_urls = self.get_platform_urls(campaign, PlatformType.TWITTER)
                                
                                # Fallback to legacy post_urls structure if new structure is empty
                                if not twitter_post_urls and campaign.post_urls:
                                    print(f"🔍 DEBUG: Using legacy post_urls structure for Twitter")
                                    for post_url in campaign.post_urls:
                                        # Initialize variables
                                        post_url_value = None
                                        post_platform = None
                                        
                                        # Handle Beanie Link objects
                                        if hasattr(post_url, 'url'):
                                            post_url_value = post_url.url
                                            post_platform = post_url.platform
                                        elif hasattr(post_url, 'ref'):
                                            try:
                                                actual_post_url = await post_url.fetch()
                                                post_url_value = actual_post_url.url
                                                post_platform = actual_post_url.platform
                                            except Exception as e:
                                                continue
                                        else:
                                            continue
                                        
                                        # Skip if url or platform is None
                                        if post_url_value is None or post_platform is None:
                                            continue
                                        
                                        # 🔧 FIX: Only use URL pattern, completely ignore platform field
                                        is_twitter_url = any(domain in post_url_value.lower() for domain in ['twitter.com', 'x.com'])
                                        
                                        # Only add if URL pattern matches Twitter (completely ignore platform field)
                                        if is_twitter_url:
                                            twitter_post_urls.append(post_url_value)
                                            print(f"✅ Added Twitter post URL: {post_url_value} (URL pattern: {is_twitter_url})")
                                        else:
                                            print(f"⚠️  Skipping non-Twitter URL: {post_url_value} (URL pattern doesn't match Twitter)")
                                
                                print(f"📱 Twitter post URLs to scrape: {twitter_post_urls}")
                                
                                loop = asyncio.get_event_loop()
                                scraped_data = await loop.run_in_executor(
                                    executor,
                                    scraper_service.scrape_twitter,
                                    campaign.keywords,
                                    None,  # Use environment configuration
                                    campaign.start_date.isoformat() if campaign.start_date else None,
                                    campaign.end_date.isoformat() if campaign.end_date else None,
                                    brand.name,
                                    twitter_post_urls if twitter_post_urls else None,
                                    "campaign"  # Campaign analysis: individual posts
                                )
                            elif platform == PlatformType.YOUTUBE:
                                # Get post URLs for YouTube from campaign using new structure
                                youtube_post_urls = self.get_platform_urls(campaign, PlatformType.YOUTUBE)
                                
                                # Fallback to legacy post_urls structure if new structure is empty
                                if not youtube_post_urls and campaign.post_urls:
                                    print(f"🔍 DEBUG: Using legacy post_urls structure for YouTube")
                                    for post_url in campaign.post_urls:
                                        # Initialize variables
                                        post_url_value = None
                                        post_platform = None
                                        
                                        # Handle Beanie Link objects
                                        if hasattr(post_url, 'url'):
                                            post_url_value = post_url.url
                                            post_platform = post_url.platform
                                        elif hasattr(post_url, 'ref'):
                                            try:
                                                actual_post_url = await post_url.fetch()
                                                post_url_value = actual_post_url.url
                                                post_platform = actual_post_url.platform
                                            except Exception as e:
                                                continue
                                        else:
                                            continue
                                        
                                        # Skip if url or platform is None
                                        if post_url_value is None or post_platform is None:
                                            continue
                                        
                                        # 🔧 FIX: Only use URL pattern, completely ignore platform field
                                        is_youtube_url = 'youtube.com' in post_url_value.lower() or 'youtu.be' in post_url_value.lower()
                                        
                                        # Only add if URL pattern matches YouTube (completely ignore platform field)
                                        if is_youtube_url:
                                            youtube_post_urls.append(post_url_value)
                                            print(f"✅ Added YouTube post URL: {post_url_value} (URL pattern: {is_youtube_url})")
                                        else:
                                            print(f"⚠️  Skipping non-YouTube URL: {post_url_value} (URL pattern doesn't match YouTube)")
                                
                                print(f"📱 YouTube post URLs to scrape: {youtube_post_urls}")
                                
                                loop = asyncio.get_event_loop()
                                scraped_data = await loop.run_in_executor(
                                    executor,
                                    scraper_service.scrape_youtube,
                                    campaign.keywords,
                                    None,  # Use environment configuration
                                    campaign.start_date.isoformat() if campaign.start_date else None,
                                    campaign.end_date.isoformat() if campaign.end_date else None,
                                    brand.name,
                                    youtube_post_urls if youtube_post_urls else None,
                                    "campaign"  # Campaign analysis: individual posts
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
                        
                        # Save scraped data to file for future use
                        try:
                            # Ensure directory exists
                            os.makedirs("data/scraped_data", exist_ok=True)
                            
                            # Save DataFrame to JSON file
                            scraped_data.to_json(file_path, orient='records', indent=2)
                            print(f"💾 Data saved to: {file_path}")
                            print(f"💰 Future analysis will use this cached data to save Apify tokens")
                        except Exception as e:
                            print(f"⚠️  Warning: Could not save data to file: {str(e)}")
                        
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
            
            # Show token savings summary
            total_platforms = len(campaign.platforms)
            used_existing = len(platforms_data)
            scraped_new = total_platforms - used_existing
            print(f"\n{'='*80}")
            print(f"💰 TOKEN SAVINGS SUMMARY")
            print(f"{'='*80}")
            print(f"📊 Total platforms: {total_platforms}")
            print(f"📁 Used existing data: {used_existing} (Apify tokens saved)")
            print(f"🚀 Scraped new data: {scraped_new} (Apify tokens consumed)")
            if used_existing > 0:
                print(f"💡 Estimated token savings: {used_existing} platform(s) × ~1000 tokens = ~{used_existing * 1000} tokens saved")
            print(f"{'='*80}")
            
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

