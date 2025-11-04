import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "./ui/card";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import { Textarea } from "./ui/textarea";
import { Alert, AlertDescription } from "./ui/alert";
import { adminCampaignAPI, CampaignSummaryPayload, CampaignTimelinePayload, CampaignTopicsPayload, CampaignEmotionsPayload, CampaignAudiencePayload, CampaignPerformancePayload } from "../lib/api-client";
import { campaignAPI } from "../lib/api-client";
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
import { Campaign } from "../lib/mock-data";

interface CampaignCMSProps {
  campaign: Campaign;
  onBack: () => void;
}

export function CampaignCMS({ campaign, onBack }: CampaignCMSProps) {
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState("summary");

  // Summary state (payload + UI-only fields for alignment with Analysis cards)
  const [summary, setSummary] = useState<CampaignSummaryPayload & {
    total_engagement?: number; // UI only
    positive_sentiment_pct?: number; // UI only (0-100)
  }>({
    total_mentions: 0,
    overall_sentiment: 0,
    engagement_rate: 0,
    reach: 0,
    sentiment_trend: 0,
    mentions_trend: 0,
    engagement_trend: 0,
    total_engagement: 0,
    positive_sentiment_pct: 0,
  });

  // Timeline state
  const [timeline, setTimeline] = useState<CampaignTimelinePayload>({ entries: [] });

  // Topics state
  const [topics, setTopics] = useState<CampaignTopicsPayload>({ items: [] });

  // Emotions state
  const [emotions, setEmotions] = useState<CampaignEmotionsPayload>({
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

  // Audience state
  const [audience, setAudience] = useState<CampaignAudiencePayload>({
    demographics: [],
  });

  // Performance state
  const [performance, setPerformance] = useState<CampaignPerformancePayload>({
    overall_metrics: {},
    platform_breakdown: [],
    conversion_funnel: {},
  });

  // Filter state - Initialize with campaign date range
  const [filters, setFilters] = useState<FilterState>(() => {
    const defaultFilters: FilterState = {
      dateRange: {
        start: campaign.start_date ? new Date(campaign.start_date).toISOString().split('T')[0] : '',
        end: campaign.end_date ? new Date(campaign.end_date).toISOString().split('T')[0] : ''
      },
      platforms: [],
      posts: [],
    };
    return defaultFilters;
  });

  // Load existing data when campaign.id or filters change
  useEffect(() => {
    loadCampaignData();
  }, [campaign.id, filters]);

  const loadCampaignData = async () => {
    try {
      const campaignId = campaign.id;

      // Build filter params
      const startDate = filters.dateRange.start || undefined;
      const endDate = filters.dateRange.end || undefined;
      const platforms = filters.platforms.length > 0 ? filters.platforms.join(',') : undefined;
      const postUrls = filters.posts.length > 0 ? filters.posts.join(',') : undefined;

      // Load summary from Results (same source as Analysis) with filters
      const summaryData = await campaignAPI.getAnalysisSummary(
        campaignId,
        startDate,
        endDate,
        platforms,
        postUrls
      );

      // Load timeline with filters
      const timelineData = await campaignAPI.getSentimentTimeline(
        campaignId,
        startDate,
        endDate,
        platforms,
        postUrls
      );
      if (timelineData?.timeline) {
        setTimeline({
          entries: timelineData.timeline.map((entry: any) => ({
            metric_date: entry.metric_date || entry.date,
            sentiment_score: entry.sentiment_score ?? 0,
            total_mentions: entry.total_mentions ?? entry.total_posts ?? 0,
            positive_count: entry.positive_count ?? entry.Positive ?? 0,
            negative_count: entry.negative_count ?? entry.Negative ?? 0,
            neutral_count: entry.neutral_count ?? entry.Neutral ?? 0,
            total_likes: entry.total_likes ?? 0,
            total_comments: entry.total_comments ?? 0,
            total_shares: entry.total_shares ?? 0,
            engagement_rate: entry.engagement_rate ?? 0,
            reach: entry.engagement_rate ?? 0,
            impressions: entry.impressions ?? 0,
            platform_distribution: entry.platform_distribution || {},
            topic_distribution: entry.topic_distribution || {},
            platform_sentiment: entry.platform_sentiment || {},
          })),
        });
      }

      // Load topics with filters
      const topicsData = await campaignAPI.getTrendingTopics(
        campaignId,
        startDate,
        endDate,
        platforms,
        postUrls
      );
      if (topicsData?.topics) {
        setTopics({
          items: topicsData.topics.map((t: any) => ({
            topic: t.topic,
            count: t.count || 0,
            sentiment: t.sentiment || 0,
            engagement: t.engagement || 0,
            likes: t.likes || 0,
            comments: t.comments || 0,
            shares: t.shares || 0,
            positive: t.positive || 0,
            negative: t.negative || 0,
            neutral: t.neutral || 0,
          })),
        });
      }

      // Load emotions with filters
      const emotionsData = await campaignAPI.getEmotions(
        campaignId,
        startDate,
        endDate,
        platforms,
        postUrls
      );
      if (emotionsData?.emotions) {
        setEmotions({ emotions: emotionsData.emotions });
      }

      // Load audience with filters
      const audienceData = await campaignAPI.getAudience(
        campaignId,
        startDate,
        endDate,
        platforms,
        postUrls
      );
      if (audienceData?.demographics) {
        setAudience({ demographics: audienceData.demographics });
      }

      // Load performance with filters
      const performanceData = await campaignAPI.getPerformance(
        campaignId,
        startDate,
        endDate,
        platforms,
        postUrls
      );
      if (performanceData) {
        setPerformance({
          overall_metrics: performanceData.overall_metrics || {},
          platform_breakdown: performanceData.platform_breakdown || [],
          conversion_funnel: performanceData.conversion_funnel || {},
        });
        // Enrich summary UI fields from Results so it matches Analysis cards
        const totalViews = (performanceData.overall_metrics && (performanceData.overall_metrics.total_views || performanceData.overall_metrics.views)) || 0;
        const totalEngagement = typeof performanceData.total_engagement === 'number'
          ? performanceData.total_engagement
          : (performanceData.overall_metrics?.total_engagement || 0);
        
        // Calculate positive_sentiment_pct from sentiment_percentage or overall_sentiment
        let positivePct = summaryData?.sentiment_percentage?.Positive;
        if (typeof positivePct !== 'number') {
          // Fallback: calculate from overall_sentiment if available
          const overallSent = summaryData?.overall_sentiment ?? timelineData?.sentiment_metrics?.overall_score ?? 0;
          // Convert overall_sentiment (-1..1) back to Positive Sentiment % (0-100)
          positivePct = Math.max(0, Math.min(100, (overallSent + 1) * 50));
        }
        
        setSummary((prev) => ({
          ...prev,
          // Align with Analysis cards - these are what user sees/edits
          total_mentions: (summaryData?.total_posts || prev.total_mentions || 0),
          total_engagement: totalEngagement || (summaryData?.total_engagement || 0),
          reach: totalViews || prev.reach || 0,
          positive_sentiment_pct: typeof positivePct === 'number' ? positivePct : 0,
          // Keep payload fields for backend
          engagement_rate: (summaryData?.engagement_rate || prev.engagement_rate || 0),
          overall_sentiment: (summaryData?.overall_sentiment ?? timelineData?.sentiment_metrics?.overall_score ?? prev.overall_sentiment ?? 0),
        }));
      }
    } catch (err: any) {
      console.error("Error loading campaign data:", err);
    }
  };

  const handleSave = async (tab: string) => {
    setLoading(true);
    setSuccess(null);
    setError(null);

    try {
      let result;
      switch (tab) {
        case "summary":
          {
            // Map UI fields to backend payload:
            // - Convert Positive Sentiment % (0-100) -> overall_sentiment (-1..1)
            // Kirim RAW sesuai input CMS; backend yang menghitung turunan
            const payload: any = {
              total_mentions: summary.total_mentions || 0,
              positive_sentiment_pct: summary.positive_sentiment_pct ?? 0,
              total_engagement: summary.total_engagement || 0,
              reach: summary.reach || 0,
              sentiment_trend: summary.sentiment_trend || 0,
              mentions_trend: summary.mentions_trend || 0,
              engagement_trend: summary.engagement_trend || 0,
            };
            result = await adminCampaignAPI.writeSummary(campaign.id, payload);
            
            // 🔧 Auto-reload data after successful save to reflect changes immediately
            await loadCampaignData();
          }
          break;
        case "timeline":
          result = await adminCampaignAPI.upsertTimeline(campaign.id, timeline);
          // Auto-reload data after save
          await loadCampaignData();
          break;
        case "topics":
          result = await adminCampaignAPI.replaceTopics(campaign.id, topics);
          // Auto-reload data after save
          await loadCampaignData();
          break;
        case "emotions":
          result = await adminCampaignAPI.writeEmotions(campaign.id, emotions);
          // Auto-reload data after save
          await loadCampaignData();
          break;
        case "audience":
          result = await adminCampaignAPI.writeAudience(campaign.id, audience);
          // Auto-reload data after save
          await loadCampaignData();
          break;
        case "performance":
          result = await adminCampaignAPI.writePerformance(campaign.id, performance);
          // Auto-reload data after save
          await loadCampaignData();
          break;
        default:
          throw new Error("Unknown tab");
      }

      setSuccess(`${tab} saved successfully! Data refreshed automatically.`);
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
          metric_date: new Date().toISOString().split('T')[0],
          sentiment_score: 0,
          total_mentions: 0,
          positive_count: 0,
          negative_count: 0,
          neutral_count: 0,
          total_likes: 0,
          total_comments: 0,
          total_shares: 0,
          engagement_rate: 0,
          reach: 0,
          impressions: 0,
          platform_distribution: {},
          topic_distribution: {},
          platform_sentiment: {},
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
          likes: 0,
          comments: 0,
          shares: 0,
          positive: 0,
          negative: 0,
          neutral: 0,
        },
      ],
    });
  };

  const removeTopic = (index: number) => {
    setTopics({
      items: topics.items.filter((_, i) => i !== index),
    });
  };

  const addAudienceEntry = () => {
    setAudience({
      demographics: [
        ...(audience.demographics || []),
        {
          age_group: "",
          gender: "",
          location: "",
          count: 0,
          percentage: 0,
        },
      ],
    });
  };

  const removeAudienceEntry = (index: number) => {
    setAudience({
      demographics: (audience.demographics || []).filter((_, i) => i !== index),
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
          <h2 className="text-2xl font-bold">CMS - Campaign: {campaign.name || (campaign as any).campaign_name}</h2>
          <p className="text-sm text-muted-foreground">Edit campaign analysis data</p>
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
              entity={campaign}
              entityType="campaign"
              filters={filters}
              onFiltersChange={setFilters}
            />
          </div>

          {/* Content */}
          <div className="lg:col-span-3 space-y-4">
            <TabsList className="grid grid-cols-3 lg:grid-cols-6 w-full">
              <TabsTrigger value="summary">Summary</TabsTrigger>
              <TabsTrigger value="timeline">Timeline</TabsTrigger>
              <TabsTrigger value="topics">Topics</TabsTrigger>
              <TabsTrigger value="emotions">Emotions</TabsTrigger>
              <TabsTrigger value="audience">Audience</TabsTrigger>
              <TabsTrigger value="performance">Performance</TabsTrigger>
            </TabsList>

        {/* Summary Tab */}
        <TabsContent value="summary" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Campaign Summary</CardTitle>
              <CardDescription>Edit campaign summary metrics</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Number of Talks</Label>
                  <Input
                    type="number"
                    value={summary.total_mentions || 0}
                    onChange={(e) => setSummary({ ...summary, total_mentions: parseInt(e.target.value) || 0 })}
                    placeholder="Total posts/mentions"
                  />
                  <p className="text-xs text-muted-foreground mt-1">Same as "Number of Talks" in Analysis</p>
                </div>
                <div>
                  <Label>Positive Sentiment %</Label>
                  <Input
                    type="number"
                    min="0"
                    max="100"
                    step="0.1"
                    value={summary.positive_sentiment_pct ?? 0}
                    onChange={(e) => {
                      const val = parseFloat(e.target.value) || 0;
                      setSummary({ 
                        ...summary, 
                        positive_sentiment_pct: Math.max(0, Math.min(100, val)),
                        // Auto-convert to overall_sentiment for backend
                        overall_sentiment: Math.max(-1, Math.min(1, (val / 50) - 1))
                      });
                    }}
                    placeholder="0-100"
                  />
                  <p className="text-xs text-muted-foreground mt-1">Same as "Positive Sentiment %" in Analysis</p>
                </div>
                <div>
                  <Label>Number of Engagement</Label>
                  <Input
                    type="number"
                    value={summary.total_engagement || 0}
                    onChange={(e) => {
                      const val = parseInt(e.target.value) || 0;
                      setSummary({ 
                        ...summary, 
                        total_engagement: val,
                        // Auto-calculate engagement_rate from total_engagement / reach
                        engagement_rate: summary.reach ? ((val / Math.max(1, summary.reach)) * 100) : summary.engagement_rate || 0
                      });
                    }}
                    placeholder="Total engagement count"
                  />
                  <p className="text-xs text-muted-foreground mt-1">Same as "Number of Engagement" in Analysis</p>
                </div>
                <div>
                  <Label>Number of Reach</Label>
                  <Input
                    type="number"
                    value={summary.reach || 0}
                    onChange={(e) => {
                      const val = parseInt(e.target.value) || 0;
                      setSummary({ 
                        ...summary, 
                        reach: val,
                        // Auto-calculate engagement_rate from total_engagement / reach
                        engagement_rate: val ? ((summary.total_engagement || 0) / Math.max(1, val) * 100) : summary.engagement_rate || 0
                      });
                    }}
                    placeholder="Total reach/views"
                  />
                  <p className="text-xs text-muted-foreground mt-1">Same as "Number of Reach" in Analysis</p>
                </div>
                <div>
                  <Label>Sentiment Trend</Label>
                  <Input
                    type="number"
                    step="0.01"
                    value={summary.sentiment_trend || 0}
                    onChange={(e) => setSummary({ ...summary, sentiment_trend: parseFloat(e.target.value) || 0 })}
                  />
                </div>
                <div>
                  <Label>Mentions Trend</Label>
                  <Input
                    type="number"
                    step="0.01"
                    value={summary.mentions_trend || 0}
                    onChange={(e) => setSummary({ ...summary, mentions_trend: parseFloat(e.target.value) || 0 })}
                  />
                </div>
                <div>
                  <Label>Engagement Trend</Label>
                  <Input
                    type="number"
                    step="0.01"
                    value={summary.engagement_trend || 0}
                    onChange={(e) => setSummary({ ...summary, engagement_trend: parseFloat(e.target.value) || 0 })}
                  />
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
                        value={entry.metric_date}
                        onChange={(e) => {
                          const newEntries = [...timeline.entries];
                          newEntries[index].metric_date = e.target.value;
                          setTimeline({ entries: newEntries });
                        }}
                      />
                    </div>
                    <div>
                      <Label>Sentiment Score</Label>
                      <Input
                        type="number"
                        step="0.01"
                        value={entry.sentiment_score || 0}
                        onChange={(e) => {
                          const newEntries = [...timeline.entries];
                          newEntries[index].sentiment_score = parseFloat(e.target.value) || 0;
                          setTimeline({ entries: newEntries });
                        }}
                      />
                    </div>
                    <div>
                      <Label>Total Mentions</Label>
                      <Input
                        type="number"
                        value={entry.total_mentions || 0}
                        onChange={(e) => {
                          const newEntries = [...timeline.entries];
                          newEntries[index].total_mentions = parseInt(e.target.value) || 0;
                          setTimeline({ entries: newEntries });
                        }}
                      />
                    </div>
                    <div>
                      <Label>Positive</Label>
                      <Input
                        type="number"
                        value={entry.positive_count || 0}
                        onChange={(e) => {
                          const newEntries = [...timeline.entries];
                          newEntries[index].positive_count = parseInt(e.target.value) || 0;
                          setTimeline({ entries: newEntries });
                        }}
                      />
                    </div>
                    <div>
                      <Label>Neutral</Label>
                      <Input
                        type="number"
                        value={entry.neutral_count || 0}
                        onChange={(e) => {
                          const newEntries = [...timeline.entries];
                          newEntries[index].neutral_count = parseInt(e.target.value) || 0;
                          setTimeline({ entries: newEntries });
                        }}
                      />
                    </div>
                    <div>
                      <Label>Negative</Label>
                      <Input
                        type="number"
                        value={entry.negative_count || 0}
                        onChange={(e) => {
                          const newEntries = [...timeline.entries];
                          newEntries[index].negative_count = parseInt(e.target.value) || 0;
                          setTimeline({ entries: newEntries });
                        }}
                      />
                    </div>
                    <div>
                      <Label>Reach</Label>
                      <Input
                        type="number"
                        value={entry.reach || 0}
                        onChange={(e) => {
                          const newEntries = [...timeline.entries];
                          newEntries[index].reach = parseInt(e.target.value) || 0;
                          setTimeline({ entries: newEntries });
                        }}
                      />
                    </div>
                    <div>
                      <Label>Engagement Rate</Label>
                      <Input
                        type="number"
                        step="0.01"
                        value={entry.engagement_rate || 0}
                        onChange={(e) => {
                          const newEntries = [...timeline.entries];
                          newEntries[index].engagement_rate = parseFloat(e.target.value) || 0;
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

        {/* Audience Tab */}
        <TabsContent value="audience" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Audience Demographics</CardTitle>
              <CardDescription>Edit audience demographics</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Button onClick={addAudienceEntry} variant="outline" className="w-full">
                <Plus className="h-4 w-4 mr-2" />
                Add Audience Entry
              </Button>

              {audience.demographics?.map((demo, index) => (
                <Card key={index} className="p-4">
                  <div className="flex items-start justify-between mb-4">
                    <h4 className="font-semibold">Entry {index + 1}</h4>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => removeAudienceEntry(index)}
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label>Age Group</Label>
                      <Input
                        value={demo.age_group}
                        onChange={(e) => {
                          const newDemos = [...(audience.demographics || [])];
                          newDemos[index].age_group = e.target.value;
                          setAudience({ demographics: newDemos });
                        }}
                      />
                    </div>
                    <div>
                      <Label>Gender</Label>
                      <Input
                        value={demo.gender}
                        onChange={(e) => {
                          const newDemos = [...(audience.demographics || [])];
                          newDemos[index].gender = e.target.value;
                          setAudience({ demographics: newDemos });
                        }}
                      />
                    </div>
                    <div>
                      <Label>Location</Label>
                      <Input
                        value={demo.location}
                        onChange={(e) => {
                          const newDemos = [...(audience.demographics || [])];
                          newDemos[index].location = e.target.value;
                          setAudience({ demographics: newDemos });
                        }}
                      />
                    </div>
                    <div>
                      <Label>Count</Label>
                      <Input
                        type="number"
                        value={demo.count || 0}
                        onChange={(e) => {
                          const newDemos = [...(audience.demographics || [])];
                          newDemos[index].count = parseInt(e.target.value) || 0;
                          setAudience({ demographics: newDemos });
                        }}
                      />
                    </div>
                    <div>
                      <Label>Percentage</Label>
                      <Input
                        type="number"
                        step="0.1"
                        value={demo.percentage || 0}
                        onChange={(e) => {
                          const newDemos = [...(audience.demographics || [])];
                          newDemos[index].percentage = parseFloat(e.target.value) || 0;
                          setAudience({ demographics: newDemos });
                        }}
                      />
                    </div>
                  </div>
                </Card>
              ))}

              <Button
                onClick={() => handleSave("audience")}
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
                    Save Audience
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
              <CardDescription>Edit performance metrics (JSON format)</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label>Overall Metrics (JSON)</Label>
                <Textarea
                  placeholder='{"metric": "value"}'
                  value={JSON.stringify(performance.overall_metrics || {}, null, 2)}
                  onChange={(e) => {
                    try {
                      const parsed = JSON.parse(e.target.value);
                      setPerformance({ ...performance, overall_metrics: parsed });
                    } catch (err) {
                      // Invalid JSON, ignore
                    }
                  }}
                  className="font-mono text-sm"
                  rows={6}
                />
              </div>

              <div>
                <Label>Platform Breakdown (JSON Array)</Label>
                <Textarea
                  placeholder='[{"platform": "value"}]'
                  value={JSON.stringify(performance.platform_breakdown || [], null, 2)}
                  onChange={(e) => {
                    try {
                      const parsed = JSON.parse(e.target.value);
                      setPerformance({ ...performance, platform_breakdown: parsed });
                    } catch (err) {
                      // Invalid JSON, ignore
                    }
                  }}
                  className="font-mono text-sm"
                  rows={6}
                />
              </div>

              <div>
                <Label>Conversion Funnel (JSON)</Label>
                <Textarea
                  placeholder='{"stage": "value"}'
                  value={JSON.stringify(performance.conversion_funnel || {}, null, 2)}
                  onChange={(e) => {
                    try {
                      const parsed = JSON.parse(e.target.value);
                      setPerformance({ ...performance, conversion_funnel: parsed });
                    } catch (err) {
                      // Invalid JSON, ignore
                    }
                  }}
                  className="font-mono text-sm"
                  rows={6}
                />
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
          </div>
        </div>
      </Tabs>
    </div>
  );
}
