from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
import pytz

from app.models.database import Brand, PlatformType

router = APIRouter(prefix="/brands", tags=["Brand Management"])

# ============= REQUEST/RESPONSE SCHEMAS =============

class BrandCreate(BaseModel):
    name: str
    description: str
    keywords: List[str] = []
    category: Optional[str] = None
    industry: Optional[str] = None
    competitors: List[str] = []
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Tesla Motors",
                "description": "Main Tesla brand monitoring across all product lines",
                "keywords": ["tesla", "electric vehicle", "ev", "model 3", "model y"],
                "category": "Automotive",
                "industry": "Electric Vehicles",
                "competitors": ["Ford", "Rivian", "Lucid Motors", "BMW"]
            }
        }

class BrandUpdate(BaseModel):
    description: Optional[str] = None
    keywords: Optional[List[str]] = None
    category: Optional[str] = None
    industry: Optional[str] = None
    competitors: Optional[List[str]] = None

class BrandResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    keywords: List[str]
    category: Optional[str]
    industry: Optional[str]
    competitors: List[str]
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
        
        # Create brand
        brand_doc = Brand(
            name=brand.name,
            keywords=brand.keywords,
            description=brand.description,
            industry=brand.industry,
            created_at=datetime.now(pytz.UTC),
            updated_at=datetime.now(pytz.UTC)
        )
        
        await brand_doc.insert()
        
        return BrandResponse(
            id=str(brand_doc.id),
            name=brand_doc.name,
            description=brand_doc.description,
            keywords=brand_doc.keywords,
            category=brand.category,
            industry=brand_doc.industry,
            competitors=brand.competitors,
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
    category: Optional[str] = None
):
    """
    List all brands with optional filtering
    """
    try:
        query = {}
        if category:
            query['industry'] = category
        
        brands = await Brand.find().skip(skip).limit(limit).to_list()
        
        return [
            BrandResponse(
                id=str(b.id),
                name=b.name,
                description=b.description,
                keywords=b.keywords,
                category=b.industry,
                industry=b.industry,
                competitors=[],
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
            category=brand.industry,
            industry=brand.industry,
            competitors=[],
            created_at=brand.created_at,
            updated_at=brand.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{brand_name}", response_model=BrandResponse)
async def update_brand(brand_name: str, update: BrandUpdate):
    """
    Update brand details
    """
    try:
        brand = await Brand.find_one(Brand.name == brand_name)
        if not brand:
            raise HTTPException(status_code=404, detail="Brand not found")
        
        # Update fields
        if update.description is not None:
            brand.description = update.description
        if update.keywords is not None:
            brand.keywords = update.keywords
        if update.industry is not None:
            brand.industry = update.industry
        
        brand.updated_at = datetime.now(pytz.UTC)
        await brand.save()
        
        return BrandResponse(
            id=str(brand.id),
            name=brand.name,
            description=brand.description,
            keywords=brand.keywords,
            category=brand.industry,
            industry=brand.industry,
            competitors=update.competitors or [],
            created_at=brand.created_at,
            updated_at=brand.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{brand_name}")
async def delete_brand(brand_name: str):
    """
    Delete a brand
    """
    try:
        brand = await Brand.find_one(Brand.name == brand_name)
        if not brand:
            raise HTTPException(status_code=404, detail="Brand not found")
        
        await brand.delete()
        
        return {"message": f"Brand '{brand_name}' deleted successfully"}
        
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
        brand = await Brand.find_one(Brand.name == brand_name)
        if not brand:
            raise HTTPException(status_code=404, detail="Brand not found")
        
        # TODO: Implement actual competitive analysis
        # For now, return mock structure
        
        return {
            "brand": brand_name,
            "competitive_insights": [
                {
                    "competitor": "Competitor 1",
                    "mention_share": 0.35,
                    "sentiment_comparison": -0.15,
                    "key_differences": ["Price point", "Availability", "Brand trust"]
                }
            ],
            "market_position": "leader",
            "sentiment_advantage": 0.12
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


