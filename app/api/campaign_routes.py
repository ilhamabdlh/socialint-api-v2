from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import pytz

from app.models.database import (
    Campaign, 
    CampaignMetrics, 
    Brand, 
    PostURL,
    CampaignStatus,
    CampaignType,
    PlatformType
)

router = APIRouter(prefix="/campaigns", tags=["Campaign Management"])

# ============= REQUEST/RESPONSE SCHEMAS =============

class PostURLCreate(BaseModel):
    url: str
    platform: PlatformType
    title: Optional[str] = None
    description: Optional[str] = None

class CampaignCreate(BaseModel):
    campaign_name: str
    description: str
    campaign_type: CampaignType
    brand_name: str
    
    # Configuration
    keywords: List[str] = []
    target_audiences: List[str] = []
    platforms: List[PlatformType] = []
    post_urls: List[PostURLCreate] = []
    
    # Timeline
    start_date: datetime
    end_date: datetime
    
    # Auto-analysis
    auto_analysis_enabled: bool = True
    analysis_frequency: str = "daily"
    
    # Tags
    tags: List[str] = []
    
    # Metadata
    created_by: Optional[str] = None
    team: Optional[str] = None
    notes: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "campaign_name": "Cybertruck Launch Campaign",
                "description": "Comprehensive campaign tracking the public reception of Tesla Cybertruck launch",
                "campaign_type": "product_launch",
                "brand_name": "tesla",
                "keywords": ["cybertruck", "tesla truck", "electric truck"],
                "target_audiences": ["Tech Enthusiasts", "Truck Owners", "EV Adopters"],
                "platforms": ["twitter", "youtube", "reddit", "instagram"],
                "post_urls": [
                    {
                        "url": "https://twitter.com/tesla/status/1234567890",
                        "platform": "twitter",
                        "title": "Cybertruck Official Launch Tweet"
                    }
                ],
                "start_date": "2025-01-15T00:00:00Z",
                "end_date": "2025-02-28T23:59:59Z",
                "auto_analysis_enabled": True,
                "tags": ["product launch", "active"],
                "created_by": "marketing_team"
            }
        }

class CampaignUpdate(BaseModel):
    description: Optional[str] = None
    campaign_type: Optional[CampaignType] = None
    status: Optional[CampaignStatus] = None
    keywords: Optional[List[str]] = None
    target_audiences: Optional[List[str]] = None
    platforms: Optional[List[PlatformType]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    auto_analysis_enabled: Optional[bool] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None

class CampaignResponse(BaseModel):
    id: str
    campaign_name: str
    description: str
    campaign_type: str
    status: str
    brand_name: str
    
    keywords: List[str]
    target_audiences: List[str]
    platforms: List[str]
    post_urls_count: int
    
    start_date: datetime
    end_date: datetime
    
    # Metrics
    total_mentions: int
    overall_sentiment: float
    engagement_rate: float
    reach: int
    
    # Trends
    sentiment_trend: float
    mentions_trend: float
    engagement_trend: float
    
    tags: List[str]
    
    created_at: datetime
    updated_at: datetime
    last_analysis_at: Optional[datetime]

class CampaignMetricsResponse(BaseModel):
    metric_date: datetime
    sentiment_score: float
    total_mentions: int
    positive_count: int
    negative_count: int
    neutral_count: int
    total_likes: int
    total_comments: int
    total_shares: int
    engagement_rate: float
    reach: int

# ============= CAMPAIGN MANAGEMENT ENDPOINTS =============

@router.post("/", response_model=CampaignResponse)
async def create_campaign(campaign: CampaignCreate):
    """
    Create a new marketing campaign
    
    Creates a campaign with specified parameters and sets up automatic
    daily analysis if enabled.
    """
    try:
        # Get or create brand
        brand = await Brand.find_one(Brand.name == campaign.brand_name)
        if not brand:
            brand = Brand(name=campaign.brand_name, keywords=campaign.keywords)
            await brand.insert()
        
        # Create post URLs
        post_url_docs = []
        for url_data in campaign.post_urls:
            post_url = PostURL(
                url=url_data.url,
                platform=url_data.platform,
                title=url_data.title,
                description=url_data.description
            )
            await post_url.insert()
            post_url_docs.append(post_url)
        
        # Calculate next analysis time
        next_analysis = None
        if campaign.auto_analysis_enabled:
            # Schedule for tomorrow at 00:00 UTC if start_date is in the past
            now = datetime.now(pytz.UTC)
            if campaign.start_date <= now:
                next_analysis = (now + timedelta(days=1)).replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
            else:
                next_analysis = campaign.start_date
        
        # Create campaign
        campaign_doc = Campaign(
            campaign_name=campaign.campaign_name,
            description=campaign.description,
            campaign_type=campaign.campaign_type,
            status=CampaignStatus.ACTIVE if campaign.start_date <= datetime.now(pytz.UTC) else CampaignStatus.DRAFT,
            brand=brand,
            keywords=campaign.keywords,
            target_audiences=campaign.target_audiences,
            platforms=campaign.platforms,
            post_urls=post_url_docs,
            start_date=campaign.start_date,
            end_date=campaign.end_date,
            auto_analysis_enabled=campaign.auto_analysis_enabled,
            analysis_frequency=campaign.analysis_frequency,
            next_analysis_at=next_analysis,
            tags=campaign.tags,
            created_by=campaign.created_by,
            team=campaign.team,
            notes=campaign.notes
        )
        
        await campaign_doc.insert()
        
        return CampaignResponse(
            id=str(campaign_doc.id),
            campaign_name=campaign_doc.campaign_name,
            description=campaign_doc.description,
            campaign_type=campaign_doc.campaign_type.value,
            status=campaign_doc.status.value,
            brand_name=brand.name,
            keywords=campaign_doc.keywords,
            target_audiences=campaign_doc.target_audiences,
            platforms=[p.value for p in campaign_doc.platforms],
            post_urls_count=len(campaign_doc.post_urls),
            start_date=campaign_doc.start_date,
            end_date=campaign_doc.end_date,
            total_mentions=campaign_doc.total_mentions,
            overall_sentiment=campaign_doc.overall_sentiment,
            engagement_rate=campaign_doc.engagement_rate,
            reach=campaign_doc.reach,
            sentiment_trend=campaign_doc.sentiment_trend,
            mentions_trend=campaign_doc.mentions_trend,
            engagement_trend=campaign_doc.engagement_trend,
            tags=campaign_doc.tags,
            created_at=campaign_doc.created_at,
            updated_at=campaign_doc.updated_at,
            last_analysis_at=campaign_doc.last_analysis_at
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[CampaignResponse])
async def list_campaigns(
    status: Optional[CampaignStatus] = None,
    brand_name: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
):
    """
    List all campaigns with optional filtering
    """
    try:
        query = {}
        
        if status:
            query['status'] = status
        
        if brand_name:
            brand = await Brand.find_one(Brand.name == brand_name)
            if brand:
                campaigns = await Campaign.find(
                    Campaign.brand.id == brand.id,
                    *[getattr(Campaign, k) == v for k, v in query.items()]
                ).skip(skip).limit(limit).to_list()
            else:
                campaigns = []
        else:
            campaigns = await Campaign.find(
                *[getattr(Campaign, k) == v for k, v in query.items()]
            ).skip(skip).limit(limit).to_list()
        
        response = []
        for campaign in campaigns:
            brand = await campaign.brand.fetch()
            response.append(CampaignResponse(
                id=str(campaign.id),
                campaign_name=campaign.campaign_name,
                description=campaign.description,
                campaign_type=campaign.campaign_type.value,
                status=campaign.status.value,
                brand_name=brand.name,
                keywords=campaign.keywords,
                target_audiences=campaign.target_audiences,
                platforms=[p.value for p in campaign.platforms],
                post_urls_count=len(campaign.post_urls),
                start_date=campaign.start_date,
                end_date=campaign.end_date,
                total_mentions=campaign.total_mentions,
                overall_sentiment=campaign.overall_sentiment,
                engagement_rate=campaign.engagement_rate,
                reach=campaign.reach,
                sentiment_trend=campaign.sentiment_trend,
                mentions_trend=campaign.mentions_trend,
                engagement_trend=campaign.engagement_trend,
                tags=campaign.tags,
                created_at=campaign.created_at,
                updated_at=campaign.updated_at,
                last_analysis_at=campaign.last_analysis_at
            ))
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{campaign_name}", response_model=CampaignResponse)
async def get_campaign(campaign_name: str):
    """
    Get campaign details by name
    """
    try:
        campaign = await Campaign.find_one(Campaign.campaign_name == campaign_name)
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        brand = await campaign.brand.fetch()
        
        return CampaignResponse(
            id=str(campaign.id),
            campaign_name=campaign.campaign_name,
            description=campaign.description,
            campaign_type=campaign.campaign_type.value,
            status=campaign.status.value,
            brand_name=brand.name,
            keywords=campaign.keywords,
            target_audiences=campaign.target_audiences,
            platforms=[p.value for p in campaign.platforms],
            post_urls_count=len(campaign.post_urls),
            start_date=campaign.start_date,
            end_date=campaign.end_date,
            total_mentions=campaign.total_mentions,
            overall_sentiment=campaign.overall_sentiment,
            engagement_rate=campaign.engagement_rate,
            reach=campaign.reach,
            sentiment_trend=campaign.sentiment_trend,
            mentions_trend=campaign.mentions_trend,
            engagement_trend=campaign.engagement_trend,
            tags=campaign.tags,
            created_at=campaign.created_at,
            updated_at=campaign.updated_at,
            last_analysis_at=campaign.last_analysis_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{campaign_name}", response_model=CampaignResponse)
async def update_campaign(campaign_name: str, update: CampaignUpdate):
    """
    Update campaign details
    """
    try:
        campaign = await Campaign.find_one(Campaign.campaign_name == campaign_name)
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        # Update fields
        if update.description is not None:
            campaign.description = update.description
        if update.campaign_type is not None:
            campaign.campaign_type = update.campaign_type
        if update.status is not None:
            campaign.status = update.status
        if update.keywords is not None:
            campaign.keywords = update.keywords
        if update.target_audiences is not None:
            campaign.target_audiences = update.target_audiences
        if update.platforms is not None:
            campaign.platforms = update.platforms
        if update.start_date is not None:
            campaign.start_date = update.start_date
        if update.end_date is not None:
            campaign.end_date = update.end_date
        if update.auto_analysis_enabled is not None:
            campaign.auto_analysis_enabled = update.auto_analysis_enabled
        if update.tags is not None:
            campaign.tags = update.tags
        if update.notes is not None:
            campaign.notes = update.notes
        
        campaign.updated_at = datetime.now(pytz.UTC)
        await campaign.save()
        
        brand = await campaign.brand.fetch()
        
        return CampaignResponse(
            id=str(campaign.id),
            campaign_name=campaign.campaign_name,
            description=campaign.description,
            campaign_type=campaign.campaign_type.value,
            status=campaign.status.value,
            brand_name=brand.name,
            keywords=campaign.keywords,
            target_audiences=campaign.target_audiences,
            platforms=[p.value for p in campaign.platforms],
            post_urls_count=len(campaign.post_urls),
            start_date=campaign.start_date,
            end_date=campaign.end_date,
            total_mentions=campaign.total_mentions,
            overall_sentiment=campaign.overall_sentiment,
            engagement_rate=campaign.engagement_rate,
            reach=campaign.reach,
            sentiment_trend=campaign.sentiment_trend,
            mentions_trend=campaign.mentions_trend,
            engagement_trend=campaign.engagement_trend,
            tags=campaign.tags,
            created_at=campaign.created_at,
            updated_at=campaign.updated_at,
            last_analysis_at=campaign.last_analysis_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{campaign_name}")
async def delete_campaign(campaign_name: str):
    """
    Delete a campaign (soft delete by archiving)
    """
    try:
        campaign = await Campaign.find_one(Campaign.campaign_name == campaign_name)
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        # Soft delete by archiving
        campaign.status = CampaignStatus.ARCHIVED
        campaign.auto_analysis_enabled = False
        campaign.updated_at = datetime.now(pytz.UTC)
        await campaign.save()
        
        return {"message": f"Campaign '{campaign_name}' archived successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============= CAMPAIGN ANALYTICS ENDPOINTS =============

@router.get("/{campaign_name}/metrics", response_model=List[CampaignMetricsResponse])
async def get_campaign_metrics(
    campaign_name: str,
    days: int = Query(default=30, description="Number of days to retrieve")
):
    """
    Get time-series metrics for a campaign
    
    Returns daily metrics for visualization in dashboard charts.
    """
    try:
        campaign = await Campaign.find_one(Campaign.campaign_name == campaign_name)
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        # Get metrics from last N days
        start_date = datetime.now(pytz.UTC) - timedelta(days=days)
        
        metrics = await CampaignMetrics.find(
            CampaignMetrics.campaign.id == campaign.id,
            CampaignMetrics.metric_date >= start_date
        ).sort("-metric_date").to_list()
        
        return [
            CampaignMetricsResponse(
                metric_date=m.metric_date,
                sentiment_score=m.sentiment_score,
                total_mentions=m.total_mentions,
                positive_count=m.positive_count,
                negative_count=m.negative_count,
                neutral_count=m.neutral_count,
                total_likes=m.total_likes,
                total_comments=m.total_comments,
                total_shares=m.total_shares,
                engagement_rate=m.engagement_rate,
                reach=m.reach
            )
            for m in metrics
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{campaign_name}/trigger-analysis")
async def trigger_campaign_analysis(campaign_name: str, background_tasks: BackgroundTasks):
    """
    Manually trigger analysis for a campaign
    
    Useful for testing or forcing immediate analysis outside the scheduler.
    """
    import asyncio
    
    try:
        campaign = await Campaign.find_one(Campaign.campaign_name == campaign_name)
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        # Only allow analysis for campaigns with active, paused, or draft status
        if campaign.status not in [CampaignStatus.ACTIVE, CampaignStatus.PAUSED, CampaignStatus.DRAFT]:
            raise HTTPException(
                status_code=400, 
                detail=f"Campaign status '{campaign.status.value}' does not allow analysis. Only active, paused, or draft campaigns can be analyzed."
            )
        
        # Auto-update campaign status to active if it was paused or draft
        if campaign.status in [CampaignStatus.PAUSED, CampaignStatus.DRAFT]:
            campaign.status = CampaignStatus.ACTIVE
            campaign.updated_at = datetime.now(pytz.UTC)
            await campaign.save()
            print(f"Campaign '{campaign.campaign_name}' status updated to ACTIVE for analysis.")
        
        # Run analysis process in background using FastAPI BackgroundTasks
        async def run_background_analysis():
            try:
                from app.services.campaign_service import CampaignService
                service = CampaignService()
                result = await service.analyze_campaign(campaign)
                print(f"✅ Background analysis completed for campaign '{campaign_name}'")
                return result
            except Exception as e:
                print(f"❌ Background analysis failed for campaign '{campaign_name}': {str(e)}")
                # Update campaign status to paused if analysis fails
                try:
                    campaign.status = CampaignStatus.PAUSED
                    await campaign.save()
                except:
                    pass
                raise e
        
        # Execute background task using FastAPI BackgroundTasks
        background_tasks.add_task(run_background_analysis)
        
        return {
            "message": "Analysis triggered successfully in the background",
            "campaign_name": campaign_name,
            "status": campaign.status.value,
            "note": "The analysis is now running in the background. You will be notified when it's complete."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{campaign_name}/active-campaigns")
async def get_active_campaigns():
    """
    Get all campaigns that should be analyzed today
    
    Returns campaigns where:
    - status = ACTIVE
    - start_date <= today <= end_date
    - auto_analysis_enabled = True
    """
    try:
        now = datetime.now(pytz.UTC)
        
        campaigns = await Campaign.find(
            Campaign.status == CampaignStatus.ACTIVE,
            Campaign.start_date <= now,
            Campaign.end_date >= now,
            Campaign.auto_analysis_enabled == True
        ).to_list()
        
        result = []
        for campaign in campaigns:
            brand = await campaign.brand.fetch()
            result.append({
                "campaign_name": campaign.campaign_name,
                "brand_name": brand.name,
                "start_date": campaign.start_date,
                "end_date": campaign.end_date,
                "last_analysis_at": campaign.last_analysis_at,
                "next_analysis_at": campaign.next_analysis_at
            })
        
        return {
            "count": len(result),
            "campaigns": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

