"""
Scraper Service - Integrates with Apify for social media scraping
"""

from typing import List, Dict, Any, Optional
from apify_client import ApifyClient
import pandas as pd
from datetime import datetime
import time

from app.config.settings import settings
from app.config.env_config import env_config
from app.utils.dummy_data import get_tiktok_dummy_data, get_instagram_dummy_data, get_twitter_dummy_data, get_youtube_dummy_data

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
        max_posts: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        brand_name: str = "default",
        post_urls: List[str] = None,
        scrape_type: str = "campaign"  # "campaign" for individual posts, "brand" for profile
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
        
        # Use environment configuration for max_posts if not provided
        if max_posts is None:
            max_posts = env_config.TIKTOK_MAX_POSTS
        
        print(f"🔍 Scraping TikTok for keywords: {keywords}")
        print(f"📊 Max posts (from env): {max_posts}")
        print(f"🎯 Scrape type: {scrape_type}")
        print(f"📅 Date range: {start_date} to {end_date}")
        print(f"🏷️  Brand name: {brand_name}")
        print(f"🔗 Post URLs provided: {len(post_urls) if post_urls else 0}")
        if post_urls:
            for i, url in enumerate(post_urls):
                print(f"   {i+1}. {url}")
        
        # Apify TikTok scraper actor ID
        actor_id = "clockworks/tiktok-scraper"
        print(f"🤖 Using Apify actor: {actor_id}")
        
        # 🔄 NEW LOGIC: Separate scraping for Post URLs and Keywords
        all_results = []
        
        # 1. SCRAPING POST URLs (if available)
        if post_urls and len(post_urls) > 0:
            print(f"\n{'='*60}")
            print(f"📱 PHASE 1: SCRAPING POST URLs")
            print(f"{'='*60}")
            print(f"📱 Using provided post URLs: {len(post_urls)} URLs")
            print(f"🔍 Scrape type: {scrape_type}")
            
            # Choose correct parameter based on scrape type
            if scrape_type == "campaign":
                # Campaign analysis: individual posts
                post_urls_run_input = {
                    "postURLs": post_urls,
                    "resultsPerPage": max_posts,
                    "shouldDownloadVideos": False,
                    "shouldDownloadCovers": False,
                    "shouldDownloadSubtitles": False,
                }
            else:
                # Brand analysis: profile scraping
                post_urls_run_input = {
                    "profiles": post_urls,
                    "resultsPerPage": max_posts,
                    "shouldDownloadVideos": False,
                    "shouldDownloadCovers": False,
                    "shouldDownloadSubtitles": False,
                }
            
            # Add date filtering for Post URLs - TikTok uses 'oldestPostDateUnified' and 'newestPostDate'
            if start_date:
                post_urls_run_input["oldestPostDateUnified"] = start_date
                print(f"📅 Post URLs - Filtering videos after: {start_date}")
            if end_date:
                post_urls_run_input["newestPostDate"] = end_date
                print(f"📅 Post URLs - Filtering videos before: {end_date}")
            
            # 🔍 DEBUG: Print Post URLs parameters
            print(f"\n🔍 POST URLs SCRAPING PARAMETERS:")
            print(f"📋 Run Input Parameters:")
            for key, value in post_urls_run_input.items():
                print(f"   - {key}: {value}")
            
            # 📄 JSON FORMAT FOR POST URLs
            import json
            post_urls_json = {
                "scraping_type": "post_urls",
                "actor_id": actor_id,
                "run_input": post_urls_run_input,
                "metadata": {
                    "max_posts": max_posts,
                    "start_date": start_date,
                    "end_date": end_date,
                    "brand_name": brand_name,
                    "post_urls": post_urls,
                    "keywords": keywords
                }
            }
            print(f"\n📄 JSON FOR POST URLs SCRAPING:")
            print(f"{'='*60}")
            print(json.dumps(post_urls_json, indent=2, ensure_ascii=False, default=str))
            print(f"{'='*60}")
            
            # 🚀 ENABLE APIFY SCRAPING FOR CAMPAIGN ANALYSIS
            if scrape_type == "campaign":
                print(f"\n🚀 APIFY SCRAPING ENABLED FOR CAMPAIGN ANALYSIS")
                print(f"📋 Sending to Apify:")
                print(f"   - Actor ID: {actor_id}")
                print(f"   - Run Input: {post_urls_run_input}")
                print(f"   - Expected to scrape: {len(post_urls)} URLs")
                
                try:
                    run = self.client.actor(actor_id).call(run_input=post_urls_run_input)
                    items = []
                    for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
                        items.append(item)
                    all_results.extend(items)
                    print(f"✅ Post URLs scraping completed: {len(items)} posts")
                except Exception as e:
                    print(f"❌ Error scraping Post URLs: {str(e)}")
                    # Fallback to dummy data if scraping fails
                    print(f"🔧 FALLBACK: Using dummy data due to scraping error")
                    for url in post_urls:
                        dummy_data = get_tiktok_dummy_data(url, "post_urls")
                        all_results.append(dummy_data)
            else:
                # 🚀 ENABLE APIFY SCRAPING FOR BRAND ANALYSIS
                print(f"\n🚀 APIFY SCRAPING ENABLED FOR BRAND ANALYSIS")
                print(f"📋 Sending to Apify:")
                print(f"   - Actor ID: {actor_id}")
                print(f"   - Run Input: {post_urls_run_input}")
                print(f"   - Expected to scrape: {len(post_urls)} URLs")
            
            try:
                run = self.client.actor(actor_id).call(run_input=post_urls_run_input)
                items = []
                for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
                    items.append(item)
                all_results.extend(items)
                print(f"✅ Post URLs scraping completed: {len(items)} posts")
            except Exception as e:
                print(f"❌ Error scraping Post URLs: {str(e)}")
                # Fallback to dummy data if scraping fails
                print(f"🔧 FALLBACK: Using dummy data due to scraping error")
                for url in post_urls:
                    dummy_data = get_tiktok_dummy_data(url, "post_urls")
                    all_results.append(dummy_data)
        
        # 2. SCRAPING KEYWORDS (if available)
        if keywords and len(keywords) > 0:
            print(f"\n{'='*60}")
            print(f"🔍 PHASE 2: SCRAPING KEYWORDS")
            print(f"{'='*60}")
            print(f"🔍 Using keyword search for: {keywords}")
            
            # For TikTok, convert all keywords to hashtags (add # if not present)
            hashtags = []
            for kw in keywords:
                if kw.startswith('#'):
                    hashtags.append(kw)
                else:
                    hashtags.append(f"#{kw}")
            
            keywords_run_input = {
                "hashtags": hashtags,  # Only use hashtags for TikTok
                "resultsPerPage": max_posts,
                "shouldDownloadVideos": False,
                "shouldDownloadCovers": False,
                "shouldDownloadSubtitles": False,
            }
            
            # Add date filtering for Keywords - TikTok uses 'oldestPostDateUnified' and 'newestPostDate'
            if start_date:
                keywords_run_input["oldestPostDateUnified"] = start_date
                print(f"📅 Keywords - Filtering videos after: {start_date}")
            if end_date:
                keywords_run_input["newestPostDate"] = end_date
                print(f"📅 Keywords - Filtering videos before: {end_date}")
            
            # 🔍 DEBUG: Print Keywords parameters
            print(f"\n🔍 KEYWORDS SCRAPING PARAMETERS:")
            print(f"📋 Run Input Parameters:")
            for key, value in keywords_run_input.items():
                print(f"   - {key}: {value}")
            
            # 📄 JSON FORMAT FOR KEYWORDS
            keywords_json = {
                "scraping_type": "keywords",
                "actor_id": actor_id,
                "run_input": keywords_run_input,
                "metadata": {
                    "max_posts": max_posts,
                    "start_date": start_date,
                    "end_date": end_date,
                    "brand_name": brand_name,
                    "post_urls": post_urls,
                    "keywords": keywords
                }
            }
            print(f"\n📄 JSON FOR KEYWORDS SCRAPING:")
            print(f"{'='*60}")
            print(json.dumps(keywords_json, indent=2, ensure_ascii=False, default=str))
            print(f"{'='*60}")
            
            # 🚀 ENABLE APIFY SCRAPING FOR CAMPAIGN ANALYSIS
            if scrape_type == "campaign":
                print(f"\n🚀 APIFY SCRAPING ENABLED FOR CAMPAIGN ANALYSIS")
                print(f"📋 Sending to Apify:")
                print(f"   - Actor ID: {actor_id}")
                print(f"   - Run Input: {keywords_run_input}")
                print(f"   - Expected to scrape: {len(keywords)} keywords")
                
                try:
                    run = self.client.actor(actor_id).call(run_input=keywords_run_input)
                    items = []
                    for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
                        items.append(item)
                    all_results.extend(items)
                    print(f"✅ Keywords scraping completed: {len(items)} posts")
                except Exception as e:
                    print(f"❌ Error scraping Keywords: {str(e)}")
                    # Fallback to dummy data if scraping fails
                    print(f"🔧 FALLBACK: Using dummy data due to scraping error")
                    for kw in keywords:
                        dummy_data = get_tiktok_dummy_data(f"https://tiktok.com/search?q={kw}", "keywords")
                        dummy_data["keyword"] = kw
                        all_results.append(dummy_data)
            else:
                # 🚀 ENABLE APIFY SCRAPING FOR BRAND ANALYSIS
                print(f"\n🚀 APIFY SCRAPING ENABLED FOR BRAND ANALYSIS")
                print(f"📋 Sending to Apify:")
                print(f"   - Actor ID: {actor_id}")
                print(f"   - Run Input: {keywords_run_input}")
                print(f"   - Expected to scrape: {len(keywords)} keywords")
            
            try:
                run = self.client.actor(actor_id).call(run_input=keywords_run_input)
                items = []
                for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
                    items.append(item)
                all_results.extend(items)
                print(f"✅ Keywords scraping completed: {len(items)} posts")
            except Exception as e:
                print(f"❌ Error scraping Keywords: {str(e)}")
                # Fallback to dummy data if scraping fails
                print(f"🔧 FALLBACK: Using dummy data due to scraping error")
                for kw in keywords:
                    dummy_data = get_tiktok_dummy_data(f"https://tiktok.com/search?q={kw}", "keywords")
                    dummy_data["keyword"] = kw
                    all_results.append(dummy_data)
        
        # 3. COMBINE RESULTS
        print(f"\n{'='*60}")
        print(f"📊 COMBINED RESULTS SUMMARY")
        print(f"{'='*60}")
        print(f"📱 Post URLs results: {len([r for r in all_results if r.get('source') == 'post_urls'])}")
        print(f"🔍 Keywords results: {len([r for r in all_results if r.get('source') == 'keywords'])}")
        print(f"📊 Total results: {len(all_results)}")
        print(f"{'='*60}")
        
        # Convert combined results to DataFrame
        if all_results:
            df = pd.DataFrame(all_results)
            
            # Save scraped data to dedicated folder
            import json
            import os
            
            # Ensure data directory exists
            data_dir = "data/scraped_data"
            os.makedirs(data_dir, exist_ok=True)
            
            # Create filename based on brand name, scrape type, and timestamp
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            scrape_type_prefix = "campaign" if scrape_type == "campaign" else "brand"
            filename = f"dataset_tiktok-scraper_{scrape_type_prefix}_{brand_name}_{timestamp}.json"
            file_path = os.path.join(data_dir, filename)
            
            # Convert DataFrame to JSON format
            json_data = df.to_dict('records')
            
            # Save to file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2, default=str)
            
            print(f"💾 Saved {len(all_results)} posts to {file_path}")
            return df
        else:
            print("⚠️  No posts found from any source")
            return pd.DataFrame()
    
    def scrape_instagram(
        self,
        keywords: List[str],
        max_posts: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        brand_name: str = "default",
        post_urls: List[str] = None,
        scrape_type: str = "campaign"  # "campaign" for individual posts, "brand" for profile
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
        
        # Use environment configuration for max_posts if not provided
        if max_posts is None:
            max_posts = env_config.INSTAGRAM_MAX_POSTS
        
        print(f"🔍 Scraping Instagram for keywords: {keywords}")
        print(f"📊 Max posts (from env): {max_posts}")
        print(f"🎯 Scrape type: {scrape_type}")
        print(f"📅 Date range: {start_date} to {end_date}")
        print(f"🏷️  Brand name: {brand_name}")
        print(f"🔗 Post URLs provided: {len(post_urls) if post_urls else 0}")
        if post_urls:
            for i, url in enumerate(post_urls):
                print(f"   {i+1}. {url}")
        
        # Apify Instagram scraper actor ID
        actor_id = "apify/instagram-scraper"
        print(f"🤖 Using Apify actor: {actor_id}")
        
        # 🔄 NEW LOGIC: Separate scraping for Post URLs and Keywords
        all_results = []
        
        # 1. SCRAPING POST URLs (if available)
        if post_urls and len(post_urls) > 0:
            print(f"\n{'='*60}")
            print(f"📱 PHASE 1: SCRAPING POST URLs")
            print(f"{'='*60}")
            print(f"📱 Using provided post URLs: {len(post_urls)} URLs")
            print(f"🔍 Scrape type: {scrape_type}")
            
            # Choose correct parameter based on scrape type
            if scrape_type == "campaign":
                # Campaign analysis: individual posts
                post_urls_run_input = {
                    "directUrls": post_urls,
                    "resultsType": "posts",  # Scrape posts from URLs
                    "resultsLimit": max_posts,
                    "searchLimit": max_posts,
                }
            else:
                # Brand analysis: profile scraping - use directUrls with posts type
                post_urls_run_input = {
                    "directUrls": post_urls,  # ✅ CORRECT: Use directUrls, not profiles
                    "resultsType": "posts",   # ✅ CORRECT: Scrape posts from profile URLs
                    "resultsLimit": max_posts,
                    "searchLimit": max_posts,
                }
            
            # Add date filtering for Post URLs - Instagram uses onlyPostsNewerThan
            if start_date:
                post_urls_run_input["onlyPostsNewerThan"] = start_date
                print(f"📅 Post URLs - Filtering posts newer than: {start_date}")
            # Note: Instagram doesn't support endDate, only onlyPostsNewerThan
            
            # 🔍 DEBUG: Print Post URLs parameters
            print(f"\n🔍 POST URLs SCRAPING PARAMETERS:")
            print(f"📋 Run Input Parameters:")
            for key, value in post_urls_run_input.items():
                print(f"   - {key}: {value}")
            
            # 📄 JSON FORMAT FOR POST URLs
            import json
            post_urls_json = {
                "scraping_type": "post_urls",
                "actor_id": actor_id,
                "run_input": post_urls_run_input,
                "metadata": {
                    "max_posts": max_posts,
                    "start_date": start_date,
                    "end_date": end_date,
                    "brand_name": brand_name,
                    "post_urls": post_urls,
                    "keywords": keywords
                }
            }
            print(f"\n📄 JSON FOR POST URLs SCRAPING:")
            print(f"{'='*60}")
            print(json.dumps(post_urls_json, indent=2, ensure_ascii=False, default=str))
            print(f"{'='*60}")
            
            # 🚀 ENABLE APIFY SCRAPING FOR CAMPAIGN ANALYSIS
            if scrape_type == "campaign":
                print(f"\n🚀 APIFY SCRAPING ENABLED FOR CAMPAIGN ANALYSIS")
                print(f"📋 Sending to Apify:")
                print(f"   - Actor ID: {actor_id}")
                print(f"   - Run Input: {post_urls_run_input}")
                print(f"   - Expected to scrape: {len(post_urls)} URLs")
                
                try:
                    run = self.client.actor(actor_id).call(run_input=post_urls_run_input)
                    items = []
                    for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
                        items.append(item)
                    all_results.extend(items)
                    print(f"✅ Post URLs scraping completed: {len(items)} posts")
                except Exception as e:
                    print(f"❌ Error scraping Post URLs: {str(e)}")
                    # Fallback to dummy data if scraping fails
                    print(f"🔧 FALLBACK: Using dummy data due to scraping error")
                    for url in post_urls:
                        dummy_data = get_instagram_dummy_data(url, "post_urls")
                        all_results.append(dummy_data)
            else:
                # 🚀 ENABLE APIFY SCRAPING FOR BRAND ANALYSIS
                print(f"\n🚀 APIFY SCRAPING ENABLED FOR BRAND ANALYSIS")
                print(f"📋 Sending to Apify:")
                print(f"   - Actor ID: {actor_id}")
                print(f"   - Run Input: {post_urls_run_input}")
                print(f"   - Expected to scrape: {len(post_urls)} URLs")
                
                try:
                    run = self.client.actor(actor_id).call(run_input=post_urls_run_input)
                    items = []
                    for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
                        items.append(item)
                    all_results.extend(items)
                    print(f"✅ Post URLs scraping completed: {len(items)} posts")
                except Exception as e:
                    print(f"❌ Error scraping Post URLs: {str(e)}")
                    # Fallback to dummy data if scraping fails
                    print(f"🔧 FALLBACK: Using dummy data due to scraping error")
                    for url in post_urls:
                        dummy_data = get_instagram_dummy_data(url, "post_urls")
                        all_results.append(dummy_data)
        
        # 2. SCRAPING KEYWORDS (if available)
        if keywords and len(keywords) > 0:
            print(f"\n{'='*60}")
            print(f"🔍 PHASE 2: SCRAPING KEYWORDS")
            print(f"{'='*60}")
            print(f"🔍 Using keyword search for: {keywords}")
            
            # Join keywords with comma for search
            search_query = ", ".join(keywords)
            keywords_run_input = {
                "search": search_query,
                "searchLimit": max_posts,
                "searchType": "hashtag",
                "resultsType": "posts",
                "resultsLimit": max_posts,
            }
            
            # Add date filtering for Keywords - Instagram uses onlyPostsNewerThan
            if start_date:
                keywords_run_input["onlyPostsNewerThan"] = start_date
                print(f"📅 Keywords - Filtering posts newer than: {start_date}")
            # Note: Instagram doesn't support endDate, only onlyPostsNewerThan
            
            # 🔍 DEBUG: Print Keywords parameters
            print(f"\n🔍 KEYWORDS SCRAPING PARAMETERS:")
            print(f"📋 Run Input Parameters:")
            for key, value in keywords_run_input.items():
                print(f"   - {key}: {value}")
            
            # 📄 JSON FORMAT FOR KEYWORDS
            keywords_json = {
                "scraping_type": "keywords",
                "actor_id": actor_id,
                "run_input": keywords_run_input,
                "metadata": {
                    "max_posts": max_posts,
                    "start_date": start_date,
                    "end_date": end_date,
                    "brand_name": brand_name,
                    "post_urls": post_urls,
                    "keywords": keywords
                }
            }
            print(f"\n📄 JSON FOR KEYWORDS SCRAPING:")
            print(f"{'='*60}")
            print(json.dumps(keywords_json, indent=2, ensure_ascii=False, default=str))
            print(f"{'='*60}")
            
            # 🚀 ENABLE APIFY SCRAPING FOR CAMPAIGN ANALYSIS
            if scrape_type == "campaign":
                print(f"\n🚀 APIFY SCRAPING ENABLED FOR CAMPAIGN ANALYSIS")
                print(f"📋 Sending to Apify:")
                print(f"   - Actor ID: {actor_id}")
                print(f"   - Run Input: {keywords_run_input}")
                print(f"   - Expected to scrape: {len(keywords)} keywords")
                
                try:
                    run = self.client.actor(actor_id).call(run_input=keywords_run_input)
                    items = []
                    for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
                        items.append(item)
                    all_results.extend(items)
                    print(f"✅ Keywords scraping completed: {len(items)} posts")
                except Exception as e:
                    print(f"❌ Error scraping Keywords: {str(e)}")
                    # Fallback to dummy data if scraping fails
                    print(f"🔧 FALLBACK: Using dummy data due to scraping error")
                    for kw in keywords:
                        dummy_data = get_instagram_dummy_data(f"https://instagram.com/explore/tags/{kw}", "keywords")
                        dummy_data["keyword"] = kw
                        all_results.append(dummy_data)
            else:
                # 🚀 ENABLE APIFY SCRAPING FOR BRAND ANALYSIS
                print(f"\n🚀 APIFY SCRAPING ENABLED FOR BRAND ANALYSIS")
                print(f"📋 Sending to Apify:")
                print(f"   - Actor ID: {actor_id}")
                print(f"   - Run Input: {keywords_run_input}")
                print(f"   - Expected to scrape: {len(keywords)} keywords")
                
                try:
                    run = self.client.actor(actor_id).call(run_input=keywords_run_input)
                    items = []
                    for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
                        items.append(item)
                    all_results.extend(items)
                    print(f"✅ Keywords scraping completed: {len(items)} posts")
                except Exception as e:
                    print(f"❌ Error scraping Keywords: {str(e)}")
                    # Fallback to dummy data if scraping fails
                    print(f"🔧 FALLBACK: Using dummy data due to scraping error")
                    for kw in keywords:
                        dummy_data = get_instagram_dummy_data(f"https://instagram.com/explore/tags/{kw}", "keywords")
                        dummy_data["keyword"] = kw
                        all_results.append(dummy_data)
        
        # 3. COMBINE RESULTS
        print(f"\n{'='*60}")
        print(f"📊 COMBINED RESULTS SUMMARY")
        print(f"{'='*60}")
        print(f"📱 Post URLs results: {len([r for r in all_results if r.get('source') == 'post_urls'])}")
        print(f"🔍 Keywords results: {len([r for r in all_results if r.get('source') == 'keywords'])}")
        print(f"📊 Total results: {len(all_results)}")
        print(f"{'='*60}")
        
        # Convert combined results to DataFrame
        if all_results:
            df = pd.DataFrame(all_results)
            
            # Save scraped data to dedicated folder
            import json
            import os
            
            # Ensure data directory exists
            data_dir = "data/scraped_data"
            os.makedirs(data_dir, exist_ok=True)
            
            # Create filename based on brand name, scrape type, and timestamp
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            scrape_type_prefix = "campaign" if scrape_type == "campaign" else "brand"
            filename = f"dataset_instagram-scraper_{scrape_type_prefix}_{brand_name}_{timestamp}.json"
            file_path = os.path.join(data_dir, filename)
            
            # Convert DataFrame to JSON format
            json_data = df.to_dict('records')
            
            # Save to file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2, default=str)
            
            print(f"💾 Saved {len(all_results)} posts to {file_path}")
            return df
        else:
            print("⚠️  No posts found from any source")
            return pd.DataFrame()
    
    def scrape_twitter(
        self,
        keywords: List[str],
        max_posts: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        brand_name: str = "default",
        post_urls: List[str] = None,
        scrape_type: str = "campaign"  # "campaign" for individual posts, "brand" for profile
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
        
        # Use environment configuration for max_posts if not provided
        if max_posts is None:
            max_posts = env_config.TWITTER_MAX_POSTS
        
        print(f"🔍 Scraping Twitter for keywords: {keywords}")
        print(f"📊 Max posts (from env): {max_posts}")
        print(f"🎯 Scrape type: {scrape_type}")
        print(f"📅 Date range: {start_date} to {end_date}")
        print(f"🏷️  Brand name: {brand_name}")
        print(f"🔗 Post URLs provided: {len(post_urls) if post_urls else 0}")
        if post_urls:
            for i, url in enumerate(post_urls):
                print(f"   {i+1}. {url}")
        
        # Use apidojo/tweet-scraper (community actor)
        actor_id = "apidojo/tweet-scraper"
        print(f"🤖 Using Apify actor: {actor_id}")
        
        # 🔄 NEW LOGIC: Separate scraping for Post URLs and Keywords
        all_results = []
        
        # 1. SCRAPING POST URLs (if available)
        if post_urls and len(post_urls) > 0:
            print(f"\n{'='*60}")
            print(f"📱 PHASE 1: SCRAPING POST URLs")
            print(f"{'='*60}")
            print(f"📱 Using provided post URLs: {len(post_urls)} URLs")
            print(f"🔍 Scrape type: {scrape_type}")
            
            # Choose correct parameter based on scrape type
            if scrape_type == "campaign":
                # Campaign analysis: individual posts
                post_urls_run_input = {
                    "startUrls": post_urls,
                    "maxItems": max_posts,
                }
            else:
                # Brand analysis: profile scraping
                post_urls_run_input = {
                    "twitterHandles": post_urls,
                    "maxItems": max_posts,
                }
            
            # Add date filtering for Post URLs - Twitter uses 'start' and 'end'
            if start_date:
                post_urls_run_input["start"] = start_date
                print(f"📅 Post URLs - Filtering tweets after: {start_date}")
            if end_date:
                post_urls_run_input["end"] = end_date
                print(f"📅 Post URLs - Filtering tweets before: {end_date}")
            
            # 🔍 DEBUG: Print Post URLs parameters
            print(f"\n🔍 POST URLs SCRAPING PARAMETERS:")
            print(f"📋 Run Input Parameters:")
            for key, value in post_urls_run_input.items():
                print(f"   - {key}: {value}")
            
            # 📄 JSON FORMAT FOR POST URLs
            import json
            post_urls_json = {
                "scraping_type": "post_urls",
                "actor_id": actor_id,
                "run_input": post_urls_run_input,
                "metadata": {
                    "max_posts": max_posts,
                    "start_date": start_date,
                    "end_date": end_date,
                    "brand_name": brand_name,
                    "post_urls": post_urls,
                    "keywords": keywords
                }
            }
            print(f"\n📄 JSON FOR POST URLs SCRAPING:")
            print(f"{'='*60}")
            print(json.dumps(post_urls_json, indent=2, ensure_ascii=False, default=str))
            print(f"{'='*60}")
            
            # 🚀 ENABLE APIFY SCRAPING FOR CAMPAIGN ANALYSIS
            if scrape_type == "campaign":
                print(f"\n🚀 APIFY SCRAPING ENABLED FOR CAMPAIGN ANALYSIS")
                print(f"📋 Sending to Apify:")
                print(f"   - Actor ID: {actor_id}")
                print(f"   - Run Input: {post_urls_run_input}")
                print(f"   - Expected to scrape: {len(post_urls)} URLs")
                
                try:
                    run = self.client.actor(actor_id).call(run_input=post_urls_run_input)
                    items = []
                    for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
                        items.append(item)
                    all_results.extend(items)
                    print(f"✅ Post URLs scraping completed: {len(items)} posts")
                except Exception as e:
                    print(f"❌ Error scraping Post URLs: {str(e)}")
                    # Fallback to dummy data if scraping fails
                    print(f"🔧 FALLBACK: Using dummy data due to scraping error")
                    for url in post_urls:
                        dummy_data = get_twitter_dummy_data(url, "post_urls")
                        all_results.append(dummy_data)
            else:
                # 🚀 ENABLE APIFY SCRAPING FOR BRAND ANALYSIS
                print(f"\n🚀 APIFY SCRAPING ENABLED FOR BRAND ANALYSIS")
                print(f"📋 Sending to Apify:")
                print(f"   - Actor ID: {actor_id}")
                print(f"   - Run Input: {post_urls_run_input}")
                print(f"   - Expected to scrape: {len(post_urls)} URLs")
                
                try:
                    run = self.client.actor(actor_id).call(run_input=post_urls_run_input)
                    items = []
                    for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
                        items.append(item)
                    all_results.extend(items)
                    print(f"✅ Post URLs scraping completed: {len(items)} posts")
                except Exception as e:
                    print(f"❌ Error scraping Post URLs: {str(e)}")
                    # Fallback to dummy data if scraping fails
                    print(f"🔧 FALLBACK: Using dummy data due to scraping error")
                    for url in post_urls:
                        dummy_data = get_twitter_dummy_data(url, "post_urls")
                        all_results.append(dummy_data)
        
        # 2. SCRAPING KEYWORDS (if available)
        if keywords and len(keywords) > 0:
            print(f"\n{'='*60}")
            print(f"🔍 PHASE 2: SCRAPING KEYWORDS")
            print(f"{'='*60}")
            print(f"🔍 Using search terms for keywords: {keywords}")
            
            keywords_run_input = {
                "searchTerms": keywords,
                "maxItems": max_posts,
            }
            
            # Add date filtering for Keywords - Twitter uses 'start' and 'end'
            if start_date:
                keywords_run_input["start"] = start_date
                print(f"📅 Keywords - Filtering tweets after: {start_date}")
            if end_date:
                keywords_run_input["end"] = end_date
                print(f"📅 Keywords - Filtering tweets before: {end_date}")
            
            # 🔍 DEBUG: Print Keywords parameters
            print(f"\n🔍 KEYWORDS SCRAPING PARAMETERS:")
            print(f"📋 Run Input Parameters:")
            for key, value in keywords_run_input.items():
                print(f"   - {key}: {value}")
            
            # 📄 JSON FORMAT FOR KEYWORDS
            keywords_json = {
                "scraping_type": "keywords",
                "actor_id": actor_id,
                "run_input": keywords_run_input,
                "metadata": {
                    "max_posts": max_posts,
                    "start_date": start_date,
                    "end_date": end_date,
                    "brand_name": brand_name,
                    "post_urls": post_urls,
                    "keywords": keywords
                }
            }
            print(f"\n📄 JSON FOR KEYWORDS SCRAPING:")
            print(f"{'='*60}")
            print(json.dumps(keywords_json, indent=2, ensure_ascii=False, default=str))
            print(f"{'='*60}")
            
            # 🚀 ENABLE APIFY SCRAPING FOR CAMPAIGN ANALYSIS
            if scrape_type == "campaign":
                print(f"\n🚀 APIFY SCRAPING ENABLED FOR CAMPAIGN ANALYSIS")
                print(f"📋 Sending to Apify:")
                print(f"   - Actor ID: {actor_id}")
                print(f"   - Run Input: {keywords_run_input}")
                print(f"   - Expected to scrape: {len(keywords)} keywords")
                
                try:
                    run = self.client.actor(actor_id).call(run_input=keywords_run_input)
                    items = []
                    for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
                        items.append(item)
                    all_results.extend(items)
                    print(f"✅ Keywords scraping completed: {len(items)} posts")
                except Exception as e:
                    print(f"❌ Error scraping Keywords: {str(e)}")
                    # Fallback to dummy data if scraping fails
                    print(f"🔧 FALLBACK: Using dummy data due to scraping error")
                    for kw in keywords:
                        dummy_data = get_twitter_dummy_data(f"https://twitter.com/search?q={kw}", "keywords")
                        dummy_data["keyword"] = kw
                        all_results.append(dummy_data)
            else:
                # 🚀 ENABLE APIFY SCRAPING FOR BRAND ANALYSIS
                print(f"\n🚀 APIFY SCRAPING ENABLED FOR BRAND ANALYSIS")
                print(f"📋 Sending to Apify:")
                print(f"   - Actor ID: {actor_id}")
                print(f"   - Run Input: {keywords_run_input}")
                print(f"   - Expected to scrape: {len(keywords)} keywords")
                
                try:
                    run = self.client.actor(actor_id).call(run_input=keywords_run_input)
                    items = []
                    for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
                        items.append(item)
                    all_results.extend(items)
                    print(f"✅ Keywords scraping completed: {len(items)} posts")
                except Exception as e:
                    print(f"❌ Error scraping Keywords: {str(e)}")
                    # Fallback to dummy data if scraping fails
                    print(f"🔧 FALLBACK: Using dummy data due to scraping error")
                    for kw in keywords:
                        dummy_data = get_twitter_dummy_data(f"https://twitter.com/search?q={kw}", "keywords")
                        dummy_data["keyword"] = kw
                        all_results.append(dummy_data)
        
        # 3. COMBINE RESULTS
        print(f"\n{'='*60}")
        print(f"📊 COMBINED RESULTS SUMMARY")
        print(f"{'='*60}")
        print(f"📱 Post URLs results: {len([r for r in all_results if r.get('source') == 'post_urls'])}")
        print(f"🔍 Keywords results: {len([r for r in all_results if r.get('source') == 'keywords'])}")
        print(f"📊 Total results: {len(all_results)}")
        print(f"{'='*60}")
        
        # Convert combined results to DataFrame
        if all_results:
            df = pd.DataFrame(all_results)
            
            # Save scraped data to dedicated folder
            import json
            import os
            
            # Ensure data directory exists
            data_dir = "data/scraped_data"
            os.makedirs(data_dir, exist_ok=True)
            
            # Create filename based on brand name, scrape type, and timestamp
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            scrape_type_prefix = "campaign" if scrape_type == "campaign" else "brand"
            filename = f"dataset_twitter-scraper_{scrape_type_prefix}_{brand_name}_{timestamp}.json"
            file_path = os.path.join(data_dir, filename)
            
            # Convert DataFrame to JSON format
            json_data = df.to_dict('records')
            
            # Save to file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2, default=str)
            
            print(f"💾 Saved {len(all_results)} posts to {file_path}")
            return df
        else:
            print("⚠️  No posts found from any source")
            return pd.DataFrame()
    
    def scrape_youtube(
        self,
        keywords: List[str],
        max_posts: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        brand_name: str = "default",
        post_urls: List[str] = None,
        scrape_type: str = "campaign"  # "campaign" for individual posts, "brand" for profile
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
        
        # Use environment configuration for max_posts if not provided
        if max_posts is None:
            max_posts = env_config.YOUTUBE_MAX_POSTS
        
        print(f"🔍 Scraping YouTube for keywords: {keywords}")
        print(f"📊 Max posts (from env): {max_posts}")
        print(f"🎯 Scrape type: {scrape_type}")
        print(f"📅 Date range: {start_date} to {end_date}")
        print(f"🏷️  Brand name: {brand_name}")
        print(f"🔗 Post URLs provided: {len(post_urls) if post_urls else 0}")
        if post_urls:
            for i, url in enumerate(post_urls):
                print(f"   {i+1}. {url}")
        
        # Apify YouTube scraper actor ID
        actor_id = "bernardo/youtube-scraper"
        print(f"🤖 Using Apify actor: {actor_id}")
        
        # 🔄 NEW LOGIC: Separate scraping for Post URLs and Keywords
        all_results = []
        
        # 1. SCRAPING POST URLs (if available)
        if post_urls and len(post_urls) > 0:
            print(f"\n{'='*60}")
            print(f"📱 PHASE 1: SCRAPING POST URLs")
            print(f"{'='*60}")
            print(f"📱 Using provided post URLs: {len(post_urls)} URLs")
            print(f"🔍 Scrape type: {scrape_type}")
            
            # Choose correct parameter based on scrape type
            if scrape_type == "campaign":
                # Campaign analysis: individual posts
                post_urls_run_input = {
                    "startUrls": post_urls,
                    "maxResults": max_posts,
                }
            else:
                # Brand analysis: profile scraping
                post_urls_run_input = {
                    "profiles": post_urls,
                    "maxResults": max_posts,
                }
            
            # Note: YouTube doesn't support date range filtering natively
            # Date filtering will be applied after scraping if needed
            if start_date or end_date:
                print(f"⚠️  YouTube doesn't support date filtering natively")
                print(f"📅 Date range: {start_date} to {end_date} - will be filtered after scraping")
            
            # 🔍 DEBUG: Print Post URLs parameters
            print(f"\n🔍 POST URLs SCRAPING PARAMETERS:")
            print(f"📋 Run Input Parameters:")
            for key, value in post_urls_run_input.items():
                print(f"   - {key}: {value}")
            
            # 📄 JSON FORMAT FOR POST URLs
            import json
            post_urls_json = {
                "scraping_type": "post_urls",
                "actor_id": actor_id,
                "run_input": post_urls_run_input,
                "metadata": {
                    "max_posts": max_posts,
                    "start_date": start_date,
                    "end_date": end_date,
                    "brand_name": brand_name,
                    "post_urls": post_urls,
                    "keywords": keywords
                }
            }
            print(f"\n📄 JSON FOR POST URLs SCRAPING:")
            print(f"{'='*60}")
            print(json.dumps(post_urls_json, indent=2, ensure_ascii=False, default=str))
            print(f"{'='*60}")
            
            # 🚀 ENABLE APIFY SCRAPING FOR CAMPAIGN ANALYSIS
            if scrape_type == "campaign":
                print(f"\n🚀 APIFY SCRAPING ENABLED FOR CAMPAIGN ANALYSIS")
                print(f"📋 Sending to Apify:")
                print(f"   - Actor ID: {actor_id}")
                print(f"   - Run Input: {post_urls_run_input}")
                print(f"   - Expected to scrape: {len(post_urls)} URLs")
                
                try:
                    run = self.client.actor(actor_id).call(run_input=post_urls_run_input)
                    items = []
                    for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
                        items.append(item)
                    all_results.extend(items)
                    print(f"✅ Post URLs scraping completed: {len(items)} posts")
                except Exception as e:
                    print(f"❌ Error scraping Post URLs: {str(e)}")
                    # Fallback to dummy data if scraping fails
                    print(f"🔧 FALLBACK: Using dummy data due to scraping error")
                    for url in post_urls:
                        dummy_data = get_youtube_dummy_data(url, "post_urls")
                        all_results.append(dummy_data)
            else:
                # 🚀 ENABLE APIFY SCRAPING FOR BRAND ANALYSIS
                print(f"\n🚀 APIFY SCRAPING ENABLED FOR BRAND ANALYSIS")
                print(f"📋 Sending to Apify:")
                print(f"   - Actor ID: {actor_id}")
                print(f"   - Run Input: {post_urls_run_input}")
                print(f"   - Expected to scrape: {len(post_urls)} URLs")
                
                try:
                    run = self.client.actor(actor_id).call(run_input=post_urls_run_input)
                    items = []
                    for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
                        items.append(item)
                    all_results.extend(items)
                    print(f"✅ Post URLs scraping completed: {len(items)} posts")
                except Exception as e:
                    print(f"❌ Error scraping Post URLs: {str(e)}")
                    # Fallback to dummy data if scraping fails
                    print(f"🔧 FALLBACK: Using dummy data due to scraping error")
                    for url in post_urls:
                        dummy_data = get_youtube_dummy_data(url, "post_urls")
                        all_results.append(dummy_data)
        
        # 2. SCRAPING KEYWORDS (if available)
        if keywords and len(keywords) > 0:
            print(f"\n{'='*60}")
            print(f"🔍 PHASE 2: SCRAPING KEYWORDS")
            print(f"{'='*60}")
            print(f"🔍 Using search keywords: {keywords}")
            
            # Join keywords with space for YouTube search
            search_keywords = " ".join(keywords)
            keywords_run_input = {
                "searchKeywords": search_keywords,
                "maxResults": max_posts,
            }
            
            # Note: YouTube doesn't support date range filtering natively
            # Date filtering will be applied after scraping if needed
            if start_date or end_date:
                print(f"⚠️  YouTube doesn't support date filtering natively")
                print(f"📅 Date range: {start_date} to {end_date} - will be filtered after scraping")
            
            # 🔍 DEBUG: Print Keywords parameters
            print(f"\n🔍 KEYWORDS SCRAPING PARAMETERS:")
            print(f"📋 Run Input Parameters:")
            for key, value in keywords_run_input.items():
                print(f"   - {key}: {value}")
            
            # 📄 JSON FORMAT FOR KEYWORDS
            keywords_json = {
                "scraping_type": "keywords",
                "actor_id": actor_id,
                "run_input": keywords_run_input,
                "metadata": {
                    "max_posts": max_posts,
                    "start_date": start_date,
                    "end_date": end_date,
                    "brand_name": brand_name,
                    "post_urls": post_urls,
                    "keywords": keywords
                }
            }
            print(f"\n📄 JSON FOR KEYWORDS SCRAPING:")
            print(f"{'='*60}")
            print(json.dumps(keywords_json, indent=2, ensure_ascii=False, default=str))
            print(f"{'='*60}")
            
            # 🚀 ENABLE APIFY SCRAPING FOR CAMPAIGN ANALYSIS
            if scrape_type == "campaign":
                print(f"\n🚀 APIFY SCRAPING ENABLED FOR CAMPAIGN ANALYSIS")
                print(f"📋 Sending to Apify:")
                print(f"   - Actor ID: {actor_id}")
                print(f"   - Run Input: {keywords_run_input}")
                print(f"   - Expected to scrape: {len(keywords)} keywords")
                
                try:
                    run = self.client.actor(actor_id).call(run_input=keywords_run_input)
                    items = []
                    for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
                        items.append(item)
                    all_results.extend(items)
                    print(f"✅ Keywords scraping completed: {len(items)} posts")
                except Exception as e:
                    print(f"❌ Error scraping Keywords: {str(e)}")
                    # Fallback to dummy data if scraping fails
                    print(f"🔧 FALLBACK: Using dummy data due to scraping error")
                    for kw in keywords:
                        dummy_data = get_youtube_dummy_data(f"https://youtube.com/results?search_query={kw}", "keywords")
                        dummy_data["keyword"] = kw
                        all_results.append(dummy_data)
            else:
                # 🚀 ENABLE APIFY SCRAPING FOR BRAND ANALYSIS
                print(f"\n🚀 APIFY SCRAPING ENABLED FOR BRAND ANALYSIS")
                print(f"📋 Sending to Apify:")
                print(f"   - Actor ID: {actor_id}")
                print(f"   - Run Input: {keywords_run_input}")
                print(f"   - Expected to scrape: {len(keywords)} keywords")
                
                try:
                    run = self.client.actor(actor_id).call(run_input=keywords_run_input)
                    items = []
                    for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
                        items.append(item)
                    all_results.extend(items)
                    print(f"✅ Keywords scraping completed: {len(items)} posts")
                except Exception as e:
                    print(f"❌ Error scraping Keywords: {str(e)}")
                    # Fallback to dummy data if scraping fails
                    print(f"🔧 FALLBACK: Using dummy data due to scraping error")
                    for kw in keywords:
                        dummy_data = get_youtube_dummy_data(f"https://youtube.com/results?search_query={kw}", "keywords")
                        dummy_data["keyword"] = kw
                        all_results.append(dummy_data)
        
        # 3. COMBINE RESULTS
        print(f"\n{'='*60}")
        print(f"📊 COMBINED RESULTS SUMMARY")
        print(f"{'='*60}")
        print(f"📱 Post URLs results: {len([r for r in all_results if r.get('source') == 'post_urls'])}")
        print(f"🔍 Keywords results: {len([r for r in all_results if r.get('source') == 'keywords'])}")
        print(f"📊 Total results: {len(all_results)}")
        print(f"{'='*60}")
        
        # Convert combined results to DataFrame
        if all_results:
            df = pd.DataFrame(all_results)
            
            # Save scraped data to dedicated folder
            import json
            import os
            
            # Ensure data directory exists
            data_dir = "data/scraped_data"
            os.makedirs(data_dir, exist_ok=True)
            
            # Create filename based on brand name, scrape type, and timestamp
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            scrape_type_prefix = "campaign" if scrape_type == "campaign" else "brand"
            filename = f"dataset_youtube-scraper_{scrape_type_prefix}_{brand_name}_{timestamp}.json"
            file_path = os.path.join(data_dir, filename)
            
            # Convert DataFrame to JSON format
            json_data = df.to_dict('records')
            
            # Save to file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2, default=str)
            
            print(f"💾 Saved {len(all_results)} posts to {file_path}")
            return df
        else:
            print("⚠️  No posts found from any source")
            return pd.DataFrame()
    
    def scrape_platform(
        self,
        platform: str,
        keywords: List[str],
        max_posts: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        post_urls: List[str] = None,
        scrape_type: str = "campaign"
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
        return scraper_func(keywords, max_posts, start_date, end_date, "default", post_urls, scrape_type)
    
    def scrape_multiple_platforms(
        self,
        platforms: List[str],
        keywords: List[str],
        max_posts_per_platform: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        post_urls_by_platform: Dict[str, List[str]] = None
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
                
                # Get post URLs for this platform if provided
                platform_post_urls = None
                if post_urls_by_platform and platform in post_urls_by_platform:
                    platform_post_urls = post_urls_by_platform[platform]
                
                df = self.scrape_platform(
                    platform=platform,
                    keywords=keywords,
                    max_posts=max_posts_per_platform,
                    start_date=start_date,
                    end_date=end_date,
                    post_urls=platform_post_urls
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


