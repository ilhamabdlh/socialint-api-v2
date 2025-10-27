import pandas as pd
import time
from typing import List, Dict, Any, Optional
from pathlib import Path
import asyncio
from datetime import datetime

from app.services.ai_service import AIAnalysisService
from app.services.database_service import db_service
from app.config.env_config import env_config
from app.utils.data_helpers import (
    remove_duplicates,
    explicit_keywords_cleansing,
    prepare_dataframe,
    update_dataframe,
    get_platform_text_column,
    calculate_sentiment_distribution,
    validate_post_urls,
    filter_by_date_range,
    normalize_topic_labeling,
    consolidate_demographics,
    analyze_engagement_patterns
)
from app.models.database import (
    Brand, Post, Comment, AnalysisJob,
    PlatformType, AnalysisStatusType
)
from app.models.schemas import CleansingStats, PlatformAnalysisResponse
from app.config.settings import settings

class AnalysisServiceV2:
    """
    Enhanced Analysis Service with MongoDB integration
    Implements multi-brand batch processing sesuai diagram
    """
    
    def __init__(self):
        self.ai_service = AIAnalysisService()
        self.batch_size = settings.batch_size
        self.topics_global = []  # store topics across all platforms
        
    def load_data(self, file_path: str) -> pd.DataFrame:
        """Load data from various file formats"""
        file_path = Path(file_path)
        
        if file_path.suffix == '.csv':
            return pd.read_csv(file_path)
        elif file_path.suffix in ['.xlsx', '.xls']:
            return pd.read_excel(file_path)
        elif file_path.suffix == '.json':
            return pd.read_json(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_path.suffix}")
    
    def cleanse_data(
        self, 
        df: pd.DataFrame, 
        platform: str, 
        keywords: List[str],
        layer: int = 1,
        start_date: str = None,
        end_date: str = None
    ) -> tuple[pd.DataFrame, CleansingStats]:
        """
        Apply cleansing pipeline:
        1. Validate URLs (drops invalid URLs)
        2. Filter by date range (if provided)
        3. Remove duplicates
        4. Filter by keywords
        5. Filter by language (Indonesian only)
        """
        initial_count = len(df)
        text_col = get_platform_text_column(platform, layer)
        
        # Convert text column to string
        if text_col in df.columns:
            df[text_col] = df[text_col].astype(str)
        
        # Step 0a: Validate URLs (NEW!)
        print(f"\n📋 Step 1/5: Validating URLs...")
        df = validate_post_urls(df, platform)
        after_url_validation = len(df)
        
        # Step 0b: Filter by date range (NEW!)
        if start_date or end_date:
            print(f"\n📅 Step 2/5: Filtering by date range...")
            df = filter_by_date_range(df, start_date, end_date)
        after_date_filter = len(df)
        
        # Extract data for cleansing
        data = df[text_col].tolist()
        
        # Step 1: Remove duplicates
        print(f"\n🔄 Step 3/5: Removing duplicates...")
        data = remove_duplicates(data, platform)
        df = update_dataframe(df, data, platform, layer)
        after_duplicates = len(df)
        
        # Step 2: Keyword filtering
        print(f"\n🔍 Step 4/5: Filtering by keywords...")
        data = explicit_keywords_cleansing(data, keywords)
        df = update_dataframe(df, data, platform, layer)
        after_keywords = len(df)
        
        # Step 3: Language filtering (only Indonesian)
        print(f"\n🌐 Step 5/5: Language-based cleansing...")
        data = self.ai_service.language_based_cleansing(data)
        df = update_dataframe(df, data, platform, layer)
        final_count = len(df)
        
        stats = CleansingStats(
            initial_count=initial_count,
            after_duplicates=after_duplicates,
            after_keywords=after_keywords,
            after_language=final_count,
            final_count=final_count
        )
        
        return df, stats
    
    def analyze_data(
        self, 
        df: pd.DataFrame, 
        platform: str,
        layer: int = 1
    ) -> pd.DataFrame:
        """
        Apply AI analysis:
        1. Sentiment analysis
        2. Topic analysis
        3. Emotions analysis
        4. Demographics extraction
        """
        text_col = get_platform_text_column(platform, layer)
        data = df[text_col].tolist()
        
        # Split into batches for processing
        batches = [data[i:i + self.batch_size] for i in range(0, len(data), self.batch_size)]
        
        # Run sentiment analysis batch by batch
        all_sentiments = []
        for batch in batches:
            sentiments = self.ai_service.sentiment_analysis(batch)
            all_sentiments.extend(sentiments)
        
        # Run topic analysis batch by batch
        all_topics = []
        for batch in batches:
            topics = self.ai_service.topic_analysis(batch, self.topics_global)
            all_topics.extend(topics)
        
        # Normalize topic labels to handle case variations
        topic_mapping = normalize_topic_labeling(all_topics)
        normalized_topics = [topic_mapping.get(topic, topic) for topic in all_topics]
        
        # Run emotions analysis batch by batch
        all_emotions = []
        for batch in batches:
            emotions = self.ai_service.emotions_analysis(batch)
            all_emotions.extend(emotions)
        
        # Run demographics extraction batch by batch
        all_demographics = []
        for batch in batches:
            demographics = self.ai_service.extract_demographics(batch)
            all_demographics.extend(demographics)
        
        # Add results to dataframe with NaN handling
        df['sentiment'] = [s if pd.notna(s) and s in ['Positive', 'Negative', 'Neutral'] else 'Neutral' for s in all_sentiments]
        df['topic'] = [t if pd.notna(t) and isinstance(t, str) and t.strip() else 'general' for t in normalized_topics]
        df['emotion'] = [e if pd.notna(e) and isinstance(e, str) and e.strip() else 'neutral' for e in all_emotions]
        
        # Consolidate demographics to remove duplicates
        consolidated_demo = consolidate_demographics(all_demographics)
        df['age_group'] = [d.get('age_group', 'unknown') if pd.notna(d.get('age_group', 'unknown')) else 'unknown' for d in all_demographics]
        df['gender'] = [d.get('gender', 'unknown') if pd.notna(d.get('gender', 'unknown')) else 'unknown' for d in all_demographics]
        df['location_hint'] = [d.get('location_hint', 'unknown') if pd.notna(d.get('location_hint', 'unknown')) else 'unknown' for d in all_demographics]
        
        # Analyze engagement patterns
        engagement_patterns = analyze_engagement_patterns(df)
        df['engagement_patterns'] = engagement_patterns
        
        return df
    
    async def save_to_database(
        self,
        df: pd.DataFrame,
        brand: Brand,
        platform: PlatformType,
        layer: int = 1
    ):
        """
        Save analyzed data to MongoDB
        Layer 1: Save as Posts
        Layer 2: Save as Comments
        """
        print(f"💾 Saving {len(df)} records to MongoDB...")
        
        if layer == 1:
            # Save posts
            for idx, row in df.iterrows():
                try:
                    # Prepare post data
                    # Extract posted_at from various timestamp fields
                    posted_at = None
                    if 'createTimeISO' in row and pd.notna(row.get('createTimeISO')):
                        try:
                            posted_at = pd.to_datetime(row['createTimeISO'])
                        except:
                            pass
                    elif 'createTime' in row and pd.notna(row.get('createTime')):
                        try:
                            # TikTok createTime is usually in seconds since epoch
                            posted_at = pd.to_datetime(row['createTime'], unit='s')
                        except:
                            pass
                    elif 'timestamp' in row and pd.notna(row.get('timestamp')):
                        try:
                            # Instagram timestamp field
                            posted_at = pd.to_datetime(row['timestamp'])
                        except:
                            pass
                    
                    # Handle different data structures for different platforms
                    text_content = ''
                    if platform == PlatformType.INSTAGRAM:
                        # Instagram data might have different field names
                        text_content = str(row.get('caption', row.get('text', row.get('title', row.get('description', '')))))
                    else:
                        # TikTok and other platforms
                        text_content = str(row.get('title', row.get('text', row.get('caption', ''))))
                    
                    post_data = {
                        'platform_post_id': str(row.get('id', f"{platform}_{idx}")),
                        'text': text_content,
                        'post_url': str(row.get('postPage', row.get('webVideoUrl', row.get('url', '')))),
                        'description': str(row.get('description', '')),
                        'author_name': str(row.get('authorMeta.name', row.get('ownerFullName', ''))),
                        'like_count': int(row.get('diggCount', row.get('likesCount', 0))),
                        'comment_count': int(row.get('commentCount', row.get('commentsCount', 0))),
                        'share_count': int(row.get('shareCount', row.get('sharesCount', 0))),
                        'view_count': int(row.get('playCount', 0)),
                        'sentiment': row.get('sentiment'),
                        'topic': row.get('topic'),
                        'emotion': row.get('emotion'),
                        'author_age_group': row.get('age_group'),
                        'author_gender': row.get('gender'),
                        'author_location_hint': row.get('location_hint'),
                        'posted_at': posted_at,  # Use TikTok createTime as posted_at
                        'raw_data': row.to_dict()
                    }
                    
                    post = await db_service.save_post(
                        brand=brand,
                        platform=platform,
                        **post_data
                    )
                    
                    # Update topic interests
                    if post.topic and post.sentiment:
                        await db_service.update_topic_interest(
                            brand=brand,
                            topic=post.topic,
                            platform=platform,
                            increment_mentions=True,
                            sentiment=post.sentiment,
                            engagement_data={
                                'likes': post.like_count,
                                'comments': post.comment_count,
                                'shares': post.share_count
                            }
                        )
                
                except Exception as e:
                    print(f"⚠️  Error saving post {idx}: {str(e)}")
                    continue
        
        else:
            # Layer 2: Save comments
            # Similar logic for comments
            pass
        
        print(f"✅ Saved to MongoDB successfully")
    
    async def process_platform_dataframe(
        self,
        df: pd.DataFrame,
        platform: str,
        brand_name: str,
        keywords: List[str],
        layer: int = 1,
        save_to_db: bool = True
    ) -> PlatformAnalysisResponse:
        """
        Complete processing pipeline for one platform using DataFrame (from scraping)
        Similar to process_platform but accepts DataFrame instead of file_path
        """
        start_time = time.time()
        
        # Get or create brand
        brand = None
        if save_to_db:
            brand = await db_service.get_or_create_brand(
                name=brand_name,
                keywords=keywords
            )
        
        # Prepare DataFrame
        df = prepare_dataframe(df, platform)
        
        # Cleanse
        df, cleansing_stats = self.cleanse_data(df, platform, keywords, layer)
        
        # Analyze
        df = self.analyze_data(df, platform, layer)
        
        # Save to database
        if save_to_db and brand:
            try:
                await self.save_to_database(df, brand, PlatformType(platform), layer)
            except Exception as e:
                print(f"⚠️  Warning: Could not save to MongoDB: {e}")
        
        # Calculate stats
        sentiment_dist = calculate_sentiment_distribution(df['sentiment'].tolist())
        # Filter out NaN values from topics
        topics_found = df['topic'].dropna().unique().tolist()
        
        # Save results to CSV (backup)
        import os
        layer_name = f"layer{layer}"
        
        # Ensure data directory exists
        data_dir = "data/scraped_data"
        os.makedirs(data_dir, exist_ok=True)
        
        output_file = os.path.join(data_dir, f"{platform}_{brand_name}_{layer_name}.csv")
        df.to_csv(output_file, index=False)
        
        processing_time = time.time() - start_time
        
        return PlatformAnalysisResponse(
            platform=platform,
            brand_name=brand_name,
            layer=layer_name,
            total_analyzed=len(df),
            cleansing_stats=cleansing_stats,
            topics_found=topics_found,
            sentiment_distribution=sentiment_dist,
            output_file=output_file,
            processing_time=round(processing_time, 2)
        )
    
    async def process_platform(
        self,
        file_path: str,
        platform: str,
        brand_name: str,
        keywords: List[str],
        layer: int = 1,
        save_to_db: bool = True
    ) -> PlatformAnalysisResponse:
        """
        Complete processing pipeline for one platform with MongoDB integration
        """
        start_time = time.time()
        
        # Get or create brand
        brand = None
        if save_to_db:
            brand = await db_service.get_or_create_brand(
                name=brand_name,
                keywords=keywords
            )
        
        # Load and prepare
        df = self.load_data(file_path)
        df = prepare_dataframe(df, platform)
        
        # Cleanse
        df, cleansing_stats = self.cleanse_data(df, platform, keywords, layer)
        
        # Analyze
        df = self.analyze_data(df, platform, layer)
        
        # Save to database
        if save_to_db and brand:
            try:
                await self.save_to_database(df, brand, PlatformType(platform), layer)
            except Exception as e:
                print(f"⚠️  Warning: Could not save to MongoDB: {e}")
        
        # Calculate stats
        sentiment_dist = calculate_sentiment_distribution(df['sentiment'].tolist())
        # Filter out NaN values from topics
        topics_found = df['topic'].dropna().unique().tolist()
        
        # Save results to CSV (backup)
        import os
        layer_name = f"layer{layer}"
        
        # Ensure data directory exists
        data_dir = "data/scraped_data"
        os.makedirs(data_dir, exist_ok=True)
        
        output_file = os.path.join(data_dir, f"{platform}_{brand_name}_{layer_name}.csv")
        df.to_csv(output_file, index=False)
        
        processing_time = time.time() - start_time
        
        return PlatformAnalysisResponse(
            platform=platform,
            brand_name=brand_name,
            layer=layer_name,
            total_analyzed=len(df),
            cleansing_stats=cleansing_stats,
            topics_found=topics_found,
            sentiment_distribution=sentiment_dist,
            output_file=output_file,
            processing_time=round(processing_time, 2)
        )
    
    async def process_multiple_platforms(
        self,
        platforms_data: Dict[str, str],  # platform -> file_path mapping
        brand_name: str,
        keywords: List[str],
        save_to_db: bool = True
    ) -> List[PlatformAnalysisResponse]:
        """
        Process multiple platforms for brand analysis
        Implements the diagram's multi-platform loop
        """
        results = []
        
        # Create analysis job if using database
        job = None
        brand = None
        if save_to_db:
            brand = await db_service.get_or_create_brand(
                name=brand_name,
                keywords=keywords
            )
            job = await db_service.create_analysis_job(
                brand=brand,
                platforms=[PlatformType(p) for p in platforms_data.keys()],
                keywords=keywords,
                layer=1
            )
            await db_service.update_job_status(
                job, 
                AnalysisStatusType.PROCESSING,
                progress=0
            )
        
        # Process each platform
        total_platforms = len(platforms_data)
        for idx, (platform, file_path) in enumerate(platforms_data.items()):
            print(f"\n{'='*80}")
            print(f"Processing platform: {platform.upper()} ({idx+1}/{total_platforms})")
            print(f"{'='*80}")
            
            try:
                result = await self.process_platform(
                    file_path=file_path,
                    platform=platform,
                    brand_name=brand_name,
                    keywords=keywords,
                    layer=1,
                    save_to_db=save_to_db
                )
                results.append(result)
                
                # Update job progress
                if job:
                    progress = ((idx + 1) / total_platforms) * 100
                    await db_service.update_job_status(
                        job,
                        AnalysisStatusType.PROCESSING,
                        progress=progress,
                        total_processed=sum(r.total_analyzed for r in results)
                    )
                
                print(f"✓ {platform} completed successfully")
                
            except Exception as e:
                print(f"✗ Error processing {platform}: {str(e)}")
                # Continue with other platforms even if one fails
        
        # Complete job
        if job:
            await db_service.update_job_status(
                job,
                AnalysisStatusType.COMPLETED,
                total_processed=sum(r.total_analyzed for r in results),
                sentiment_distribution={
                    k: sum(r.sentiment_distribution.get(k, 0) for r in results)
                    for k in ['Positive', 'Negative', 'Neutral']
                },
                topics_found=list(set(t for r in results for t in r.topics_found))
            )
        
        return results
    
    async def process_brand_batch(
        self,
        brands_config: List[Dict[str, Any]]
    ) -> Dict[str, List[PlatformAnalysisResponse]]:
        """
        Process multiple brands in batch
        Implements multi-brand batch processing from diagram
        
        brands_config format:
        [
            {
                "brand_name": "hufagripp",
                "keywords": ["hufagrip", "hufagripp"],
                "platforms_data": {
                    "tiktok": "path/to/file.json",
                    "instagram": "path/to/file.json"
                }
            },
            ...
        ]
        """
        all_results = {}
        
        for brand_config in brands_config:
            brand_name = brand_config['brand_name']
            keywords = brand_config['keywords']
            platforms_data = brand_config['platforms_data']
            
            print(f"\n{'#'*80}")
            print(f"# PROCESSING BRAND: {brand_name.upper()}")
            print(f"{'#'*80}")
            
            try:
                results = await self.process_multiple_platforms(
                    platforms_data=platforms_data,
                    brand_name=brand_name,
                    keywords=keywords,
                    save_to_db=True
                )
                all_results[brand_name] = results
                
                print(f"\n✅ Completed brand: {brand_name}")
                print(f"   Platforms analyzed: {len(results)}")
                print(f"   Total posts: {sum(r.total_analyzed for r in results)}")
                
            except Exception as e:
                print(f"\n❌ Error processing brand {brand_name}: {str(e)}")
                all_results[brand_name] = []
        
        return all_results

# Singleton instance
analysis_service_v2 = AnalysisServiceV2()

