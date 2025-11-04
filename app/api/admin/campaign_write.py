"""
Campaign Admin Write API
Direct write operations for Campaign analysis collections.
"""
from typing import Any, Dict, List, Optional
from datetime import datetime
from bson import ObjectId

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from app.api.admin.auth import admin_auth
from app.models.database import Campaign, CampaignMetrics, Brand


router = APIRouter()


class CampaignSummaryPayload(BaseModel):
    # Raw fields from CMS UI
    total_mentions: Optional[int] = 0
    positive_sentiment_pct: Optional[float] = None  # 0-100 (preferred)
    total_engagement: Optional[int] = None
    reach: Optional[int] = 0
    # Backward compatible fields
    overall_sentiment: Optional[float] = None  # -1..1 (if provided, override conversion)
    engagement_rate: Optional[float] = None  # % (if provided, override conversion)
    # Trends
    sentiment_trend: Optional[float] = 0.0
    mentions_trend: Optional[float] = 0.0
    engagement_trend: Optional[float] = 0.0


class CampaignMetricsEntry(BaseModel):
    metric_date: str  # ISO format
    sentiment_score: Optional[float] = 0.0  # 0-100
    total_mentions: Optional[int] = 0
    positive_count: Optional[int] = 0
    negative_count: Optional[int] = 0
    neutral_count: Optional[int] = 0
    total_likes: Optional[int] = 0
    total_comments: Optional[int] = 0
    total_shares: Optional[int] = 0
    total_views: Optional[int] = 0
    engagement_rate: Optional[float] = 0.0
    reach: Optional[int] = 0
    impressions: Optional[int] = 0
    unique_users: Optional[int] = 0
    platform_distribution: Optional[Dict[str, int]] = Field(default_factory=dict)
    topic_distribution: Optional[Dict[str, int]] = Field(default_factory=dict)
    platform_sentiment: Optional[Dict[str, Dict[str, int]]] = Field(default_factory=dict)
    top_topics: Optional[List[str]] = Field(default_factory=list)


class CampaignTimelinePayload(BaseModel):
    entries: List[CampaignMetricsEntry]


class CampaignTopicPayload(BaseModel):
    items: List[Dict[str, Any]]  # {topic, count, sentiment, engagement, likes, comments, shares, positive, negative, neutral}


class CampaignEmotionPayload(BaseModel):
    total_emotions: Optional[int] = 0
    dominant_emotion: Optional[str] = ""
    emotions: Optional[List[Dict[str, Any]]] = Field(default_factory=list)  # [{emotion, percentage, count}]


class CampaignAudiencePayload(BaseModel):
    demographics: List[Dict[str, Any]]  # [{category, value, percentage, count, platform?}]


class CampaignPerformancePayload(BaseModel):
    overall_metrics: Optional[Dict[str, Any]] = Field(default_factory=dict)  # {total_views, total_engagement, total_likes, total_comments, total_shares}
    platform_breakdown: Optional[List[Dict[str, Any]]] = Field(default_factory=list)  # [{platform, posts, total_views, ...}]
    conversion_funnel: Optional[Dict[str, int]] = Field(default_factory=dict)  # {engagement, clicks, conversions}


async def _get_campaign(campaign_id: str) -> Campaign:
    """Get campaign by ID and validate"""
    try:
        if not ObjectId.is_valid(campaign_id):
            raise HTTPException(status_code=400, detail="Invalid campaign ID format")
        campaign = await Campaign.get(ObjectId(campaign_id))
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
        return campaign
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching campaign: {str(e)}")


@router.post("/campaigns/{campaign_id}/summary", dependencies=[Depends(admin_auth)])
async def admin_write_campaign_summary(campaign_id: str, payload: CampaignSummaryPayload):
    """Write campaign summary metrics directly to Campaign document AND CampaignMetrics."""
    campaign = await _get_campaign(campaign_id)
    
    # Derivations (server-side) to honor raw CMS inputs
    # overall_sentiment: prefer explicit field, else derive from positive_sentiment_pct
    derived_overall_sentiment: float = 0.0
    if payload.overall_sentiment is not None:
        derived_overall_sentiment = float(payload.overall_sentiment)
    elif payload.positive_sentiment_pct is not None:
        try:
            pct = max(0.0, min(100.0, float(payload.positive_sentiment_pct)))
            derived_overall_sentiment = (pct / 50.0) - 1.0
        except Exception:
            derived_overall_sentiment = 0.0
    # engagement_rate: prefer explicit field, else derive from total_engagement/reach
    derived_engagement_rate: float = 0.0
    if payload.engagement_rate is not None:
        derived_engagement_rate = float(payload.engagement_rate)
    elif payload.total_engagement is not None and (payload.reach or 0) > 0:
        try:
            derived_engagement_rate = (float(payload.total_engagement) / max(1.0, float(payload.reach or 0))) * 100.0
        except Exception:
            derived_engagement_rate = 0.0

    # Update campaign cached metrics
    campaign.total_mentions = payload.total_mentions or 0
    campaign.overall_sentiment = derived_overall_sentiment
    campaign.engagement_rate = derived_engagement_rate
    campaign.reach = payload.reach or 0
    campaign.sentiment_trend = payload.sentiment_trend or 0.0
    campaign.mentions_trend = payload.mentions_trend or 0.0
    campaign.engagement_trend = payload.engagement_trend or 0.0
    campaign.last_analysis_at = datetime.now()
    campaign.updated_at = datetime.now()
    
    await campaign.save()
    
    # 🔧 FIX: Also update/create CampaignMetrics entry so Results endpoint can read it
    from app.models.database import CampaignMetrics
    from bson import ObjectId
    
    # Get or create latest CampaignMetrics entry
    latest_metric = await CampaignMetrics.find(
        CampaignMetrics.campaign.id == campaign.id
    ).sort("-metric_date").first_or_none()
    
    if not latest_metric:
        # Create new metric entry for today
        brand = await campaign.brand.fetch()
        latest_metric = CampaignMetrics(
            campaign=ObjectId(campaign_id),
            brand=ObjectId(str(brand.id)) if brand else None,
            metric_date=datetime.now().date(),
            sentiment_score=derived_overall_sentiment,
            total_mentions=payload.total_mentions or 0,
            positive_count=0,
            negative_count=0,
            neutral_count=0,
            total_likes=0,
            total_comments=0,
            total_shares=0,
            engagement_rate=derived_engagement_rate,
            reach=payload.reach or 0,
            impressions=payload.reach or 0,
            platform_distribution={},
            topic_distribution={},
            top_topics=[],
            is_manual_override=True  # Mark as manual override
        )
    else:
        # Update existing metric entry with manual override flag
        latest_metric.sentiment_score = derived_overall_sentiment
        latest_metric.total_mentions = payload.total_mentions or 0
        latest_metric.engagement_rate = derived_engagement_rate
        latest_metric.reach = payload.reach or 0
        latest_metric.impressions = payload.reach or 0
        latest_metric.metric_date = datetime.now().date()
        latest_metric.is_manual_override = True  # Mark as manual override
    
    await latest_metric.save()
    
    return {"campaign_id": str(campaign.id), "updated": 1, "metric_updated": True}


@router.post("/campaigns/{campaign_id}/timeline:upsert", dependencies=[Depends(admin_auth)])
async def admin_write_campaign_timeline(campaign_id: str, payload: CampaignTimelinePayload):
    """Upsert campaign metrics entries into campaign_metrics collection."""
    campaign = await _get_campaign(campaign_id)
    brand = await campaign.brand.fetch()
    
    inserted = 0
    updated = 0
    
    for entry in payload.entries:
        try:
            metric_date = datetime.fromisoformat(entry.metric_date.replace('Z', '+00:00'))
        except Exception:
            raise HTTPException(status_code=400, detail=f"Invalid date format: {entry.metric_date}")
        
        # Check if metric already exists for this date
        existing = await CampaignMetrics.find_one(
            CampaignMetrics.campaign.id == campaign.id,
            CampaignMetrics.metric_date == metric_date
        )
        
        if existing:
            # Update existing
            existing.sentiment_score = entry.sentiment_score or 0.0
            existing.total_mentions = entry.total_mentions or 0
            existing.positive_count = entry.positive_count or 0
            existing.negative_count = entry.negative_count or 0
            existing.neutral_count = entry.neutral_count or 0
            existing.total_likes = entry.total_likes or 0
            existing.total_comments = entry.total_comments or 0
            existing.total_shares = entry.total_shares or 0
            existing.total_views = entry.total_views or 0
            existing.engagement_rate = entry.engagement_rate or 0.0
            existing.reach = entry.reach or 0
            existing.impressions = entry.impressions or 0
            existing.unique_users = entry.unique_users or 0
            existing.platform_distribution = entry.platform_distribution or {}
            existing.topic_distribution = entry.topic_distribution or {}
            existing.platform_sentiment = entry.platform_sentiment or {}
            existing.top_topics = entry.top_topics or []
            await existing.save()
            updated += 1
        else:
            # Insert new
            metric = CampaignMetrics(
                campaign=campaign,
                brand=brand,
                metric_date=metric_date,
                sentiment_score=entry.sentiment_score or 0.0,
                total_mentions=entry.total_mentions or 0,
                positive_count=entry.positive_count or 0,
                negative_count=entry.negative_count or 0,
                neutral_count=entry.neutral_count or 0,
                total_likes=entry.total_likes or 0,
                total_comments=entry.total_comments or 0,
                total_shares=entry.total_shares or 0,
                total_views=entry.total_views or 0,
                engagement_rate=entry.engagement_rate or 0.0,
                reach=entry.reach or 0,
                impressions=entry.impressions or 0,
                unique_users=entry.unique_users or 0,
                platform_distribution=entry.platform_distribution or {},
                topic_distribution=entry.topic_distribution or {},
                platform_sentiment=entry.platform_sentiment or {},
                top_topics=entry.top_topics or [],
            )
            await metric.insert()
            inserted += 1
    
    return {"campaign_id": str(campaign.id), "inserted": inserted, "updated": updated}


@router.post("/campaigns/{campaign_id}/topics:replace", dependencies=[Depends(admin_auth)])
async def admin_write_campaign_topics(
    campaign_id: str,
    payload: CampaignTopicPayload,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    platforms: Optional[str] = None
):
    """
    Replace topics data for a campaign.
    Stores topics in campaign_metrics as topic_distribution or top_topics.
    """
    campaign = await _get_campaign(campaign_id)
    
    # Convert topics to topic_distribution format
    topic_distribution: Dict[str, int] = {}
    top_topics: List[str] = []
    
    for item in payload.items:
        topic_name = item.get("topic", "")
        count = item.get("count", 0)
        if topic_name:
            topic_distribution[topic_name] = count
            top_topics.append(topic_name)
    
    # Find or create latest campaign metric to store topics
    latest_metric = await CampaignMetrics.find(
        CampaignMetrics.campaign.id == campaign.id
    ).sort("-metric_date").first_or_none()
    
    if latest_metric:
        latest_metric.topic_distribution = topic_distribution
        latest_metric.top_topics = top_topics[:10]  # Top 10
        await latest_metric.save()
        return {"campaign_id": str(campaign.id), "topics_count": len(topic_distribution), "updated": 1}
    else:
        # Create a new metric entry with current date
        brand = await campaign.brand.fetch()
        metric = CampaignMetrics(
            campaign=campaign,
            brand=brand,
            metric_date=datetime.now(),
            topic_distribution=topic_distribution,
            top_topics=top_topics[:10],
        )
        await metric.insert()
        return {"campaign_id": str(campaign.id), "topics_count": len(topic_distribution), "inserted": 1}


@router.post("/campaigns/{campaign_id}/emotions", dependencies=[Depends(admin_auth)])
async def admin_write_campaign_emotions(campaign_id: str, payload: CampaignEmotionPayload):
    """Write campaign emotions data (stored in latest campaign_metrics or as separate snapshot)."""
    campaign = await _get_campaign(campaign_id)
    brand = await campaign.brand.fetch()
    
    # Store emotions in a new or latest campaign_metrics entry
    latest_metric = await CampaignMetrics.find(
        CampaignMetrics.campaign.id == campaign.id
    ).sort("-metric_date").first_or_none()
    
    emotions_data = {
        "total_emotions": payload.total_emotions or 0,
        "dominant_emotion": payload.dominant_emotion or "",
        "emotions": payload.emotions or [],
    }
    
    if latest_metric:
        # Store emotions as custom field (MongoDB allows additional fields)
        setattr(latest_metric, 'emotions', emotions_data)
        await latest_metric.save()
        return {"campaign_id": str(campaign.id), "updated": 1}
    else:
        # Create new metric with emotions
        metric = CampaignMetrics(
            campaign=campaign,
            brand=brand,
            metric_date=datetime.now(),
        )
        setattr(metric, 'emotions', emotions_data)
        await metric.insert()
        return {"campaign_id": str(campaign.id), "inserted": 1}


@router.post("/campaigns/{campaign_id}/audience", dependencies=[Depends(admin_auth)])
async def admin_write_campaign_audience(campaign_id: str, payload: CampaignAudiencePayload):
    """Write campaign audience demographics (stored in latest campaign_metrics)."""
    campaign = await _get_campaign(campaign_id)
    brand = await campaign.brand.fetch()
    
    latest_metric = await CampaignMetrics.find(
        CampaignMetrics.campaign.id == campaign.id
    ).sort("-metric_date").first_or_none()
    
    demographics_data = payload.demographics
    
    if latest_metric:
        setattr(latest_metric, 'demographics', demographics_data)
        await latest_metric.save()
        return {"campaign_id": str(campaign.id), "updated": 1}
    else:
        metric = CampaignMetrics(
            campaign=campaign,
            brand=brand,
            metric_date=datetime.now(),
        )
        setattr(metric, 'demographics', demographics_data)
        await metric.insert()
        return {"campaign_id": str(campaign.id), "inserted": 1}


@router.post("/campaigns/{campaign_id}/performance", dependencies=[Depends(admin_auth)])
async def admin_write_campaign_performance(campaign_id: str, payload: CampaignPerformancePayload):
    """Write campaign performance metrics."""
    campaign = await _get_campaign(campaign_id)
    brand = await campaign.brand.fetch()
    
    latest_metric = await CampaignMetrics.find(
        CampaignMetrics.campaign.id == campaign.id
    ).sort("-metric_date").first_or_none()
    
    # Map performance payload into existing CampaignMetrics fields
    overall = payload.overall_metrics or {}
    platform_breakdown = payload.platform_breakdown or []
    
    def apply_to_metric(metric: CampaignMetrics):
        # Overall metrics → existing numeric fields
        metric.total_views = int(overall.get("total_views", overall.get("views", metric.total_views or 0)) or 0)
        metric.total_likes = int(overall.get("total_likes", overall.get("likes", metric.total_likes or 0)) or 0)
        metric.total_comments = int(overall.get("total_comments", overall.get("comments", metric.total_comments or 0)) or 0)
        metric.total_shares = int(overall.get("total_shares", overall.get("shares", metric.total_shares or 0)) or 0)
        # total_engagement not a field; infer engagement_rate if provided
        if overall.get("engagement_rate") is not None:
            try:
                metric.engagement_rate = float(overall.get("engagement_rate", 0))
            except Exception:
                metric.engagement_rate = 0.0
        # Reach/impressions
        metric.reach = int(overall.get("reach", overall.get("estimated_reach", metric.reach or 0)) or 0)
        metric.impressions = int(overall.get("impressions", metric.impressions or 0) or 0)
        
        # Platform breakdown → flatten into platform_distribution using 'posts' or 'mentions'
        if platform_breakdown:
            distribution: Dict[str, int] = {}
            for item in platform_breakdown:
                try:
                    plat = str(item.get("platform") or item.get("name") or "").lower()
                    if plat:
                        distribution[plat] = int(item.get("posts") or item.get("mentions") or item.get("count") or 0)
                except Exception:
                    continue
            if distribution:
                metric.platform_distribution = distribution
    
    if latest_metric:
        apply_to_metric(latest_metric)
        await latest_metric.save()
        return {"campaign_id": str(campaign.id), "updated": 1}
    else:
        metric = CampaignMetrics(
            campaign=campaign,
            brand=brand,
            metric_date=datetime.now(),
        )
        apply_to_metric(metric)
        await metric.insert()
        return {"campaign_id": str(campaign.id), "inserted": 1}

