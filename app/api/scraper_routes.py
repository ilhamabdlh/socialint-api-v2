from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from app.services.scraper_service import scraper_service
from app.services.analysis_service_v2 import AnalysisServiceV2
from app.services.database_service import db_service
from app.models.database import Brand, PlatformType

router = APIRouter(prefix="/scrape", tags=["Scraping"])

# ============= REQUEST/RESPONSE SCHEMAS =============

class ScrapeRequest(BaseModel):
    brand_name: str
    keywords: List[str]
    platforms: List[str]
    max_posts_per_platform: int = Field(default=100, ge=10, le=1000)
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    auto_analyze: bool = Field(default=True, description="Automatically analyze after scraping")
    
    class Config:
        json_schema_extra = {
            "example": {
                "brand_name": "hufagripp",
                "keywords": ["hufagrip", "hufagripp", "obat batuk"],
                "platforms": ["tiktok", "instagram"],
                "max_posts_per_platform": 100,
                "start_date": "2025-01-01",
                "end_date": "2025-10-10",
                "auto_analyze": True
            }
        }

class ScrapeResponse(BaseModel):
    message: str
    brand_name: str
    platforms_scraped: List[str]
    total_posts_scraped: int
    posts_by_platform: dict
    analysis_triggered: bool
    timestamp: datetime

# ============= SCRAPING ENDPOINTS =============

@router.post("/", response_model=ScrapeResponse)
async def scrape_and_analyze(request: ScrapeRequest):
    """
    Scrape social media platforms using Apify and optionally analyze the data
    
    This endpoint:
    1. Scrapes data from specified platforms using Apify
    2. Optionally runs sentiment, topic, emotions, and demographics analysis
    3. Saves everything to MongoDB
    
    Requires: Apify API token configured in settings
    """
    try:
        # Check if Apify is configured
        if not scraper_service.client:
            raise HTTPException(
                status_code=503,
                detail="Apify scraper not configured. Please add APIFY_API_TOKEN to .env or settings"
            )
        
        # Get or create brand
        brand = await db_service.get_or_create_brand(
            name=request.brand_name,
            keywords=request.keywords
        )
        
        print(f"\n{'='*80}")
        print(f"🔍 SCRAPING REQUEST")
        print(f"{'='*80}")
        print(f"Brand: {request.brand_name}")
        print(f"Keywords: {request.keywords}")
        print(f"Platforms: {request.platforms}")
        print(f"Max posts per platform: {request.max_posts_per_platform}")
        print(f"{'='*80}\n")
        
        # Scrape all platforms
        scraped_data = scraper_service.scrape_multiple_platforms(
            platforms=request.platforms,
            keywords=request.keywords,
            max_posts_per_platform=request.max_posts_per_platform,
            start_date=request.start_date,
            end_date=request.end_date
        )
        
        # Count total posts
        total_posts = sum(len(df) for df in scraped_data.values() if not df.empty)
        posts_by_platform = {
            platform: len(df) for platform, df in scraped_data.items()
        }
        
        analysis_triggered = False
        analysis_errors = []
        
        # Optionally analyze the data
        if request.auto_analyze and total_posts > 0:
            print(f"\n{'='*80}")
            print(f"🤖 AUTO-ANALYZING SCRAPED DATA")
            print(f"{'='*80}\n")
            
            analysis_service = AnalysisServiceV2()
            
            for platform, df in scraped_data.items():
                if df.empty:
                    continue
                
                try:
                    platform_type = PlatformType(platform.lower())
                    
                    print(f"📊 Analyzing {len(df)} posts from {platform}...")
                    
                    # Run analysis pipeline with DataFrame
                    result = await analysis_service.process_platform_dataframe(
                        df=df,
                        platform=platform,
                        brand_name=request.brand_name,
                        keywords=request.keywords,
                        layer=1,
                        save_to_db=True
                    )
                    
                    analysis_triggered = True
                    print(f"✅ Analysis completed for {platform}")
                    print(f"   Total analyzed: {result.total_analyzed}")
                    print(f"   Sentiment: {result.sentiment_distribution}")
                    print(f"   Topics: {len(result.topics_found)} found")
                    
                except Exception as e:
                    error_msg = f"Failed to analyze {platform}: {str(e)}"
                    print(f"❌ {error_msg}")
                    import traceback
                    print(traceback.format_exc())
                    analysis_errors.append(error_msg)
        
        return ScrapeResponse(
            message="Scraping completed successfully",
            brand_name=request.brand_name,
            platforms_scraped=list(scraped_data.keys()),
            total_posts_scraped=total_posts,
            posts_by_platform=posts_by_platform,
            analysis_triggered=analysis_triggered,
            timestamp=datetime.now()
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")

@router.post("/single-platform")
async def scrape_single_platform(
    brand_name: str,
    platform: str,
    keywords: List[str] = Query(..., description="Search keywords"),
    max_posts: int = Query(default=100, ge=10, le=1000),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    auto_analyze: bool = True
):
    """
    Scrape a single platform
    
    Simpler endpoint for scraping just one platform at a time
    """
    try:
        # Check if Apify is configured
        if not scraper_service.client:
            raise HTTPException(
                status_code=503,
                detail="Apify scraper not configured. Please add APIFY_API_TOKEN to .env or settings"
            )
        
        # Get or create brand
        brand = await db_service.get_brand(brand_name)
        if not brand:
            brand = await db_service.create_brand(
                name=brand_name,
                keywords=keywords
            )
        
        print(f"\n{'='*80}")
        print(f"🔍 SCRAPING {platform.upper()}")
        print(f"{'='*80}")
        print(f"Brand: {brand_name}")
        print(f"Keywords: {keywords}")
        print(f"Max posts: {max_posts}")
        print(f"{'='*80}\n")
        
        # Scrape platform
        df = scraper_service.scrape_platform(
            platform=platform,
            keywords=keywords,
            max_posts=max_posts,
            start_date=start_date,
            end_date=end_date
        )
        
        total_posts = len(df)
        analysis_triggered = False
        
        # Optionally analyze
        if auto_analyze and total_posts > 0:
            print(f"\n🤖 Auto-analyzing {total_posts} posts...")
            
            analysis_service = AnalysisServiceV2()
            platform_type = PlatformType(platform.lower())
            
            await analysis_service.process_platform(
                brand_name=brand_name,
                platform=platform_type,
                df=df,
                keywords=keywords
            )
            
            analysis_triggered = True
        
        return {
            "message": "Scraping completed",
            "brand_name": brand_name,
            "platform": platform,
            "posts_scraped": total_posts,
            "analysis_triggered": analysis_triggered,
            "timestamp": datetime.now()
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")

@router.get("/supported-platforms")
async def get_supported_scrapers():
    """
    Get list of platforms that can be scraped via Apify
    """
    return {
        "supported_platforms": [
            {
                "name": "tiktok",
                "scraper": "clockworks/tiktok-scraper",
                "features": ["hashtag search", "user posts"]
            },
            {
                "name": "instagram",
                "scraper": "apify/instagram-scraper",
                "features": ["hashtag search", "user posts", "locations"]
            },
            {
                "name": "twitter",
                "scraper": "apify/twitter-scraper",
                "features": ["keyword search", "user timeline", "date filters"]
            },
            {
                "name": "youtube",
                "scraper": "bernardo/youtube-scraper",
                "features": ["keyword search", "channel videos"]
            }
        ],
        "note": "Requires Apify API token. Get yours at https://apify.com"
    }


