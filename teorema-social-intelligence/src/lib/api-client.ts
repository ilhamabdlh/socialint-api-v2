/**
 * API Client for Social Intelligence Backend
 * 
 * Connects to FastAPI backend running on staging environment
 */

// =============================================================================
// Configuration
// =============================================================================

const API_BASE_URL = (import.meta as any).env?.VITE_API_URL || 'http://localhost:8000';
const API_PREFIX = '/api/v1';

// =============================================================================
// Types & Interfaces
// =============================================================================

// Campaign Types
export interface CampaignCreate {
  campaign_name: string;
  description: string;
  campaign_type: 'product_launch' | 'brand_awareness' | 'feature_highlight' | 'crisis_response' | 'seasonal' | 'event';
  brand_name: string;
  
  keywords: string[];
  target_audiences: string[];
  platforms: ('tiktok' | 'instagram' | 'twitter' | 'youtube' | 'linkedin' | 'facebook' | 'reddit')[];
  post_urls: {
    url: string;
    platform: string;
    title?: string;
    description?: string;
  }[];
  
  start_date: string; // ISO datetime
  end_date: string;   // ISO datetime
  
  auto_analysis_enabled?: boolean;
  analysis_frequency?: string;
  tags?: string[];
  created_by?: string;
  team?: string;
  notes?: string;
}

export interface CampaignUpdate {
  description?: string;
  campaign_type?: string;
  status?: 'draft' | 'active' | 'paused' | 'completed' | 'archived';
  brand_name?: string;
  keywords?: string[];
  target_audiences?: string[];
  platforms?: string[];
  start_date?: string;
  end_date?: string;
  auto_analysis_enabled?: boolean;
  tags?: string[];
  notes?: string;
}

export interface CampaignResponse {
  id: string;
  campaign_name: string;
  description: string;
  campaign_type: string;
  status: string;
  brand_name: string;
  
  keywords: string[];
  target_audiences: string[];
  platforms: string[];
  post_urls_count: number;
  post_urls: {
    url: string;
    platform: string;
    title?: string;
    description?: string;
  }[];
  
  start_date: string;
  end_date: string;
  
  total_mentions: number;
  overall_sentiment: number;
  engagement_rate: number;
  reach: number;
  
  sentiment_trend: number;
  mentions_trend: number;
  engagement_trend: number;
  
  tags: string[];
  
  created_at: string;
  updated_at: string;
  last_analysis_at?: string;
}

export interface CampaignMetrics {
  metric_date: string;
  sentiment_score: number;
  total_mentions: number;
  positive_count: number;
  negative_count: number;
  neutral_count: number;
  total_likes: number;
  total_comments: number;
  total_shares: number;
  engagement_rate: number;
  reach: number;
}

// Brand Types
export interface BrandCreate {
  name: string;
  description?: string;
  keywords: string[];
  competitors?: string[];
  industry?: string;
}

export interface BrandResponse {
  id: string;
  name: string;
  description?: string;
  keywords: string[];
  platforms: string[];
  postUrls: string[];
  category?: string;
  industry?: string;
  competitors: string[];
  startDate?: string;
  endDate?: string;
  created_from: string;
  created_at: string;
  updated_at: string;
}

export interface ContentCreate {
  // Basic Content Info
  title: string;
  description: string;
  content_text: string;
  post_url: string;
  platform: string;
  content_type: string;
  author: string;
  publish_date: string;
  status: string;
  tags: string[];
  
  // Content Metadata
  brand_name?: string;
  campaign_id?: string;
  keywords: string[];
  target_audience: string[];
  content_category: string;
  language: string;
  priority: string;
  
  // Legacy fields for backward compatibility
  text?: string;
  url?: string;
}

export interface ContentResponse {
  id: string;
  // Basic Content Info
  title: string;
  description: string;
  content_text: string;
  post_url: string;
  platform: string;
  content_type: string;
  author: string;
  publish_date: string;
  status: string;
  tags: string[];
  
  // Content Metadata
  brand_name?: string;
  campaign_id?: string;
  keywords: string[];
  target_audience: string[];
  content_category: string;
  language: string;
  priority: string;
  
  // Analysis Results - Topic Analysis
  topics: any[];
  dominant_topic?: string;
  
  // Analysis Results - Sentiment Analysis
  sentiment_overall?: number;
  sentiment_positive?: number;
  sentiment_negative?: number;
  sentiment_neutral?: number;
  sentiment_confidence?: number;
  sentiment_breakdown: any[];
  
  // Analysis Results - Emotion Analysis
  emotion_joy?: number;
  emotion_anger?: number;
  emotion_fear?: number;
  emotion_sadness?: number;
  emotion_surprise?: number;
  emotion_trust?: number;
  emotion_anticipation?: number;
  emotion_disgust?: number;
  dominant_emotion?: string;
  emotion_distribution: any[];
  
  // Performance Metrics
  engagement_score?: number;
  reach_estimate?: number;
  virality_score?: number;
  content_health_score?: number;
  
  // Demographics Analysis
  author_age_group?: string;
  author_gender?: string;
  author_location_hint?: string;
  target_audience_match?: number;
  
  // Competitive Analysis
  similar_content_count?: number;
  benchmark_engagement?: number;
  benchmark_sentiment?: number;
  benchmark_topic_trend?: number;
  
  // Analysis Status
  analysis_status: string;
  analysis_type: string;
  
  // Timestamps
  created_at: string;
  updated_at: string;
  analyzed_at?: string;
  
  // Legacy fields for backward compatibility
  text?: string;
  url?: string;
  sentiment?: string;
  topic?: string;
}

// Analysis Types
export interface AnalysisRequest {
  platform: string;
  file_path: string;
  brand_name: string;
  keywords: string[];
  layer?: number;
}

export interface ScrapeRequest {
  brand_name: string;
  keywords: string[];
  platforms: string[];
  max_posts_per_platform?: number;
  start_date?: string;
  end_date?: string;
  auto_analyze?: boolean;
}

// =============================================================================
// HTTP Helper Functions
// =============================================================================

async function fetchAPI<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${API_PREFIX}${endpoint}`;
  
  const defaultHeaders: HeadersInit = {
    'Content-Type': 'application/json',
  };
  
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        ...defaultHeaders,
        ...options.headers,
      },
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
}

// =============================================================================
// Campaign API
// =============================================================================

export const campaignAPI = {
  /**
   * Create a new campaign
   */
  async create(data: CampaignCreate): Promise<CampaignResponse> {
    return fetchAPI<CampaignResponse>('/campaigns/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  /**
   * List all campaigns
   */
  async list(params?: {
    status?: string;
    brand_name?: string;
    skip?: number;
    limit?: number;
  }): Promise<CampaignResponse[]> {
    const queryParams = new URLSearchParams();
    if (params?.status) queryParams.append('status', params.status);
    if (params?.brand_name) queryParams.append('brand_name', params.brand_name);
    if (params?.skip) queryParams.append('skip', params.skip.toString());
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    
    const query = queryParams.toString();
    return fetchAPI<CampaignResponse[]>(`/campaigns/${query ? '?' + query : ''}`);
  },

  /**
   * Get campaign by name
   */
  async get(campaignName: string): Promise<CampaignResponse> {
    return fetchAPI<CampaignResponse>(`/campaigns/${campaignName}`);
  },

  /**
   * Update campaign
   */
  async update(campaignName: string, data: CampaignUpdate): Promise<CampaignResponse> {
    return fetchAPI<CampaignResponse>(`/campaigns/${campaignName}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  /**
   * Delete (archive) campaign
   */
  async delete(campaignName: string): Promise<{ message: string }> {
    return fetchAPI<{ message: string }>(`/campaigns/${campaignName}`, {
      method: 'DELETE',
    });
  },

  /**
   * Get campaign metrics (time-series data)
   */
  async getMetrics(campaignName: string, days: number = 30): Promise<CampaignMetrics[]> {
    return fetchAPI<CampaignMetrics[]>(`/campaigns/${campaignName}/metrics?days=${days}`);
  },

  /**
   * Trigger manual analysis
   */
  async triggerAnalysis(campaignName: string): Promise<any> {
    return fetchAPI<any>(`/campaigns/${campaignName}/trigger-analysis`, {
      method: 'POST',
    });
  },

  /**
   * Get active campaigns
   */
  async getActive(): Promise<{ count: number; campaigns: any[] }> {
    return fetchAPI<{ count: number; campaigns: any[] }>('/campaigns/active');
  },

  // =============================================================================
  // Campaign Analysis Results API
  // =============================================================================

  /**
   * Get campaign analysis summary
   */
  async getAnalysisSummary(
    campaignId: string,
    startDate?: string,
    endDate?: string,
    platforms?: string,
    postUrls?: string,
    days: number = 30
  ): Promise<any> {
    const params = new URLSearchParams({ days: days.toString() });
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    if (platforms) params.append('platforms', platforms);
    if (postUrls) params.append('post_urls', postUrls);
    
    return fetchAPI<any>(`/results/campaigns/${campaignId}/summary?${params.toString()}`);
  },

  /**
   * Get campaign sentiment timeline
   */
  async getSentimentTimeline(
    campaignId: string,
    startDate?: string,
    endDate?: string,
    platforms?: string,
    postUrls?: string,
    days: number = 30
  ): Promise<any> {
    const params = new URLSearchParams({ days: days.toString() });
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    if (platforms) params.append('platforms', platforms);
    if (postUrls) params.append('post_urls', postUrls);
    
    return fetchAPI<any>(`/results/campaigns/${campaignId}/sentiment-timeline?${params.toString()}`);
  },

  /**
   * Get campaign trending topics
   */
  async getTrendingTopics(
    campaignId: string,
    startDate?: string,
    endDate?: string,
    platforms?: string,
    postUrls?: string,
    limit: number = 10
  ): Promise<any> {
    const params = new URLSearchParams({ limit: limit.toString() });
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    if (platforms) params.append('platforms', platforms);
    if (postUrls) params.append('post_urls', postUrls);
    
    return fetchAPI<any>(`/results/campaigns/${campaignId}/trending-topics?${params.toString()}`);
  },

  /**
   * Get campaign emotions analysis
   */
  async getEmotions(
    campaignId: string,
    startDate?: string,
    endDate?: string,
    platforms?: string,
    postUrls?: string
  ): Promise<any> {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    if (platforms) params.append('platforms', platforms);
    if (postUrls) params.append('post_urls', postUrls);
    
    return fetchAPI<any>(`/results/campaigns/${campaignId}/emotions?${params.toString()}`);
  },

  /**
   * Get campaign audience demographics
   */
  async getAudience(
    campaignId: string,
    startDate?: string,
    endDate?: string,
    platforms?: string,
    postUrls?: string
  ): Promise<any> {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    if (platforms) params.append('platforms', platforms);
    if (postUrls) params.append('post_urls', postUrls);
    
    return fetchAPI<any>(`/results/campaigns/${campaignId}/audience?${params.toString()}`);
  },

  /**
   * Get campaign performance metrics
   */
  async getPerformance(
    campaignId: string,
    startDate?: string,
    endDate?: string,
    platforms?: string,
    postUrls?: string
  ): Promise<any> {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    if (platforms) params.append('platforms', platforms);
    if (postUrls) params.append('post_urls', postUrls);
    
    return fetchAPI<any>(`/results/campaigns/${campaignId}/performance?${params.toString()}`);
  },
};

// =============================================================================
// Brand API
// =============================================================================

export const brandAPI = {
  /**
   * Create a new brand
   */
  async create(data: BrandCreate): Promise<BrandResponse> {
    return fetchAPI<BrandResponse>('/brands/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  /**
   * List all brands
   */
  async list(skip: number = 0, limit: number = 100): Promise<BrandResponse[]> {
    return fetchAPI<BrandResponse[]>(`/brands/?skip=${skip}&limit=${limit}`);
  },

  /**
   * Get brand by name
   */
  async get(brandName: string): Promise<BrandResponse> {
    return fetchAPI<BrandResponse>(`/brands/${brandName}`);
  },

  /**
   * Update brand
   */
  async update(brandName: string, data: Partial<BrandCreate>): Promise<BrandResponse> {
    return fetchAPI<BrandResponse>(`/brands/${brandName}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  /**
   * Delete brand
   */
  async delete(brandName: string): Promise<{ message: string }> {
    return fetchAPI<{ message: string }>(`/brands/${brandName}`, {
      method: 'DELETE',
    });
  },
};

// =============================================================================
// Content API
// =============================================================================

export const contentAPI = {
  /**
   * Create a new content
   */
  async create(data: ContentCreate): Promise<ContentResponse> {
    return fetchAPI<ContentResponse>('/contents/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  /**
   * List all contents
   */
  async list(skip: number = 0, limit: number = 100): Promise<ContentResponse[]> {
    return fetchAPI<ContentResponse[]>(`/contents/?skip=${skip}&limit=${limit}`);
  },

  /**
   * Get content by ID
   */
  async get(contentId: string): Promise<ContentResponse> {
    return fetchAPI<ContentResponse>(`/contents/${contentId}`);
  },

  /**
   * Update content
   */
  async update(contentId: string, data: Partial<ContentCreate>): Promise<ContentResponse> {
    return fetchAPI<ContentResponse>(`/contents/${contentId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  /**
   * Delete content
   */
  async delete(contentId: string): Promise<{ message: string }> {
    return fetchAPI<{ message: string }>(`/contents/${contentId}`, {
      method: 'DELETE',
    });
  },
};

// =============================================================================
// Analysis API
// =============================================================================

export const analysisAPI = {
  /**
   * Analyze platform data
   */
  async analyzePlatform(data: AnalysisRequest): Promise<any> {
    return fetchAPI<any>('/analyze/platform', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  /**
   * Analyze brand across multiple platforms
   */
  async analyzeBrand(data: {
    brand_name: string;
    platforms_data: Record<string, string>;
    keywords: string[];
  }): Promise<any> {
    return fetchAPI<any>('/analyze/brand', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },
};

// =============================================================================
// Scraping API
// =============================================================================

export const scrapingAPI = {
  /**
   * Scrape social media data
   */
  async scrape(data: ScrapeRequest): Promise<any> {
    return fetchAPI<any>('/scrape/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  /**
   * Scrape single platform
   */
  async scrapeSinglePlatform(data: {
    platform: string;
    keywords: string[];
    max_posts?: number;
    start_date?: string;
    end_date?: string;
    auto_analyze?: boolean;
  }): Promise<any> {
    return fetchAPI<any>('/scrape/single-platform', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  /**
   * Get supported platforms
   */
  async getSupportedPlatforms(): Promise<string[]> {
    return fetchAPI<string[]>('/scrape/supported-platforms');
  },
};

// =============================================================================
// Results API
// =============================================================================

export const resultsAPI = {
  /**
   * Get brand summary (legacy - use getBrandAnalysisSummary instead)
   */
  async getBrandSummary(brandIdentifier: string, startDate?: string, endDate?: string, platforms?: string, days: number = 30): Promise<any> {
    const params = new URLSearchParams({ days: days.toString() });
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    if (platforms) params.append('platforms', platforms);
    
    return fetchAPI<any>(`/results/brands/${brandIdentifier}/summary?${params.toString()}`);
  },

  /**
   * Get brand posts
   */
  async getBrandPosts(
    brandIdentifier: string,
    platform?: string,
    skip: number = 0,
    limit: number = 100
  ): Promise<any> {
    const params = new URLSearchParams({
      skip: skip.toString(),
      limit: limit.toString(),
    });
    if (platform) params.append('platform', platform);
    
    return fetchAPI<any>(`/results/brands/${brandIdentifier}/posts?${params.toString()}`);
  },

  /**
   * Get trending topics (legacy - use getBrandTrendingTopics instead)
   */
  async getTrendingTopics(
    brandIdentifier: string,
    platform?: string,
    limit: number = 10
  ): Promise<any> {
    const params = new URLSearchParams({ limit: limit.toString() });
    if (platform) params.append('platform', platform);
    
    return fetchAPI<any>(`/results/brands/${brandIdentifier}/trending-topics?${params.toString()}`);
  },

  /**
   * Get sentiment timeline (legacy - use getBrandSentimentTimeline instead)
   */
  async getSentimentTimeline(
    brandIdentifier: string,
    platform?: string,
    days: number = 30
  ): Promise<any> {
    const params = new URLSearchParams({ days: days.toString() });
    if (platform) params.append('platform', platform);
    
    return fetchAPI<any>(`/results/brands/${brandIdentifier}/sentiment-timeline?${params.toString()}`);
  },

  /**
   * Get audience insights
   */
  async getAudienceInsights(brandIdentifier: string): Promise<any> {
    return fetchAPI<any>(`/results/brands/${brandIdentifier}/audience-insights`);
  },

  /**
   * Get emotions analysis (legacy - use getBrandEmotions instead)
   */
  async getEmotions(
    brandIdentifier: string,
    platform?: string,
    limit: number = 10000
  ): Promise<any> {
    const params = new URLSearchParams({ limit: limit.toString() });
    if (platform) params.append('platform', platform);
    
    return fetchAPI<any>(`/results/brands/${brandIdentifier}/emotions?${params.toString()}`);
  },

  /**
   * Get demographics analysis (legacy - use getBrandDemographics instead)
   */
  async getDemographics(
    brandIdentifier: string,
    platform?: string,
    limit: number = 10000
  ): Promise<any> {
    const params = new URLSearchParams({ limit: limit.toString() });
    if (platform) params.append('platform', platform);
    
    return fetchAPI<any>(`/results/brands/${brandIdentifier}/demographics?${params.toString()}`);
  },

  /**
   * Get engagement patterns (legacy - use getBrandEngagementPatterns instead)
   */
  async getEngagementPatterns(
    brandIdentifier: string,
    platform?: string,
    limit: number = 10000
  ): Promise<EngagementPatterns> {
    const params = new URLSearchParams({ limit: limit.toString() });
    if (platform) params.append('platform', platform);
    
    return fetchAPI<EngagementPatterns>(`/results/brands/${brandIdentifier}/engagement-patterns?${params.toString()}`);
  },

  /**
   * Get performance metrics (legacy - use getBrandPerformance instead)
   */
  async getPerformance(
    brandIdentifier: string,
    platform?: string,
    days: number = 30
  ): Promise<any> {
    const params = new URLSearchParams({ days: days.toString() });
    if (platform) params.append('platform', platform);
    
    return fetchAPI<any>(`/results/brands/${brandIdentifier}/performance?${params.toString()}`);
  },

  // ============= BRAND ANALYSIS ENDPOINTS =============

  /**
   * Get brand analysis summary
   */
  async getBrandAnalysisSummary(
    brandIdentifier: string,
    startDate?: string,
    endDate?: string,
    platforms?: string,
    days: number = 30
  ): Promise<any> {
    const params = new URLSearchParams({ days: days.toString() });
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    if (platforms) params.append('platforms', platforms);
    
    return fetchAPI<any>(`/results/brands/${brandIdentifier}/summary?${params.toString()}`);
  },

  /**
   * Get brand sentiment timeline
   */
  async getBrandSentimentTimeline(
    brandIdentifier: string,
    startDate?: string,
    endDate?: string,
    platforms?: string,
    days: number = 30
  ): Promise<any> {
    const params = new URLSearchParams({ days: days.toString() });
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    if (platforms) params.append('platforms', platforms);
    
    return fetchAPI<any>(`/results/brands/${brandIdentifier}/sentiment-timeline?${params.toString()}`);
  },

  /**
   * Get brand trending topics
   */
  async getBrandTrendingTopics(
    brandIdentifier: string,
    startDate?: string,
    endDate?: string,
    platforms?: string,
    limit: number = 10
  ): Promise<any> {
    const params = new URLSearchParams({ limit: limit.toString() });
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    if (platforms) params.append('platforms', platforms);
    
    return fetchAPI<any>(`/results/brands/${brandIdentifier}/trending-topics?${params.toString()}`);
  },

  /**
   * Get brand engagement patterns
   */
  async getBrandEngagementPatterns(
    brandIdentifier: string,
    startDate?: string,
    endDate?: string,
    platforms?: string
  ): Promise<any> {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    if (platforms) params.append('platforms', platforms);
    
    return fetchAPI<any>(`/results/brands/${brandIdentifier}/engagement-patterns?${params.toString()}`);
  },

  /**
   * Get brand performance metrics
   */
  async getBrandPerformance(
    brandIdentifier: string,
    startDate?: string,
    endDate?: string,
    platforms?: string,
    days: number = 30
  ): Promise<any> {
    const params = new URLSearchParams({ days: days.toString() });
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    if (platforms) params.append('platforms', platforms);
    
    return fetchAPI<any>(`/results/brands/${brandIdentifier}/performance?${params.toString()}`);
  },

  /**
   * Get brand emotion analysis
   */
  async getBrandEmotions(
    brandIdentifier: string,
    startDate?: string,
    endDate?: string,
    platforms?: string
  ): Promise<any> {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    if (platforms) params.append('platforms', platforms);
    
    return fetchAPI<any>(`/results/brands/${brandIdentifier}/emotions?${params.toString()}`);
  },

  /**
   * Get brand demographics
   */
  async getBrandDemographics(
    brandIdentifier: string,
    startDate?: string,
    endDate?: string,
    platforms?: string
  ): Promise<any> {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    if (platforms) params.append('platforms', platforms);
    
    return fetchAPI<any>(`/results/brands/${brandIdentifier}/demographics?${params.toString()}`);
  },

  /**
   * Get brand competitive analysis
   */
  async getBrandCompetitive(
    brandIdentifier: string,
    startDate?: string,
    endDate?: string,
    platforms?: string
  ): Promise<any> {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    if (platforms) params.append('platforms', platforms);
    
    return fetchAPI<any>(`/results/brands/${brandIdentifier}/competitive?${params.toString()}`);
  },

  // ============= CONTENT ANALYSIS ENDPOINTS =============

  /**
   * Get content analysis summary
   */
  async getContentAnalysisSummary(
    contentId: string,
    startDate?: string,
    endDate?: string,
    platforms?: string,
    days: number = 30
  ): Promise<any> {
    const params = new URLSearchParams({ days: days.toString() });
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    if (platforms) params.append('platforms', platforms);
    
    return fetchAPI<any>(`/results/contents/${contentId}/summary?${params.toString()}`);
  },

  /**
   * Get content sentiment timeline
   */
  async getContentSentimentTimeline(
    contentId: string,
    startDate?: string,
    endDate?: string,
    platforms?: string,
    days: number = 30
  ): Promise<any> {
    const params = new URLSearchParams({ days: days.toString() });
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    if (platforms) params.append('platforms', platforms);
    
    return fetchAPI<any>(`/results/contents/${contentId}/sentiment-timeline?${params.toString()}`);
  },

  /**
   * Get content trending topics
   */
  async getContentTrendingTopics(
    contentId: string,
    startDate?: string,
    endDate?: string,
    platforms?: string,
    limit: number = 10
  ): Promise<any> {
    const params = new URLSearchParams({ limit: limit.toString() });
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    if (platforms) params.append('platforms', platforms);
    
    return fetchAPI<any>(`/results/contents/${contentId}/trending-topics?${params.toString()}`);
  },

  /**
   * Get content engagement patterns
   */
  async getContentEngagementPatterns(
    contentId: string,
    startDate?: string,
    endDate?: string,
    platforms?: string
  ): Promise<any> {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    if (platforms) params.append('platforms', platforms);
    
    return fetchAPI<any>(`/results/contents/${contentId}/engagement-patterns?${params.toString()}`);
  },

  /**
   * Get content performance metrics
   */
  async getContentPerformance(
    contentId: string,
    startDate?: string,
    endDate?: string,
    platforms?: string,
    days: number = 30
  ): Promise<any> {
    const params = new URLSearchParams({ days: days.toString() });
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    if (platforms) params.append('platforms', platforms);
    
    return fetchAPI<any>(`/results/contents/${contentId}/performance?${params.toString()}`);
  },

  /**
   * Get content emotion analysis
   */
  async getContentEmotions(
    contentId: string,
    startDate?: string,
    endDate?: string,
    platforms?: string
  ): Promise<any> {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    if (platforms) params.append('platforms', platforms);
    
    return fetchAPI<any>(`/results/contents/${contentId}/emotions?${params.toString()}`);
  },

  /**
   * Get content demographics
   */
  async getContentDemographics(
    contentId: string,
    startDate?: string,
    endDate?: string,
    platforms?: string
  ): Promise<any> {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    if (platforms) params.append('platforms', platforms);
    
    return fetchAPI<any>(`/results/contents/${contentId}/demographics?${params.toString()}`);
  },

  /**
   * Get content competitive analysis
   */
  async getContentCompetitive(
    contentId: string,
    startDate?: string,
    endDate?: string,
    platforms?: string
  ): Promise<any> {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    if (platforms) params.append('platforms', platforms);
    
    return fetchAPI<any>(`/results/contents/${contentId}/competitive?${params.toString()}`);
  },

  // ============= TRIGGER ANALYSIS ENDPOINTS =============

  /**
   * Trigger brand analysis
   */
  async triggerBrandAnalysis(
    brandId: string,
    keywords?: string[],
    platforms?: string[],
    startDate?: string,
    endDate?: string
  ): Promise<any> {
    return fetchAPI<any>(`/results/brands/${brandId}/trigger-analysis`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        keywords,
        platforms,
        start_date: startDate,
        end_date: endDate
      })
    });
  },

  /**
   * Trigger content analysis
   */
  async triggerContentAnalysis(
    contentId: string,
    analysisType: string = "comprehensive",
    parameters?: any
  ): Promise<any> {
    return fetchAPI<any>(`/results/contents/${contentId}/trigger-analysis`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        analysis_type: analysisType,
        parameters
      })
    });
  },
};

// =============================================================================
// Health Check
// =============================================================================

export const healthAPI = {
  /**
   * Check if API is running
   */
  async ping(): Promise<{ message: string; status: string; version: string }> {
    return fetchAPI<{ message: string; status: string; version: string }>('/');
  },

  /**
   * Get supported platforms
   */
  async getPlatforms(): Promise<{ platforms: string[] }> {
    return fetchAPI<{ platforms: string[] }>('/platforms');
  },
};

// =============================================================================
// Export All
// =============================================================================

// Engagement Patterns Interface
export interface EngagementPatterns {
  brand_name: string;
  platform: string;
  peak_hours: string[];
  active_days: string[];
  avg_engagement_rate: number;
  total_posts: number;
}

export default {
  campaign: campaignAPI,
  brand: brandAPI,
  analysis: analysisAPI,
  scraping: scrapingAPI,
  results: resultsAPI,
  health: healthAPI,
};
