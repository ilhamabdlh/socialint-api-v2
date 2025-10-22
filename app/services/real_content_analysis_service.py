from typing import Dict, List, Any, Optional
from datetime import datetime
import pandas as pd

from app.models.database import ContentAnalysis, PlatformType
from app.services.ai_service import AIAnalysisService


class RealContentAnalysisService:
    """
    Real Content Analysis Service yang menggunakan scraping yang sesungguhnya
    dengan fallback ke mock data jika Apify limit habis
    """
    
    def __init__(self):
        self.ai_service = AIAnalysisService()
        
    async def trigger_content_analysis(self, content_id: str) -> Dict[str, Any]:
        """
        Trigger comprehensive content analysis following the flowchart:
        1. Scrape post data and comments from platform
        2. Clean and validate data
        3. Perform NLP analysis (Topic, Sentiment, Emotion)
        4. Store results
        """
        try:
            # Get content from database
            content = await ContentAnalysis.get(content_id)
            if not content:
                return {"success": False, "message": "Content not found"}
            
            # Update status to running
            content.analysis_status = "running"
            await content.save()
            
            # Step 1: Try to scrape data from platform
            scraped_data = await self._scrape_content_from_platform(content)
            
            if not scraped_data["success"]:
                content.analysis_status = "failed"
                await content.save()
                return {"success": False, "message": f"Failed to scrape data: {scraped_data['message']}"}
            
            # Step 2: Process scraped data
            processed_data = await self._process_scraped_data(scraped_data["data"], content)
            
            # Step 3: Perform comprehensive analysis
            analysis_results = await self._perform_comprehensive_analysis(processed_data["data"], content)
            
            # Step 4: Update Content with Results
            await self._update_content_with_analysis_results(content, analysis_results)
            
            return {
                "success": True,
                "message": "Content analysis completed successfully",
                "data": {
                    "content_id": content_id,
                    "analysis_results": analysis_results,
                    "scraped_data": scraped_data["data"],
                    "is_real_scraping": not scraped_data["data"].get("is_mock_data", False)
                }
            }
            
        except Exception as e:
            # Update status to failed
            if 'content' in locals():
                content.analysis_status = "failed"
                await content.save()
            return {"success": False, "message": f"Analysis failed: {str(e)}"}
    
    async def _scrape_content_from_platform(self, content: ContentAnalysis) -> Dict[str, Any]:
        """
        Scrape content from platform using the same scraper service as brand/campaign analysis
        """
        try:
            from app.services.scraper_service import ScraperService
            
            scraper = ScraperService()
            
            # Extract keywords from content tags and title
            keywords = content.tags if content.tags else [content.title.lower()]
            
            # Scrape based on platform
            if content.platform == PlatformType.INSTAGRAM:
                df = scraper.scrape_instagram(
                    keywords=keywords,
                    max_posts=50,
                    brand_name=content.author
                )
            elif content.platform == PlatformType.TIKTOK:
                df = scraper.scrape_tiktok(
                    keywords=keywords,
                    max_posts=50,
                    brand_name=content.author
                )
            elif content.platform == PlatformType.TWITTER:
                df = scraper.scrape_twitter(
                    keywords=keywords,
                    max_posts=50,
                    brand_name=content.author
                )
            elif content.platform == PlatformType.YOUTUBE:
                df = scraper.scrape_youtube(
                    keywords=keywords,
                    max_posts=50,
                    brand_name=content.author
                )
            else:
                return {"success": False, "message": f"Unsupported platform: {content.platform}"}
            
            if df.empty:
                return {"success": False, "message": "No data scraped from platform"}
            
            return {
                "success": True,
                "data": {
                    "platform": content.platform.value,
                    "scraped_df": df,
                    "total_posts": len(df),
                    "keywords": keywords,
                    "is_mock_data": False
                }
            }
            
        except Exception as e:
            error_msg = str(e)
            if "Monthly usage hard limit exceeded" in error_msg:
                # Fallback to mock data if Apify limit exceeded
                print(f"⚠️  Apify limit exceeded, using mock data for testing")
                return await self._get_mock_scraped_data(content)
            return {"success": False, "message": f"Scraping error: {str(e)}"}
    
    async def _get_mock_scraped_data(self, content: ContentAnalysis) -> Dict[str, Any]:
        """
        Generate mock scraped data for testing when Apify limit is exceeded
        """
        try:
            # Create mock DataFrame with realistic data structure
            mock_data = []
            for i in range(15):
                mock_data.append({
                    "text": f"Mock post {i+1} about {content.title} - this is a realistic post content with engagement",
                    "author": f"user_{i+1}",
                    "likes": 100 + i * 15,
                    "comments": 5 + i * 2,
                    "shares": 2 + i,
                    "post_date": content.publish_date,
                    "url": f"https://{content.platform.value}.com/post/{i+1}",
                    "hashtags": content.tags or [content.title.lower()],
                    "mentions": [],
                    "platform": content.platform.value,
                    "views": 1000 + i * 100 if content.platform == PlatformType.TIKTOK or content.platform == PlatformType.YOUTUBE else None
                })
            
            df = pd.DataFrame(mock_data)
            
            return {
                "success": True,
                "data": {
                    "platform": content.platform.value,
                    "scraped_df": df,
                    "total_posts": len(df),
                    "keywords": content.tags or [content.title.lower()],
                    "is_mock_data": True
                }
            }
            
        except Exception as e:
            return {"success": False, "message": f"Mock data generation error: {str(e)}"}
    
    async def _process_scraped_data(self, scraped_data: Dict[str, Any], content: ContentAnalysis) -> Dict[str, Any]:
        """
        Process scraped data using the same pipeline as brand analysis
        """
        try:
            df = scraped_data["scraped_df"]
            platform = scraped_data["platform"]
            
            # Apply basic data processing
            if not df.empty:
                # Remove duplicates
                df = df.drop_duplicates(subset=['text'], keep='first')
                
                # Clean text data
                df['text'] = df['text'].fillna('').astype(str)
                df = df[df['text'].str.len() > 10]  # Filter out very short posts
            
            return {
                "success": True,
                "data": {
                    "processed_df": df,
                    "platform": platform,
                    "total_processed_posts": len(df),
                    "is_mock_data": scraped_data.get("is_mock_data", False)
                }
            }
            
        except Exception as e:
            return {"success": False, "message": f"Data processing error: {str(e)}"}
    
    async def _perform_comprehensive_analysis(self, processed_data: Dict[str, Any], content: ContentAnalysis) -> Dict[str, Any]:
        """
        Perform comprehensive analysis using AI service
        """
        try:
            df = processed_data["processed_df"]
            platform = processed_data["platform"]
            is_mock_data = processed_data.get("is_mock_data", False)
            
            if df.empty:
                return {"success": False, "message": "No data to analyze"}
            
            # Combine all text for analysis
            all_texts = df['text'].tolist()
            combined_text = " ".join(all_texts)
            
            # Perform AI analysis
            topics_result = await self.ai_service.analyze_topics(combined_text)
            sentiment_result = await self.ai_service.analyze_sentiment(combined_text)
            emotions_result = await self.ai_service.analyze_emotions(combined_text)
            
            # Calculate engagement metrics
            total_likes = int(df['likes'].sum()) if 'likes' in df.columns else 0
            total_comments = int(df['comments'].sum()) if 'comments' in df.columns else 0
            total_shares = int(df['shares'].sum()) if 'shares' in df.columns else 0
            total_posts = len(df)
            
            engagement_rate = (total_likes + total_comments + total_shares) / total_posts if total_posts > 0 else 0
            
            # Extract analysis results
            analysis_results = {
                "platform": platform,
                "total_posts": total_posts,
                "is_mock_data": is_mock_data,
                "topics": topics_result.get("data", {}).get("topics", []) if topics_result.get("success") else [],
                "sentiment": sentiment_result.get("data", {}) if sentiment_result.get("success") else {},
                "emotions": emotions_result.get("data", {}) if emotions_result.get("success") else {},
                "engagement": {
                    "total_likes": total_likes,
                    "total_comments": total_comments,
                    "total_shares": total_shares,
                    "engagement_rate": engagement_rate,
                    "reach": total_posts * 1000,  # Estimate
                    "virality": min(engagement_rate * 10, 1.0)
                }
            }
            
            return {
                "success": True,
                "data": analysis_results
            }
            
        except Exception as e:
            return {"success": False, "message": f"Analysis error: {str(e)}"}
    
    async def _update_content_with_analysis_results(self, content: ContentAnalysis, analysis_results: Dict[str, Any]) -> None:
        """Update content with comprehensive analysis results"""
        try:
            if not analysis_results.get("success"):
                raise Exception(f"Analysis failed: {analysis_results.get('message')}")
            
            results = analysis_results["data"]
            
            # Update performance metrics
            engagement = results.get("engagement", {})
            content.engagement_score = engagement.get("engagement_rate", 0)
            content.reach_estimate = engagement.get("reach", 0)
            content.virality_score = engagement.get("virality", 0)
            content.content_health_score = min(int(engagement.get("engagement_rate", 0) * 100), 100)
            
            # Update analysis results
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
                
                # Find dominant emotion
                if emotion_data:
                    content.dominant_emotion = max(emotion_data.items(), key=lambda x: x[1])[0]
                
                # Create emotion distribution
                content.emotion_distribution = [
                    {"emotion": emotion, "score": score, "percentage": score * 100}
                    for emotion, score in emotion_data.items()
                ]
            
            # Update analysis status and timestamps
            content.analysis_status = "completed"
            content.analyzed_at = datetime.now()
            content.updated_at = datetime.now()
            
            # Store raw analysis data for debugging
            content.raw_analysis_data = {
                "analysis_results": analysis_results,
                "analyzed_at": datetime.now().isoformat(),
                "total_posts_analyzed": results.get("total_posts", 0),
                "platform": results.get("platform"),
                "is_mock_data": results.get("is_mock_data", False)
            }
            
            await content.save()
            
        except Exception as e:
            raise Exception(f"Failed to update content: {str(e)}")
