from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File
from typing import Dict, Any, List
import os
from pathlib import Path

from app.models.schemas import (
    BrandAnalysisRequest,
    BrandAnalysisResponse,
    PlatformAnalysisResponse,
    DataUploadRequest
)

from app.services.analysis_service import AnalysisService
from app.services.analysis_service_v2 import analysis_service_v2
from app.utils.data_helpers import calculate_sentiment_distribution
from pydantic import BaseModel

router = APIRouter()
analysis_service = AnalysisService()

# New request models
class BrandBatchRequest(BaseModel):
    brands: List[Dict[str, Any]]
    
    class Config:
        json_schema_extra = {
            "example": {
                "brands": [
                    {
                        "brand_name": "hufagripp",
                        "keywords": ["hufagrip", "hufagripp"],
                        "platforms_data": {
                            "tiktok": "dataset_tiktok-scraper_hufagripp.json"
                        }
                    }
                ]
            }
        }

@router.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Social Intelligence API v2.0 - MongoDB Required",
        "status": "running",
        "version": "2.0.0"
    }

@router.get("/platforms")
async def get_supported_platforms():
    """Get list of supported platforms"""
    from app.config.settings import settings
    return {
        "platforms": settings.supported_platforms
    }

@router.post("/upload/data")
async def upload_data(
    platform: str,
    brand_name: str,
    file: UploadFile = File(...)
):
    """
    Upload data file for analysis
    Accepts CSV, JSON, or Excel files
    """
    try:
        # Validate file type
        allowed_extensions = ['.csv', '.json', '.xlsx', '.xls']
        file_ext = Path(file.filename).suffix
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Allowed: {allowed_extensions}"
            )
        
        # Save file
        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)
        
        file_path = upload_dir / f"{platform}_{brand_name}_{file.filename}"
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        return {
            "message": "File uploaded successfully",
            "file_path": str(file_path),
            "platform": platform,
            "brand_name": brand_name
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============= ANALYSIS ENDPOINTS (All save to MongoDB) =============

class PlatformAnalysisRequest(BaseModel):
    platform: str
    brand_name: str
    file_path: str
    keywords: List[str]
    
    class Config:
        json_schema_extra = {
            "example": {
                "platform": "tiktok",
                "brand_name": "hufagripp",
                "file_path": "dataset_tiktok-scraper_hufagripp.json",
                "keywords": ["hufagrip", "hufagripp"]
            }
        }

@router.post("/analyze/platform")
async def analyze_platform(request: PlatformAnalysisRequest):
    """
    Analyze single platform and save to MongoDB
    Also generates CSV file as backup
    
    Example:
    ```json
    {
        "platform": "tiktok",
        "brand_name": "hufagripp",
        "file_path": "dataset_tiktok-scraper_hufagripp.json",
        "keywords": ["hufagrip", "hufagripp"]
    }
    ```
    """
    try:
        if not os.path.exists(request.file_path):
            raise HTTPException(status_code=404, detail=f"File not found: {request.file_path}")
        
        result = await analysis_service_v2.process_platform(
            file_path=request.file_path,
            platform=request.platform,
            brand_name=request.brand_name,
            keywords=request.keywords,
            layer=1,
            save_to_db=True  # Always save to MongoDB
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze/brand")
async def analyze_brand(request: BrandAnalysisRequest):
    """
    Multi-platform brand analysis with MongoDB
    All results are automatically saved to MongoDB and also exported as CSV
    
    Automatically looks for files with naming convention:
    dataset_{platform}-scraper_{brand_name}.json
    
    Example:
    ```json
    {
        "brand_name": "hufagripp",
        "keywords": ["hufagrip", "hufagripp"],
        "platforms": ["tiktok"]
    }
    ```
    """
    try:
        # Build file paths
        platforms_data = {}
        for platform in request.platforms:
            file_path = f"dataset_{platform}-scraper_{request.brand_name}.json"
            
            if not os.path.exists(file_path):
                print(f"Warning: File not found for {platform}: {file_path}")
                continue
            
            platforms_data[platform] = file_path
        
        if not platforms_data:
            raise HTTPException(
                status_code=404,
                detail="No data files found for specified platforms"
            )
        
        # Process - always save to MongoDB
        results = await analysis_service_v2.process_multiple_platforms(
            platforms_data=platforms_data,
            brand_name=request.brand_name,
            keywords=request.keywords,
            save_to_db=True  # Always save to MongoDB
        )
        
        # Aggregate results
        total_posts = sum(r.total_analyzed for r in results)
        overall_sentiment = {}
        all_topics = []
        
        for result in results:
            for sentiment, count in result.sentiment_distribution.items():
                overall_sentiment[sentiment] = overall_sentiment.get(sentiment, 0) + count
            all_topics.extend(result.topics_found)
        
        from collections import Counter
        topic_counts = Counter(all_topics)
        top_topics = [topic for topic, _ in topic_counts.most_common(10)]
        
        return {
            "brand_name": request.brand_name,
            "platforms_analyzed": [r.platform for r in results],
            "total_posts": total_posts,
            "overall_sentiment": overall_sentiment,
            "top_topics": top_topics,
            "results": results,
            "saved_to_db": True,
            "message": "Analysis completed and saved to MongoDB. CSV files also generated."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze/batch")
async def analyze_brand_batch(request: BrandBatchRequest):
    """
    Process multiple brands in batch
    Implements multi-brand batch processing from diagram
    All results are automatically saved to MongoDB
    
    Example:
    ```json
    {
        "brands": [
            {
                "brand_name": "hufagripp",
                "keywords": ["hufagrip", "hufagripp"],
                "platforms_data": {
                    "tiktok": "dataset_tiktok-scraper_hufagripp.json"
                }
            },
            {
                "brand_name": "competitor1",
                "keywords": ["competitor1"],
                "platforms_data": {
                    "tiktok": "dataset_tiktok-scraper_competitor1.json"
                }
            }
        ]
    }
    ```
    """
    try:
        results = await analysis_service_v2.process_brand_batch(
            brands_config=request.brands
        )
        
        # Summary
        summary = {
            "total_brands_processed": len(results),
            "brands": {}
        }
        
        for brand_name, brand_results in results.items():
            if brand_results:
                summary["brands"][brand_name] = {
                    "platforms_analyzed": len(brand_results),
                    "total_posts": sum(r.total_analyzed for r in brand_results),
                    "sentiment_summary": {
                        k: sum(r.sentiment_distribution.get(k, 0) for r in brand_results)
                        for k in ['Positive', 'Negative', 'Neutral']
                    }
                }
        
        return {
            "summary": summary,
            "detailed_results": results,
            "saved_to_db": True,
            "message": "Batch analysis completed and saved to MongoDB"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

