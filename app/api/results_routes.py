from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timedelta

from app.models.database import (
    Brand, Post, Comment, AnalysisJob, AudienceProfile, TopicInterest,
    PlatformType, AnalysisStatusType
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

@router.get("/brands/{brand_identifier}/summary")
async def get_brand_summary(
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
    
    
    # Debug logging
    print(f"🔍 Timeline has {len(timeline)} date entries")
    if timeline:
        print(f"🔍 Timeline dates: {list(timeline.keys())}")
        for date, data in timeline.items():
            print(f"🔍 {date}: {data['total_posts']} posts, {data['Positive']} positive, {data['Negative']} negative, {data['Neutral']} neutral")
    
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
        posts_data.append({
            'like_count': post.like_count or 0,
            'comment_count': post.comment_count or 0,
            'share_count': post.share_count or 0,
            'view_count': getattr(post, 'view_count', 1) or 1,
            'posted_at': post.posted_at
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


