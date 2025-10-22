"""
Scraper Service - Integrates with Apify for social media scraping
"""

from typing import List, Dict, Any, Optional
from apify_client import ApifyClient
import pandas as pd
from datetime import datetime
import time

from app.config.settings import settings

class ScraperService:
    """
    Service for scraping social media platforms using Apify
    """
    
    def __init__(self, apify_token: Optional[str] = None):
        """
        Initialize Apify client
        
        Args:
            apify_token: Apify API token. If None, will try to get from settings
        """
        self.apify_token = apify_token or getattr(settings, 'apify_api_token', None)
        
        if not self.apify_token:
            print("⚠️  Warning: Apify API token not configured")
            self.client = None
        else:
            self.client = ApifyClient(self.apify_token)
    
    def scrape_tiktok(
        self,
        keywords: List[str],
        max_posts: int = 100,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        brand_name: str = "default"
    ) -> pd.DataFrame:
        """
        Scrape TikTok posts using Apify
        
        Args:
            keywords: List of search keywords/hashtags
            max_posts: Maximum number of posts to scrape
            start_date: Start date for filtering (YYYY-MM-DD)
            end_date: End date for filtering (YYYY-MM-DD)
        
        Returns:
            DataFrame with scraped posts
        """
        if not self.client:
            raise ValueError("Apify client not initialized. Please provide API token.")
        
        print(f"🔍 Scraping TikTok for keywords: {keywords}")
        
        # Apify TikTok scraper actor ID
        actor_id = "clockworks/tiktok-scraper"
        
        # Prepare run input - using hashtags for search
        hashtags = [kw if kw.startswith('#') else f"#{kw}" for kw in keywords]
        
        run_input = {
            "hashtags": hashtags,
            "resultsPerPage": max_posts,
            "shouldDownloadVideos": False,
            "shouldDownloadCovers": False,
            "shouldDownloadSubtitles": False,
        }
        
        # Add date filtering if provided
        if start_date:
            run_input["startDate"] = start_date
            print(f"📅 Filtering from date: {start_date}")
        if end_date:
            run_input["endDate"] = end_date
            print(f"📅 Filtering until date: {end_date}")
        
        print(f"⏳ Running Apify TikTok scraper with hashtags: {hashtags}")
        
        try:
            # Run the actor
            run = self.client.actor(actor_id).call(run_input=run_input)
            
            # Fetch results
            print(f"📥 Fetching results from dataset...")
            items = []
            for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
                items.append(item)
            
            print(f"✅ Scraped {len(items)} TikTok posts")
            
            # Convert to DataFrame
            if items:
                df = pd.DataFrame(items)
                
                # Save scraped data to dedicated folder
                import json
                import os
                
                # Ensure data directory exists
                data_dir = "data/scraped_data"
                os.makedirs(data_dir, exist_ok=True)
                
                # Create filename based on brand name
                filename = f"dataset_tiktok-scraper_{brand_name}.json"
                file_path = os.path.join(data_dir, filename)
                
                # Convert DataFrame to JSON format
                json_data = df.to_dict('records')
                
                # Save to file
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(json_data, f, ensure_ascii=False, indent=2, default=str)
                
                print(f"💾 Saved {len(items)} posts to {file_path}")
                return df
            else:
                print("⚠️  No posts found")
                return pd.DataFrame()
                
        except Exception as e:
            print(f"❌ Error scraping TikTok: {str(e)}")
            raise
    
    def scrape_instagram(
        self,
        keywords: List[str],
        max_posts: int = 100,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        brand_name: str = "default"
    ) -> pd.DataFrame:
        """
        Scrape Instagram posts using Apify
        
        Args:
            keywords: List of search keywords/hashtags
            max_posts: Maximum number of posts to scrape
            start_date: Start date for filtering (YYYY-MM-DD)
            end_date: End date for filtering (YYYY-MM-DD)
        
        Returns:
            DataFrame with scraped posts
        """
        if not self.client:
            raise ValueError("Apify client not initialized. Please provide API token.")
        
        print(f"🔍 Scraping Instagram for keywords: {keywords}")
        
        # Apify Instagram scraper actor ID
        actor_id = "apify/instagram-scraper"
        
        # Prepare search URLs for hashtags
        search_urls = [f"https://www.instagram.com/explore/tags/{kw.replace('#', '')}/" for kw in keywords]
        
        run_input = {
            "directUrls": search_urls,
            "resultsLimit": max_posts,
            "searchLimit": max_posts,
        }
        
        # Add date filtering if provided
        if start_date:
            run_input["startDate"] = start_date
            print(f"📅 Filtering from date: {start_date}")
        if end_date:
            run_input["endDate"] = end_date
            print(f"📅 Filtering until date: {end_date}")
        
        print(f"⏳ Running Apify Instagram scraper...")
        
        try:
            # Run the actor
            run = self.client.actor(actor_id).call(run_input=run_input)
            
            # Fetch results
            print(f"📥 Fetching results from dataset...")
            items = []
            for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
                items.append(item)
            
            print(f"✅ Scraped {len(items)} Instagram posts")
            
            # Convert to DataFrame and save to file
            if items:
                df = pd.DataFrame(items)
                
                # Save scraped data to dedicated folder
                import json
                import os
                
                # Ensure data directory exists
                data_dir = "data/scraped_data"
                os.makedirs(data_dir, exist_ok=True)
                
                # Create filename based on brand name
                filename = f"dataset_instagram-scraper_{brand_name}.json"
                file_path = os.path.join(data_dir, filename)
                
                # Convert DataFrame to JSON format
                json_data = df.to_dict('records')
                
                # Save to file
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(json_data, f, ensure_ascii=False, indent=2, default=str)
                
                print(f"💾 Saved {len(items)} posts to {file_path}")
                return df
            else:
                print("⚠️  No posts found")
                return pd.DataFrame()
                
        except Exception as e:
            print(f"❌ Error scraping Instagram: {str(e)}")
            raise
    
    def scrape_twitter(
        self,
        keywords: List[str],
        max_posts: int = 100,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        brand_name: str = "default"
    ) -> pd.DataFrame:
        """
        Scrape Twitter/X posts using Apify
        
        Args:
            keywords: List of search keywords
            max_posts: Maximum number of posts to scrape
            start_date: Start date for filtering (YYYY-MM-DD)
            end_date: End date for filtering (YYYY-MM-DD)
        
        Returns:
            DataFrame with scraped posts
        """
        if not self.client:
            raise ValueError("Apify client not initialized. Please provide API token.")
        
        print(f"🔍 Scraping Twitter for keywords: {keywords}")
        
        # Use apidojo/tweet-scraper (community actor)
        actor_id = "apidojo/tweet-scraper"
        
        # Prepare search queries
        search_terms = " OR ".join(keywords)
        
        run_input = {
            "searchTerms": [search_terms],
            "maxItems": max_posts,
        }
        
        # Add date filters if provided
        if start_date:
            run_input["startDate"] = start_date
        if end_date:
            run_input["endDate"] = end_date
        
        print(f"⏳ Running Apify Twitter scraper...")
        
        try:
            # Run the actor
            run = self.client.actor(actor_id).call(run_input=run_input)
            
            # Fetch results
            print(f"📥 Fetching results from dataset...")
            items = []
            for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
                items.append(item)
            
            print(f"✅ Scraped {len(items)} Twitter posts")
            
            # Convert to DataFrame and save to file
            if items:
                df = pd.DataFrame(items)
                
                # Save scraped data to dedicated folder
                import json
                import os
                
                # Ensure data directory exists
                data_dir = "data/scraped_data"
                os.makedirs(data_dir, exist_ok=True)
                
                # Create filename based on brand name
                filename = f"dataset_twitter-scraper_{brand_name}.json"
                file_path = os.path.join(data_dir, filename)
                
                # Convert DataFrame to JSON format
                json_data = df.to_dict('records')
                
                # Save to file
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(json_data, f, ensure_ascii=False, indent=2, default=str)
                
                print(f"💾 Saved {len(items)} posts to {file_path}")
                return df
            else:
                print("⚠️  No posts found")
                return pd.DataFrame()
                
        except Exception as e:
            print(f"❌ Error scraping Twitter: {str(e)}")
            raise
    
    def scrape_youtube(
        self,
        keywords: List[str],
        max_posts: int = 100,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        brand_name: str = "default"
    ) -> pd.DataFrame:
        """
        Scrape YouTube videos using Apify
        
        Args:
            keywords: List of search keywords
            max_posts: Maximum number of videos to scrape
            start_date: Start date for filtering (YYYY-MM-DD)
            end_date: End date for filtering (YYYY-MM-DD)
        
        Returns:
            DataFrame with scraped videos
        """
        if not self.client:
            raise ValueError("Apify client not initialized. Please provide API token.")
        
        print(f"🔍 Scraping YouTube for keywords: {keywords}")
        
        # Apify YouTube scraper actor ID
        actor_id = "bernardo/youtube-scraper"
        
        # Prepare search queries
        search_keywords = " OR ".join(keywords)
        
        # Prepare run input
        run_input = {
            "searchKeywords": search_keywords,
            "maxResults": max_posts,
        }
        
        # Add date filtering if provided
        if start_date:
            run_input["startDate"] = start_date
            print(f"📅 Filtering from date: {start_date}")
        if end_date:
            run_input["endDate"] = end_date
            print(f"📅 Filtering until date: {end_date}")
        
        try:
            # Run the actor
            print(f"⏳ Running Apify YouTube scraper...")
            run = self.client.actor(actor_id).call(run_input=run_input)
            
            # Fetch results
            print(f"📥 Fetching results...")
            items = []
            for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
                items.append(item)
            
            print(f"✅ Scraped {len(items)} YouTube videos")
            
            # Convert to DataFrame and save to file
            if items:
                df = pd.DataFrame(items)
                
                # Save scraped data to dedicated folder
                import json
                import os
                
                # Ensure data directory exists
                data_dir = "data/scraped_data"
                os.makedirs(data_dir, exist_ok=True)
                
                # Create filename based on brand name
                filename = f"dataset_youtube-scraper_{brand_name}.json"
                file_path = os.path.join(data_dir, filename)
                
                # Convert DataFrame to JSON format
                json_data = df.to_dict('records')
                
                # Save to file
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(json_data, f, ensure_ascii=False, indent=2, default=str)
                
                print(f"💾 Saved {len(items)} posts to {file_path}")
                return df
            else:
                return pd.DataFrame()
                
        except Exception as e:
            print(f"❌ Error scraping YouTube: {str(e)}")
            raise
    
    def scrape_platform(
        self,
        platform: str,
        keywords: List[str],
        max_posts: int = 100,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Generic method to scrape any supported platform
        
        Args:
            platform: Platform name (tiktok, instagram, twitter, youtube)
            keywords: List of search keywords
            max_posts: Maximum number of posts to scrape
            start_date: Start date for filtering (YYYY-MM-DD)
            end_date: End date for filtering (YYYY-MM-DD)
        
        Returns:
            DataFrame with scraped data
        """
        platform_lower = platform.lower()
        
        scraper_map = {
            'tiktok': self.scrape_tiktok,
            'instagram': self.scrape_instagram,
            'twitter': self.scrape_twitter,
            'youtube': self.scrape_youtube,
        }
        
        if platform_lower not in scraper_map:
            raise ValueError(f"Platform '{platform}' not supported. Supported: {list(scraper_map.keys())}")
        
        scraper_func = scraper_map[platform_lower]
        return scraper_func(keywords, max_posts, start_date, end_date)
    
    def scrape_multiple_platforms(
        self,
        platforms: List[str],
        keywords: List[str],
        max_posts_per_platform: int = 100,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, pd.DataFrame]:
        """
        Scrape multiple platforms
        
        Args:
            platforms: List of platform names
            keywords: List of search keywords
            max_posts_per_platform: Max posts per platform
            start_date: Start date for filtering (YYYY-MM-DD)
            end_date: End date for filtering (YYYY-MM-DD)
        
        Returns:
            Dictionary mapping platform names to DataFrames
        """
        results = {}
        
        for platform in platforms:
            try:
                print(f"\n{'='*80}")
                print(f"📱 Scraping {platform.upper()}...")
                print(f"{'='*80}")
                
                df = self.scrape_platform(
                    platform=platform,
                    keywords=keywords,
                    max_posts=max_posts_per_platform,
                    start_date=start_date,
                    end_date=end_date
                )
                
                results[platform] = df
                
                # Rate limiting - wait between platforms
                time.sleep(2)
                
            except Exception as e:
                print(f"❌ Failed to scrape {platform}: {str(e)}")
                results[platform] = pd.DataFrame()
        
        return results
    
    def scrape_content_comments(
        self,
        content_url: str,
        platform: str,
        max_comments: int = 200
    ) -> pd.DataFrame:
        """
        Scrape comments from individual content for content analysis
        
        Args:
            content_url: URL of the content to scrape comments from
            platform: Platform type (instagram, twitter, youtube, tiktok)
            max_comments: Maximum number of comments to scrape
        
        Returns:
            DataFrame with scraped comments
        """
        if not self.client:
            raise ValueError("Apify client not initialized. Please provide API token.")
        
        print(f"🔍 Scraping comments from {platform}: {content_url}")
        
        try:
            if platform.lower() == "instagram":
                return self._scrape_instagram_comments(content_url, max_comments)
            elif platform.lower() == "twitter":
                return self._scrape_twitter_comments(content_url, max_comments)
            elif platform.lower() == "youtube":
                return self._scrape_youtube_comments(content_url, max_comments)
            elif platform.lower() == "tiktok":
                return self._scrape_tiktok_comments(content_url, max_comments)
            else:
                print(f"⚠️  Unsupported platform for comment scraping: {platform}")
                return pd.DataFrame()
                
        except Exception as e:
            print(f"❌ Error scraping comments from {platform}: {str(e)}")
            return pd.DataFrame()
    
    def _scrape_instagram_comments(self, content_url: str, max_comments: int) -> pd.DataFrame:
        """Scrape Instagram comments using Apify Instagram scraper with comments configuration"""
        # Apify Instagram scraper actor ID
        actor_id = "apify/instagram-scraper"
        
        run_input = {
            "directUrls": [content_url],
            "resultsLimit": max_comments,
            "resultsType": "comments",  # ✅ Configure to scrape comments, not posts
            "searchLimit": max_comments,
        }
        
        print(f"⏳ Running Apify Instagram scraper for comments...")
        
        try:
            # Run the actor
            run = self.client.actor(actor_id).call(run_input=run_input)
            
            # Fetch results
            print(f"📥 Fetching comment results from dataset...")
            dataset_items = list(self.client.dataset(run["defaultDatasetId"]).iterate_items())
            
            if not dataset_items:
                print("⚠️  No comments found")
                return pd.DataFrame()
            
            # Convert to DataFrame
            df = pd.DataFrame(dataset_items)
            
            # Add metadata
            df['scraped_at'] = datetime.now()
            df['platform'] = 'instagram'
            df['content_url'] = content_url
            
            print(f"✅ Instagram comments scraped: {len(df)} comments")
            return df
            
        except Exception as e:
            print(f"❌ Error scraping Instagram comments: {str(e)}")
            raise
    
    def _scrape_twitter_comments(self, content_url: str, max_comments: int) -> pd.DataFrame:
        """Scrape Twitter comments/replies using Apify Twitter scraper"""
        # Apify Twitter scraper actor ID
        actor_id = "apify/twitter-scraper"
        
        run_input = {
            "tweetUrls": [content_url],
            "maxTweets": max_comments,
            "addUserInfo": True,
            "addSearchTerms": False,
        }
        
        print(f"⏳ Running Apify Twitter scraper for comments...")
        
        try:
            # Run the actor
            run = self.client.actor(actor_id).call(run_input=run_input)
            
            # Fetch results
            print(f"📥 Fetching comment results from dataset...")
            dataset_items = list(self.client.dataset(run["defaultDatasetId"]).iterate_items())
            
            if not dataset_items:
                print("⚠️  No comments found")
                return pd.DataFrame()
            
            # Convert to DataFrame
            df = pd.DataFrame(dataset_items)
            
            # Add metadata
            df['scraped_at'] = datetime.now()
            df['platform'] = 'twitter'
            df['content_url'] = content_url
            
            print(f"✅ Twitter comments scraped: {len(df)} comments")
            return df
            
        except Exception as e:
            print(f"❌ Error scraping Twitter comments: {str(e)}")
            raise
    
    def _scrape_youtube_comments(self, content_url: str, max_comments: int) -> pd.DataFrame:
        """Scrape YouTube comments using Apify YouTube scraper"""
        # Apify YouTube scraper actor ID
        actor_id = "apify/youtube-scraper"
        
        run_input = {
            "startUrls": [content_url],
            "maxResults": max_comments,
            "includeComments": True,
            "includeReplies": True,
        }
        
        print(f"⏳ Running Apify YouTube scraper for comments...")
        
        try:
            # Run the actor
            run = self.client.actor(actor_id).call(run_input=run_input)
            
            # Fetch results
            print(f"📥 Fetching comment results from dataset...")
            dataset_items = list(self.client.dataset(run["defaultDatasetId"]).iterate_items())
            
            if not dataset_items:
                print("⚠️  No comments found")
                return pd.DataFrame()
            
            # Convert to DataFrame
            df = pd.DataFrame(dataset_items)
            
            # Add metadata
            df['scraped_at'] = datetime.now()
            df['platform'] = 'youtube'
            df['content_url'] = content_url
            
            print(f"✅ YouTube comments scraped: {len(df)} comments")
            return df
            
        except Exception as e:
            print(f"❌ Error scraping YouTube comments: {str(e)}")
            raise
    
    def _scrape_tiktok_comments(self, content_url: str, max_comments: int) -> pd.DataFrame:
        """Scrape TikTok comments using Apify TikTok scraper"""
        # Apify TikTok scraper actor ID
        actor_id = "apify/tiktok-scraper"
        
        run_input = {
            "startUrls": [content_url],
            "maxResults": max_comments,
            "includeComments": True,
        }
        
        print(f"⏳ Running Apify TikTok scraper for comments...")
        
        try:
            # Run the actor
            run = self.client.actor(actor_id).call(run_input=run_input)
            
            # Fetch results
            print(f"📥 Fetching comment results from dataset...")
            dataset_items = list(self.client.dataset(run["defaultDatasetId"]).iterate_items())
            
            if not dataset_items:
                print("⚠️  No comments found")
                return pd.DataFrame()
            
            # Convert to DataFrame
            df = pd.DataFrame(dataset_items)
            
            # Add metadata
            df['scraped_at'] = datetime.now()
            df['platform'] = 'tiktok'
            df['content_url'] = content_url
            
            print(f"✅ TikTok comments scraped: {len(df)} comments")
            return df
            
        except Exception as e:
            print(f"❌ Error scraping TikTok comments: {str(e)}")
            raise


# Singleton instance
scraper_service = ScraperService()


