#!/usr/bin/env python3
"""
Debug script untuk trending topics
"""
import asyncio
import json
import os
from datetime import datetime, timedelta

async def debug_trending_topics():
    # Simulate the trending topics logic
    brand_name = "bmw"
    start_dt = datetime.now() - timedelta(days=30)
    end_dt = datetime.now()
    
    # Load data from all platforms
    all_scraped_posts = []
    scraping_data_dir = "data/scraped_data"
    
    if os.path.exists(scraping_data_dir):
        available_platforms = ['instagram', 'tiktok', 'twitter']
        print(f"🔍 DEBUG: Processing all available platforms: {available_platforms}")
        
        for platform_name in available_platforms:
            print(f"🔍 DEBUG: Processing platform: {platform_name}")
            
            # Look for files
            import glob
            pattern = f"dataset_{platform_name}-scraper_*_{brand_name}_*.json"
            matching_files = glob.glob(os.path.join(scraping_data_dir, pattern))
            
            if matching_files:
                latest_file = max(matching_files, key=os.path.getctime)
                print(f"🔍 DEBUG: Found file: {latest_file}")
                
                try:
                    with open(latest_file, 'r', encoding='utf-8') as f:
                        scraped_data = json.load(f)
                        print(f"🔍 DEBUG: Loaded {len(scraped_data)} items from {latest_file}")
                        
                        # Process first few items
                        for i, item in enumerate(scraped_data[:3]):
                            try:
                                item['platform'] = platform_name
                                all_scraped_posts.append(item)
                                
                                # Extract topics
                                topics = []
                                
                                # Extract from hashtags
                                hashtags = item.get('hashtags', [])
                                if isinstance(hashtags, list):
                                    for tag in hashtags:
                                        if isinstance(tag, str):
                                            topics.append(tag.replace('#', '').lower())
                                        elif isinstance(tag, dict) and 'name' in tag:
                                            topics.append(tag['name'].replace('#', '').lower())
                                
                                # Extract from captions
                                caption = ""
                                if platform_name == 'instagram':
                                    caption = item.get('caption', '') or item.get('text', '')
                                elif platform_name == 'tiktok':
                                    caption = item.get('description', '') or item.get('text', '')
                                elif platform_name == 'twitter':
                                    caption = item.get('text', '') or item.get('fullText', '')
                                
                                if caption:
                                    import re
                                    words = re.findall(r'\b\w+\b', caption.lower())
                                    common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them', 'car', 'bmw', 'series', 'the', 'game', 'team', 'dream', 'complete', 'destination', 'fun', 'mandatory', 'information', 'according'}
                                    topics.extend([word for word in words if len(word) > 2 and word not in common_words])
                                
                                # Add brand name and platform topics
                                topics.append(brand_name.lower())
                                if platform_name == 'instagram':
                                    topics.extend(['instagram', 'photo', 'post'])
                                elif platform_name == 'tiktok':
                                    topics.extend(['tiktok', 'video', 'short'])
                                elif platform_name == 'twitter':
                                    topics.extend(['twitter', 'tweet', 'social'])
                                
                                # Filter out any non-string topics
                                topics = [str(topic).lower() for topic in topics if isinstance(topic, (str, int, float))]
                                
                                print(f"🔍 DEBUG: Post {i+1} - platform: {platform_name}")
                                print(f"  Hashtags: {hashtags[:3]}")
                                print(f"  Caption: {caption[:50] if caption else 'None'}")
                                print(f"  Topics: {topics[:5]}")
                                print()
                            except Exception as e:
                                print(f"Error processing post {i+1}: {e}")
                                continue
                            
                except Exception as e:
                    print(f"Error loading {latest_file}: {e}")
    
    print(f"📊 Total posts processed: {len(all_scraped_posts)}")

if __name__ == "__main__":
    asyncio.run(debug_trending_topics())
