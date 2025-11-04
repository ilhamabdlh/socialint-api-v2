import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "./ui/card";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import { Textarea } from "./ui/textarea";
import { Alert, AlertDescription } from "./ui/alert";
import { Badge } from "./ui/badge";
import { adminBrandAPI, BrandSummaryPayload, BrandTimelinePayload, BrandTopicsPayload, BrandEmotionsPayload, BrandDemographicsPayload, BrandPerformancePayload, BrandEngagementPatternsPayload, BrandCompetitivePayload } from "../lib/api-client";
import { resultsAPI } from "../lib/api-client";
import { AnalysisFilters, FilterState } from "./AnalysisFilters";
import { 
  Save, 
  Loader2, 
  CheckCircle2, 
  AlertCircle,
  Plus,
  X,
  ArrowLeft
} from "lucide-react";
import { Brand } from "../lib/mock-data";

interface BrandCMSProps {
  brand: Brand;
  onBack: () => void;
}

export function BrandCMS({ brand, onBack }: BrandCMSProps) {
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState("summary");

  // Summary state
  const [summary, setSummary] = useState<BrandSummaryPayload>({
    total_posts: 0,
    total_engagement: 0,
    avg_engagement_per_post: 0,
    sentiment_distribution: { Positive: 0, Negative: 0, Neutral: 0 },
    sentiment_percentage: { Positive: 0, Negative: 0, Neutral: 0 },
    platform_breakdown: {},
    trending_topics: [],
  });

  // Timeline state
  const [timeline, setTimeline] = useState<BrandTimelinePayload>({ entries: [] });

  // Topics state
  const [topics, setTopics] = useState<BrandTopicsPayload>({ items: [] });

  // Emotions state
  const [emotions, setEmotions] = useState<BrandEmotionsPayload>({
    emotions: [
      { emotion: "joy", count: 0, percentage: 0 },
      { emotion: "sadness", count: 0, percentage: 0 },
      { emotion: "anger", count: 0, percentage: 0 },
      { emotion: "fear", count: 0, percentage: 0 },
      { emotion: "surprise", count: 0, percentage: 0 },
      { emotion: "disgust", count: 0, percentage: 0 },
      { emotion: "anticipation", count: 0, percentage: 0 },
      { emotion: "trust", count: 0, percentage: 0 },
      { emotion: "neutral", count: 0, percentage: 0 },
    ],
  });

  // Demographics state
  const [demographics, setDemographics] = useState<BrandDemographicsPayload>({
    total_analyzed: 0,
    age_groups: [],
    genders: [],
    top_locations: [],
  });

  // Performance state
  const [performance, setPerformance] = useState<BrandPerformancePayload>({
    total_posts: 0,
    total_engagement: 0,
    total_likes: 0,
    total_comments: 0,
    total_shares: 0,
    avg_engagement_per_post: 0,
    avg_likes_per_post: 0,
    avg_comments_per_post: 0,
    avg_shares_per_post: 0,
    engagement_rate: 0,
    estimated_reach: 0,
  });

  // Engagement Patterns state
  const [engagementPatterns, setEngagementPatterns] = useState<BrandEngagementPatternsPayload>({
    peak_hours: [],
    active_days: [],
    avg_engagement_rate: 0,
    total_posts: 0,
    patterns: [],
  });

  // Competitive state
  const [competitive, setCompetitive] = useState<BrandCompetitivePayload>({
    brand_metrics: {},
    industry_benchmarks: {},
    performance_vs_benchmark: {},
    market_position: "follower",
    recommendations: [],
  });

  // Get brand identifier (id or name)
  const getBrandIdentifier = () => {
    return brand.id || brand.name;
  };

  // Filter state - Initialize with default 30 days
  const [filters, setFilters] = useState<FilterState>(() => {
    const end = new Date();
    const start = new Date();
    start.setDate(start.getDate() - 30);
    
    const defaultFilters: FilterState = {
      dateRange: {
        start: start.toISOString().split('T')[0],
        end: end.toISOString().split('T')[0]
      },
      platforms: [],
      posts: [],
      keywords: [],
    };
    return defaultFilters;
  });

  // Load existing data when brand.id, brand.name, or filters change
  useEffect(() => {
    loadBrandData();
  }, [brand.id, brand.name, filters]);

  const loadBrandData = async () => {
    try {
      const brandIdentifier = getBrandIdentifier();

      // Build filter params
      const startDate = filters.dateRange.start || undefined;
      const endDate = filters.dateRange.end || undefined;
      const platforms = filters.platforms.length > 0 ? filters.platforms.join(',') : undefined;

      // Load summary with filters
      const summaryData = await resultsAPI.getBrandAnalysisSummary(
        brandIdentifier,
        startDate,
        endDate,
        platforms
      );
      if (summaryData) {
        setSummary({
          total_posts: summaryData.total_posts || 0,
          total_engagement: summaryData.total_engagement || 0,
          avg_engagement_per_post: summaryData.avg_engagement_per_post || 0,
          sentiment_distribution: summaryData.sentiment_distribution || { Positive: 0, Negative: 0, Neutral: 0 },
          sentiment_percentage: summaryData.sentiment_percentage || { Positive: 0, Negative: 0, Neutral: 0 },
          platform_breakdown: summaryData.platform_breakdown || {},
          trending_topics: summaryData.trending_topics || [],
        });
      }

      // Load timeline with filters
      const timelineData = await resultsAPI.getBrandSentimentTimeline(
        brandIdentifier,
        startDate,
        endDate,
        platforms
      );
      if (timelineData?.timeline) {
        setTimeline({
          entries: timelineData.timeline.map((entry: any) => ({
            date: entry.date,
            Positive: entry.Positive || entry.positive_count || 0,
            Neutral: entry.Neutral || entry.neutral_count || 0,
            Negative: entry.Negative || entry.negative_count || 0,
            total_posts: entry.total_posts || 0,
            total_likes: entry.total_likes || 0,
            total_comments: entry.total_comments || 0,
            total_shares: entry.total_shares || 0,
          })),
        });
      }

      // Load topics with filters
      const topicsData = await resultsAPI.getBrandTrendingTopics(
        brandIdentifier,
        startDate,
        endDate,
        platforms
      );
      if (topicsData?.topics) {
        setTopics({
          items: topicsData.topics.map((topic: any) => ({
            topic: topic.topic,
            count: topic.count || 0,
            sentiment: topic.sentiment || 0,
            engagement: topic.engagement || 0,
            positive: topic.positive || 0,
            negative: topic.negative || 0,
            neutral: topic.neutral || 0,
            platform: topic.platform || "all",
          })),
        });
      }

      // Load emotions with filters
      const emotionsData = await resultsAPI.getBrandEmotions(
        brandIdentifier,
        startDate,
        endDate,
        platforms
      );
      if (emotionsData?.emotions) {
        setEmotions({ emotions: emotionsData.emotions });
      }

      // Load demographics with filters
      const demographicsData = await resultsAPI.getBrandDemographics(
        brandIdentifier,
        startDate,
        endDate,
        platforms
      );
      if (demographicsData) {
        setDemographics({
          total_analyzed: demographicsData.total_analyzed || 0,
          age_groups: demographicsData.age_groups || [],
          genders: demographicsData.genders || [],
          top_locations: demographicsData.top_locations || [],
        });
      }

      // Load performance with filters
      const performanceData = await resultsAPI.getBrandPerformance(
        brandIdentifier,
        startDate,
        endDate,
        platforms
      );
      if (performanceData) {
        setPerformance({
          total_posts: performanceData.total_posts || 0,
          total_engagement: performanceData.total_engagement || 0,
          total_likes: performanceData.total_likes || 0,
          total_comments: performanceData.total_comments || 0,
          total_shares: performanceData.total_shares || 0,
          avg_engagement_per_post: performanceData.avg_engagement_per_post || 0,
          avg_likes_per_post: performanceData.avg_likes_per_post || 0,
          avg_comments_per_post: performanceData.avg_comments_per_post || 0,
          avg_shares_per_post: performanceData.avg_shares_per_post || 0,
          engagement_rate: performanceData.engagement_rate || 0,
          estimated_reach: performanceData.estimated_reach || 0,
        });
      }

      // Load competitive with filters
      const competitiveData = await resultsAPI.getBrandCompetitive(
        brandIdentifier,
        startDate,
        endDate,
        platforms
      );
      if (competitiveData) {
        setCompetitive({
          brand_metrics: competitiveData.brand_metrics || {},
          industry_benchmarks: competitiveData.industry_benchmarks || {},
          performance_vs_benchmark: competitiveData.performance_vs_benchmark || {},
          market_position: competitiveData.market_position || "follower",
          recommendations: competitiveData.recommendations || [],
        });
      }
    } catch (err: any) {
      console.error("Error loading brand data:", err);
      // Don't show error for first load, just use defaults
    }
  };

  const handleSave = async (tab: string) => {
    setLoading(true);
    setSuccess(null);
    setError(null);

    try {
      const brandIdentifier = getBrandIdentifier();
      let result;
      switch (tab) {
        case "summary":
          result = await adminBrandAPI.writeSummary(brandIdentifier, summary);
          break;
        case "timeline":
          result = await adminBrandAPI.upsertTimeline(brandIdentifier, timeline);
          break;
        case "topics":
          result = await adminBrandAPI.replaceTopics(brandIdentifier, topics);
          break;
        case "emotions":
          result = await adminBrandAPI.writeEmotions(brandIdentifier, emotions);
          break;
        case "demographics":
          result = await adminBrandAPI.writeDemographics(brandIdentifier, demographics);
          break;
        case "performance":
          result = await adminBrandAPI.writePerformance(brandIdentifier, performance);
          break;
        case "engagement-patterns":
          result = await adminBrandAPI.writeEngagementPatterns(brandIdentifier, engagementPatterns);
          break;
        case "competitive":
          result = await adminBrandAPI.writeCompetitive(brandIdentifier, competitive);
          break;
        default:
          throw new Error("Unknown tab");
      }

      setSuccess(`${tab} saved successfully!`);
      setTimeout(() => setSuccess(null), 3000);
    } catch (err: any) {
      setError(err.message || "Failed to save data");
      setTimeout(() => setError(null), 5000);
    } finally {
      setLoading(false);
    }
  };

  const addTimelineEntry = () => {
    setTimeline({
      entries: [
        ...timeline.entries,
        {
          date: new Date().toISOString().split('T')[0],
          Positive: 0,
          Neutral: 0,
          Negative: 0,
          total_posts: 0,
          total_likes: 0,
          total_comments: 0,
          total_shares: 0,
        },
      ],
    });
  };

  const removeTimelineEntry = (index: number) => {
    setTimeline({
      entries: timeline.entries.filter((_, i) => i !== index),
    });
  };

  const addTopic = () => {
    setTopics({
      items: [
        ...topics.items,
        {
          topic: "",
          count: 0,
          sentiment: 0,
          engagement: 0,
          positive: 0,
          negative: 0,
          neutral: 0,
          platform: "all",
        },
      ],
    });
  };

  const removeTopic = (index: number) => {
    setTopics({
      items: topics.items.filter((_, i) => i !== index),
    });
  };

  const addDemographicAgeGroup = () => {
    setDemographics({
      ...demographics,
      age_groups: [
        ...(demographics.age_groups || []),
        { age_group: "", count: 0, percentage: 0 },
      ],
    });
  };

  const addDemographicGender = () => {
    setDemographics({
      ...demographics,
      genders: [
        ...(demographics.genders || []),
        { gender: "", count: 0, percentage: 0 },
      ],
    });
  };

  const addDemographicLocation = () => {
    setDemographics({
      ...demographics,
      top_locations: [
        ...(demographics.top_locations || []),
        { location: "", count: 0, percentage: 0 },
      ],
    });
  };

  const addRecommendation = () => {
    setCompetitive({
      ...competitive,
      recommendations: [...(competitive.recommendations || []), ""],
    });
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <Button variant="ghost" onClick={onBack} className="mb-4">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back
          </Button>
          <h2 className="text-2xl font-bold">CMS - Brand: {brand.name}</h2>
          <p className="text-sm text-muted-foreground">Edit brand analysis data</p>
        </div>
      </div>

      {success && (
        <Alert className="border-green-200 bg-green-50">
          <CheckCircle2 className="h-4 w-4 text-green-600" />
          <AlertDescription className="text-green-800">{success}</AlertDescription>
        </Alert>
      )}

      {error && (
        <Alert className="border-red-200 bg-red-50">
          <AlertCircle className="h-4 w-4 text-red-600" />
          <AlertDescription className="text-red-800">{error}</AlertDescription>
        </Alert>
      )}

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <div className="grid lg:grid-cols-4 gap-6">
          {/* Filters Sidebar */}
          <div className="lg:col-span-1">
            <AnalysisFilters
              entity={brand}
              entityType="brand"
              filters={filters}
              onFiltersChange={setFilters}
            />
          </div>

          {/* Content */}
          <div className="lg:col-span-3 space-y-4">
            <TabsList className="grid grid-cols-4 lg:grid-cols-8 w-full">
              <TabsTrigger value="summary">Summary</TabsTrigger>
              <TabsTrigger value="timeline">Timeline</TabsTrigger>
              <TabsTrigger value="topics">Topics</TabsTrigger>
              <TabsTrigger value="emotions">Emotions</TabsTrigger>
              <TabsTrigger value="demographics">Demographics</TabsTrigger>
              <TabsTrigger value="performance">Performance</TabsTrigger>
              <TabsTrigger value="engagement-patterns">Engagement</TabsTrigger>
              <TabsTrigger value="competitive">Competitive</TabsTrigger>
            </TabsList>

        {/* Summary Tab */}
        <TabsContent value="summary" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Brand Summary</CardTitle>
              <CardDescription>Edit brand summary metrics</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Total Posts</Label>
                  <Input
                    type="number"
                    value={summary.total_posts || 0}
                    onChange={(e) => setSummary({ ...summary, total_posts: parseInt(e.target.value) || 0 })}
                  />
                </div>
                <div>
                  <Label>Total Engagement</Label>
                  <Input
                    type="number"
                    value={summary.total_engagement || 0}
                    onChange={(e) => setSummary({ ...summary, total_engagement: parseInt(e.target.value) || 0 })}
                  />
                </div>
                <div>
                  <Label>Avg Engagement Per Post</Label>
                  <Input
                    type="number"
                    step="0.01"
                    value={summary.avg_engagement_per_post || 0}
                    onChange={(e) => setSummary({ ...summary, avg_engagement_per_post: parseFloat(e.target.value) || 0 })}
                  />
                </div>
              </div>

              <div>
                <Label>Sentiment Distribution</Label>
                <div className="grid grid-cols-3 gap-4 mt-2">
                  <div>
                    <Label className="text-xs">Positive</Label>
                    <Input
                      type="number"
                      value={summary.sentiment_distribution?.Positive || 0}
                      onChange={(e) =>
                        setSummary({
                          ...summary,
                          sentiment_distribution: {
                            ...summary.sentiment_distribution,
                            Positive: parseInt(e.target.value) || 0,
                          },
                        })
                      }
                    />
                  </div>
                  <div>
                    <Label className="text-xs">Neutral</Label>
                    <Input
                      type="number"
                      value={summary.sentiment_distribution?.Neutral || 0}
                      onChange={(e) =>
                        setSummary({
                          ...summary,
                          sentiment_distribution: {
                            ...summary.sentiment_distribution,
                            Neutral: parseInt(e.target.value) || 0,
                          },
                        })
                      }
                    />
                  </div>
                  <div>
                    <Label className="text-xs">Negative</Label>
                    <Input
                      type="number"
                      value={summary.sentiment_distribution?.Negative || 0}
                      onChange={(e) =>
                        setSummary({
                          ...summary,
                          sentiment_distribution: {
                            ...summary.sentiment_distribution,
                            Negative: parseInt(e.target.value) || 0,
                          },
                        })
                      }
                    />
                  </div>
                </div>
              </div>

              <div>
                <Label>Sentiment Percentage</Label>
                <div className="grid grid-cols-3 gap-4 mt-2">
                  <div>
                    <Label className="text-xs">Positive %</Label>
                    <Input
                      type="number"
                      step="0.1"
                      value={summary.sentiment_percentage?.Positive || 0}
                      onChange={(e) =>
                        setSummary({
                          ...summary,
                          sentiment_percentage: {
                            ...summary.sentiment_percentage,
                            Positive: parseFloat(e.target.value) || 0,
                          },
                        })
                      }
                    />
                  </div>
                  <div>
                    <Label className="text-xs">Neutral %</Label>
                    <Input
                      type="number"
                      step="0.1"
                      value={summary.sentiment_percentage?.Neutral || 0}
                      onChange={(e) =>
                        setSummary({
                          ...summary,
                          sentiment_percentage: {
                            ...summary.sentiment_percentage,
                            Neutral: parseFloat(e.target.value) || 0,
                          },
                        })
                      }
                    />
                  </div>
                  <div>
                    <Label className="text-xs">Negative %</Label>
                    <Input
                      type="number"
                      step="0.1"
                      value={summary.sentiment_percentage?.Negative || 0}
                      onChange={(e) =>
                        setSummary({
                          ...summary,
                          sentiment_percentage: {
                            ...summary.sentiment_percentage,
                            Negative: parseFloat(e.target.value) || 0,
                          },
                        })
                      }
                    />
                  </div>
                </div>
              </div>

              <Button
                onClick={() => handleSave("summary")}
                disabled={loading}
                className="w-full"
              >
                {loading ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Saving...
                  </>
                ) : (
                  <>
                    <Save className="h-4 w-4 mr-2" />
                    Save Summary
                  </>
                )}
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Timeline Tab */}
        <TabsContent value="timeline" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Sentiment Timeline</CardTitle>
              <CardDescription>Edit sentiment timeline entries</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Button onClick={addTimelineEntry} variant="outline" className="w-full">
                <Plus className="h-4 w-4 mr-2" />
                Add Timeline Entry
              </Button>

              {timeline.entries.map((entry, index) => (
                <Card key={index} className="p-4">
                  <div className="flex items-start justify-between mb-4">
                    <h4 className="font-semibold">Entry {index + 1}</h4>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => removeTimelineEntry(index)}
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label>Date</Label>
                      <Input
                        type="date"
                        value={entry.date}
                        onChange={(e) => {
                          const newEntries = [...timeline.entries];
                          newEntries[index].date = e.target.value;
                          setTimeline({ entries: newEntries });
                        }}
                      />
                    </div>
                    <div>
                      <Label>Total Posts</Label>
                      <Input
                        type="number"
                        value={entry.total_posts || 0}
                        onChange={(e) => {
                          const newEntries = [...timeline.entries];
                          newEntries[index].total_posts = parseInt(e.target.value) || 0;
                          setTimeline({ entries: newEntries });
                        }}
                      />
                    </div>
                    <div>
                      <Label>Positive</Label>
                      <Input
                        type="number"
                        value={entry.Positive || 0}
                        onChange={(e) => {
                          const newEntries = [...timeline.entries];
                          newEntries[index].Positive = parseInt(e.target.value) || 0;
                          setTimeline({ entries: newEntries });
                        }}
                      />
                    </div>
                    <div>
                      <Label>Neutral</Label>
                      <Input
                        type="number"
                        value={entry.Neutral || 0}
                        onChange={(e) => {
                          const newEntries = [...timeline.entries];
                          newEntries[index].Neutral = parseInt(e.target.value) || 0;
                          setTimeline({ entries: newEntries });
                        }}
                      />
                    </div>
                    <div>
                      <Label>Negative</Label>
                      <Input
                        type="number"
                        value={entry.Negative || 0}
                        onChange={(e) => {
                          const newEntries = [...timeline.entries];
                          newEntries[index].Negative = parseInt(e.target.value) || 0;
                          setTimeline({ entries: newEntries });
                        }}
                      />
                    </div>
                  </div>
                </Card>
              ))}

              <Button
                onClick={() => handleSave("timeline")}
                disabled={loading}
                className="w-full"
              >
                {loading ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Saving...
                  </>
                ) : (
                  <>
                    <Save className="h-4 w-4 mr-2" />
                    Save Timeline
                  </>
                )}
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Topics Tab */}
        <TabsContent value="topics" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Trending Topics</CardTitle>
              <CardDescription>Edit trending topics</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Button onClick={addTopic} variant="outline" className="w-full">
                <Plus className="h-4 w-4 mr-2" />
                Add Topic
              </Button>

              {topics.items.map((item, index) => (
                <Card key={index} className="p-4">
                  <div className="flex items-start justify-between mb-4">
                    <h4 className="font-semibold">Topic {index + 1}</h4>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => removeTopic(index)}
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label>Topic</Label>
                      <Input
                        value={item.topic}
                        onChange={(e) => {
                          const newItems = [...topics.items];
                          newItems[index].topic = e.target.value;
                          setTopics({ items: newItems });
                        }}
                      />
                    </div>
                    <div>
                      <Label>Count</Label>
                      <Input
                        type="number"
                        value={item.count || 0}
                        onChange={(e) => {
                          const newItems = [...topics.items];
                          newItems[index].count = parseInt(e.target.value) || 0;
                          setTopics({ items: newItems });
                        }}
                      />
                    </div>
                    <div>
                      <Label>Sentiment</Label>
                      <Input
                        type="number"
                        step="0.01"
                        value={item.sentiment || 0}
                        onChange={(e) => {
                          const newItems = [...topics.items];
                          newItems[index].sentiment = parseFloat(e.target.value) || 0;
                          setTopics({ items: newItems });
                        }}
                      />
                    </div>
                    <div>
                      <Label>Engagement</Label>
                      <Input
                        type="number"
                        value={item.engagement || 0}
                        onChange={(e) => {
                          const newItems = [...topics.items];
                          newItems[index].engagement = parseInt(e.target.value) || 0;
                          setTopics({ items: newItems });
                        }}
                      />
                    </div>
                  </div>
                </Card>
              ))}

              <Button
                onClick={() => handleSave("topics")}
                disabled={loading}
                className="w-full"
              >
                {loading ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Saving...
                  </>
                ) : (
                  <>
                    <Save className="h-4 w-4 mr-2" />
                    Save Topics
                  </>
                )}
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Emotions Tab */}
        <TabsContent value="emotions" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Emotions Analysis</CardTitle>
              <CardDescription>Edit emotion distribution</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {emotions.emotions.map((emotion, index) => (
                <div key={emotion.emotion} className="grid grid-cols-3 gap-4 items-end">
                  <div>
                    <Label>{emotion.emotion.charAt(0).toUpperCase() + emotion.emotion.slice(1)}</Label>
                    <Input value={emotion.emotion} disabled />
                  </div>
                  <div>
                    <Label>Count</Label>
                    <Input
                      type="number"
                      value={emotion.count || 0}
                      onChange={(e) => {
                        const newEmotions = [...emotions.emotions];
                        newEmotions[index].count = parseInt(e.target.value) || 0;
                        setEmotions({ emotions: newEmotions });
                      }}
                    />
                  </div>
                  <div>
                    <Label>Percentage</Label>
                    <Input
                      type="number"
                      step="0.1"
                      value={emotion.percentage || 0}
                      onChange={(e) => {
                        const newEmotions = [...emotions.emotions];
                        newEmotions[index].percentage = parseFloat(e.target.value) || 0;
                        setEmotions({ emotions: newEmotions });
                      }}
                    />
                  </div>
                </div>
              ))}

              <Button
                onClick={() => handleSave("emotions")}
                disabled={loading}
                className="w-full"
              >
                {loading ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Saving...
                  </>
                ) : (
                  <>
                    <Save className="h-4 w-4 mr-2" />
                    Save Emotions
                  </>
                )}
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Demographics Tab */}
        <TabsContent value="demographics" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Demographics Analysis</CardTitle>
              <CardDescription>Edit audience demographics</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label>Total Analyzed</Label>
                <Input
                  type="number"
                  value={demographics.total_analyzed || 0}
                  onChange={(e) =>
                    setDemographics({
                      ...demographics,
                      total_analyzed: parseInt(e.target.value) || 0,
                    })
                  }
                />
              </div>

              <div>
                <div className="flex items-center justify-between mb-2">
                  <Label>Age Groups</Label>
                  <Button onClick={addDemographicAgeGroup} variant="outline" size="sm">
                    <Plus className="h-4 w-4 mr-1" />
                    Add
                  </Button>
                </div>
                {demographics.age_groups?.map((ageGroup, index) => (
                  <Card key={index} className="p-3 mb-2">
                    <div className="grid grid-cols-3 gap-2">
                      <Input
                        placeholder="Age Group"
                        value={ageGroup.age_group}
                        onChange={(e) => {
                          const newAgeGroups = [...(demographics.age_groups || [])];
                          newAgeGroups[index].age_group = e.target.value;
                          setDemographics({ ...demographics, age_groups: newAgeGroups });
                        }}
                      />
                      <Input
                        type="number"
                        placeholder="Count"
                        value={ageGroup.count || 0}
                        onChange={(e) => {
                          const newAgeGroups = [...(demographics.age_groups || [])];
                          newAgeGroups[index].count = parseInt(e.target.value) || 0;
                          setDemographics({ ...demographics, age_groups: newAgeGroups });
                        }}
                      />
                      <div className="flex gap-2">
                        <Input
                          type="number"
                          step="0.1"
                          placeholder="%"
                          value={ageGroup.percentage || 0}
                          onChange={(e) => {
                            const newAgeGroups = [...(demographics.age_groups || [])];
                            newAgeGroups[index].percentage = parseFloat(e.target.value) || 0;
                            setDemographics({ ...demographics, age_groups: newAgeGroups });
                          }}
                        />
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            const newAgeGroups = (demographics.age_groups || []).filter((_, i) => i !== index);
                            setDemographics({ ...demographics, age_groups: newAgeGroups });
                          }}
                        >
                          <X className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  </Card>
                ))}
              </div>

              <div>
                <div className="flex items-center justify-between mb-2">
                  <Label>Genders</Label>
                  <Button onClick={addDemographicGender} variant="outline" size="sm">
                    <Plus className="h-4 w-4 mr-1" />
                    Add
                  </Button>
                </div>
                {demographics.genders?.map((gender, index) => (
                  <Card key={index} className="p-3 mb-2">
                    <div className="grid grid-cols-3 gap-2">
                      <Input
                        placeholder="Gender"
                        value={gender.gender}
                        onChange={(e) => {
                          const newGenders = [...(demographics.genders || [])];
                          newGenders[index].gender = e.target.value;
                          setDemographics({ ...demographics, genders: newGenders });
                        }}
                      />
                      <Input
                        type="number"
                        placeholder="Count"
                        value={gender.count || 0}
                        onChange={(e) => {
                          const newGenders = [...(demographics.genders || [])];
                          newGenders[index].count = parseInt(e.target.value) || 0;
                          setDemographics({ ...demographics, genders: newGenders });
                        }}
                      />
                      <div className="flex gap-2">
                        <Input
                          type="number"
                          step="0.1"
                          placeholder="%"
                          value={gender.percentage || 0}
                          onChange={(e) => {
                            const newGenders = [...(demographics.genders || [])];
                            newGenders[index].percentage = parseFloat(e.target.value) || 0;
                            setDemographics({ ...demographics, genders: newGenders });
                          }}
                        />
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            const newGenders = (demographics.genders || []).filter((_, i) => i !== index);
                            setDemographics({ ...demographics, genders: newGenders });
                          }}
                        >
                          <X className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  </Card>
                ))}
              </div>

              <div>
                <div className="flex items-center justify-between mb-2">
                  <Label>Top Locations</Label>
                  <Button onClick={addDemographicLocation} variant="outline" size="sm">
                    <Plus className="h-4 w-4 mr-1" />
                    Add
                  </Button>
                </div>
                {demographics.top_locations?.map((location, index) => (
                  <Card key={index} className="p-3 mb-2">
                    <div className="grid grid-cols-3 gap-2">
                      <Input
                        placeholder="Location"
                        value={location.location}
                        onChange={(e) => {
                          const newLocations = [...(demographics.top_locations || [])];
                          newLocations[index].location = e.target.value;
                          setDemographics({ ...demographics, top_locations: newLocations });
                        }}
                      />
                      <Input
                        type="number"
                        placeholder="Count"
                        value={location.count || 0}
                        onChange={(e) => {
                          const newLocations = [...(demographics.top_locations || [])];
                          newLocations[index].count = parseInt(e.target.value) || 0;
                          setDemographics({ ...demographics, top_locations: newLocations });
                        }}
                      />
                      <div className="flex gap-2">
                        <Input
                          type="number"
                          step="0.1"
                          placeholder="%"
                          value={location.percentage || 0}
                          onChange={(e) => {
                            const newLocations = [...(demographics.top_locations || [])];
                            newLocations[index].percentage = parseFloat(e.target.value) || 0;
                            setDemographics({ ...demographics, top_locations: newLocations });
                          }}
                        />
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            const newLocations = (demographics.top_locations || []).filter((_, i) => i !== index);
                            setDemographics({ ...demographics, top_locations: newLocations });
                          }}
                        >
                          <X className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  </Card>
                ))}
              </div>

              <Button
                onClick={() => handleSave("demographics")}
                disabled={loading}
                className="w-full"
              >
                {loading ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Saving...
                  </>
                ) : (
                  <>
                    <Save className="h-4 w-4 mr-2" />
                    Save Demographics
                  </>
                )}
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Performance Tab */}
        <TabsContent value="performance" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Performance Metrics</CardTitle>
              <CardDescription>Edit performance metrics</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Total Posts</Label>
                  <Input
                    type="number"
                    value={performance.total_posts || 0}
                    onChange={(e) =>
                      setPerformance({
                        ...performance,
                        total_posts: parseInt(e.target.value) || 0,
                      })
                    }
                  />
                </div>
                <div>
                  <Label>Total Engagement</Label>
                  <Input
                    type="number"
                    value={performance.total_engagement || 0}
                    onChange={(e) =>
                      setPerformance({
                        ...performance,
                        total_engagement: parseInt(e.target.value) || 0,
                      })
                    }
                  />
                </div>
                <div>
                  <Label>Total Likes</Label>
                  <Input
                    type="number"
                    value={performance.total_likes || 0}
                    onChange={(e) =>
                      setPerformance({
                        ...performance,
                        total_likes: parseInt(e.target.value) || 0,
                      })
                    }
                  />
                </div>
                <div>
                  <Label>Total Comments</Label>
                  <Input
                    type="number"
                    value={performance.total_comments || 0}
                    onChange={(e) =>
                      setPerformance({
                        ...performance,
                        total_comments: parseInt(e.target.value) || 0,
                      })
                    }
                  />
                </div>
                <div>
                  <Label>Total Shares</Label>
                  <Input
                    type="number"
                    value={performance.total_shares || 0}
                    onChange={(e) =>
                      setPerformance({
                        ...performance,
                        total_shares: parseInt(e.target.value) || 0,
                      })
                    }
                  />
                </div>
                <div>
                  <Label>Engagement Rate</Label>
                  <Input
                    type="number"
                    step="0.01"
                    value={performance.engagement_rate || 0}
                    onChange={(e) =>
                      setPerformance({
                        ...performance,
                        engagement_rate: parseFloat(e.target.value) || 0,
                      })
                    }
                  />
                </div>
                <div>
                  <Label>Estimated Reach</Label>
                  <Input
                    type="number"
                    value={performance.estimated_reach || 0}
                    onChange={(e) =>
                      setPerformance({
                        ...performance,
                        estimated_reach: parseInt(e.target.value) || 0,
                      })
                    }
                  />
                </div>
              </div>

              <Button
                onClick={() => handleSave("performance")}
                disabled={loading}
                className="w-full"
              >
                {loading ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Saving...
                  </>
                ) : (
                  <>
                    <Save className="h-4 w-4 mr-2" />
                    Save Performance
                  </>
                )}
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Engagement Patterns Tab */}
        <TabsContent value="engagement-patterns" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Engagement Patterns</CardTitle>
              <CardDescription>Edit engagement patterns</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Total Posts</Label>
                  <Input
                    type="number"
                    value={engagementPatterns.total_posts || 0}
                    onChange={(e) =>
                      setEngagementPatterns({
                        ...engagementPatterns,
                        total_posts: parseInt(e.target.value) || 0,
                      })
                    }
                  />
                </div>
                <div>
                  <Label>Avg Engagement Rate</Label>
                  <Input
                    type="number"
                    step="0.01"
                    value={engagementPatterns.avg_engagement_rate || 0}
                    onChange={(e) =>
                      setEngagementPatterns({
                        ...engagementPatterns,
                        avg_engagement_rate: parseFloat(e.target.value) || 0,
                      })
                    }
                  />
                </div>
              </div>

              <div>
                <Label>Peak Hours (comma-separated)</Label>
                <Input
                  placeholder="09:00, 14:00, 18:00"
                  value={(engagementPatterns.peak_hours || []).join(", ")}
                  onChange={(e) =>
                    setEngagementPatterns({
                      ...engagementPatterns,
                      peak_hours: e.target.value.split(",").map((h) => h.trim()),
                    })
                  }
                />
              </div>

              <div>
                <Label>Active Days (comma-separated)</Label>
                <Input
                  placeholder="Monday, Tuesday, Wednesday"
                  value={(engagementPatterns.active_days || []).join(", ")}
                  onChange={(e) =>
                    setEngagementPatterns({
                      ...engagementPatterns,
                      active_days: e.target.value.split(",").map((d) => d.trim()),
                    })
                  }
                />
              </div>

              <Button
                onClick={() => handleSave("engagement-patterns")}
                disabled={loading}
                className="w-full"
              >
                {loading ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Saving...
                  </>
                ) : (
                  <>
                    <Save className="h-4 w-4 mr-2" />
                    Save Engagement Patterns
                  </>
                )}
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Competitive Tab */}
        <TabsContent value="competitive" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Competitive Analysis</CardTitle>
              <CardDescription>Edit competitive analysis data</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label>Market Position</Label>
                <Input
                  value={competitive.market_position || "follower"}
                  onChange={(e) =>
                    setCompetitive({
                      ...competitive,
                      market_position: e.target.value,
                    })
                  }
                />
              </div>

              <div>
                <div className="flex items-center justify-between mb-2">
                  <Label>Recommendations</Label>
                  <Button onClick={addRecommendation} variant="outline" size="sm">
                    <Plus className="h-4 w-4 mr-1" />
                    Add
                  </Button>
                </div>
                {(competitive.recommendations || []).map((rec, index) => (
                  <div key={index} className="flex gap-2 mb-2">
                    <Textarea
                      placeholder="Recommendation"
                      value={rec}
                      onChange={(e) => {
                        const newRecs = [...(competitive.recommendations || [])];
                        newRecs[index] = e.target.value;
                        setCompetitive({ ...competitive, recommendations: newRecs });
                      }}
                    />
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        const newRecs = (competitive.recommendations || []).filter((_, i) => i !== index);
                        setCompetitive({ ...competitive, recommendations: newRecs });
                      }}
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                ))}
              </div>

              <Button
                onClick={() => handleSave("competitive")}
                disabled={loading}
                className="w-full"
              >
                {loading ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Saving...
                  </>
                ) : (
                  <>
                    <Save className="h-4 w-4 mr-2" />
                    Save Competitive Analysis
                  </>
                )}
              </Button>
            </CardContent>
          </Card>
        </TabsContent>
          </div>
        </div>
      </Tabs>
    </div>
  );
}
