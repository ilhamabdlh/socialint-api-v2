from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime

class PlatformType(str, Enum):
    TIKTOK = "tiktok"
    INSTAGRAM = "instagram"
    TWITTER = "twitter"
    YOUTUBE = "youtube"

class SentimentType(str, Enum):
    POSITIVE = "Positive"
    NEGATIVE = "Negative"
    NEUTRAL = "Neutral"

class AnalysisLayerType(str, Enum):
    POSTS = "layer1"  # post-level
    COMMENTS = "layer2"  # comment-level

# Request Models
class BrandAnalysisRequest(BaseModel):
    brand_name: str = Field(..., description="Brand name to analyze")
    keywords: List[str] = Field(..., description="Keywords to filter")
    platforms: List[PlatformType] = Field(..., description="Platforms to analyze")
    
    class Config:
        json_schema_extra = {
            "example": {
                "brand_name": "hufagripp",
                "keywords": ["hufagrip", "hufagripp"],
                "platforms": ["tiktok", "instagram"]
            }
        }

class DataUploadRequest(BaseModel):
    platform: PlatformType
    brand_name: str
    file_path: str
    layer: AnalysisLayerType = AnalysisLayerType.POSTS

# Response Models
class AnalysisResult(BaseModel):
    text: str
    sentiment: Optional[str] = None
    topic: Optional[str] = None
    
class CleansingStats(BaseModel):
    initial_count: int
    after_duplicates: int
    after_keywords: int
    after_language: int
    final_count: int

class PlatformAnalysisResponse(BaseModel):
    platform: str
    brand_name: str
    layer: str
    total_analyzed: int
    cleansing_stats: CleansingStats
    topics_found: List[str]
    sentiment_distribution: Dict[str, int]
    output_file: str
    processing_time: float

class BrandAnalysisResponse(BaseModel):
    brand_name: str
    platforms_analyzed: List[str]
    total_posts: int
    overall_sentiment: Dict[str, int]
    top_topics: List[str]
    results: List[PlatformAnalysisResponse]
    created_at: datetime = Field(default_factory=datetime.now)

