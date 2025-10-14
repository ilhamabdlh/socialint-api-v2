import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import { Progress } from "./ui/progress";
import { Campaign, Brand, Content, AnalysisResult, analysisResults, timeSeriesData } from "../lib/mock-data";
import { AnalysisFilters, FilterState } from "./AnalysisFilters";
import { TimeSeriesCharts } from "./TimeSeriesCharts";
import { EntityDetails } from "./EntityDetails";
import { 
  ArrowLeft, 
  TrendingUp, 
  MessageSquare, 
  Heart, 
  Users, 
  Target, 
  BarChart3,
  PieChart,
  Activity,
  Globe,
  Clock,
  Zap,
  Info
} from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart as RechartsPieChart, Pie, Cell, LineChart, Line, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from "recharts";

interface AnalysisViewProps {
  entity: Campaign | Brand | Content;
  entityType: 'campaign' | 'brand' | 'content';
  onBack: () => void;
}

export function AnalysisView({ entity, entityType, onBack }: AnalysisViewProps) {
  // Get analysis results for this entity (using mock data for now)
  const analysis = analysisResults.find(a => a.entity_id === entity.id) || analysisResults[0];
  
  // Get time series data for this entity
  const entityTimeSeriesData = timeSeriesData[entity.id] || timeSeriesData['camp_001'];
  
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

  const sentimentData = [
    { name: 'Positive', value: analysis.sentiment.positive, color: '#22c55e' },
    { name: 'Neutral', value: analysis.sentiment.neutral, color: '#6b7280' },
    { name: 'Negative', value: analysis.sentiment.negative, color: '#ef4444' }
  ];

  const emotionData = Object.entries(analysis.emotions).map(([emotion, value]) => ({
    emotion: emotion.charAt(0).toUpperCase() + emotion.slice(1),
    value: Math.round(value * 100)
  }));

  const topicData = analysis.topics.map(topic => ({
    name: topic.topic,
    mentions: topic.mentions,
    sentiment: Math.round(topic.sentiment * 100)
  }));

  const competitorData = analysis.competitive_insights.map(comp => ({
    name: comp.competitor,
    share: Math.round(comp.mention_share * 100),
    sentiment: Math.round((comp.sentiment_comparison + 1) * 50) // Normalize to 0-100
  }));

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
    if (score >= 0.7) return 'text-green-600';
    if (score >= 0.5) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getSentimentBackground = (score: number) => {
    if (score >= 0.7) return 'bg-green-100';
    if (score >= 0.5) return 'bg-yellow-100';
    return 'bg-red-100';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
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
          Last updated: {analysis.analysis_date}
        </Badge>
      </div>

      {/* Description */}
      <Card>
        <CardContent className="pt-6">
          <p className="text-muted-foreground">{getEntityDescription()}</p>
        </CardContent>
      </Card>

      {/* Key Metrics Overview */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Overall Sentiment</p>
                <p className={`text-2xl font-bold ${getSentimentColor(analysis.sentiment.overall_score)}`}>
                  {Math.round(analysis.sentiment.overall_score * 100)}%
                </p>
              </div>
              <div className={`p-2 rounded-lg ${getSentimentBackground(analysis.sentiment.overall_score)}`}>
                <TrendingUp className={`h-5 w-5 ${getSentimentColor(analysis.sentiment.overall_score)}`} />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Total Mentions</p>
                <p className="text-2xl font-bold">{analysis.metrics.total_mentions.toLocaleString()}</p>
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
                <p className="text-2xl font-bold">{analysis.metrics.engagement_rate}%</p>
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
                <p className="text-2xl font-bold">{(analysis.metrics.reach / 1000000).toFixed(1)}M</p>
              </div>
              <div className="p-2 rounded-lg bg-purple-100">
                <Globe className="h-5 w-5 text-purple-600" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Analysis Content */}
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
            data={entityTimeSeriesData}
            title={`${getEntityTitle()} - Time Series Analysis`}
          />

          {/* Detailed Analysis Tabs */}
          <Tabs defaultValue="overview" className="space-y-6">
            <TabsList className="grid w-full grid-cols-7">
              <TabsTrigger value="overview" className="flex items-center gap-2">
                <Info className="h-4 w-4" />
                <span className="hidden sm:inline">Overview</span>
              </TabsTrigger>
              <TabsTrigger value="sentiment" className="flex items-center gap-2">
                <TrendingUp className="h-4 w-4" />
                <span className="hidden sm:inline">Sentiment</span>
              </TabsTrigger>
              <TabsTrigger value="topics" className="flex items-center gap-2">
                <MessageSquare className="h-4 w-4" />
                <span className="hidden sm:inline">Topics</span>
              </TabsTrigger>
              <TabsTrigger value="emotions" className="flex items-center gap-2">
                <Heart className="h-4 w-4" />
                <span className="hidden sm:inline">Emotions</span>
              </TabsTrigger>
              <TabsTrigger value="audience" className="flex items-center gap-2">
                <Users className="h-4 w-4" />
                <span className="hidden sm:inline">Audience</span>
              </TabsTrigger>
              <TabsTrigger value="performance" className="flex items-center gap-2">
                <BarChart3 className="h-4 w-4" />
                <span className="hidden sm:inline">Performance</span>
              </TabsTrigger>
              <TabsTrigger value="competitive" className="flex items-center gap-2">
                <Target className="h-4 w-4" />
                <span className="hidden sm:inline">Competitive</span>
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
                    <span className={getSentimentColor(analysis.sentiment.overall_score)}>
                      {Math.round(analysis.sentiment.overall_score * 100)}%
                    </span>
                  </div>
                  <Progress value={analysis.sentiment.overall_score * 100} className="h-2" />
                </div>
                
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>Confidence Level</span>
                    <span>{Math.round(analysis.sentiment.confidence * 100)}%</span>
                  </div>
                  <Progress value={analysis.sentiment.confidence * 100} className="h-2" />
                </div>

                <div className="pt-4 space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-sm">Positive</span>
                    <Badge className="bg-green-100 text-green-800">
                      {analysis.sentiment.positive}%
                    </Badge>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm">Neutral</span>
                    <Badge className="bg-gray-100 text-gray-800">
                      {analysis.sentiment.neutral}%
                    </Badge>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm">Negative</span>
                    <Badge className="bg-red-100 text-red-800">
                      {analysis.sentiment.negative}%
                    </Badge>
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
              <ResponsiveContainer width="100%" height={400}>
                <BarChart data={topicData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} />
                  <YAxis yAxisId="left" />
                  <YAxis yAxisId="right" orientation="right" />
                  <Tooltip />
                  <Bar yAxisId="left" dataKey="mentions" fill="#3b82f6" name="Mentions" />
                  <Bar yAxisId="right" dataKey="sentiment" fill="#22c55e" name="Sentiment %" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <div className="grid gap-4">
            {analysis.topics.map((topic, index) => (
              <Card key={index}>
                <CardContent className="p-4">
                  <div className="flex justify-between items-center mb-2">
                    <h4 className="font-medium">{topic.topic}</h4>
                    <Badge variant="outline">
                      {topic.mentions} mentions
                    </Badge>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="flex-1">
                      <div className="flex justify-between text-sm mb-1">
                        <span>Relevance</span>
                        <span>{Math.round(topic.relevance * 100)}%</span>
                      </div>
                      <Progress value={topic.relevance * 100} className="h-2" />
                    </div>
                    <div className="flex-1">
                      <div className="flex justify-between text-sm mb-1">
                        <span>Sentiment</span>
                        <span className={getSentimentColor(topic.sentiment)}>
                          {Math.round(topic.sentiment * 100)}%
                        </span>
                      </div>
                      <Progress value={topic.sentiment * 100} className="h-2" />
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
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
              <ResponsiveContainer width="100%" height={400}>
                <RadarChart data={emotionData}>
                  <PolarGrid />
                  <PolarAngleAxis dataKey="emotion" />
                  <PolarRadiusAxis angle={30} domain={[0, 100]} />
                  <Radar
                    name="Emotion Intensity"
                    dataKey="value"
                    stroke="#8884d8"
                    fill="#8884d8"
                    fillOpacity={0.6}
                  />
                  <Tooltip formatter={(value) => [`${value}%`, 'Intensity']} />
                </RadarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="audience" className="space-y-6">
          <div className="grid md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Demographics</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <h4 className="font-medium mb-2">Age Groups</h4>
                  {analysis.audience.demographics.age_groups.map((group, index) => (
                    <div key={index} className="flex justify-between items-center mb-2">
                      <span className="text-sm">{group.range}</span>
                      <div className="flex items-center gap-2">
                        <Progress value={group.percentage} className="w-20 h-2" />
                        <span className="text-sm w-10">{group.percentage}%</span>
                      </div>
                    </div>
                  ))}
                </div>

                <div>
                  <h4 className="font-medium mb-2">Gender Distribution</h4>
                  {analysis.audience.demographics.genders.map((gender, index) => (
                    <div key={index} className="flex justify-between items-center mb-2">
                      <span className="text-sm">{gender.gender}</span>
                      <div className="flex items-center gap-2">
                        <Progress value={gender.percentage} className="w-20 h-2" />
                        <span className="text-sm w-10">{gender.percentage}%</span>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Geographic Distribution</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {analysis.audience.demographics.locations.map((location, index) => (
                  <div key={index} className="flex justify-between items-center">
                    <span className="text-sm">{location.location}</span>
                    <div className="flex items-center gap-2">
                      <Progress value={location.percentage} className="w-20 h-2" />
                      <span className="text-sm w-10">{location.percentage}%</span>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Engagement Patterns</CardTitle>
            </CardHeader>
            <CardContent className="grid md:grid-cols-3 gap-6">
              <div>
                <h4 className="font-medium mb-2">Peak Hours</h4>
                <div className="flex flex-wrap gap-1">
                  {analysis.audience.engagement_patterns.peak_hours.map((hour, index) => (
                    <Badge key={index} variant="secondary">{hour}</Badge>
                  ))}
                </div>
              </div>
              <div>
                <h4 className="font-medium mb-2">Active Days</h4>
                <div className="flex flex-wrap gap-1">
                  {analysis.audience.engagement_patterns.active_days.map((day, index) => (
                    <Badge key={index} variant="secondary">{day}</Badge>
                  ))}
                </div>
              </div>
              <div>
                <h4 className="font-medium mb-2">Avg. Engagement Rate</h4>
                <p className="text-2xl font-bold text-green-600">
                  {analysis.audience.engagement_patterns.engagement_rate}%
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="performance" className="space-y-6">
          <div className="grid md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Performance Metrics</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="text-center p-3 bg-blue-50 rounded-lg">
                    <p className="text-sm text-muted-foreground">Total Reach</p>
                    <p className="text-xl font-bold text-blue-600">
                      {(analysis.metrics.reach / 1000000).toFixed(1)}M
                    </p>
                  </div>
                  <div className="text-center p-3 bg-green-50 rounded-lg">
                    <p className="text-sm text-muted-foreground">Impressions</p>
                    <p className="text-xl font-bold text-green-600">
                      {(analysis.metrics.impressions / 1000000).toFixed(1)}M
                    </p>
                  </div>
                  <div className="text-center p-3 bg-orange-50 rounded-lg">
                    <p className="text-sm text-muted-foreground">Share Rate</p>
                    <p className="text-xl font-bold text-orange-600">
                      {analysis.metrics.share_rate}%
                    </p>
                  </div>
                  <div className="text-center p-3 bg-purple-50 rounded-lg">
                    <p className="text-sm text-muted-foreground">Click Rate</p>
                    <p className="text-xl font-bold text-purple-600">
                      {analysis.metrics.click_rate}%
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Conversion Funnel</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-sm">Impressions</span>
                    <span className="font-medium">{analysis.metrics.impressions.toLocaleString()}</span>
                  </div>
                  <Progress value={100} className="h-2" />
                  
                  <div className="flex justify-between items-center">
                    <span className="text-sm">Engagement</span>
                    <span className="font-medium">
                      {Math.round(analysis.metrics.impressions * analysis.metrics.engagement_rate / 100).toLocaleString()}
                    </span>
                  </div>
                  <Progress value={analysis.metrics.engagement_rate} className="h-2" />
                  
                  <div className="flex justify-between items-center">
                    <span className="text-sm">Clicks</span>
                    <span className="font-medium">
                      {Math.round(analysis.metrics.impressions * analysis.metrics.click_rate / 100).toLocaleString()}
                    </span>
                  </div>
                  <Progress value={analysis.metrics.click_rate} className="h-2" />
                  
                  <div className="flex justify-between items-center">
                    <span className="text-sm">Conversions</span>
                    <span className="font-medium">
                      {Math.round(analysis.metrics.impressions * analysis.metrics.conversion_rate / 100).toLocaleString()}
                    </span>
                  </div>
                  <Progress value={analysis.metrics.conversion_rate} className="h-2" />
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="competitive" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Target className="h-5 w-5" />
                Competitive Landscape
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={competitorData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis yAxisId="left" />
                  <YAxis yAxisId="right" orientation="right" />
                  <Tooltip />
                  <Bar yAxisId="left" dataKey="share" fill="#3b82f6" name="Mention Share %" />
                  <Bar yAxisId="right" dataKey="sentiment" fill="#22c55e" name="Relative Sentiment" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <div className="grid gap-4">
            {analysis.competitive_insights.map((competitor, index) => (
              <Card key={index}>
                <CardContent className="p-4">
                  <div className="flex justify-between items-center mb-3">
                    <h4 className="font-medium">{competitor.competitor}</h4>
                    <div className="flex gap-2">
                      <Badge variant="outline">
                        {Math.round(competitor.mention_share * 100)}% share
                      </Badge>
                      <Badge 
                        variant="outline" 
                        className={competitor.sentiment_comparison > 0 ? 'text-green-600' : 'text-red-600'}
                      >
                        {competitor.sentiment_comparison > 0 ? '+' : ''}
                        {Math.round(competitor.sentiment_comparison * 100)}% sentiment
                      </Badge>
                    </div>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground mb-2">Key Differences:</p>
                    <div className="flex flex-wrap gap-1">
                      {competitor.key_differences.map((diff, i) => (
                        <Badge key={i} variant="secondary" className="text-xs">
                          {diff}
                        </Badge>
                      ))}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
}