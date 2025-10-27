from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from app.models.database import (
    Brand, Post, Comment, AnalysisJob,
    AudienceProfile, TopicInterest,
    PlatformType, SentimentType, AnalysisStatusType
)

class DatabaseService:
    """Service untuk database operations"""
    
    # Brand Operations
    async def get_or_create_brand(
        self, 
        name: str, 
        keywords: List[str] = None,
        description: str = None
    ) -> Brand:
        """Get existing brand or create new one"""
        brand = await Brand.find_one(Brand.name == name)
        
        if not brand:
            brand = Brand(
                name=name,
                keywords=keywords or [],
                description=description
            )
            await brand.insert()
            print(f"✅ Created new brand: {name}")
        else:
            # Update keywords if provided
            if keywords:
                brand.keywords = list(set(brand.keywords + keywords))
                brand.updated_at = datetime.now()
                await brand.save()
        
        return brand
    
    async def get_brand(self, name: str) -> Optional[Brand]:
        """Get brand by name"""
        try:
            return await Brand.find_one({'name': name})
        except Exception as e:
            print(f"Error in get_brand: {e}")
            # Fallback to direct MongoDB query
            from app.database.mongodb import get_database
            db = await get_database()
            brand_data = await db.brands.find_one({'name': name})
            if brand_data:
                return Brand(**brand_data)
            return None
    
    async def get_brand_by_id(self, brand_id: str) -> Optional[Brand]:
        """Get brand by ObjectID"""
        try:
            from bson import ObjectId
            print(f"Looking for brand with ID: {brand_id}")
            brand = await Brand.get(ObjectId(brand_id))
            print(f"Found brand: {brand}")
            return brand
        except Exception as e:
            print(f"Error in get_brand_by_id: {str(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            # Fallback to direct MongoDB query
            try:
                from app.database.mongodb import get_database
                from bson import ObjectId
                db = await get_database()
                brand_data = await db.brands.find_one({'_id': ObjectId(brand_id)})
                if brand_data:
                    return Brand(**brand_data)
            except Exception as e2:
                print(f"Fallback error: {e2}")
            return None
    
    async def list_brands(self) -> List[Brand]:
        """List all brands"""
        return await Brand.find_all().to_list()
    
    # Post Operations
    async def save_post(
        self,
        brand: Brand,
        platform: PlatformType,
        platform_post_id: str,
        text: str,
        **kwargs
    ) -> Post:
        """Save or update a post"""
        # Check if post already exists
        existing_post = await Post.find_one(
            Post.platform == platform,
            Post.platform_post_id == platform_post_id
        )
        
        if existing_post:
            # Update existing post
            for key, value in kwargs.items():
                setattr(existing_post, key, value)
            existing_post.text = text
            existing_post.brand = brand
            await existing_post.save()
            return existing_post
        
        # Create new post
        post = Post(
            brand=brand,
            platform=platform,
            platform_post_id=platform_post_id,
            text=text,
            **kwargs
        )
        await post.insert()
        return post
    
    async def bulk_save_posts(
        self,
        brand: Brand,
        platform: PlatformType,
        posts_data: List[Dict[str, Any]]
    ) -> List[Post]:
        """Bulk save posts"""
        saved_posts = []
        
        for post_data in posts_data:
            post = await self.save_post(
                brand=brand,
                platform=platform,
                **post_data
            )
            saved_posts.append(post)
        
        return saved_posts
    
    async def update_post_analysis(
        self,
        post: Post,
        sentiment: Optional[str] = None,
        topic: Optional[str] = None
    ):
        """Update post with analysis results"""
        if sentiment:
            post.sentiment = sentiment
        if topic:
            post.topic = topic
        
        post.analyzed_at = datetime.now()
        await post.save()
    
    async def get_posts_by_brand(
        self,
        brand: Brand,
        platform: Optional[PlatformType] = None,
        limit: int = 100
    ) -> List[Post]:
        """Get posts for a brand"""
        query = Post.find(Post.brand.id == brand.id)
        
        if platform:
            query = query.find(Post.platform == platform)
        
        return await query.limit(limit).to_list()
    
    # Comment Operations  
    async def save_comment(
        self,
        post: Post,
        brand: Brand,
        platform: PlatformType,
        platform_comment_id: str,
        text: str,
        **kwargs
    ) -> Comment:
        """Save or update a comment"""
        existing_comment = await Comment.find_one(
            Comment.platform == platform,
            Comment.platform_comment_id == platform_comment_id
        )
        
        if existing_comment:
            for key, value in kwargs.items():
                setattr(existing_comment, key, value)
            existing_comment.text = text
            await existing_comment.save()
            return existing_comment
        
        comment = Comment(
            post=post,
            brand=brand,
            platform=platform,
            platform_comment_id=platform_comment_id,
            text=text,
            **kwargs
        )
        await comment.insert()
        return comment
    
    async def update_comment_analysis(
        self,
        comment: Comment,
        sentiment: Optional[str] = None,
        topic: Optional[str] = None,
        interest: Optional[str] = None,
        communication_style: Optional[str] = None,
        values: Optional[str] = None
    ):
        """Update comment with analysis results"""
        if sentiment:
            comment.sentiment = sentiment
        if topic:
            comment.topic = topic
        if interest:
            comment.interest = interest
        if communication_style:
            comment.communication_style = communication_style
        if values:
            comment.values = values
        
        comment.analyzed_at = datetime.now()
        await comment.save()
    
    # Analysis Job Operations
    async def create_analysis_job(
        self,
        brand: Brand,
        platforms: List[PlatformType],
        keywords: List[str],
        layer: int = 1
    ) -> AnalysisJob:
        """Create new analysis job"""
        job_id = str(uuid.uuid4())
        
        job = AnalysisJob(
            job_id=job_id,
            brand=brand,
            platforms=platforms,
            keywords=keywords,
            layer=layer,
            status=AnalysisStatusType.PENDING
        )
        await job.insert()
        
        return job
    
    async def update_job_status(
        self,
        job: AnalysisJob,
        status: AnalysisStatusType,
        progress: float = None,
        **kwargs
    ):
        """Update analysis job status"""
        job.status = status
        
        if progress is not None:
            job.progress = progress
        
        if status == AnalysisStatusType.PROCESSING and not job.started_at:
            job.started_at = datetime.now()
        elif status == AnalysisStatusType.COMPLETED:
            job.completed_at = datetime.now()
            job.progress = 100.0
        
        for key, value in kwargs.items():
            setattr(job, key, value)
        
        await job.save()
    
    async def get_job(self, job_id: str) -> Optional[AnalysisJob]:
        """Get job by ID"""
        return await AnalysisJob.find_one(AnalysisJob.job_id == job_id)
    
    async def list_jobs(
        self,
        brand: Optional[Brand] = None,
        status: Optional[AnalysisStatusType] = None,
        limit: int = 50
    ) -> List[AnalysisJob]:
        """List analysis jobs"""
        query = AnalysisJob.find()
        
        if brand:
            query = query.find(AnalysisJob.brand.id == brand.id)
        if status:
            query = query.find(AnalysisJob.status == status)
        
        return await query.sort("-created_at").limit(limit).to_list()
    
    # Audience Profile Operations
    async def save_audience_profile(
        self,
        brand: Brand,
        profile_type: str,
        **data
    ) -> AudienceProfile:
        """Save or update audience profile"""
        # Find existing profile
        query = AudienceProfile.find(
            AudienceProfile.brand.id == brand.id,
            AudienceProfile.profile_type == profile_type
        )
        
        # Add platform/topic filters if provided
        if 'platform' in data and data['platform']:
            query = query.find(AudienceProfile.platform == data['platform'])
        if 'topic' in data and data['topic']:
            query = query.find(AudienceProfile.topic == data['topic'])
        
        existing = await query.first_or_none()
        
        if existing:
            # Update existing profile
            for key, value in data.items():
                setattr(existing, key, value)
            existing.updated_at = datetime.now()
            await existing.save()
            return existing
        
        # Create new profile
        profile = AudienceProfile(
            brand=brand,
            profile_type=profile_type,
            **data
        )
        await profile.insert()
        return profile
    
    async def get_audience_profiles(
        self,
        brand: Brand,
        profile_type: Optional[str] = None,
        platform: Optional[PlatformType] = None
    ) -> List[AudienceProfile]:
        """Get audience profiles"""
        query = AudienceProfile.find(AudienceProfile.brand.id == brand.id)
        
        if profile_type:
            query = query.find(AudienceProfile.profile_type == profile_type)
        if platform:
            query = query.find(AudienceProfile.platform == platform)
        
        return await query.to_list()
    
    # Topic Interest Operations
    async def update_topic_interest(
        self,
        brand: Brand,
        topic: str,
        platform: Optional[PlatformType] = None,
        increment_mentions: bool = False,
        sentiment: Optional[str] = None,
        engagement_data: Optional[Dict] = None
    ) -> TopicInterest:
        """Update or create topic interest"""
        query = TopicInterest.find(
            TopicInterest.brand.id == brand.id,
            TopicInterest.topic == topic
        )
        
        if platform:
            query = query.find(TopicInterest.platform == platform)
        
        topic_interest = await query.first_or_none()
        
        if not topic_interest:
            topic_interest = TopicInterest(
                brand=brand,
                topic=topic,
                platform=platform
            )
        
        # Update counts
        if increment_mentions:
            topic_interest.mention_count += 1
        
        # Update sentiment counts
        if sentiment:
            if sentiment == "Positive":
                topic_interest.positive_count += 1
            elif sentiment == "Negative":
                topic_interest.negative_count += 1
            else:
                topic_interest.neutral_count += 1
        
        # Update engagement
        if engagement_data:
            topic_interest.total_likes += engagement_data.get('likes', 0)
            topic_interest.total_comments += engagement_data.get('comments', 0)
            topic_interest.total_shares += engagement_data.get('shares', 0)
        
        topic_interest.last_seen = datetime.now()
        
        # Calculate trend score (simple formula)
        if topic_interest.mention_count > 0:
            sentiment_ratio = (topic_interest.positive_count - topic_interest.negative_count) / topic_interest.mention_count
            topic_interest.trend_score = topic_interest.mention_count * (1 + sentiment_ratio)
            topic_interest.is_trending = topic_interest.trend_score > 10  # threshold
        
        await topic_interest.save()
        return topic_interest
    
    async def get_trending_topics(
        self,
        brand: Brand,
        platform: Optional[PlatformType] = None,
        limit: int = 10
    ) -> List[TopicInterest]:
        """Get trending topics"""
        query = TopicInterest.find(
            TopicInterest.brand.id == brand.id,
            TopicInterest.is_trending == True
        )
        
        if platform:
            query = query.find(TopicInterest.platform == platform)
        
        return await query.sort("-trend_score").limit(limit).to_list()

    # =============================================================================
    # Brand Analysis Collections
    # =============================================================================
    
    async def create_brand_analysis(
        self,
        brand_id: str,
        analysis_name: str,
        analysis_type: str = "comprehensive",
        keywords: List[str] = None,
        platforms: List[str] = None,
        date_range: Dict[str, Any] = None
    ) -> str:
        """Create a new brand analysis record"""
        try:
            from app.models.database import BrandAnalysis, PlatformType
            
            print(f"Creating brand analysis for brand_id: {brand_id}")
            print(f"Analysis name: {analysis_name}")
            print(f"Keywords: {keywords}")
            print(f"Platforms: {platforms}")
            
            analysis = BrandAnalysis(
                brand_id=brand_id,
                analysis_name=analysis_name,
                analysis_type=analysis_type,
                keywords=keywords or [],
                platforms=[PlatformType(p) for p in platforms] if platforms else [],
                date_range=date_range or {},
                status="pending"
            )
            
            await analysis.save()
            print(f"Brand analysis created with ID: {analysis.id}")
            return str(analysis.id)
        except Exception as e:
            print(f"Error in create_brand_analysis: {str(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            raise
    
    async def update_brand_analysis_status(
        self,
        analysis_id: str,
        status: str,
        total_posts: int = 0,
        total_engagement: int = 0,
        sentiment_distribution: Dict[str, int] = None,
        top_topics: List[str] = None
    ):
        """Update brand analysis status and results"""
        from app.models.database import BrandAnalysis
        
        from bson import ObjectId
        analysis = await BrandAnalysis.get(ObjectId(analysis_id))
        if analysis:
            analysis.status = status
            analysis.total_posts = total_posts
            analysis.total_engagement = total_engagement
            if sentiment_distribution:
                analysis.sentiment_distribution = sentiment_distribution
            if top_topics:
                analysis.top_topics = top_topics
            analysis.updated_at = datetime.now()
            if status == "completed":
                analysis.completed_at = datetime.now()
            await analysis.save()
    
    async def save_brand_metrics(
        self,
        brand_analysis_id: str,
        brand_id: str,
        metrics_data: Dict[str, Any]
    ):
        """Save brand metrics data"""
        from app.models.database import BrandMetrics
        
        metrics = BrandMetrics(
            brand_analysis_id=brand_analysis_id,
            brand_id=brand_id,
            **metrics_data
        )
        await metrics.save()
    
    async def save_brand_sentiment_timeline(
        self,
        brand_analysis_id: str,
        brand_id: str,
        timeline_data: List[Dict[str, Any]]
    ):
        """Save brand sentiment timeline data"""
        from app.models.database import BrandSentimentTimeline
        
        for data in timeline_data:
            timeline = BrandSentimentTimeline(
                brand_analysis_id=brand_analysis_id,
                brand_id=brand_id,
                **data
            )
            await timeline.save()
    
    async def save_brand_trending_topics(
        self,
        brand_analysis_id: str,
        brand_id: str,
        topics_data: List[Dict[str, Any]]
    ):
        """Save brand trending topics data"""
        from app.models.database import BrandTrendingTopics
        
        for data in topics_data:
            topic = BrandTrendingTopics(
                brand_analysis_id=brand_analysis_id,
                brand_id=brand_id,
                **data
            )
            await topic.save()
    
    async def save_brand_demographics(
        self,
        brand_analysis_id: str,
        brand_id: str,
        demographics_data: Dict[str, Any]
    ):
        """Save brand demographics data"""
        from app.models.database import BrandDemographics
        
        demographics = BrandDemographics(
            brand_analysis_id=brand_analysis_id,
            brand_id=brand_id,
            **demographics_data
        )
        await demographics.save()
    
    async def save_brand_engagement_patterns(
        self,
        brand_analysis_id: str,
        brand_id: str,
        patterns_data: Dict[str, Any]
    ):
        """Save brand engagement patterns data"""
        from app.models.database import BrandEngagementPatterns
        
        patterns = BrandEngagementPatterns(
            brand_analysis_id=brand_analysis_id,
            brand_id=brand_id,
            **patterns_data
        )
        await patterns.save()
    
    async def save_brand_performance(
        self,
        brand_analysis_id: str,
        brand_id: str,
        performance_data: Dict[str, Any]
    ):
        """Save brand performance data"""
        from app.models.database import BrandPerformance
        
        performance = BrandPerformance(
            brand_analysis_id=brand_analysis_id,
            brand_id=brand_id,
            **performance_data
        )
        await performance.save()
    
    async def save_brand_emotions(
        self,
        brand_analysis_id: str,
        brand_id: str,
        emotions_data: Dict[str, Any]
    ):
        """Save brand emotions data"""
        from app.models.database import BrandEmotions
        
        emotions = BrandEmotions(
            brand_analysis_id=brand_analysis_id,
            brand_id=brand_id,
            **emotions_data
        )
        await emotions.save()
    
    async def save_brand_competitive(
        self,
        brand_analysis_id: str,
        brand_id: str,
        competitive_data: Dict[str, Any]
    ):
        """Save brand competitive analysis data"""
        from app.models.database import BrandCompetitive
        
        competitive = BrandCompetitive(
            brand_analysis_id=brand_analysis_id,
            brand_id=brand_id,
            **competitive_data
        )
        await competitive.save()
    
    async def get_brand_analysis(self, analysis_id: str):
        """Get brand analysis by ID"""
        from app.models.database import BrandAnalysis
        return await BrandAnalysis.find_one(BrandAnalysis.id == analysis_id)
    
    async def get_brand_metrics(self, brand_analysis_id: str):
        """Get brand metrics by analysis ID"""
        from app.models.database import BrandMetrics
        return await BrandMetrics.find_one(BrandMetrics.brand_analysis_id == brand_analysis_id)
    
    async def get_brand_sentiment_timeline(self, brand_analysis_id: str, start_date: str = None, end_date: str = None):
        """Get brand sentiment timeline by analysis ID"""
        from app.models.database import BrandSentimentTimeline
        
        query = BrandSentimentTimeline.find(BrandSentimentTimeline.brand_analysis_id == brand_analysis_id)
        
        if start_date:
            query = query.find(BrandSentimentTimeline.date >= datetime.fromisoformat(start_date))
        if end_date:
            query = query.find(BrandSentimentTimeline.date <= datetime.fromisoformat(end_date))
        
        return await query.sort("date").to_list()
    
    async def get_brand_trending_topics(self, brand_analysis_id: str, platform: str = None):
        """Get brand trending topics by analysis ID"""
        from app.models.database import BrandTrendingTopics
        
        query = BrandTrendingTopics.find(BrandTrendingTopics.brand_analysis_id == brand_analysis_id)
        
        if platform and platform != "all":
            query = query.find(BrandTrendingTopics.platform == platform)
        
        return await query.sort("-topic_count").to_list()
    
    async def get_brand_demographics(self, brand_analysis_id: str, platform: str = None):
        """Get brand demographics by analysis ID"""
        from app.models.database import BrandDemographics
        
        query = BrandDemographics.find(BrandDemographics.brand_analysis_id == brand_analysis_id)
        
        if platform and platform != "all":
            query = query.find(BrandDemographics.platform == platform)
        
        return await query.to_list()
    
    async def get_brand_engagement_patterns(self, brand_analysis_id: str, platform: str = None):
        """Get brand engagement patterns by analysis ID"""
        from app.models.database import BrandEngagementPatterns
        
        query = BrandEngagementPatterns.find(BrandEngagementPatterns.brand_analysis_id == brand_analysis_id)
        
        if platform and platform != "all":
            query = query.find(BrandEngagementPatterns.platform == platform)
        
        return await query.to_list()
    
    async def get_brand_performance(self, brand_analysis_id: str, platform: str = None):
        """Get brand performance by analysis ID"""
        from app.models.database import BrandPerformance
        
        query = BrandPerformance.find(BrandPerformance.brand_analysis_id == brand_analysis_id)
        
        if platform and platform != "all":
            query = query.find(BrandPerformance.platform == platform)
        
        return await query.to_list()
    
    async def get_brand_emotions(self, brand_analysis_id: str, platform: str = None):
        """Get brand emotions by analysis ID"""
        from app.models.database import BrandEmotions
        
        query = BrandEmotions.find(BrandEmotions.brand_analysis_id == brand_analysis_id)
        
        if platform and platform != "all":
            query = query.find(BrandEmotions.platform == platform)
        
        return await query.to_list()
    
    async def get_brand_competitive(self, brand_analysis_id: str):
        """Get brand competitive analysis by analysis ID"""
        from app.models.database import BrandCompetitive
        return await BrandCompetitive.find_one(BrandCompetitive.brand_analysis_id == brand_analysis_id)

# Singleton instance
db_service = DatabaseService()

