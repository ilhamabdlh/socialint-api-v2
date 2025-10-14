from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    # API Keys
    google_api_key: str = "AIzaSyBm5bwUn44kQQExgAVamMqgvInUu7A-RGg"
    apify_api_token: str = ""  # Add your Apify API token here or in .env
    
    # App Settings
    app_name: str = "Social Intelligence API"
    debug: bool = True
    
    # AI Settings
    max_workers: int = 20
    batch_size: int = 100
    gemini_model: str = "gemini-2.0-flash"
    
    # Platforms
    supported_platforms: List[str] = ["tiktok", "instagram", "twitter", "youtube"]
    
    # MongoDB Settings
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "socialint"
    
    # Feature Flags
    enable_audience_profiling: bool = True
    enable_user_mapping: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# singleton instance
settings = Settings()

