import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime
import re

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

