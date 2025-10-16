import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import { Progress } from "./ui/progress";
import { Campaign, Brand, Content } from "../lib/mock-data";
import { AnalysisFilters, FilterState } from "./AnalysisFilters";
import { TimeSeriesCharts } from "./TimeSeriesCharts";
import { EntityDetails } from "./EntityDetails";
import { resultsAPI } from "../lib/api-client";
import { 
  ArrowLeft, 
  TrendingUp, 
  MessageSquare, 
  Heart, 
  Users, 
  Target, 
  BarChart3,
  PieChart,
  Globe,
  Info,
  Loader2
} from "lucide-react";
import { 
  Tooltip, 
  ResponsiveContainer, 
  PieChart as RechartsPieChart, 
  Pie, 
  Cell,
  BarChart as RechartsBarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Legend,
  RadarChart as RechartsRadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis
} from "recharts";

interface AnalysisViewProps {
  entity: Campaign | Brand | Content;
  entityType: 'campaign' | 'brand' | 'content';
  onBack: () => void;
}

// Interface untuk data API response
interface BrandSummaryData {
  brand_name: string;
  period: string;
  total_posts: number;
  total_engagement: number;
  avg_engagement_per_post: number;
  sentiment_distribution: {
    Positive: number;
    Negative: number;
    Neutral: number;
  };
  sentiment_percentage: {
    Positive: number;
    Negative: number;
    Neutral: number;
  };
  platform_breakdown: Record<string, number>;
  trending_topics: Array<{
    topic: string;
    count: number;
    sentiment: number;
  }>;
}

interface SentimentTimelineData {
  timeline: Array<{
    date: string;
    Positive: number;
    Negative: number;
    Neutral: number;
  }>;
}

export function RealAnalysisView({ entity, entityType, onBack }: AnalysisViewProps) {
  // State untuk data API
  const [brandSummary, setBrandSummary] = useState<BrandSummaryData | null>(null);
  const [sentimentTimeline, setSentimentTimeline] = useState<SentimentTimelineData | null>(null);
  const [trendingTopics, setTrendingTopics] = useState<any[]>([]);
  const [emotionsData, setEmotionsData] = useState<any>(null);
  const [demographicsData, setDemographicsData] = useState<any>(null);
  const [performanceData, setPerformanceData] = useState<any>(null);
  const [engagementPatterns, setEngagementPatterns] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Pagination state untuk topics
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 6;

  // Filter state
  const [filters, setFilters] = useState<FilterState>({
    dateRange: {
      start: '',
      end: ''
    },
    platforms: [],
    posts: [],
    ...(entityType === 'brand' && { keywords: [] })
  });

  // Get brand name berdasarkan entity type
  const getBrandName = () => {
    switch (entityType) {
      case 'campaign': return (entity as Campaign).name;
      case 'brand': return (entity as Brand).name;
      case 'content': return 'testbrand'; // Default untuk content
      default: return 'testbrand';
    }
  };

  // Load data dari API
  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        const brandName = getBrandName();
        
        // Build query parameters from filters
        const queryParams = new URLSearchParams();
        if (filters.dateRange.start) {
          queryParams.append('start_date', filters.dateRange.start);
        }
        if (filters.dateRange.end) {
          queryParams.append('end_date', filters.dateRange.end);
        }
        if (filters.platforms.length > 0) {
          queryParams.append('platforms', filters.platforms.join(','));
        }
        
        // Load brand summary
        const summaryResponse = await resultsAPI.getBrandSummary(brandName);
        setBrandSummary(summaryResponse);
        
        // Load sentiment timeline
        try {
          const timelineResponse = await resultsAPI.getSentimentTimeline(brandName);
          setSentimentTimeline(timelineResponse);
        } catch (timelineError) {
          console.warn('Timeline data not available:', timelineError);
          // Timeline data tidak tersedia, tidak perlu error
        }
        
        // Load additional data for tabs
        try {
          // Load trending topics
          const topicsResponse = await fetch(`http://localhost:8000/api/v1/results/brands/${brandName}/trending-topics`);
          if (topicsResponse.ok) {
            const topicsData = await topicsResponse.json();
            console.log('Trending topics loaded:', topicsData);
            setTrendingTopics(topicsData);
          } else {
            console.error('Failed to load trending topics:', topicsResponse.status, topicsResponse.statusText);
          }

          // Load engagement patterns
          try {
            const engagementResponse = await resultsAPI.getEngagementPatterns(brandName);
            setEngagementPatterns(engagementResponse);
            console.log('Engagement patterns loaded:', engagementResponse);
          } catch (engagementError) {
            console.warn('Engagement patterns not available:', engagementError);
          }
          
          // Load emotions data
          const emotionsResponse = await fetch(`http://localhost:8000/api/v1/results/brands/${brandName}/emotions`);
          if (emotionsResponse.ok) {
            const emotionsData = await emotionsResponse.json();
            console.log('Emotions data loaded:', emotionsData);
            setEmotionsData(emotionsData);
          }
          
          // Load demographics data
          const demographicsResponse = await fetch(`http://localhost:8000/api/v1/results/brands/${brandName}/demographics`);
          if (demographicsResponse.ok) {
            const demographicsData = await demographicsResponse.json();
            console.log('Demographics data loaded:', demographicsData);
            setDemographicsData(demographicsData);
          }
          
          // Load performance metrics
          const performanceResponse = await fetch(`http://localhost:8000/api/v1/results/brands/${brandName}/performance`);
          if (performanceResponse.ok) {
            const performanceData = await performanceResponse.json();
            console.log('Performance data loaded:', performanceData);
            console.log('Performance data keys:', Object.keys(performanceData));
            console.log('Total engagement:', performanceData.total_engagement);
            console.log('Estimated reach:', performanceData.estimated_reach);
            setPerformanceData(performanceData);
          } else {
            console.error('Failed to load performance data:', performanceResponse.status, performanceResponse.statusText);
          }
          
          
        } catch (additionalDataError) {
          console.warn('Additional data loading failed:', additionalDataError);
          // Non-critical, continue with main data
        }
        
      } catch (err) {
        console.error('Error loading analysis data:', err);
        setError(err instanceof Error ? err.message : 'Failed to load analysis data');
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [entity, entityType, filters]);

  // Fallback data jika API tidak tersedia - dengan nilai 0 untuk parameter kosong
  const getFallbackData = (): BrandSummaryData => ({
    brand_name: getBrandName(),
    period: "Last 30 days",
    total_posts: 0,
    total_engagement: 0,
    avg_engagement_per_post: 0,
    sentiment_distribution: { Positive: 0, Negative: 0, Neutral: 0 },
    sentiment_percentage: { Positive: 0, Negative: 0, Neutral: 0 },
    platform_breakdown: {},
    trending_topics: []
  });

  const data = brandSummary || getFallbackData();

  // Pastikan semua nilai memiliki default 0 jika kosong
  const safeData = {
    ...data,
    total_posts: data.total_posts || 0,
    total_engagement: data.total_engagement || 0,
    avg_engagement_per_post: data.avg_engagement_per_post || 0,
    sentiment_distribution: {
      Positive: data.sentiment_distribution.Positive || 0,
      Negative: data.sentiment_distribution.Negative || 0,
      Neutral: data.sentiment_distribution.Neutral || 0
    },
    sentiment_percentage: {
      Positive: data.sentiment_percentage.Positive || 0,
      Negative: data.sentiment_percentage.Negative || 0,
      Neutral: data.sentiment_percentage.Neutral || 0
    },
    platform_breakdown: data.platform_breakdown || {},
    trending_topics: data.trending_topics || []
  };

  // Prepare chart data dengan nilai 0 untuk data kosong
  const sentimentData = [
    { name: 'Positive', value: safeData.sentiment_percentage.Positive, color: '#22c55e' },
    { name: 'Neutral', value: safeData.sentiment_percentage.Neutral, color: '#6b7280' },
    { name: 'Negative', value: safeData.sentiment_percentage.Negative, color: '#ef4444' }
  ];


  const topicData = safeData.trending_topics.map(topic => ({
    name: topic.topic,
    mentions: topic.count || 0,
    sentiment: Math.round((topic.sentiment || 0) * 100)
  }));

  // Timeline data untuk chart dengan nilai 0 jika kosong
  const timelineChartData = sentimentTimeline?.timeline?.map(item => ({
    date: new Date(item.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    positive: item.Positive || 0,
    negative: item.Negative || 0,
    neutral: item.Neutral || 0,
    sentiment: Math.round(((item.Positive || 0) - (item.Negative || 0)) / ((item.Positive || 0) + (item.Negative || 0) + (item.Neutral || 0) || 1) * 100)
  })) || [];

  const getEntityTitle = () => {
    switch (entityType) {
      case 'campaign': return (entity as Campaign).name;
      case 'brand': return (entity as Brand).name;
      case 'content': return (entity as Content).title;
    }
  };

  const getEntityDescription = () => {
    switch (entityType) {
      case 'campaign': return (entity as Campaign).description;
      case 'brand': return (entity as Brand).description;
      case 'content': return (entity as Content).description;
    }
  };

  const getSentimentColor = (score: number) => {
    if (score >= 70) return 'text-green-600';
    if (score >= 50) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getSentimentBackground = (score: number) => {
    if (score >= 70) return 'bg-green-100';
    if (score >= 50) return 'bg-yellow-100';
    return 'bg-red-100';
  };

  // Calculate overall sentiment score dengan default 0
  const overallSentiment = Math.round(safeData.sentiment_percentage.Positive);

  // Mock analysis data untuk kompatibilitas dengan struktur lama
  const mockAnalysis = {
    analysis_date: new Date().toLocaleDateString(),
    sentiment: {
      overall_score: safeData.sentiment_percentage.Positive / 100,
      confidence: 0.85,
      positive: safeData.sentiment_distribution.Positive,
      negative: safeData.sentiment_distribution.Negative,
      neutral: safeData.sentiment_distribution.Neutral
    },
    metrics: {
      total_mentions: safeData.total_posts,
      engagement_rate: safeData.total_posts > 0 ? ((safeData.total_engagement / safeData.total_posts) * 100) : 0,
      reach: safeData.total_engagement
    },
    emotions: {
      joy: 0.3,
      sadness: 0.1,
      anger: 0.05,
      fear: 0.02,
      surprise: 0.1,
      disgust: 0.03
    },
    topics: topicData.map(topic => ({
      topic: topic.name,
      mentions: topic.mentions,
      sentiment: topic.sentiment / 100
    })),
    competitive_insights: []
  };

  // Mock time series data - convert to array format expected by TimeSeriesCharts
  const mockTimeSeriesData = timelineChartData.map(item => ({
    date: item.date,
    sentiment: item.sentiment,
    mentions: item.positive + item.negative + item.neutral,
    engagement: Math.round((item.positive + item.negative + item.neutral) * 1.5),
    positive: item.positive,
    negative: item.negative,
    neutral: item.neutral
  }));

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button variant="outline" size="sm" onClick={onBack}>
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back
            </Button>
            <div>
              <h2 className="text-xl font-semibold">{getEntityTitle()}</h2>
              <p className="text-sm text-muted-foreground">{entityType.charAt(0).toUpperCase() + entityType.slice(1)} Analysis</p>
            </div>
          </div>
          <Badge variant="secondary">
            Loading...
          </Badge>
        </div>
        
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4" />
            <p className="text-muted-foreground">Loading analysis data...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button variant="outline" size="sm" onClick={onBack}>
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back
            </Button>
            <div>
              <h2 className="text-xl font-semibold">{getEntityTitle()}</h2>
              <p className="text-sm text-muted-foreground">{entityType.charAt(0).toUpperCase() + entityType.slice(1)} Analysis</p>
            </div>
          </div>
        </div>
        
        <Card>
          <CardContent className="pt-6">
            <div className="text-center">
              <p className="text-red-600 mb-4">Error loading analysis data</p>
              <p className="text-muted-foreground">{error}</p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header - SAMA PERSIS dengan AnalysisView asli */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="outline" size="sm" onClick={onBack}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back
          </Button>
          <div>
            <h2 className="text-xl font-semibold">{getEntityTitle()}</h2>
            <p className="text-sm text-muted-foreground">{entityType.charAt(0).toUpperCase() + entityType.slice(1)} Analysis</p>
          </div>
        </div>
        <Badge variant="secondary">
          Last updated: {mockAnalysis.analysis_date}
        </Badge>
      </div>

      {/* Description - SAMA PERSIS dengan AnalysisView asli */}
      <Card>
        <CardContent className="pt-6">
          <p className="text-muted-foreground">{getEntityDescription()}</p>
        </CardContent>
      </Card>

      {/* Key Metrics Overview - SAMA PERSIS dengan AnalysisView asli */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Overall Sentiment</p>
                <p className={`text-2xl font-bold ${getSentimentColor(overallSentiment)}`}>
                  {overallSentiment}%
                </p>
              </div>
              <div className={`p-2 rounded-lg ${getSentimentBackground(overallSentiment)}`}>
                <TrendingUp className={`h-5 w-5 ${getSentimentColor(overallSentiment)}`} />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Total Mentions</p>
                <p className="text-2xl font-bold">{safeData.total_posts.toLocaleString()}</p>
              </div>
              <div className="p-2 rounded-lg bg-blue-100">
                <MessageSquare className="h-5 w-5 text-blue-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Engagement Rate</p>
                <p className="text-2xl font-bold">
                  {performanceData?.engagement_rate ? 
                    `${performanceData.engagement_rate.toFixed(1)}%` : 
                    safeData.total_posts > 0 ? 
                      `${((safeData.total_engagement / safeData.total_posts) * 100).toFixed(1)}%` : 
                      '0%'
                  }
                </p>
              </div>
              <div className="p-2 rounded-lg bg-green-100">
                <Heart className="h-5 w-5 text-green-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Reach</p>
                <p className="text-2xl font-bold">
                  {safeData.total_engagement > 1000000 
                    ? `${(safeData.total_engagement / 1000000).toFixed(1)}M`
                    : safeData.total_engagement > 1000
                    ? `${(safeData.total_engagement / 1000).toFixed(1)}K`
                    : safeData.total_engagement.toLocaleString()}
                </p>
              </div>
              <div className="p-2 rounded-lg bg-purple-100">
                <Globe className="h-5 w-5 text-purple-600" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Analysis Content - SAMA PERSIS dengan AnalysisView asli */}
      <div className="grid lg:grid-cols-4 gap-6">
        {/* Filters Sidebar */}
        <div className="lg:col-span-1">
          <AnalysisFilters
            entity={entity}
            entityType={entityType}
            filters={filters}
            onFiltersChange={setFilters}
          />
        </div>

        {/* Analysis Content */}
        <div className="lg:col-span-3 space-y-6">
          {/* Time Series Charts */}
          <TimeSeriesCharts 
            data={[]} // Use empty array to force real data usage
            title={`${getEntityTitle()} - Time Series Analysis`}
            brandSummary={brandSummary}
            performanceData={performanceData}
            sentimentTimeline={sentimentTimeline}
          />

          {/* Detailed Analysis Tabs */}
          <Tabs defaultValue="overview" className="space-y-6">
            <TabsList className="flex w-full justify-start space-x-1">
              <TabsTrigger value="overview" className="flex items-center gap-2 px-4 py-2">
                <Info className="h-4 w-4" />
                <span className="hidden sm:inline">Overview</span>
              </TabsTrigger>
              <TabsTrigger value="sentiment" className="flex items-center gap-2 px-4 py-2">
                <TrendingUp className="h-4 w-4" />
                <span className="hidden sm:inline">Sentiment</span>
              </TabsTrigger>
              <TabsTrigger value="topics" className="flex items-center gap-2 px-4 py-2">
                <MessageSquare className="h-4 w-4" />
                <span className="hidden sm:inline">Topics</span>
              </TabsTrigger>
              <TabsTrigger value="emotions" className="flex items-center gap-2 px-4 py-2">
                <Heart className="h-4 w-4" />
                <span className="hidden sm:inline">Emotions</span>
              </TabsTrigger>
              <TabsTrigger value="audience" className="flex items-center gap-2 px-4 py-2">
                <Users className="h-4 w-4" />
                <span className="hidden sm:inline">Audience</span>
              </TabsTrigger>
            </TabsList>

            <TabsContent value="overview" className="space-y-6">
              <EntityDetails entity={entity} entityType={entityType} />
            </TabsContent>

            <TabsContent value="sentiment" className="space-y-6">
              <div className="grid md:grid-cols-2 gap-6">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <PieChart className="h-5 w-5" />
                      Sentiment Distribution
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={300}>
                      <RechartsPieChart>
                        <Pie
                          data={sentimentData}
                          cx="50%"
                          cy="50%"
                          innerRadius={60}
                          outerRadius={120}
                          paddingAngle={5}
                          dataKey="value"
                        >
                          {sentimentData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.color} />
                          ))}
                        </Pie>
                        <Tooltip formatter={(value) => [`${value}%`, 'Percentage']} />
                      </RechartsPieChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Sentiment Metrics</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span>Overall Score</span>
                        <span className="text-orange-500 font-semibold">
                          {overallSentiment}%
                        </span>
                      </div>
                      <Progress value={overallSentiment} className="h-2" />
                    </div>
                    
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span>Confidence Level</span>
                        <span className="text-gray-500 font-semibold">
                          {Math.round(overallSentiment * 1.3)}%
                        </span>
                      </div>
                      <Progress value={Math.round(overallSentiment * 1.3)} className="h-2" />
                    </div>

                    <div className="space-y-3 pt-4">
                      <div className="flex justify-between text-sm">
                        <span>Positive</span>
                        <span className="text-green-600 font-semibold">{safeData.sentiment_percentage.Positive}%</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span>Neutral</span>
                        <span className="text-gray-500 font-semibold">{safeData.sentiment_percentage.Neutral}%</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span>Negative</span>
                        <span className="text-red-600 font-semibold">{safeData.sentiment_percentage.Negative}%</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>

            <TabsContent value="topics" className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <MessageSquare className="h-5 w-5" />
                    Topic Analysis
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  
                  {trendingTopics.length > 0 ? (
                    <div className="space-y-6">
                      {/* Bar Chart - Dual Y-axis dengan engagement dan sentiment */}
                      <div className="h-[500px] bg-white p-6 rounded-lg border shadow-sm">
                        <div className="text-lg font-semibold text-gray-800 mb-4">Topic Analysis</div>
                        <div style={{ width: '100%', height: '400px', overflow: 'hidden' }}>
                          <RechartsBarChart
                            width={900}
                            height={400}
                            data={trendingTopics.map(topic => ({
                              name: topic.topic.length > 12 ? topic.topic.substring(0, 12) + '...' : topic.topic,
                              engagement: topic.engagement || 0,
                              sentiment: Math.round(((topic.sentiment || 0) + 1) * 50)
                            }))}
                            margin={{ top: 20, right: 50, left: 50, bottom: 60 }}
                          >
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis 
                              dataKey="name" 
                              angle={-15}
                              textAnchor="end"
                              height={60}
                              tick={{ fontSize: 10 }}
                            />
                            <YAxis 
                              yAxisId="left"
                              orientation="left"
                              tick={{ fontSize: 12 }}
                              tickFormatter={(value) => value.toLocaleString()}
                            />
                            <YAxis 
                              yAxisId="right"
                              orientation="right"
                              domain={[0, 100]}
                              tick={{ fontSize: 12 }}
                              tickFormatter={(value) => `${value}%`}
                            />
                            <Tooltip 
                              formatter={(value, name, props) => {
                                if (name === 'engagement') {
                                  return [value.toLocaleString(), 'Engagement'];
                                } else if (name === 'sentiment') {
                                  return [`${value}%`, 'Sentiment %'];
                                }
                                return [value, name];
                              }}
                              labelFormatter={(label, payload) => {
                                if (payload && payload.length > 0) {
                                  const originalTopic = trendingTopics.find(t => 
                                    (t.topic.length > 12 ? t.topic.substring(0, 12) + '...' : t.topic) === label
                                  );
                                  return originalTopic ? originalTopic.topic : label;
                                }
                                return label;
                              }}
                            />
                            <Legend />
                            <Bar yAxisId="left" dataKey="engagement" fill="#3b82f6" name="Engagement" />
                            <Bar yAxisId="right" dataKey="sentiment" fill="#10b981" name="Sentiment %" />
                          </RechartsBarChart>
                        </div>
                      </div>

                      {/* Topic Details - Dengan pagination */}
                      <div className="space-y-4">
                        <div className="flex items-center justify-between">
                          <h3 className="text-lg font-semibold text-gray-800">All Topics ({trendingTopics.length})</h3>
                          <div className="flex items-center gap-2">
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
                              disabled={currentPage === 1}
                            >
                              Previous
                            </Button>
                            <span className="text-sm text-gray-500">
                              Page {currentPage} of {Math.ceil(trendingTopics.length / itemsPerPage)}
                            </span>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => setCurrentPage(prev => Math.min(prev + 1, Math.ceil(trendingTopics.length / itemsPerPage)))}
                              disabled={currentPage === Math.ceil(trendingTopics.length / itemsPerPage)}
                            >
                              Next
                            </Button>
                          </div>
                        </div>
                        
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          {trendingTopics
                            .slice((currentPage - 1) * itemsPerPage, currentPage * itemsPerPage)
                            .map((topic, index) => {
                              // Hitung relevance berdasarkan count relatif terhadap max count
                              const maxCount = Math.max(...trendingTopics.map(t => t.count));
                              const relevancePercentage = Math.round((topic.count / maxCount) * 100);
                              
                              // Convert sentiment dari range -1 to 1 ke 0-100%
                              const sentimentPercentage = Math.round(((topic.sentiment + 1) / 2) * 100);
                              
                              return (
                                <div key={(currentPage - 1) * itemsPerPage + index} className="space-y-3 p-4 border rounded-lg">
                                  <div className="flex items-center justify-between">
                                    <h3 className="font-semibold text-gray-800 text-sm">{topic.topic}</h3>
                                    <span className="text-xs text-gray-500">{topic.count} mentions</span>
                                  </div>
                                  
                                  <div className="space-y-3">
                                    {/* Relevance */}
                                    <div className="space-y-2">
                                      <div className="flex justify-between text-xs">
                                        <span>Relevance</span>
                                        <span className="text-gray-500">{relevancePercentage}%</span>
                                      </div>
                                      <Progress value={relevancePercentage} className="h-2" />
                                    </div>
                                    
                                    {/* Sentiment */}
                                    <div className="space-y-2">
                                      <div className="flex justify-between text-xs">
                                        <span>Sentiment</span>
                                        <span className={
                                          sentimentPercentage > 60 ? "text-green-600" : 
                                          sentimentPercentage < 40 ? "text-red-600" : 
                                          "text-orange-600"
                                        }>
                                          {sentimentPercentage}%
                                        </span>
                                      </div>
                                      <Progress 
                                        value={sentimentPercentage} 
                                        className={`h-2 ${
                                          sentimentPercentage > 60 ? '[&>div]:bg-green-600' : 
                                          sentimentPercentage < 40 ? '[&>div]:bg-red-600' : 
                                          '[&>div]:bg-orange-600'
                                        }`}
                                      />
                                    </div>
                                  </div>
                                </div>
                              );
                            })}
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="text-center py-8 text-muted-foreground">
                      No trending topics available
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="emotions" className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Heart className="h-5 w-5" />
                    Emotional Analysis
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  
                  {emotionsData && emotionsData.emotions && emotionsData.emotions.length > 0 ? (
                    <div className="space-y-6">
                      {/* Radar Chart */}
                      <div className="h-[600px] bg-white p-6 rounded-lg border shadow-sm">
                        <div className="text-lg font-semibold text-gray-800 mb-4">Emotional Analysis</div>
                        <div className="flex justify-center items-center" style={{ width: '100%', height: '500px' }}>
                          {(() => {
                            const chartData = [
                              {
                                emotion: 'Joy',
                                value: emotionsData.emotions.find((e: any) => e.emotion === 'joy')?.percentage || 0,
                                fullMark: 100
                              },
                              {
                                emotion: 'Anger',
                                value: emotionsData.emotions.find((e: any) => e.emotion === 'anger')?.percentage || 0,
                                fullMark: 100
                              },
                              {
                                emotion: 'Fear',
                                value: emotionsData.emotions.find((e: any) => e.emotion === 'fear')?.percentage || 0,
                                fullMark: 100
                              },
                              {
                                emotion: 'Sadness',
                                value: emotionsData.emotions.find((e: any) => e.emotion === 'sadness')?.percentage || 0,
                                fullMark: 100
                              },
                              {
                                emotion: 'Surprise',
                                value: emotionsData.emotions.find((e: any) => e.emotion === 'surprise')?.percentage || 0,
                                fullMark: 100
                              },
                              {
                                emotion: 'Trust',
                                value: emotionsData.emotions.find((e: any) => e.emotion === 'trust')?.percentage || 0,
                                fullMark: 100
                              },
                              {
                                emotion: 'Anticipation',
                                value: emotionsData.emotions.find((e: any) => e.emotion === 'anticipation')?.percentage || 0,
                                fullMark: 100
                              },
                              {
                                emotion: 'Disgust',
                                value: emotionsData.emotions.find((e: any) => e.emotion === 'disgust')?.percentage || 0,
                                fullMark: 100
                              },
                              {
                                emotion: 'Neutral',
                                value: emotionsData.emotions.find((e: any) => e.emotion === 'neutral')?.percentage || 0,
                                fullMark: 100
                              }
                            ];
                            
                            // Calculate dynamic maximum axis value based on highest emotion
                            const maxEmotionValue = Math.max(...chartData.map(d => d.value));
                            const dynamicMax = Math.ceil(maxEmotionValue / 10) * 10; // Round up to nearest 10
                            
                            return (
                              <RechartsRadarChart
                                width={800}
                                height={500}
                                data={chartData}
                              >
                                <PolarGrid />
                                <PolarAngleAxis dataKey="emotion" />
                                <PolarRadiusAxis domain={[0, dynamicMax]} />
                                <Radar
                                  name="Emotions"
                                  dataKey="value"
                                  stroke="#8884d8"
                                  fill="#8884d8"
                                  fillOpacity={0.3}
                                />
                                <Tooltip 
                                  formatter={(value, name) => [`${value}%`, 'Percentage']}
                                />
                              </RechartsRadarChart>
                            );
                          })()}
                        </div>
                      </div>
                      
                      {/* Additional info */}
                      <div className="grid grid-cols-2 gap-4">
                        <div className="text-center p-3 bg-gray-50 rounded-lg">
                          <div className="text-sm text-gray-600">Total Analyzed</div>
                          <div className="text-lg font-semibold">{emotionsData.total_analyzed}</div>
                        </div>
                        <div className="text-center p-3 bg-gray-50 rounded-lg">
                          <div className="text-sm text-gray-600">Dominant Emotion</div>
                          <div className="text-lg font-semibold capitalize">{emotionsData.dominant_emotion}</div>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="text-center py-8 text-muted-foreground">
                      No emotion data available
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="audience" className="space-y-6">
              <div className="grid md:grid-cols-2 gap-6">
                {/* Left Column */}
                <div className="space-y-6">
                  {/* Demographics */}
                  <Card>
                    <CardHeader>
                      <CardTitle>Demographics</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-6">
                      
                      {/* Age Groups */}
                      <div>
                        <h3 className="text-lg font-semibold mb-3">Age Groups</h3>
                        <div className="space-y-3">
                          {demographicsData && demographicsData.age_groups && demographicsData.age_groups.length > 0 ? (
                            demographicsData.age_groups.map((age: any, index: number) => (
                              <div key={index} className="space-y-2">
                                <div className="flex justify-between text-sm">
                                  <span className="font-medium">{age.age_group}</span>
                                  <span className="text-gray-600">{age.percentage}%</span>
                                </div>
                                <Progress value={age.percentage} className="h-2" />
                              </div>
                            ))
                          ) : (
                            <div className="text-center text-muted-foreground">No age data available</div>
                          )}
                        </div>
                      </div>

                      {/* Gender Distribution */}
                      <div>
                        <h3 className="text-lg font-semibold mb-3">Gender Distribution</h3>
                        <div className="space-y-3">
                          {demographicsData && demographicsData.genders && demographicsData.genders.length > 0 ? (
                            demographicsData.genders.map((gender: any, index: number) => (
                              <div key={index} className="space-y-2">
                                <div className="flex justify-between text-sm">
                                  <span className="font-medium capitalize">{gender.gender}</span>
                                  <span className="text-gray-600">{gender.percentage}%</span>
                                </div>
                                <Progress value={gender.percentage} className="h-2" />
                              </div>
                            ))
                          ) : (
                            <div className="text-center text-muted-foreground">No gender data available</div>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </div>

                {/* Right Column - Geographic Distribution */}
                <Card>
                  <CardHeader>
                    <CardTitle>Geographic Distribution</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {demographicsData && demographicsData.top_locations && demographicsData.top_locations.length > 0 ? (
                        demographicsData.top_locations.slice(0, 6).map((location: any, index: number) => (
                          <div key={index} className="space-y-2">
                            <div className="flex justify-between text-sm">
                              <span className="font-medium">{location.location}</span>
                              <span className="text-gray-600">{location.percentage}%</span>
                            </div>
                            <Progress value={location.percentage} className="h-2" />
                          </div>
                        ))
                      ) : (
                        <div className="text-center text-muted-foreground">No location data available</div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Engagement Patterns - Full Width */}
              <Card>
                <CardHeader>
                  <CardTitle>Engagement Patterns</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid md:grid-cols-3 gap-6">
                    {/* Peak Hours */}
                    <div>
                      <h3 className="text-lg font-semibold mb-3">Peak Hours</h3>
                      <div className="flex flex-wrap gap-2">
                        {engagementPatterns?.peak_hours?.length > 0 ? (
                          engagementPatterns.peak_hours.map((hour: string, index: number) => (
                            <div key={index} className="px-3 py-1 bg-gray-100 rounded-full text-sm font-medium">
                              {hour}
                            </div>
                          ))
                        ) : (
                          <div className="text-gray-500 text-sm">No data available</div>
                        )}
                      </div>
                    </div>

                    {/* Active Days */}
                    <div>
                      <h3 className="text-lg font-semibold mb-3">Active Days</h3>
                      <div className="flex flex-wrap gap-2">
                        {engagementPatterns?.active_days?.length > 0 ? (
                          engagementPatterns.active_days.map((day: string, index: number) => (
                            <div key={index} className="px-3 py-1 bg-gray-100 rounded-full text-sm font-medium">
                              {day}
                            </div>
                          ))
                        ) : (
                          <div className="text-gray-500 text-sm">No data available</div>
                        )}
                      </div>
                    </div>

                    {/* Avg Engagement Rate */}
                    <div>
                      <h3 className="text-lg font-semibold mb-3">Avg. Engagement Rate</h3>
                      <div className="text-3xl font-bold text-green-600">
                        {engagementPatterns?.avg_engagement_rate ? 
                          `${engagementPatterns.avg_engagement_rate}%` : 
                          '0%'
                        }
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>


          </Tabs>
        </div>
      </div>
    </div>
  );
}