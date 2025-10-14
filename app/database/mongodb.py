from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from typing import Optional

from app.config.settings import settings
from app.models.database import (
    Brand,
    Post,
    Comment,
    AnalysisJob,
    AudienceProfile,
    TopicInterest,
    Campaign,
    CampaignMetrics,
    PostURL,
    PlatformAnalysis
)

# Global client instance
mongo_client: Optional[AsyncIOMotorClient] = None

async def connect_to_mongodb():
    """Initialize MongoDB connection"""
    global mongo_client
    
    try:
        # Create motor client
        mongo_client = AsyncIOMotorClient(settings.mongodb_url)
        
        # Get database
        database = mongo_client[settings.mongodb_db_name]
        
        # Initialize beanie with document models
        await init_beanie(
            database=database,
            document_models=[
                Brand,
                Post,
                Comment,
                AnalysisJob,
                AudienceProfile,
                TopicInterest,
                Campaign,
                CampaignMetrics,
                PostURL,
                PlatformAnalysis
            ]
        )
        
        print(f"✅ Connected to MongoDB: {settings.mongodb_db_name}")
        
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB: {str(e)}")
        raise

async def close_mongodb_connection():
    """Close MongoDB connection"""
    global mongo_client
    
    if mongo_client:
        mongo_client.close()
        print("👋 Closed MongoDB connection")

async def get_database():
    """Get database instance"""
    if mongo_client is None:
        await connect_to_mongodb()
    return mongo_client[settings.mongodb_db_name]

