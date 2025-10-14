import pandas as pd
import time
from typing import List, Dict, Any, Optional
from pathlib import Path

from app.services.ai_service import AIAnalysisService
from app.utils.data_helpers import (
    remove_duplicates,
    explicit_keywords_cleansing,
    prepare_dataframe,
    update_dataframe,
    get_platform_text_column,
    calculate_sentiment_distribution
)
from app.models.schemas import CleansingStats, PlatformAnalysisResponse
from app.config.settings import settings

class AnalysisService:
    def __init__(self):
        self.ai_service = AIAnalysisService()
        self.batch_size = settings.batch_size
        self.topics_global = []  # store topics across all platforms
        
    def load_data(self, file_path: str) -> pd.DataFrame:
        """Load data from various file formats"""
        file_path = Path(file_path)
        
        if file_path.suffix == '.csv':
            return pd.read_csv(file_path)
        elif file_path.suffix in ['.xlsx', '.xls']:
            return pd.read_excel(file_path)
        elif file_path.suffix == '.json':
            return pd.read_json(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_path.suffix}")
    
    def cleanse_data(
        self, 
        df: pd.DataFrame, 
        platform: str, 
        keywords: List[str],
        layer: int = 1
    ) -> tuple[pd.DataFrame, CleansingStats]:
        """
        Apply cleansing pipeline:
        1. Remove duplicates
        2. Filter by keywords
        3. Filter by language (Indonesian only)
        """
        initial_count = len(df)
        text_col = get_platform_text_column(platform, layer)
        
        # Convert text column to string
        if text_col in df.columns:
            df[text_col] = df[text_col].astype(str)
        
        # Extract data for cleansing
        data = df[text_col].tolist()
        
        # Step 1: Remove duplicates
        data = remove_duplicates(data, platform)
        df = update_dataframe(df, data, platform, layer)
        after_duplicates = len(df)
        
        # Step 2: Keyword filtering
        data = explicit_keywords_cleansing(data, keywords)
        df = update_dataframe(df, data, platform, layer)
        after_keywords = len(df)
        
        # Step 3: Language filtering (only Indonesian)
        data = self.ai_service.language_based_cleansing(data)
        df = update_dataframe(df, data, platform, layer)
        final_count = len(df)
        
        stats = CleansingStats(
            initial_count=initial_count,
            after_duplicates=after_duplicates,
            after_keywords=after_keywords,
            after_language=final_count,
            final_count=final_count
        )
        
        return df, stats
    
    def analyze_data(
        self, 
        df: pd.DataFrame, 
        platform: str,
        layer: int = 1
    ) -> pd.DataFrame:
        """
        Apply AI analysis:
        1. Sentiment analysis
        2. Topic analysis
        """
        text_col = get_platform_text_column(platform, layer)
        data = df[text_col].tolist()
        
        # Split into batches for processing
        batches = [data[i:i + self.batch_size] for i in range(0, len(data), self.batch_size)]
        
        # Run sentiment analysis batch by batch
        all_sentiments = []
        for batch in batches:
            sentiments = self.ai_service.sentiment_analysis(batch)
            all_sentiments.extend(sentiments)
        
        # Run topic analysis batch by batch
        all_topics = []
        for batch in batches:
            topics = self.ai_service.topic_analysis(batch, self.topics_global)
            all_topics.extend(topics)
        
        # Add results to dataframe
        df['sentiment'] = all_sentiments
        df['topic'] = all_topics
        
        return df
    
    def process_platform(
        self,
        file_path: str,
        platform: str,
        brand_name: str,
        keywords: List[str],
        layer: int = 1
    ) -> PlatformAnalysisResponse:
        """
        Complete processing pipeline for one platform:
        1. Load data
        2. Prepare dataframe (platform-specific)
        3. Cleanse data
        4. Analyze with AI
        5. Save results
        """
        start_time = time.time()
        
        # Load and prepare
        df = self.load_data(file_path)
        df = prepare_dataframe(df, platform)
        
        # Cleanse
        df, cleansing_stats = self.cleanse_data(df, platform, keywords, layer)
        
        # Analyze
        df = self.analyze_data(df, platform, layer)
        
        # Calculate stats
        sentiment_dist = calculate_sentiment_distribution(df['sentiment'].tolist())
        topics_found = df['topic'].unique().tolist()
        
        # Save results
        import os
        layer_name = f"layer{layer}"
        
        # Ensure data directory exists
        data_dir = "data/scraped_data"
        os.makedirs(data_dir, exist_ok=True)
        
        output_file = os.path.join(data_dir, f"{platform}_{brand_name}_{layer_name}.csv")
        df.to_csv(output_file, index=False)
        
        processing_time = time.time() - start_time
        
        return PlatformAnalysisResponse(
            platform=platform,
            brand_name=brand_name,
            layer=layer_name,
            total_analyzed=len(df),
            cleansing_stats=cleansing_stats,
            topics_found=topics_found,
            sentiment_distribution=sentiment_dist,
            output_file=output_file,
            processing_time=round(processing_time, 2)
        )
    
    def process_multiple_platforms(
        self,
        platforms_data: Dict[str, str],  # platform -> file_path mapping
        brand_name: str,
        keywords: List[str]
    ) -> List[PlatformAnalysisResponse]:
        """
        Process multiple platforms for brand analysis
        This follows the diagram's multi-platform loop
        """
        results = []
        
        for platform, file_path in platforms_data.items():
            print(f"\n{'='*80}")
            print(f"Processing platform: {platform.upper()}")
            print(f"{'='*80}")
            
            try:
                result = self.process_platform(
                    file_path=file_path,
                    platform=platform,
                    brand_name=brand_name,
                    keywords=keywords,
                    layer=1
                )
                results.append(result)
                print(f"✓ {platform} completed successfully")
            except Exception as e:
                print(f"✗ Error processing {platform}: {str(e)}")
                # Continue with other platforms even if one fails
        
        return results

