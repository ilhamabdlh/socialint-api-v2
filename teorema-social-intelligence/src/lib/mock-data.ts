// Mock data for Tesla public perception analytics

export interface SentimentData {
  date: string;
  positive: number;
  negative: number;
  neutral: number;
  overall_score: number;
}

export interface SocialMetric {
  platform: string;
  mentions: number;
  sentiment: number;
  engagement: number;
  growth: number;
}

export interface TopicData {
  topic: string;
  mentions: number;
  sentiment: number;
  trend: 'up' | 'down' | 'stable';
}

export interface KeywordCluster {
  keyword: string;
  frequency: number;
  sentiment: number;
  related_terms: string[];
}

// Mock sentiment data over time (last 30 days)
export const sentimentTrends: SentimentData[] = [
  { date: '2025-01-28', positive: 45, negative: 25, neutral: 30, overall_score: 0.72 },
  { date: '2025-01-27', positive: 48, negative: 22, neutral: 30, overall_score: 0.75 },
  { date: '2025-01-26', positive: 42, negative: 28, neutral: 30, overall_score: 0.68 },
  { date: '2025-01-25', positive: 50, negative: 20, neutral: 30, overall_score: 0.78 },
  { date: '2025-01-24', positive: 38, negative: 32, neutral: 30, overall_score: 0.62 },
  { date: '2025-01-23', positive: 44, negative: 26, neutral: 30, overall_score: 0.71 },
  { date: '2025-01-22', positive: 47, negative: 23, neutral: 30, overall_score: 0.74 },
  { date: '2025-01-21', positive: 41, negative: 29, neutral: 30, overall_score: 0.66 },
  { date: '2025-01-20', positive: 46, negative: 24, neutral: 30, overall_score: 0.73 },
  { date: '2025-01-19', positive: 43, negative: 27, neutral: 30, overall_score: 0.69 },
  { date: '2025-01-18', positive: 49, negative: 21, neutral: 30, overall_score: 0.76 },
  { date: '2025-01-17', positive: 40, negative: 30, neutral: 30, overall_score: 0.65 },
  { date: '2025-01-16', positive: 45, negative: 25, neutral: 30, overall_score: 0.72 },
  { date: '2025-01-15', positive: 52, negative: 18, neutral: 30, overall_score: 0.80 },
  { date: '2025-01-14', positive: 37, negative: 33, neutral: 30, overall_score: 0.60 },
];

// Social media platform metrics
export const socialMetrics: SocialMetric[] = [
  { platform: 'Twitter/X', mentions: 15420, sentiment: 0.73, engagement: 245000, growth: 12.5 },
  { platform: 'Reddit', mentions: 8750, sentiment: 0.68, engagement: 156000, growth: -2.3 },
  { platform: 'YouTube', mentions: 3200, sentiment: 0.81, engagement: 892000, growth: 18.7 },
  { platform: 'LinkedIn', mentions: 2100, sentiment: 0.79, engagement: 67000, growth: 8.4 },
  { platform: 'TikTok', mentions: 5600, sentiment: 0.62, engagement: 1200000, growth: 22.1 },
];

// Topic analysis data
export const topicAnalysis: TopicData[] = [
  { topic: 'Autopilot & FSD', mentions: 4520, sentiment: 0.71, trend: 'up' },
  { topic: 'Cybertruck Production', mentions: 3850, sentiment: 0.68, trend: 'stable' },
  { topic: 'Supercharger Network', mentions: 2940, sentiment: 0.83, trend: 'up' },
  { topic: 'Stock Performance', mentions: 2650, sentiment: 0.59, trend: 'down' },
  { topic: 'Model Y Updates', mentions: 2180, sentiment: 0.76, trend: 'up' },
  { topic: 'Tesla Bot/Optimus', mentions: 1920, sentiment: 0.65, trend: 'stable' },
  { topic: 'Energy Storage', mentions: 1560, sentiment: 0.74, trend: 'up' },
  { topic: 'Manufacturing', mentions: 1340, sentiment: 0.72, trend: 'stable' },
  { topic: 'Competition', mentions: 1180, sentiment: 0.45, trend: 'down' },
  { topic: 'Elon Musk Leadership', mentions: 980, sentiment: 0.52, trend: 'down' },
];

// Keyword clustering data
export const keywordClusters: KeywordCluster[] = [
  {
    keyword: 'autopilot',
    frequency: 4520,
    sentiment: 0.71,
    related_terms: ['FSD', 'self-driving', 'autonomous', 'safety']
  },
  {
    keyword: 'cybertruck',
    frequency: 3850,
    sentiment: 0.68,
    related_terms: ['production', 'delivery', 'design', 'bulletproof']
  },
  {
    keyword: 'supercharger',
    frequency: 2940,
    sentiment: 0.83,
    related_terms: ['charging', 'network', 'fast', 'expansion']
  },
  {
    keyword: 'model-y',
    frequency: 2180,
    sentiment: 0.76,
    related_terms: ['suv', 'family', 'popular', 'efficient']
  },
  {
    keyword: 'stock',
    frequency: 2650,
    sentiment: 0.59,
    related_terms: ['price', 'valuation', 'market', 'investors']
  },
  {
    keyword: 'optimus',
    frequency: 1920,
    sentiment: 0.65,
    related_terms: ['robot', 'humanoid', 'ai', 'future']
  },
  {
    keyword: 'energy',
    frequency: 1560,
    sentiment: 0.74,
    related_terms: ['solar', 'powerwall', 'grid', 'storage']
  },
  {
    keyword: 'competition',
    frequency: 1180,
    sentiment: 0.45,
    related_terms: ['rivals', 'market-share', 'pressure', 'challenge']
  }
];

// Dashboard overview metrics
export const overviewMetrics = {
  totalMentions: 35420,
  avgSentiment: 0.72,
  sentimentChange: '+0.05',
  engagementRate: 8.7,
  topCountries: ['United States', 'Germany', 'China', 'United Kingdom', 'Canada'],
  peakHours: ['9:00 AM', '1:00 PM', '7:00 PM'],
};

// Real-time alerts (mock)
export const recentAlerts = [
  {
    id: 1,
    type: 'positive',
    message: 'Major surge in positive Cybertruck mentions following delivery announcement',
    timestamp: '2025-01-28T10:30:00Z',
    impact: 'high'
  },
  {
    id: 2,
    type: 'negative',
    message: 'Increased concerns about Autopilot safety after recent incident coverage',
    timestamp: '2025-01-28T08:15:00Z',
    impact: 'medium'
  },
  {
    id: 3,
    type: 'neutral',
    message: 'Tesla quarterly earnings discussion trending across financial platforms',
    timestamp: '2025-01-28T07:45:00Z',
    impact: 'high'
  }
];

// New architecture interfaces
export interface Campaign {
  id: string;
  name: string;
  description: string;
  postUrls: string[];
  type: 'product_launch' | 'brand_awareness' | 'feature_highlight' | 'crisis_response';
  status: 'active' | 'paused' | 'completed' | 'draft';
  created_date: string;
  start_date: string;
  end_date: string;
  target_audience: string[];
  platforms: string[];
}

export interface Brand {
  id: string;
  name: string;
  description: string;
  postUrls: string[];
  keywords: string[];
  category: string;
  status: 'active' | 'inactive';
  created_date: string;
  competitors: string[];
}

export interface Content {
  id: string;
  title: string;
  description: string;
  postUrl: string;
  platform: string;
  content_type: 'video' | 'post' | 'article' | 'image' | 'story';
  author: string;
  publish_date: string;
  status: 'published' | 'draft' | 'archived';
  tags: string[];
}

export interface AnalysisResult {
  id: string;
  entity_id: string;
  entity_type: 'campaign' | 'brand' | 'content';
  analysis_date: string;
  
  // Sentiment Analysis
  sentiment: {
    overall_score: number;
    positive: number;
    negative: number;
    neutral: number;
    confidence: number;
  };
  
  // Topic Analysis
  topics: Array<{
    topic: string;
    relevance: number;
    mentions: number;
    sentiment: number;
  }>;
  
  // Emotional Analysis
  emotions: {
    joy: number;
    anger: number;
    fear: number;
    sadness: number;
    surprise: number;
    trust: number;
    anticipation: number;
    disgust: number;
  };
  
  // Audience Analysis
  audience: {
    demographics: {
      age_groups: Array<{ range: string; percentage: number }>;
      genders: Array<{ gender: string; percentage: number }>;
      locations: Array<{ location: string; percentage: number }>;
    };
    engagement_patterns: {
      peak_hours: string[];
      active_days: string[];
      engagement_rate: number;
    };
    interests: Array<{ interest: string; affinity: number }>;
  };
  
  // Performance Metrics
  metrics: {
    total_mentions: number;
    reach: number;
    impressions: number;
    engagement_rate: number;
    share_rate: number;
    click_rate: number;
    conversion_rate: number;
  };
  
  // Competitive Analysis
  competitive_insights: Array<{
    competitor: string;
    mention_share: number;
    sentiment_comparison: number;
    key_differences: string[];
  }>;
}

// Mock data for new architecture
export const campaigns: Campaign[] = [
  {
    id: 'camp_001',
    name: 'Cybertruck Launch Campaign',
    description: 'Comprehensive campaign tracking the public reception of Tesla Cybertruck launch',
    postUrls: [
      'https://twitter.com/tesla/status/1234567890',
      'https://youtube.com/watch?v=cybertruck_launch',
      'https://reddit.com/r/teslamotors/cybertruck_delivery'
    ],
    type: 'product_launch',
    status: 'active',
    created_date: '2025-01-10',
    start_date: '2025-01-15',
    end_date: '2025-02-28',
    target_audience: ['Tech Enthusiasts', 'Truck Owners', 'EV Adopters'],
    platforms: ['Twitter/X', 'YouTube', 'Reddit', 'Instagram']
  },
  {
    id: 'camp_002',
    name: 'FSD Beta Awareness',
    description: 'Monitor public sentiment around Full Self-Driving beta releases and updates',
    postUrls: [
      'https://twitter.com/elonmusk/status/fsd_update',
      'https://youtube.com/watch?v=fsd_demo_v12',
      'https://linkedin.com/posts/tesla-fsd-safety'
    ],
    type: 'feature_highlight',
    status: 'active',
    created_date: '2025-01-05',
    start_date: '2025-01-10',
    end_date: '2025-03-15',
    target_audience: ['Current Tesla Owners', 'Tech Enthusiasts', 'Early Adopters'],
    platforms: ['Twitter/X', 'YouTube', 'LinkedIn']
  },
  {
    id: 'camp_003',
    name: 'Supercharger Network Expansion',
    description: 'Track public response to Tesla Supercharger network expansion announcements',
    postUrls: [
      'https://twitter.com/tesla/supercharger_expansion',
      'https://linkedin.com/posts/tesla-charging-network',
      'https://facebook.com/tesla/supercharger_news'
    ],
    type: 'brand_awareness',
    status: 'active',
    created_date: '2024-11-25',
    start_date: '2024-12-01',
    end_date: '2025-02-15',
    target_audience: ['EV Owners', 'Road Trip Enthusiasts', 'Fleet Managers'],
    platforms: ['Twitter/X', 'LinkedIn', 'Facebook']
  }
];

export const brands: Brand[] = [
  {
    id: 'brand_001',
    name: 'Tesla Motors',
    description: 'Main Tesla brand monitoring across all product lines and corporate communications',
    postUrls: [
      'https://twitter.com/tesla',
      'https://instagram.com/teslamotors',
      'https://youtube.com/tesla',
      'https://linkedin.com/company/tesla-motors'
    ],
    keywords: ['tesla', 'electric vehicle', 'ev', 'elon musk', 'model s', 'model 3', 'model x', 'model y', 'cybertruck'],
    category: 'Automotive',
    status: 'active',
    created_date: '2024-01-01',
    competitors: ['Ford', 'Rivian', 'Lucid Motors', 'BMW', 'Mercedes EQS']
  },
  {
    id: 'brand_002',
    name: 'Tesla Energy',
    description: 'Tesla energy products including solar panels, solar roof, and energy storage solutions',
    postUrls: [
      'https://twitter.com/tesla/energy',
      'https://linkedin.com/showcase/tesla-energy'
    ],
    keywords: ['tesla energy', 'solar panels', 'solar roof', 'powerwall', 'megapack', 'renewable energy'],
    category: 'Energy',
    status: 'active',
    created_date: '2024-01-01',
    competitors: ['SunPower', 'Enphase', 'First Solar', 'Canadian Solar']
  },
  {
    id: 'brand_003',
    name: 'Tesla Autopilot/FSD',
    description: 'Focus on Tesla autonomous driving capabilities and public perception',
    postUrls: [
      'https://twitter.com/tesla/autopilot',
      'https://youtube.com/playlist?list=tesla_fsd_demos'
    ],
    keywords: ['autopilot', 'full self driving', 'fsd', 'autonomous', 'self driving', 'tesla ai'],
    category: 'Technology',
    status: 'active',
    created_date: '2024-01-01',
    competitors: ['Waymo', 'Cruise', 'Argo AI', 'Mercedes Drive Pilot']
  }
];

export const contents: Content[] = [
  {
    id: 'content_001',
    title: 'Cybertruck Delivery Event Highlights',
    description: 'Official Tesla video showcasing the first Cybertruck deliveries to customers',
    postUrl: 'https://youtube.com/watch?v=cybertruck_delivery_event',
    platform: 'YouTube',
    content_type: 'video',
    author: 'Tesla',
    publish_date: '2025-01-20',
    status: 'published',
    tags: ['cybertruck', 'delivery', 'launch', 'electric truck']
  },
  {
    id: 'content_002',
    title: 'FSD Beta v12.3 Safety Update',
    description: 'Elon Musk tweet thread about FSD Beta safety improvements and statistics',
    postUrl: 'https://twitter.com/elonmusk/status/fsd_safety_update',
    platform: 'Twitter/X',
    content_type: 'post',
    author: 'Elon Musk',
    publish_date: '2025-01-25',
    status: 'published',
    tags: ['fsd', 'safety', 'beta', 'autonomous driving']
  },
  {
    id: 'content_003',
    title: 'Customer Review: First Week with Cybertruck',
    description: 'Detailed Reddit post from early Cybertruck customer sharing first impressions',
    postUrl: 'https://reddit.com/r/teslamotors/cybertruck_first_week',
    platform: 'Reddit',
    content_type: 'post',
    author: 'u/TeslaOwner2025',
    publish_date: '2025-01-22',
    status: 'published',
    tags: ['cybertruck', 'review', 'customer experience', 'electric truck']
  },
  {
    id: 'content_004',
    title: 'Tesla Supercharger Network Reaches 50,000 Stalls',
    description: 'LinkedIn article announcing major milestone in charging infrastructure',
    postUrl: 'https://linkedin.com/posts/tesla-supercharger-milestone',
    platform: 'LinkedIn',
    content_type: 'article',
    author: 'Tesla',
    publish_date: '2025-01-18',
    status: 'published',
    tags: ['supercharger', 'charging', 'infrastructure', 'milestone']
  }
];

// Time series data for analysis dimensions
export interface TimeSeriesData {
  date: string;
  sentiment: number;
  mentions: number;
  engagement: number;
  positive: number;
  negative: number;
  neutral: number;
}

// Generate time series data for the last 30 days
const generateTimeSeriesData = (baseValue: number, variance: number = 0.2): TimeSeriesData[] => {
  const data: TimeSeriesData[] = [];
  const now = new Date();
  
  for (let i = 29; i >= 0; i--) {
    const date = new Date(now);
    date.setDate(date.getDate() - i);
    
    const variation = (Math.random() - 0.5) * variance;
    const sentiment = Math.max(0.1, Math.min(1, baseValue + variation));
    const mentions = Math.floor(Math.random() * 1000) + 500;
    const engagement = Math.floor(Math.random() * 15) + 5;
    
    // Calculate sentiment distribution
    const positive = Math.floor(sentiment * 100);
    const negative = Math.floor((1 - sentiment) * 60);
    const neutral = 100 - positive - negative;
    
    data.push({
      date: date.toISOString().split('T')[0],
      sentiment: Math.round(sentiment * 100),
      mentions,
      engagement,
      positive,
      negative,
      neutral
    });
  }
  
  return data;
};

// Time series data for different entities
export const timeSeriesData = {
  'camp_001': generateTimeSeriesData(0.68),
  'camp_002': generateTimeSeriesData(0.75),
  'camp_003': generateTimeSeriesData(0.72),
  'brand_001': generateTimeSeriesData(0.73),
  'brand_002': generateTimeSeriesData(0.78),
  'brand_003': generateTimeSeriesData(0.71),
  'content_001': generateTimeSeriesData(0.76),
  'content_002': generateTimeSeriesData(0.82),
  'content_003': generateTimeSeriesData(0.69),
  'content_004': generateTimeSeriesData(0.74)
};

// Mock analysis results
export const analysisResults: AnalysisResult[] = [
  {
    id: 'analysis_001',
    entity_id: 'camp_001',
    entity_type: 'campaign',
    analysis_date: '2025-01-28',
    sentiment: {
      overall_score: 0.68,
      positive: 42,
      negative: 28,
      neutral: 30,
      confidence: 0.89
    },
    topics: [
      { topic: 'Delivery Timeline', relevance: 0.85, mentions: 1200, sentiment: 0.65 },
      { topic: 'Design & Aesthetics', relevance: 0.78, mentions: 980, sentiment: 0.72 },
      { topic: 'Performance Specs', relevance: 0.73, mentions: 850, sentiment: 0.81 },
      { topic: 'Pricing Concerns', relevance: 0.69, mentions: 720, sentiment: 0.45 }
    ],
    emotions: {
      joy: 0.32,
      anger: 0.18,
      fear: 0.12,
      sadness: 0.08,
      surprise: 0.25,
      trust: 0.38,
      anticipation: 0.45,
      disgust: 0.09
    },
    audience: {
      demographics: {
        age_groups: [
          { range: '25-34', percentage: 35 },
          { range: '35-44', percentage: 28 },
          { range: '45-54', percentage: 22 },
          { range: '18-24', percentage: 15 }
        ],
        genders: [
          { gender: 'Male', percentage: 72 },
          { gender: 'Female', percentage: 26 },
          { gender: 'Other', percentage: 2 }
        ],
        locations: [
          { location: 'United States', percentage: 45 },
          { location: 'Germany', percentage: 15 },
          { location: 'Canada', percentage: 12 },
          { location: 'United Kingdom', percentage: 10 },
          { location: 'Australia', percentage: 8 },
          { location: 'Other', percentage: 10 }
        ]
      },
      engagement_patterns: {
        peak_hours: ['9:00 AM', '1:00 PM', '7:00 PM'],
        active_days: ['Monday', 'Wednesday', 'Friday'],
        engagement_rate: 11.2
      },
      interests: [
        { interest: 'Electric Vehicles', affinity: 0.92 },
        { interest: 'Technology', affinity: 0.85 },
        { interest: 'Automotive', affinity: 0.78 },
        { interest: 'Environment', affinity: 0.65 }
      ]
    },
    metrics: {
      total_mentions: 38500,
      reach: 2800000,
      impressions: 4200000,
      engagement_rate: 11.2,
      share_rate: 3.4,
      click_rate: 2.8,
      conversion_rate: 1.2
    },
    competitive_insights: [
      {
        competitor: 'Ford Lightning',
        mention_share: 0.35,
        sentiment_comparison: -0.15,
        key_differences: ['Price point', 'Availability', 'Traditional brand trust']
      },
      {
        competitor: 'Rivian R1T',
        mention_share: 0.25,
        sentiment_comparison: -0.08,
        key_differences: ['Adventure focus', 'Startup perception', 'Feature set']
      }
    ]
  },
  {
    id: 'analysis_002',
    entity_id: 'brand_001',
    entity_type: 'brand',
    analysis_date: '2025-01-28',
    sentiment: {
      overall_score: 0.73,
      positive: 48,
      negative: 24,
      neutral: 28,
      confidence: 0.92
    },
    topics: [
      { topic: 'Innovation', relevance: 0.92, mentions: 3200, sentiment: 0.81 },
      { topic: 'Sustainability', relevance: 0.87, mentions: 2800, sentiment: 0.78 },
      { topic: 'Customer Service', relevance: 0.71, mentions: 1900, sentiment: 0.58 },
      { topic: 'Leadership', relevance: 0.69, mentions: 1600, sentiment: 0.62 },
      { topic: 'Product Quality', relevance: 0.82, mentions: 2400, sentiment: 0.74 }
    ],
    emotions: {
      joy: 0.38,
      anger: 0.15,
      fear: 0.09,
      sadness: 0.06,
      surprise: 0.22,
      trust: 0.45,
      anticipation: 0.42,
      disgust: 0.07
    },
    audience: {
      demographics: {
        age_groups: [
          { range: '25-34', percentage: 32 },
          { range: '35-44', percentage: 31 },
          { range: '45-54', percentage: 25 },
          { range: '18-24', percentage: 12 }
        ],
        genders: [
          { gender: 'Male', percentage: 68 },
          { gender: 'Female', percentage: 30 },
          { gender: 'Other', percentage: 2 }
        ],
        locations: [
          { location: 'United States', percentage: 42 },
          { location: 'China', percentage: 18 },
          { location: 'Germany', percentage: 12 },
          { location: 'United Kingdom', percentage: 9 },
          { location: 'Canada', percentage: 8 },
          { location: 'Other', percentage: 11 }
        ]
      },
      engagement_patterns: {
        peak_hours: ['8:00 AM', '12:00 PM', '6:00 PM'],
        active_days: ['Tuesday', 'Wednesday', 'Thursday'],
        engagement_rate: 13.7
      },
      interests: [
        { interest: 'Electric Vehicles', affinity: 0.95 },
        { interest: 'Technology', affinity: 0.89 },
        { interest: 'Environment', affinity: 0.82 },
        { interest: 'Innovation', affinity: 0.87 }
      ]
    },
    metrics: {
      total_mentions: 125000,
      reach: 8500000,
      impressions: 12800000,
      engagement_rate: 13.7,
      share_rate: 4.2,
      click_rate: 3.1,
      conversion_rate: 1.8
    },
    competitive_insights: [
      {
        competitor: 'BMW',
        mention_share: 0.28,
        sentiment_comparison: 0.12,
        key_differences: ['Traditional luxury', 'Dealership network', 'Heritage']
      },
      {
        competitor: 'Mercedes',
        mention_share: 0.32,
        sentiment_comparison: 0.08,
        key_differences: ['Luxury positioning', 'Comfort focus', 'Premium pricing']
      },
      {
        competitor: 'Ford',
        mention_share: 0.45,
        sentiment_comparison: 0.15,
        key_differences: ['Mass market appeal', 'Traditional manufacturing', 'Established brand']
      }
    ]
  },
  {
    id: 'analysis_003',
    entity_id: 'content_001',
    entity_type: 'content',
    analysis_date: '2025-01-28',
    sentiment: {
      overall_score: 0.76,
      positive: 52,
      negative: 18,
      neutral: 30,
      confidence: 0.87
    },
    topics: [
      { topic: 'Product Features', relevance: 0.94, mentions: 2800, sentiment: 0.82 },
      { topic: 'User Experience', relevance: 0.81, mentions: 1950, sentiment: 0.78 },
      { topic: 'Performance', relevance: 0.77, mentions: 1650, sentiment: 0.84 },
      { topic: 'Value Proposition', relevance: 0.65, mentions: 1200, sentiment: 0.69 }
    ],
    emotions: {
      joy: 0.41,
      anger: 0.12,
      fear: 0.08,
      sadness: 0.05,
      surprise: 0.28,
      trust: 0.42,
      anticipation: 0.48,
      disgust: 0.06
    },
    audience: {
      demographics: {
        age_groups: [
          { range: '25-34', percentage: 38 },
          { range: '35-44', percentage: 27 },
          { range: '18-24', percentage: 20 },
          { range: '45-54', percentage: 15 }
        ],
        genders: [
          { gender: 'Male', percentage: 75 },
          { gender: 'Female', percentage: 23 },
          { gender: 'Other', percentage: 2 }
        ],
        locations: [
          { location: 'United States', percentage: 48 },
          { location: 'Germany', percentage: 14 },
          { location: 'Canada', percentage: 11 },
          { location: 'United Kingdom', percentage: 9 },
          { location: 'Australia', percentage: 7 },
          { location: 'Other', percentage: 11 }
        ]
      },
      engagement_patterns: {
        peak_hours: ['7:00 PM', '8:00 PM', '9:00 PM'],
        active_days: ['Friday', 'Saturday', 'Sunday'],
        engagement_rate: 15.6
      },
      interests: [
        { interest: 'Automotive', affinity: 0.94 },
        { interest: 'Technology', affinity: 0.88 },
        { interest: 'Electric Vehicles', affinity: 0.91 },
        { interest: 'Innovation', affinity: 0.83 }
      ]
    },
    metrics: {
      total_mentions: 8600,
      reach: 450000,
      impressions: 680000,
      engagement_rate: 15.6,
      share_rate: 6.2,
      click_rate: 4.3,
      conversion_rate: 2.1
    },
    competitive_insights: [
      {
        competitor: 'Traditional Auto Content',
        mention_share: 0.62,
        sentiment_comparison: 0.22,
        key_differences: ['Innovation focus', 'Tech integration', 'Future vision']
      },
      {
        competitor: 'Other EV Content',
        mention_share: 0.38,
        sentiment_comparison: 0.18,
        key_differences: ['Production scale', 'Ecosystem approach', 'Brand strength']
      }
    ]
  }
];