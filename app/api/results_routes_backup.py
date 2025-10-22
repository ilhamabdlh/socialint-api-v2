from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from typing import List, Optional
from datetime import datetime, timedelta

from app.models.database import (
    Brand, Post, Comment, AnalysisJob, AudienceProfile, TopicInterest,
    PlatformType, AnalysisStatusType, BrandAnalysis, BrandMetrics,
    BrandSentimentTimeline, BrandTrendingTopics, BrandDemographics,
    BrandEngagementPatterns, BrandPerformance, BrandEmotions, BrandCompetitive
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

@router.get("/brands/{brand_name}/posts", response_model=List[PostSummary])
async def get_brand_posts(
    brand_name: str,
    platform: Optional[PlatformType] = None,
    sentiment: Optional[str] = None,
    topic: Optional[str] = None,
    limit: int = Query(default=50, le=500)
):
    """Get posts for a brand with filters"""
    brand = await db_service.get_brand(brand_name)
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

@router.get("/brands/{brand_name}/audience-insights", response_model=List[AudienceInsight])
async def get_audience_insights(
    brand_name: str,
    platform: Optional[PlatformType] = None
):
    """Get audience insights for a brand"""
    brand = await db_service.get_brand(brand_name)
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
    total_engagement = sum(p.like_count + p.comment_count + p.share_count for p in posts)
    avg_engagement = total_engagement / len(posts) if posts else 0
    
    sentiment_dist = {"Positive": 0, "Negative": 0, "Neutral": 0}
    for post in posts:
        if post.sentiment:
            sentiment_dist[post.sentiment] += 1
    
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

@router.get("/brands/{brand_name}/sentiment-timeline")
async def get_sentiment_timeline(
    brand_name: str,
    platform: Optional[PlatformType] = None,
    days: int = Query(default=30),
    start_date: Optional[str] = Query(default=None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(default=None, description="End date (YYYY-MM-DD)"),
    platforms: Optional[str] = Query(default=None, description="Comma-separated platform names")
):
    """Get sentiment timeline (daily breakdown) with filtering"""
    brand = await db_service.get_brand(brand_name)
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
            timeline[date_key]["total_likes"] += post.like_count or 0
            timeline[date_key]["total_comments"] += post.comment_count or 0
            timeline[date_key]["total_shares"] += post.share_count or 0
            
            if post.sentiment:
                timeline[date_key][post.sentiment] += 1
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
            timeline[date_key]["total_likes"] += post.like_count or 0
            timeline[date_key]["total_comments"] += post.comment_count or 0
            timeline[date_key]["total_shares"] += post.share_count or 0
            
            if post.sentiment:
                timeline[date_key][post.sentiment] += 1
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

@router.get("/brands/{brand_name}/emotions")
async def get_emotions_analysis(
    brand_name: str,
    platform: Optional[PlatformType] = None,
    limit: int = Query(default=10000),
    start_date: Optional[str] = Query(default=None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(default=None, description="End date (YYYY-MM-DD)"),
    platforms: Optional[str] = Query(default=None, description="Comma-separated platform names")
):
    """
    Get emotions analysis for a brand with filtering
    Returns distribution of emotions: joy, anger, sadness, fear, surprise, disgust, trust, anticipation
    """
    brand = await db_service.get_brand(brand_name)
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

@router.get("/brands/{brand_name}/demographics")
async def get_demographics_analysis(
    brand_name: str,
    platform: Optional[PlatformType] = None,
    limit: int = Query(default=10000),
    start_date: Optional[str] = Query(default=None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(default=None, description="End date (YYYY-MM-DD)"),
    platforms: Optional[str] = Query(default=None, description="Comma-separated platform names")
):
    """
    Get demographics analysis for a brand's audience with filtering
    Returns age groups, gender distribution, and location insights
    """
    brand = await db_service.get_brand(brand_name)
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

@router.get("/brands/{brand_name}/engagement-patterns")
async def get_engagement_patterns(
    brand_name: str,
    platform: Optional[PlatformType] = None,
    limit: int = Query(default=10000),
    start_date: Optional[str] = Query(default=None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(default=None, description="End date (YYYY-MM-DD)"),
    platforms: Optional[str] = Query(default=None, description="Comma-separated platform names")
):
    """
    Get engagement patterns analysis for a brand with filtering
    Returns peak hours, active days, and average engagement rate
    """
    brand = await db_service.get_brand(brand_name)
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

@router.get("/brands/{brand_name}/performance")
async def get_performance_metrics(
    brand_name: str,
    platform: Optional[PlatformType] = None,
    days: int = Query(default=30),
    start_date: Optional[str] = Query(default=None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(default=None, description="End date (YYYY-MM-DD)"),
    platforms: Optional[str] = Query(default=None, description="Comma-separated platform names")
):
    """
    Get performance metrics for a brand with filtering
    Returns engagement rates, reach, and other performance indicators
    """
    brand = await db_service.get_brand(brand_name)
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
    total_likes = sum(p.like_count for p in posts)
    total_comments = sum(p.comment_count for p in posts)
    total_shares = sum(p.share_count for p in posts)
    total_engagement = total_likes + total_comments + total_shares
    
    # Calculate averages
    avg_likes_per_post = total_likes / total_posts if total_posts > 0 else 0
    avg_comments_per_post = total_comments / total_posts if total_posts > 0 else 0
    avg_shares_per_post = total_shares / total_posts if total_posts > 0 else 0
    avg_engagement_per_post = total_engagement / total_posts if total_posts > 0 else 0
    
    # Engagement rate calculation (simplified)
    # Assuming reach is roughly 10x the engagement for social media
    estimated_reach = total_engagement * 10
    engagement_rate = (total_engagement / estimated_reach) * 100 if estimated_reach > 0 else 0
    
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
        platform_breakdown[platform_name]['engagement'] += post.like_count + post.comment_count + post.share_count
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

# ============= COMPETITIVE ANALYSIS ENDPOINTS =============

@router.get("/brands/{brand_name}/competitive")
async def get_competitive_analysis(
    brand_name: str,
    days: int = Query(default=30)
):
    """
    Get competitive analysis for a brand
    Compares brand performance with industry benchmarks
    """
    brand = await db_service.get_brand(brand_name)
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    posts = await db_service.get_posts_by_brand(brand, limit=10000)
    
    # Calculate brand metrics
    total_posts = len(posts)
    total_engagement = sum(p.like_count + p.comment_count + p.share_count for p in posts)
    avg_engagement_per_post = total_engagement / total_posts if total_posts > 0 else 0
    
    # Calculate estimated reach (same as performance endpoint)
    estimated_reach = total_engagement * 10
    
    # Calculate sentiment metrics
    sentiment_counts = {"Positive": 0, "Negative": 0, "Neutral": 0}
    for post in posts:
        if post.sentiment:
            sentiment_counts[post.sentiment] += 1
    
    total_sentiment = sum(sentiment_counts.values())
    sentiment_score = 0
    if total_sentiment > 0:
        sentiment_score = (sentiment_counts["Positive"] - sentiment_counts["Negative"]) / total_sentiment
    
    # Industry benchmarks (mock data - in real implementation, this would come from industry data)
    industry_benchmarks = {
        "avg_engagement_rate": 3.5,  # 3.5% average engagement rate
        "avg_sentiment_score": 0.15,  # 15% positive sentiment advantage
        "avg_posts_per_month": 25,   # Average posts per month
        "top_performers_engagement": 8.2  # Top 10% performers engagement rate
    }
    
    # Calculate competitive position - use the same calculation as performance endpoint
    brand_engagement_rate = (total_engagement / estimated_reach * 100) if estimated_reach > 0 else 0
    
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
        total_engagement = sum(p.like_count + p.comment_count + p.share_count for p in posts)
        avg_engagement_per_post = total_engagement / total_posts if total_posts > 0 else 0
        
        # Sentiment analysis
        sentiment_counts = {"Positive": 0, "Negative": 0, "Neutral": 0}
        sentiment_scores = []
        
        for post in posts:
            if post.sentiment is not None:
                sentiment_scores.append(post.sentiment)
                if post.sentiment > 0.1:
                    sentiment_counts["Positive"] += 1
                elif post.sentiment < -0.1:
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
            platform_breakdown[platform_name]["engagement"] += post.like_count + post.comment_count + post.share_count
            if post.sentiment is not None:
                platform_breakdown[platform_name]["sentiment"] += post.sentiment
        
        # Calculate platform-specific metrics
        for platform_data in platform_breakdown.values():
            if platform_data["posts"] > 0:
                platform_data["avg_engagement"] = round(platform_data["engagement"] / platform_data["posts"], 2)
                platform_data["avg_sentiment"] = round(platform_data["sentiment"] / platform_data["posts"], 3)
        
        # Get trending topics
        topic_interests = await db_service.get_topic_interests_by_brand(brand, platform)
        trending_topics = []
        for topic_interest in topic_interests[:10]:  # Top 10 topics
            trending_topics.append({
                "topic": topic_interest.topic,
                "mentions": topic_interest.mention_count,
                "sentiment": round(topic_interest.avg_sentiment, 2),
                "engagement": topic_interest.total_engagement
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
                    timeline[date_key]["total_sentiment"] += post.sentiment
                    if post.sentiment > 0.1:
                        timeline[date_key]["Positive"] += 1
                    elif post.sentiment < -0.1:
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
        
        # Parse platform filter
        platform = None
        if platforms:
            try:
                platform_list = [PlatformType(p.strip().lower()) for p in platforms.split(',')]
                platform = platform_list[0] if platform_list else platform
            except:
                pass
        
        # Get topic interests
        topic_interests = await db_service.get_topic_interests_by_brand(brand, platform)
        
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
                        total_sentiment = sum(p.sentiment for p in valid_posts if p.sentiment is not None)
                        total_engagement = sum(p.like_count + p.comment_count + p.share_count for p in valid_posts)
                        
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
                        "sentiment": round(topic.avg_sentiment, 2),
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
        
        # Engagement rate calculation
        estimated_reach = total_engagement * 10  # Assuming 10x multiplier for reach
        engagement_rate = (total_engagement / estimated_reach * 100) if estimated_reach > 0 else 0
        
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
            platform_breakdown[platform_name]['engagement'] += post.like_count + post.comment_count + post.share_count
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
        brand_total_engagement = sum(p.like_count + p.comment_count + p.share_count for p in brand_posts)
        brand_avg_engagement = brand_total_engagement / brand_total_posts if brand_total_posts > 0 else 0
        
        # Calculate brand sentiment
        brand_sentiment_scores = [p.sentiment for p in brand_posts if p.sentiment is not None]
        brand_avg_sentiment = sum(brand_sentiment_scores) / len(brand_sentiment_scores) if brand_sentiment_scores else 0
        
        # Industry benchmarks (mock data - in real implementation, this would come from industry data)
        industry_benchmarks = {
            "avg_posts_per_month": 50,
            "avg_engagement_rate": 3.5,
            "avg_sentiment_score": 0.65,
            "avg_reach": 10000
        }
        
        # Calculate performance vs benchmarks
        posts_per_month = brand_total_posts  # Simplified calculation
        engagement_rate = (brand_total_engagement / (brand_total_posts * 1000)) * 100 if brand_total_posts > 0 else 0
        
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
        # Get content by ID
        content = await db_service.get_post_by_id(content_id)
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
        
        # Get related posts for analysis (posts from same brand/platform)
        related_posts = await db_service.get_posts_by_brand(content.brand, platform, limit=1000)
        
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
        
        # Calculate content-specific metrics
        content_engagement = content.like_count + content.comment_count + content.share_count
        content_sentiment = content.sentiment if content.sentiment is not None else 0
        
        # Calculate benchmark metrics from related posts
        total_related_posts = len(related_posts)
        avg_engagement_benchmark = sum(p.like_count + p.comment_count + p.share_count for p in related_posts) / total_related_posts if total_related_posts > 0 else 0
        avg_sentiment_benchmark = sum(p.sentiment for p in related_posts if p.sentiment is not None) / len([p for p in related_posts if p.sentiment is not None]) if any(p.sentiment is not None for p in related_posts) else 0
        
        # Performance comparison
        engagement_performance = "above" if content_engagement > avg_engagement_benchmark else "below"
        sentiment_performance = "above" if content_sentiment > avg_sentiment_benchmark else "below"
        
        # Content health score
        health_score = 0
        if content_engagement > avg_engagement_benchmark:
            health_score += 40
        if content_sentiment > avg_sentiment_benchmark:
            health_score += 30
        if content.like_count > 0:
            health_score += 15
        if content.comment_count > 0:
            health_score += 15
        
        return {
            "content_id": content_id,
            "content_title": getattr(content, 'title', 'Untitled Content'),
            "platform": content.platform.value,
            "period": f"Last {days} days",
            "content_metrics": {
                "likes": content.like_count,
                "comments": content.comment_count,
                "shares": content.share_count,
                "total_engagement": content_engagement,
                "sentiment": round(content_sentiment, 3),
                "engagement_rate": round((content_engagement / max(getattr(content, 'view_count', 1), 1)) * 100, 2)
            },
            "benchmark_comparison": {
                "engagement_performance": engagement_performance,
                "sentiment_performance": sentiment_performance,
                "avg_engagement_benchmark": round(avg_engagement_benchmark, 2),
                "avg_sentiment_benchmark": round(avg_sentiment_benchmark, 3)
            },
            "content_health_score": health_score,
            "content_insights": {
                "best_performing_metric": "likes" if content.like_count >= max(content.comment_count, content.share_count) else "comments" if content.comment_count >= content.share_count else "shares",
                "engagement_trend": "positive" if content_engagement > avg_engagement_benchmark else "negative",
                "sentiment_category": "positive" if content_sentiment > 0.1 else "negative" if content_sentiment < -0.1 else "neutral"
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
        # Get content by ID
        content = await db_service.get_post_by_id(content_id)
        if not content:
            raise HTTPException(status_code=404, detail="Content not found")
        
        # For individual content, we'll analyze sentiment over time based on comments/engagement
        # This is a simplified implementation - in real scenario, you'd track sentiment changes
        
        # Get content creation date
        content_date = content.posted_at or content.created_at
        
        # Create timeline data (simplified - in real implementation, track actual sentiment changes)
        timeline_data = []
        
        # Generate timeline for the past days
        for i in range(days):
            date = datetime.now() - timedelta(days=i)
            date_key = date.strftime("%Y-%m-%d")
            
            # Simulate sentiment variation over time
            base_sentiment = content.sentiment if content.sentiment is not None else 0
            variation = (i % 3 - 1) * 0.1  # Simple variation pattern
            daily_sentiment = base_sentiment + variation
            
            timeline_data.append({
                "date": date_key,
                "sentiment": round(daily_sentiment, 3),
                "engagement": content.like_count + content.comment_count + content.share_count,
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
        content = await db_service.get_post_by_id(content_id)
        if not content:
            raise HTTPException(status_code=404, detail="Content not found")
        
        # Get related topics from content analysis
        content_topic = content.topic if content.topic else "general"
        
        # Get related posts for topic analysis
        related_posts = await db_service.get_posts_by_brand(content.brand, content.platform, limit=1000)
        
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
        
        # Analyze topics from related posts
        topic_analysis = {}
        for post in related_posts:
            if post.topic:
                topic = post.topic.lower()
                if topic not in topic_analysis:
                    topic_analysis[topic] = {
                        "count": 0,
                        "sentiment": 0,
                        "engagement": 0,
                        "positive": 0,
                        "negative": 0,
                        "neutral": 0
                    }
                
                topic_analysis[topic]["count"] += 1
                if post.sentiment is not None:
                    topic_analysis[topic]["sentiment"] += post.sentiment
                    if post.sentiment > 0.1:
                        topic_analysis[topic]["positive"] += 1
                    elif post.sentiment < -0.1:
                        topic_analysis[topic]["negative"] += 1
                    else:
                        topic_analysis[topic]["neutral"] += 1
                
                topic_analysis[topic]["engagement"] += post.like_count + post.comment_count + post.share_count
        
        # Convert to trending topics format
        trending_topics = []
        for topic, data in topic_analysis.items():
            trending_topics.append({
                "topic": topic,
                "count": data["count"],
                "sentiment": round(data["sentiment"] / data["count"], 2) if data["count"] > 0 else 0,
                "engagement": data["engagement"],
                "positive": data["positive"],
                "negative": data["negative"],
                "neutral": data["neutral"]
            })
        
        # Sort by count and limit
        trending_topics = sorted(trending_topics, key=lambda x: x["count"], reverse=True)[:limit]
        
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
        content = await db_service.get_post_by_id(content_id)
        if not content:
            raise HTTPException(status_code=404, detail="Content not found")
        
        # Get content creation time
        content_time = content.posted_at or content.created_at
        
        # Analyze engagement patterns based on content timing
        hour = content_time.hour if content_time else 12
        day_of_week = content_time.strftime("%A") if content_time else "Monday"
        
        # Generate engagement pattern insights
        peak_hours = [f"{hour:02d}:00", f"{(hour + 1) % 24:02d}:00", f"{(hour + 2) % 24:02d}:00"]
        active_days = [day_of_week, "Tuesday", "Wednesday"]  # Simplified pattern
        
        # Calculate engagement rate
        view_count = getattr(content, 'view_count', 1) or 1
        engagement_rate = ((content.like_count + content.comment_count + content.share_count) / view_count) * 100
        
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
        content = await db_service.get_post_by_id(content_id)
        if not content:
            raise HTTPException(status_code=404, detail="Content not found")
        
        # Calculate content performance metrics
        total_engagement = content.like_count + content.comment_count + content.share_count
        view_count = getattr(content, 'view_count', 1) or 1
        
        # Calculate engagement rate
        engagement_rate = (total_engagement / view_count) * 100 if view_count > 0 else 0
        
        # Calculate reach (estimated)
        estimated_reach = view_count * 0.8  # Assume 80% of views are unique reach
        
        # Calculate conversion metrics (simplified)
        conversion_rate = (content.share_count / view_count) * 100 if view_count > 0 else 0
        
        # Performance breakdown by metric
        performance_breakdown = {
            "likes": {
                "count": content.like_count,
                "rate": round((content.like_count / view_count) * 100, 2) if view_count > 0 else 0,
                "impact": "high" if content.like_count > view_count * 0.05 else "medium" if content.like_count > view_count * 0.02 else "low"
            },
            "comments": {
                "count": content.comment_count,
                "rate": round((content.comment_count / view_count) * 100, 2) if view_count > 0 else 0,
                "impact": "high" if content.comment_count > view_count * 0.01 else "medium" if content.comment_count > view_count * 0.005 else "low"
            },
            "shares": {
                "count": content.share_count,
                "rate": round((content.share_count / view_count) * 100, 2) if view_count > 0 else 0,
                "impact": "high" if content.share_count > view_count * 0.01 else "medium" if content.share_count > view_count * 0.005 else "low"
            }
        }
        
        return {
            "content_id": content_id,
            "platform": content.platform.value,
            "period": f"Last {days} days",
            "performance_metrics": {
                "views": view_count,
                "likes": content.like_count,
                "comments": content.comment_count,
                "shares": content.share_count,
                "total_engagement": total_engagement,
                "engagement_rate": round(engagement_rate, 2),
                "estimated_reach": round(estimated_reach, 0),
                "conversion_rate": round(conversion_rate, 2)
            },
            "performance_breakdown": performance_breakdown,
            "content_insights": {
                "best_performing_metric": max(performance_breakdown.keys(), key=lambda k: performance_breakdown[k]["count"]),
                "engagement_quality": "high" if engagement_rate > 5 else "medium" if engagement_rate > 2 else "low",
                "viral_potential": "high" if content.share_count > view_count * 0.02 else "medium" if content.share_count > view_count * 0.01 else "low"
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
        content = await db_service.get_post_by_id(content_id)
        if not content:
            raise HTTPException(status_code=404, detail="Content not found")
        
        # Analyze content emotion
        content_emotion = content.emotion if content.emotion else "neutral"
        content_sentiment = content.sentiment if content.sentiment is not None else 0
        
        # Generate emotion insights based on content performance
        emotion_insights = {
            "primary_emotion": content_emotion,
            "emotion_confidence": min(100, abs(content_sentiment) * 100),  # Convert sentiment to confidence
            "emotional_impact": "high" if abs(content_sentiment) > 0.5 else "medium" if abs(content_sentiment) > 0.2 else "low"
        }
        
        # Calculate emotion-based engagement
        total_engagement = content.like_count + content.comment_count + content.share_count
        emotion_engagement = {
            content_emotion: total_engagement
        }
        
        return {
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
        content = await db_service.get_post_by_id(content_id)
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
                "targeting_effectiveness": "high" if content.like_count > 10 else "medium" if content.like_count > 5 else "low"
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
        content = await db_service.get_post_by_id(content_id)
        if not content:
            raise HTTPException(status_code=404, detail="Content not found")
        
        # Get related content for comparison
        related_content = await db_service.get_posts_by_brand(content.brand, content.platform, limit=100)
        
        # Calculate content metrics
        content_engagement = content.like_count + content.comment_count + content.share_count
        content_sentiment = content.sentiment if content.sentiment is not None else 0
        
        # Calculate benchmark metrics from related content
        if related_content:
            avg_engagement_benchmark = sum(p.like_count + p.comment_count + p.share_count for p in related_content) / len(related_content)
            avg_sentiment_benchmark = sum(p.sentiment for p in related_content if p.sentiment is not None) / len([p for p in related_content if p.sentiment is not None]) if any(p.sentiment is not None for p in related_content) else 0
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
        
        # Validate platforms
        valid_platforms = []
        if platforms:
            for platform in platforms:
                try:
                    valid_platforms.append(PlatformType(platform.lower()))
                except:
                    continue
        
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
            platforms=[p.value for p in valid_platforms] if valid_platforms else ["tiktok", "instagram", "twitter", "youtube"],
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
        # Get content by ID
        content = await db_service.get_post_by_id(content_id)
        if not content:
            raise HTTPException(status_code=404, detail="Content not found")
        
        # Create analysis job
        analysis_job = AnalysisJob(
            brand_id=content.brand.id if content.brand else None,
            content_id=content_id,
            analysis_type="content_analysis",
            status=AnalysisStatusType.PENDING,
            parameters={
                "analysis_type": analysis_type,
                "parameters": parameters or {},
                "platform": content.platform.value,
                "content_url": content.url
            }
        )
        
        # Save analysis job
        job_id = await db_service.create_analysis_job(analysis_job)
        
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
        
        # Import analysis service
        from app.services.analysis_service_v2 import AnalysisServiceV2
        analysis_service = AnalysisServiceV2()
        
        # Run analysis for each platform
        for platform in platforms:
            try:
                # Scrape data for this platform
                if platform == PlatformType.TIKTOK:
                    from app.services.scraper_service import ScraperService
                    scraper = ScraperService()
                    df = await scraper.scrape_tiktok(
                        keywords=keywords,
                        max_posts=100,
                        start_date=start_date,
                        end_date=end_date,
                        brand_name=brand.name
                    )
                elif platform == PlatformType.INSTAGRAM:
                    from app.services.scraper_service import ScraperService
                    scraper = ScraperService()
                    df = await scraper.scrape_instagram(
                        keywords=keywords,
                        max_posts=100,
                        start_date=start_date,
                        end_date=end_date,
                        brand_name=brand.name
                    )
                elif platform == PlatformType.TWITTER:
                    from app.services.scraper_service import ScraperService
                    scraper = ScraperService()
                    df = await scraper.scrape_twitter(
                        keywords=keywords,
                        max_posts=100,
                        start_date=start_date,
                        end_date=end_date,
                        brand_name=brand.name
                    )
                elif platform == PlatformType.YOUTUBE:
                    from app.services.scraper_service import ScraperService
                    scraper = ScraperService()
                    df = await scraper.scrape_youtube(
                        keywords=keywords,
                        max_posts=100,
                        start_date=start_date,
                        end_date=end_date,
                        brand_name=brand.name
                    )
                else:
                    continue
                
                # Process and analyze the data
                if not df.empty:
                    await analysis_service.process_platform_dataframe(
                        df=df,
                        platform=platform.value,
                        brand_name=brand.name,
                        campaign_id=None
                    )
                
            except Exception as e:
                print(f"Error analyzing platform {platform.value}: {str(e)}")
                continue
        
        # Get analysis results and save to new collections
        await save_brand_analysis_results(analysis_id, str(brand.id))
        
        # Update analysis status to completed
        await db_service.update_brand_analysis_status(analysis_id, "completed")
        
    except Exception as e:
        # Update analysis status to failed
        await db_service.update_brand_analysis_status(analysis_id, "failed")
        print(f"Error in brand analysis background task: {str(e)}")

    """
    Generate sample brand analysis data for testing
    """
    try:
        print(f"Generating sample data for brand: {brand_name}")
        
        # Generate sample metrics
        import random
        total_posts = random.randint(50, 200)
        total_engagement = random.randint(1000, 5000)
        
        # Generate sentiment distribution
        sentiment_counts = {
            "Positive": random.randint(30, 60),
            "Negative": random.randint(5, 15),
            "Neutral": random.randint(20, 40)
        }
        
        # Calculate percentages
        total_sentiment = sum(sentiment_counts.values())
        sentiment_percentage = {
            k: round((v / total_sentiment * 100), 1) if total_sentiment > 0 else 0
            for k, v in sentiment_counts.items()
        }
        
        # Save brand metrics
        metrics_data = {
            "total_posts": total_posts,
            "total_engagement": total_engagement,
            "avg_engagement_per_post": round(total_engagement / total_posts, 2),
            "engagement_rate": round((total_engagement / total_posts * 100), 2),
            "sentiment_distribution": sentiment_counts,
            "sentiment_percentage": sentiment_percentage,
            "overall_sentiment_score": round(random.uniform(0.2, 0.8), 2)
        }
        await db_service.save_brand_metrics(analysis_id, brand_id, metrics_data)
        print(f"Saved brand metrics: {metrics_data}")
        
        # Generate sample sentiment timeline
        timeline_data = []
        from datetime import datetime, timedelta
        for i in range(7):  # Last 7 days
            date = datetime.now() - timedelta(days=i)
            timeline_data.append({
                "date": date,
                "sentiment_score": round(random.uniform(-0.5, 0.8), 2),
                "positive_count": random.randint(5, 20),
                "negative_count": random.randint(1, 5),
                "neutral_count": random.randint(3, 10),
                "total_posts": random.randint(10, 30)
            })
        
        await db_service.save_brand_sentiment_timeline(analysis_id, brand_id, timeline_data)
        print(f"Saved sentiment timeline: {len(timeline_data)} records")
        
        # Generate sample trending topics
        topics_data = [
            {"topic": f"{brand_name} smartphone", "topic_count": random.randint(20, 50), "sentiment": round(random.uniform(0.3, 0.8), 2), "engagement": random.randint(100, 500), "positive": random.randint(15, 30), "negative": random.randint(2, 8), "neutral": random.randint(5, 15)},
            {"topic": f"{brand_name} technology", "topic_count": random.randint(15, 40), "sentiment": round(random.uniform(0.2, 0.7), 2), "engagement": random.randint(80, 400), "positive": random.randint(10, 25), "negative": random.randint(1, 5), "neutral": random.randint(4, 12)},
            {"topic": f"{brand_name} review", "topic_count": random.randint(10, 30), "sentiment": round(random.uniform(0.1, 0.6), 2), "engagement": random.randint(60, 300), "positive": random.randint(8, 20), "negative": random.randint(1, 4), "neutral": random.randint(3, 10)},
            {"topic": f"{brand_name} camera", "topic_count": random.randint(8, 25), "sentiment": round(random.uniform(0.4, 0.9), 2), "engagement": random.randint(50, 250), "positive": random.randint(6, 18), "negative": random.randint(1, 3), "neutral": random.randint(2, 8)},
            {"topic": f"{brand_name} battery", "topic_count": random.randint(5, 20), "sentiment": round(random.uniform(0.2, 0.7), 2), "engagement": random.randint(40, 200), "positive": random.randint(4, 15), "negative": random.randint(1, 3), "neutral": random.randint(2, 6)}
        ]
        
        await db_service.save_brand_trending_topics(analysis_id, brand_id, topics_data)
        print(f"Saved trending topics: {len(topics_data)} topics")
        
        # Generate sample demographics
        demographics_data = {
            "platform": "all",
            "total_analyzed": total_posts,
            "age_groups": [
                {"age_group": "18-24", "count": random.randint(20, 40), "percentage": round(random.uniform(25, 45), 1)},
                {"age_group": "25-34", "count": random.randint(15, 35), "percentage": round(random.uniform(20, 40), 1)},
                {"age_group": "35-44", "count": random.randint(10, 25), "percentage": round(random.uniform(15, 30), 1)},
                {"age_group": "45+", "count": random.randint(5, 15), "percentage": round(random.uniform(8, 20), 1)}
            ],
            "genders": [
                {"gender": "male", "count": random.randint(30, 60), "percentage": round(random.uniform(40, 70), 1)},
                {"gender": "female", "count": random.randint(20, 50), "percentage": round(random.uniform(25, 55), 1)},
                {"gender": "neutral", "count": random.randint(5, 15), "percentage": round(random.uniform(5, 20), 1)}
            ],
            "top_locations": [
                {"location": "Indonesia", "count": random.randint(40, 80), "percentage": round(random.uniform(50, 80), 1)},
                {"location": "Malaysia", "count": random.randint(10, 25), "percentage": round(random.uniform(10, 25), 1)},
                {"location": "Singapore", "count": random.randint(5, 15), "percentage": round(random.uniform(5, 15), 1)}
            ]
        }
        await db_service.save_brand_demographics(analysis_id, brand_id, demographics_data)
        print(f"Saved demographics data")
        
        # Generate sample engagement patterns
        patterns_data = {
            "platform": "all",
            "peak_hours": ["09:00", "12:00", "18:00", "21:00"],
            "active_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
            "avg_engagement_rate": round(random.uniform(2.0, 8.0), 2),
            "total_posts": total_posts
        }
        await db_service.save_brand_engagement_patterns(analysis_id, brand_id, patterns_data)
        print(f"Saved engagement patterns")
        
        # Generate sample performance metrics
        performance_data = {
            "total_reach": total_posts * random.randint(50, 100),
            "total_impressions": total_posts * random.randint(200, 500),
            "total_engagement": total_engagement,
            "engagement_rate": round((total_engagement / (total_posts * 100) * 100), 2),
            "estimated_reach": total_posts * random.randint(30, 80),
            "conversion_funnel": {
                "impressions": total_posts * random.randint(200, 500),
                "engagement": total_engagement,
                "clicks": random.randint(total_engagement // 3, total_engagement // 2),
                "conversions": random.randint(total_engagement // 10, total_engagement // 5)
            }
        }
        await db_service.save_brand_performance(analysis_id, brand_id, performance_data)
        print(f"Saved performance data")
        
        # Generate sample emotions
        emotions_data = {
            "total_analyzed": total_posts,
            "dominant_emotion": random.choice(["joy", "neutral", "surprise"]),
            "emotions": {
                "joy": round(random.uniform(0.3, 0.6), 2),
                "sadness": round(random.uniform(0.1, 0.3), 2),
                "anger": round(random.uniform(0.05, 0.2), 2),
                "fear": round(random.uniform(0.05, 0.15), 2),
                "surprise": round(random.uniform(0.1, 0.4), 2),
                "neutral": round(random.uniform(0.2, 0.4), 2)
            }
        }
        await db_service.save_brand_emotions(analysis_id, brand_id, emotions_data)
        print(f"Saved emotions data")
        
        # Generate sample competitive analysis
        competitive_data = {
            "competitive_metrics": {
                "market_share": round(random.uniform(5, 25), 1),
                "brand_awareness": round(random.uniform(60, 90), 1),
                "customer_satisfaction": round(random.uniform(70, 95), 1)
            },
            "market_position": random.choice(["leader", "challenger", "follower", "niche"]),
            "competitive_insights": [
                f"{brand_name} shows strong engagement in smartphone category",
                "Positive sentiment trends indicate good brand perception",
                "Active user base across multiple age groups"
            ],
            "recommendations": [
                "Increase content frequency during peak hours",
                "Focus on trending topics for better reach",
                "Engage more with user-generated content"
            ]
        }
        await db_service.save_brand_competitive(analysis_id, brand_id, competitive_data)
        print(f"Saved competitive analysis")
        
        print(f"=== Sample data generation completed for {brand_name} ===")
        
    except Exception as e:
        print(f"Error generating sample data: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")


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
        total_engagement = sum(post.engagement_count for post in posts if post.engagement_count)
        
        # Calculate sentiment distribution
        sentiment_counts = {"Positive": 0, "Negative": 0, "Neutral": 0}
        for post in posts:
            if post.sentiment_score:
                if post.sentiment_score > 0.1:
                    sentiment_counts["Positive"] += 1
                elif post.sentiment_score < -0.1:
                    sentiment_counts["Negative"] += 1
                else:
                    sentiment_counts["Neutral"] += 1
        
        # Calculate sentiment percentages
        total_sentiment = sum(sentiment_counts.values())
        sentiment_percentage = {
            k: (v / total_sentiment * 100) if total_sentiment > 0 else 0
            for k, v in sentiment_counts.items()
        }
        
        # Save brand metrics
        metrics_data = {
            "total_posts": total_posts,
            "total_engagement": total_engagement,
            "avg_engagement_per_post": total_engagement / total_posts if total_posts > 0 else 0,
            "engagement_rate": (total_engagement / total_posts * 100) if total_posts > 0 else 0,
            "sentiment_distribution": sentiment_counts,
            "sentiment_percentage": sentiment_percentage,
            "overall_sentiment_score": sum(post.sentiment_score for post in posts if post.sentiment_score) / total_posts if total_posts > 0 else 0
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
                if post.sentiment_score:
                    if post.sentiment_score > 0.1:
                        daily_sentiment[date_key]["positive"] += 1
                    elif post.sentiment_score < -0.1:
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
        
        # Save trending topics (simplified)
        topics_data = []
        from collections import Counter
        topic_counts = Counter()
        
        for post in posts:
            if post.topic:
                topic_counts[post.topic] += 1
        
        for topic, count in topic_counts.most_common(10):
            topics_data.append({
                "topic": topic,
                "topic_count": count,
                "sentiment": 0.0,  # Simplified
                "engagement": 0,    # Simplified
                "positive": 0,      # Simplified
                "negative": 0,      # Simplified
                "neutral": 0        # Simplified
            })
        
        if topics_data:
            await db_service.save_brand_trending_topics(analysis_id, brand_id, topics_data)
        
        # Save demographics (simplified)
        demographics_data = {
            "platform": "all",
            "total_analyzed": total_posts,
            "age_groups": [],
            "genders": [],
            "top_locations": []
        }
        await db_service.save_brand_demographics(analysis_id, brand_id, demographics_data)
        
        # Save engagement patterns (simplified)
        patterns_data = {
            "platform": "all",
            "peak_hours": [],
            "active_days": [],
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
        
        # Save emotions (simplified)
        emotions_data = {
            "total_analyzed": total_posts,
            "dominant_emotion": "neutral",
            "emotions": {
                "joy": 0.3,
                "sadness": 0.2,
                "anger": 0.1,
                "fear": 0.1,
                "surprise": 0.1,
                "neutral": 0.2
            }
        }
        await db_service.save_brand_emotions(analysis_id, brand_id, emotions_data)
        
        # Save competitive analysis (simplified)
        competitive_data = {
            "competitive_metrics": {},
            "market_position": "medium",
            "competitive_insights": ["Brand shows moderate engagement", "Sentiment is generally positive"],
            "recommendations": ["Increase content frequency", "Focus on trending topics"]
        }
        await db_service.save_brand_competitive(analysis_id, brand_id, competitive_data)
        
    except Exception as e:
        print(f"Error saving brand analysis results: {str(e)}")


async def run_content_analysis_background(job_id: str, content, analysis_type: str, parameters: dict):
    """
    Background function to run content analysis
    
    This function handles the actual analysis process for individual
    content pieces in the background.
    """
    try:
        # Update job status to running
        await db_service.update_analysis_job_status(job_id, AnalysisStatusType.RUNNING)
        
        # Import analysis service
        from app.services.analysis_service_v2 import AnalysisServiceV2
        analysis_service = AnalysisServiceV2()
        
        # Run content-specific analysis
        if analysis_type == "comprehensive":
            # Perform comprehensive content analysis
            await analysis_service.analyze_content_performance(content)
            await analysis_service.analyze_content_sentiment(content)
            await analysis_service.analyze_content_emotions(content)
            await analysis_service.analyze_content_demographics(content)
        elif analysis_type == "sentiment":
            # Perform sentiment analysis only
            await analysis_service.analyze_content_sentiment(content)
        elif analysis_type == "engagement":
            # Perform engagement analysis only
            await analysis_service.analyze_content_performance(content)
        else:
            # Default to comprehensive analysis
            await analysis_service.analyze_content_performance(content)
            await analysis_service.analyze_content_sentiment(content)
        
        # Update job status to completed
        await db_service.update_analysis_job_status(job_id, AnalysisStatusType.COMPLETED)
        
    except Exception as e:
        # Update job status to failed
        await db_service.update_analysis_job_status(job_id, AnalysisStatusType.FAILED)
        print(f"Error in content analysis background task: {str(e)}")


