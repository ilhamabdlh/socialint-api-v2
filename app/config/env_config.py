"""
Environment Configuration for Social Intelligence API
"""
import os
from typing import List, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class EnvConfig:
    """Environment configuration class"""
    
    # =============================================================================
    # DATABASE CONFIGURATION
    # =============================================================================
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    MONGODB_DATABASE: str = os.getenv("MONGODB_DATABASE", "socialint")
    
    # =============================================================================
    # API CREDENTIALS
    # =============================================================================
    APIFY_API_TOKEN: Optional[str] = os.getenv("APIFY_API_TOKEN")
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
    
    # =============================================================================
    # SCRAPING LIMITS & CONFIGURATION
    # =============================================================================
    # Default max posts per platform
    DEFAULT_MAX_POSTS_PER_PLATFORM: int = int(os.getenv("DEFAULT_MAX_POSTS_PER_PLATFORM", "100"))
    
    # TikTok scraping limits
    TIKTOK_MAX_POSTS: int = int(os.getenv("TIKTOK_MAX_POSTS", "100"))
    TIKTOK_RESULTS_PER_PAGE: int = int(os.getenv("TIKTOK_RESULTS_PER_PAGE", "100"))
    
    # Instagram scraping limits
    INSTAGRAM_MAX_POSTS: int = int(os.getenv("INSTAGRAM_MAX_POSTS", "100"))
    INSTAGRAM_RESULTS_LIMIT: int = int(os.getenv("INSTAGRAM_RESULTS_LIMIT", "100"))
    INSTAGRAM_SEARCH_LIMIT: int = int(os.getenv("INSTAGRAM_SEARCH_LIMIT", "100"))
    
    # Twitter scraping limits
    TWITTER_MAX_POSTS: int = int(os.getenv("TWITTER_MAX_POSTS", "100"))
    TWITTER_MAX_ITEMS: int = int(os.getenv("TWITTER_MAX_ITEMS", "100"))
    
    # YouTube scraping limits
    YOUTUBE_MAX_POSTS: int = int(os.getenv("YOUTUBE_MAX_POSTS", "100"))
    YOUTUBE_MAX_RESULTS: int = int(os.getenv("YOUTUBE_MAX_RESULTS", "100"))
    
    # =============================================================================
    # ANALYSIS CONFIGURATION
    # =============================================================================
    AI_MODEL: str = os.getenv("AI_MODEL", "gemini-2.0-flash")
    MAX_WORKERS: int = int(os.getenv("MAX_WORKERS", "20"))
    BATCH_SIZE: int = int(os.getenv("BATCH_SIZE", "100"))
    
    # Analysis limits
    MAX_POSTS_FOR_ANALYSIS: int = int(os.getenv("MAX_POSTS_FOR_ANALYSIS", "1000"))
    SENTIMENT_ANALYSIS_BATCH_SIZE: int = int(os.getenv("SENTIMENT_ANALYSIS_BATCH_SIZE", "50"))
    TOPIC_ANALYSIS_BATCH_SIZE: int = int(os.getenv("TOPIC_ANALYSIS_BATCH_SIZE", "100"))
    
    # =============================================================================
    # SCHEDULER CONFIGURATION
    # =============================================================================
    DAILY_ANALYSIS_HOUR: int = int(os.getenv("DAILY_ANALYSIS_HOUR", "0"))
    DAILY_ANALYSIS_MINUTE: int = int(os.getenv("DAILY_ANALYSIS_MINUTE", "0"))
    STATUS_CHECK_INTERVAL_HOURS: int = int(os.getenv("STATUS_CHECK_INTERVAL_HOURS", "6"))
    
    # =============================================================================
    # API CONFIGURATION
    # =============================================================================
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    API_WORKERS: int = int(os.getenv("API_WORKERS", "1"))
    
    # CORS configuration
    CORS_ORIGINS: List[str] = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")
    
    # =============================================================================
    # LOGGING CONFIGURATION
    # =============================================================================
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    
    # =============================================================================
    # CACHE CONFIGURATION
    # =============================================================================
    ENABLE_CACHE: bool = os.getenv("ENABLE_CACHE", "true").lower() == "true"
    CACHE_TTL_SECONDS: int = int(os.getenv("CACHE_TTL_SECONDS", "3600"))
    
    # =============================================================================
    # RATE LIMITING
    # =============================================================================
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_REQUESTS_PER_MINUTE", "60"))
    RATE_LIMIT_BURST: int = int(os.getenv("RATE_LIMIT_BURST", "10"))
    
    # =============================================================================
    # DEVELOPMENT CONFIGURATION
    # =============================================================================
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    RELOAD: bool = os.getenv("RELOAD", "true").lower() == "true"
    
    # =============================================================================
    # SECURITY CONFIGURATION
    # =============================================================================
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your_jwt_secret_key_here")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # =============================================================================
    # NOTIFICATION CONFIGURATION
    # =============================================================================
    SMTP_HOST: Optional[str] = os.getenv("SMTP_HOST")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME: Optional[str] = os.getenv("SMTP_USERNAME")
    SMTP_PASSWORD: Optional[str] = os.getenv("SMTP_PASSWORD")
    SMTP_USE_TLS: bool = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
    
    # =============================================================================
    # MONITORING CONFIGURATION
    # =============================================================================
    HEALTH_CHECK_INTERVAL_SECONDS: int = int(os.getenv("HEALTH_CHECK_INTERVAL_SECONDS", "30"))
    HEALTH_CHECK_TIMEOUT_SECONDS: int = int(os.getenv("HEALTH_CHECK_TIMEOUT_SECONDS", "10"))
    
    # =============================================================================
    # OVERRIDES / ADMIN CONFIGURATION
    # =============================================================================
    ENABLE_OVERRIDES: bool = os.getenv("ENABLE_OVERRIDES", "true").lower() == "true"
    ADMIN_API_KEY: Optional[str] = os.getenv("ADMIN_API_KEY")
    
    # =============================================================================
    # DATA RETENTION
    # =============================================================================
    DATA_RETENTION_DAYS: int = int(os.getenv("DATA_RETENTION_DAYS", "90"))
    ANALYSIS_RETENTION_DAYS: int = int(os.getenv("ANALYSIS_RETENTION_DAYS", "30"))
    SCRAPED_DATA_RETENTION_DAYS: int = int(os.getenv("SCRAPED_DATA_RETENTION_DAYS", "7"))
    
    @classmethod
    def get_scraping_limits(cls, platform: str) -> dict:
        """Get scraping limits for specific platform"""
        limits = {
            "tiktok": {
                "max_posts": cls.TIKTOK_MAX_POSTS,
                "results_per_page": cls.TIKTOK_RESULTS_PER_PAGE
            },
            "instagram": {
                "max_posts": cls.INSTAGRAM_MAX_POSTS,
                "results_limit": cls.INSTAGRAM_RESULTS_LIMIT,
                "search_limit": cls.INSTAGRAM_SEARCH_LIMIT
            },
            "twitter": {
                "max_posts": cls.TWITTER_MAX_POSTS,
                "max_items": cls.TWITTER_MAX_ITEMS
            },
            "youtube": {
                "max_posts": cls.YOUTUBE_MAX_POSTS,
                "max_results": cls.YOUTUBE_MAX_RESULTS
            }
        }
        return limits.get(platform.lower(), {
            "max_posts": cls.DEFAULT_MAX_POSTS_PER_PLATFORM
        })
    
    @classmethod
    def validate_config(cls) -> List[str]:
        """Validate configuration and return list of missing required variables"""
        missing = []
        
        if not cls.APIFY_API_TOKEN:
            missing.append("APIFY_API_TOKEN")
        
        if not cls.GEMINI_API_KEY:
            missing.append("GEMINI_API_KEY")
        
        return missing

# Create global instance
env_config = EnvConfig()

