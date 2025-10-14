from beanie import Document, Indexed, Link
from pydantic import Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

# Enums
class PlatformType(str, Enum):
    TIKTOK = "tiktok"
    INSTAGRAM = "instagram"
    TWITTER = "twitter"
    YOUTUBE = "youtube"
    LINKEDIN = "linkedin"
    FACEBOOK = "facebook"
    REDDIT = "reddit"

class SentimentType(str, Enum):
    POSITIVE = "Positive"
    NEGATIVE = "Negative"
    NEUTRAL = "Neutral"

class AnalysisStatusType(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class CampaignStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"

class CampaignType(str, Enum):
    PRODUCT_LAUNCH = "product_launch"
    BRAND_AWARENESS = "brand_awareness"
    FEATURE_HIGHLIGHT = "feature_highlight"
    SEASONAL = "seasonal"
    EVENT = "event"
    INFLUENCER = "influencer"
    OTHER = "other"

# Database Models
class Brand(Document):
    """Brand model - represents a brand being analyzed"""
    name: Indexed(str, unique=True)  # Brand name
    keywords: List[str] = []  # Keywords for this brand
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    # Metadata
    description: Optional[str] = None
    industry: Optional[str] = None
    
    class Settings:
        name = "brands"
        indexes = [
            "name",
            "created_at",
        ]

class Post(Document):
    """Post model - represents a social media post"""
    # References
    brand: Link[Brand]
    
    # Post info
    platform: PlatformType
    platform_post_id: Indexed(str)  # ID from platform
    post_url: str
    
    # Content
    title: Optional[str] = None
    text: str
    description: Optional[str] = None
    
    # Author info
    author_name: Optional[str] = None
    author_id: Optional[str] = None
    
    # Engagement metrics
    like_count: int = 0
    comment_count: int = 0
    share_count: int = 0
    view_count: int = 0
    
    # Analysis results
    sentiment: Optional[SentimentType] = None
    topic: Optional[str] = None
    emotion: Optional[str] = None  # joy, anger, sadness, fear, surprise, disgust, trust, anticipation, neutral
    
    # Demographics (extracted from content)
    author_age_group: Optional[str] = None  # 18-24, 25-34, 35-44, 45-54, 55+
    author_gender: Optional[str] = None  # male, female, neutral, unknown
    author_location_hint: Optional[str] = None  # Inferred location
    
    # Timestamps
    posted_at: Optional[datetime] = None
    scraped_at: datetime = Field(default_factory=datetime.now)
    analyzed_at: Optional[datetime] = None
    
    # Raw data
    raw_data: Dict[str, Any] = {}
    
    class Settings:
        name = "posts"
        indexes = [
            "brand",
            "platform",
            "platform_post_id",
            "sentiment",
            "topic",
            "posted_at",
        ]

class Comment(Document):
    """Comment model - represents a comment on a post"""
    # References
    post: Link[Post]
    brand: Link[Brand]
    
    # Comment info
    platform: PlatformType
    platform_comment_id: Indexed(str)
    
    # Content
    text: str
    
    # Author info
    author_name: Optional[str] = None
    author_id: Optional[str] = None
    
    # Engagement
    like_count: int = 0
    reply_count: int = 0
    
    # Analysis results
    sentiment: Optional[SentimentType] = None
    topic: Optional[str] = None
    interest: Optional[str] = None  # User interest
    communication_style: Optional[str] = None  # formal/informal
    values: Optional[str] = None  # User values
    
    # Timestamps
    commented_at: Optional[datetime] = None
    scraped_at: datetime = Field(default_factory=datetime.now)
    analyzed_at: Optional[datetime] = None
    
    # Raw data
    raw_data: Dict[str, Any] = {}
    
    class Settings:
        name = "comments"
        indexes = [
            "post",
            "brand",
            "platform",
            "sentiment",
            "topic",
            "author_id",
        ]

class AnalysisJob(Document):
    """Analysis Job - tracks analysis progress"""
    # Job info
    job_id: Indexed(str, unique=True)
    brand: Link[Brand]
    platforms: List[PlatformType]
    
    # Status
    status: AnalysisStatusType = AnalysisStatusType.PENDING
    progress: float = 0.0  # 0-100
    
    # Configuration
    keywords: List[str] = []
    layer: int = 1  # 1=posts, 2=comments
    
    # Results
    total_processed: int = 0
    total_cleansed: int = 0
    
    # Statistics
    cleansing_stats: Dict[str, Any] = {}
    sentiment_distribution: Dict[str, int] = {}
    topics_found: List[str] = []
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Errors
    error_message: Optional[str] = None
    
    class Settings:
        name = "analysis_jobs"
        indexes = [
            "job_id",
            "brand",
            "status",
            "created_at",
        ]

class AudienceProfile(Document):
    """Audience Profile - aggregated user profiling"""
    # References
    brand: Link[Brand]
    
    # Profile info
    profile_type: str  # "overall", "platform_specific", "topic_specific"
    platform: Optional[PlatformType] = None
    topic: Optional[str] = None
    
    # Aggregated insights
    total_users: int = 0
    total_interactions: int = 0
    
    # Interest distribution
    interests: Dict[str, int] = {}  # interest -> count
    top_interests: List[str] = []
    
    # Communication style
    communication_styles: Dict[str, int] = {}  # style -> count
    
    # Values
    values: Dict[str, int] = {}  # value -> count
    top_values: List[str] = []
    
    # Sentiment
    sentiment_distribution: Dict[str, int] = {}
    
    # Demographics (if available)
    demographics: Dict[str, Any] = {}
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    class Settings:
        name = "audience_profiles"
        indexes = [
            "brand",
            "profile_type",
            "platform",
            "topic",
        ]

class TopicInterest(Document):
    """Topic Interest - tracks topic trends and interests"""
    # References
    brand: Link[Brand]
    
    # Topic info
    topic: Indexed(str)
    platform: Optional[PlatformType] = None
    
    # Statistics
    mention_count: int = 0
    unique_users: int = 0
    
    # Sentiment breakdown
    positive_count: int = 0
    negative_count: int = 0
    neutral_count: int = 0
    
    # Engagement
    total_likes: int = 0
    total_comments: int = 0
    total_shares: int = 0
    
    # Trending
    trend_score: float = 0.0
    is_trending: bool = False
    
    # Related topics
    related_topics: List[str] = []
    
    # Timestamps
    first_seen: datetime = Field(default_factory=datetime.now)
    last_seen: datetime = Field(default_factory=datetime.now)
    
    class Settings:
        name = "topic_interests"
        indexes = [
            "brand",
            "topic",
            "platform",
            "is_trending",
            "mention_count",
        ]

class PostURL(Document):
    """Post URL - tracks specific post URLs in a campaign"""
    url: str
    platform: PlatformType
    platform_post_id: Optional[str] = None
    
    # Content preview
    title: Optional[str] = None
    description: Optional[str] = None
    
    # Status
    is_active: bool = True
    last_scraped: Optional[datetime] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    
    class Settings:
        name = "post_urls"

class Campaign(Document):
    """Campaign model - represents a marketing campaign"""
    # Basic info
    campaign_name: Indexed(str, unique=True)
    description: str
    campaign_type: CampaignType
    status: CampaignStatus = CampaignStatus.DRAFT
    
    # References
    brand: Link[Brand]
    
    # Campaign configuration
    keywords: List[str] = []
    target_audiences: List[str] = []  # e.g., ["Tech Enthusiasts", "Truck Owners", "EV Adopters"]
    platforms: List[PlatformType] = []
    
    # Post URLs to track
    post_urls: List[Link[PostURL]] = []
    
    # Timeline
    start_date: datetime
    end_date: datetime
    
    # Auto-analysis settings
    auto_analysis_enabled: bool = True  # Enable daily scheduler
    analysis_frequency: str = "daily"  # daily, hourly, etc.
    last_analysis_at: Optional[datetime] = None
    next_analysis_at: Optional[datetime] = None
    
    # Current metrics (cached for performance)
    total_mentions: int = 0
    overall_sentiment: float = 0.0  # Percentage (0-100)
    engagement_rate: float = 0.0  # Percentage
    reach: int = 0
    
    # Sentiment trend
    sentiment_trend: float = 0.0  # Percentage change
    mentions_trend: float = 0.0  # Percentage change
    engagement_trend: float = 0.0  # Percentage change
    
    # Tags
    tags: List[str] = []  # e.g., ["product launch", "brand awareness"]
    
    # Metadata
    created_by: Optional[str] = None
    team: Optional[str] = None
    notes: Optional[str] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    last_modified_by: Optional[str] = None
    
    class Settings:
        name = "campaigns"
        indexes = [
            "campaign_name",
            "brand",
            "status",
            "start_date",
            "end_date",
            "auto_analysis_enabled",
            "next_analysis_at",
        ]

class CampaignMetrics(Document):
    """Campaign Metrics - time-series metrics for campaigns"""
    # References
    campaign: Link[Campaign]
    brand: Link[Brand]
    
    # Date for this metric snapshot
    metric_date: Indexed(datetime)
    
    # Sentiment metrics
    sentiment_score: float = 0.0  # 0-100
    positive_count: int = 0
    negative_count: int = 0
    neutral_count: int = 0
    
    # Volume metrics
    total_mentions: int = 0
    new_mentions: int = 0  # New mentions since last snapshot
    
    # Engagement metrics
    total_likes: int = 0
    total_comments: int = 0
    total_shares: int = 0
    total_views: int = 0
    engagement_rate: float = 0.0  # (likes + comments + shares) / views
    
    # Reach metrics
    reach: int = 0
    impressions: int = 0
    unique_users: int = 0
    
    # Platform breakdown
    platform_distribution: Dict[str, int] = {}  # platform -> mention_count
    
    # Topic breakdown
    top_topics: List[str] = []
    topic_distribution: Dict[str, int] = {}  # topic -> count
    
    # Sentiment by platform
    platform_sentiment: Dict[str, Dict[str, int]] = {}  # platform -> {pos, neg, neu}
    
    # Trends (compared to previous snapshot)
    sentiment_change: float = 0.0
    mentions_change: float = 0.0
    engagement_change: float = 0.0
    
    # Analysis metadata
    posts_analyzed: int = 0
    comments_analyzed: int = 0
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    
    class Settings:
        name = "campaign_metrics"
        indexes = [
            "campaign",
            "brand",
            "metric_date",
            "created_at",
        ]

class PlatformAnalysis(Document):
    """Platform Analysis - legacy model for non-campaign analysis"""
    # References
    brand: Link[Brand]
    campaign: Optional[Link[Campaign]] = None  # Optional campaign link
    
    # Analysis info
    platform: PlatformType
    layer: int = 1  # 1=posts, 2=comments
    
    # Statistics
    total_analyzed: int = 0
    cleansing_stats: Dict[str, Any] = {}
    
    # Results
    sentiment_distribution: Dict[str, int] = {}
    topics_found: List[str] = []
    
    # Files
    output_file: Optional[str] = None
    
    # Performance
    processing_time: float = 0.0
    
    # Timestamps
    analyzed_at: datetime = Field(default_factory=datetime.now)
    
    class Settings:
        name = "platform_analyses"
        indexes = [
            "brand",
            "campaign",
            "platform",
            "analyzed_at",
        ]

