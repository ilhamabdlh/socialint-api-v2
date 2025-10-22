from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
import pytz

from app.models.database import Post, PlatformType, SentimentType, ContentAnalysis
from app.services.content_scraper_service import ContentScraperService

router = APIRouter(prefix="/contents", tags=["Content Management"])

# ============= REQUEST/RESPONSE SCHEMAS =============

class ContentCreate(BaseModel):
    # Basic Content Info
    title: str
    description: str
    content_text: str  # Main content text
    post_url: str
    platform: str
    content_type: str = "post"  # video, post, article, image, story
    author: str
    publish_date: str
    status: str = "published"  # published, draft, archived
    tags: List[str] = []
    
    # Content Metadata
    brand_name: Optional[str] = None
    campaign_id: Optional[str] = None
    keywords: List[str] = []
    target_audience: List[str] = []
    content_category: str = "general"  # general, promotional, educational, entertainment, news
    language: str = "en"
    priority: str = "medium"  # low, medium, high
    
    # Legacy fields for backward compatibility
    text: Optional[str] = None  # Will map to content_text
    url: Optional[str] = None   # Will map to post_url
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Tesla Model 3 Review",
                "description": "Sharing my experience with the new Tesla Model 3",
                "content_text": "Just got my new Tesla Model 3! Best car ever! #Tesla #EV",
                "post_url": "https://twitter.com/teslaowner/status/123456",
                "platform": "twitter",
                "content_type": "post",
                "author": "@teslaowner",
                "publish_date": "2025-01-28",
                "status": "published",
                "tags": ["tesla", "ev", "review"],
                "brand_name": "Tesla",
                "campaign_id": "winter-sale-2025",
                "keywords": ["tesla", "model 3", "electric vehicle", "ev"],
                "target_audience": ["tech enthusiasts", "ev adopters", "car buyers"],
                "content_category": "promotional",
                "language": "en",
                "priority": "high"
            }
        }

class ContentResponse(BaseModel):
    id: str
    # Basic Content Info
    title: str
    description: str
    content_text: str
    post_url: str
    platform: str
    content_type: str
    author: str
    publish_date: str
    status: str
    tags: List[str]
    
    # Content Metadata
    brand_name: Optional[str] = None
    campaign_id: Optional[str] = None
    keywords: List[str] = []
    target_audience: List[str] = []
    content_category: str = "general"
    language: str = "en"
    priority: str = "medium"
    
    # Analysis Results - Topic Analysis
    topics: List[dict] = []
    dominant_topic: Optional[str] = None
    
    # Analysis Results - Sentiment Analysis
    sentiment_overall: Optional[float] = None
    sentiment_positive: Optional[float] = None
    sentiment_negative: Optional[float] = None
    sentiment_neutral: Optional[float] = None
    sentiment_confidence: Optional[float] = None
    sentiment_breakdown: List[dict] = []
    
    # Analysis Results - Emotion Analysis
    emotion_joy: Optional[float] = None
    emotion_anger: Optional[float] = None
    emotion_fear: Optional[float] = None
    emotion_sadness: Optional[float] = None
    emotion_surprise: Optional[float] = None
    emotion_trust: Optional[float] = None
    emotion_anticipation: Optional[float] = None
    emotion_disgust: Optional[float] = None
    dominant_emotion: Optional[str] = None
    emotion_distribution: List[dict] = []
    
    # Performance Metrics
    engagement_score: Optional[float] = None
    reach_estimate: Optional[int] = None
    virality_score: Optional[float] = None
    content_health_score: Optional[int] = None
    
    # Demographics Analysis
    author_age_group: Optional[str] = None
    author_gender: Optional[str] = None
    author_location_hint: Optional[str] = None
    target_audience_match: Optional[float] = None
    
    # Competitive Analysis
    similar_content_count: Optional[int] = None
    benchmark_engagement: Optional[float] = None
    benchmark_sentiment: Optional[float] = None
    benchmark_topic_trend: Optional[float] = None
    
    # Analysis Status
    analysis_status: str = "pending"
    analysis_type: str = "comprehensive"
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    analyzed_at: Optional[datetime] = None
    
    # Legacy fields for backward compatibility
    text: Optional[str] = None  # Maps to content_text
    url: Optional[str] = None   # Maps to post_url
    sentiment: Optional[str] = None  # Maps to sentiment_overall
    topic: Optional[str] = None      # Maps to dominant_topic

class ContentAnalytics(BaseModel):
    total_contents: int
    by_platform: dict
    by_sentiment: dict
    avg_engagement: float
    top_topics: List[dict]

# ============= CONTENT CRUD ENDPOINTS =============

@router.post("/", response_model=ContentResponse)
async def create_content(content: ContentCreate):
    """
    Manually add content for tracking
    
    Example:
    ```json
    {
        "platform": "twitter",
        "author": "@user",
        "text": "Great product!",
        "url": "https://twitter.com/user/status/123",
        "brand_name": "Tesla"
    }
    ```
    """
    try:
        # Handle legacy field mapping
        content_text = content.content_text or content.text or ""
        post_url = content.post_url or content.url or ""
        
        # Create content analysis document
        content_analysis = ContentAnalysis(
            title=content.title,
            description=content.description,
            content_text=content_text,
            post_url=post_url,
            platform=PlatformType(content.platform.lower()),
            content_type=content.content_type,
            author=content.author,
            publish_date=content.publish_date,
            status=content.status,
            tags=content.tags or [],
            brand_name=content.brand_name,
            campaign_id=content.campaign_id,
            keywords=content.keywords or [],
            target_audience=content.target_audience or [],
            content_category=content.content_category,
            language=content.language,
            priority=content.priority,
            created_at=datetime.now(pytz.UTC),
            updated_at=datetime.now(pytz.UTC)
        )
        
        await content_analysis.insert()
        
        return ContentResponse(
            id=str(content_analysis.id),
            title=content_analysis.title,
            description=content_analysis.description,
            content_text=content_analysis.content_text,
            post_url=content_analysis.post_url,
            platform=content_analysis.platform.value,
            content_type=content_analysis.content_type,
            author=content_analysis.author,
            publish_date=content_analysis.publish_date,
            status=content_analysis.status,
            tags=content_analysis.tags,
            brand_name=content_analysis.brand_name,
            campaign_id=content_analysis.campaign_id,
            keywords=content_analysis.keywords,
            target_audience=content_analysis.target_audience,
            content_category=content_analysis.content_category,
            language=content_analysis.language,
            priority=content_analysis.priority,
            topics=content_analysis.topics,
            dominant_topic=content_analysis.dominant_topic,
            sentiment_overall=content_analysis.sentiment_overall,
            sentiment_positive=content_analysis.sentiment_positive,
            sentiment_negative=content_analysis.sentiment_negative,
            sentiment_neutral=content_analysis.sentiment_neutral,
            sentiment_confidence=content_analysis.sentiment_confidence,
            sentiment_breakdown=content_analysis.sentiment_breakdown,
            emotion_joy=content_analysis.emotion_joy,
            emotion_anger=content_analysis.emotion_anger,
            emotion_fear=content_analysis.emotion_fear,
            emotion_sadness=content_analysis.emotion_sadness,
            emotion_surprise=content_analysis.emotion_surprise,
            emotion_trust=content_analysis.emotion_trust,
            emotion_anticipation=content_analysis.emotion_anticipation,
            emotion_disgust=content_analysis.emotion_disgust,
            dominant_emotion=content_analysis.dominant_emotion,
            emotion_distribution=content_analysis.emotion_distribution,
            engagement_score=content_analysis.engagement_score,
            reach_estimate=content_analysis.reach_estimate,
            virality_score=content_analysis.virality_score,
            content_health_score=content_analysis.content_health_score,
            author_age_group=content_analysis.author_age_group,
            author_gender=content_analysis.author_gender,
            author_location_hint=content_analysis.author_location_hint,
            target_audience_match=content_analysis.target_audience_match,
            similar_content_count=content_analysis.similar_content_count,
            benchmark_engagement=content_analysis.benchmark_engagement,
            benchmark_sentiment=content_analysis.benchmark_sentiment,
            benchmark_topic_trend=content_analysis.benchmark_topic_trend,
            analysis_status=content_analysis.analysis_status,
            analysis_type=content_analysis.analysis_type,
            created_at=content_analysis.created_at,
            updated_at=content_analysis.updated_at,
            analyzed_at=content_analysis.analyzed_at,
            # Legacy fields for backward compatibility
            text=content_analysis.content_text,
            url=content_analysis.post_url,
            sentiment=str(content_analysis.sentiment_overall) if content_analysis.sentiment_overall is not None else None,
            topic=content_analysis.dominant_topic
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[ContentResponse])
async def list_contents(
    skip: int = 0,
    limit: int = 50,
    platform: Optional[str] = None,
    brand_name: Optional[str] = None,
    sentiment: Optional[str] = None,
    search: Optional[str] = None,
    content_type: Optional[str] = None,
    status: Optional[str] = None,
    analysis_status: Optional[str] = None,
    content_category: Optional[str] = None,
    priority: Optional[str] = None,
    language: Optional[str] = None,
    author: Optional[str] = None,
    dominant_topic: Optional[str] = None,
    dominant_emotion: Optional[str] = None
):
    """
    List content analysis with comprehensive filtering and search
    """
    try:
        query = ContentAnalysis.find()
        
        # Basic filters
        if platform:
            query = query.find(ContentAnalysis.platform == PlatformType(platform.lower()))
        if brand_name:
            query = query.find(ContentAnalysis.brand_name == brand_name)
        if content_type:
            query = query.find(ContentAnalysis.content_type == content_type)
        if status:
            query = query.find(ContentAnalysis.status == status)
        if analysis_status:
            query = query.find(ContentAnalysis.analysis_status == analysis_status)
        if content_category:
            query = query.find(ContentAnalysis.content_category == content_category)
        if priority:
            query = query.find(ContentAnalysis.priority == priority)
        if language:
            query = query.find(ContentAnalysis.language == language)
        if author:
            query = query.find(ContentAnalysis.author == author)
        
        # Analysis result filters
        if sentiment:
            if sentiment == "positive":
                query = query.find(ContentAnalysis.sentiment_overall > 0.1)
            elif sentiment == "negative":
                query = query.find(ContentAnalysis.sentiment_overall < -0.1)
            elif sentiment == "neutral":
                query = query.find(ContentAnalysis.sentiment_overall >= -0.1, ContentAnalysis.sentiment_overall <= 0.1)
        
        if dominant_topic:
            query = query.find(ContentAnalysis.dominant_topic == dominant_topic)
        if dominant_emotion:
            query = query.find(ContentAnalysis.dominant_emotion == dominant_emotion)
        
        # Search functionality
        if search:
            # Search in title, description, content_text, and tags
            search_regex = {"$regex": search, "$options": "i"}
            query = query.find({
                "$or": [
                    {"title": search_regex},
                    {"description": search_regex},
                    {"content_text": search_regex},
                    {"tags": {"$in": [search]}},
                    {"keywords": {"$in": [search]}}
                ]
            })
        
        contents = await query.skip(skip).limit(limit).to_list()
        
        return [
            ContentResponse(
                id=str(c.id),
                title=c.title,
                description=c.description,
                content_text=c.content_text,
                post_url=c.post_url,
                platform=c.platform.value,
                content_type=c.content_type,
                author=c.author,
                publish_date=c.publish_date,
                status=c.status,
                tags=c.tags,
                brand_name=c.brand_name,
                campaign_id=c.campaign_id,
                keywords=c.keywords,
                target_audience=c.target_audience,
                content_category=c.content_category,
                language=c.language,
                priority=c.priority,
                topics=c.topics,
                dominant_topic=c.dominant_topic,
                sentiment_overall=c.sentiment_overall,
                sentiment_positive=c.sentiment_positive,
                sentiment_negative=c.sentiment_negative,
                sentiment_neutral=c.sentiment_neutral,
                sentiment_confidence=c.sentiment_confidence,
                sentiment_breakdown=c.sentiment_breakdown,
                emotion_joy=c.emotion_joy,
                emotion_anger=c.emotion_anger,
                emotion_fear=c.emotion_fear,
                emotion_sadness=c.emotion_sadness,
                emotion_surprise=c.emotion_surprise,
                emotion_trust=c.emotion_trust,
                emotion_anticipation=c.emotion_anticipation,
                emotion_disgust=c.emotion_disgust,
                dominant_emotion=c.dominant_emotion,
                emotion_distribution=c.emotion_distribution,
                engagement_score=c.engagement_score,
                reach_estimate=c.reach_estimate,
                virality_score=c.virality_score,
                content_health_score=c.content_health_score,
                author_age_group=c.author_age_group,
                author_gender=c.author_gender,
                author_location_hint=c.author_location_hint,
                target_audience_match=c.target_audience_match,
                similar_content_count=c.similar_content_count,
                benchmark_engagement=c.benchmark_engagement,
                benchmark_sentiment=c.benchmark_sentiment,
                benchmark_topic_trend=c.benchmark_topic_trend,
                analysis_status=c.analysis_status,
                analysis_type=c.analysis_type,
                created_at=c.created_at,
                updated_at=c.updated_at,
                analyzed_at=c.analyzed_at,
                # Legacy fields for backward compatibility
                text=c.content_text,
                url=c.post_url,
                sentiment=str(c.sentiment_overall) if c.sentiment_overall is not None else None,
                topic=c.dominant_topic
            )
            for c in contents
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics", response_model=ContentAnalytics)
async def get_content_analytics(
    brand_name: Optional[str] = None,
    platform: Optional[str] = None,
    days: int = 30
):
    """
    Get aggregate analytics for contents
    """
    try:
        query = Post.find()
        
        if brand_name:
            query = query.find(Post.brand_name == brand_name)
        if platform:
            query = query.find(Post.platform == PlatformType(platform.lower()))
        
        posts = await query.to_list()
        
        # Calculate analytics
        total = len(posts)
        
        by_platform = {}
        by_sentiment = {}
        topics_count = {}
        
        for post in posts:
            # Platform distribution
            platform_key = post.platform.value
            by_platform[platform_key] = by_platform.get(platform_key, 0) + 1
            
            # Sentiment distribution
            if post.sentiment:
                sentiment_key = post.sentiment.value
                by_sentiment[sentiment_key] = by_sentiment.get(sentiment_key, 0) + 1
            
            # Topic counting
            if post.topic:
                topics_count[post.topic] = topics_count.get(post.topic, 0) + 1
        
        # Top topics
        top_topics = [
            {"topic": topic, "count": count}
            for topic, count in sorted(topics_count.items(), key=lambda x: x[1], reverse=True)[:10]
        ]
        
        return ContentAnalytics(
            total_contents=total,
            by_platform=by_platform,
            by_sentiment=by_sentiment,
            avg_engagement=0.0,  # TODO: Calculate from actual engagement data
            top_topics=top_topics
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{content_id}", response_model=ContentResponse)
async def get_content(content_id: str):
    """
    Get specific content analysis by ID
    """
    try:
        from beanie import PydanticObjectId
        
        content = await ContentAnalysis.get(PydanticObjectId(content_id))
        if not content:
            raise HTTPException(status_code=404, detail="Content not found")
        
        return ContentResponse(
            id=str(content.id),
            title=content.title,
            description=content.description,
            content_text=content.content_text,
            post_url=content.post_url,
            platform=content.platform.value,
            content_type=content.content_type,
            author=content.author,
            publish_date=content.publish_date,
            status=content.status,
            tags=content.tags,
            brand_name=content.brand_name,
            campaign_id=content.campaign_id,
            keywords=content.keywords,
            target_audience=content.target_audience,
            content_category=content.content_category,
            language=content.language,
            priority=content.priority,
            topics=content.topics,
            dominant_topic=content.dominant_topic,
            sentiment_overall=content.sentiment_overall,
            sentiment_positive=content.sentiment_positive,
            sentiment_negative=content.sentiment_negative,
            sentiment_neutral=content.sentiment_neutral,
            sentiment_confidence=content.sentiment_confidence,
            sentiment_breakdown=content.sentiment_breakdown,
            emotion_joy=content.emotion_joy,
            emotion_anger=content.emotion_anger,
            emotion_fear=content.emotion_fear,
            emotion_sadness=content.emotion_sadness,
            emotion_surprise=content.emotion_surprise,
            emotion_trust=content.emotion_trust,
            emotion_anticipation=content.emotion_anticipation,
            emotion_disgust=content.emotion_disgust,
            dominant_emotion=content.dominant_emotion,
            emotion_distribution=content.emotion_distribution,
            engagement_score=content.engagement_score,
            reach_estimate=content.reach_estimate,
            virality_score=content.virality_score,
            content_health_score=content.content_health_score,
            author_age_group=content.author_age_group,
            author_gender=content.author_gender,
            author_location_hint=content.author_location_hint,
            target_audience_match=content.target_audience_match,
            similar_content_count=content.similar_content_count,
            benchmark_engagement=content.benchmark_engagement,
            benchmark_sentiment=content.benchmark_sentiment,
            benchmark_topic_trend=content.benchmark_topic_trend,
            analysis_status=content.analysis_status,
            analysis_type=content.analysis_type,
            created_at=content.created_at,
            updated_at=content.updated_at,
            analyzed_at=content.analyzed_at,
            # Legacy fields for backward compatibility
            text=content.content_text,
            url=content.post_url,
            sentiment=str(content.sentiment_overall) if content.sentiment_overall is not None else None,
            topic=content.dominant_topic
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{content_id}", response_model=ContentResponse)
async def update_content(content_id: str, content: ContentCreate):
    """
    Update content analysis by ID
    """
    try:
        from beanie import PydanticObjectId
        
        content_analysis = await ContentAnalysis.get(PydanticObjectId(content_id))
        if not content_analysis:
            raise HTTPException(status_code=404, detail="Content not found")
        
        # Handle legacy field mapping
        content_text = content.content_text or content.text or content_analysis.content_text
        post_url = content.post_url or content.url or content_analysis.post_url
        
        # Update content analysis fields
        content_analysis.title = content.title
        content_analysis.description = content.description
        content_analysis.content_text = content_text
        content_analysis.post_url = post_url
        content_analysis.platform = PlatformType(content.platform.lower())
        content_analysis.content_type = content.content_type
        content_analysis.author = content.author
        content_analysis.publish_date = content.publish_date
        content_analysis.status = content.status
        content_analysis.tags = content.tags or []
        content_analysis.brand_name = content.brand_name
        content_analysis.campaign_id = content.campaign_id
        content_analysis.keywords = content.keywords or []
        content_analysis.target_audience = content.target_audience or []
        content_analysis.content_category = content.content_category
        content_analysis.language = content.language
        content_analysis.priority = content.priority
        content_analysis.updated_at = datetime.now(pytz.UTC)
        
        await content_analysis.save()
        
        return ContentResponse(
            id=str(content_analysis.id),
            title=content_analysis.title,
            description=content_analysis.description,
            content_text=content_analysis.content_text,
            post_url=content_analysis.post_url,
            platform=content_analysis.platform.value,
            content_type=content_analysis.content_type,
            author=content_analysis.author,
            publish_date=content_analysis.publish_date,
            status=content_analysis.status,
            tags=content_analysis.tags,
            brand_name=content_analysis.brand_name,
            campaign_id=content_analysis.campaign_id,
            keywords=content_analysis.keywords,
            target_audience=content_analysis.target_audience,
            content_category=content_analysis.content_category,
            language=content_analysis.language,
            priority=content_analysis.priority,
            topics=content_analysis.topics,
            dominant_topic=content_analysis.dominant_topic,
            sentiment_overall=content_analysis.sentiment_overall,
            sentiment_positive=content_analysis.sentiment_positive,
            sentiment_negative=content_analysis.sentiment_negative,
            sentiment_neutral=content_analysis.sentiment_neutral,
            sentiment_confidence=content_analysis.sentiment_confidence,
            sentiment_breakdown=content_analysis.sentiment_breakdown,
            emotion_joy=content_analysis.emotion_joy,
            emotion_anger=content_analysis.emotion_anger,
            emotion_fear=content_analysis.emotion_fear,
            emotion_sadness=content_analysis.emotion_sadness,
            emotion_surprise=content_analysis.emotion_surprise,
            emotion_trust=content_analysis.emotion_trust,
            emotion_anticipation=content_analysis.emotion_anticipation,
            emotion_disgust=content_analysis.emotion_disgust,
            dominant_emotion=content_analysis.dominant_emotion,
            emotion_distribution=content_analysis.emotion_distribution,
            engagement_score=content_analysis.engagement_score,
            reach_estimate=content_analysis.reach_estimate,
            virality_score=content_analysis.virality_score,
            content_health_score=content_analysis.content_health_score,
            author_age_group=content_analysis.author_age_group,
            author_gender=content_analysis.author_gender,
            author_location_hint=content_analysis.author_location_hint,
            target_audience_match=content_analysis.target_audience_match,
            similar_content_count=content_analysis.similar_content_count,
            benchmark_engagement=content_analysis.benchmark_engagement,
            benchmark_sentiment=content_analysis.benchmark_sentiment,
            benchmark_topic_trend=content_analysis.benchmark_topic_trend,
            analysis_status=content_analysis.analysis_status,
            analysis_type=content_analysis.analysis_type,
            created_at=content_analysis.created_at,
            updated_at=content_analysis.updated_at,
            analyzed_at=content_analysis.analyzed_at,
            # Legacy fields for backward compatibility
            text=content_analysis.content_text,
            url=content_analysis.post_url,
            sentiment=str(content_analysis.sentiment_overall) if content_analysis.sentiment_overall is not None else None,
            topic=content_analysis.dominant_topic
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{content_id}")
async def delete_content(content_id: str):
    """
    Delete a content analysis
    """
    try:
        from beanie import PydanticObjectId
        
        content = await ContentAnalysis.get(PydanticObjectId(content_id))
        if not content:
            raise HTTPException(status_code=404, detail="Content not found")
        
        await content.delete()
        
        return {"message": "Content deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{content_id}/scrape")
async def trigger_content_scraping(content_id: str):
    """
    Trigger scraping for content and comments
    """
    try:
        from beanie import PydanticObjectId
        
        # Verify content exists
        content = await ContentAnalysis.get(PydanticObjectId(content_id))
        if not content:
            raise HTTPException(status_code=404, detail="Content not found")
        
        # Check if already running
        if content.analysis_status == "running":
            return {"message": "Scraping already in progress", "status": "running"}
        
        # Start scraping process
        async with ContentScraperService() as scraper:
            result = await scraper.scrape_content_and_comments(content_id)
            
            if result["success"]:
                return {
                    "message": "Content and comments scraped successfully",
                    "status": "completed",
                    "data": result["data"]
                }
            else:
                raise HTTPException(status_code=500, detail=result["message"])
                
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{content_id}/scraped-data")
async def get_scraped_data(content_id: str):
    """
    Get scraped data for a content analysis
    """
    try:
        from beanie import PydanticObjectId
        
        content = await ContentAnalysis.get(PydanticObjectId(content_id))
        if not content:
            raise HTTPException(status_code=404, detail="Content not found")
        
        return {
            "content_id": content_id,
            "analysis_status": content.analysis_status,
            "analyzed_at": content.analyzed_at,
            "engagement_score": content.engagement_score,
            "reach_estimate": content.reach_estimate,
            "virality_score": content.virality_score,
            "content_health_score": content.content_health_score,
            "scraped_data": content.raw_analysis_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


