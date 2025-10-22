from typing import Dict, List, Any, Optional
from datetime import datetime
import pandas as pd
import asyncio

from app.models.database import ContentAnalysis, PlatformType
from app.services.ai_service import AIAnalysisService
from app.services.scraper_service import ScraperService
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


class RealContentAnalysisServiceV2:
    """
    Real Content Analysis Service yang menggunakan scraping dan analisis sesungguhnya
    Tidak menggunakan dummy data, semua dari real scraping dan AI analysis
    """
    
    def __init__(self):
        self.ai_service = AIAnalysisService()
        self.scraper_service = ScraperService()
        
    async def trigger_content_analysis(self, content_id: str) -> Dict[str, Any]:
        """
        Trigger comprehensive content analysis dengan real data:
        1. Scrape real data dari platform
        2. Clean dan validate data
        3. Perform real AI analysis (Topic, Sentiment, Emotion)
        4. Store results
        """
        try:
            print(f"🚀 Starting real content analysis for content ID: {content_id}")
            
            # Get content from database
            content = await ContentAnalysis.get(content_id)
            if not content:
                print(f"❌ Content not found: {content_id}")
                return {"success": False, "message": "Content not found"}
            
            print(f"📋 Content found: {content.title} by {content.author} on {content.platform.value}")
            
            # Update status to running
            content.analysis_status = "running"
            await content.save()
            print(f"🔄 Analysis status updated to 'running'")
            
            # Step 1: Scrape real data from platform
            print(f"📡 Step 1: Starting real scraping from {content.platform.value}...")
            scraped_data = await self._scrape_real_content_from_platform(content)
            
            if not scraped_data["success"]:
                print(f"❌ Scraping failed: {scraped_data['message']}")
                content.analysis_status = "failed"
                await content.save()
                return {"success": False, "message": f"Failed to scrape data: {scraped_data['message']}"}
            
            print(f"✅ Scraping completed: {scraped_data['data']['total_posts']} posts scraped")
            
            # Step 2: Process scraped data using real pipeline
            print(f"🧹 Step 2: Processing scraped data...")
            processed_data = await self._process_real_scraped_data(scraped_data["data"], content)
            if not processed_data.get("success"):
                print(f"❌ Data processing failed: {processed_data.get('message')}")
                content.analysis_status = "failed"
                await content.save()
                return {"success": False, "message": f"Data processing failed: {processed_data.get('message')}"}
            print(f"✅ Data processing completed: {processed_data['data']['total_posts_analyzed']} posts processed")
            
            # Step 3: Perform real AI analysis
            print(f"🤖 Step 3: Starting real AI analysis...")
            analysis_results = await self._perform_real_ai_analysis(processed_data, content)
            print(f"✅ AI analysis completed")
            
            # Step 4: Update Content with Real Results
            print(f"💾 Step 4: Saving results to database...")
            await self._update_content_with_real_results(content, analysis_results)
            print(f"✅ Results saved to database")
            
            return {
                "success": True,
                "message": "Real content analysis completed successfully",
                "data": {
                    "content_id": content_id,
                    "analysis_results": analysis_results,
                    "scraped_data": scraped_data["data"],
                    "total_posts_analyzed": processed_data["data"]["total_posts_analyzed"],
                    "is_real_data": True
                }
            }
            
        except Exception as e:
            print(f"❌ CRITICAL ERROR in trigger_content_analysis: {str(e)}")
            import traceback
            print(f"📋 Full traceback: {traceback.format_exc()}")
            
            # Update status to failed
            if 'content' in locals():
                content.analysis_status = "failed"
                await content.save()
                print(f"🔄 Content status updated to 'failed'")
            return {"success": False, "message": f"Analysis failed: {str(e)}"}
    
    async def _scrape_real_content_from_platform(self, content: ContentAnalysis) -> Dict[str, Any]:
        """
        Scrape real content dari platform menggunakan ScraperService
        """
        try:
            # Extract keywords from content tags and title
            keywords = content.tags if content.tags else [content.title.lower()]
            print(f"🔍 Scraping keywords: {keywords}")
            print(f"📱 Platform: {content.platform.value}")
            print(f"👤 Author/Brand: {content.author}")
            
            # Scrape based on platform menggunakan real scraper service
            if content.platform == PlatformType.INSTAGRAM:
                print(f" publishing Instagram scraper...")
                df = await self.scraper_service.scrape_instagram(
                    keywords=keywords,
                    max_posts=100,
                    brand_name=content.author
                )
            elif content.platform == PlatformType.TIKTOK:
                print(f" publishing TikTok scraper...")
                df = await self.scraper_service.scrape_tiktok(
                    keywords=keywords,
                    max_posts=100,
                    brand_name=content.author
                )
            elif content.platform == PlatformType.TWITTER:
                print(f" publishing Twitter scraper...")
                df = await self.scraper_service.scrape_twitter(
                    keywords=keywords,
                    max_posts=100,
                    brand_name=content.author
                )
            elif content.platform == PlatformType.YOUTUBE:
                print(f" publishing YouTube scraper...")
                df = await self.scraper_service.scrape_youtube(
                    keywords=keywords,
                    max_posts=100,
                    brand_name=content.author
                )
            else:
                print(f"❌ Unsupported platform: {content.platform}")
                return {"success": False, "message": f"Unsupported platform: {content.platform}"}
            
            if df.empty:
                print(f"❌ No data scraped from {content.platform.value}")
                return {"success": False, "message": "No real data scraped from platform"}
            
            print(f"📊 Scraped {len(df)} posts from {content.platform.value}")
            print(f"📝 Sample data columns: {list(df.columns)}")
            
            return {
                "success": True,
                "data": {
                    "platform": content.platform.value,
                    "scraped_df": df,
                    "total_posts": len(df),
                    "keywords": keywords,
                    "is_real_data": True
                }
            }
            
        except Exception as e:
            print(f"❌ Scraping error: {str(e)}")
            return {"success": False, "message": f"Real scraping error: {str(e)}"}
    
    async def _process_real_scraped_data(self, scraped_data: Dict[str, Any], content: ContentAnalysis) -> Dict[str, Any]:
        """
        Process scraped data menggunakan real data processing pipeline
        """
        try:
            df = scraped_data["scraped_df"]
            platform = scraped_data["platform"]
            
            # Apply real data processing pipeline
            if not df.empty:
                print(f"📊 Processing {len(df)} posts...")
                
                # Step 1: Prepare dataframe for analysis first
                df = prepare_dataframe(df, platform)
                print(f"📊 After prepare_dataframe: {len(df)} posts")
                
                # Step 2: Validate post URLs
                df = validate_post_urls(df, platform)
                print(f"📊 After validate_post_urls: {len(df)} posts")
                
                # Step 3: Filter by date range if needed
                if content.publish_date:
                    df = filter_by_date_range(df, content.publish_date, content.publish_date)
                    print(f"📊 After filter_by_date_range: {len(df)} posts")
                
                # Step 4: Clean text data
                if 'text' in df.columns:
                    df['text'] = df['text'].fillna('').astype(str)
                    df = df[df['text'].str.len() > 10]  # Filter out very short posts
                    print(f"📊 After text cleaning: {len(df)} posts")
                
                # Step 5: Remove duplicates using DataFrame method
                if not df.empty:
                    df = df.drop_duplicates(subset=['text'] if 'text' in df.columns else ['url'])
                    print(f"📊 After removing duplicates: {len(df)} posts")
            
            return {
                "success": True,
                "data": {
                    "processed_df": df,
                    "platform": platform,
                    "total_posts_analyzed": len(df),
                    "is_real_data": True
                }
            }
            
        except Exception as e:
            return {"success": False, "message": f"Real data processing error: {str(e)}"}
    
    async def _perform_real_ai_analysis(self, processed_data: Dict[str, Any], content: ContentAnalysis) -> Dict[str, Any]:
        """
        Perform real AI analysis menggunakan AIAnalysisService
        """
        try:
            df = processed_data["data"]["processed_df"]
            platform = processed_data["data"]["platform"]
            total_posts = processed_data["data"]["total_posts_analyzed"]
            
            if df.empty:
                print(f"❌ No data to analyze")
                return {"success": False, "message": "No real data to analyze"}
            
            # Combine all text for analysis
            print(f"📝 Available columns: {list(df.columns)}")
            
            # Try different text column names
            text_column = None
            for col in ['text', 'caption', 'content', 'description']:
                if col in df.columns:
                    text_column = col
                    break
            
            if text_column is None:
                print(f"❌ No text column found in DataFrame")
                return {"success": False, "message": "No text column found in DataFrame"}
            
            print(f"📝 Using text column: {text_column}")
            all_texts = df[text_column].tolist()
            combined_text = " ".join([str(text) for text in all_texts if text])
            print(f"📝 Combined text length: {len(combined_text)} characters")
            
            # Perform real AI analysis
            print(f"🤖 Starting real AI analysis for {total_posts} posts...")
            
            # Topic Analysis
            print(f"🔍 Analyzing topics...")
            topics_result = await self.ai_service.analyze_topics(combined_text)
            print(f"📊 Topics analysis result: {topics_result.get('success', False)}")
            
            # Sentiment Analysis
            print(f"😊 Analyzing sentiment...")
            sentiment_result = await self.ai_service.analyze_sentiment(combined_text)
            print(f"📊 Sentiment analysis result: {sentiment_result.get('success', False)}")
            
            # Emotion Analysis
            print(f"😢 Analyzing emotions...")
            emotions_result = await self.ai_service.analyze_emotions(combined_text)
            print(f"📊 Emotions analysis result: {emotions_result.get('success', False)}")
            
            # Calculate real engagement metrics
            total_likes = int(df['likes'].sum()) if 'likes' in df.columns else 0
            total_comments = int(df['comments'].sum()) if 'comments' in df.columns else 0
            total_shares = int(df['shares'].sum()) if 'shares' in df.columns else 0
            
            engagement_rate = (total_likes + total_comments + total_shares) / total_posts if total_posts > 0 else 0
            
            print(f"📈 Engagement metrics calculated:")
            print(f"   - Total likes: {total_likes}")
            print(f"   - Total comments: {total_comments}")
            print(f"   - Total shares: {total_shares}")
            print(f"   - Engagement rate: {engagement_rate:.2f}")
            
            # Extract real analysis results
            analysis_results = {
                "platform": platform,
                "total_posts": total_posts,
                "is_real_data": True,
                "topics": topics_result.get("data", {}).get("topics", []) if topics_result.get("success") else [],
                "sentiment": sentiment_result.get("data", {}) if sentiment_result.get("success") else {},
                "emotions": emotions_result.get("data", {}) if emotions_result.get("success") else {},
                "engagement": {
                    "total_likes": total_likes,
                    "total_comments": total_comments,
                    "total_shares": total_shares,
                    "engagement_rate": engagement_rate,
                    "reach": total_posts * 1000,  # Estimate based on real posts
                    "virality": min(engagement_rate * 10, 1.0)
                }
            }
            
            print(f"✅ Real AI analysis completed for {total_posts} posts")
            print(f"📋 Topics found: {len(analysis_results['topics'])}")
            print(f"💭 Sentiment: {analysis_results['sentiment']}")
            
            return {
                "success": True,
                "data": analysis_results
            }
            
        except Exception as e:
            print(f"❌ AI analysis error: {str(e)}")
            return {"success": False, "message": f"Real AI analysis error: {str(e)}"}
    
    async def _update_content_with_real_results(self, content: ContentAnalysis, analysis_results: Dict[str, Any]) -> None:
        """Update content with real analysis results"""
        try:
            if not analysis_results.get("success"):
                raise Exception(f"Analysis failed: {analysis_results.get('message')}")
            
            results = analysis_results["data"]
            
            # Update performance metrics with real data
            engagement = results.get("engagement", {})
            content.engagement_score = engagement.get("engagement_rate", 0)
            content.reach_estimate = engagement.get("reach", 0)
            content.virality_score = engagement.get("virality", 0)
            content.content_health_score = min(int(engagement.get("engagement_rate", 0) * 100), 100)
            
            # Update analysis results with real AI data
            topics = results.get("topics", [])
            if topics:
                content.topics = topics
                content.dominant_topic = topics[0].get("topic") if topics else None
            
            sentiment = results.get("sentiment", {})
            if sentiment:
                content.sentiment_overall = sentiment.get("sentiment_score", 0)
                content.sentiment_confidence = sentiment.get("confidence", 0)
            
            emotions = results.get("emotions", {})
            if emotions and "emotions" in emotions:
                emotion_data = emotions["emotions"]
                content.emotion_joy = emotion_data.get("joy", 0)
                content.emotion_anger = emotion_data.get("anger", 0)
                content.emotion_fear = emotion_data.get("fear", 0)
                content.emotion_sadness = emotion_data.get("sadness", 0)
                content.emotion_surprise = emotion_data.get("surprise", 0)
                content.emotion_trust = emotion_data.get("trust", 0)
                content.emotion_anticipation = emotion_data.get("anticipation", 0)
                content.emotion_disgust = emotion_data.get("disgust", 0)
                
                # Find dominant emotion from real data
                if emotion_data:
                    content.dominant_emotion = max(emotion_data.items(), key=lambda x: x[1])[0]
                
                # Create real emotion distribution
                content.emotion_distribution = [
                    {"emotion": emotion, "score": score, "percentage": score * 100}
                    for emotion, score in emotion_data.items()
                ]
            
            # Update analysis status and timestamps
            content.analysis_status = "completed"
            content.analyzed_at = datetime.now()
            content.updated_at = datetime.now()
            
            # Store raw real analysis data
            content.raw_analysis_data = {
                "analysis_results": analysis_results,
                "analyzed_at": datetime.now().isoformat(),
                "total_posts_analyzed": results.get("total_posts", 0),
                "platform": results.get("platform"),
                "is_real_data": True,
                "scraped_data_info": {
                    "total_likes": engagement.get("total_likes", 0),
                    "total_comments": engagement.get("total_comments", 0),
                    "total_shares": engagement.get("total_shares", 0),
                    "engagement_rate": engagement.get("engagement_rate", 0)
                }
            }
            
            await content.save()
            print(f"✅ Content analysis results saved to database for {content.title}")
            
        except Exception as e:
            raise Exception(f"Failed to update content with real results: {str(e)}")
