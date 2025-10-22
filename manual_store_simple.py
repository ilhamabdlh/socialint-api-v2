"""
Simple Manual Data Store Script for Hyundai Instagram Data
This is a simplified version that stores data without AI analysis
"""

import asyncio
import json
import pandas as pd
import random
from datetime import datetime
from pathlib import Path
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from app.database.mongodb import connect_to_mongodb
from app.services.database_service import db_service
from app.models.database import (
    Brand, Post, PlatformType, BrandAnalysis
)


# Simple sentiment analysis based on hashtags and caption
def simple_sentiment_analysis(caption, hashtags):
    """Simple rule-based sentiment analysis"""
    positive_words = ['love', 'amazing', 'beautiful', 'best', 'great', 'perfect', 'excellent', 'wonderful']
    negative_words = ['bad', 'worst', 'terrible', 'awful', 'hate', 'poor', 'disappointing']
    
    text = (caption + ' ' + ' '.join(hashtags)).lower()
    
    positive_count = sum(1 for word in positive_words if word in text)
    negative_count = sum(1 for word in negative_words if word in text)
    
    if positive_count > negative_count:
        return "Positive", 0.6
    elif negative_count > positive_count:
        return "Negative", -0.6
    else:
        return "Neutral", 0.0


# Simple topic extraction based on hashtags
def simple_topic_extraction(hashtags, caption):
    """Extract main topic from hashtags"""
    if not hashtags:
        return "General"
    
    # Common automotive topics
    automotive_topics = {
        'design': ['design', 'styling', 'architecture', 'aesthetic'],
        'technology': ['tech', 'innovation', 'future', 'electric', 'ev'],
        'performance': ['performance', 'power', 'speed', 'drive'],
        'features': ['features', 'interior', 'comfort', 'safety'],
        'lifestyle': ['lifestyle', 'adventure', 'journey', 'travel']
    }
    
    # Check hashtags for topic keywords
    for topic, keywords in automotive_topics.items():
        for keyword in keywords:
            if any(keyword.lower() in tag.lower() for tag in hashtags):
                return topic.capitalize()
    
    # Return first hashtag as topic if no match
    return hashtags[0] if hashtags else "General"


# Simple emotion detection
def simple_emotion_detection(sentiment):
    """Map sentiment to basic emotions"""
    if sentiment == "Positive":
        return random.choice(['joy', 'trust', 'anticipation'])
    elif sentiment == "Negative":
        return random.choice(['sadness', 'anger', 'fear'])
    else:
        return 'neutral'


# Analyze demographics from real data
def analyze_demographics_from_data(item):
    """Analyze demographics based on available data patterns"""
    caption = item.get('caption', '')
    hashtags = item.get('hashtags', [])
    like_count = int(item.get('likesCount', 0)) if pd.notna(item.get('likesCount')) else 0
    comment_count = int(item.get('commentsCount', 0)) if pd.notna(item.get('commentsCount')) else 0
    owner_name = item.get('ownerFullName', '').lower()
    owner_username = item.get('ownerUsername', '').lower()
    
    # Analyze age group based on content type and engagement patterns
    age_group = "25-34"  # Default
    
    # Analyze based on content sophistication and engagement
    text_complexity = len(caption.split()) if caption else 0
    total_engagement = like_count + comment_count
    
    # Simple heuristics based on data patterns
    if total_engagement > 50 and text_complexity > 20:
        age_group = "25-34"  # More sophisticated content, higher engagement
    elif total_engagement > 20 and text_complexity > 10:
        age_group = "35-44"  # Moderate engagement, good content
    elif total_engagement > 100:
        age_group = "18-24"  # Very high engagement, likely younger audience
    elif text_complexity > 30:
        age_group = "45-54"  # Very detailed content, likely older professional
    elif total_engagement < 5:
        age_group = "55-64"  # Lower engagement, likely older demographic
    
    # Analyze gender based on content themes and engagement patterns
    gender = "Other"  # Default
    
    # Analyze based on content themes
    content_text = (caption + ' ' + ' '.join(hashtags)).lower()
    
    # Keywords that might indicate gender preferences (based on general patterns)
    lifestyle_keywords = ['design', 'style', 'beauty', 'fashion', 'lifestyle', 'interior']
    tech_keywords = ['tech', 'innovation', 'performance', 'engineering', 'specs', 'technical']
    adventure_keywords = ['adventure', 'travel', 'road', 'journey', 'explore', 'outdoor']
    
    lifestyle_score = sum(1 for word in lifestyle_keywords if word in content_text)
    tech_score = sum(1 for word in tech_keywords if word in content_text)
    adventure_score = sum(1 for word in adventure_keywords if word in content_text)
    
    # Simple heuristic based on content themes
    if lifestyle_score > tech_score and lifestyle_score > adventure_score:
        gender = "Female"
    elif tech_score > lifestyle_score and tech_score > adventure_score:
        gender = "Male"
    elif adventure_score > 0:
        gender = "Male"  # Adventure content tends to be more male-oriented
    else:
        gender = "Other"
    
    # Analyze location based on owner name patterns and content
    location = "Jakarta"  # Default to Jakarta as major Indonesian city
    
    # Simple location analysis based on owner patterns
    indonesian_cities = {
        'jakarta': ['jakarta', 'jkt', 'jaksel', 'jakut', 'jakpus', 'jaktim'],
        'surabaya': ['surabaya', 'sby', 'jawa timur'],
        'bandung': ['bandung', 'bdg', 'jawa barat', 'west java'],
        'medan': ['medan', 'sumatera utara', 'north sumatra'],
        'semarang': ['semarang', 'jawa tengah', 'central java'],
        'palembang': ['palembang', 'sumatera selatan', 'south sumatra'],
        'makassar': ['makassar', 'sulawesi selatan', 'south sulawesi'],
        'bekasi': ['bekasi', 'jabodetabek'],
        'tangerang': ['tangerang', 'jabodetabek'],
        'depok': ['depok', 'jabodetabek']
    }
    
    # Check owner name and username for location hints
    owner_text = (owner_name + ' ' + owner_username).lower()
    
    for city, keywords in indonesian_cities.items():
        if any(keyword in owner_text for keyword in keywords):
            location = city.capitalize()
            break
    
    # If no location found in owner info, use content analysis
    if location == "Jakarta":
        location_keywords = {
            'Surabaya': ['surabaya', 'sby', 'jawa timur'],
            'Bandung': ['bandung', 'bdg', 'jawa barat'],
            'Medan': ['medan', 'sumatera utara'],
            'Semarang': ['semarang', 'jawa tengah'],
            'Palembang': ['palembang', 'sumatera selatan'],
            'Makassar': ['makassar', 'sulawesi selatan']
        }
        
        for city, keywords in location_keywords.items():
            if any(keyword in content_text for keyword in keywords):
                location = city
                break
    
    return age_group, gender, location


async def main():
    """Main execution flow - simplified version"""
    print("\n" + "=" * 80)
    print("🚀 SIMPLE MANUAL DATA STORE PROCESS FOR HYUNDAI")
    print("   (Without AI Analysis - Using Rule-Based Analysis)")
    print("=" * 80)
    
    try:
        # 1. Initialize database
        print("\n[1/6] Initializing database...")
        await connect_to_mongodb()
        print("✅ Database connected")
        
        # 2. Load data
        print("\n[2/6] Loading Instagram data...")
        data_path = Path(__file__).parent / "data" / "scraped_data" / "dataset_instagram-scraper_hyundai.json"
        
        with open(data_path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
        
        print(f"✅ Loaded {len(raw_data)} Instagram posts")
        
        # 3. Get or create brand
        print("\n[3/6] Getting/creating Hyundai brand...")
        brand = await db_service.get_brand("Hyundai")
        
        if not brand:
            brand = Brand(
                name="Hyundai",
                description="Hyundai Motor Company - Global automotive manufacturer",
                keywords=["hyundai", "ionic", "ioniq", "santa fe", "tucson"],
                platforms=[PlatformType.INSTAGRAM],
                created_at=datetime.now()
            )
            await brand.insert()
            print(f"✅ Created brand: {brand.name} (ID: {brand.id})")
        else:
            print(f"✅ Found brand: {brand.name} (ID: {brand.id})")
        
        # 4. Create analysis record
        print("\n[4/6] Creating analysis record...")
        analysis_name = f"Brand Analysis - {brand.name} - Manual Import - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        analysis_id = await db_service.create_brand_analysis(
            brand_id=str(brand.id),
            analysis_name=analysis_name,
            analysis_type="manual_import",
            keywords=brand.keywords or [],
            platforms=["instagram"],
            date_range={}
        )
        
        await db_service.update_brand_analysis_status(analysis_id, "running")
        print(f"✅ Created analysis: {analysis_id}")
        
        # 5. Process and store posts
        print("\n[5/6] Processing and storing posts...")
        stored_count = 0
        
        for idx, item in enumerate(raw_data):
            try:
                caption = item.get('caption', '')
                hashtags = item.get('hashtags', [])
                
                # Simple analysis
                from app.models.database import SentimentType
                sentiment_str, sentiment_score = simple_sentiment_analysis(caption, hashtags)
                topic = simple_topic_extraction(hashtags, caption)
                emotion = simple_emotion_detection(sentiment_str)
                
                # Convert sentiment string to enum
                sentiment_enum = None
                if sentiment_str == "Positive":
                    sentiment_enum = SentimentType.POSITIVE
                elif sentiment_str == "Negative":
                    sentiment_enum = SentimentType.NEGATIVE
                else:
                    sentiment_enum = SentimentType.NEUTRAL
                
                # Analyze demographics from real data
                age_group, gender, location = analyze_demographics_from_data(item)
                
                # Parse timestamp
                timestamp = None
                if item.get('timestamp'):
                    try:
                        timestamp = pd.to_datetime(item['timestamp'])
                    except:
                        timestamp = datetime.now()
                else:
                    # If no timestamp, use current time
                    timestamp = datetime.now()
                
                post = Post(
                    brand=brand,
                    platform=PlatformType.INSTAGRAM,
                    platform_post_id=str(item.get('id', f"instagram_{idx}")),
                    text=caption,
                    author_name=item.get('ownerFullName', 'unknown'),
                    author_username=item.get('ownerUsername', 'unknown'),
                    like_count=int(item.get('likesCount', 0)),
                    comment_count=int(item.get('commentsCount', 0)),
                    share_count=0,
                    view_count=0,
                    post_url=item.get('url', ''),
                    posted_at=timestamp,
                    created_at=datetime.now(),
                    
                # Simple analysis results
                sentiment=sentiment_enum,
                topic=topic,
                emotion=emotion,
                # Analyze demographics from real data instead of random choice
                author_age_group=age_group,
                author_gender=gender,
                author_location_hint=location
                )
                
                # Check if exists
                existing = await Post.find_one(Post.platform_post_id == post.platform_post_id)
                if not existing:
                    await post.insert()
                    stored_count += 1
                    
                    if stored_count % 100 == 0:
                        print(f"   ✓ Stored {stored_count} posts...")
                
            except Exception as e:
                print(f"   ⚠️  Error at post {idx}: {str(e)}")
                continue
        
        print(f"\n✅ Stored {stored_count} posts")
        
        # 6. Save analysis results
        print("\n[6/6] Saving analysis results to collections...")
        
        # Import save function
        from app.api.results_routes import save_brand_analysis_results
        await save_brand_analysis_results(analysis_id, str(brand.id))
        
        # Complete analysis
        await db_service.update_brand_analysis_status(analysis_id, "completed")
        
        print("\n✅ Analysis results saved to all collections")
        
        # Verify
        print("\n" + "=" * 80)
        print("🔍 VERIFICATION")
        print("=" * 80)
        
        posts = await db_service.get_posts_by_brand(brand, limit=10000)
        metrics = await db_service.get_brand_metrics(analysis_id)
        
        print(f"✅ Posts: {len(posts)}")
        if metrics:
            print(f"✅ Metrics: Found")
            print(f"   - Total posts: {metrics.total_posts}")
            print(f"   - Total engagement: {metrics.total_engagement}")
            print(f"   - Sentiment: {metrics.sentiment_distribution}")
        
        print("\n" + "=" * 80)
        print("🎉 SUCCESS! DATA STORED AND READY!")
        print("=" * 80)
        print(f"\n📊 Analysis ID: {analysis_id}")
        print(f"🏢 Brand: {brand.name}")
        print(f"📈 Posts: {stored_count}")
        print(f"\n✅ You can now view the data in Brand Analysis dashboard!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

