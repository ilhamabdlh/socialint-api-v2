from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
import pytz

from app.models.database import Post, PlatformType, SentimentType

router = APIRouter(prefix="/contents", tags=["Content Management"])

# ============= REQUEST/RESPONSE SCHEMAS =============

class ContentCreate(BaseModel):
    platform: str
    author: str
    text: str
    url: Optional[str] = None
    brand_name: Optional[str] = None
    campaign_id: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "platform": "twitter",
                "author": "@teslaowner",
                "text": "Just got my new Tesla Model 3! Best car ever! #Tesla #EV",
                "url": "https://twitter.com/teslaowner/status/123456",
                "brand_name": "Tesla",
                "campaign_id": "winter-sale-2025"
            }
        }

class ContentResponse(BaseModel):
    id: str
    platform: str
    author: str
    text: str
    url: Optional[str]
    brand_name: Optional[str]
    sentiment: Optional[str]
    topic: Optional[str]
    engagement_score: Optional[float]
    created_at: datetime
    analyzed_at: Optional[datetime]

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
        # Create post document
        post = Post(
            platform=PlatformType(content.platform.lower()),
            author=content.author,
            text=content.text,
            url=content.url or "",
            brand_name=content.brand_name or "",
            created_at=datetime.now(pytz.UTC)
        )
        
        await post.insert()
        
        return ContentResponse(
            id=str(post.id),
            platform=post.platform.value,
            author=post.author,
            text=post.text,
            url=post.url,
            brand_name=post.brand_name,
            sentiment=post.sentiment.value if post.sentiment else None,
            topic=post.topic,
            engagement_score=None,
            created_at=post.created_at,
            analyzed_at=None
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
    search: Optional[str] = None
):
    """
    List contents with filtering and search
    """
    try:
        query = Post.find()
        
        if platform:
            query = query.find(Post.platform == PlatformType(platform.lower()))
        if brand_name:
            query = query.find(Post.brand_name == brand_name)
        if sentiment:
            query = query.find(Post.sentiment == SentimentType(sentiment.lower()))
        if search:
            # Simple text search in content
            query = query.find({"text": {"$regex": search, "$options": "i"}})
        
        posts = await query.skip(skip).limit(limit).to_list()
        
        return [
            ContentResponse(
                id=str(p.id),
                platform=p.platform.value,
                author=p.author,
                text=p.text,
                url=p.url,
                brand_name=p.brand_name,
                sentiment=p.sentiment.value if p.sentiment else None,
                topic=p.topic,
                engagement_score=None,
                created_at=p.created_at,
                analyzed_at=None
            )
            for p in posts
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
    Get specific content by ID
    """
    try:
        from beanie import PydanticObjectId
        
        post = await Post.get(PydanticObjectId(content_id))
        if not post:
            raise HTTPException(status_code=404, detail="Content not found")
        
        return ContentResponse(
            id=str(post.id),
            platform=post.platform.value,
            author=post.author,
            text=post.text,
            url=post.url,
            brand_name=post.brand_name,
            sentiment=post.sentiment.value if post.sentiment else None,
            topic=post.topic,
            engagement_score=None,
            created_at=post.created_at,
            analyzed_at=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{content_id}")
async def delete_content(content_id: str):
    """
    Delete a content
    """
    try:
        from beanie import PydanticObjectId
        
        post = await Post.get(PydanticObjectId(content_id))
        if not post:
            raise HTTPException(status_code=404, detail="Content not found")
        
        await post.delete()
        
        return {"message": "Content deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


