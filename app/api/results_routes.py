from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from typing import List, Optional
from datetime import datetime, timedelta

from app.models.database import (
    Brand, Post, Comment, AnalysisJob, AudienceProfile, TopicInterest,
    PlatformType, AnalysisStatusType, BrandAnalysis, BrandMetrics,
    BrandSentimentTimeline, BrandTrendingTopics, BrandDemographics,
    BrandEngagementPatterns, BrandPerformance, BrandEmotions, BrandCompetitive,
    Campaign, CampaignMetrics
)
from app.services.database_service import db_service
from app.utils.data_helpers import consolidate_demographics, analyze_engagement_patterns, normalize_topic_labeling, normalize_location
from pydantic import BaseModel

router = APIRouter()

# Helper function to get brand by ObjectID or name
async def get_brand_by_identifier(brand_identifier: str):
    """Get brand by ObjectID or brand name"""
    brand = None
    try:
        # Check if it's a valid ObjectID
        from bson import ObjectId
        if ObjectId.is_valid(brand_identifier):
            brand = await db_service.get_brand_by_id(brand_identifier)
    except:
        pass
    
    # If not found by ObjectID, try by name
    if not brand:
        brand = await db_service.get_brand(brand_identifier)
    
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    return brand

# Response Models
class BrandInfo(BaseModel):
    name: str
    keywords: List[str]
    total_posts: int
    total_comments: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class PostSummary(BaseModel):
    id: str
    platform: str
    text: str
    author_name: Optional[str]
    sentiment: Optional[str]
    topic: Optional[str]
    like_count: int
    comment_count: int
    post_url: str
    posted_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class AnalysisJobResponse(BaseModel):
    job_id: str
    brand_name: str
    platforms: List[str]
    status: str
    progress: float
    total_processed: int
    sentiment_distribution: dict
    topics_found: List[str]
    created_at: datetime
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class TopicTrend(BaseModel):
    topic: str
    mention_count: int
    trend_score: float
    sentiment_breakdown: dict
    total_engagement: int
    
    class Config:
        from_attributes = True

class AudienceInsight(BaseModel):
    profile_type: str
    total_users: int
    top_interests: List[str]
    communication_styles: dict
    top_values: List[str]
    sentiment_distribution: dict
    
    class Config:
        from_attributes = True

# ============= BRAND ENDPOINTS =============

@router.get("/brands", response_model=List[BrandInfo])
async def list_brands():
    """Get list of all brands"""
    brands = await db_service.list_brands()
    
    results = []
    for brand in brands:
        # Count posts and comments
        posts = await db_service.get_posts_by_brand(brand, limit=10000)
        total_comments = 0  # TODO: implement comment counting
        
        results.append(BrandInfo(
            name=brand.name,
            keywords=brand.keywords,
            total_posts=len(posts),
            total_comments=total_comments,
            created_at=brand.created_at
        ))
    
    return results

@router.get("/brands/{brand_identifier}")
async def get_brand_details(brand_identifier: str):
    """Get detailed brand information using ObjectID or brand name"""
    brand = await get_brand_by_identifier(brand_identifier)
    
    # Get statistics
    posts = await db_service.get_posts_by_brand(brand, limit=10000)
    
    # Calculate sentiment distribution
    sentiment_dist = {"Positive": 0, "Negative": 0, "Neutral": 0}
    topic_counts = {}
    platform_counts = {}
    
    for post in posts:
        if post.sentiment:
            sentiment_dist[post.sentiment] = sentiment_dist.get(post.sentiment, 0) + 1
        if post.topic:
            topic_counts[post.topic] = topic_counts.get(post.topic, 0) + 1
        platform_counts[post.platform] = platform_counts.get(post.platform, 0) + 1
    
    # Top topics
    top_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    
    return {
        "name": brand.name,
        "keywords": brand.keywords,
        "description": brand.description,
        "created_at": brand.created_at,
        "statistics": {
            "total_posts": len(posts),
            "sentiment_distribution": sentiment_dist,
            "platform_distribution": platform_counts,
            "top_topics": [{"topic": t[0], "count": t[1]} for t in top_topics]
        }
    }

# ============= POSTS ENDPOINTS =============

@router.get("/brands/{brand_identifier}/posts", response_model=List[PostSummary])
async def get_brand_posts(
    brand_identifier: str,
    platform: Optional[PlatformType] = None,
    sentiment: Optional[str] = None,
    topic: Optional[str] = None,
    limit: int = Query(default=50, le=500)
):
    """Get posts for a brand with filters using ObjectID or brand name"""
    brand = await get_brand_by_identifier(brand_identifier)
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    # Get posts
    posts = await db_service.get_posts_by_brand(brand, platform, limit=1000)
    
    # Apply filters
    if sentiment:
        posts = [p for p in posts if p.sentiment == sentiment]
    if topic:
        posts = [p for p in posts if p.topic == topic]
    
    # Limit results
    posts = posts[:limit]
    
    # Convert to response model
    results = []
    for post in posts:
        results.append(PostSummary(
            id=str(post.id),
            platform=post.platform.value,
            text=post.text[:200] + "..." if len(post.text) > 200 else post.text,
            author_name=post.author_name,
            sentiment=post.sentiment,
            topic=post.topic,
            like_count=post.like_count,
            comment_count=post.comment_count,
            post_url=post.post_url,
            posted_at=post.posted_at
        ))
    
    return results

# ============= ANALYSIS JOBS ENDPOINTS =============

@router.get("/jobs", response_model=List[AnalysisJobResponse])
async def list_analysis_jobs(
    brand_name: Optional[str] = None,
    status: Optional[AnalysisStatusType] = None,
    limit: int = 50
):
    """List analysis jobs"""
    brand = None
    if brand_name:
        brand = await db_service.get_brand(brand_name)
        if not brand:
            raise HTTPException(status_code=404, detail="Brand not found")
    
    jobs = await db_service.list_jobs(brand, status, limit)
    
    results = []
    for job in jobs:
        job_brand = await job.brand.fetch()
        results.append(AnalysisJobResponse(
            job_id=job.job_id,
            brand_name=job_brand.name,
            platforms=[p.value for p in job.platforms],
            status=job.status.value,
            progress=job.progress,
            total_processed=job.total_processed,
            sentiment_distribution=job.sentiment_distribution,
            topics_found=job.topics_found,
            created_at=job.created_at,
            completed_at=job.completed_at
        ))
    
    return results

@router.get("/jobs/{job_id}", response_model=AnalysisJobResponse)
async def get_job_status(job_id: str):
    """Get analysis job status and results"""
    job = await db_service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    brand = await job.brand.fetch()
    
    return AnalysisJobResponse(
        job_id=job.job_id,
        brand_name=brand.name,
        platforms=[p.value for p in job.platforms],
        status=job.status.value,
        progress=job.progress,
        total_processed=job.total_processed,
        sentiment_distribution=job.sentiment_distribution,
        topics_found=job.topics_found,
        created_at=job.created_at,
        completed_at=job.completed_at
    )

# ============= TRENDING TOPICS ENDPOINTS =============

@router.get("/brands/{brand_identifier}/trending-topics")
async def get_trending_topics(
    brand_identifier: str,
    platform: Optional[PlatformType] = None,
    limit: int = 10,
    start_date: Optional[str] = Query(default=None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(default=None, description="End date (YYYY-MM-DD)"),
    platforms: Optional[str] = Query(default=None, description="Comma-separated platform names")
):
    """Get trending topics for a brand using ObjectID or brand name with filtering"""
    brand = await get_brand_by_identifier(brand_identifier)
    
    # Parse platform filter
    if platforms:
        try:
            platform_list = [PlatformType(p.strip().lower()) for p in platforms.split(',')]
            platform = platform_list[0] if platform_list else platform
        except:
            pass
    
    # Get posts to analyze topics
    posts = await db_service.get_posts_by_brand(brand, platform, limit=10000)
    
    # Filter by date range
    if start_date or end_date:
        try:
            start_dt = datetime.fromisoformat(start_date) if start_date else None
            end_dt = datetime.fromisoformat(end_date) if end_date else None
            
            if start_dt or end_dt:
                filtered_posts = []
                for p in posts:
                    if p.posted_at:
                        if start_dt and p.posted_at < start_dt:
                            continue
                        if end_dt and p.posted_at > end_dt:
                            continue
                        filtered_posts.append(p)
                if filtered_posts:
                    posts = filtered_posts
        except:
            pass
    
    # Collect all topics for normalization
    all_topics = [post.topic for post in posts if post.topic and post.topic != 'Unknown']
    
    # Normalize topic labels to handle case variations
    topic_mapping = normalize_topic_labeling(all_topics)
    
    # Count topics and calculate sentiment using normalized topics
    topic_counts = {}
    for post in posts:
        if post.topic and post.topic != 'Unknown':
            # Use normalized topic
            normalized_topic = topic_mapping.get(post.topic, post.topic)
            
            if normalized_topic not in topic_counts:
                topic_counts[normalized_topic] = {
                    'count': 0,
                    'sentiment': 0,
                    'positive': 0,
                    'negative': 0,
                    'neutral': 0,
                    'engagement': 0
                }
            
            topic_counts[normalized_topic]['count'] += 1
            engagement_value = (post.like_count or 0) + (post.comment_count or 0) + (post.share_count or 0)
            topic_counts[normalized_topic]['engagement'] += engagement_value
            
            # Sentiment scoring
            if post.sentiment == 'Positive':
                topic_counts[normalized_topic]['positive'] += 1
                topic_counts[normalized_topic]['sentiment'] += 1
            elif post.sentiment == 'Negative':
                topic_counts[normalized_topic]['negative'] += 1
                topic_counts[normalized_topic]['sentiment'] -= 1
            else:
                topic_counts[normalized_topic]['neutral'] += 1
    
    # Sort by count and format results
    sorted_topics = sorted(topic_counts.items(), key=lambda x: x[1]['count'], reverse=True)
    
    results = []
    for topic, data in sorted_topics[:limit]:
        total_sentiment = data['positive'] + data['negative'] + data['neutral']
        sentiment_score = data['sentiment'] / total_sentiment if total_sentiment > 0 else 0
        
        results.append({
            "topic": topic,
            "count": data['count'],
            "sentiment": round(sentiment_score, 2),
            "engagement": data['engagement'],
            "positive": data['positive'],
            "negative": data['negative'],
            "neutral": data['neutral']
        })
    
    return results

# ============= AUDIENCE INSIGHTS ENDPOINTS =============

@router.get("/brands/{brand_identifier}/audience-insights", response_model=List[AudienceInsight])
async def get_audience_insights(
    brand_identifier: str,
    platform: Optional[PlatformType] = None
):
    """Get audience insights for a brand using ObjectID or brand name"""
    brand = await get_brand_by_identifier(brand_identifier)
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    profiles = await db_service.get_audience_profiles(brand, platform=platform)
    
    results = []
    for profile in profiles:
        results.append(AudienceInsight(
            profile_type=profile.profile_type,
            total_users=profile.total_users,
            top_interests=profile.top_interests,
            communication_styles=profile.communication_styles,
            top_values=profile.top_values,
            sentiment_distribution=profile.sentiment_distribution
        ))
    
    return results

# ============= ANALYTICS/SUMMARY ENDPOINTS =============

@router.get("/brands/{brand_identifier}/summary-old")
async def get_brand_summary_old(
    brand_identifier: str,
    days: int = Query(default=30, description="Number of days to analyze"),
    start_date: Optional[str] = Query(default=None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(default=None, description="End date (YYYY-MM-DD)"),
    platforms: Optional[str] = Query(default=None, description="Comma-separated platform names")
):
    """Get comprehensive brand summary using ObjectID or brand name with filtering"""
    brand = await get_brand_by_identifier(brand_identifier)
    
    # Parse platform filter
    platform_list = None
    if platforms:
        try:
            platform_list = [PlatformType(p.strip().lower()) for p in platforms.split(',')]
        except:
            pass
    
    # Get posts with platform filter
    posts = await db_service.get_posts_by_brand(brand, platform=platform_list[0] if platform_list and len(platform_list) > 0 else None, limit=10000)
    
    # Filter by date range
    if start_date or end_date:
        try:
            start_dt = datetime.fromisoformat(start_date) if start_date else None
            end_dt = datetime.fromisoformat(end_date) if end_date else None
            
            if start_dt or end_dt:
                recent_posts = []
                for p in posts:
                    if p.posted_at:
                        if start_dt and p.posted_at < start_dt:
                            continue
                        if end_dt and p.posted_at > end_dt:
                            continue
                        recent_posts.append(p)
                if recent_posts:
                    posts = recent_posts
        except:
            pass
    else:
        # Use days parameter if no date range specified
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_posts = [p for p in posts if p.posted_at and p.posted_at >= cutoff_date]
        if recent_posts:
            posts = recent_posts
    
    # Calculate metrics
    total_engagement = sum(int(p.like_count or 0) + int(p.comment_count or 0) + int(p.share_count or 0) for p in posts)
    avg_engagement = total_engagement / len(posts) if posts else 0
    
    sentiment_dist = {"Positive": 0, "Negative": 0, "Neutral": 0}
    for post in posts:
        if post.sentiment:
            # Convert SentimentType enum to string for dictionary key
            sentiment_key = post.sentiment.value if hasattr(post.sentiment, 'value') else str(post.sentiment)
            sentiment_dist[sentiment_key] += 1
    
    # Get trending topics
    trending = await db_service.get_trending_topics(brand, limit=5)
    
    # Platform breakdown
    platform_breakdown = {}
    for post in posts:
        platform_breakdown[post.platform.value] = platform_breakdown.get(post.platform.value, 0) + 1
    
    return {
        "brand_name": brand.name,
        "period": f"Last {days} days" if not (start_date or end_date) else f"{start_date or 'start'} to {end_date or 'end'}",
        "total_posts": len(posts),
        "total_engagement": total_engagement,
        "avg_engagement_per_post": round(avg_engagement, 2),
        "sentiment_distribution": sentiment_dist,
        "sentiment_percentage": {
            k: round(v / len(posts) * 100, 1) if posts else 0
            for k, v in sentiment_dist.items()
        },
        "platform_breakdown": platform_breakdown,
        "trending_topics": [
            {"topic": t.topic, "mentions": t.mention_count, "score": round(t.trend_score, 2)}
            for t in trending
        ]
    }

@router.get("/brands/{brand_identifier}/sentiment-timeline")
async def get_sentiment_timeline(
    brand_identifier: str,
    platform: Optional[PlatformType] = None,
    days: int = Query(default=30),
    start_date: Optional[str] = Query(default=None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(default=None, description="End date (YYYY-MM-DD)"),
    platforms: Optional[str] = Query(default=None, description="Comma-separated platform names")
):
    """Get sentiment timeline (daily breakdown) with filtering using ObjectID or brand name"""
    brand = await get_brand_by_identifier(brand_identifier)
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    # Parse platform filter
    if platforms:
        try:
            platform_list = [PlatformType(p.strip().lower()) for p in platforms.split(',')]
            platform = platform_list[0] if platform_list else platform
        except:
            pass
    
    posts = await db_service.get_posts_by_brand(brand, platform, limit=10000)
    
    # Filter by date range
    if start_date or end_date:
        try:
            start_dt = datetime.fromisoformat(start_date) if start_date else None
            end_dt = datetime.fromisoformat(end_date) if end_date else None
            
            print(f"🔍 Date filtering: start={start_date}, end={end_date}")
            print(f"🔍 Parsed dates: start_dt={start_dt}, end_dt={end_dt}")
            print(f"🔍 Original posts count: {len(posts)}")
            
            if start_dt or end_dt:
                filtered_posts = []
                for p in posts:
                    if p.posted_at:
                        if start_dt and p.posted_at < start_dt:
                            continue
                        if end_dt and p.posted_at > end_dt:
                            continue
                        filtered_posts.append(p)
                if filtered_posts:
                    posts = filtered_posts
                    print(f"🔍 Filtered posts count: {len(posts)}")
        except Exception as e:
            print(f"❌ Date filtering error: {e}")
            pass
    
    # Group by date
    timeline = {}
    for post in posts:
        if post.posted_at:
            date_key = post.posted_at.date().isoformat()
            if date_key not in timeline:
                timeline[date_key] = {
                    "Positive": 0, 
                    "Negative": 0, 
                    "Neutral": 0,
                    "total_posts": 0,
                    "total_likes": 0,
                    "total_comments": 0,
                    "total_shares": 0
                }
            
            timeline[date_key]["total_posts"] += 1
            timeline[date_key]["total_likes"] += int(post.like_count or 0)
            timeline[date_key]["total_comments"] += int(post.comment_count or 0)
            timeline[date_key]["total_shares"] += int(post.share_count or 0)
            
            if post.sentiment:
                # Convert SentimentType enum to string for dictionary key
                sentiment_key = post.sentiment.value if hasattr(post.sentiment, 'value') else str(post.sentiment)
                timeline[date_key][sentiment_key] += 1
            else:
                # If no sentiment, assign based on engagement
                if (post.like_count or 0) > 10:
                    timeline[date_key]["Positive"] += 1
                elif (post.comment_count or 0) > 5:
                    timeline[date_key]["Negative"] += 1
                else:
                    timeline[date_key]["Neutral"] += 1
        else:
            # If no posted_at, use created_at or current date
            fallback_date = post.created_at.date() if hasattr(post, 'created_at') and post.created_at else datetime.now().date()
            date_key = fallback_date.isoformat()
            if date_key not in timeline:
                timeline[date_key] = {
                    "Positive": 0, 
                    "Negative": 0, 
                    "Neutral": 0,
                    "total_posts": 0,
                    "total_likes": 0,
                    "total_comments": 0,
                    "total_shares": 0
                }
            
            timeline[date_key]["total_posts"] += 1
            timeline[date_key]["total_likes"] += int(post.like_count or 0)
            timeline[date_key]["total_comments"] += int(post.comment_count or 0)
            timeline[date_key]["total_shares"] += int(post.share_count or 0)
            
            if post.sentiment:
                # Convert SentimentType enum to string for dictionary key
                sentiment_key = post.sentiment.value if hasattr(post.sentiment, 'value') else str(post.sentiment)
                timeline[date_key][sentiment_key] += 1
            else:
                # If no sentiment, assign based on engagement
                if (post.like_count or 0) > 10:
                    timeline[date_key]["Positive"] += 1
                elif (post.comment_count or 0) > 5:
                    timeline[date_key]["Negative"] += 1
                else:
                    timeline[date_key]["Neutral"] += 1
    
    
    
    # Return empty timeline if no data exists - no mock data generation
    if not timeline:
        return {
            "brand_name": brand.name,
            "platform": platform.value if platform else "all",
            "timeline": []
        }
    
    # Sort by date and fill missing dates
    sorted_timeline = sorted(timeline.items(), key=lambda x: x[0])
    
    # Calculate percentages and averages
    processed_timeline = []
    for date, data in sorted_timeline:
        total_sentiment = data["Positive"] + data["Negative"] + data["Neutral"]
        if total_sentiment == 0:
            total_sentiment = 1  # Avoid division by zero
            
        processed_timeline.append({
            "date": date,
            "Positive": data["Positive"],
            "Negative": data["Negative"],
            "Neutral": data["Neutral"],
            "positive_percentage": round((data["Positive"] / total_sentiment) * 100, 1),
            "negative_percentage": round((data["Negative"] / total_sentiment) * 100, 1),
            "neutral_percentage": round((data["Neutral"] / total_sentiment) * 100, 1),
            "total_posts": data["total_posts"],
            "total_likes": data["total_likes"],
            "total_comments": data["total_comments"],
            "total_shares": data["total_shares"],
            "avg_sentiment": round((data["Positive"] - data["Negative"]) / total_sentiment, 3)
        })
    
    return {
        "brand_name": brand.name,
        "platform": platform.value if platform else "all",
        "timeline": processed_timeline
    }

@router.get("/brands/{brand_identifier}/emotions")
async def get_emotions_analysis(
    brand_identifier: str,
    platform: Optional[PlatformType] = None,
    limit: int = Query(default=10000),
    start_date: Optional[str] = Query(default=None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(default=None, description="End date (YYYY-MM-DD)"),
    platforms: Optional[str] = Query(default=None, description="Comma-separated platform names")
):
    """
    Get emotions analysis for a brand with filtering using ObjectID or brand name
    Returns distribution of emotions: joy, anger, sadness, fear, surprise, disgust, trust, anticipation
    """
    brand = await get_brand_by_identifier(brand_identifier)
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    # Parse platform filter
    if platforms:
        try:
            platform_list = [PlatformType(p.strip().lower()) for p in platforms.split(',')]
            platform = platform_list[0] if platform_list else platform
        except:
            pass
    
    posts = await db_service.get_posts_by_brand(brand, platform, limit=limit)
    
    # Filter by date range
    if start_date or end_date:
        try:
            start_dt = datetime.fromisoformat(start_date) if start_date else None
            end_dt = datetime.fromisoformat(end_date) if end_date else None
            
            if start_dt or end_dt:
                filtered_posts = []
                for p in posts:
                    if p.posted_at:
                        if start_dt and p.posted_at < start_dt:
                            continue
                        if end_dt and p.posted_at > end_dt:
                            continue
                        filtered_posts.append(p)
                if filtered_posts:
                    posts = filtered_posts
        except:
            pass
    
    # Count emotions
    emotions_count = {}
    total = 0
    
    for post in posts:
        if post.emotion and post.emotion != 'unknown':
            emotions_count[post.emotion] = emotions_count.get(post.emotion, 0) + 1
            total += 1
    
    # Calculate percentages
    emotions_data = [
        {
            "emotion": emotion,
            "count": count,
            "percentage": round(count / total * 100, 2) if total > 0 else 0
        }
        for emotion, count in sorted(emotions_count.items(), key=lambda x: x[1], reverse=True)
    ]
    
    return {
        "brand_name": brand.name,
        "platform": platform.value if platform else "all",
        "total_analyzed": total,
        "emotions": emotions_data,
        "dominant_emotion": emotions_data[0]["emotion"] if emotions_data else None
    }

@router.get("/brands/{brand_identifier}/demographics")
async def get_demographics_analysis(
    brand_identifier: str,
    platform: Optional[PlatformType] = None,
    limit: int = Query(default=10000),
    start_date: Optional[str] = Query(default=None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(default=None, description="End date (YYYY-MM-DD)"),
    platforms: Optional[str] = Query(default=None, description="Comma-separated platform names")
):
    """
    Get demographics analysis for a brand's audience with filtering using ObjectID or brand name
    Returns age groups, gender distribution, and location insights
    """
    brand = await get_brand_by_identifier(brand_identifier)
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    # Parse platform filter
    if platforms:
        try:
            platform_list = [PlatformType(p.strip().lower()) for p in platforms.split(',')]
            platform = platform_list[0] if platform_list else platform
        except:
            pass
    
    posts = await db_service.get_posts_by_brand(brand, platform, limit=limit)
    
    # Filter by date range
    if start_date or end_date:
        try:
            start_dt = datetime.fromisoformat(start_date) if start_date else None
            end_dt = datetime.fromisoformat(end_date) if end_date else None
            
            if start_dt or end_dt:
                filtered_posts = []
                for p in posts:
                    if p.posted_at:
                        if start_dt and p.posted_at < start_dt:
                            continue
                        if end_dt and p.posted_at > end_dt:
                            continue
                        filtered_posts.append(p)
                if filtered_posts:
                    posts = filtered_posts
        except:
            pass
    
    # Prepare demographics data for consolidation
    demographics_data = []
    locations = {}
    total = 0
    
    for post in posts:
        demographics_data.append({
            'age_group': post.author_age_group,
            'gender': post.author_gender,
            'location_hint': post.author_location_hint
        })
        
        if post.author_location_hint and post.author_location_hint != 'unknown':
            locations[post.author_location_hint] = locations.get(post.author_location_hint, 0) + 1
        
        total += 1
    
    # Consolidate demographics to remove duplicates
    consolidated_demo = consolidate_demographics(demographics_data)
    
    # Format consolidated data
    age_data = [
        {"age_group": age, "count": count, "percentage": round(count / total * 100, 2) if total > 0 else 0}
        for age, count in sorted(consolidated_demo.get('age_groups', {}).items(), key=lambda x: x[1], reverse=True)
    ]
    
    gender_data = [
        {"gender": gender, "count": count, "percentage": round(count / total * 100, 2) if total > 0 else 0}
        for gender, count in sorted(consolidated_demo.get('gender_distribution', {}).items(), key=lambda x: x[1], reverse=True)
    ]
    
    # Use consolidated locations instead of raw locations
    consolidated_locations = consolidated_demo.get('locations', {})
    location_data = [
        {"location": loc, "count": count, "percentage": round(count / total * 100, 2) if total > 0 else 0}
        for loc, count in sorted(consolidated_locations.items(), key=lambda x: x[1], reverse=True)[:10]  # Top 10 locations
    ]
    
    return {
        "brand_name": brand.name,
        "platform": platform.value if platform else "all",
        "total_analyzed": total,
        "age_groups": age_data,
        "genders": gender_data,
        "top_locations": location_data
    }

@router.get("/brands/{brand_identifier}/engagement-patterns")
async def get_engagement_patterns(
    brand_identifier: str,
    platform: Optional[PlatformType] = None,
    limit: int = Query(default=10000),
    start_date: Optional[str] = Query(default=None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(default=None, description="End date (YYYY-MM-DD)"),
    platforms: Optional[str] = Query(default=None, description="Comma-separated platform names")
):
    """
    Get engagement patterns analysis for a brand with filtering using ObjectID or brand name
    Returns peak hours, active days, and average engagement rate
    """
    brand = await get_brand_by_identifier(brand_identifier)
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    # Parse platform filter
    if platforms:
        try:
            platform_list = [PlatformType(p.strip().lower()) for p in platforms.split(',')]
            platform = platform_list[0] if platform_list else platform
        except:
            pass
    
    posts = await db_service.get_posts_by_brand(brand, platform, limit=limit)
    
    # Filter by date range
    if start_date or end_date:
        try:
            start_dt = datetime.fromisoformat(start_date) if start_date else None
            end_dt = datetime.fromisoformat(end_date) if end_date else None
            
            if start_dt or end_dt:
                filtered_posts = []
                for p in posts:
                    if p.posted_at:
                        if start_dt and p.posted_at < start_dt:
                            continue
                        if end_dt and p.posted_at > end_dt:
                            continue
                        filtered_posts.append(p)
                if filtered_posts:
                    posts = filtered_posts
        except:
            pass
    
    if not posts:
        return {
            "brand_name": brand.name,
            "platform": platform.value if platform else "all",
            "peak_hours": [],
            "active_days": [],
            "avg_engagement_rate": 0.0,
            "total_posts": 0
        }
    
    # Convert posts to DataFrame for analysis
    import pandas as pd
    posts_data = []
    for post in posts:
        # Use posted_at if available, otherwise use created_at or current time
        posted_at = post.posted_at
        if not posted_at and hasattr(post, 'created_at') and post.created_at:
            posted_at = post.created_at
        elif not posted_at:
            # If no timestamp available, use current time as fallback
            from datetime import datetime
            posted_at = datetime.now()
        
        posts_data.append({
            'like_count': post.like_count or 0,
            'comment_count': post.comment_count or 0,
            'share_count': post.share_count or 0,
            'view_count': getattr(post, 'view_count', 1) or 1,
            'posted_at': posted_at
        })
    
    df = pd.DataFrame(posts_data)
    engagement_patterns = analyze_engagement_patterns(df)
    
    return {
        "brand_name": brand.name,
        "platform": platform.value if platform else "all",
        "peak_hours": engagement_patterns.get('peak_hours', []),
        "active_days": engagement_patterns.get('active_days', []),
        "avg_engagement_rate": engagement_patterns.get('avg_engagement_rate', 0.0),
        "total_posts": len(posts)
    }

# ============= PERFORMANCE METRICS ENDPOINTS =============

@router.get("/brands/{brand_identifier}/performance")
async def get_performance_metrics(
    brand_identifier: str,
    platform: Optional[PlatformType] = None,
    days: int = Query(default=30),
    start_date: Optional[str] = Query(default=None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(default=None, description="End date (YYYY-MM-DD)"),
    platforms: Optional[str] = Query(default=None, description="Comma-separated platform names")
):
    """
    Get performance metrics for a brand with filtering using ObjectID or brand name
    Returns engagement rates, reach, and other performance indicators
    """
    brand = await get_brand_by_identifier(brand_identifier)
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    # Parse platform filter
    if platforms:
        try:
            platform_list = [PlatformType(p.strip().lower()) for p in platforms.split(',')]
            platform = platform_list[0] if platform_list else platform
        except:
            pass
    
    posts = await db_service.get_posts_by_brand(brand, platform, limit=10000)
    
    # Filter by date range
    if start_date or end_date:
        try:
            start_dt = datetime.fromisoformat(start_date) if start_date else None
            end_dt = datetime.fromisoformat(end_date) if end_date else None
            
            if start_dt or end_dt:
                filtered_posts = []
                for p in posts:
                    if p.posted_at:
                        if start_dt and p.posted_at < start_dt:
                            continue
                        if end_dt and p.posted_at > end_dt:
                            continue
                        filtered_posts.append(p)
                if filtered_posts:
                    posts = filtered_posts
        except:
            pass
    else:
        # Use days parameter if no date range specified
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_posts = [p for p in posts if p.posted_at and p.posted_at >= cutoff_date]
        if recent_posts:
            posts = recent_posts
    
    # Calculate performance metrics
    total_posts = len(posts)
    total_likes = sum(int(p.like_count or 0) for p in posts)
    total_comments = sum(int(p.comment_count or 0) for p in posts)
    total_shares = sum(int(p.share_count or 0) for p in posts)
    total_engagement = total_likes + total_comments + total_shares
    
    # Calculate averages
    avg_likes_per_post = total_likes / total_posts if total_posts > 0 else 0
    avg_comments_per_post = total_comments / total_posts if total_posts > 0 else 0
    avg_shares_per_post = total_shares / total_posts if total_posts > 0 else 0
    avg_engagement_per_post = total_engagement / total_posts if total_posts > 0 else 0
    
    # Engagement rate calculation: total_engagement / total_posts
    estimated_reach = total_engagement * 10  # Assuming reach is roughly 10x the engagement for social media
    engagement_rate = (total_engagement / total_posts) if total_posts > 0 else 0
    
    # Platform breakdown
    platform_breakdown = {}
    for post in posts:
        platform_name = post.platform.value
        if platform_name not in platform_breakdown:
            platform_breakdown[platform_name] = {
                'posts': 0,
                'engagement': 0,
                'likes': 0,
                'comments': 0,
                'shares': 0
            }
        
        platform_breakdown[platform_name]['posts'] += 1
        platform_breakdown[platform_name]['engagement'] += int(post.like_count or 0) + int(post.comment_count or 0) + int(post.share_count or 0)
        platform_breakdown[platform_name]['likes'] += int(post.like_count or 0)
        platform_breakdown[platform_name]['comments'] += int(post.comment_count or 0)
        platform_breakdown[platform_name]['shares'] += post.share_count
    
    # Calculate platform-specific engagement rates
    for platform_data in platform_breakdown.values():
        platform_data['avg_engagement_per_post'] = platform_data['engagement'] / platform_data['posts'] if platform_data['posts'] > 0 else 0
    
    return {
        "brand_name": brand.name,
        "period": f"Last {days} days",
        "platform": platform.value if platform else "all",
        "total_posts": total_posts,
        "total_engagement": total_engagement,
        "total_likes": total_likes,
        "total_comments": total_comments,
        "total_shares": total_shares,
        "avg_engagement_per_post": round(avg_engagement_per_post, 2),
        "avg_likes_per_post": round(avg_likes_per_post, 2),
        "avg_comments_per_post": round(avg_comments_per_post, 2),
        "avg_shares_per_post": round(avg_shares_per_post, 2),
        "engagement_rate": round(engagement_rate, 2),
        "estimated_reach": estimated_reach,
        "platform_breakdown": platform_breakdown
    }

# ============= COMPETITIVE ANALYSIS ENDPOINTS =============

@router.get("/brands/{brand_identifier}/competitive")
async def get_competitive_analysis(
    brand_identifier: str,
    days: int = Query(default=30)
):
    """
    Get competitive analysis for a brand using ObjectID or brand name
    Compares brand performance with industry benchmarks
    """
    brand = await get_brand_by_identifier(brand_identifier)
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    posts = await db_service.get_posts_by_brand(brand, limit=10000)
    
    # Calculate brand metrics
    total_posts = len(posts)
    total_engagement = sum(int(p.like_count or 0) + int(p.comment_count or 0) + int(p.share_count or 0) for p in posts)
    avg_engagement_per_post = total_engagement / total_posts if total_posts > 0 else 0
    
    # Calculate estimated reach (same as performance endpoint)
    estimated_reach = total_engagement * 10
    
    # Calculate sentiment metrics
    sentiment_counts = {"Positive": 0, "Negative": 0, "Neutral": 0}
    for post in posts:
        if post.sentiment:
            # Convert SentimentType enum to string for dictionary key
            sentiment_key = post.sentiment.value if hasattr(post.sentiment, 'value') else str(post.sentiment)
            sentiment_counts[sentiment_key] += 1
    
    total_sentiment = sum(sentiment_counts.values())
    sentiment_score = 0
    if total_sentiment > 0:
        sentiment_score = (sentiment_counts["Positive"] - sentiment_counts["Negative"]) / total_sentiment
    
    # Calculate industry benchmarks from actual data
    # Get all posts from the same industry/category for comparison
    all_posts = await db_service.get_all_posts(limit=10000)
    if all_posts:
        # Calculate industry averages from real data
        industry_engagement_rates = []
        industry_sentiment_scores = []
        industry_posts_per_month = []
        
        for post in all_posts:
            if post.like_count and post.comment_count and post.share_count:
                total_engagement = post.like_count + post.comment_count + post.share_count
                estimated_reach = total_engagement * 10  # Assuming 10x multiplier
                engagement_rate = (total_engagement / 1) if 1 > 0 else 0  # Simplified for industry calculation
                industry_engagement_rates.append(engagement_rate)
            
            if post.sentiment is not None:
                industry_sentiment_scores.append(post.sentiment)
        
        # Calculate averages
        avg_engagement_rate = sum(industry_engagement_rates) / len(industry_engagement_rates) if industry_engagement_rates else 3.5
        avg_sentiment_score = sum(industry_sentiment_scores) / len(industry_sentiment_scores) if industry_sentiment_scores else 0.15
        avg_posts_per_month = len(all_posts) // 12 if all_posts else 25  # Rough estimate
        top_performers_engagement = max(industry_engagement_rates) if industry_engagement_rates else 8.2
    else:
        # Fallback to reasonable defaults if no data available
        avg_engagement_rate = 3.5
        avg_sentiment_score = 0.15
        avg_posts_per_month = 25
        top_performers_engagement = 8.2
    
    industry_benchmarks = {
        "avg_engagement_rate": round(avg_engagement_rate, 2),
        "avg_sentiment_score": round(avg_sentiment_score, 3),
        "avg_posts_per_month": avg_posts_per_month,
        "top_performers_engagement": round(top_performers_engagement, 2)
    }
    
    # Calculate competitive position - use the same calculation as performance endpoint
    brand_engagement_rate = (total_engagement / total_posts) if total_posts > 0 else 0
    
    competitive_position = "average"
    if brand_engagement_rate > industry_benchmarks["top_performers_engagement"]:
        competitive_position = "leader"
    elif brand_engagement_rate > industry_benchmarks["avg_engagement_rate"]:
        competitive_position = "above_average"
    elif brand_engagement_rate < industry_benchmarks["avg_engagement_rate"] * 0.7:
        competitive_position = "below_average"
    
    # Competitive insights
    competitive_insights = []
    
    # Engagement comparison
    engagement_vs_industry = brand_engagement_rate - industry_benchmarks["avg_engagement_rate"]
    competitive_insights.append({
        "metric": "engagement_rate",
        "brand_value": round(brand_engagement_rate, 2),
        "industry_average": industry_benchmarks["avg_engagement_rate"],
        "difference": round(engagement_vs_industry, 2),
        "performance": "above_average" if engagement_vs_industry > 0 else "below_average"
    })
    
    # Sentiment comparison
    sentiment_vs_industry = sentiment_score - industry_benchmarks["avg_sentiment_score"]
    competitive_insights.append({
        "metric": "sentiment_score",
        "brand_value": round(sentiment_score, 3),
        "industry_average": industry_benchmarks["avg_sentiment_score"],
        "difference": round(sentiment_vs_industry, 3),
        "performance": "above_average" if sentiment_vs_industry > 0 else "below_average"
    })
    
    return {
        "brand_name": brand.name,
        "period": f"Last {days} days",
        "competitive_position": competitive_position,
        "brand_metrics": {
            "total_posts": total_posts,
            "total_engagement": total_engagement,
            "avg_engagement_per_post": round(avg_engagement_per_post, 2),
            "engagement_rate": round(brand_engagement_rate, 2),
            "sentiment_score": round(sentiment_score, 3),
            "sentiment_breakdown": sentiment_counts
        },
        "industry_benchmarks": industry_benchmarks,
        "competitive_insights": competitive_insights,
        "recommendations": [
            "Increase posting frequency" if total_posts < industry_benchmarks["avg_posts_per_month"] else "Maintain current posting frequency",
            "Focus on engagement optimization" if brand_engagement_rate < industry_benchmarks["avg_engagement_rate"] else             "Continue current engagement strategy",
            "Improve sentiment through better content" if sentiment_score < industry_benchmarks["avg_sentiment_score"] else "Maintain positive sentiment trend"
        ]
    }


# ============= BRAND ANALYSIS ENDPOINTS =============

@router.get("/brands/{brand_identifier}/summary-simple")
async def get_brand_analysis_summary_simple(
    brand_identifier: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    platforms: Optional[str] = None,
    days: int = 30
):
    """
    Get simplified brand analysis summary for testing
    """
    try:
        # Get brand by identifier
        brand = await get_brand_by_identifier(brand_identifier)
        
        # Get posts with filters
        posts = await db_service.get_posts_by_brand(brand)
        
        if not posts:
            return {
                "brand_name": brand.name,
                "period": f"Last {days} days",
                "total_posts": 0,
                "total_engagement": 0,
                "avg_engagement_per_post": 0,
                "sentiment_distribution": {"Positive": 0, "Negative": 0, "Neutral": 0},
                "sentiment_percentage": {"Positive": 0, "Negative": 0, "Neutral": 0},
                "platform_breakdown": {},
                "trending_topics": [],
                "brand_health_score": 0
            }
        
        # Calculate key metrics - simplified approach
        total_posts = len(posts)
        total_engagement = 0
        sentiment_counts = {"Positive": 0, "Negative": 0, "Neutral": 0}
        platform_breakdown = {}
        
        for post in posts:
            # Safe engagement calculation
            try:
                like_count = int(post.like_count) if post.like_count is not None else 0
                comment_count = int(post.comment_count) if post.comment_count is not None else 0
                share_count = int(post.share_count) if post.share_count is not None else 0
                total_engagement += like_count + comment_count + share_count
            except (ValueError, TypeError):
                continue
            
            # Safe sentiment counting
            if post.sentiment is not None:
                try:
                    sentiment_str = str(post.sentiment.value) if hasattr(post.sentiment, 'value') else str(post.sentiment)
                    if sentiment_str in sentiment_counts:
                        sentiment_counts[sentiment_str] += 1
                except:
                    continue
            
            # Safe platform breakdown
            try:
                platform_name = str(post.platform.value) if hasattr(post.platform, 'value') else str(post.platform)
                if platform_name not in platform_breakdown:
                    platform_breakdown[platform_name] = {
                        "posts": 0,
                        "engagement": 0
                    }
                platform_breakdown[platform_name]["posts"] += 1
                platform_breakdown[platform_name]["engagement"] += like_count + comment_count + share_count
            except:
                continue
        
        # Calculate averages
        avg_engagement_per_post = total_engagement / total_posts if total_posts > 0 else 0
        
        # Calculate engagement rate using the formula: avg_engagement_per_post / 100
        engagement_rate = avg_engagement_per_post / 100
        
        # Calculate sentiment percentages
        total_sentiment_posts = sum(sentiment_counts.values())
        sentiment_percentage = {
            "Positive": round((sentiment_counts["Positive"] / total_sentiment_posts * 100), 1) if total_sentiment_posts > 0 else 0,
            "Negative": round((sentiment_counts["Negative"] / total_sentiment_posts * 100), 1) if total_sentiment_posts > 0 else 0,
            "Neutral": round((sentiment_counts["Neutral"] / total_sentiment_posts * 100), 1) if total_sentiment_posts > 0 else 0
        }
        
        return {
            "brand_name": brand.name,
            "period": f"Last {days} days",
            "total_posts": total_posts,
            "total_engagement": total_engagement,
            "avg_engagement_per_post": round(avg_engagement_per_post, 2),
            "engagement_rate": round(engagement_rate, 2),
            "sentiment_distribution": sentiment_counts,
            "sentiment_percentage": sentiment_percentage,
            "platform_breakdown": platform_breakdown,
            "trending_topics": [],
            "brand_health_score": 0
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing brand: {str(e)}")

@router.get("/brands/{brand_identifier}/summary")
async def get_brand_analysis_summary(
    brand_identifier: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    platforms: Optional[str] = None,
    days: int = 30
):
    """
    Get comprehensive brand analysis summary
    
    This endpoint provides key metrics and insights for brand analysis including:
    - Overall sentiment distribution
    - Platform performance breakdown
    - Trending topics and keywords
    - Engagement metrics
    - Brand health indicators
    """
    try:
        # Get brand by identifier (ObjectID or name)
        brand = await get_brand_by_identifier(brand_identifier)
        if not brand:
            raise HTTPException(status_code=404, detail="Brand not found")
        
        # Try to get latest brand analysis
        print(f"Looking for brand analyses for brand_id: {str(brand.id)}")
        brand_analyses = await BrandAnalysis.find(
            BrandAnalysis.brand_id == str(brand.id)
        ).sort("-created_at").limit(1).to_list()
        
        print(f"Found {len(brand_analyses)} brand analyses")
        
        # If brand analysis exists, get metrics from new collections
        if brand_analyses:
            analysis = brand_analyses[0]
            metrics = await db_service.get_brand_metrics(str(analysis.id))
            
            if metrics:
                return {
                    "brand_name": brand.name,
                    "period": f"Last {days} days",
                    "total_posts": metrics.total_posts,
                    "total_engagement": metrics.total_engagement,
                    "avg_engagement_per_post": metrics.avg_engagement_per_post,
                    "sentiment_distribution": metrics.sentiment_distribution,
                    "sentiment_percentage": metrics.sentiment_percentage,
                    "platform_breakdown": metrics.platform_breakdown,
                    "trending_topics": metrics.trending_topics[:5] if metrics.trending_topics else []
                }
        
        # Fallback to old method if no brand analysis found
        # Parse platform filter
        platform = None
        if platforms:
            try:
                platform_list = [PlatformType(p.strip().lower()) for p in platforms.split(',')]
                platform = platform_list[0] if platform_list else platform
            except:
                pass
        
        # Get posts for analysis
        posts = await db_service.get_posts_by_brand(brand, platform, limit=10000)
        
        # Apply date filtering
        if start_date or end_date:
            try:
                start_dt = datetime.fromisoformat(start_date) if start_date else None
                end_dt = datetime.fromisoformat(end_date) if end_date else None
                
                if start_dt or end_dt:
                    filtered_posts = []
                    for p in posts:
                        if p.posted_at:
                            if start_dt and p.posted_at < start_dt:
                                continue
                            if end_dt and p.posted_at > end_dt:
                                continue
                            filtered_posts.append(p)
                    if filtered_posts:
                        posts = filtered_posts
            except:
                pass
        else:
            # Use days parameter if no date range specified
            cutoff_date = datetime.now() - timedelta(days=days)
            recent_posts = [p for p in posts if p.posted_at and p.posted_at >= cutoff_date]
            if recent_posts:
                posts = recent_posts
        
        # Calculate key metrics
        total_posts = len(posts)
        total_engagement = sum(int(p.like_count or 0) + int(p.comment_count or 0) + int(p.share_count or 0) for p in posts)
        avg_engagement_per_post = total_engagement / total_posts if total_posts > 0 else 0
        
        # Sentiment analysis
        sentiment_counts = {"Positive": 0, "Negative": 0, "Neutral": 0}
        sentiment_scores = []
        
        for post in posts:
            if post.sentiment is not None:
                # Convert SentimentType enum to string for counting
                sentiment_str = post.sentiment.value if hasattr(post.sentiment, 'value') else str(post.sentiment)
                sentiment_scores.append(sentiment_str)
                if sentiment_str == "Positive":
                    sentiment_counts["Positive"] += 1
                elif sentiment_str == "Negative":
                    sentiment_counts["Negative"] += 1
                else:
                    sentiment_counts["Neutral"] += 1
        
        # Calculate sentiment percentages
        total_sentiment_posts = sum(sentiment_counts.values())
        sentiment_percentage = {
            "Positive": round((sentiment_counts["Positive"] / total_sentiment_posts * 100), 1) if total_sentiment_posts > 0 else 0,
            "Negative": round((sentiment_counts["Negative"] / total_sentiment_posts * 100), 1) if total_sentiment_posts > 0 else 0,
            "Neutral": round((sentiment_counts["Neutral"] / total_sentiment_posts * 100), 1) if total_sentiment_posts > 0 else 0
        }
        
        # Platform breakdown
        platform_breakdown = {}
        for post in posts:
            platform_name = post.platform.value
            if platform_name not in platform_breakdown:
                platform_breakdown[platform_name] = {
                    "posts": 0,
                    "engagement": 0,
                    "sentiment": 0
                }
            
            platform_breakdown[platform_name]["posts"] += 1
            platform_breakdown[platform_name]["engagement"] += int(post.like_count or 0) + int(post.comment_count or 0) + int(post.share_count or 0)
            if post.sentiment is not None:
                # Convert SentimentType enum to numeric value for calculation
                sentiment_value = 1 if post.sentiment.value == "Positive" else -1 if post.sentiment.value == "Negative" else 0
                platform_breakdown[platform_name]["sentiment"] += sentiment_value
        
        # Calculate platform-specific metrics
        for platform_data in platform_breakdown.values():
            if platform_data["posts"] > 0:
                platform_data["avg_engagement"] = round(platform_data["engagement"] / platform_data["posts"], 2)
                platform_data["avg_sentiment"] = round(platform_data["sentiment"] / platform_data["posts"], 3)
        
        # Get trending topics
        topic_interests = await db_service.get_trending_topics(brand, limit=10)
        trending_topics = []
        for topic_interest in topic_interests[:10]:  # Top 10 topics
            # Calculate avg_sentiment from available data
            total_mentions = topic_interest.positive_count + topic_interest.negative_count + topic_interest.neutral_count
            avg_sentiment = 0
            if total_mentions > 0:
                avg_sentiment = (topic_interest.positive_count - topic_interest.negative_count) / total_mentions
            
            trending_topics.append({
                "topic": topic_interest.topic,
                "mentions": topic_interest.mention_count,
                "sentiment": round(avg_sentiment, 2),
                "engagement": int(topic_interest.total_likes or 0) + int(topic_interest.total_comments or 0)
            })
        
        return {
            "brand_name": brand.name,
            "period": f"Last {days} days",
            "total_posts": total_posts,
            "total_engagement": total_engagement,
            "avg_engagement_per_post": round(avg_engagement_per_post, 2),
            "sentiment_distribution": sentiment_counts,
            "sentiment_percentage": sentiment_percentage,
            "platform_breakdown": platform_breakdown,
            "trending_topics": trending_topics,
            "brand_health_score": round(sum(sentiment_scores) / len(sentiment_scores), 2) if sentiment_scores else 0
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing brand: {str(e)}")


@router.get("/brands/{brand_identifier}/sentiment-timeline")
async def get_brand_sentiment_timeline(
    brand_identifier: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    platforms: Optional[str] = None,
    days: int = 30
):
    """
    Get brand sentiment timeline for trend analysis
    
    Returns daily sentiment breakdown showing how brand perception
    changes over time across different platforms.
    """
    try:
        # Get brand by identifier
        brand = await get_brand_by_identifier(brand_identifier)
        if not brand:
            raise HTTPException(status_code=404, detail="Brand not found")
        
        # Try to get latest brand analysis
        brand_analyses = await BrandAnalysis.find(
            BrandAnalysis.brand_id == str(brand.id)
        ).sort("-created_at").limit(1).to_list()
        
        # If brand analysis exists, get timeline from new collections
        if brand_analyses:
            analysis = brand_analyses[0]
            timeline_data = await db_service.get_brand_sentiment_timeline(
                str(analysis.id), start_date, end_date
            )
            
            if timeline_data:
                # Convert to frontend format
                timeline_list = []
                for item in timeline_data:
                    timeline_list.append({
                        "date": item.date.strftime("%Y-%m-%d"),
                        "total_posts": item.total_posts,
                        "positive": item.positive_count,
                        "negative": item.negative_count,
                        "neutral": item.neutral_count,
                        "avg_sentiment": round(item.sentiment_score, 3)
                    })
                
                return {
                    "brand_name": brand.name,
                    "platform": "all",
                    "timeline": timeline_list,
                    "summary": {
                        "total_days": len(timeline_list),
                        "avg_sentiment": round(sum(item.sentiment_score for item in timeline_data) / len(timeline_data), 3) if timeline_data else 0
                    }
                }
        
        # Fallback to old method if no brand analysis found
        # Parse platform filter
        platform = None
        if platforms:
            try:
                platform_list = [PlatformType(p.strip().lower()) for p in platforms.split(',')]
                platform = platform_list[0] if platform_list else platform
            except:
                pass
        
        # Get posts for analysis
        posts = await db_service.get_posts_by_brand(brand, platform, limit=10000)
        
        # Apply date filtering
        if start_date or end_date:
            try:
                start_dt = datetime.fromisoformat(start_date) if start_date else None
                end_dt = datetime.fromisoformat(end_date) if end_date else None
                
                if start_dt or end_dt:
                    filtered_posts = []
                    for p in posts:
                        if p.posted_at:
                            if start_dt and p.posted_at < start_dt:
                                continue
                            if end_dt and p.posted_at > end_dt:
                                continue
                            filtered_posts.append(p)
                    if filtered_posts:
                        posts = filtered_posts
            except:
                pass
        else:
            # Use days parameter if no date range specified
            cutoff_date = datetime.now() - timedelta(days=days)
            recent_posts = [p for p in posts if p.posted_at and p.posted_at >= cutoff_date]
            if recent_posts:
                posts = recent_posts
        
        # Build timeline
        timeline = {}
        for post in posts:
            if post.posted_at:
                date_key = post.posted_at.strftime("%Y-%m-%d")
                if date_key not in timeline:
                    timeline[date_key] = {
                        "total_posts": 0,
                        "Positive": 0,
                        "Negative": 0,
                        "Neutral": 0,
                        "total_sentiment": 0
                    }
                
                timeline[date_key]["total_posts"] += 1
                
                if post.sentiment is not None:
                    # Convert SentimentType enum to numeric value for calculation
                    sentiment_value = 1 if post.sentiment.value == "Positive" else -1 if post.sentiment.value == "Negative" else 0
                    timeline[date_key]["total_sentiment"] += sentiment_value
                    if post.sentiment.value == "Positive":
                        timeline[date_key]["Positive"] += 1
                    elif post.sentiment.value == "Negative":
                        timeline[date_key]["Negative"] += 1
                    else:
                        timeline[date_key]["Neutral"] += 1
        
        # Convert to list format for frontend
        timeline_data = []
        for date, data in sorted(timeline.items()):
            timeline_data.append({
                "date": date,
                "total_posts": data["total_posts"],
                "positive": data["Positive"],
                "negative": data["Negative"],
                "neutral": data["Neutral"],
                "avg_sentiment": round(data["total_sentiment"] / data["total_posts"], 3) if data["total_posts"] > 0 else 0
            })
        
        return {
            "brand_name": brand.name,
            "platform": platform.value if platform else "all",
            "timeline": timeline_data,
            "summary": {
                "total_days": len(timeline_data),
                "avg_daily_posts": round(sum(d["total_posts"] for d in timeline_data) / len(timeline_data), 1) if timeline_data else 0,
                "overall_sentiment": round(sum(d["avg_sentiment"] for d in timeline_data) / len(timeline_data), 3) if timeline_data else 0
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting brand sentiment timeline: {str(e)}")


@router.get("/brands/{brand_identifier}/trending-topics")
async def get_brand_trending_topics(
    brand_identifier: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    platforms: Optional[str] = None,
    limit: int = 10
):
    """
    Get trending topics for brand analysis
    
    Returns the most discussed topics related to the brand,
    including sentiment analysis and engagement metrics.
    """
    try:
        # Get brand by identifier
        brand = await get_brand_by_identifier(brand_identifier)
        if not brand:
            raise HTTPException(status_code=404, detail="Brand not found")
        
        # Try to get latest brand analysis
        brand_analyses = await BrandAnalysis.find(
            BrandAnalysis.brand_id == str(brand.id)
        ).sort("-created_at").limit(1).to_list()
        
        # If brand analysis exists, get topics from new collections
        if brand_analyses:
            analysis = brand_analyses[0]
            platform_filter = platforms.split(',')[0] if platforms else None
            trending_topics = await db_service.get_brand_trending_topics(
                str(analysis.id), platform_filter
            )
            
            if trending_topics:
                # Convert to frontend format
                topics_list = []
                for topic in trending_topics[:limit]:
                    topics_list.append({
                        "topic": topic.topic,
                        "count": topic.topic_count,
                        "sentiment": round(topic.sentiment, 2),
                        "engagement": topic.engagement,
                        "positive": topic.positive,
                        "negative": topic.negative,
                        "neutral": topic.neutral,
                        "platform": topic.platform
                    })
                
                return {
                    "brand_name": brand.name,
                    "platform": platform_filter or "all",
                    "topics": topics_list,
                    "summary": {
                        "total_topics": len(topics_list),
                        "avg_sentiment": round(sum(t["sentiment"] for t in topics_list) / len(topics_list), 2) if topics_list else 0
                    }
                }
        
        # Fallback to old method if no brand analysis found
        # Parse platform filter
        platform = None
        if platforms:
            try:
                platform_list = [PlatformType(p.strip().lower()) for p in platforms.split(',')]
                platform = platform_list[0] if platform_list else platform
            except:
                pass
        
        # Get topic interests
        topic_interests = await db_service.get_trending_topics(brand, limit=10)
        
        # Apply date filtering if needed
        if start_date or end_date:
            # Filter topic interests by date range
            start_dt = datetime.fromisoformat(start_date) if start_date else None
            end_dt = datetime.fromisoformat(end_date) if end_date else None
            
            filtered_topics = []
            for topic in topic_interests:
                # Get posts for this topic to check date range
                topic_posts = await db_service.get_posts_by_brand_and_topic(brand, topic.topic, platform)
                
                if start_dt or end_dt:
                    valid_posts = []
                    for post in topic_posts:
                        if post.posted_at:
                            if start_dt and post.posted_at < start_dt:
                                continue
                            if end_dt and post.posted_at > end_dt:
                                continue
                            valid_posts.append(post)
                    
                    if valid_posts:
                        # Recalculate metrics for filtered posts
                        total_mentions = len(valid_posts)
                        total_sentiment = sum(1 if p.sentiment.value == "Positive" else -1 if p.sentiment.value == "Negative" else 0 for p in valid_posts if p.sentiment is not None)
                        total_engagement = sum(int(p.like_count or 0) + int(p.comment_count or 0) + int(p.share_count or 0) for p in valid_posts)
                        
                        filtered_topics.append({
                            "topic": topic.topic,
                            "count": total_mentions,
                            "sentiment": round(total_sentiment / total_mentions, 2) if total_mentions > 0 else 0,
                            "engagement": total_engagement,
                            "positive": len([p for p in valid_posts if p.sentiment and p.sentiment > 0.1]),
                            "negative": len([p for p in valid_posts if p.sentiment and p.sentiment < -0.1]),
                            "neutral": len([p for p in valid_posts if p.sentiment and -0.1 <= p.sentiment <= 0.1])
                        })
                else:
                    filtered_topics.append({
                        "topic": topic.topic,
                        "count": topic.mention_count,
                        "sentiment": round((topic.positive_count - topic.negative_count) / max(topic.positive_count + topic.negative_count + topic.neutral_count, 1), 2),
                        "engagement": topic.total_engagement,
                        "positive": topic.positive_count,
                        "negative": topic.negative_count,
                        "neutral": topic.neutral_count
                    })
            
            # Sort by mention count and limit
            trending_topics = sorted(filtered_topics, key=lambda x: x["count"], reverse=True)[:limit]
        else:
            # Use existing topic interests
            trending_topics = []
            for topic in topic_interests[:limit]:
                trending_topics.append({
                    "topic": topic.topic,
                    "count": topic.mention_count,
                    "sentiment": round(topic.avg_sentiment, 2),
                    "engagement": topic.total_engagement,
                    "positive": topic.positive_count,
                    "negative": topic.negative_count,
                    "neutral": topic.neutral_count
                })
        
        return {
            "brand_name": brand.name,
            "platform": platform.value if platform else "all",
            "trending_topics": trending_topics,
            "total_topics": len(trending_topics)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting brand trending topics: {str(e)}")


@router.get("/brands/{brand_identifier}/engagement-patterns")
async def get_brand_engagement_patterns(
    brand_identifier: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    platforms: Optional[str] = None
):
    """
    Get brand engagement patterns for optimal posting strategy
    
    Analyzes when the brand's audience is most active and engaged,
    providing insights for content scheduling.
    """
    try:
        # Get brand by identifier
        brand = await get_brand_by_identifier(brand_identifier)
        if not brand:
            raise HTTPException(status_code=404, detail="Brand not found")
        
        # Try to get latest brand analysis
        brand_analyses = await BrandAnalysis.find(
            BrandAnalysis.brand_id == str(brand.id)
        ).sort("-created_at").limit(1).to_list()
        
        # If brand analysis exists, get patterns from new collections
        if brand_analyses:
            analysis = brand_analyses[0]
            platform_filter = platforms.split(',')[0] if platforms else None
            engagement_patterns = await db_service.get_brand_engagement_patterns(
                str(analysis.id), platform_filter
            )
            
            if engagement_patterns:
                # Convert to frontend format
                patterns_list = []
                for pattern in engagement_patterns:
                    patterns_list.append({
                        "time_slot": pattern.time_slot,
                        "day_of_week": pattern.day_of_week,
                        "avg_engagement": pattern.avg_engagement,
                        "post_count": pattern.post_count,
                        "platform": pattern.platform
                    })
                
                return {
                    "brand_name": brand.name,
                    "platform": platform_filter or "all",
                    "patterns": patterns_list,
                    "summary": {
                        "total_patterns": len(patterns_list),
                        "best_time": max(patterns_list, key=lambda x: x["avg_engagement"])["time_slot"] if patterns_list else None
                    }
                }
        
        # Fallback to old method if no brand analysis found
        # Parse platform filter
        platform = None
        if platforms:
            try:
                platform_list = [PlatformType(p.strip().lower()) for p in platforms.split(',')]
                platform = platform_list[0] if platform_list else platform
            except:
                pass
        
        # Get posts for analysis
        posts = await db_service.get_posts_by_brand(brand, platform, limit=10000)
        
        # Apply date filtering
        if start_date or end_date:
            try:
                start_dt = datetime.fromisoformat(start_date) if start_date else None
                end_dt = datetime.fromisoformat(end_date) if end_date else None
                
                if start_dt or end_dt:
                    filtered_posts = []
                    for p in posts:
                        if p.posted_at:
                            if start_dt and p.posted_at < start_dt:
                                continue
                            if end_dt and p.posted_at > end_dt:
                                continue
                            filtered_posts.append(p)
                    if filtered_posts:
                        posts = filtered_posts
            except:
                pass
        
        # Convert posts to DataFrame for analysis
        import pandas as pd
        posts_data = []
        for post in posts:
            # Use posted_at if available, otherwise use created_at or current time
            posted_at = post.posted_at
            if not posted_at and hasattr(post, 'created_at') and post.created_at:
                posted_at = post.created_at
            elif not posted_at:
                from datetime import datetime
                posted_at = datetime.now()
            
            posts_data.append({
                'like_count': post.like_count or 0,
                'comment_count': post.comment_count or 0,
                'share_count': post.share_count or 0,
                'view_count': getattr(post, 'view_count', 1) or 1,
                'posted_at': posted_at
            })
        
        df = pd.DataFrame(posts_data)
        engagement_patterns = analyze_engagement_patterns(df)
        
        return {
            "brand_name": brand.name,
            "platform": platform.value if platform else "all",
            "peak_hours": engagement_patterns.get("peak_hours", []),
            "active_days": engagement_patterns.get("active_days", []),
            "avg_engagement_rate": engagement_patterns.get("avg_engagement_rate", 0.0),
            "total_posts": engagement_patterns.get("total_posts", 0)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing brand engagement patterns: {str(e)}")


@router.get("/brands/{brand_identifier}/performance")
async def get_brand_performance_metrics(
    brand_identifier: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    platforms: Optional[str] = None,
    days: int = 30
):
    """
    Get brand performance metrics for ROI analysis
    
    Provides comprehensive performance data including reach, impressions,
    engagement rates, and conversion metrics.
    """
    try:
        # Get brand by identifier
        brand = await get_brand_by_identifier(brand_identifier)
        if not brand:
            raise HTTPException(status_code=404, detail="Brand not found")
        
        # Try to get latest brand analysis
        brand_analyses = await BrandAnalysis.find(
            BrandAnalysis.brand_id == str(brand.id)
        ).sort("-created_at").limit(1).to_list()
        
        # If brand analysis exists, get performance from new collections
        if brand_analyses:
            analysis = brand_analyses[0]
            platform_filter = platforms.split(',')[0] if platforms else None
            performance_data = await db_service.get_brand_performance(
                str(analysis.id), platform_filter
            )
            
            if performance_data:
                # Convert to frontend format
                performance_list = []
                for perf in performance_data:
                    performance_list.append({
                        "metric": perf.metric,
                        "value": perf.value,
                        "trend": perf.trend,
                        "platform": perf.platform,
                        "period": perf.period
                    })
                
                return {
                    "brand_name": brand.name,
                    "platform": platform_filter or "all",
                    "performance": performance_list,
                    "summary": {
                        "total_metrics": len(performance_list),
                        "avg_performance": round(sum(p["value"] for p in performance_list) / len(performance_list), 2) if performance_list else 0
                    }
                }
        
        # Fallback to old method if no brand analysis found
        # Parse platform filter
        platform = None
        if platforms:
            try:
                platform_list = [PlatformType(p.strip().lower()) for p in platforms.split(',')]
                platform = platform_list[0] if platform_list else platform
            except:
                pass
        
        # Get posts for analysis
        posts = await db_service.get_posts_by_brand(brand, platform, limit=10000)
        
        # Apply date filtering
        if start_date or end_date:
            try:
                start_dt = datetime.fromisoformat(start_date) if start_date else None
                end_dt = datetime.fromisoformat(end_date) if end_date else None
                
                if start_dt or end_dt:
                    filtered_posts = []
                    for p in posts:
                        if p.posted_at:
                            if start_dt and p.posted_at < start_dt:
                                continue
                            if end_dt and p.posted_at > end_dt:
                                continue
                            filtered_posts.append(p)
                    if filtered_posts:
                        posts = filtered_posts
            except:
                pass
        else:
            # Use days parameter if no date range specified
            cutoff_date = datetime.now() - timedelta(days=days)
            recent_posts = [p for p in posts if p.posted_at and p.posted_at >= cutoff_date]
            if recent_posts:
                posts = recent_posts
        
        # Calculate performance metrics
        total_posts = len(posts)
        total_likes = sum(p.like_count for p in posts)
        total_comments = sum(p.comment_count for p in posts)
        total_shares = sum(p.share_count for p in posts)
        total_engagement = total_likes + total_comments + total_shares
        
        # Calculate averages
        avg_likes_per_post = total_likes / total_posts if total_posts > 0 else 0
        avg_comments_per_post = total_comments / total_posts if total_posts > 0 else 0
        avg_shares_per_post = total_shares / total_posts if total_posts > 0 else 0
        avg_engagement_per_post = total_engagement / total_posts if total_posts > 0 else 0
        
        # Engagement rate calculation: total_engagement / total_posts
        estimated_reach = total_engagement * 10  # Assuming 10x multiplier for reach
        engagement_rate = (total_engagement / total_posts) if total_posts > 0 else 0
        
        # Platform breakdown
        platform_breakdown = {}
        for post in posts:
            platform_name = post.platform.value
            if platform_name not in platform_breakdown:
                platform_breakdown[platform_name] = {
                    'posts': 0,
                    'engagement': 0,
                    'likes': 0,
                    'comments': 0,
                    'shares': 0
                }
            
            platform_breakdown[platform_name]['posts'] += 1
            platform_breakdown[platform_name]['engagement'] += int(post.like_count or 0) + int(post.comment_count or 0) + int(post.share_count or 0)
            platform_breakdown[platform_name]['likes'] += post.like_count
            platform_breakdown[platform_name]['comments'] += post.comment_count
            platform_breakdown[platform_name]['shares'] += post.share_count
        
        # Calculate platform-specific engagement rates
        for platform_data in platform_breakdown.values():
            platform_data['avg_engagement_per_post'] = platform_data['engagement'] / platform_data['posts'] if platform_data['posts'] > 0 else 0
        
        return {
            "brand_name": brand.name,
            "period": f"Last {days} days",
            "platform": platform.value if platform else "all",
            "total_posts": total_posts,
            "total_engagement": total_engagement,
            "total_likes": total_likes,
            "total_comments": total_comments,
            "total_shares": total_shares,
            "avg_engagement_per_post": round(avg_engagement_per_post, 2),
            "avg_likes_per_post": round(avg_likes_per_post, 2),
            "avg_comments_per_post": round(avg_comments_per_post, 2),
            "avg_shares_per_post": round(avg_shares_per_post, 2),
            "engagement_rate": round(engagement_rate, 2),
            "estimated_reach": estimated_reach,
            "platform_breakdown": platform_breakdown
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing brand performance: {str(e)}")


@router.get("/brands/{brand_identifier}/emotions")
async def get_brand_emotion_analysis(
    brand_identifier: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    platforms: Optional[str] = None
):
    """
    Get brand emotion analysis for audience insights
    
    Analyzes emotional responses to brand content across different
    platforms to understand audience sentiment and engagement.
    """
    try:
        # Get brand by identifier
        brand = await get_brand_by_identifier(brand_identifier)
        if not brand:
            raise HTTPException(status_code=404, detail="Brand not found")
        
        # Try to get latest brand analysis
        brand_analyses = await BrandAnalysis.find(
            BrandAnalysis.brand_id == str(brand.id)
        ).sort("-created_at").limit(1).to_list()
        
        # If brand analysis exists, get emotions from new collections
        if brand_analyses:
            analysis = brand_analyses[0]
            platform_filter = platforms.split(',')[0] if platforms else None
            emotions_data = await db_service.get_brand_emotions(
                str(analysis.id), platform_filter
            )
            
            if emotions_data:
                # Convert to frontend format
                emotions_list = []
                for emotion in emotions_data:
                    emotions_list.append({
                        "emotion": emotion.emotion,
                        "count": emotion.count,
                        "percentage": emotion.percentage,
                        "platform": emotion.platform
                    })
                
                return {
                    "brand_name": brand.name,
                    "platform": platform_filter or "all",
                    "emotions": emotions_list,
                    "summary": {
                        "total_emotions": len(emotions_list),
                        "dominant_emotion": max(emotions_list, key=lambda x: x["count"])["emotion"] if emotions_list else "neutral"
                    }
                }
        
        # Fallback to old method if no brand analysis found
        # Parse platform filter
        platform = None
        if platforms:
            try:
                platform_list = [PlatformType(p.strip().lower()) for p in platforms.split(',')]
                platform = platform_list[0] if platform_list else platform
            except:
                pass
        
        # Get posts for analysis
        posts = await db_service.get_posts_by_brand(brand, platform, limit=10000)
        
        # Apply date filtering
        if start_date or end_date:
            try:
                start_dt = datetime.fromisoformat(start_date) if start_date else None
                end_dt = datetime.fromisoformat(end_date) if end_date else None
                
                if start_dt or end_dt:
                    filtered_posts = []
                    for p in posts:
                        if p.posted_at:
                            if start_dt and p.posted_at < start_dt:
                                continue
                            if end_dt and p.posted_at > end_dt:
                                continue
                            filtered_posts.append(p)
                    if filtered_posts:
                        posts = filtered_posts
            except:
                pass
        
        # Analyze emotions
        emotion_counts = {}
        total_posts = len(posts)
        
        for post in posts:
            if post.emotion:
                emotion = post.emotion.lower()
                if emotion not in emotion_counts:
                    emotion_counts[emotion] = 0
                emotion_counts[emotion] += 1
        
        # Calculate emotion percentages
        emotion_percentages = {}
        for emotion, count in emotion_counts.items():
            emotion_percentages[emotion] = round((count / total_posts * 100), 1) if total_posts > 0 else 0
        
        # Find dominant emotion
        dominant_emotion = max(emotion_counts.items(), key=lambda x: x[1])[0] if emotion_counts else "neutral"
        
        return {
            "brand_name": brand.name,
            "platform": platform.value if platform else "all",
            "total_analyzed": total_posts,
            "emotion_distribution": emotion_counts,
            "emotion_percentages": emotion_percentages,
            "dominant_emotion": dominant_emotion,
            "emotion_insights": {
                "most_positive_emotion": max(emotion_counts.items(), key=lambda x: x[1])[0] if emotion_counts else "neutral",
                "emotion_diversity": len(emotion_counts),
                "engagement_by_emotion": emotion_counts  # Simplified - in real implementation, calculate engagement per emotion
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing brand emotions: {str(e)}")


@router.get("/brands/{brand_identifier}/demographics")
async def get_brand_demographics(
    brand_identifier: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    platforms: Optional[str] = None
):
    """
    Get brand audience demographics for targeting insights
    
    Provides detailed demographic breakdown of the brand's audience
    including age groups, gender distribution, and geographic data.
    """
    try:
        # Get brand by identifier
        brand = await get_brand_by_identifier(brand_identifier)
        if not brand:
            raise HTTPException(status_code=404, detail="Brand not found")
        
        # Try to get latest brand analysis
        brand_analyses = await BrandAnalysis.find(
            BrandAnalysis.brand_id == str(brand.id)
        ).sort("-created_at").limit(1).to_list()
        
        # If brand analysis exists, get demographics from new collections
        if brand_analyses:
            analysis = brand_analyses[0]
            platform_filter = platforms.split(',')[0] if platforms else None
            demographics_data = await db_service.get_brand_demographics(
                str(analysis.id), platform_filter
            )
            
            if demographics_data:
                # Convert to frontend format
                demographics_list = []
                for demo in demographics_data:
                    demographics_list.append({
                        "category": demo.category,
                        "value": demo.value,
                        "count": demo.count,
                        "percentage": demo.percentage,
                        "platform": demo.platform
                    })
                
                return {
                    "brand_name": brand.name,
                    "platform": platform_filter or "all",
                    "demographics": demographics_list,
                    "summary": {
                        "total_categories": len(demographics_list),
                        "most_common": max(demographics_list, key=lambda x: x["count"])["value"] if demographics_list else "unknown"
                    }
                }
        
        # Fallback to old method if no brand analysis found
        # Parse platform filter
        platform = None
        if platforms:
            try:
                platform_list = [PlatformType(p.strip().lower()) for p in platforms.split(',')]
                platform = platform_list[0] if platform_list else platform
            except:
                pass
        
        # Get posts for analysis
        posts = await db_service.get_posts_by_brand(brand, platform, limit=10000)
        
        # Apply date filtering
        if start_date or end_date:
            try:
                start_dt = datetime.fromisoformat(start_date) if start_date else None
                end_dt = datetime.fromisoformat(end_date) if end_date else None
                
                if start_dt or end_dt:
                    filtered_posts = []
                    for p in posts:
                        if p.posted_at:
                            if start_dt and p.posted_at < start_dt:
                                continue
                            if end_dt and p.posted_at > end_dt:
                                continue
                            filtered_posts.append(p)
                    if filtered_posts:
                        posts = filtered_posts
            except:
                pass
        
        # Analyze demographics
        age_groups = {}
        genders = {}
        locations = {}
        total_analyzed = 0
        
        for post in posts:
            if post.author_age_group or post.author_gender or post.author_location_hint:
                total_analyzed += 1
                
                # Age groups
                if post.author_age_group:
                    age_group = post.author_age_group
                    if age_group not in age_groups:
                        age_groups[age_group] = 0
                    age_groups[age_group] += 1
                
                # Gender
                if post.author_gender:
                    gender = post.author_gender.lower()
                    if gender not in genders:
                        genders[gender] = 0
                    genders[gender] += 1
                
                # Location
                if post.author_location_hint:
                    location = post.author_location_hint
                    if location not in locations:
                        locations[location] = 0
                    locations[location] += 1
        
        # Convert to percentage format
        age_group_data = []
        for age_group, count in age_groups.items():
            age_group_data.append({
                "age_group": age_group,
                "count": count,
                "percentage": round((count / total_analyzed * 100), 2) if total_analyzed > 0 else 0
            })
        
        gender_data = []
        for gender, count in genders.items():
            gender_data.append({
                "gender": gender,
                "count": count,
                "percentage": round((count / total_analyzed * 100), 2) if total_analyzed > 0 else 0
            })
        
        # Top locations
        top_locations = []
        for location, count in sorted(locations.items(), key=lambda x: x[1], reverse=True)[:10]:
            top_locations.append({
                "location": location,
                "count": count,
                "percentage": round((count / total_analyzed * 100), 2) if total_analyzed > 0 else 0
            })
        
        return {
            "brand_name": brand.name,
            "platform": platform.value if platform else "all",
            "total_analyzed": total_analyzed,
            "age_groups": age_group_data,
            "genders": gender_data,
            "top_locations": top_locations
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing brand demographics: {str(e)}")


@router.get("/brands/{brand_identifier}/competitive")
async def get_brand_competitive_analysis(
    brand_identifier: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    platforms: Optional[str] = None
):
    """
    Get brand competitive analysis for market positioning
    
    Provides insights into how the brand performs compared to competitors
    and market benchmarks, including recommendations for improvement.
    """
    try:
        # Get brand by identifier
        brand = await get_brand_by_identifier(brand_identifier)
        if not brand:
            raise HTTPException(status_code=404, detail="Brand not found")
        
        # Parse platform filter
        platform = None
        if platforms:
            try:
                platform_list = [PlatformType(p.strip().lower()) for p in platforms.split(',')]
                platform = platform_list[0] if platform_list else platform
            except:
                pass
        
        # Get brand posts for analysis
        brand_posts = await db_service.get_posts_by_brand(brand, platform, limit=10000)
        
        # Apply date filtering
        if start_date or end_date:
            try:
                start_dt = datetime.fromisoformat(start_date) if start_date else None
                end_dt = datetime.fromisoformat(end_date) if end_date else None
                
                if start_dt or end_dt:
                    filtered_posts = []
                    for p in brand_posts:
                        if p.posted_at:
                            if start_dt and p.posted_at < start_dt:
                                continue
                            if end_dt and p.posted_at > end_dt:
                                continue
                            filtered_posts.append(p)
                    if filtered_posts:
                        brand_posts = filtered_posts
            except:
                pass
        
        # Calculate brand metrics
        brand_total_posts = len(brand_posts)
        brand_total_engagement = sum(int(p.like_count or 0) + int(p.comment_count or 0) + int(p.share_count or 0) for p in brand_posts)
        brand_avg_engagement = brand_total_engagement / brand_total_posts if brand_total_posts > 0 else 0
        
        # Calculate brand sentiment
        brand_sentiment_scores = [1 if p.sentiment.value == "Positive" else -1 if p.sentiment.value == "Negative" else 0 for p in brand_posts if p.sentiment is not None]
        brand_avg_sentiment = sum(brand_sentiment_scores) / len(brand_sentiment_scores) if brand_sentiment_scores else 0
        
        # Calculate industry benchmarks from actual data
        all_posts = await db_service.get_all_posts(limit=10000)
        if all_posts:
            # Calculate industry averages from real data
            industry_engagement_rates = []
            industry_sentiment_scores = []
            
            for post in all_posts:
                if post.like_count and post.comment_count and post.share_count:
                    total_engagement = post.like_count + post.comment_count + post.share_count
                    estimated_reach = total_engagement * 10  # Assuming 10x multiplier
                    engagement_rate = (total_engagement / 1) if 1 > 0 else 0  # Simplified for industry calculation
                    industry_engagement_rates.append(engagement_rate)
                
                if post.sentiment is not None:
                    industry_sentiment_scores.append(post.sentiment)
            
            # Calculate averages
            avg_engagement_rate = sum(industry_engagement_rates) / len(industry_engagement_rates) if industry_engagement_rates else 3.5
            avg_sentiment_score = sum(industry_sentiment_scores) / len(industry_sentiment_scores) if industry_sentiment_scores else 0.65
            avg_posts_per_month = len(all_posts) // 12 if all_posts else 50
            avg_reach = sum(industry_engagement_rates) * 10 if industry_engagement_rates else 10000
        else:
            # Fallback to reasonable defaults if no data available
            avg_engagement_rate = 3.5
            avg_sentiment_score = 0.65
            avg_posts_per_month = 50
            avg_reach = 10000
        
        industry_benchmarks = {
            "avg_posts_per_month": avg_posts_per_month,
            "avg_engagement_rate": round(avg_engagement_rate, 2),
            "avg_sentiment_score": round(avg_sentiment_score, 3),
            "avg_reach": round(avg_reach, 0)
        }
        
        # Calculate performance vs benchmarks
        posts_per_month = brand_total_posts  # Simplified calculation
        engagement_rate = (brand_total_engagement / brand_total_posts) if brand_total_posts > 0 else 0
        
        performance_vs_benchmark = {
            "posts_performance": "above" if posts_per_month > industry_benchmarks["avg_posts_per_month"] else "below",
            "engagement_performance": "above" if engagement_rate > industry_benchmarks["avg_engagement_rate"] else "below",
            "sentiment_performance": "above" if brand_avg_sentiment > industry_benchmarks["avg_sentiment_score"] else "below"
        }
        
        # Generate recommendations
        recommendations = []
        if posts_per_month < industry_benchmarks["avg_posts_per_month"]:
            recommendations.append("Increase posting frequency to match industry standards")
        if engagement_rate < industry_benchmarks["avg_engagement_rate"]:
            recommendations.append("Focus on creating more engaging content")
        if brand_avg_sentiment < industry_benchmarks["avg_sentiment_score"]:
            recommendations.append("Improve content sentiment through better messaging")
        
        return {
            "brand_name": brand.name,
            "platform": platform.value if platform else "all",
            "brand_metrics": {
                "total_posts": brand_total_posts,
                "total_engagement": brand_total_engagement,
                "avg_engagement_per_post": round(brand_avg_engagement, 2),
                "avg_sentiment": round(brand_avg_sentiment, 3)
            },
            "industry_benchmarks": industry_benchmarks,
            "performance_vs_benchmark": performance_vs_benchmark,
            "market_position": "leader" if all(v == "above" for v in performance_vs_benchmark.values()) else "follower",
            "recommendations": recommendations
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing brand competitive position: {str(e)}")


# ============= CONTENT ANALYSIS ENDPOINTS =============

@router.get("/contents/{content_id}/summary")
async def get_content_analysis_summary(
    content_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    platforms: Optional[str] = None,
    days: int = 30
):
    """
    Get comprehensive content analysis summary
    
    This endpoint provides key metrics and insights for individual content analysis including:
    - Content performance metrics
    - Engagement analysis
    - Sentiment breakdown
    - Audience insights
    - Content health indicators
    """
    try:
        # Get content analysis by ID
        from beanie import PydanticObjectId
        from app.models.database import ContentAnalysis, Brand
        content = await ContentAnalysis.get(PydanticObjectId(content_id))
        if not content:
            raise HTTPException(status_code=404, detail="Content not found")
        
        # Parse platform filter
        platform = None
        if platforms:
            try:
                platform_list = [PlatformType(p.strip().lower()) for p in platforms.split(',')]
                platform = platform_list[0] if platform_list else platform
            except:
                pass
        
        # For content analysis, we should NOT use brand posts for benchmark
        # Content analysis should be independent of brand analysis
        related_posts = []
        # Note: Content analysis should focus on individual content performance
        # without comparing to brand posts to avoid data contamination
        
        # Apply date filtering
        if start_date or end_date:
            try:
                start_dt = datetime.fromisoformat(start_date) if start_date else None
                end_dt = datetime.fromisoformat(end_date) if end_date else None
                
                if start_dt or end_dt:
                    filtered_posts = []
                    for p in related_posts:
                        if p.posted_at:
                            if start_dt and p.posted_at < start_dt:
                                continue
                            if end_dt and p.posted_at > end_dt:
                                continue
                            filtered_posts.append(p)
                    if filtered_posts:
                        related_posts = filtered_posts
            except:
                pass
        else:
            # Use days parameter if no date range specified
            cutoff_date = datetime.now() - timedelta(days=days)
            recent_posts = [p for p in related_posts if p.posted_at and p.posted_at >= cutoff_date]
            if recent_posts:
                related_posts = recent_posts
        
        # Calculate content-specific metrics from ContentAnalysis
        content_engagement = content.engagement_score or 0
        content_sentiment = content.sentiment_overall or 0
        
        # For content analysis, use industry benchmarks instead of brand posts
        # This ensures content analysis is independent of brand analysis
        industry_engagement_benchmark = 100  # Industry average engagement
        industry_sentiment_benchmark = 0.1   # Industry average sentiment
        
        # Performance comparison against industry benchmarks
        engagement_performance = "above" if content_engagement > industry_engagement_benchmark else "below"
        sentiment_performance = "above" if content_sentiment > industry_sentiment_benchmark else "below"
        
        # Content health score
        health_score = content.content_health_score or 0
        if health_score == 0:
            # Calculate health score if not set
            if content_engagement > industry_engagement_benchmark:
                health_score += 40
            if content_sentiment > industry_sentiment_benchmark:
                health_score += 30
            if content.engagement_score and content.engagement_score > 0:
                health_score += 15
            if content.reach_estimate and content.reach_estimate > 0:
                health_score += 15
        
        # Convert content analysis data to frontend-compatible format
        # Map sentiment to distribution format
        sentiment_distribution = {"Positive": 0, "Negative": 0, "Neutral": 0}
        sentiment_percentage = {"Positive": 0, "Negative": 0, "Neutral": 0}
        
        if content_sentiment > 0.1:
            sentiment_distribution["Positive"] = 1
            sentiment_percentage["Positive"] = 100
        elif content_sentiment < -0.1:
            sentiment_distribution["Negative"] = 1
            sentiment_percentage["Negative"] = 100
        else:
            sentiment_distribution["Neutral"] = 1
            sentiment_percentage["Neutral"] = 100
        
        # Create trending topics from content analysis
        trending_topics = []
        if content.dominant_topic:
            trending_topics.append({
                "topic": content.dominant_topic,
                "count": 1,
                "sentiment": content_sentiment,
                "engagement": content_engagement,
                "positive": 1 if content_sentiment > 0.1 else 0,
                "negative": 1 if content_sentiment < -0.1 else 0,
                "neutral": 1 if -0.1 <= content_sentiment <= 0.1 else 0
            })
        
        # Create platform breakdown
        platform_breakdown = {
            content.platform.value: {
                "posts": 1,
                "engagement": content_engagement,
                "sentiment": content_sentiment
            }
        }
        
        return {
            # Frontend-compatible format
            "brand_name": content.title,  # Use content title as brand name for compatibility
            "total_posts": 1,  # Single content analysis
            "total_engagement": content_engagement,
            "avg_engagement_per_post": content_engagement,
            "engagement_rate": round(content_engagement / 100, 2),  # Convert to percentage
            "sentiment_distribution": sentiment_distribution,
            "sentiment_percentage": sentiment_percentage,
            "platform_breakdown": platform_breakdown,
            "trending_topics": trending_topics,
            "brand_health_score": health_score,
            
            # Additional content-specific data
            "content_id": content_id,
            "content_title": content.title,
            "platform": content.platform.value,
            "period": f"Last {days} days",
            "content_metrics": {
                "likes": 0,  # ContentAnalysis doesn't have like_count
                "comments": 0,  # ContentAnalysis doesn't have comment_count
                "shares": 0,  # ContentAnalysis doesn't have share_count
                "total_engagement": content_engagement,
                "sentiment": round(content_sentiment, 3),
                "engagement_rate": round(content_engagement / 1, 2),
                "reach_estimate": content.reach_estimate or 0,
                "virality_score": content.virality_score or 0
            },
            "benchmark_comparison": {
                "engagement_performance": engagement_performance,
                "sentiment_performance": sentiment_performance,
                "industry_engagement_benchmark": industry_engagement_benchmark,
                "industry_sentiment_benchmark": industry_sentiment_benchmark,
                "benchmark_type": "industry"
            },
            "content_health_score": health_score,
            "content_insights": {
                "best_performing_metric": "engagement" if content.engagement_score and content.engagement_score > 0 else "reach" if content.reach_estimate and content.reach_estimate > 0 else "virality",
                "engagement_trend": "positive" if content_engagement > industry_engagement_benchmark else "negative",
                "sentiment_category": "positive" if content_sentiment > 0.1 else "negative" if content_sentiment < -0.1 else "neutral",
                "dominant_topic": content.dominant_topic or "general",
                "dominant_emotion": content.dominant_emotion or "neutral"
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing content: {str(e)}")


@router.get("/contents/{content_id}/sentiment-timeline")
async def get_content_sentiment_timeline(
    content_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    platforms: Optional[str] = None,
    days: int = 30
):
    """
    Get content sentiment timeline for trend analysis
    
    Returns sentiment analysis over time for the specific content,
    showing how audience perception changes.
    """
    try:
        # Get content analysis by ID
        from beanie import PydanticObjectId
        from app.models.database import ContentAnalysis
        content = await ContentAnalysis.get(PydanticObjectId(content_id))
        if not content:
            raise HTTPException(status_code=404, detail="Content not found")
        
        # For individual content, we'll analyze sentiment over time based on content analysis data
        # This is a simplified implementation - in real scenario, you'd track sentiment changes
        
        # Get content creation date
        content_date = content.created_at
        
        # Create timeline data (simplified - in real implementation, track actual sentiment changes)
        timeline_data = []
        
        # Generate timeline for the past days
        for i in range(days):
            date = datetime.now() - timedelta(days=i)
            date_key = date.strftime("%Y-%m-%d")
            
            # Simulate sentiment variation over time
            base_sentiment = content.sentiment_overall or 0
            variation = (i % 3 - 1) * 0.1  # Simple variation pattern
            daily_sentiment = base_sentiment + variation
            
            timeline_data.append({
                "date": date_key,
                "sentiment": round(daily_sentiment, 3),
                "engagement": content.engagement_score or 0,
                "mentions": 1 if i == 0 else 0  # Content was mentioned on creation day
            })
        
        # Sort by date
        timeline_data.sort(key=lambda x: x["date"])
        
        return {
            "content_id": content_id,
            "platform": content.platform.value,
            "timeline": timeline_data,
            "summary": {
                "total_days": len(timeline_data),
                "avg_sentiment": round(sum(d["sentiment"] for d in timeline_data) / len(timeline_data), 3),
                "sentiment_trend": "stable"  # Simplified - in real implementation, calculate actual trend
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting content sentiment timeline: {str(e)}")


@router.get("/contents/{content_id}/trending-topics")
async def get_content_trending_topics(
    content_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    platforms: Optional[str] = None,
    limit: int = 10
):
    """
    Get trending topics related to content analysis
    
    Returns topics and keywords related to the content,
    including sentiment analysis and engagement metrics.
    """
    try:
        # Get content by ID
        from beanie import PydanticObjectId
        from app.models.database import ContentAnalysis
        content = await ContentAnalysis.get(PydanticObjectId(content_id))
        if not content:
            raise HTTPException(status_code=404, detail="Content not found")
        
        # Get related topics from content analysis
        content_topic = content.dominant_topic if content.dominant_topic else "general"
        
        # For content analysis, we don't need related posts from brand
        # Content analysis should be independent
        related_posts = []
        
        # Apply date filtering
        if start_date or end_date:
            try:
                start_dt = datetime.fromisoformat(start_date) if start_date else None
                end_dt = datetime.fromisoformat(end_date) if end_date else None
                
                if start_dt or end_dt:
                    filtered_posts = []
                    for p in related_posts:
                        if p.posted_at:
                            if start_dt and p.posted_at < start_dt:
                                continue
                            if end_dt and p.posted_at > end_dt:
                                continue
                            filtered_posts.append(p)
                    if filtered_posts:
                        related_posts = filtered_posts
            except:
                pass
        
        # For content analysis, use content's own topic data
        trending_topics = []
        
        # Get topics from content analysis
        if content.topics and len(content.topics) > 0:
            for topic_data in content.topics:
                if isinstance(topic_data, dict) and "topic" in topic_data:
                    trending_topics.append({
                        "topic": topic_data["topic"],
                        "count": 1,
                        "sentiment": topic_data.get("sentiment", 0),
                        "engagement": content.engagement_score or 0,
                        "positive": 1 if topic_data.get("sentiment", 0) > 0 else 0,
                        "negative": 1 if topic_data.get("sentiment", 0) < 0 else 0,
                        "neutral": 1 if topic_data.get("sentiment", 0) == 0 else 0
                    })
        else:
            # Fallback to content's dominant topic
            if content.dominant_topic:
                trending_topics.append({
                    "topic": content.dominant_topic,
                    "count": 1,
                    "sentiment": content.sentiment_overall or 0,
                    "engagement": content.engagement_score or 0,
                    "positive": 1 if (content.sentiment_overall or 0) > 0 else 0,
                    "negative": 1 if (content.sentiment_overall or 0) < 0 else 0,
                    "neutral": 1 if (content.sentiment_overall or 0) == 0 else 0
                })
        
        # Sort by engagement and limit
        trending_topics.sort(key=lambda x: x["engagement"], reverse=True)
        trending_topics = trending_topics[:limit]
        
        return {
            "content_id": content_id,
            "platform": content.platform.value,
            "trending_topics": trending_topics,
            "total_topics": len(trending_topics),
            "content_topic": content_topic
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting content trending topics: {str(e)}")


@router.get("/contents/{content_id}/engagement-patterns")
async def get_content_engagement_patterns(
    content_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    platforms: Optional[str] = None
):
    """
    Get content engagement patterns for optimization insights
    
    Analyzes when the content performs best and provides
    insights for content scheduling and optimization.
    """
    try:
        # Get content by ID
        from beanie import PydanticObjectId
        from app.models.database import ContentAnalysis
        content = await ContentAnalysis.get(PydanticObjectId(content_id))
        if not content:
            raise HTTPException(status_code=404, detail="Content not found")
        
        # Get content creation time
        content_time = content.created_at
        
        # Analyze engagement patterns based on content timing
        hour = content_time.hour if content_time else 12
        day_of_week = content_time.strftime("%A") if content_time else "Monday"
        
        # Generate engagement pattern insights
        peak_hours = [f"{hour:02d}:00", f"{(hour + 1) % 24:02d}:00", f"{(hour + 2) % 24:02d}:00"]
        active_days = [day_of_week, "Tuesday", "Wednesday"]  # Simplified pattern
        
        # Calculate engagement rate: total_engagement / total_posts (for content, we use 1 as total_posts)
        total_engagement = content.engagement_score or 0
        engagement_rate = total_engagement / 1 if 1 > 0 else 0
        
        return {
            "content_id": content_id,
            "platform": content.platform.value,
            "peak_hours": peak_hours,
            "active_days": active_days,
            "avg_engagement_rate": round(engagement_rate, 2),
            "content_performance": {
                "best_hour": f"{hour:02d}:00",
                "best_day": day_of_week,
                "engagement_score": min(100, engagement_rate * 10),  # Scale to 0-100
                "viral_potential": "high" if engagement_rate > 5 else "medium" if engagement_rate > 2 else "low"
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing content engagement patterns: {str(e)}")


@router.get("/contents/{content_id}/performance")
async def get_content_performance_metrics(
    content_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    platforms: Optional[str] = None,
    days: int = 30
):
    """
    Get content performance metrics for ROI analysis
    
    Provides comprehensive performance data for individual content
    including reach, impressions, engagement rates, and conversion metrics.
    """
    try:
        # Get content by ID
        from beanie import PydanticObjectId
        from app.models.database import ContentAnalysis
        content = await ContentAnalysis.get(PydanticObjectId(content_id))
        if not content:
            raise HTTPException(status_code=404, detail="Content not found")
        
        # Calculate content performance metrics
        total_engagement = content.engagement_score or 0
        view_count = content.reach_estimate or 1000
        
        # Calculate engagement rate: total_engagement / total_posts (for content, we use 1 as total_posts)
        engagement_rate = total_engagement / 1 if 1 > 0 else 0
        
        # Calculate reach (estimated)
        estimated_reach = content.reach_estimate or 1000
        
        # Calculate conversion metrics (simplified)
        conversion_rate = (content.virality_score or 0) * 100 if view_count > 0 else 0
        
        # Performance breakdown by metric (simplified for content analysis)
        performance_breakdown = {
            "engagement": {
                "score": content.engagement_score or 0,
                "rate": round((content.engagement_score or 0) / view_count * 100, 2) if view_count > 0 else 0,
                "impact": "high" if (content.engagement_score or 0) > view_count * 0.05 else "medium" if (content.engagement_score or 0) > view_count * 0.02 else "low"
            },
            "reach": {
                "estimate": content.reach_estimate or 0,
                "rate": round((content.reach_estimate or 0) / view_count * 100, 2) if view_count > 0 else 0,
                "impact": "high" if (content.reach_estimate or 0) > view_count * 0.8 else "medium" if (content.reach_estimate or 0) > view_count * 0.5 else "low"
            },
            "virality": {
                "score": content.virality_score or 0,
                "rate": round((content.virality_score or 0) * 100, 2),
                "impact": "high" if (content.virality_score or 0) > 0.1 else "medium" if (content.virality_score or 0) > 0.05 else "low"
            }
        }
        
        return {
            "content_id": content_id,
            "platform": content.platform.value,
            "period": f"Last {days} days",
            "performance_metrics": {
                "views": view_count,
                "likes": 0,  # ContentAnalysis doesn't have like_count
                "comments": 0,  # ContentAnalysis doesn't have comment_count
                "shares": 0,  # ContentAnalysis doesn't have share_count
                "total_engagement": total_engagement,
                "engagement_rate": round(engagement_rate, 2),
                "estimated_reach": round(estimated_reach, 0),
                "conversion_rate": round(conversion_rate, 2)
            },
            "performance_breakdown": performance_breakdown,
            "content_insights": {
                "best_performing_metric": "engagement",  # Simplified for content analysis
                "engagement_quality": "high" if engagement_rate > 5 else "medium" if engagement_rate > 2 else "low",
                "viral_potential": "high" if (content.virality_score or 0) > 0.1 else "medium" if (content.virality_score or 0) > 0.05 else "low"
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing content performance: {str(e)}")


@router.get("/contents/{content_id}/emotions")
async def get_content_emotion_analysis(
    content_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    platforms: Optional[str] = None
):
    """
    Get content emotion analysis for audience insights
    
    Analyzes emotional responses to the specific content to understand
    audience sentiment and engagement patterns.
    """
    try:
        # Get content by ID
        from beanie import PydanticObjectId
        from app.models.database import ContentAnalysis
        content = await ContentAnalysis.get(PydanticObjectId(content_id))
        if not content:
            raise HTTPException(status_code=404, detail="Content not found")
        
        # Analyze content emotion
        content_emotion = content.dominant_emotion if content.dominant_emotion else "neutral"
        content_sentiment = content.sentiment_overall or 0
        
        # Generate emotion insights based on content performance
        emotion_insights = {
            "primary_emotion": content_emotion,
            "emotion_confidence": min(100, abs(content_sentiment) * 100),  # Convert sentiment to confidence
            "emotional_impact": "high" if abs(content_sentiment) > 0.5 else "medium" if abs(content_sentiment) > 0.2 else "low"
        }
        
        # Calculate emotion-based engagement
        total_engagement = content.engagement_score or 0
        emotion_engagement = {
            content_emotion: total_engagement
        }
        
        # Create emotions array for frontend compatibility
        emotions = []
        
        # Get emotion values from ContentAnalysis
        joy = content.emotion_joy or 0
        anger = content.emotion_anger or 0
        fear = content.emotion_fear or 0
        sadness = content.emotion_sadness or 0
        surprise = content.emotion_surprise or 0
        trust = content.emotion_trust or 0
        anticipation = content.emotion_anticipation or 0
        disgust = content.emotion_disgust or 0
        
        # If no emotion data, create based on dominant emotion
        if not any([joy, anger, fear, sadness, surprise, trust, anticipation, disgust]):
            if content_emotion == "joy":
                joy = 0.8
            elif content_emotion == "anger":
                anger = 0.8
            elif content_emotion == "fear":
                fear = 0.8
            elif content_emotion == "sadness":
                sadness = 0.8
            elif content_emotion == "surprise":
                surprise = 0.8
            elif content_emotion == "trust":
                trust = 0.8
            elif content_emotion == "anticipation":
                anticipation = 0.8
            elif content_emotion == "disgust":
                disgust = 0.8
            else:
                # Default to neutral
                joy = 0.2
                trust = 0.2
                anticipation = 0.2
        
        # Create emotions array with percentages
        emotions = [
            {"emotion": "joy", "percentage": round(joy * 100, 1)},
            {"emotion": "anger", "percentage": round(anger * 100, 1)},
            {"emotion": "fear", "percentage": round(fear * 100, 1)},
            {"emotion": "sadness", "percentage": round(sadness * 100, 1)},
            {"emotion": "surprise", "percentage": round(surprise * 100, 1)},
            {"emotion": "trust", "percentage": round(trust * 100, 1)},
            {"emotion": "anticipation", "percentage": round(anticipation * 100, 1)},
            {"emotion": "disgust", "percentage": round(disgust * 100, 1)},
            {"emotion": "neutral", "percentage": round((1 - max(joy, anger, fear, sadness, surprise, trust, anticipation, disgust)) * 100, 1)}
        ]
        
        return {
            # Frontend-compatible format
            "emotions": emotions,
            "total_analyzed": 1,  # Single content
            "dominant_emotion": content_emotion,
            "emotion_summary": {
                "primary_emotion": content_emotion,
                "confidence": emotion_insights["emotion_confidence"],
                "impact": emotion_insights["emotional_impact"]
            },
            
            # Additional content-specific data
            "content_id": content_id,
            "platform": content.platform.value,
            "emotion_analysis": {
                "primary_emotion": content_emotion,
                "sentiment_score": round(content_sentiment, 3),
                "emotion_confidence": emotion_insights["emotion_confidence"],
                "emotional_impact": emotion_insights["emotional_impact"]
            },
            "emotion_engagement": emotion_engagement,
            "emotion_insights": {
                "emotion_performance": "positive" if content_sentiment > 0 else "negative" if content_sentiment < 0 else "neutral",
                "audience_response": "strong" if total_engagement > 100 else "moderate" if total_engagement > 50 else "weak",
                "emotional_resonance": "high" if abs(content_sentiment) > 0.5 and total_engagement > 50 else "medium" if abs(content_sentiment) > 0.2 else "low"
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing content emotions: {str(e)}")


@router.get("/contents/{content_id}/demographics")
async def get_content_demographics(
    content_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    platforms: Optional[str] = None
):
    """
    Get content audience demographics for targeting insights
    
    Provides detailed demographic breakdown of the content's audience
    including age groups, gender distribution, and geographic data.
    """
    try:
        # Get content by ID
        from beanie import PydanticObjectId
        from app.models.database import ContentAnalysis
        content = await ContentAnalysis.get(PydanticObjectId(content_id))
        if not content:
            raise HTTPException(status_code=404, detail="Content not found")
        
        # Get content demographics
        content_age_group = content.author_age_group if content.author_age_group else "unknown"
        content_gender = content.author_gender if content.author_gender else "unknown"
        content_location = content.author_location_hint if content.author_location_hint else "unknown"
        
        # Generate demographic insights
        demographics = {
            "age_groups": [{
                "age_group": content_age_group,
                "count": 1,
                "percentage": 100.0
            }],
            "genders": [{
                "gender": content_gender,
                "count": 1,
                "percentage": 100.0
            }],
            "top_locations": [{
                "location": content_location,
                "count": 1,
                "percentage": 100.0
            }]
        }
        
        return {
            "content_id": content_id,
            "platform": content.platform.value,
            "total_analyzed": 1,
            "demographics": demographics,
            "audience_insights": {
                "primary_age_group": content_age_group,
                "primary_gender": content_gender,
                "primary_location": content_location,
                "audience_diversity": "low",  # Single content has low diversity
                "targeting_effectiveness": "high" if (content.engagement_score or 0) > 100 else "medium" if (content.engagement_score or 0) > 50 else "low"
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing content demographics: {str(e)}")


@router.get("/contents/{content_id}/competitive")
async def get_content_competitive_analysis(
    content_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    platforms: Optional[str] = None
):
    """
    Get content competitive analysis for market positioning
    
    Provides insights into how the content performs compared to similar content
    and industry benchmarks, including recommendations for improvement.
    """
    try:
        # Get content by ID
        from beanie import PydanticObjectId
        from app.models.database import ContentAnalysis
        content = await ContentAnalysis.get(PydanticObjectId(content_id))
        if not content:
            raise HTTPException(status_code=404, detail="Content not found")
        
        # Get related content for comparison
        related_content = await db_service.get_posts_by_brand(content.brand, content.platform, limit=100)
        
        # Calculate content metrics
        content_engagement = int(content.like_count or 0) + int(content.comment_count or 0) + int(content.share_count or 0)
        content_sentiment = 1 if content.sentiment and content.sentiment.value == "Positive" else -1 if content.sentiment and content.sentiment.value == "Negative" else 0
        
        # Calculate benchmark metrics from related content
        if related_content:
            avg_engagement_benchmark = sum(int(p.like_count or 0) + int(p.comment_count or 0) + int(p.share_count or 0) for p in related_content) / len(related_content)
            avg_sentiment_benchmark = sum(1 if p.sentiment.value == "Positive" else -1 if p.sentiment.value == "Negative" else 0 for p in related_content if p.sentiment is not None) / len([p for p in related_content if p.sentiment is not None]) if any(p.sentiment is not None for p in related_content) else 0
        else:
            avg_engagement_benchmark = 0
            avg_sentiment_benchmark = 0
        
        # Performance comparison
        engagement_performance = "above" if content_engagement > avg_engagement_benchmark else "below"
        sentiment_performance = "above" if content_sentiment > avg_sentiment_benchmark else "below"
        
        # Generate recommendations
        recommendations = []
        if content_engagement < avg_engagement_benchmark:
            recommendations.append("Improve content engagement through better visuals or captions")
        if content_sentiment < avg_sentiment_benchmark:
            recommendations.append("Focus on more positive messaging to improve sentiment")
        if content.like_count < avg_engagement_benchmark * 0.5:
            recommendations.append("Create more likeable content to increase audience approval")
        
        return {
            "content_id": content_id,
            "platform": content.platform.value,
            "content_metrics": {
                "engagement": content_engagement,
                "sentiment": round(content_sentiment, 3),
                "likes": content.like_count,
                "comments": content.comment_count,
                "shares": content.share_count
            },
            "benchmark_comparison": {
                "engagement_performance": engagement_performance,
                "sentiment_performance": sentiment_performance,
                "avg_engagement_benchmark": round(avg_engagement_benchmark, 2),
                "avg_sentiment_benchmark": round(avg_sentiment_benchmark, 3)
            },
            "content_position": "top_performer" if engagement_performance == "above" and sentiment_performance == "above" else "average_performer",
            "recommendations": recommendations
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing content competitive position: {str(e)}")


# ============= DEBUG ENDPOINTS =============

@router.get("/brands/{brand_identifier}/debug")
async def debug_brand_data(
    brand_identifier: str
):
    """
    Debug endpoint to check what data exists for a brand
    """
    try:
        # Get brand by identifier
        brand = await get_brand_by_identifier(brand_identifier)
        if not brand:
            raise HTTPException(status_code=404, detail="Brand not found")
        
        # Check posts in database
        posts = await db_service.get_posts_by_brand(brand, limit=1000)
        
        # Check brand analyses
        brand_analyses = await BrandAnalysis.find(
            BrandAnalysis.brand_id == str(brand.id)
        ).sort("-created_at").limit(5).to_list()
        
        # Check brand metrics
        brand_metrics = []
        if brand_analyses:
            for analysis in brand_analyses:
                metrics = await db_service.get_brand_metrics(str(analysis.id))
                if metrics:
                    brand_metrics.append(metrics)
        
        return {
            "brand": {
                "id": str(brand.id),
                "name": brand.name,
                "platforms": [p.value for p in brand.platforms],
                "keywords": brand.keywords
            },
            "posts_count": len(posts),
            "posts_sample": [
                {
                    "id": str(p.id),
                    "platform": p.platform.value,
                    "text": p.text[:100] + "..." if len(p.text) > 100 else p.text,
                    "sentiment": p.sentiment.value if p.sentiment else None,
                    "topic": p.topic,
                    "like_count": p.like_count,
                    "comment_count": p.comment_count,
                    "share_count": p.share_count,
                    "posted_at": p.posted_at
                } for p in posts[:5]
            ],
            "brand_analyses_count": len(brand_analyses),
            "brand_analyses": [
                {
                    "id": str(a.id),
                    "analysis_name": a.analysis_name,
                    "status": a.status,
                    "platforms": a.platforms,
                    "keywords": a.keywords,
                    "created_at": a.created_at
                } for a in brand_analyses
            ],
            "brand_metrics_count": len(brand_metrics),
            "brand_metrics": [
                {
                    "id": str(m.id),
                    "total_posts": m.total_posts,
                    "total_engagement": m.total_engagement,
                    "sentiment_distribution": m.sentiment_distribution
                } for m in brand_metrics
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error debugging brand data: {str(e)}")

@router.post("/brands/{brand_identifier}/process-real-data")
async def process_real_data(
    brand_identifier: str
):
    """
    Process real scraped data from files into database
    """
    try:
        # Get brand by identifier
        brand = await get_brand_by_identifier(brand_identifier)
        if not brand:
            raise HTTPException(status_code=404, detail="Brand not found")
        
        import os
        import json
        import pandas as pd
        from pathlib import Path
        
        # Check for existing scraped data files
        data_dir = "data/scraped_data"
        processed_count = 0
        platforms_processed = []
        
        # Process each platform's scraped data
        # If brand has no platforms configured, check all available platforms
        platforms_to_check = brand.platforms if brand.platforms else [PlatformType.INSTAGRAM, PlatformType.TWITTER, PlatformType.TIKTOK]
        
        for platform in platforms_to_check:
            platform_name = platform.value
            json_file = f"dataset_{platform_name}-scraper_{brand.name}.json"
            file_path = os.path.join(data_dir, json_file)
            
            if os.path.exists(file_path):
                print(f"📁 Processing {platform_name} data from {file_path}")
                
                # Load JSON data
                with open(file_path, 'r', encoding='utf-8') as f:
                    scraped_data = json.load(f)
                
                if scraped_data:
                    # Convert to DataFrame
                    df = pd.DataFrame(scraped_data)
                    
                    # Process through analysis service
                    from app.services.analysis_service_v2 import analysis_service_v2
                    
                    # Process the data
                    result = await analysis_service_v2.process_platform_dataframe(
                        df=df,
                        platform=platform_name,
                        brand_name=brand.name,
                        keywords=brand.keywords,
                        layer=1,
                        save_to_db=True
                    )
                    
                    processed_count += result.total_analyzed
                    platforms_processed.append(platform_name)
                    print(f"✅ Processed {result.total_analyzed} {platform_name} posts")
                else:
                    print(f"⚠️  No data in {file_path}")
            else:
                print(f"⚠️  File not found: {file_path}")
        
        if processed_count == 0:
            return {
                "message": f"No scraped data found for brand {brand.name}",
                "brand_id": str(brand.id),
                "platforms_checked": [p.value for p in brand.platforms],
                "files_checked": [f"dataset_{p.value}-scraper_{brand.name}.json" for p in brand.platforms]
            }
        
        # Create or update brand metrics
        from app.models.database import BrandMetrics
        brand_analysis = await BrandAnalysis.find_one(
            BrandAnalysis.brand_id == str(brand.id)
        )
        
        if brand_analysis:
            # Get posts from database to calculate real metrics
            posts = await db_service.get_posts_by_brand(brand, limit=10000)
            
            if posts:
                total_posts = len(posts)
                total_engagement = sum(int(p.like_count or 0) + int(p.comment_count or 0) + int(p.share_count or 0) for p in posts)
                
                # Calculate real sentiment distribution
                sentiment_counts = {"Positive": 0, "Negative": 0, "Neutral": 0}
                for post in posts:
                    if post.sentiment:
                        sentiment_counts[post.sentiment.value] += 1
                
                # Calculate platform breakdown
                platform_breakdown = {}
                for post in posts:
                    platform_name = post.platform.value
                    if platform_name not in platform_breakdown:
                        platform_breakdown[platform_name] = {"posts": 0, "engagement": 0}
                    platform_breakdown[platform_name]["posts"] += 1
                    platform_breakdown[platform_name]["engagement"] += int(post.like_count or 0) + int(post.comment_count or 0) + int(post.share_count or 0)
                
                # Create or update brand metrics
                existing_metrics = await BrandMetrics.find_one(
                    BrandMetrics.brand_analysis_id == str(brand_analysis.id)
                )
                
                if existing_metrics:
                    # Update existing metrics
                    existing_metrics.total_posts = total_posts
                    existing_metrics.total_engagement = total_engagement
                    existing_metrics.avg_engagement_per_post = total_engagement / total_posts if total_posts > 0 else 0
                    existing_metrics.sentiment_distribution = sentiment_counts
                    existing_metrics.sentiment_percentage = {
                        "Positive": round((sentiment_counts["Positive"] / total_posts * 100), 1) if total_posts > 0 else 0,
                        "Negative": round((sentiment_counts["Negative"] / total_posts * 100), 1) if total_posts > 0 else 0,
                        "Neutral": round((sentiment_counts["Neutral"] / total_posts * 100), 1) if total_posts > 0 else 0
                    }
                    existing_metrics.platform_breakdown = platform_breakdown
                    await existing_metrics.save()
                else:
                    # Create new metrics
                    metrics = BrandMetrics(
                        brand_analysis_id=str(brand_analysis.id),
                        brand_id=str(brand.id),
                        total_posts=total_posts,
                        total_engagement=total_engagement,
                        avg_engagement_per_post=total_engagement / total_posts if total_posts > 0 else 0,
                        engagement_rate=0.05,  # Default 5%
                        sentiment_distribution=sentiment_counts,
                        sentiment_percentage={
                            "Positive": round((sentiment_counts["Positive"] / total_posts * 100), 1) if total_posts > 0 else 0,
                            "Negative": round((sentiment_counts["Negative"] / total_posts * 100), 1) if total_posts > 0 else 0,
                            "Neutral": round((sentiment_counts["Neutral"] / total_posts * 100), 1) if total_posts > 0 else 0
                        },
                        overall_sentiment_score=0.2,  # Default slightly positive
                        platform_breakdown=platform_breakdown,
                        trending_topics=[],
                        demographics={},
                        engagement_patterns={},
                        performance_metrics={}
                    )
                    await metrics.insert()
        
        return {
            "message": f"Processed real scraped data for brand {brand.name}",
            "brand_id": str(brand.id),
            "posts_processed": processed_count,
            "platforms_processed": platforms_processed,
            "data_sources": [f"dataset_{p}-scraper_{brand.name}.json" for p in platforms_processed]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing real data: {str(e)}")

# ============= TRIGGER ANALYSIS ENDPOINTS =============

@router.post("/brands/{brand_id}/trigger-analysis-sync")
async def trigger_brand_analysis_sync(
    brand_id: str,
    keywords: List[str] = None,
    platforms: List[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """
    Trigger brand analysis synchronously (for testing)
    """
    try:
        # Get brand by ID
        brand = await db_service.get_brand_by_id(brand_id)
        if not brand:
            raise HTTPException(status_code=404, detail="Brand not found")
        
        # Create brand analysis record
        analysis_name = f"Brand Analysis - {brand.name} - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        date_range = {}
        if start_date:
            date_range["start_date"] = start_date
        if end_date:
            date_range["end_date"] = end_date
        
        analysis_id = await db_service.create_brand_analysis(
            brand_id=str(brand.id),
            analysis_name=analysis_name,
            analysis_type="comprehensive",
            keywords=keywords or brand.keywords or [],
            platforms=platforms or ["tiktok", "instagram", "twitter", "youtube"],
            date_range=date_range
        )
        
        # Update status to running
        await db_service.update_brand_analysis_status(analysis_id, "running")
        
        # Get analysis results and save to new collections
        await save_brand_analysis_results(analysis_id, str(brand.id))
        
        # Update status to completed
        await db_service.update_brand_analysis_status(analysis_id, "completed")
        
        return {
            "analysis_id": analysis_id,
            "status": "completed",
            "message": f"Brand analysis completed for {brand.name}",
            "brand_name": brand.name,
            "platforms": platforms or ["tiktok", "instagram", "twitter", "youtube"],
            "keywords": keywords or brand.keywords or []
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error triggering brand analysis: {str(e)}")


@router.get("/brands/{brand_id}/analysis-status")
async def get_brand_analysis_status(brand_id: str):
    """
    Get brand analysis status
    
    Returns the status of the latest brand analysis for this brand.
    """
    try:
        brand = await db_service.get_brand_by_id(brand_id)
        if not brand:
            raise HTTPException(status_code=404, detail="Brand not found")
        
        # Get latest brand analysis
        analyses = await BrandAnalysis.find(
            BrandAnalysis.brand_id == str(brand.id)
        ).sort("-created_at").limit(1).to_list()
        
        if not analyses:
            return {
                "has_analysis": False,
                "message": "No analysis found for this brand"
            }
        
        analysis = analyses[0]
        return {
            "has_analysis": True,
            "analysis_id": str(analysis.id),
            "status": analysis.status,
            "created_at": analysis.created_at,
            "updated_at": analysis.updated_at,
            "completed_at": analysis.completed_at,
            "total_posts": analysis.total_posts,
            "total_engagement": analysis.total_engagement
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting analysis status: {str(e)}")


@router.post("/brands/{brand_id}/trigger-analysis")
async def trigger_brand_analysis(
    background_tasks: BackgroundTasks,
    brand_id: str,
    keywords: List[str] = None,
    platforms: List[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """
    Trigger comprehensive brand analysis
    
    Initiates data collection and analysis for a specific brand across
    multiple platforms and keywords. This endpoint starts the analysis
    process in the background.
    """
    try:
        # Get brand by ID
        brand = await db_service.get_brand_by_id(brand_id)
        if not brand:
            raise HTTPException(status_code=404, detail="Brand not found")
        
        # Validate platforms - use brand platforms if none provided
        valid_platforms = []
        if platforms:
            for platform in platforms:
                try:
                    valid_platforms.append(PlatformType(platform.lower()))
                except:
                    continue
        else:
            # Use brand's configured platforms
            valid_platforms = brand.platforms or []
        
        # Use brand keywords if none provided
        if not keywords:
            keywords = brand.keywords or []
        
        # Create brand analysis record
        analysis_name = f"Brand Analysis - {brand.name} - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        date_range = {}
        if start_date:
            date_range["start_date"] = start_date
        if end_date:
            date_range["end_date"] = end_date
        
        analysis_id = await db_service.create_brand_analysis(
            brand_id=str(brand.id),
            analysis_name=analysis_name,
            analysis_type="comprehensive",
            keywords=keywords,
            platforms=[p.value for p in valid_platforms] if valid_platforms else [],
            date_range=date_range
        )
        
        # Start background analysis
        background_tasks.add_task(
            run_brand_analysis_background, 
            analysis_id, 
            brand, 
            keywords, 
            valid_platforms, 
            start_date, 
            end_date
        )
        
        return {
            "analysis_id": analysis_id,
            "status": "started",
            "message": f"Brand analysis started for {brand.name}",
            "estimated_completion": "5-10 minutes",
            "brand_name": brand.name,
            "platforms": [p.value for p in valid_platforms] if valid_platforms else ["tiktok", "instagram", "twitter", "youtube"],
            "keywords": keywords
        }
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error in trigger_brand_analysis: {str(e)}")
        print(f"Traceback: {error_details}")
        raise HTTPException(status_code=500, detail=f"Error triggering brand analysis: {str(e)}")


@router.post("/contents/{content_id}/trigger-analysis")
async def trigger_content_analysis(
    content_id: str,
    analysis_type: str = "comprehensive",
    parameters: dict = None
):
    """
    Trigger comprehensive content analysis
    
    Initiates detailed analysis for a specific content piece including
    sentiment analysis, engagement patterns, and audience insights.
    """
    try:
        # Get content analysis by ID
        from beanie import PydanticObjectId
        from app.models.database import ContentAnalysis
        content = await ContentAnalysis.get(PydanticObjectId(content_id))
        if not content:
            raise HTTPException(status_code=404, detail="Content not found")
        
        # Create analysis job
        analysis_job = AnalysisJob(
            job_id=f"content_analysis_{content_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            brand_id=None,  # ContentAnalysis doesn't have brand relationship
            brand=None,  # No brand for content analysis
            content_id=content_id,
            analysis_type="content_analysis",
            status=AnalysisStatusType.PENDING,
            platforms=[content.platform.value],  # Required field
            parameters={
                "analysis_type": analysis_type,
                "parameters": parameters or {},
                "platform": content.platform.value,
                "content_url": content.post_url
            }
        )
        
        # Save analysis job
        await analysis_job.insert()
        job_id = str(analysis_job.id)
        
        # Start background analysis
        import asyncio
        asyncio.create_task(run_content_analysis_background(job_id, content, analysis_type, parameters))
        
        return {
            "analysis_id": str(job_id),
            "status": "started",
            "message": f"Content analysis started for content {content_id}",
            "estimated_completion": "2-5 minutes",
            "content_id": content_id,
            "platform": content.platform.value,
            "analysis_type": analysis_type
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error triggering content analysis: {str(e)}")


# ============= BACKGROUND ANALYSIS FUNCTIONS =============

# Simple sentiment analysis function (from manual_store_simple.py)
def simple_sentiment_analysis(caption, hashtags):
    """Simple rule-based sentiment analysis"""
    positive_words = ['love', 'amazing', 'beautiful', 'best', 'great', 'perfect', 'excellent', 'wonderful']
    negative_words = ['bad', 'worst', 'terrible', 'awful', 'hate', 'poor', 'disappointing']
    
    text = (caption + ' ' + ' '.join(hashtags)).lower()
    
    positive_count = sum(1 for word in positive_words if word in text)
    negative_count = sum(1 for word in negative_words if word in text)
    
    if positive_count > negative_count:
        return "Positive", 0.6
    elif negative_count > positive_count:
        return "Negative", -0.6
    else:
        return "Neutral", 0.0

async def load_brand_specific_data(brand_name: str, platform: str, keywords: List[str]):
    """
    Load brand-specific data only - NO FALLBACK to other brands
    """
    try:
        import pandas as pd
        import json
        import os
        from datetime import datetime
        
        print(f"🔄 Loading brand-specific data for {brand_name} on {platform}")
        
        # Map platform to file path based on brand name
        base_path = '/Users/ilhamabdullah/Documents/teorema/socialint-api/data/scraped_data'
        brand_lower = brand_name.lower()
        
        file_paths = {
            'instagram': f'{base_path}/dataset_instagram-scraper_{brand_lower}.json',
            'tiktok': f'{base_path}/dataset_tiktok-scraper_{brand_lower}.json',
            'twitter': f'{base_path}/dataset_twitter-scraper_{brand_lower}.json',
            'youtube': f'{base_path}/dataset_youtube-scraper_{brand_lower}.json'
        }
        
        file_path = file_paths.get(platform.lower())
        
        # Check if brand-specific file exists
        if not file_path or not os.path.exists(file_path):
            print(f"⚠️ No brand-specific data file found for {brand_name} on {platform}: {file_path}")
            return pd.DataFrame()
        
        print(f"📁 Using brand-specific data file: {file_path}")
        
        # Load data from JSON file
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not data:
            print(f"⚠️ Empty data file: {file_path}")
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        if df.empty:
            print(f"⚠️ Empty DataFrame from file: {file_path}")
            return pd.DataFrame()
        
        # Limit to reasonable number of posts
        max_posts = 100
        if len(df) > max_posts:
            df = df.head(max_posts)
            print(f"📊 Limited to {max_posts} posts from {len(data)} total posts")
        
        print(f"✅ Loaded {len(df)} posts from brand-specific data for {platform}")
        return df
        
    except Exception as e:
        print(f"❌ Error loading brand-specific data: {str(e)}")
        return pd.DataFrame()

async def load_fallback_data(brand_name: str, platform: str, keywords: List[str]):
    """
    Load fallback data from JSON files when scraping fails
    Similar to manual_store_simple.py approach
    """
    try:
        import pandas as pd
        import json
        import os
        from datetime import datetime
        
        print(f"🔄 Loading fallback data for {brand_name} on {platform}")
        
        # Map platform to file path based on brand name
        base_path = '/Users/ilhamabdullah/Documents/teorema/socialint-api/data/scraped_data'
        
        # Try to find brand-specific data first, fallback to generic data
        brand_lower = brand_name.lower()
        
        file_paths = {
            'instagram': f'{base_path}/dataset_instagram-scraper_{brand_lower}.json',
            'tiktok': f'{base_path}/dataset_tiktok-scraper_{brand_lower}.json',
            'twitter': f'{base_path}/dataset_twitter-scraper_{brand_lower}.json',
            'youtube': f'{base_path}/dataset_youtube-scraper_{brand_lower}.json'
        }
        
        # Fallback to available data if brand-specific data not found
        fallback_paths = {
            'instagram': f'{base_path}/dataset_instagram-scraper_hyundai.json',
            'tiktok': '/Users/ilhamabdullah/Documents/teorema/socialint-api/dataset_tiktok-scraper_jokowi.json',
            'twitter': f'{base_path}/dataset_twitter-scraper_bahlil.json',
            'youtube': f'{base_path}/dataset_youtube-scraper_hyundai.json'
        }
        
        file_path = file_paths.get(platform.lower())
        
        # Try brand-specific file first, then fallback
        if not file_path or not os.path.exists(file_path):
            file_path = fallback_paths.get(platform.lower())
            if not file_path or not os.path.exists(file_path):
                print(f"⚠️ No fallback data file found for platform: {platform}")
                return pd.DataFrame()
            else:
                print(f"📁 Using fallback data file: {file_path}")
        else:
            print(f"📁 Using brand-specific data file: {file_path}")
        
        # Load data from JSON file
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not data:
            print(f"⚠️ Empty data file: {file_path}")
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        if df.empty:
            print(f"⚠️ Empty DataFrame from file: {file_path}")
            return pd.DataFrame()
        
        # Limit to reasonable number of posts
        max_posts = 100
        if len(df) > max_posts:
            df = df.head(max_posts)
            print(f"📊 Limited to {max_posts} posts from {len(data)} total posts")
        
        print(f"✅ Loaded {len(df)} posts from fallback data for {platform}")
        return df
        
    except Exception as e:
        print(f"❌ Error loading fallback data: {str(e)}")
        return pd.DataFrame()

async def process_platform_data_manual(df, platform: str, brand, keywords: List[str]):
    """
    Process platform data using manual store approach
    Similar to manual_store_simple.py
    """
    try:
        import pandas as pd
        from datetime import datetime
        from app.models.database import Post, SentimentType, PlatformType
        
        print(f"🔄 Processing {len(df)} posts for {platform}")
        
        posts_stored = 0
        for idx, item in df.iterrows():
            try:
                # Parse sentiment using rule-based approach (same as manual_store_simple.py)
                caption = item.get('caption', '')
                hashtags = item.get('hashtags', [])
                
                # Simple analysis
                sentiment_str, sentiment_score = simple_sentiment_analysis(caption, hashtags)
                
                # Convert to enum
                if sentiment_str == "Positive":
                    sentiment_enum = SentimentType.POSITIVE
                elif sentiment_str == "Negative":
                    sentiment_enum = SentimentType.NEGATIVE
                else:
                    sentiment_enum = SentimentType.NEUTRAL
                
                # Parse timestamp
                timestamp = None
                if pd.notna(item.get('timestamp')):
                    try:
                        timestamp = pd.to_datetime(item['timestamp'])
                    except:
                        timestamp = datetime.now()
                else:
                    timestamp = datetime.now()
                
                # Create post
                post = Post(
                    brand=brand,
                    platform=PlatformType(platform.lower()),
                    platform_post_id=str(item.get('id', f"{platform}_{idx}")),
                    text=str(item.get('caption', '')),
                    author_name=str(item.get('ownerFullName', 'unknown')),
                    like_count=int(item.get('likesCount', 0)) if pd.notna(item.get('likesCount')) else 0,
                    comment_count=int(item.get('commentsCount', 0)) if pd.notna(item.get('commentsCount')) else 0,
                    share_count=int(item.get('sharesCount', 0)) if pd.notna(item.get('sharesCount')) else 0,
                    post_url=str(item.get('url', '')),
                    posted_at=timestamp,
                    scraped_at=datetime.now(),
                    sentiment=sentiment_enum,
                    topic="General",  # Default topic
                    emotion="Neutral",  # Default emotion
                    author_age_group="Unknown",
                    author_gender="Unknown",
                    author_location_hint="Unknown"
                )
                
                await post.save()
                posts_stored += 1
                
                if posts_stored % 50 == 0:
                    print(f"   ✓ Stored {posts_stored} posts...")
                    
            except Exception as e:
                print(f"   ⚠️ Error at post {idx}: {str(e)}")
                continue
        
        print(f"✅ Stored {posts_stored} posts for {platform}")
        
    except Exception as e:
        print(f"❌ Error processing platform data: {str(e)}")

async def run_brand_analysis_background(analysis_id: str, brand, keywords: List[str], platforms: List[PlatformType], start_date: Optional[str], end_date: Optional[str]):
    """
    Background function to run brand analysis
    
    This function handles the actual data collection and analysis
    process for brand analysis in the background.
    """
    try:
        print(f"=== Starting brand analysis background task ===")
        print(f"Analysis ID: {analysis_id}")
        print(f"Brand: {brand.name}")
        print(f"Keywords: {keywords}")
        print(f"Platforms: {[p.value for p in platforms]}")
        
        # Update analysis status to running
        await db_service.update_brand_analysis_status(analysis_id, "running")
        print(f"Updated analysis status to 'running'")
        
        # Use ScraperService approach like campaign analysis
        print(f"🔄 Using ScraperService approach for {len(platforms)} platforms")
        
        # Initialize scraper service
        from app.services.scraper_service import ScraperService
        scraper_service = ScraperService()
        
        # Check if brand has keywords
        if not keywords:
            print("⚠️  Brand has no keywords configured")
            print("💡 Please add keywords to the brand for scraping to work")
            await db_service.update_brand_analysis_status(analysis_id, "failed")
            return
        
        # Step 1: Check existing data files first, then scrape if needed
        platforms_data = {}
        posts_processed = 0
        
        for platform in platforms:
            print(f"\n{'='*80}")
            print(f"Processing platform: {platform.value.upper()} ({platforms.index(platform) + 1}/{len(platforms)})")
            print(f"{'='*80}")
            
            try:
                # Check if dataset file already exists for this brand and platform
                file_path = f"data/scraped_data/dataset_{platform.value}-scraper_{brand.name}.json"
                import os
                
                if os.path.exists(file_path):
                    print(f"📁 Found existing dataset file: {file_path}")
                    
                    # Load and validate existing data
                    import pandas as pd
                    try:
                        existing_df = pd.read_json(file_path)
                        if not existing_df.empty:
                            platforms_data[platform.value] = file_path
                            posts_processed += len(existing_df)
                            print(f"✅ Using existing data for {platform.value} - {len(existing_df)} posts found")
                            continue
                        else:
                            print(f"⚠️  Existing file is empty, will scrape new data")
                    except Exception as e:
                        print(f"⚠️  Error reading existing file: {str(e)}, will scrape new data")
                else:
                    print(f"📁 No existing dataset found for {brand.name} on {platform.value}")
                    print(f"🔄 Will proceed with scraping...")
                
                # Execute platform-specific scraping (only if no existing data or existing data is invalid)
                print(f"🚀 Starting scraping for {platform.value}...")
                import asyncio
                from concurrent.futures import ThreadPoolExecutor
                
                async def run_scraping():
                    with ThreadPoolExecutor(max_workers=1) as executor:
                        if platform == PlatformType.TIKTOK:
                            loop = asyncio.get_event_loop()
                            scraped_data = await loop.run_in_executor(
                                executor, 
                                scraper_service.scrape_tiktok,
                                keywords,
                                100,
                                start_date,
                                end_date,
                                brand.name
                            )
                        elif platform == PlatformType.INSTAGRAM:
                            loop = asyncio.get_event_loop()
                            scraped_data = await loop.run_in_executor(
                                executor,
                                scraper_service.scrape_instagram,
                                keywords,
                                100,
                                start_date,
                                end_date,
                                brand.name
                            )
                        elif platform == PlatformType.TWITTER:
                            loop = asyncio.get_event_loop()
                            scraped_data = await loop.run_in_executor(
                                executor,
                                scraper_service.scrape_twitter,
                                keywords,
                                100,
                                start_date,
                                end_date,
                                brand.name
                            )
                        elif platform == PlatformType.YOUTUBE:
                            loop = asyncio.get_event_loop()
                            scraped_data = await loop.run_in_executor(
                                executor,
                                scraper_service.scrape_youtube,
                                keywords,
                                100,
                                start_date,
                                end_date,
                                brand.name
                            )
                        else:
                            scraped_data = None
                        return scraped_data
                
                scraped_data = await run_scraping()
                
                if scraped_data is None:
                    print(f"⚠️  Unsupported platform: {platform.value}")
                    continue
                
                # Check if scraped_data is valid and not empty
                if scraped_data is not None and not scraped_data.empty:
                    # Save scraped data to file
                    scraped_data.to_json(file_path, orient='records', indent=2)
                    platforms_data[platform.value] = file_path
                    posts_processed += len(scraped_data)
                    print(f"✅ Scraping completed for {platform.value} - {len(scraped_data)} posts found")
                    print(f"💾 Data saved to: {file_path}")
                else:
                    print(f"❌ No data scraped for {platform.value} - empty or invalid data")
                    
            except Exception as e:
                print(f"✗ Error processing {platform.value}: {str(e)}")
                continue
        
        # If no posts were processed, fail the analysis
        if posts_processed == 0:
            print(f"❌ No data scraped for brand '{brand.name}' - analysis failed")
            await db_service.update_brand_analysis_status(analysis_id, "failed")
            return
        
        # Step 2: Data Cleansing and NLP Processing using AnalysisServiceV2
        print(f"\n{'='*80}")
        print(f"🔍 Starting data analysis and processing")
        print(f"{'='*80}")
        
        try:
            from app.services.analysis_service_v2 import analysis_service_v2
            
            results = await analysis_service_v2.process_multiple_platforms(
                platforms_data=platforms_data,
                brand_name=brand.name,
                keywords=keywords,
                save_to_db=True
            )
            
            print(f"✅ Analysis completed - processed {len(results)} platform results")
            
        except Exception as e:
            print(f"⚠️ Error in analysis processing: {str(e)}")
            # Continue with manual processing as fallback
            print("🔄 Falling back to manual processing...")
            
            # Process each platform using manual store approach
            for platform in platforms:
                try:
                    if platform.value in platforms_data:
                        file_path = platforms_data[platform.value]
                        import pandas as pd
                        df = pd.read_json(file_path)
                        
                        if not df.empty:
                            await process_platform_data_manual(df, platform.value, brand, keywords)
                            print(f"✅ Manual processing completed for {platform.value}")
                        
                except Exception as e:
                    print(f"❌ Error in manual processing for {platform.value}: {str(e)}")
                continue
        
        # Get analysis results and save to new collections
        await save_brand_analysis_results(analysis_id, str(brand.id))
        
        # Update analysis status to completed
        await db_service.update_brand_analysis_status(analysis_id, "completed")
        
    except Exception as e:
        # Update analysis status to failed
        await db_service.update_brand_analysis_status(analysis_id, "failed")
        print(f"Error in brand analysis background task: {str(e)}")


async def save_brand_analysis_results(analysis_id: str, brand_id: str):
    """
    Save brand analysis results to new collections
    """
    try:
        # Get posts for this brand
        brand = await db_service.get_brand_by_id(brand_id)
        if not brand:
            return
        posts = await db_service.get_posts_by_brand(brand)
        
        if not posts:
            return
        
        # Calculate metrics
        total_posts = len(posts)
        total_engagement = sum(
            (int(post.like_count or 0) + int(post.comment_count or 0) + int(post.share_count or 0))
            for post in posts
        )
        
        # Calculate sentiment distribution
        sentiment_counts = {"Positive": 0, "Negative": 0, "Neutral": 0}
        for post in posts:
            if post.sentiment:
                sentiment_str = post.sentiment.value if hasattr(post.sentiment, 'value') else str(post.sentiment)
                if sentiment_str in sentiment_counts:
                    sentiment_counts[sentiment_str] += 1
        
        # Calculate sentiment percentages
        total_sentiment = sum(sentiment_counts.values())
        sentiment_percentage = {
            k: (v / total_sentiment * 100) if total_sentiment > 0 else 0
            for k, v in sentiment_counts.items()
        }
        
        # Calculate platform breakdown for metrics
        platform_breakdown = {}
        for post in posts:
            platform_name = post.platform.value if hasattr(post.platform, 'value') else str(post.platform)
            if platform_name not in platform_breakdown:
                platform_breakdown[platform_name] = {
                    "posts": 0,
                    "engagement": 0,
                    "sentiment": 0
                }
            
            platform_breakdown[platform_name]["posts"] += 1
            post_engagement = int(post.like_count or 0) + int(post.comment_count or 0) + int(post.share_count or 0)
            platform_breakdown[platform_name]["engagement"] += post_engagement
            
            if post.sentiment:
                # Convert sentiment enum to score: Positive=1, Negative=-1, Neutral=0
                sentiment_value = 1 if post.sentiment.value == "Positive" else -1 if post.sentiment.value == "Negative" else 0
                platform_breakdown[platform_name]["sentiment"] += sentiment_value
        
        # Calculate platform averages
        for platform_data in platform_breakdown.values():
            if platform_data["posts"] > 0:
                platform_data["avg_engagement"] = round(platform_data["engagement"] / platform_data["posts"], 2)
                platform_data["avg_sentiment"] = round(platform_data["sentiment"] / platform_data["posts"], 3)
        
        # Save brand metrics
        metrics_data = {
            "total_posts": total_posts,
            "total_engagement": total_engagement,
            "avg_engagement_per_post": total_engagement / total_posts if total_posts > 0 else 0,
            "engagement_rate": (total_engagement / total_posts * 100) if total_posts > 0 else 0,
            "sentiment_distribution": sentiment_counts,
            "sentiment_percentage": sentiment_percentage,
            "overall_sentiment_score": (sentiment_counts["Positive"] - sentiment_counts["Negative"]) / total_posts if total_posts > 0 else 0,
            "platform_breakdown": platform_breakdown,
            "trending_topics": []  # Will be populated after topics are saved
        }
        await db_service.save_brand_metrics(analysis_id, brand_id, metrics_data)
        
        # Save sentiment timeline (simplified - group by date)
        timeline_data = []
        from collections import defaultdict
        daily_sentiment = defaultdict(lambda: {"positive": 0, "negative": 0, "neutral": 0, "total": 0})
        
        for post in posts:
            if post.posted_at:
                date_key = post.posted_at.date()
                daily_sentiment[date_key]["total"] += 1
                if post.sentiment:
                    sentiment_str = post.sentiment.value if hasattr(post.sentiment, 'value') else str(post.sentiment)
                    if sentiment_str == "Positive":
                        daily_sentiment[date_key]["positive"] += 1
                    elif sentiment_str == "Negative":
                        daily_sentiment[date_key]["negative"] += 1
                    else:
                        daily_sentiment[date_key]["neutral"] += 1
        
        for date, counts in daily_sentiment.items():
            timeline_data.append({
                "date": datetime.combine(date, datetime.min.time()),
                "sentiment_score": (counts["positive"] - counts["negative"]) / counts["total"] if counts["total"] > 0 else 0,
                "positive_count": counts["positive"],
                "negative_count": counts["negative"],
                "neutral_count": counts["neutral"],
                "total_posts": counts["total"]
            })
        
        if timeline_data:
            await db_service.save_brand_sentiment_timeline(analysis_id, brand_id, timeline_data)
        
        # Save trending topics (improved calculation)
        topics_data = []
        topic_analysis = {}
        
        for post in posts:
            if post.topic and post.topic != 'Unknown':
                if post.topic not in topic_analysis:
                    topic_analysis[post.topic] = {
                        'count': 0,
                        'sentiment_score': 0,
                        'positive': 0,
                        'negative': 0,
                        'neutral': 0,
                        'engagement': 0
                    }
                
                topic_analysis[post.topic]['count'] += 1
                
                # Calculate engagement
                post_engagement = int(post.like_count or 0) + int(post.comment_count or 0) + int(post.share_count or 0)
                topic_analysis[post.topic]['engagement'] += post_engagement
                
                # Calculate sentiment
                if post.sentiment:
                    sentiment_str = post.sentiment.value if hasattr(post.sentiment, 'value') else str(post.sentiment)
                    sentiment_value = 1 if sentiment_str == "Positive" else -1 if sentiment_str == "Negative" else 0
                    topic_analysis[post.topic]['sentiment_score'] += sentiment_value
                    if sentiment_str == "Positive":
                        topic_analysis[post.topic]['positive'] += 1
                    elif sentiment_str == "Negative":
                        topic_analysis[post.topic]['negative'] += 1
                    else:
                        topic_analysis[post.topic]['neutral'] += 1
        
        # Sort by count and get top 10
        for topic, data in sorted(topic_analysis.items(), key=lambda x: x[1]['count'], reverse=True)[:10]:
            avg_sentiment = data['sentiment_score'] / data['count'] if data['count'] > 0 else 0
            topics_data.append({
                "topic": topic,
                "topic_count": data['count'],
                "sentiment": round(avg_sentiment, 2),
                "engagement": data['engagement'],
                "positive": data['positive'],
                "negative": data['negative'],
                "neutral": data['neutral']
            })
        
        if topics_data:
            await db_service.save_brand_trending_topics(analysis_id, brand_id, topics_data)
        
            # Update metrics with trending topics
            metrics = await db_service.get_brand_metrics(analysis_id)
            if metrics:
                metrics.trending_topics = topics_data
                await metrics.save()
        
        # Save demographics (improved calculation)
        age_groups = {}
        genders = {}
        locations = {}
        
        for post in posts:
            if post.author_age_group:
                age_groups[post.author_age_group] = age_groups.get(post.author_age_group, 0) + 1
            if post.author_gender:
                genders[post.author_gender] = genders.get(post.author_gender, 0) + 1
            if post.author_location_hint:
                locations[post.author_location_hint] = locations.get(post.author_location_hint, 0) + 1
        
        demographics_data = {
            "platform": "all",
            "total_analyzed": total_posts,
            "age_groups": [{"age_group": age, "count": count, "percentage": round(count/total_posts*100, 2)} for age, count in age_groups.items()],
            "genders": [{"gender": gender, "count": count, "percentage": round(count/total_posts*100, 2)} for gender, count in genders.items()],
            "top_locations": [{"location": loc, "count": count, "percentage": round(count/total_posts*100, 2)} for loc, count in sorted(locations.items(), key=lambda x: x[1], reverse=True)[:10]]
        }
        await db_service.save_brand_demographics(analysis_id, brand_id, demographics_data)
        
        # Save engagement patterns (improved calculation)
        hourly_engagement = {}
        daily_engagement = {}
        
        for post in posts:
            if post.posted_at:
                hour = post.posted_at.hour
                day = post.posted_at.strftime("%A")
                
                if hour not in hourly_engagement:
                    hourly_engagement[hour] = {"posts": 0, "engagement": 0}
                if day not in daily_engagement:
                    daily_engagement[day] = {"posts": 0, "engagement": 0}
                
                post_engagement = int(post.like_count or 0) + int(post.comment_count or 0) + int(post.share_count or 0)
                hourly_engagement[hour]["posts"] += 1
                hourly_engagement[hour]["engagement"] += post_engagement
                daily_engagement[day]["posts"] += 1
                daily_engagement[day]["engagement"] += post_engagement
        
        # Calculate peak hours and active days
        peak_hours = sorted(hourly_engagement.items(), key=lambda x: x[1]["engagement"], reverse=True)[:3]
        active_days = sorted(daily_engagement.items(), key=lambda x: x[1]["engagement"], reverse=True)[:3]
        
        patterns_data = {
            "platform": "all",
            "peak_hours": [f"{hour:02d}:00" for hour, _ in peak_hours],
            "active_days": [day for day, _ in active_days],
            "avg_engagement_rate": total_engagement / total_posts if total_posts > 0 else 0,
            "total_posts": total_posts
        }
        await db_service.save_brand_engagement_patterns(analysis_id, brand_id, patterns_data)
        
        # Save performance metrics
        performance_data = {
            "total_reach": total_posts * 100,  # Simplified
            "total_impressions": total_posts * 1000,  # Simplified
            "total_engagement": total_engagement,
            "engagement_rate": (total_engagement / total_posts * 100) if total_posts > 0 else 0,
            "estimated_reach": total_posts * 100,
            "conversion_funnel": {
                "impressions": total_posts * 1000,
                "engagement": total_engagement,
                "clicks": total_engagement // 2,
                "conversions": total_engagement // 10
            }
        }
        await db_service.save_brand_performance(analysis_id, brand_id, performance_data)
        
        # Save emotions (improved calculation)
        emotion_counts = {}
        for post in posts:
            if post.emotion and post.emotion != 'unknown':
                emotion_counts[post.emotion] = emotion_counts.get(post.emotion, 0) + 1
        
        # Calculate emotion percentages
        total_emotions = sum(emotion_counts.values())
        emotion_percentages = {}
        for emotion, count in emotion_counts.items():
            emotion_percentages[emotion] = round(count / total_emotions * 100, 2) if total_emotions > 0 else 0
        
        # Find dominant emotion
        dominant_emotion = max(emotion_counts.items(), key=lambda x: x[1])[0] if emotion_counts else "neutral"
        
        emotions_data = {
            "total_analyzed": total_posts,
            "dominant_emotion": dominant_emotion,
            "emotions": emotion_percentages
        }
        await db_service.save_brand_emotions(analysis_id, brand_id, emotions_data)
        
        # Save competitive analysis (improved calculation)
        # Calculate competitive metrics
        avg_engagement_per_post = total_engagement / total_posts if total_posts > 0 else 0
        positive_sentiment_ratio = sentiment_counts.get("Positive", 0) / total_sentiment if total_sentiment > 0 else 0
        
        # Determine market position based on metrics
        market_position = "leader" if avg_engagement_per_post > 50 and positive_sentiment_ratio > 0.6 else "follower" if avg_engagement_per_post < 20 or positive_sentiment_ratio < 0.4 else "medium"
        
        competitive_metrics = {
            "avg_engagement_per_post": round(avg_engagement_per_post, 2),
            "positive_sentiment_ratio": round(positive_sentiment_ratio, 3),
            "total_posts": total_posts,
            "total_engagement": total_engagement
        }
        
        competitive_insights = []
        if avg_engagement_per_post > 50:
            competitive_insights.append("High engagement indicates strong brand resonance")
        if positive_sentiment_ratio > 0.6:
            competitive_insights.append("Positive sentiment shows good brand perception")
        if total_posts > 100:
            competitive_insights.append("Active content strategy with regular posting")
        
        recommendations = []
        if avg_engagement_per_post < 20:
            recommendations.append("Focus on creating more engaging content")
        if positive_sentiment_ratio < 0.4:
            recommendations.append("Improve brand messaging to increase positive sentiment")
        if total_posts < 50:
            recommendations.append("Increase content posting frequency")
        
        competitive_data = {
            "competitive_metrics": competitive_metrics,
            "market_position": market_position,
            "competitive_insights": competitive_insights,
            "recommendations": recommendations
        }
        await db_service.save_brand_competitive(analysis_id, brand_id, competitive_data)
        
        # Update analysis record with total metrics
        from app.models.database import BrandAnalysis
        from bson import ObjectId
        analysis = await BrandAnalysis.find_one(BrandAnalysis.id == ObjectId(analysis_id))
        if analysis:
            analysis.total_posts = total_posts
            analysis.total_engagement = total_engagement
            await analysis.save()
            print(f"✅ Updated analysis record: {total_posts} posts, {total_engagement} engagement")
        
    except Exception as e:
        print(f"Error saving brand analysis results: {str(e)}")


async def run_content_analysis_background(job_id: str, content, analysis_type: str, parameters: dict):
    """
    Background function to run content analysis with realtime data scraping
    
    This function handles the actual analysis process for individual
    content pieces in the background, including realtime data scraping.
    """
    try:
        # Update job status to running
        from app.models.database import AnalysisJob
        job = await AnalysisJob.find_one(AnalysisJob.id == job_id)
        if job:
            await db_service.update_job_status(job, AnalysisStatusType.RUNNING)
        
        # Step 1: Scrape realtime data from the content URL
        print(f"Starting realtime content analysis for: {content.title}")
        
        # Import scraping service
        from app.services.content_scraper_service import ContentScraperService
        
        # Scrape realtime data
        scraped_data = None
        try:
            async with ContentScraperService() as scraper:
                scraped_data = await scraper.scrape_content_realtime(content.post_url, content.platform.value)
                print(f"Scraped data: {scraped_data}")
        except Exception as e:
            print(f"Scraping failed, using existing data: {str(e)}")
            scraped_data = None
        
        # Step 2: Process scraped data and update content analysis
        if scraped_data and scraped_data.get('success'):
            # Update content with realtime data
            content.raw_analysis_data = scraped_data.get('data', {})
            
            # Extract engagement data
            engagement_data = scraped_data.get('data', {}).get('engagement', {})
            if engagement_data:
                content.engagement_score = engagement_data.get('total_engagement', 0)
                content.reach_estimate = engagement_data.get('reach', 0)
                content.virality_score = engagement_data.get('virality_score', 0)
            
            # Extract sentiment data
            sentiment_data = scraped_data.get('data', {}).get('sentiment', {})
            if sentiment_data:
                content.sentiment_overall = sentiment_data.get('overall', 0)
                content.sentiment_positive = sentiment_data.get('positive', 0)
                content.sentiment_negative = sentiment_data.get('negative', 0)
                content.sentiment_neutral = sentiment_data.get('neutral', 0)
                content.sentiment_confidence = sentiment_data.get('confidence', 0)
            
            # Extract emotion data
            emotion_data = scraped_data.get('data', {}).get('emotions', {})
            if emotion_data:
                content.emotion_joy = emotion_data.get('joy', 0)
                content.emotion_anger = emotion_data.get('anger', 0)
                content.emotion_fear = emotion_data.get('fear', 0)
                content.emotion_sadness = emotion_data.get('sadness', 0)
                content.emotion_surprise = emotion_data.get('surprise', 0)
                content.emotion_trust = emotion_data.get('trust', 0)
                content.emotion_anticipation = emotion_data.get('anticipation', 0)
                content.emotion_disgust = emotion_data.get('disgust', 0)
                content.dominant_emotion = emotion_data.get('dominant', 'neutral')
            
            # Extract topic data
            topic_data = scraped_data.get('data', {}).get('topics', {})
            if topic_data:
                content.topics = topic_data.get('topics', [])
                content.dominant_topic = topic_data.get('dominant', 'general')
            
            # Calculate content health score
            health_score = 0
            if content.engagement_score and content.engagement_score > 0:
                health_score += 30
            if content.sentiment_overall and content.sentiment_overall > 0:
                health_score += 25
            if content.reach_estimate and content.reach_estimate > 1000:
                health_score += 25
            if content.virality_score and content.virality_score > 0.1:
                health_score += 20
            content.content_health_score = health_score
            
            # Update analysis status
            content.analysis_status = "completed"
            content.analyzed_at = datetime.now()
            
            # Save updated content
            await content.save()
            print(f"Content analysis completed with realtime data")
        
        else:
            # Fallback: Use content analysis service
            print("Using fallback content analysis service")
            from app.services.content_analysis_service import ContentAnalysisService
            content_analysis_service = ContentAnalysisService()
            
            # Use the proper content analysis service
            analysis_result = await content_analysis_service.trigger_content_analysis(str(content.id))
            print(f"Content analysis result: {analysis_result}")
        
        # Update job status to completed
        job = await AnalysisJob.find_one(AnalysisJob.id == job_id)
        if job:
            await db_service.update_job_status(job, AnalysisStatusType.COMPLETED)
        print(f"Content analysis job {job_id} completed successfully")
        
    except Exception as e:
        # Update job status to failed
        job = await AnalysisJob.find_one(AnalysisJob.id == job_id)
        if job:
            await db_service.update_job_status(job, AnalysisStatusType.FAILED)
        print(f"Error in content analysis background task: {str(e)}")
        import traceback
        print(traceback.format_exc())


# ============= CAMPAIGN ANALYSIS ENDPOINTS =============

@router.get("/campaigns/{campaign_id}/summary")
async def get_campaign_analysis_summary(
    campaign_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    platforms: Optional[str] = None,
    days: int = 30
):
    """
    Get campaign analysis summary - similar to brand analysis but for campaigns
    """
    try:
        print(f"🔍 Debug: Looking for campaign with ID: {campaign_id}")
        
        # Get campaign - convert string ID to ObjectId
        from bson import ObjectId
        try:
            campaign = await Campaign.find_one(Campaign.id == ObjectId(campaign_id))
            print(f"🔍 Debug: Campaign found: {campaign}")
        except Exception as e:
            print(f"Error finding campaign: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Invalid campaign ID format: {str(e)}")
        
        if not campaign:
            print(f"🔍 Debug: Campaign not found for ID: {campaign_id}")
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        # Get campaign metrics directly
        print(f"🔍 Debug: Looking for metrics for campaign ID: {campaign.id}")
        try:
            metrics = await CampaignMetrics.find(CampaignMetrics.campaign.id == campaign.id).to_list()
            print(f"🔍 Debug: Found {len(metrics)} metrics")
        except Exception as e:
            print(f"Error finding campaign metrics: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error retrieving campaign metrics: {str(e)}")
        
        if not metrics:
            # Return empty data if no metrics
            return {
                "campaign_name": campaign.campaign_name,
                "period": "Last 30 days",
                "total_posts": 0,
                "total_engagement": 0,
                "avg_engagement_per_post": 0,
                "sentiment_distribution": {
                    "Positive": 0,
                    "Negative": 0,
                    "Neutral": 0
                },
                "sentiment_percentage": {
                    "Positive": 0,
                    "Negative": 0,
                    "Neutral": 0
                },
                "platform_breakdown": {},
                "trending_topics": [],
                "campaign_health_score": 0
            }
        
        # Use latest metrics for summary
        latest_metric = metrics[-1]
        
        # Calculate sentiment distribution
        total_mentions = latest_metric.total_mentions
        positive_count = latest_metric.positive_count
        negative_count = latest_metric.negative_count
        neutral_count = latest_metric.neutral_count
        
        # Calculate engagement metrics
        total_engagement = latest_metric.total_likes + latest_metric.total_comments + latest_metric.total_shares
        
        # Calculate engagement rate using the formula: avg_engagement_per_post / 100
        avg_engagement_per_post = total_engagement / total_mentions if total_mentions > 0 else 0
        engagement_rate = avg_engagement_per_post / 100
        
        # Calculate platform breakdown from campaign metrics
        platform_breakdown = {}
        
        # Get all metrics grouped by platform if available
        all_metrics = await CampaignMetrics.find(CampaignMetrics.campaign.id == campaign.id).to_list()
        
        if all_metrics:
            # Group metrics by platform if platform info is available
            for metric in all_metrics:
                platform_name = getattr(metric, 'platform', 'all')
                if platform_name and platform_name != 'all':
                    if platform_name not in platform_breakdown:
                        platform_breakdown[platform_name] = {
                            "posts": 0,
                            "engagement": 0,
                            "sentiment": 0
                        }
                    platform_breakdown[platform_name]["posts"] += metric.total_mentions
                    platform_breakdown[platform_name]["engagement"] += metric.total_likes + metric.total_comments + metric.total_shares
                    platform_breakdown[platform_name]["sentiment"] += metric.sentiment_score * metric.total_mentions
            
            # Calculate averages for sentiment
            for platform_data in platform_breakdown.values():
                if platform_data["posts"] > 0:
                    platform_data["sentiment"] = round(platform_data["sentiment"] / platform_data["posts"], 3)
        
        # If no platform-specific data, get from posts directly
        if not platform_breakdown:
            # Query posts directly using Post model based on the campaign's brand
            # Note: Post model does not have a direct link to Campaign, only to Brand
            # so we fallback to aggregating posts by the associated brand
            try:
                brand = await campaign.brand.fetch()
            except Exception:
                brand = None
            campaign_posts = []
            if brand:
                campaign_posts = await Post.find(Post.brand.id == brand.id).to_list()
            
            for post in campaign_posts:
                platform_name = post.platform.value
                if platform_name not in platform_breakdown:
                    platform_breakdown[platform_name] = {
                        "posts": 0,
                        "engagement": 0,
                        "sentiment": 0
                    }
                
                platform_breakdown[platform_name]["posts"] += 1
                platform_breakdown[platform_name]["engagement"] += int(post.like_count or 0) + int(post.comment_count or 0) + int(post.share_count or 0)
                
                # Calculate sentiment for this platform
                if post.sentiment is not None:
                    sentiment_value = 1 if post.sentiment.value == "Positive" else -1 if post.sentiment.value == "Negative" else 0
                    platform_breakdown[platform_name]["sentiment"] += sentiment_value
            
            # Calculate platform-specific sentiment scores
            for platform_data in platform_breakdown.values():
                if platform_data["posts"] > 0:
                    platform_data["sentiment"] = round(platform_data["sentiment"] / platform_data["posts"], 3)
        
        return {
            "campaign_name": campaign.campaign_name,
            "period": "Last 30 days",
            "total_posts": total_mentions,  # Use mentions as posts
            "total_engagement": total_engagement,
            "avg_engagement_per_post": avg_engagement_per_post,
            "engagement_rate": engagement_rate,
            "sentiment_distribution": {
                "Positive": positive_count,
                "Negative": negative_count,
                "Neutral": neutral_count
            },
            "sentiment_percentage": {
                "Positive": round(positive_count / total_mentions * 100, 2) if total_mentions > 0 else 0,
                "Negative": round(negative_count / total_mentions * 100, 2) if total_mentions > 0 else 0,
                "Neutral": round(neutral_count / total_mentions * 100, 2) if total_mentions > 0 else 0
            },
            "platform_breakdown": platform_breakdown,
            "trending_topics": [],  # Could be populated from campaign keywords
            "campaign_health_score": latest_metric.sentiment_score
        }
        
    except Exception as e:
        print(f"Error getting campaign summary: {str(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error getting campaign summary: {str(e)}")


@router.get("/campaigns/{campaign_id}/sentiment-timeline")
async def get_campaign_sentiment_timeline(
    campaign_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    platforms: Optional[str] = None,
    days: int = 30
):
    """
    Get campaign sentiment timeline
    """
    try:
        # Get campaign - convert string ID to ObjectId
        from bson import ObjectId
        campaign = await Campaign.find_one(Campaign.id == ObjectId(campaign_id))
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        # Get campaign metrics directly
        metrics = await CampaignMetrics.find(CampaignMetrics.campaign.id == campaign.id).to_list()
        
        if not metrics:
            return {
                "campaign_name": campaign.campaign_name,
                "sentiment_timeline": [],
                "period": "Last 30 days"
            }
        
        # Convert metrics to timeline format (matching brand API format)
        timeline_data = []
        for metric in metrics:
            total_posts = metric.total_mentions
            positive_count = metric.positive_count
            negative_count = metric.negative_count
            neutral_count = metric.neutral_count
            
            # Calculate percentages
            positive_percentage = (positive_count / total_posts * 100) if total_posts > 0 else 0
            negative_percentage = (negative_count / total_posts * 100) if total_posts > 0 else 0
            neutral_percentage = (neutral_count / total_posts * 100) if total_posts > 0 else 0
            
            # Calculate total engagement
            total_engagement = metric.total_likes + metric.total_comments + metric.total_shares
            
            timeline_data.append({
                "date": metric.metric_date.strftime("%Y-%m-%d"),
                "Positive": positive_count,
                "Negative": negative_count,
                "Neutral": neutral_count,
                "positive_percentage": round(positive_percentage, 1),
                "negative_percentage": round(negative_percentage, 1),
                "neutral_percentage": round(neutral_percentage, 1),
                "total_posts": total_posts,
                "total_likes": metric.total_likes,
                "total_comments": metric.total_comments,
                "total_shares": metric.total_shares,
                "avg_sentiment": round(metric.sentiment_score, 3)
            })
        
        # Calculate overall sentiment distribution for frontend
        latest_metric = metrics[-1] if metrics else None
        if latest_metric:
            total_mentions = latest_metric.total_mentions
            positive_count = latest_metric.positive_count
            negative_count = latest_metric.negative_count
            neutral_count = latest_metric.neutral_count
            
            # Calculate percentages
            positive_percentage = (positive_count / total_mentions * 100) if total_mentions > 0 else 0
            negative_percentage = (negative_count / total_mentions * 100) if total_mentions > 0 else 0
            neutral_percentage = (neutral_count / total_mentions * 100) if total_mentions > 0 else 0
            
            # Calculate overall sentiment score
            overall_score = latest_metric.sentiment_score
            confidence_level = min(100, max(0, abs(overall_score) * 100))  # Convert to 0-100 scale
            
            sentiment_distribution = {
                "Positive": positive_count,
                "Negative": negative_count,
                "Neutral": neutral_count
            }
            
            sentiment_percentage = {
                "Positive": round(positive_percentage, 1),
                "Negative": round(negative_percentage, 1),
                "Neutral": round(neutral_percentage, 1)
            }
            
            sentiment_metrics = {
                "overall_score": round(overall_score, 1),
                "confidence_level": round(confidence_level, 1),
                "positive": round(positive_percentage, 1),
                "neutral": round(neutral_percentage, 1),
                "negative": round(negative_percentage, 1)
            }
        else:
            sentiment_distribution = {"Positive": 0, "Negative": 0, "Neutral": 0}
            sentiment_percentage = {"Positive": 0, "Negative": 0, "Neutral": 0}
            sentiment_metrics = {
                "overall_score": 0,
                "confidence_level": 0,
                "positive": 0,
                "neutral": 0,
                "negative": 0
            }

        return {
            "campaign_name": campaign.campaign_name,
            "platform": "all",
            "timeline": timeline_data,
            "period": "Last 30 days",
            "sentiment_distribution": sentiment_distribution,
            "sentiment_percentage": sentiment_percentage,
            "sentiment_metrics": sentiment_metrics
        }
        
    except Exception as e:
        print(f"Error getting campaign sentiment timeline: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting campaign sentiment timeline: {str(e)}")


