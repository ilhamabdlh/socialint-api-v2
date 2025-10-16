import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import { Badge } from "./ui/badge";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area, ComposedChart, Bar } from "recharts";
import { TrendingUp, MessageSquare, Heart, Activity } from "lucide-react";
import { TimeSeriesData } from "../lib/mock-data";

interface TimeSeriesChartsProps {
  data: TimeSeriesData[];
  title?: string;
  brandSummary?: any;
  performanceData?: any;
  sentimentTimeline?: any;
}

export function TimeSeriesCharts({ data, title = "Time Series Analysis", brandSummary, performanceData, sentimentTimeline }: TimeSeriesChartsProps) {
  // Format engagement value for display
  const formatEngagement = (value: number) => {
    if (value >= 1000000) {
      return `${(value / 1000000).toFixed(1)}M`;
    } else if (value >= 1000) {
      return `${(value / 1000).toFixed(1)}K`;
    }
    return value.toString();
  };

  // Calculate trends
  const calculateTrend = (values: number[]) => {
    if (values.length < 2) return 0;
    const recent = values.slice(-7).reduce((a, b) => a + b, 0) / 7;
    const previous = values.slice(-14, -7).reduce((a, b) => a + b, 0) / 7;
    return ((recent - previous) / previous) * 100;
  };

  // Use real data from API if available, otherwise fallback to calculated trends
  const sentimentTrend = data.length > 0 ? calculateTrend(data.map(d => d.sentiment)) : 0;
  const mentionsTrend = data.length > 0 ? calculateTrend(data.map(d => d.mentions)) : 0;
  // For engagement trend, calculate based on engagement rate if available
  const engagementTrend = data.length > 0 ? calculateTrend(data.map(d => d.engagement)) : 0;
  
  // Get current values from API data
  const currentSentiment = brandSummary?.sentiment_percentage?.Positive || data[data.length - 1]?.sentiment || 0;
  const currentMentions = brandSummary?.total_posts || data[data.length - 1]?.mentions || 0;
  const currentEngagement = performanceData?.total_engagement || data[data.length - 1]?.engagement || 0;

  const getTrendColor = (trend: number) => {
    if (trend > 5) return "text-green-600";
    if (trend < -5) return "text-red-600";
    return "text-gray-600";
  };

  const getTrendIcon = (trend: number) => {
    if (trend > 5) return "↗";
    if (trend < -5) return "↘";
    return "→";
  };

  // Use real API data if available, otherwise fallback to mock data
  const realChartData = sentimentTimeline?.timeline?.map((item: any) => {
    // Calculate sentiment score from positive, neutral, negative counts
    const totalSentiment = (item.Positive || 0) + (item.Neutral || 0) + (item.Negative || 0);
    const sentimentScore = totalSentiment > 0 
      ? Math.round(((item.Positive || 0) - (item.Negative || 0)) / totalSentiment * 100) 
      : 0;
    
    return {
      date: new Date(item.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      sentiment: sentimentScore, // Sentiment score calculated from positive/negative ratio
      mentions: item.total_posts || 0, // Total mentions from total_posts
      engagement: (item.total_likes || 0) + (item.total_comments || 0) + (item.total_shares || 0), // Total engagement
      positive: item.positive_percentage || 0, // Distribution: positive percentage
      neutral: item.neutral_percentage || 0, // Distribution: neutral percentage
      negative: item.negative_percentage || 0 // Distribution: negative percentage
    };
  }) || [];


  // Use only real data - no fallback to mock data
  const chartData = realChartData;

  // Use real data for trend calculations
  const realSentimentTrend = realChartData.length > 0 ? calculateTrend(realChartData.map(d => d.sentiment)) : 0;
  const realMentionsTrend = realChartData.length > 0 ? calculateTrend(realChartData.map(d => d.mentions)) : 0;
  const realEngagementTrend = realChartData.length > 0 ? calculateTrend(realChartData.map(d => d.engagement)) : 0;

  return (
    <div className="space-y-6">

      {/* Time Series Charts */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            {title}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="sentiment" className="space-y-4">
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="sentiment">Sentiment</TabsTrigger>
              <TabsTrigger value="mentions">Mentions</TabsTrigger>
              <TabsTrigger value="engagement">Engagement</TabsTrigger>
              <TabsTrigger value="distribution">Distribution</TabsTrigger>
            </TabsList>

            <TabsContent value="sentiment" className="space-y-4">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <TrendingUp className="h-4 w-4" />
                  <span className="font-medium">Sentiment Trend</span>
                  <Badge variant="outline" className={getTrendColor(realSentimentTrend)}>
                    {getTrendIcon(realSentimentTrend)} {Math.abs(realSentimentTrend).toFixed(1)}%
                  </Badge>
                </div>
              </div>
              {chartData.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis domain={[0, 100]} />
                    <Tooltip 
                      formatter={(value) => [`${value}%`, 'Sentiment Score']}
                      labelFormatter={(label) => `Date: ${label}`}
                    />
                    <Line 
                      type="monotone" 
                      dataKey="sentiment" 
                      stroke="#3b82f6" 
                      strokeWidth={2}
                      dot={{ r: 4 }}
                      activeDot={{ r: 6 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex items-center justify-center h-[300px] text-muted-foreground">
                  <div className="text-center">
                    <TrendingUp className="h-12 w-12 mx-auto mb-4 opacity-50" />
                    <p className="text-lg font-medium">No sentiment data available</p>
                    <p className="text-sm">Try adjusting your date range or platform filters</p>
                  </div>
                </div>
              )}
            </TabsContent>

            <TabsContent value="mentions" className="space-y-4">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <MessageSquare className="h-4 w-4" />
                  <span className="font-medium">Mentions Trend</span>
                  <Badge variant="outline" className={getTrendColor(realMentionsTrend)}>
                    {getTrendIcon(realMentionsTrend)} {Math.abs(realMentionsTrend).toFixed(1)}%
                  </Badge>
                </div>
              </div>
              {chartData.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip 
                      formatter={(value) => [value, 'Mentions']}
                      labelFormatter={(label) => `Date: ${label}`}
                    />
                    <Area 
                      type="monotone" 
                      dataKey="mentions" 
                      stroke="#22c55e" 
                      fill="#22c55e" 
                      fillOpacity={0.3}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex items-center justify-center h-[300px] text-muted-foreground">
                  <div className="text-center">
                    <MessageSquare className="h-12 w-12 mx-auto mb-4 opacity-50" />
                    <p className="text-lg font-medium">No mentions data available</p>
                    <p className="text-sm">Try adjusting your date range or platform filters</p>
                  </div>
                </div>
              )}
            </TabsContent>

            <TabsContent value="engagement" className="space-y-4">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <Heart className="h-4 w-4" />
                  <span className="font-medium">Engagement Trend</span>
                  <Badge variant="outline" className={getTrendColor(realEngagementTrend)}>
                    {getTrendIcon(realEngagementTrend)} {Math.abs(realEngagementTrend).toFixed(1)}%
                  </Badge>
                </div>
              </div>
              {chartData.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip 
                      formatter={(value) => [value.toLocaleString(), 'Total Engagement']}
                      labelFormatter={(label) => `Date: ${label}`}
                    />
                    <Line 
                      type="monotone" 
                      dataKey="engagement" 
                      stroke="#f59e0b" 
                      strokeWidth={2}
                      dot={{ r: 4 }}
                      activeDot={{ r: 6 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex items-center justify-center h-[300px] text-muted-foreground">
                  <div className="text-center">
                    <Heart className="h-12 w-12 mx-auto mb-4 opacity-50" />
                    <p className="text-lg font-medium">No engagement data available</p>
                    <p className="text-sm">Try adjusting your date range or platform filters</p>
                  </div>
                </div>
              )}
            </TabsContent>

            <TabsContent value="distribution" className="space-y-4">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <Activity className="h-4 w-4" />
                  <span className="font-medium">Sentiment Distribution</span>
                </div>
              </div>
              {chartData.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <ComposedChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis domain={[0, 100]} />
                    <Tooltip 
                      formatter={(value, name) => [`${value}%`, typeof name === 'string' ? name.charAt(0).toUpperCase() + name.slice(1) : name]}
                      labelFormatter={(label) => `Date: ${label}`}
                    />
                    <Bar dataKey="positive" stackId="sentiment" fill="#22c55e" name="positive" />
                    <Bar dataKey="neutral" stackId="sentiment" fill="#6b7280" name="neutral" />
                    <Bar dataKey="negative" stackId="sentiment" fill="#ef4444" name="negative" />
                  </ComposedChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex items-center justify-center h-[300px] text-muted-foreground">
                  <div className="text-center">
                    <Activity className="h-12 w-12 mx-auto mb-4 opacity-50" />
                    <p className="text-lg font-medium">No distribution data available</p>
                    <p className="text-sm">Try adjusting your date range or platform filters</p>
                  </div>
                </div>
              )}
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
}