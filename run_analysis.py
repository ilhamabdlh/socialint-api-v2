#!/usr/bin/env python3
"""
CLI tool untuk menjalankan analisis tanpa API
Usage: python run_analysis.py --brand hufagripp --platform tiktok --file dataset.json
"""

import argparse
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.analysis_service import AnalysisService
from app.config.settings import settings

def main():
    parser = argparse.ArgumentParser(
        description='Social Intelligence Analysis CLI'
    )
    
    parser.add_argument(
        '--brand',
        required=True,
        help='Brand name to analyze'
    )
    
    parser.add_argument(
        '--platform',
        required=True,
        choices=settings.supported_platforms,
        help='Platform to analyze'
    )
    
    parser.add_argument(
        '--file',
        required=True,
        help='Path to data file (JSON/CSV/Excel)'
    )
    
    parser.add_argument(
        '--keywords',
        nargs='+',
        help='Keywords to filter (space-separated)'
    )
    
    parser.add_argument(
        '--layer',
        type=int,
        default=1,
        choices=[1, 2],
        help='Analysis layer (1=posts, 2=comments)'
    )
    
    args = parser.parse_args()
    
    # Use brand name as default keyword if not provided
    keywords = args.keywords if args.keywords else [args.brand]
    
    print(f"\n{'='*80}")
    print(f"🎯 Starting Analysis")
    print(f"{'='*80}")
    print(f"Brand: {args.brand}")
    print(f"Platform: {args.platform}")
    print(f"File: {args.file}")
    print(f"Keywords: {keywords}")
    print(f"Layer: {args.layer}")
    print(f"{'='*80}\n")
    
    # Check if file exists
    if not Path(args.file).exists():
        print(f"❌ Error: File not found: {args.file}")
        sys.exit(1)
    
    # Run analysis
    try:
        service = AnalysisService()
        result = service.process_platform(
            file_path=args.file,
            platform=args.platform,
            brand_name=args.brand,
            keywords=keywords,
            layer=args.layer
        )
        
        # Print results
        print(f"\n{'='*80}")
        print(f"✅ ANALYSIS COMPLETE")
        print(f"{'='*80}")
        print(f"Platform: {result.platform}")
        print(f"Brand: {result.brand_name}")
        print(f"Total Analyzed: {result.total_analyzed} posts")
        print(f"\nCleansing Stats:")
        print(f"  Initial: {result.cleansing_stats.initial_count}")
        print(f"  After Duplicates: {result.cleansing_stats.after_duplicates}")
        print(f"  After Keywords: {result.cleansing_stats.after_keywords}")
        print(f"  After Language: {result.cleansing_stats.after_language}")
        print(f"  Final: {result.cleansing_stats.final_count}")
        print(f"\nSentiment Distribution:")
        for sentiment, count in result.sentiment_distribution.items():
            percentage = (count / result.total_analyzed * 100) if result.total_analyzed > 0 else 0
            print(f"  {sentiment}: {count} ({percentage:.1f}%)")
        print(f"\nTopics Found: {len(result.topics_found)}")
        for topic in result.topics_found[:10]:
            print(f"  - {topic}")
        print(f"\nOutput File: {result.output_file}")
        print(f"Processing Time: {result.processing_time}s")
        print(f"{'='*80}\n")
        
    except Exception as e:
        print(f"\n❌ Error during analysis: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()

