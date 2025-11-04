"""
Brand Admin Write API
Direct write operations for Brand analysis collections.
"""
from typing import Any, Dict, List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from app.api.admin.auth import admin_auth
from app.services.database_service import db_service


router = APIRouter()


class SummaryPayload(BaseModel):
    total_posts: Optional[int] = 0
    total_engagement: Optional[int] = 0
    avg_engagement_per_post: Optional[float] = 0
    sentiment_distribution: Optional[Dict[str, int]] = Field(default_factory=dict)
    sentiment_percentage: Optional[Dict[str, float]] = Field(default_factory=dict)
    platform_breakdown: Optional[Dict[str, int]] = Field(default_factory=dict)
    trending_topics: Optional[List[Dict[str, Any]]] = Field(default_factory=list)


class TimelineEntry(BaseModel):
    date: str
    Positive: Optional[int] = 0
    Neutral: Optional[int] = 0
    Negative: Optional[int] = 0
    total_posts: Optional[int] = 0
    total_likes: Optional[int] = 0
    total_comments: Optional[int] = 0
    total_shares: Optional[int] = 0
    positive_percentage: Optional[float] = 0
    neutral_percentage: Optional[float] = 0
    negative_percentage: Optional[float] = 0


class TimelinePayload(BaseModel):
    entries: List[TimelineEntry]


async def _ensure_analysis(brand_id: str) -> str:
    """Get or create a manual override analysis for a brand."""
    analysis_name = "manual_override"
    try:
        return await db_service.create_brand_analysis(
            brand_id=brand_id,
            analysis_name=analysis_name,
            analysis_type="manual",
            keywords=[],
            platforms=[],
            date_range={},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to prepare analysis: {e}")


@router.post("/brands/{brand_id}/summary", dependencies=[Depends(admin_auth)])
async def admin_write_brand_summary(brand_id: str, payload: SummaryPayload):
    """Write brand summary into brand_metrics collection (new analysis snapshot)."""
    brand = await db_service.get_brand_by_id(brand_id)
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")

    analysis_id = await _ensure_analysis(brand_id)
    metrics_data: Dict[str, Any] = {
        "total_posts": payload.total_posts or 0,
        "total_engagement": payload.total_engagement or 0,
        "avg_engagement_per_post": payload.avg_engagement_per_post or 0,
        "sentiment_distribution": payload.sentiment_distribution or {},
        "sentiment_percentage": payload.sentiment_percentage or {},
        "overall_sentiment_score": float(payload.sentiment_percentage.get("Positive", 0.0)) if payload.sentiment_percentage else 0.0,
        "platform_breakdown": payload.platform_breakdown or {},
        "trending_topics": payload.trending_topics or [],
        "demographics": {},
        "engagement_patterns": {},
        "performance_metrics": {},
        "emotions": {},
        "competitive_analysis": {},
    }

    await db_service.save_brand_metrics(analysis_id, brand_id, metrics_data)
    await db_service.update_brand_analysis_status(
        analysis_id,
        status="completed",
        total_posts=metrics_data["total_posts"],
        total_engagement=metrics_data["total_engagement"],
        sentiment_distribution=metrics_data["sentiment_distribution"],
        top_topics=[t.get("topic") for t in (payload.trending_topics or [])],
    )

    return {"analysis_id": analysis_id, "updated": 1}


@router.post("/brands/{brand_id}/timeline:upsert", dependencies=[Depends(admin_auth)])
async def admin_write_brand_timeline(brand_id: str, payload: TimelinePayload):
    """Upsert timeline entries for a brand into brand_sentiment_timeline."""
    brand = await db_service.get_brand_by_id(brand_id)
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")

    analysis_id = await _ensure_analysis(brand_id)

    entries = []
    for e in payload.entries:
        try:
            dt = datetime.fromisoformat(e.date)
        except Exception:
            raise HTTPException(status_code=400, detail=f"Invalid date format: {e.date}")
        entry = {
            "date": dt,
            "sentiment_score": 0.0,
            "positive_count": e.Positive or 0,
            "negative_count": e.Negative or 0,
            "neutral_count": e.Neutral or 0,
            "total_posts": e.total_posts or 0,
            "platform_breakdown": {},
        }
        entries.append(entry)

    await db_service.save_brand_sentiment_timeline(analysis_id, brand_id, entries)
    await db_service.update_brand_analysis_status(analysis_id, status="completed")

    return {"analysis_id": analysis_id, "inserted": len(entries)}


# ============= Additional Brand Write Endpoints =============

class TopicItem(BaseModel):
    topic: str
    count: Optional[int] = 0
    sentiment: Optional[float] = 0.0
    engagement: Optional[int] = 0
    positive: Optional[int] = 0
    negative: Optional[int] = 0
    neutral: Optional[int] = 0
    platform: Optional[str] = None


class TopicsPayload(BaseModel):
    items: List[TopicItem]


@router.post("/brands/{brand_id}/topics:replace", dependencies=[Depends(admin_auth)])
async def admin_write_brand_topics(brand_id: str, payload: TopicsPayload):
    """Replace topics data for a brand."""
    brand = await db_service.get_brand_by_id(brand_id)
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")

    analysis_id = await _ensure_analysis(brand_id)

    # Delete existing topics
    from app.models.database import BrandTrendingTopics
    await BrandTrendingTopics.find(
        BrandTrendingTopics.brand_analysis_id == analysis_id
    ).delete()

    # Save new topics
    topics_data = []
    for item in payload.items:
        topics_data.append({
            "topic": item.topic,
            "count": item.count or 0,
            "sentiment": item.sentiment or 0.0,
            "engagement": item.engagement or 0,
            "positive": item.positive or 0,
            "negative": item.negative or 0,
            "neutral": item.neutral or 0,
            "platform": item.platform or "all",
        })

    await db_service.save_brand_trending_topics(analysis_id, brand_id, topics_data)
    await db_service.update_brand_analysis_status(analysis_id, status="completed")

    return {"analysis_id": analysis_id, "replaced": len(topics_data)}


class EmotionItem(BaseModel):
    emotion: str
    count: Optional[int] = 0
    percentage: Optional[float] = 0.0


class EmotionsPayload(BaseModel):
    emotions: List[EmotionItem]


@router.post("/brands/{brand_id}/emotions", dependencies=[Depends(admin_auth)])
async def admin_write_brand_emotions(brand_id: str, payload: EmotionsPayload):
    """Write emotions data for a brand."""
    brand = await db_service.get_brand_by_id(brand_id)
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")

    analysis_id = await _ensure_analysis(brand_id)

    emotions_data = {
        "emotions": [{"emotion": e.emotion, "count": e.count or 0, "percentage": e.percentage or 0.0} for e in payload.emotions],
    }

    await db_service.save_brand_emotions(analysis_id, brand_id, emotions_data)
    await db_service.update_brand_analysis_status(analysis_id, status="completed")

    return {"analysis_id": analysis_id, "updated": 1}


class DemographicsAgeGroup(BaseModel):
    age_group: str
    count: Optional[int] = 0
    percentage: Optional[float] = 0.0


class DemographicsGender(BaseModel):
    gender: str
    count: Optional[int] = 0
    percentage: Optional[float] = 0.0


class DemographicsLocation(BaseModel):
    location: str
    count: Optional[int] = 0
    percentage: Optional[float] = 0.0


class DemographicsPayload(BaseModel):
    total_analyzed: Optional[int] = 0
    age_groups: Optional[List[DemographicsAgeGroup]] = Field(default_factory=list)
    genders: Optional[List[DemographicsGender]] = Field(default_factory=list)
    top_locations: Optional[List[DemographicsLocation]] = Field(default_factory=list)


@router.post("/brands/{brand_id}/demographics", dependencies=[Depends(admin_auth)])
async def admin_write_brand_demographics(brand_id: str, payload: DemographicsPayload):
    """Write demographics data for a brand."""
    brand = await db_service.get_brand_by_id(brand_id)
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")

    analysis_id = await _ensure_analysis(brand_id)

    demographics_data = {
        "platform": "all",
        "total_analyzed": payload.total_analyzed or 0,
        "age_groups": [{"age_group": a.age_group, "count": a.count or 0, "percentage": a.percentage or 0.0} for a in (payload.age_groups or [])],
        "genders": [{"gender": g.gender, "count": g.count or 0, "percentage": g.percentage or 0.0} for g in (payload.genders or [])],
        "top_locations": [{"location": l.location, "count": l.count or 0, "percentage": l.percentage or 0.0} for l in (payload.top_locations or [])],
    }

    await db_service.save_brand_demographics(analysis_id, brand_id, demographics_data)
    await db_service.update_brand_analysis_status(analysis_id, status="completed")

    return {"analysis_id": analysis_id, "updated": 1}


class PerformancePayload(BaseModel):
    total_posts: Optional[int] = 0
    total_engagement: Optional[int] = 0
    total_likes: Optional[int] = 0
    total_comments: Optional[int] = 0
    total_shares: Optional[int] = 0
    avg_engagement_per_post: Optional[float] = 0.0
    avg_likes_per_post: Optional[float] = 0.0
    avg_comments_per_post: Optional[float] = 0.0
    avg_shares_per_post: Optional[float] = 0.0
    engagement_rate: Optional[float] = 0.0
    estimated_reach: Optional[int] = 0


@router.post("/brands/{brand_id}/performance", dependencies=[Depends(admin_auth)])
async def admin_write_brand_performance(brand_id: str, payload: PerformancePayload):
    """Write performance metrics for a brand."""
    brand = await db_service.get_brand_by_id(brand_id)
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")

    analysis_id = await _ensure_analysis(brand_id)

    performance_data = {
        "total_posts": payload.total_posts or 0,
        "total_engagement": payload.total_engagement or 0,
        "total_likes": payload.total_likes or 0,
        "total_comments": payload.total_comments or 0,
        "total_shares": payload.total_shares or 0,
        "avg_engagement_per_post": payload.avg_engagement_per_post or 0.0,
        "avg_likes_per_post": payload.avg_likes_per_post or 0.0,
        "avg_comments_per_post": payload.avg_comments_per_post or 0.0,
        "avg_shares_per_post": payload.avg_shares_per_post or 0.0,
        "engagement_rate": payload.engagement_rate or 0.0,
        "estimated_reach": payload.estimated_reach or 0,
    }

    await db_service.save_brand_performance(analysis_id, brand_id, performance_data)
    await db_service.update_brand_analysis_status(analysis_id, status="completed")

    return {"analysis_id": analysis_id, "updated": 1}


class EngagementPattern(BaseModel):
    time_slot: Optional[str] = None
    day_of_week: Optional[str] = None
    avg_engagement: Optional[float] = 0.0
    post_count: Optional[int] = 0
    platform: Optional[str] = None


class EngagementPatternsPayload(BaseModel):
    peak_hours: Optional[List[str]] = Field(default_factory=list)
    active_days: Optional[List[str]] = Field(default_factory=list)
    avg_engagement_rate: Optional[float] = 0.0
    total_posts: Optional[int] = 0
    patterns: Optional[List[EngagementPattern]] = Field(default_factory=list)


@router.post("/brands/{brand_id}/engagement-patterns", dependencies=[Depends(admin_auth)])
async def admin_write_brand_engagement_patterns(brand_id: str, payload: EngagementPatternsPayload):
    """Write engagement patterns for a brand."""
    brand = await db_service.get_brand_by_id(brand_id)
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")

    analysis_id = await _ensure_analysis(brand_id)

    patterns_data = {
        "peak_hours": payload.peak_hours or [],
        "active_days": payload.active_days or [],
        "avg_engagement_rate": payload.avg_engagement_rate or 0.0,
        "total_posts": payload.total_posts or 0,
        "patterns": [{
            "time_slot": p.time_slot,
            "day_of_week": p.day_of_week,
            "avg_engagement": p.avg_engagement or 0.0,
            "post_count": p.post_count or 0,
            "platform": p.platform or "all",
        } for p in (payload.patterns or [])],
    }

    await db_service.save_brand_engagement_patterns(analysis_id, brand_id, patterns_data)
    await db_service.update_brand_analysis_status(analysis_id, status="completed")

    return {"analysis_id": analysis_id, "updated": 1}


class CompetitivePayload(BaseModel):
    brand_metrics: Optional[Dict[str, Any]] = Field(default_factory=dict)
    industry_benchmarks: Optional[Dict[str, Any]] = Field(default_factory=dict)
    performance_vs_benchmark: Optional[Dict[str, Any]] = Field(default_factory=dict)
    market_position: Optional[str] = None
    recommendations: Optional[List[str]] = Field(default_factory=list)


@router.post("/brands/{brand_id}/competitive", dependencies=[Depends(admin_auth)])
async def admin_write_brand_competitive(brand_id: str, payload: CompetitivePayload):
    """Write competitive analysis data for a brand."""
    brand = await db_service.get_brand_by_id(brand_id)
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")

    analysis_id = await _ensure_analysis(brand_id)

    competitive_data = {
        "brand_metrics": payload.brand_metrics or {},
        "industry_benchmarks": payload.industry_benchmarks or {},
        "performance_vs_benchmark": payload.performance_vs_benchmark or {},
        "market_position": payload.market_position or "follower",
        "recommendations": payload.recommendations or [],
    }

    # Save to brand_metrics as competitive_analysis field
    from app.models.database import BrandMetrics
    metrics = await BrandMetrics.find_one(
        BrandMetrics.brand_analysis_id == analysis_id
    )
    
    if metrics:
        metrics.competitive_analysis = competitive_data
        await metrics.save()
    else:
        # Create new metrics entry
        metrics_data: Dict[str, Any] = {
            "total_posts": 0,
            "total_engagement": 0,
            "competitive_analysis": competitive_data,
        }
        await db_service.save_brand_metrics(analysis_id, brand_id, metrics_data)

    await db_service.update_brand_analysis_status(analysis_id, status="completed")

    return {"analysis_id": analysis_id, "updated": 1}

