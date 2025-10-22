from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
import pytz

from app.models.database import Brand, PlatformType, CreatedFromType
from app.services.database_service import DatabaseService

# Initialize database service
db_service = DatabaseService()

router = APIRouter(prefix="/brands", tags=["Brand Management"])

# ============= REQUEST/RESPONSE SCHEMAS =============

class BrandCreate(BaseModel):
    name: str
    description: str
    keywords: List[str] = []
    platforms: List[str] = []  # List of platform names (e.g., ["tiktok", "instagram", "twitter", "youtube"])
    postUrls: List[str] = []  # Platform URLs
    category: Optional[str] = None
    industry: Optional[str] = None
    competitors: List[str] = []
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    created_from: Optional[CreatedFromType] = CreatedFromType.BRAND  # Default to 'brand' when created directly
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Tesla Motors",
                "description": "Main Tesla brand monitoring across all product lines",
                "keywords": ["tesla", "electric vehicle", "ev", "model 3", "model y"],
                "platforms": ["tiktok", "instagram", "twitter"],
                "category": "Automotive",
                "industry": "Electric Vehicles",
                "competitors": ["Ford", "Rivian", "Lucid Motors", "BMW"]
            }
        }

class BrandUpdate(BaseModel):
    description: Optional[str] = None
    keywords: Optional[List[str]] = None
    platforms: Optional[List[str]] = None
    postUrls: Optional[List[str]] = None
    category: Optional[str] = None
    industry: Optional[str] = None
    competitors: Optional[List[str]] = None
    startDate: Optional[str] = None
    endDate: Optional[str] = None

class BrandResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    keywords: List[str]
    platforms: List[str]
    postUrls: List[str]
    category: Optional[str]
    industry: Optional[str]
    competitors: List[str]
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    created_from: str  # "brand", "campaign", or "content"
    created_at: datetime
    updated_at: datetime

# ============= BRAND CRUD ENDPOINTS =============

@router.post("/", response_model=BrandResponse)
async def create_brand(brand: BrandCreate):
    """
    Create a new brand for monitoring
    
    Example:
    ```json
    {
        "name": "Tesla Motors",
        "description": "Electric vehicle manufacturer",
        "keywords": ["tesla", "ev", "electric car"],
        "category": "Automotive",
        "competitors": ["Ford", "Rivian"]
    }
    ```
    """
    try:
        # Check if brand already exists
        existing = await Brand.find_one(Brand.name == brand.name)
        if existing:
            raise HTTPException(status_code=400, detail=f"Brand '{brand.name}' already exists")
        
        # Convert platform strings to PlatformType enums
        platform_enums = []
        for platform_str in brand.platforms:
            try:
                platform_enum = PlatformType(platform_str.lower())
                platform_enums.append(platform_enum)
            except ValueError:
                # Skip invalid platform names
                continue
        
        # Create brand
        brand_doc = Brand(
            name=brand.name,
            keywords=brand.keywords,
            platforms=platform_enums,
            postUrls=brand.postUrls,
            competitors=brand.competitors,
            startDate=brand.startDate,
            endDate=brand.endDate,
            description=brand.description,
            industry=brand.industry,
            created_from=brand.created_from,
            created_at=datetime.now(pytz.UTC),
            updated_at=datetime.now(pytz.UTC)
        )
        
        await brand_doc.insert()
        
        return BrandResponse(
            id=str(brand_doc.id),
            name=brand_doc.name,
            description=brand_doc.description,
            keywords=brand_doc.keywords,
            platforms=[p.value for p in brand_doc.platforms],
            postUrls=brand_doc.postUrls,
            category=brand.category,
            industry=brand_doc.industry,
            competitors=brand_doc.competitors,
            startDate=brand_doc.startDate,
            endDate=brand_doc.endDate,
            created_from=brand_doc.created_from.value,
            created_at=brand_doc.created_at,
            updated_at=brand_doc.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[BrandResponse])
async def list_brands(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    created_from: Optional[CreatedFromType] = CreatedFromType.BRAND,  # Default to 'brand'
    include_all: bool = False  # Set true to get all brands regardless of created_from
):
    """
    List all brands with optional filtering
    
    By default, only returns brands created directly (created_from='brand').
    Use include_all=true to get all brands regardless of source.
    Use created_from parameter to filter by specific source (brand/campaign/content).
    """
    try:
        # Build query filters
        filters = []
        
        if category:
            filters.append(Brand.industry == category)
        
        # Only apply created_from filter if include_all is False
        if not include_all and created_from:
            filters.append(Brand.created_from == created_from.value)
        
        # Apply filters
        if filters:
            brands = await Brand.find(*filters).skip(skip).limit(limit).to_list()
        else:
            brands = await Brand.find().skip(skip).limit(limit).to_list()
        
        return [
            BrandResponse(
                id=str(b.id),
                name=b.name,
                description=b.description,
                keywords=b.keywords,
                platforms=[p.value for p in b.platforms],
                postUrls=b.postUrls,
                category=b.industry,
                industry=b.industry,
                competitors=b.competitors,
                startDate=b.startDate,
                endDate=b.endDate,
                created_from=b.created_from.value,
                created_at=b.created_at,
                updated_at=b.updated_at
            )
            for b in brands
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{brand_name}", response_model=BrandResponse)
async def get_brand(brand_name: str):
    """
    Get brand details by name
    """
    try:
        brand = await Brand.find_one(Brand.name == brand_name)
        if not brand:
            raise HTTPException(status_code=404, detail="Brand not found")
        
        return BrandResponse(
            id=str(brand.id),
            name=brand.name,
            description=brand.description,
            keywords=brand.keywords,
            platforms=[p.value for p in brand.platforms],
            postUrls=brand.postUrls,
            category=brand.industry,
            industry=brand.industry,
            competitors=brand.competitors,
            startDate=brand.startDate,
            endDate=brand.endDate,
            created_from=brand.created_from.value,
            created_at=brand.created_at,
            updated_at=brand.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{brand_identifier}", response_model=BrandResponse)
async def update_brand(brand_identifier: str, update: BrandUpdate):
    """
    Update brand details by name or ID
    """
    try:
        brand = None
        
        # Try to find by ObjectID first
        try:
            from bson import ObjectId
            if ObjectId.is_valid(brand_identifier):
                brand = await Brand.find_one(Brand.id == ObjectId(brand_identifier))
        except:
            pass
        
        # If not found by ObjectID, try by name
        if not brand:
            brand = await Brand.find_one(Brand.name == brand_identifier)
        
        if not brand:
            raise HTTPException(status_code=404, detail="Brand not found")
        
        # Update fields
        if update.description is not None:
            brand.description = update.description
        if update.keywords is not None:
            brand.keywords = update.keywords
        if update.platforms is not None:
            # Convert platform strings to PlatformType enums
            platform_enums = []
            for platform_str in update.platforms:
                try:
                    platform_enum = PlatformType(platform_str.lower())
                    platform_enums.append(platform_enum)
                except ValueError:
                    # Skip invalid platform names
                    continue
            brand.platforms = platform_enums
        if update.postUrls is not None:
            brand.postUrls = update.postUrls
        if update.industry is not None:
            brand.industry = update.industry
        if update.competitors is not None:
            brand.competitors = update.competitors
        if update.startDate is not None:
            brand.startDate = update.startDate
        if update.endDate is not None:
            brand.endDate = update.endDate
        
        brand.updated_at = datetime.now(pytz.UTC)
        await brand.save()
        
        return BrandResponse(
            id=str(brand.id),
            name=brand.name,
            description=brand.description,
            keywords=brand.keywords,
            platforms=[p.value for p in brand.platforms],
            postUrls=brand.postUrls,
            category=brand.industry,
            industry=brand.industry,
            competitors=brand.competitors,
            startDate=brand.startDate,
            endDate=brand.endDate,
            created_from=brand.created_from.value,
            created_at=brand.created_at,
            updated_at=brand.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{brand_identifier}")
async def delete_brand(brand_identifier: str):
    """
    Delete a brand by ObjectID or brand name
    """
    try:
        # Try to find brand by ObjectID first, then by name
        from bson import ObjectId
        brand = None
        
        try:
            # Try ObjectID first
            brand = await Brand.find_one(Brand.id == ObjectId(brand_identifier))
        except:
            # If ObjectID fails, try by name
            brand = await Brand.find_one(Brand.name == brand_identifier)
        
        if not brand:
            raise HTTPException(status_code=404, detail="Brand not found")
        
        await brand.delete()
        
        return {"message": f"Brand '{brand.name}' deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============= BRAND ANALYTICS ENDPOINTS =============

@router.get("/{brand_name}/competitors/analysis")
async def get_competitive_analysis(brand_name: str):
    """
    Get competitive analysis for a brand
    
    Compares brand mention share and sentiment with competitors
    """
    try:
        # Get brand by name
        brand = await Brand.find_one(Brand.name == brand_name)
        if not brand:
            raise HTTPException(status_code=404, detail="Brand not found")
        
        # Get brand posts for analysis
        brand_posts = await db_service.get_posts_by_brand(brand, limit=1000)
        
        # Calculate real competitive insights
        total_mentions = len(brand_posts)
        total_engagement = sum(p.like_count + p.comment_count + p.share_count for p in brand_posts)
        avg_sentiment = sum(p.sentiment for p in brand_posts if p.sentiment is not None) / len([p for p in brand_posts if p.sentiment is not None]) if brand_posts else 0
        
        # Get competitor data if available
        competitive_insights = []
        if brand.competitors:
            for competitor in brand.competitors[:3]:  # Top 3 competitors
                # Find competitor brand
                competitor_brand = await Brand.find_one(Brand.name == competitor)
                if competitor_brand:
                    competitor_posts = await db_service.get_posts_by_brand(competitor_brand, limit=500)
                    if competitor_posts:
                        competitor_mentions = len(competitor_posts)
                        competitor_engagement = sum(p.like_count + p.comment_count + p.share_count for p in competitor_posts)
                        competitor_sentiment = sum(p.sentiment for p in competitor_posts if p.sentiment is not None) / len([p for p in competitor_posts if p.sentiment is not None]) if competitor_posts else 0
                        
                        mention_share = competitor_mentions / (total_mentions + competitor_mentions) if (total_mentions + competitor_mentions) > 0 else 0
                        sentiment_comparison = competitor_sentiment - avg_sentiment
                        
                        competitive_insights.append({
                            "competitor": competitor,
                            "mention_share": round(mention_share, 3),
                            "sentiment_comparison": round(sentiment_comparison, 3),
                            "key_differences": ["Engagement rate", "Content quality", "Audience reach"]
                        })
        
        # Determine market position based on real metrics
        market_position = "leader" if avg_sentiment > 0.1 and total_engagement > 1000 else "follower"
        sentiment_advantage = max(0, avg_sentiment) if avg_sentiment > 0 else 0
        
        return {
            "brand": brand_name,
            "competitive_insights": competitive_insights,
            "market_position": market_position,
            "sentiment_advantage": round(sentiment_advantage, 3)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


