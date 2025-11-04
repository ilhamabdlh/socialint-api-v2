#!/usr/bin/env python3
"""
Script untuk menganalisis hashtags dari file scraped data
"""

import json
import re
from collections import Counter
from typing import Dict, List, Set

def extract_hashtags_from_text(text: str) -> List[str]:
    """Extract hashtags from text using regex"""
    if not text:
        return []
    
    # Find all hashtags (words starting with #)
    hashtags = re.findall(r'#(\w+)', text.lower())
    return hashtags

def analyze_instagram_data(file_path: str) -> Dict:
    """Analyze Instagram data for hashtags"""
    print(f"📱 Analyzing Instagram data from {file_path}")
    
    hashtag_counts = Counter()
    related_hashtags = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for item in data:
            # Extract hashtags from caption
            if 'caption' in item and item['caption']:
                hashtags = extract_hashtags_from_text(item['caption'])
                hashtag_counts.update(hashtags)
                related_hashtags.extend(hashtags)
            
            # Extract hashtags from hashtags array
            if 'hashtags' in item and item['hashtags']:
                for hashtag in item['hashtags']:
                    if hashtag and isinstance(hashtag, str):
                        clean_hashtag = hashtag.lower().replace('#', '')
                        hashtag_counts[clean_hashtag] += 1
                        related_hashtags.append(clean_hashtag)
            
            # Extract hashtags from related hashtags data
            if 'related' in item and item['related']:
                for related in item['related']:
                    if 'hash' in related and related['hash']:
                        clean_hashtag = related['hash'].lower().replace('#', '')
                        hashtag_counts[clean_hashtag] += 1
                        related_hashtags.append(clean_hashtag)
            
            # Extract hashtags from relatedFrequent, relatedAverage, relatedRare
            for key in ['relatedFrequent', 'relatedAverage', 'relatedRare']:
                if key in item and item[key]:
                    for related in item[key]:
                        if 'hash' in related and related['hash']:
                            clean_hashtag = related['hash'].lower().replace('#', '')
                            hashtag_counts[clean_hashtag] += 1
                            related_hashtags.append(clean_hashtag)
    
    except Exception as e:
        print(f"❌ Error reading Instagram file: {e}")
        return {}
    
    return {
        'platform': 'Instagram',
        'total_hashtags': len(related_hashtags),
        'unique_hashtags': len(hashtag_counts),
        'top_hashtags': hashtag_counts.most_common(20),
        'all_hashtags': related_hashtags
    }

def analyze_tiktok_data(file_path: str) -> Dict:
    """Analyze TikTok data for hashtags"""
    print(f"🎵 Analyzing TikTok data from {file_path}")
    
    hashtag_counts = Counter()
    related_hashtags = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for item in data:
            # Extract hashtags from text
            if 'text' in item and item['text']:
                hashtags = extract_hashtags_from_text(item['text'])
                hashtag_counts.update(hashtags)
                related_hashtags.extend(hashtags)
            
            # Extract hashtags from hashtags array
            if 'hashtags' in item and item['hashtags']:
                for hashtag_obj in item['hashtags']:
                    if isinstance(hashtag_obj, dict) and 'name' in hashtag_obj:
                        clean_hashtag = hashtag_obj['name'].lower()
                        hashtag_counts[clean_hashtag] += 1
                        related_hashtags.append(clean_hashtag)
    
    except Exception as e:
        print(f"❌ Error reading TikTok file: {e}")
        return {}
    
    return {
        'platform': 'TikTok',
        'total_hashtags': len(related_hashtags),
        'unique_hashtags': len(hashtag_counts),
        'top_hashtags': hashtag_counts.most_common(20),
        'all_hashtags': related_hashtags
    }

def analyze_twitter_data(file_path: str) -> Dict:
    """Analyze Twitter data for hashtags"""
    print(f"🐦 Analyzing Twitter data from {file_path}")
    
    hashtag_counts = Counter()
    related_hashtags = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for item in data:
            # Extract hashtags from text and fullText
            for text_field in ['text', 'fullText']:
                if text_field in item and item[text_field]:
                    hashtags = extract_hashtags_from_text(item[text_field])
                    hashtag_counts.update(hashtags)
                    related_hashtags.extend(hashtags)
    
    except Exception as e:
        print(f"❌ Error reading Twitter file: {e}")
        return {}
    
    return {
        'platform': 'Twitter',
        'total_hashtags': len(related_hashtags),
        'unique_hashtags': len(hashtag_counts),
        'top_hashtags': hashtag_counts.most_common(20),
        'all_hashtags': related_hashtags
    }

def main():
    """Main function to analyze all platforms"""
    print("🔍 Analyzing Hashtags from Scraped Data")
    print("=" * 60)
    
    # File paths
    files = {
        'instagram': 'data/scraped_data/dataset_instagram-scraper_audi-v2.json',
        'tiktok': 'data/scraped_data/dataset_tiktok-scraper_audi-v2.json',
        'twitter': 'data/scraped_data/dataset_twitter-scraper_audi-v2.json'
    }
    
    # Analyze each platform
    results = {}
    for platform, file_path in files.items():
        if platform == 'instagram':
            results[platform] = analyze_instagram_data(file_path)
        elif platform == 'tiktok':
            results[platform] = analyze_tiktok_data(file_path)
        elif platform == 'twitter':
            results[platform] = analyze_twitter_data(file_path)
    
    # Print results for each platform
    print("\n" + "=" * 60)
    print("📊 HASHTAG ANALYSIS RESULTS")
    print("=" * 60)
    
    for platform, data in results.items():
        if not data:
            continue
            
        print(f"\n🔸 {data['platform']} Results:")
        print(f"   Total hashtags found: {data['total_hashtags']}")
        print(f"   Unique hashtags: {data['unique_hashtags']}")
        print(f"   Top 10 hashtags:")
        
        for i, (hashtag, count) in enumerate(data['top_hashtags'][:10], 1):
            print(f"   {i:2d}. #{hashtag} ({count} times)")
    
    # Combine all hashtags and find overall top hashtags
    print("\n" + "=" * 60)
    print("🏆 OVERALL TOP HASHTAGS (All Platforms Combined)")
    print("=" * 60)
    
    all_hashtags = Counter()
    for data in results.values():
        if data and 'all_hashtags' in data:
            all_hashtags.update(data['all_hashtags'])
    
    print(f"Total unique hashtags across all platforms: {len(all_hashtags)}")
    print(f"Total hashtag mentions: {sum(all_hashtags.values())}")
    print(f"\nTop 20 hashtags overall:")
    
    for i, (hashtag, count) in enumerate(all_hashtags.most_common(20), 1):
        print(f"{i:2d}. #{hashtag} ({count} times)")
    
    # Find Audi-related hashtags specifically
    print("\n" + "=" * 60)
    print("🚗 AUDI-RELATED HASHTAGS")
    print("=" * 60)
    
    audi_keywords = ['audi', 'audia', 'audis', 'audir', 'audiq', 'auditt', 'quattro', 'vorsprungdurchtechnik']
    audi_related = {}
    
    for hashtag, count in all_hashtags.items():
        for keyword in audi_keywords:
            if keyword in hashtag.lower():
                audi_related[hashtag] = count
                break
    
    print(f"Found {len(audi_related)} Audi-related hashtags:")
    for i, (hashtag, count) in enumerate(sorted(audi_related.items(), key=lambda x: x[1], reverse=True), 1):
        print(f"{i:2d}. #{hashtag} ({count} times)")

if __name__ == "__main__":
    main()


