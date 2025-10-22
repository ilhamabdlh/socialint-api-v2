"""
Manual Data Store Script for Hyundai Instagram Data
This script processes Instagram scraped data and stores it following the trigger analysis flow
"""

import asyncio
import json
import pandas as pd
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


async def load_and_process_instagram_data():
    """Load Instagram data from JSON file"""
    print("=" * 80)
    print("📥 LOADING INSTAGRAM DATA FOR HYUNDAI")
    print("=" * 80)
    
    data_path = Path(__file__).parent / "data" / "scraped_data" / "dataset_instagram-scraper_hyundai.json"
    
    if not data_path.exists():
        print(f"❌ Error: File not found at {data_path}")
        return None
    
    print(f"✅ Loading data from: {data_path}")
    
    with open(data_path, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
    
    print(f"✅ Loaded {len(raw_data)} Instagram posts")
    
    # Convert to DataFrame for processing
    df = pd.DataFrame(raw_data)
    
    # Clean and normalize data
    print("\n🔧 Cleaning and normalizing data...")
    
    # Convert timestamp to datetime
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Fill NaN values
    df['caption'] = df['caption'].fillna('')
    df['commentsCount'] = df['commentsCount'].fillna(0)
    df['likesCount'] = df['likesCount'].fillna(0)
    df['ownerUsername'] = df['ownerUsername'].fillna('unknown')
    df['ownerFullName'] = df['ownerFullName'].fillna('unknown')
    
    print(f"✅ Data cleaned. Ready to process {len(df)} posts")
    
    return df


async def get_or_create_hyundai_brand():
    """Get or create Hyundai brand in database"""
    print("\n" + "=" * 80)
    print("🏢 GETTING/CREATING HYUNDAI BRAND")
    print("=" * 80)
    
    # Check if brand exists
    brand = await db_service.get_brand("Hyundai")
    
    if not brand:
        print("⚠️  Brand 'Hyundai' not found. Creating new brand...")
        
        brand = Brand(
            name="Hyundai",
            description="Hyundai Motor Company - Global automotive manufacturer",
            keywords=["hyundai", "ionic", "ioniq", "santa fe", "tucson", "elantra"],
            platforms=[PlatformType.INSTAGRAM],
            created_at=datetime.now()
        )
        await brand.insert()
        print(f"✅ Created brand: {brand.name} (ID: {brand.id})")
    else:
        print(f"✅ Found existing brand: {brand.name} (ID: {brand.id})")
    
    return brand


async def create_brand_analysis_record(brand):
    """Create BrandAnalysis record"""
    print("\n" + "=" * 80)
    print("📊 CREATING BRAND ANALYSIS RECORD")
    print("=" * 80)
    
    analysis_name = f"Brand Analysis - {brand.name} - Manual Import - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    
    analysis_id = await db_service.create_brand_analysis(
        brand_id=str(brand.id),
        analysis_name=analysis_name,
        analysis_type="manual_import",
        keywords=brand.keywords or [],
        platforms=["instagram"],
        date_range={}
    )
    
    print(f"✅ Created analysis record: {analysis_id}")
    
    # Update status to running
    await db_service.update_brand_analysis_status(analysis_id, "running")
    print(f"✅ Status updated to 'running'")
    
    return analysis_id


async def process_and_store_posts(df, brand):
    """Process Instagram data and store as Post documents"""
    print("\n" + "=" * 80)
    print("💾 PROCESSING AND STORING POSTS")
    print("=" * 80)
    
    stored_count = 0
    
    for idx, row in df.iterrows():
        try:
            # Create Post document
            post = Post(
                brand=brand,
                platform=PlatformType.INSTAGRAM,
                post_id=str(row.get('id', f"instagram_{idx}")),
                text=row.get('caption', ''),
                author_name=row.get('ownerFullName', 'unknown'),
                author_username=row.get('ownerUsername', 'unknown'),
                like_count=int(row.get('likesCount', 0)),
                comment_count=int(row.get('commentsCount', 0)),
                share_count=0,  # Instagram doesn't provide share count
                view_count=0,
                post_url=row.get('url', ''),
                posted_at=row.get('timestamp'),
                created_at=datetime.now(),
                
                # These will be filled by AI analysis later
                sentiment=None,
                sentiment_score=None,
                topic=None,
                emotion=None,
                author_age_group=None,
                author_gender=None,
                author_location_hint=None
            )
            
            # Check if post already exists
            existing = await Post.find_one(Post.post_id == post.post_id)
            if not existing:
                await post.insert()
                stored_count += 1
                
                if stored_count % 100 == 0:
                    print(f"   ✓ Stored {stored_count} posts...")
            
        except Exception as e:
            print(f"   ⚠️  Error storing post {idx}: {str(e)}")
            continue
    
    print(f"\n✅ Successfully stored {stored_count} new posts to database")
    return stored_count


async def run_ai_analysis_on_posts(brand):
    """Run AI analysis on stored posts to fill sentiment, topic, emotion"""
    print("\n" + "=" * 80)
    print("🤖 RUNNING AI ANALYSIS ON POSTS")
    print("=" * 80)
    
    try:
        from app.services.analysis_service_v2 import AnalysisServiceV2
        analysis_service = AnalysisServiceV2()
        
        # Get all posts for this brand that need analysis
        posts = await db_service.get_posts_by_brand(brand, limit=10000)
        
        posts_needing_analysis = [p for p in posts if p.sentiment is None or p.topic is None]
        
        print(f"📊 Found {len(posts_needing_analysis)} posts needing AI analysis")
        
        if posts_needing_analysis:
            # Convert to DataFrame for analysis
            posts_data = []
            for post in posts_needing_analysis:
                posts_data.append({
                    'text': post.text,
                    'like_count': post.like_count,
                    'comment_count': post.comment_count,
                    'share_count': post.share_count,
                    'author_name': post.author_name,
                    'posted_at': post.posted_at,
                    'post_url': post.post_url,
                    'post_id': post.post_id
                })
            
            df = pd.DataFrame(posts_data)
            
            print(f"🔄 Processing {len(df)} posts through AI analysis...")
            
            # Process through analysis service
            result = await analysis_service.process_platform_dataframe(
                df=df,
                platform="instagram",
                brand_name=brand.name,
                keywords=brand.keywords,
                layer=1,
                save_to_db=True
            )
            
            print(f"✅ AI Analysis completed:")
            print(f"   - Total analyzed: {result.total_analyzed}")
            print(f"   - Positive: {result.positive_count}")
            print(f"   - Negative: {result.negative_count}")
            print(f"   - Neutral: {result.neutral_count}")
        else:
            print("✅ All posts already have AI analysis")
            
    except Exception as e:
        print(f"⚠️  Warning: AI analysis failed: {str(e)}")
        print("   Posts stored but without AI-generated sentiment/topic/emotion")


async def save_brand_analysis_results(analysis_id, brand):
    """Save aggregated brand analysis results to all collections"""
    print("\n" + "=" * 80)
    print("💾 SAVING BRAND ANALYSIS RESULTS TO COLLECTIONS")
    print("=" * 80)
    
    # Import the save function from results_routes
    from app.api.results_routes import save_brand_analysis_results
    
    try:
        await save_brand_analysis_results(analysis_id, str(brand.id))
        print("✅ Successfully saved results to all 8 collections:")
        print("   1. ✅ BrandMetrics")
        print("   2. ✅ BrandSentimentTimeline")
        print("   3. ✅ BrandTrendingTopics")
        print("   4. ✅ BrandDemographics")
        print("   5. ✅ BrandEngagementPatterns")
        print("   6. ✅ BrandPerformance")
        print("   7. ✅ BrandEmotions")
        print("   8. ✅ BrandCompetitive")
    except Exception as e:
        print(f"❌ Error saving analysis results: {str(e)}")
        raise


async def complete_analysis(analysis_id):
    """Mark analysis as completed"""
    print("\n" + "=" * 80)
    print("✅ COMPLETING ANALYSIS")
    print("=" * 80)
    
    await db_service.update_brand_analysis_status(analysis_id, "completed")
    print("✅ Analysis status updated to 'completed'")


async def verify_stored_data(brand, analysis_id):
    """Verify that data is stored correctly"""
    print("\n" + "=" * 80)
    print("🔍 VERIFYING STORED DATA")
    print("=" * 80)
    
    # Check posts
    posts = await db_service.get_posts_by_brand(brand, limit=10000)
    print(f"✅ Posts stored: {len(posts)}")
    
    # Check brand analysis
    analysis = await BrandAnalysis.find_one(BrandAnalysis.id == analysis_id)
    if analysis:
        print(f"✅ BrandAnalysis record: Found (Status: {analysis.status})")
    
    # Check metrics
    metrics = await db_service.get_brand_metrics(analysis_id)
    if metrics:
        print(f"✅ BrandMetrics: Found")
        print(f"   - Total posts: {metrics.total_posts}")
        print(f"   - Total engagement: {metrics.total_engagement}")
        print(f"   - Sentiment: {metrics.sentiment_distribution}")
    
    # Check sentiment timeline
    timeline = await db_service.get_brand_sentiment_timeline(analysis_id)
    if timeline:
        print(f"✅ BrandSentimentTimeline: {len(timeline)} records")
    
    # Check trending topics
    topics = await db_service.get_brand_trending_topics(analysis_id)
    if topics:
        print(f"✅ BrandTrendingTopics: {len(topics)} topics")
    
    # Check demographics
    demographics = await db_service.get_brand_demographics(analysis_id)
    if demographics:
        print(f"✅ BrandDemographics: Found")
    
    print("\n" + "=" * 80)
    print("✅ DATA VERIFICATION COMPLETE")
    print("=" * 80)


async def main():
    """Main execution flow"""
    print("\n" + "=" * 80)
    print("🚀 MANUAL DATA STORE PROCESS FOR HYUNDAI")
    print("   Following Trigger Analysis Flow")
    print("=" * 80)
    
    try:
        # 1. Initialize database connection
        print("\n[1/8] Initializing database connection...")
        await connect_to_mongodb()
        print("✅ Database connected")
        
        # 2. Load Instagram data
        print("\n[2/8] Loading Instagram data...")
        df = await load_and_process_instagram_data()
        if df is None:
            return
        
        # 3. Get or create Hyundai brand
        print("\n[3/8] Getting/creating Hyundai brand...")
        brand = await get_or_create_hyundai_brand()
        
        # 4. Create brand analysis record
        print("\n[4/8] Creating brand analysis record...")
        analysis_id = await create_brand_analysis_record(brand)
        
        # 5. Store posts to database
        print("\n[5/8] Storing posts to database...")
        stored_count = await process_and_store_posts(df, brand)
        
        # 6. Run AI analysis on posts
        print("\n[6/8] Running AI analysis on posts...")
        await run_ai_analysis_on_posts(brand)
        
        # 7. Save aggregated analysis results
        print("\n[7/8] Saving aggregated analysis results...")
        await save_brand_analysis_results(analysis_id, brand)
        
        # 8. Complete analysis
        print("\n[8/8] Completing analysis...")
        await complete_analysis(analysis_id)
        
        # Verify stored data
        await verify_stored_data(brand, analysis_id)
        
        print("\n" + "=" * 80)
        print("🎉 SUCCESS! MANUAL DATA STORE COMPLETED")
        print("=" * 80)
        print(f"\n📊 Analysis ID: {analysis_id}")
        print(f"🏢 Brand: {brand.name} (ID: {brand.id})")
        print(f"📈 Posts stored: {stored_count}")
        print(f"\n✅ Data is now ready to be viewed in Brand Analysis dashboard!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Try to mark analysis as failed
        try:
            if 'analysis_id' in locals():
                await db_service.update_brand_analysis_status(analysis_id, "failed")
                print(f"⚠️  Analysis marked as failed: {analysis_id}")
        except:
            pass


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("Manual Data Store Script - Hyundai Instagram Data")
    print("=" * 80)
    
    asyncio.run(main())

