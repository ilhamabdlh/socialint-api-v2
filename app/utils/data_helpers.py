import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime
import re
from collections import Counter

def remove_duplicates(data: List[str], platform: str) -> List[str]:
    """Remove duplicate texts from list"""
    unique_data = []
    for text in data:
        if text not in unique_data:
            unique_data.append(text)
    return unique_data

def explicit_keywords_cleansing(data: List[str], keywords: List[str]) -> List[str]:
    """Filter data that contains at least one keyword"""
    cleaned_data = []
    for text in data:
        if isinstance(text, str) and any(keyword.lower() in text.lower() for keyword in keywords):
            cleaned_data.append(text)
    return cleaned_data

def normalize_topic_labeling(topics: List[str]) -> Dict[str, str]:
    """
    Normalize topic labels to handle case variations and similar topics
    e.g., "Indonesian politics", "Indonesian Politics", "indonesian politic" -> "indonesian politics"
    """
    if not topics:
        return {}
    
    # Create mapping from normalized to original topics
    normalized_map = {}
    topic_counts = Counter()
    
    for topic in topics:
        if not isinstance(topic, str) or not topic.strip():
            continue
            
        # Normalize: lowercase, strip, remove extra spaces
        normalized = re.sub(r'\s+', ' ', topic.strip().lower())
        
        # Count occurrences
        topic_counts[normalized] += 1
        
        # Keep track of original topic for mapping
        if normalized not in normalized_map:
            normalized_map[normalized] = topic
    
    # Create final mapping from original topics to normalized topics
    final_mapping = {}
    for topic in topics:
        if not isinstance(topic, str) or not topic.strip():
            continue
            
        normalized = re.sub(r'\s+', ' ', topic.strip().lower())
        final_mapping[topic] = normalized
    
    return final_mapping

def consolidate_demographics(demographics: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Consolidate duplicate demographic data
    Merge overlapping age groups and gender categories
    """
    if not demographics:
        return {}
    
    # Process age groups
    age_groups = {}
    for demo in demographics:
        age_group = demo.get('age_group', 'unknown')
        if age_group and age_group != 'unknown':
            # Normalize age group labels
            normalized_age = normalize_age_group(age_group)
            if normalized_age in age_groups:
                age_groups[normalized_age] += 1
            else:
                age_groups[normalized_age] = 1
    
    # Process gender distribution
    gender_dist = {}
    for demo in demographics:
        gender = demo.get('gender', 'unknown')
        if gender and gender != 'unknown':
            # Normalize gender labels - merge 'or' combinations into neutral
            normalized_gender = normalize_gender(gender)
            if normalized_gender in gender_dist:
                gender_dist[normalized_gender] += 1
            else:
                gender_dist[normalized_gender] = 1
    
    # Process location distribution
    locations = {}
    for demo in demographics:
        location = demo.get('location_hint', 'unknown')
        if location and location != 'unknown':
            # Normalize location labels
            normalized_location = normalize_location(location)
            if normalized_location in locations:
                locations[normalized_location] += 1
            else:
                locations[normalized_location] = 1
    
    return {
        'age_groups': age_groups,
        'gender_distribution': gender_dist,
        'locations': locations
    }

def normalize_age_group(age_group: str) -> str:
    """Normalize age group labels"""
    if not age_group:
        return 'unknown'
    
    # Convert to lowercase and handle common variations
    normalized = age_group.lower().strip()
    
    # Handle overlapping age groups
    if '18-24' in normalized or '18-24 or' in normalized:
        return '18-24'
    elif '25-34' in normalized and '35-44' not in normalized and '45-54' not in normalized:
        return '25-34'
    elif '35-44' in normalized and '45-54' not in normalized:
        return '35-44'
    elif '45-54' in normalized and '55+' not in normalized:
        return '45-54'
    elif '55+' in normalized:
        return '55+'
    elif '35-54' in normalized:
        return '35-54'
    
    return normalized

def normalize_gender(gender: str) -> str:
    """Normalize gender labels - merge 'or' combinations into neutral"""
    if not gender:
        return 'unknown'
    
    normalized = gender.lower().strip()
    
    # If contains 'or' combinations, merge into neutral
    if ' or ' in normalized or 'or' in normalized:
        return 'neutral'
    
    # Handle common gender labels
    if 'male' in normalized and 'female' not in normalized and 'neutral' not in normalized:
        return 'male'
    elif 'female' in normalized and 'male' not in normalized and 'neutral' not in normalized:
        return 'female'
    elif 'neutral' in normalized or 'unknown' in normalized:
        return 'neutral'
    
    return normalized

def get_platform_text_column(platform: str, layer: int = 1) -> str:
    """Get the appropriate text column name based on platform and layer"""
    if layer == 1:
        mapping = {
            'tiktok': 'title',
            'youtube': 'title',
            'twitter': 'text',
            'instagram': 'caption'
        }
    else:  # layer 2 (comments)
        mapping = {
            'tiktok': 'text',
            'youtube': 'text',
            'twitter': 'text',
            'instagram': 'text'
        }
    return mapping.get(platform, 'text')

def prepare_dataframe(df: pd.DataFrame, platform: str) -> pd.DataFrame:
    """Platform-specific dataframe preparation"""
    df = df.copy()
    
    # Instagram-specific: unpack topPosts
    if platform == 'instagram' and 'topPosts' in df.columns:
        df = df.explode('topPosts')
        df = pd.json_normalize(df['topPosts'])
        df = df.drop_duplicates(subset=['id'])
        df = df.reset_index(drop=True)
    
    # TikTok-specific: rename columns
    if platform == 'tiktok':
        if 'title' not in df.columns and 'text' in df.columns:
            df['title'] = df['text']
        if 'postPage' not in df.columns and 'webVideoUrl' in df.columns:
            df['postPage'] = df['webVideoUrl']
        if 'description' not in df.columns:
            df['description'] = df['text'] if 'text' in df.columns else ''
    
    return df

def update_dataframe(df: pd.DataFrame, data: List[str], platform: str, layer: int) -> pd.DataFrame:
    """Filter dataframe to keep only rows with text in data list"""
    text_col = get_platform_text_column(platform, layer)
    
    if text_col in df.columns:
        df = df[df[text_col].isin(data)].reset_index(drop=True)
    
    return df

def calculate_sentiment_distribution(sentiments: List[str]) -> Dict[str, int]:
    """Calculate sentiment distribution"""
    dist = {'Positive': 0, 'Negative': 0, 'Neutral': 0}
    for sentiment in sentiments:
        if sentiment in dist:
            dist[sentiment] += 1
    return dist

def validate_post_urls(df: pd.DataFrame, platform: str) -> pd.DataFrame:
    """
    Validate and filter posts with correct URLs for each platform
    Removes rows with invalid or missing URLs
    """
    df = df.copy()
    
    # Platform-specific URL validation patterns
    url_patterns = {
        'tiktok': r'(tiktok\.com|vm\.tiktok\.com)',
        'instagram': r'instagram\.com',
        'twitter': r'(twitter\.com|x\.com)',
        'youtube': r'(youtube\.com|youtu\.be)',
        'linkedin': r'linkedin\.com',
        'facebook': r'facebook\.com',
        'reddit': r'reddit\.com'
    }
    
    # Platform-specific URL column names
    url_columns = {
        'tiktok': 'webVideoUrl',
        'instagram': 'url',
        'twitter': 'url',
        'youtube': 'url',
        'linkedin': 'url',
        'facebook': 'url',
        'reddit': 'url'
    }
    
    platform_lower = platform.lower()
    
    if platform_lower not in url_patterns:
        print(f"⚠️  Warning: URL validation pattern not defined for platform '{platform}'")
        return df
    
    url_col = url_columns.get(platform_lower, 'url')
    
    # Check if URL column exists
    if url_col not in df.columns:
        # Try alternative column names
        alt_cols = ['postPage', 'post_url', 'link', 'permalink']
        for alt_col in alt_cols:
            if alt_col in df.columns:
                url_col = alt_col
                break
        else:
            print(f"⚠️  Warning: No URL column found for platform '{platform}'")
            return df
    
    initial_count = len(df)
    pattern = url_patterns[platform_lower]
    
    # Filter rows where URL matches the platform pattern
    df = df[df[url_col].astype(str).str.contains(pattern, case=False, na=False, regex=True)]
    
    removed_count = initial_count - len(df)
    if removed_count > 0:
        print(f"✓ Removed {removed_count} posts with invalid URLs for {platform}")
    
    return df.reset_index(drop=True)

def filter_by_date_range(
    df: pd.DataFrame, 
    start_date: Optional[str] = None, 
    end_date: Optional[str] = None,
    date_column: Optional[str] = None
) -> pd.DataFrame:
    """
    Filter dataframe to keep only posts within the specified date range
    
    Args:
        df: Input dataframe
        start_date: Start date in format 'YYYY-MM-DD' or None
        end_date: End date in format 'YYYY-MM-DD' or None
        date_column: Column name containing dates, if None will auto-detect
    
    Returns:
        Filtered dataframe
    """
    if start_date is None and end_date is None:
        return df
    
    df = df.copy()
    
    # Auto-detect date column if not provided
    if date_column is None:
        date_cols = ['createTimeISO', 'created_at', 'timestamp', 'date', 'posted_at', 'createdAt']
        for col in date_cols:
            if col in df.columns:
                date_column = col
                break
        
        if date_column is None:
            print(f"⚠️  Warning: No date column found in dataframe")
            return df
    
    if date_column not in df.columns:
        print(f"⚠️  Warning: Date column '{date_column}' not found")
        return df
    
    initial_count = len(df)
    
    # Convert date column to datetime
    try:
        df['_temp_date'] = pd.to_datetime(df[date_column], errors='coerce')
    except Exception as e:
        print(f"⚠️  Warning: Could not parse dates in column '{date_column}': {e}")
        return df
    
    # Remove rows with invalid dates
    df = df[df['_temp_date'].notna()]
    
    # Apply date filters
    if start_date:
        try:
            start_dt = pd.to_datetime(start_date)
            df = df[df['_temp_date'] >= start_dt]
        except Exception as e:
            print(f"⚠️  Warning: Invalid start_date format '{start_date}': {e}")
    
    if end_date:
        try:
            end_dt = pd.to_datetime(end_date)
            # Include the entire end date (until 23:59:59)
            end_dt = end_dt + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
            df = df[df['_temp_date'] <= end_dt]
        except Exception as e:
            print(f"⚠️  Warning: Invalid end_date format '{end_date}': {e}")
    
    # Clean up temporary column
    df = df.drop('_temp_date', axis=1)
    
    removed_count = initial_count - len(df)
    if removed_count > 0:
        date_range_str = f"{start_date or 'beginning'} to {end_date or 'now'}"
        print(f"✓ Removed {removed_count} posts outside date range ({date_range_str})")
    
    return df.reset_index(drop=True)

def analyze_engagement_patterns(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Analyze engagement patterns to find peak hours, active days, and average engagement rate
    """
    if df.empty:
        return {
            'peak_hours': [],
            'active_days': [],
            'avg_engagement_rate': 0.0
        }
    
    # Calculate engagement rate for each post
    if 'like_count' in df.columns and 'comment_count' in df.columns and 'share_count' in df.columns:
        df['engagement_rate'] = (df['like_count'] + df['comment_count'] + df['share_count']) / df.get('view_count', 1)
    else:
        df['engagement_rate'] = 0
    
    # Extract time patterns if timestamp is available
    peak_hours = []
    active_days = []
    
    if 'posted_at' in df.columns:
        # Convert to datetime if needed
        df['posted_at'] = pd.to_datetime(df['posted_at'], errors='coerce')
        
        # Extract hour and day of week
        df['hour'] = df['posted_at'].dt.hour
        df['day_of_week'] = df['posted_at'].dt.day_name()
        
        # Find peak hours (top 3 hours with highest engagement)
        if not df['hour'].isna().all():
            hour_engagement = df.groupby('hour')['engagement_rate'].mean().sort_values(ascending=False)
            peak_hours = [f"{int(hour):02d}:00" for hour in hour_engagement.head(3).index if not pd.isna(hour)]
        
        # Find active days (top 3 days with highest engagement)
        if not df['day_of_week'].isna().all():
            day_engagement = df.groupby('day_of_week')['engagement_rate'].mean().sort_values(ascending=False)
            active_days = day_engagement.head(3).index.tolist()
    
    # Calculate average engagement rate
    avg_engagement_rate = df['engagement_rate'].mean() if not df['engagement_rate'].isna().all() else 0.0
    
    return {
        'peak_hours': peak_hours,
        'active_days': active_days,
        'avg_engagement_rate': round(avg_engagement_rate * 100, 2)  # Convert to percentage
    }

def normalize_location(location: str) -> str:
    """Normalize location labels - merge case variations"""
    if not location:
        return 'unknown'
    
    # Convert to lowercase and strip whitespace
    normalized = location.lower().strip()
    
    # Handle common location variations
    if 'indonesia' in normalized:
        return 'Indonesia'
    elif 'jakarta' in normalized:
        return 'Jakarta, Indonesia'
    elif 'solo' in normalized:
        return 'Solo, Indonesia'
    elif 'maluku' in normalized:
        return 'Maluku, Indonesia'
    elif 'ambon' in normalized:
        return 'Ambon, Indonesia'
    
    # For other locations, capitalize first letter of each word
    return ' '.join(word.capitalize() for word in normalized.split())

