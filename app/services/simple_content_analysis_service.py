from typing import Dict, Any
from datetime import datetime
from app.models.database import ContentAnalysis


class SimpleContentAnalysisService:
    """
    Simple Content Analysis Service for testing
    Directly updates content with mock analysis results
    """
    
    async def trigger_content_analysis(self, content_id: str) -> Dict[str, Any]:
        """
        Simple content analysis that directly updates content with mock data
        """
        try:
            # Get content from database
            content = await ContentAnalysis.get(content_id)
            if not content:
                return {"success": False, "message": "Content not found"}
            
            # Update status to running
            content.analysis_status = "running"
            await content.save()
            
            # Mock analysis results
            mock_analysis_results = {
                "topics": [
                    {"topic": "automotive", "relevance": 0.9, "confidence": 0.8},
                    {"topic": "hyundai", "relevance": 0.8, "confidence": 0.9},
                    {"topic": "creta", "relevance": 0.7, "confidence": 0.8}
                ],
                "sentiment": {
                    "overall_sentiment": 0.6,
                    "sentiment_confidence": 0.8
                },
                "emotions": {
                    "emotions": {
                        "joy": 0.4,
                        "anger": 0.1,
                        "fear": 0.0,
                        "sadness": 0.1,
                        "surprise": 0.2,
                        "trust": 0.5,
                        "anticipation": 0.3,
                        "disgust": 0.0
                    },
                    "dominant_emotion": "trust"
                }
            }
            
            # Update content with mock results
            await self._update_content_with_mock_results(content, mock_analysis_results)
            
            return {
                "success": True,
                "message": "Content analysis completed successfully",
                "data": {
                    "content_id": content_id,
                    "analysis_results": mock_analysis_results
                }
            }
            
        except Exception as e:
            # Update status to failed
            if 'content' in locals():
                content.analysis_status = "failed"
                await content.save()
            return {"success": False, "message": f"Analysis failed: {str(e)}"}
    
    async def _update_content_with_mock_results(self, content: ContentAnalysis, analysis_results: Dict[str, Any]) -> None:
        """Update content with mock analysis results"""
        try:
            # Update basic content info
            if not content.title:
                content.title = "Hyundai Creta Analysis"
            if not content.description:
                content.description = "Comprehensive analysis of Hyundai Creta content"
            
            # Update performance metrics (mock data)
            content.engagement_score = 0.08
            content.reach_estimate = 15000
            content.virality_score = 0.05
            content.content_health_score = 85
            
            # Update analysis results
            topics_data = analysis_results["topics"]
            content.topics = topics_data
            content.dominant_topic = topics_data[0]["topic"] if topics_data else None
            
            sentiment_data = analysis_results["sentiment"]
            content.sentiment_overall = sentiment_data["overall_sentiment"]
            content.sentiment_confidence = sentiment_data["sentiment_confidence"]
            
            emotions_data = analysis_results["emotions"]
            emotions = emotions_data["emotions"]
            content.emotion_joy = emotions["joy"]
            content.emotion_anger = emotions["anger"]
            content.emotion_fear = emotions["fear"]
            content.emotion_sadness = emotions["sadness"]
            content.emotion_surprise = emotions["surprise"]
            content.emotion_trust = emotions["trust"]
            content.emotion_anticipation = emotions["anticipation"]
            content.emotion_disgust = emotions["disgust"]
            content.dominant_emotion = emotions_data["dominant_emotion"]
            
            # Create emotion distribution
            content.emotion_distribution = [
                {"emotion": emotion, "score": score, "percentage": score * 100}
                for emotion, score in emotions.items()
            ]
            
            # Update analysis status and timestamps
            content.analysis_status = "completed"
            content.analyzed_at = datetime.now()
            content.updated_at = datetime.now()
            
            # Store raw analysis data for debugging
            content.raw_analysis_data = {
                "analysis_results": analysis_results,
                "analyzed_at": datetime.now().isoformat()
            }
            
            await content.save()
            
        except Exception as e:
            raise Exception(f"Failed to update content: {str(e)}")

