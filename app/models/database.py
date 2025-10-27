from beanie import Document, Indexed, Link
from pydantic import Field, BaseModel
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

class CreatedFromType(str, Enum):
    BRAND = "brand"
    CAMPAIGN = "campaign"
    CONTENT = "content"

class CampaignType(str, Enum):
    PRODUCT_LAUNCH = "product_launch"
    BRAND_AWARENESS = "brand_awareness"
    FEATURE_HIGHLIGHT = "feature_highlight"
    SEASONAL = "seasonal"
    EVENT = "event"
    INFLUENCER = "influencer"
    OTHER = "other"

# New Models for Platform URLs
class PlatformURL(BaseModel):
    """Platform URL model - represents a platform with its URL"""
    platform: PlatformType
    post_url: str
    
    class Config:
        use_enum_values = True

# Database Models
class Brand(Document):
    """Brand model - represents a brand being analyzed"""
    name: Indexed(str, unique=True)  # Brand name
    keywords: List[str] = []  # Keywords for this brand
    platforms: List[PlatformType] = []  # Platforms to monitor for this brand
    competitors: List[str] = []  # Competitors for this brand
    startDate: Optional[str] = None  # Start date for analysis
    endDate: Optional[str] = None  # End date for analysis
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    # Metadata
    description: Optional[str] = None
    industry: Optional[str] = None
    
    # New fields for content analysis
    created_from: CreatedFromType = CreatedFromType.BRAND  # Track where brand was created from
    platform_urls: List[PlatformURL] = []  # Platform URLs for this brand (new structure)
    postUrls: List[str] = []  # Legacy field - kept for backward compatibility
    
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
    
    # Platform URLs to track (new structure)
    platform_urls: List[PlatformURL] = []
    
    # Post URLs to track (legacy field - kept for backward compatibility)
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

# =============================================================================
# Brand Analysis Collections
# =============================================================================

class BrandAnalysis(Document):
    """Brand Analysis - Main analysis record"""
    brand_id: Indexed(str)  # Reference to brand
    analysis_name: str
    analysis_type: str = "comprehensive"  # comprehensive, sentiment, engagement, etc.
    status: str = "pending"  # pending, running, completed, failed
    
    # Analysis configuration
    keywords: List[str] = []
    platforms: List[PlatformType] = []
    date_range: Dict[str, Any] = {}  # start_date, end_date
    
    # Analysis results summary
    total_posts: int = 0
    total_engagement: int = 0
    sentiment_distribution: Dict[str, int] = {}
    top_topics: List[str] = []
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    
    class Settings:
        name = "brand_analyses"
        indexes = [
            "brand_id",
            "status",
            "created_at",
        ]

class BrandMetrics(Document):
    """Brand Metrics - Detailed analysis metrics"""
    brand_analysis_id: Indexed(str)  # Reference to BrandAnalysis
    brand_id: Indexed(str)  # Reference to brand
    
    # Engagement metrics
    total_posts: int = 0
    total_engagement: int = 0
    avg_engagement_per_post: float = 0.0
    engagement_rate: float = 0.0
    
    # Sentiment metrics
    sentiment_distribution: Dict[str, int] = {}
    sentiment_percentage: Dict[str, float] = {}
    overall_sentiment_score: float = 0.0
    
    # Platform breakdown
    platform_breakdown: Dict[str, Dict[str, Any]] = {}
    
    # Trending topics
    trending_topics: List[Dict[str, Any]] = []
    
    # Demographics
    demographics: Dict[str, Any] = {}
    
    # Engagement patterns
    engagement_patterns: Dict[str, Any] = {}
    
    # Performance metrics
    performance_metrics: Dict[str, Any] = {}
    
    # Emotions analysis
    emotions: Dict[str, Any] = {}
    
    # Competitive analysis
    competitive_analysis: Dict[str, Any] = {}
    
    # Timestamps
    analyzed_at: datetime = Field(default_factory=datetime.now)
    created_at: datetime = Field(default_factory=datetime.now)
    
    class Settings:
        name = "brand_metrics"
        indexes = [
            "brand_analysis_id",
            "brand_id",
            "analyzed_at",
        ]

class BrandSentimentTimeline(Document):
    """Brand Sentiment Timeline - Time series sentiment data"""
    brand_analysis_id: Indexed(str)
    brand_id: Indexed(str)
    
    # Timeline data
    date: datetime
    sentiment_score: float
    positive_count: int = 0
    negative_count: int = 0
    neutral_count: int = 0
    total_posts: int = 0
    
    # Platform breakdown
    platform_breakdown: Dict[str, Dict[str, Any]] = {}
    
    created_at: datetime = Field(default_factory=datetime.now)
    
    class Settings:
        name = "brand_sentiment_timeline"
        indexes = [
            "brand_analysis_id",
            "brand_id",
            "date",
        ]

class BrandTrendingTopics(Document):
    """Brand Trending Topics - Topic analysis data"""
    brand_analysis_id: Indexed(str)
    brand_id: Indexed(str)
    
    # Topic data
    topic: str
    topic_count: int
    sentiment: float
    engagement: int
    positive: int = 0
    negative: int = 0
    neutral: int = 0
    
    # Platform breakdown
    platform: str = "all"
    
    created_at: datetime = Field(default_factory=datetime.now)
    
    class Settings:
        name = "brand_trending_topics"
        indexes = [
            "brand_analysis_id",
            "brand_id",
            "topic",
            "platform",
        ]

class BrandDemographics(Document):
    """Brand Demographics - Audience demographics data"""
    brand_analysis_id: Indexed(str)
    brand_id: Indexed(str)
    
    # Demographics data
    platform: str = "all"
    total_analyzed: int = 0
    
    # Age groups
    age_groups: List[Dict[str, Any]] = []
    
    # Gender distribution
    genders: List[Dict[str, Any]] = []
    
    # Geographic distribution
    top_locations: List[Dict[str, Any]] = []
    
    created_at: datetime = Field(default_factory=datetime.now)
    
    class Settings:
        name = "brand_demographics"
        indexes = [
            "brand_analysis_id",
            "brand_id",
            "platform",
        ]

class BrandEngagementPatterns(Document):
    """Brand Engagement Patterns - Engagement pattern analysis"""
    brand_analysis_id: Indexed(str)
    brand_id: Indexed(str)
    
    # Engagement patterns
    platform: str = "all"
    peak_hours: List[str] = []
    active_days: List[str] = []
    avg_engagement_rate: float = 0.0
    total_posts: int = 0
    
    created_at: datetime = Field(default_factory=datetime.now)
    
    class Settings:
        name = "brand_engagement_patterns"
        indexes = [
            "brand_analysis_id",
            "brand_id",
            "platform",
        ]

class BrandPerformance(Document):
    """Brand Performance - Performance metrics"""
    brand_analysis_id: Indexed(str)
    brand_id: Indexed(str)
    
    # Performance data
    total_reach: int = 0
    total_impressions: int = 0
    total_engagement: int = 0
    engagement_rate: float = 0.0
    estimated_reach: int = 0
    
    # Conversion funnel
    conversion_funnel: Dict[str, Any] = {}
    
    created_at: datetime = Field(default_factory=datetime.now)
    
    class Settings:
        name = "brand_performance"
        indexes = [
            "brand_analysis_id",
            "brand_id",
        ]

class BrandEmotions(Document):
    """Brand Emotions - Emotion analysis data"""
    brand_analysis_id: Indexed(str)
    brand_id: Indexed(str)
    
    # Emotions data
    total_analyzed: int = 0
    dominant_emotion: str = ""
    emotions: Dict[str, float] = {}
    
    created_at: datetime = Field(default_factory=datetime.now)
    
    class Settings:
        name = "brand_emotions"
        indexes = [
            "brand_analysis_id",
            "brand_id",
        ]

class BrandCompetitive(Document):
    """Brand Competitive - Competitive analysis data"""
    brand_analysis_id: Indexed(str)
    brand_id: Indexed(str)
    
    # Competitive data
    competitive_metrics: Dict[str, Any] = {}
    market_position: str = ""
    competitive_insights: List[str] = []
    recommendations: List[str] = []
    
    created_at: datetime = Field(default_factory=datetime.now)
    
    class Settings:
        name = "brand_competitive"
        indexes = [
            "brand_analysis_id",
            "brand_id",
        ]

class ContentAnalysis(Document):
    """Content Analysis model - represents individual content analysis"""
    # Basic Content Info
    title: str
    description: str
    content_text: str  # Main content text
    post_url: str
    platform: PlatformType
    content_type: str = "post"  # video, post, article, image, story
    author: str
    publish_date: str
    status: str = "published"  # published, draft, archived
    tags: List[str] = []
    
    # Legacy fields for backward compatibility
    brand_name: Optional[str] = None
    campaign_id: Optional[str] = None
    keywords: List[str] = []
    target_audience: List[str] = []
    content_category: str = "general"
    language: str = "en"
    priority: str = "medium"
    
    # Analysis Results - Topic Analysis
    topics: List[dict] = []  # [{"topic": "AI", "relevance": 0.8, "confidence": 0.9}]
    dominant_topic: Optional[str] = None
    
    # Analysis Results - Sentiment Analysis
    sentiment_overall: Optional[float] = None  # -1 to 1
    sentiment_positive: Optional[float] = None  # 0 to 1
    sentiment_negative: Optional[float] = None  # 0 to 1
    sentiment_neutral: Optional[float] = None   # 0 to 1
    sentiment_confidence: Optional[float] = None
    sentiment_breakdown: List[dict] = []  # [{"text_segment": "...", "sentiment": "positive", "score": 0.8}]
    
    # Analysis Results - Emotion Analysis
    emotion_joy: Optional[float] = None      # 0 to 1
    emotion_anger: Optional[float] = None    # 0 to 1
    emotion_fear: Optional[float] = None     # 0 to 1
    emotion_sadness: Optional[float] = None  # 0 to 1
    emotion_surprise: Optional[float] = None # 0 to 1
    emotion_trust: Optional[float] = None    # 0 to 1
    emotion_anticipation: Optional[float] = None # 0 to 1
    emotion_disgust: Optional[float] = None  # 0 to 1
    dominant_emotion: Optional[str] = None
    emotion_distribution: List[dict] = []  # [{"emotion": "joy", "score": 0.8, "percentage": 40}]
    
    # Performance Metrics
    engagement_score: Optional[float] = None
    reach_estimate: Optional[int] = None
    virality_score: Optional[float] = None
    content_health_score: Optional[int] = None  # 0 to 100
    
    # Demographics Analysis
    author_age_group: Optional[str] = None  # 18-24, 25-34, 35-44, 45-54, 55+
    author_gender: Optional[str] = None     # male, female, neutral, unknown
    author_location_hint: Optional[str] = None
    target_audience_match: Optional[float] = None  # 0 to 1
    
    # Competitive Analysis
    similar_content_count: Optional[int] = None
    benchmark_engagement: Optional[float] = None
    benchmark_sentiment: Optional[float] = None
    benchmark_topic_trend: Optional[float] = None
    
    # Analysis Status
    analysis_status: str = "pending"  # pending, running, completed, failed
    analysis_type: str = "comprehensive"  # comprehensive, sentiment, engagement, emotion
    analysis_job_id: Optional[str] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    analyzed_at: Optional[datetime] = None
    
    # Raw data for debugging
    raw_analysis_data: Dict[str, Any] = {}
    
    class Settings:
        name = "content_analysis"
        indexes = [
            "platform",
            "content_type",
            "author",
            "status",
            "analysis_status",
            "created_at",
            "analyzed_at",
            "sentiment_overall",
            "dominant_emotion",
            "dominant_topic"
        ]

