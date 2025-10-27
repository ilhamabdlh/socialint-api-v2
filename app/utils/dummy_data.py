"""
Dummy data utilities for debugging scraping
"""

def get_tiktok_dummy_data(url: str, source: str = "post_urls") -> dict:
    """Generate dummy TikTok data with all required fields"""
    return {
        "source": source,
        "url": url,
        "type": "direct_url" if source == "post_urls" else "search",
        "title": f"TikTok Video - {url.split('/')[-1]}",
        "description": "Dummy TikTok video description",
        "author": "dummy_author",
        "likeCount": 100,
        "commentCount": 10,
        "shareCount": 5,
        "viewCount": 1000,
        "createdAt": "2025-10-25T10:00:00Z"
    }

def get_instagram_dummy_data(url: str, source: str = "post_urls") -> dict:
    """Generate dummy Instagram data with all required fields"""
    return {
        "source": source,
        "url": url,
        "type": "direct_url" if source == "post_urls" else "search",
        "caption": f"Instagram post about {url.split('/')[-1]}",
        "description": "Dummy Instagram post description",
        "author": "dummy_author",
        "likeCount": 200,
        "commentCount": 20,
        "shareCount": 10,
        "viewCount": 2000,
        "createdAt": "2025-10-25T10:00:00Z"
    }

def get_twitter_dummy_data(url: str, source: str = "post_urls") -> dict:
    """Generate dummy Twitter data with all required fields"""
    return {
        "source": source,
        "url": url,
        "type": "direct_url" if source == "post_urls" else "search",
        "text": f"Twitter post about {url.split('/')[-1]}",
        "description": "Dummy Twitter post description",
        "author": "dummy_author",
        "likeCount": 50,
        "commentCount": 5,
        "shareCount": 2,
        "viewCount": 500,
        "createdAt": "2025-10-25T10:00:00Z"
    }

def get_youtube_dummy_data(url: str, source: str = "post_urls") -> dict:
    """Generate dummy YouTube data with all required fields"""
    return {
        "source": source,
        "url": url,
        "type": "direct_url" if source == "post_urls" else "search",
        "title": f"YouTube Video - {url.split('/')[-1]}",
        "description": "Dummy YouTube video description",
        "author": "dummy_author",
        "likeCount": 300,
        "commentCount": 30,
        "shareCount": 15,
        "viewCount": 3000,
        "createdAt": "2025-10-25T10:00:00Z"
    }

