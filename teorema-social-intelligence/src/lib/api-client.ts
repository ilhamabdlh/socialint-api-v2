/**
 * API Client for Social Intelligence Backend
 * 
 * Connects to FastAPI backend running on staging environment
 */

// =============================================================================
// Configuration
// =============================================================================

const API_BASE_URL = (import.meta as any).env?.VITE_API_URL || 'https://api.staging.teoremaintelligence.com';
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
  competitors: string[];
  industry?: string;
  created_at: string;
  updated_at: string;
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
   * Get brand summary
   */
  async getBrandSummary(brandName: string): Promise<any> {
    return fetchAPI<any>(`/results/brands/${brandName}/summary`);
  },

  /**
   * Get brand posts
   */
  async getBrandPosts(
    brandName: string,
    platform?: string,
    skip: number = 0,
    limit: number = 100
  ): Promise<any> {
    const params = new URLSearchParams({
      skip: skip.toString(),
      limit: limit.toString(),
    });
    if (platform) params.append('platform', platform);
    
    return fetchAPI<any>(`/results/brands/${brandName}/posts?${params.toString()}`);
  },

  /**
   * Get trending topics
   */
  async getTrendingTopics(
    brandName: string,
    platform?: string,
    limit: number = 10
  ): Promise<any> {
    const params = new URLSearchParams({ limit: limit.toString() });
    if (platform) params.append('platform', platform);
    
    return fetchAPI<any>(`/results/brands/${brandName}/trending-topics?${params.toString()}`);
  },

  /**
   * Get sentiment timeline
   */
  async getSentimentTimeline(
    brandName: string,
    platform?: string,
    days: number = 30
  ): Promise<any> {
    const params = new URLSearchParams({ days: days.toString() });
    if (platform) params.append('platform', platform);
    
    return fetchAPI<any>(`/results/brands/${brandName}/sentiment-timeline?${params.toString()}`);
  },

  /**
   * Get audience insights
   */
  async getAudienceInsights(brandName: string): Promise<any> {
    return fetchAPI<any>(`/results/brands/${brandName}/audience-insights`);
  },

  /**
   * Get emotions analysis
   */
  async getEmotions(
    brandName: string,
    platform?: string,
    limit: number = 10000
  ): Promise<any> {
    const params = new URLSearchParams({ limit: limit.toString() });
    if (platform) params.append('platform', platform);
    
    return fetchAPI<any>(`/results/brands/${brandName}/emotions?${params.toString()}`);
  },

  /**
   * Get demographics analysis
   */
  async getDemographics(
    brandName: string,
    platform?: string,
    limit: number = 10000
  ): Promise<any> {
    const params = new URLSearchParams({ limit: limit.toString() });
    if (platform) params.append('platform', platform);
    
    return fetchAPI<any>(`/results/brands/${brandName}/demographics?${params.toString()}`);
  },

  /**
   * Get engagement patterns
   */
  async getEngagementPatterns(
    brandName: string,
    platform?: string,
    limit: number = 10000
  ): Promise<EngagementPatterns> {
    const params = new URLSearchParams({ limit: limit.toString() });
    if (platform) params.append('platform', platform);
    
    return fetchAPI<EngagementPatterns>(`/results/brands/${brandName}/engagement-patterns?${params.toString()}`);
  },

  /**
   * Get performance metrics
   */
  async getPerformance(
    brandName: string,
    platform?: string,
    days: number = 30
  ): Promise<any> {
    const params = new URLSearchParams({ days: days.toString() });
    if (platform) params.append('platform', platform);
    
    return fetchAPI<any>(`/results/brands/${brandName}/performance?${params.toString()}`);
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
