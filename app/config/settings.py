from pydantic_settings import BaseSettings
from typing import List, Optional
import os
from .env_config import env_config

class Settings(BaseSettings):
    # API Keys - using env_config
    google_api_key: str = env_config.GEMINI_API_KEY or "AIzaSyBm5bwUn44kQQExgAVamMqgvInUu7A-RGg"
    apify_api_token: str = env_config.APIFY_API_TOKEN or ""
    
    # App Settings
    app_name: str = "Social Intelligence API"
    debug: bool = env_config.DEBUG
    
    # AI Settings - using env_config
    max_workers: int = env_config.MAX_WORKERS
    batch_size: int = env_config.BATCH_SIZE
    gemini_model: str = env_config.AI_MODEL
    ai_model: str = env_config.AI_MODEL
    
    # Platforms
    supported_platforms: List[str] = ["tiktok", "instagram", "twitter", "youtube"]
    
    # MongoDB Settings - using env_config
    mongodb_url: str = env_config.MONGODB_URL
    mongodb_db_name: str = env_config.MONGODB_DATABASE
    
    # Scraping Limits - using env_config
    default_max_posts_per_platform: int = env_config.DEFAULT_MAX_POSTS_PER_PLATFORM
    tiktok_max_posts: int = env_config.TIKTOK_MAX_POSTS
    instagram_max_posts: int = env_config.INSTAGRAM_MAX_POSTS
    twitter_max_posts: int = env_config.TWITTER_MAX_POSTS
    youtube_max_posts: int = env_config.YOUTUBE_MAX_POSTS
    
    # Platform-specific limits - using env_config
    tiktok_results_per_page: int = env_config.TIKTOK_RESULTS_PER_PAGE
    instagram_results_limit: int = env_config.INSTAGRAM_RESULTS_LIMIT
    instagram_search_limit: int = env_config.INSTAGRAM_SEARCH_LIMIT
    twitter_max_items: int = env_config.TWITTER_MAX_ITEMS
    youtube_max_results: int = env_config.YOUTUBE_MAX_RESULTS
    
    # Analysis Configuration - using env_config
    max_posts_for_analysis: int = env_config.MAX_POSTS_FOR_ANALYSIS
    sentiment_analysis_batch_size: int = env_config.SENTIMENT_ANALYSIS_BATCH_SIZE
    topic_analysis_batch_size: int = env_config.TOPIC_ANALYSIS_BATCH_SIZE
    
    # Scheduler Configuration - using env_config
    daily_analysis_hour: int = env_config.DAILY_ANALYSIS_HOUR
    daily_analysis_minute: int = env_config.DAILY_ANALYSIS_MINUTE
    status_check_interval_hours: int = env_config.STATUS_CHECK_INTERVAL_HOURS
    
    # API Configuration - using env_config
    api_host: str = env_config.API_HOST
    api_port: int = env_config.API_PORT
    api_workers: int = env_config.API_WORKERS
    cors_origins: str = ",".join(env_config.CORS_ORIGINS)
    
    # Logging Configuration - using env_config
    log_level: str = env_config.LOG_LEVEL
    log_format: str = env_config.LOG_FORMAT
    
    # Cache Configuration - using env_config
    enable_cache: bool = env_config.ENABLE_CACHE
    cache_ttl_seconds: int = env_config.CACHE_TTL_SECONDS
    
    # Rate Limiting - using env_config
    rate_limit_requests_per_minute: int = env_config.RATE_LIMIT_REQUESTS_PER_MINUTE
    rate_limit_burst: int = env_config.RATE_LIMIT_BURST
    
    # Development Configuration - using env_config
    reload: bool = env_config.RELOAD
    
    # Security Configuration - using env_config
    jwt_secret_key: str = env_config.JWT_SECRET_KEY
    jwt_algorithm: str = env_config.JWT_ALGORITHM
    jwt_access_token_expire_minutes: int = env_config.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    
    # Notification Configuration - using env_config
    smtp_host: Optional[str] = env_config.SMTP_HOST
    smtp_port: int = env_config.SMTP_PORT
    smtp_username: Optional[str] = env_config.SMTP_USERNAME
    smtp_password: Optional[str] = env_config.SMTP_PASSWORD
    smtp_use_tls: bool = env_config.SMTP_USE_TLS
    
    # Monitoring Configuration - using env_config
    health_check_interval_seconds: int = env_config.HEALTH_CHECK_INTERVAL_SECONDS
    health_check_timeout_seconds: int = env_config.HEALTH_CHECK_TIMEOUT_SECONDS
    
    # Data Retention - using env_config
    data_retention_days: int = env_config.DATA_RETENTION_DAYS
    analysis_retention_days: int = env_config.ANALYSIS_RETENTION_DAYS
    scraped_data_retention_days: int = env_config.SCRAPED_DATA_RETENTION_DAYS
    
    # Feature Flags
    enable_audience_profiling: bool = True
    enable_user_mapping: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# singleton instance
settings = Settings()

