from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import warnings

from app.api.routes import router
from app.config.settings import settings
from app.config.env_config import env_config
from app.database.mongodb import connect_to_mongodb, close_mongodb_connection

warnings.filterwarnings('ignore')

# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="AI-powered Social Media Intelligence Analysis API",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=env_config.CORS_ORIGINS,  # Use environment config
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
from app.api.results_routes import router as results_router
from app.api.campaign_routes import router as campaign_router
from app.api.brand_routes import router as brand_router
# from app.api.content_routes import router as content_router
from app.api.scraper_routes import router as scraper_router
app.include_router(router, prefix="/api/v1", tags=["analysis"])
app.include_router(results_router, prefix="/api/v1/results", tags=["results"])
app.include_router(campaign_router, prefix="/api/v1", tags=["campaigns"])
app.include_router(brand_router, prefix="/api/v1", tags=["brands"])
# app.include_router(content_router, prefix="/api/v1", tags=["contents"])
app.include_router(scraper_router, prefix="/api/v1", tags=["scraping"])

@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    print(f"\n{'='*80}")
    print(f"🚀 {settings.app_name} Started")
    print(f"{'='*80}")
    print(f"📊 Supported Platforms: {', '.join(settings.supported_platforms)}")
    print(f"🤖 AI Model: {settings.gemini_model}")
    print(f"⚡ Max Workers: {settings.max_workers}")
    print(f"📦 Batch Size: {settings.batch_size}")
    print(f"💾 MongoDB: {settings.mongodb_db_name}")
    print(f"{'='*80}\n")
    
    # Connect to MongoDB
    try:
        await connect_to_mongodb()
    except Exception as e:
        print(f"⚠️  Warning: Could not connect to MongoDB: {e}")
        print("📝 API will work with limited functionality (CSV export only)")
    
    # Start campaign scheduler
    try:
        from app.services.scheduler_service import scheduler_service
        scheduler_service.start()
    except Exception as e:
        print(f"⚠️  Warning: Could not start scheduler: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    print("\n👋 Shutting down Social Intelligence API...")
    
    # Stop scheduler
    try:
        from app.services.scheduler_service import scheduler_service
        scheduler_service.stop()
    except Exception as e:
        print(f"⚠️  Warning: Could not stop scheduler: {e}")
    
    # Close MongoDB connection
    await close_mongodb_connection()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )

