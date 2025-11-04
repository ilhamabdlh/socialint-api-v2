#!/usr/bin/env python3
"""
Detailed analysis of hashtags with relevance scoring
"""

import json
import re
from collections import Counter, defaultdict
from typing import Dict, List, Set, Tuple

def extract_hashtags_from_text(text: str) -> List[str]:
    """Extract hashtags from text using regex"""
    if not text:
        return []
    
    # Find all hashtags (words starting with #)
    hashtags = re.findall(r'#(\w+)', text.lower())
    return hashtags

def calculate_hashtag_relevance_score(hashtag: str, brand_keywords: Set[str]) -> int:
    """Calculate relevance score for a hashtag based on brand keywords"""
    score = 0
    hashtag_lower = hashtag.lower()
    
    # Direct brand keyword matches
    for keyword in brand_keywords:
        if keyword in hashtag_lower:
            if keyword == hashtag_lower:  # Exact match
                score += 10
            elif hashtag_lower.startswith(keyword):  # Starts with brand
                score += 8
            else:  # Contains brand
                score += 5
    
    # Boost for specific Audi-related terms
    audi_terms = {
        'quattro': 8,
        'vorsprungdurchtechnik': 7,
        'rs': 6,
        'sport': 5,
        'a3': 4, 'a4': 4, 'a5': 4, 'a6': 4, 'a7': 4, 'a8': 4,
        'q3': 4, 'q5': 4, 'q7': 4, 'q8': 4,
        'tt': 4, 'r8': 4
    }
    
    for term, term_score in audi_terms.items():
        if term in hashtag_lower:
            score += term_score
    
    # Boost for engagement-related terms
    engagement_terms = ['love', 'fans', 'club', 'world', 'official', 'life', 'gram']
    for term in engagement_terms:
        if term in hashtag_lower:
            score += 2
    
    return score

def analyze_platform_hashtags(file_path: str, platform: str) -> Dict:
    """Analyze hashtags for a specific platform with engagement data"""
    print(f"📊 Analyzing {platform} data from {file_path}")
    
    hashtag_data = defaultdict(lambda: {
        'count': 0,
        'total_engagement': 0,
        'posts': [],
        'relevance_score': 0
    })
    
    brand_keywords = {'audi', 'quattro', 'vorsprungdurchtechnik'}
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for item in data:
            # Extract hashtags
            hashtags = []
            
            if platform == 'instagram':
                # From caption
                if 'caption' in item and item['caption']:
                    hashtags.extend(extract_hashtags_from_text(item['caption']))
                
                # From hashtags array
                if 'hashtags' in item and item['hashtags']:
                    for hashtag in item['hashtags']:
                        if hashtag and isinstance(hashtag, str):
                            clean_hashtag = hashtag.lower().replace('#', '')
                            hashtags.append(clean_hashtag)
                
                # From related hashtags
                for key in ['related', 'relatedFrequent', 'relatedAverage', 'relatedRare']:
                    if key in item and item[key]:
                        for related in item[key]:
                            if 'hash' in related and related['hash']:
                                clean_hashtag = related['hash'].lower().replace('#', '')
                                hashtags.append(clean_hashtag)
                
                # Get engagement data
                engagement = 0
                if 'likesCount' in item and item['likesCount']:
                    engagement += item['likesCount']
                if 'commentsCount' in item and item['commentsCount']:
                    engagement += item['commentsCount']
                if 'shareCount' in item and item['shareCount']:
                    engagement += item['shareCount']
            
            elif platform == 'tiktok':
                # From text
                if 'text' in item and item['text']:
                    hashtags.extend(extract_hashtags_from_text(item['text']))
                
                # From hashtags array
                if 'hashtags' in item and item['hashtags']:
                    for hashtag_obj in item['hashtags']:
                        if isinstance(hashtag_obj, dict) and 'name' in hashtag_obj:
                            clean_hashtag = hashtag_obj['name'].lower()
                            hashtags.append(clean_hashtag)
                
                # Get engagement data
                engagement = 0
                if 'diggCount' in item and item['diggCount']:
                    engagement += item['diggCount']
                if 'commentCount' in item and item['commentCount']:
                    engagement += item['commentCount']
                if 'shareCount' in item and item['shareCount']:
                    engagement += item['shareCount']
            
            elif platform == 'twitter':
                # From text and fullText
                for text_field in ['text', 'fullText']:
                    if text_field in item and item[text_field]:
                        hashtags.extend(extract_hashtags_from_text(item[text_field]))
                
                # Get engagement data
                engagement = 0
                if 'likeCount' in item and item['likeCount']:
                    engagement += item['likeCount']
                if 'replyCount' in item and item['replyCount']:
                    engagement += item['replyCount']
                if 'retweetCount' in item and item['retweetCount']:
                    engagement += item['retweetCount']
            
            # Process each hashtag
            for hashtag in hashtags:
                if hashtag and len(hashtag) > 1:  # Filter out single characters
                    hashtag_data[hashtag]['count'] += 1
                    hashtag_data[hashtag]['total_engagement'] += engagement
                    hashtag_data[hashtag]['posts'].append({
                        'platform': platform,
                        'engagement': engagement,
                        'item_id': item.get('id', 'unknown')
                    })
    
    except Exception as e:
        print(f"❌ Error reading {platform} file: {e}")
        return {}
    
    # Calculate relevance scores
    for hashtag, data in hashtag_data.items():
        data['relevance_score'] = calculate_hashtag_relevance_score(hashtag, brand_keywords)
        data['avg_engagement'] = data['total_engagement'] / data['count'] if data['count'] > 0 else 0
    
    return dict(hashtag_data)

def main():
    """Main function for detailed hashtag analysis"""
    print("🔍 DETAILED HASHTAG ANALYSIS")
    print("=" * 80)
    
    # File paths
    files = {
        'instagram': 'data/scraped_data/dataset_instagram-scraper_audi-v2.json',
        'tiktok': 'data/scraped_data/dataset_tiktok-scraper_audi-v2.json',
        'twitter': 'data/scraped_data/dataset_twitter-scraper_audi-v2.json'
    }
    
    # Analyze each platform
    all_platform_data = {}
    for platform, file_path in files.items():
        all_platform_data[platform] = analyze_platform_hashtags(file_path, platform)
    
    # Combine all hashtags
    combined_hashtags = defaultdict(lambda: {
        'count': 0,
        'total_engagement': 0,
        'platforms': set(),
        'relevance_score': 0,
        'avg_engagement': 0
    })
    
    for platform, hashtag_data in all_platform_data.items():
        for hashtag, data in hashtag_data.items():
            combined_hashtags[hashtag]['count'] += data['count']
            combined_hashtags[hashtag]['total_engagement'] += data['total_engagement']
            combined_hashtags[hashtag]['platforms'].add(platform)
            combined_hashtags[hashtag]['relevance_score'] = max(
                combined_hashtags[hashtag]['relevance_score'], 
                data['relevance_score']
            )
    
    # Calculate average engagement
    for hashtag, data in combined_hashtags.items():
        data['avg_engagement'] = data['total_engagement'] / data['count'] if data['count'] > 0 else 0
        data['platforms'] = list(data['platforms'])
    
    # Sort by relevance score, then by count, then by engagement
    sorted_hashtags = sorted(
        combined_hashtags.items(),
        key=lambda x: (x[1]['relevance_score'], x[1]['count'], x[1]['total_engagement']),
        reverse=True
    )
    
    print("\n🏆 TOP 30 MOST RELEVANT HASHTAGS")
    print("=" * 80)
    print(f"{'Rank':<4} {'Hashtag':<25} {'Count':<6} {'Engagement':<12} {'Relevance':<9} {'Platforms':<15}")
    print("-" * 80)
    
    for i, (hashtag, data) in enumerate(sorted_hashtags[:30], 1):
        platforms_str = ', '.join(data['platforms'])
        print(f"{i:<4} #{hashtag:<24} {data['count']:<6} {data['total_engagement']:<12,} {data['relevance_score']:<9} {platforms_str:<15}")
    
    # Filter highly relevant hashtags (relevance score > 5)
    highly_relevant = [(h, d) for h, d in sorted_hashtags if d['relevance_score'] > 5]
    
    print(f"\n🎯 HIGHLY RELEVANT HASHTAGS (Score > 5)")
    print("=" * 80)
    print(f"Found {len(highly_relevant)} highly relevant hashtags:")
    print(f"{'Rank':<4} {'Hashtag':<25} {'Count':<6} {'Engagement':<12} {'Relevance':<9} {'Platforms':<15}")
    print("-" * 80)
    
    for i, (hashtag, data) in enumerate(highly_relevant, 1):
        platforms_str = ', '.join(data['platforms'])
        print(f"{i:<4} #{hashtag:<24} {data['count']:<6} {data['total_engagement']:<12,} {data['relevance_score']:<9} {platforms_str:<15}")
    
    # Most used hashtags (by count)
    most_used = sorted(combined_hashtags.items(), key=lambda x: x[1]['count'], reverse=True)
    
    print(f"\n📈 MOST USED HASHTAGS (By Count)")
    print("=" * 80)
    print(f"{'Rank':<4} {'Hashtag':<25} {'Count':<6} {'Engagement':<12} {'Relevance':<9} {'Platforms':<15}")
    print("-" * 80)
    
    for i, (hashtag, data) in enumerate(most_used[:20], 1):
        platforms_str = ', '.join(data['platforms'])
        print(f"{i:<4} #{hashtag:<24} {data['count']:<6} {data['total_engagement']:<12,} {data['relevance_score']:<9} {platforms_str:<15}")
    
    # High engagement hashtags
    high_engagement = sorted(combined_hashtags.items(), key=lambda x: x[1]['total_engagement'], reverse=True)
    
    print(f"\n🔥 HIGH ENGAGEMENT HASHTAGS")
    print("=" * 80)
    print(f"{'Rank':<4} {'Hashtag':<25} {'Count':<6} {'Engagement':<12} {'Relevance':<9} {'Platforms':<15}")
    print("-" * 80)
    
    for i, (hashtag, data) in enumerate(high_engagement[:20], 1):
        platforms_str = ', '.join(data['platforms'])
        print(f"{i:<4} #{hashtag:<24} {data['count']:<6} {data['total_engagement']:<12,} {data['relevance_score']:<9} {platforms_str:<15}")
    
    # Summary statistics
    print(f"\n📊 SUMMARY STATISTICS")
    print("=" * 80)
    total_hashtags = len(combined_hashtags)
    total_mentions = sum(data['count'] for data in combined_hashtags.values())
    total_engagement = sum(data['total_engagement'] for data in combined_hashtags.values())
    avg_engagement = total_engagement / total_mentions if total_mentions > 0 else 0
    
    print(f"Total unique hashtags: {total_hashtags}")
    print(f"Total hashtag mentions: {total_mentions}")
    print(f"Total engagement: {total_engagement:,}")
    print(f"Average engagement per mention: {avg_engagement:.2f}")
    print(f"Highly relevant hashtags (score > 5): {len(highly_relevant)}")

if __name__ == "__main__":
    main()


