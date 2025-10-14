import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { Progress } from "./ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  ResponsiveContainer,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  AreaChart,
  Area
} from "recharts";
import {
  ArrowLeft,
  Calendar,
  DollarSign,
  Target,
  TrendingUp,
  TrendingDown,
  Users,
  MessageSquare,
  Eye,
  Heart,
  Share,
  MapPin,
  Play,
  Pause,
  Edit
} from "lucide-react";
import { Campaign } from "../lib/mock-data";

interface CampaignDetailsProps {
  campaign: Campaign;
  onBack: () => void;
}

export function CampaignDetails({ campaign, onBack }: CampaignDetailsProps) {
  const [selectedMetric, setSelectedMetric] = useState<'mentions' | 'sentiment' | 'engagement' | 'reach'>('mentions');

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800 border-green-300';
      case 'paused': return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      case 'completed': return 'bg-blue-100 text-blue-800 border-blue-300';
      case 'draft': return 'bg-gray-100 text-gray-800 border-gray-300';
      default: return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'product_launch': return 'bg-purple-100 text-purple-800 border-purple-300';
      case 'brand_awareness': return 'bg-blue-100 text-blue-800 border-blue-300';
      case 'feature_highlight': return 'bg-orange-100 text-orange-800 border-orange-300';
      case 'crisis_response': return 'bg-red-100 text-red-800 border-red-300';
      default: return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  const formatType = (type: string) => {
    return type.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
  };

  const budgetUtilization = (campaign.spent / campaign.budget) * 100;
  const daysElapsed = Math.floor((new Date().getTime() - new Date(campaign.start_date).getTime()) / (1000 * 60 * 60 * 24));
  const totalDays = Math.floor((new Date(campaign.end_date).getTime() - new Date(campaign.start_date).getTime()) / (1000 * 60 * 60 * 24));
  const timeProgress = (daysElapsed / totalDays) * 100;

  // KPI comparison data
  const kpiComparison = [
    {
      metric: 'Sentiment Score',
      current: campaign.current_performance.sentiment_score * 100,
      target: campaign.primary_kpis.sentiment_target * 100,
      unit: '%'
    },
    {
      metric: 'Total Mentions',
      current: campaign.current_performance.total_mentions,
      target: campaign.primary_kpis.mentions_target,
      unit: ''
    },
    {
      metric: 'Engagement Rate',
      current: campaign.current_performance.engagement_rate,
      target: campaign.primary_kpis.engagement_target,
      unit: '%'
    }
  ];

  // Platform performance data
  const platformColors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];
  const platformData = campaign.platforms.map((platform, index) => ({
    platform,
    mentions: Math.floor(campaign.current_performance.total_mentions / campaign.platforms.length * (1 + Math.random() * 0.4 - 0.2)),
    color: platformColors[index % platformColors.length]
  }));

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Button variant="outline" onClick={onBack} className="flex items-center space-x-2">
            <ArrowLeft className="h-4 w-4" />
            <span>Back to Campaigns</span>
          </Button>
          <div>
            <div className="flex items-center space-x-3">
              <h1 className="text-2xl font-bold">{campaign.name}</h1>
              <Badge className={getStatusColor(campaign.status)}>
                {campaign.status.toUpperCase()}
              </Badge>
              <Badge className={getTypeColor(campaign.type)}>
                {formatType(campaign.type)}
              </Badge>
            </div>
            <p className="text-muted-foreground mt-1">
              {new Date(campaign.start_date).toLocaleDateString()} - {new Date(campaign.end_date).toLocaleDateString()}
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline" size="sm">
            <Edit className="h-4 w-4 mr-2" />
            Edit Campaign
          </Button>
          {campaign.status === 'active' ? (
            <Button variant="outline" size="sm">
              <Pause className="h-4 w-4 mr-2" />
              Pause
            </Button>
          ) : (
            <Button variant="outline" size="sm">
              <Play className="h-4 w-4 mr-2" />
              Resume
            </Button>
          )}
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Budget Progress</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${(campaign.spent / 1000).toFixed(0)}K</div>
            <p className="text-xs text-muted-foreground mb-2">
              of ${(campaign.budget / 1000).toFixed(0)}K budget
            </p>
            <Progress value={budgetUtilization} className="h-2" />
            <p className="text-xs text-muted-foreground mt-1">{budgetUtilization.toFixed(1)}% utilized</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Time Progress</CardTitle>
            <Calendar className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{daysElapsed}</div>
            <p className="text-xs text-muted-foreground mb-2">
              of {totalDays} days elapsed
            </p>
            <Progress value={timeProgress} className="h-2" />
            <p className="text-xs text-muted-foreground mt-1">{timeProgress.toFixed(1)}% complete</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Reach</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{(campaign.current_performance.reach / 1000000).toFixed(1)}M</div>
            <p className="text-xs text-muted-foreground">
              Conversion Rate: {campaign.current_performance.conversion_rate}%
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Sentiment Score</CardTitle>
            <Target className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="flex items-center space-x-2">
              <div className="text-2xl font-bold">{(campaign.current_performance.sentiment_score * 100).toFixed(1)}%</div>
              {campaign.current_performance.sentiment_score >= campaign.primary_kpis.sentiment_target ? (
                <TrendingUp className="h-4 w-4 text-green-500" />
              ) : (
                <TrendingDown className="h-4 w-4 text-red-500" />
              )}
            </div>
            <p className="text-xs text-muted-foreground">
              Target: {(campaign.primary_kpis.sentiment_target * 100).toFixed(1)}%
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Performance Analytics */}
      <Tabs defaultValue="performance" className="space-y-6">
        <TabsList>
          <TabsTrigger value="performance">Performance Trends</TabsTrigger>
          <TabsTrigger value="kpis">KPI Analysis</TabsTrigger>
          <TabsTrigger value="content">Top Content</TabsTrigger>
          <TabsTrigger value="regional">Regional Performance</TabsTrigger>
        </TabsList>

        <TabsContent value="performance" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Daily Performance Trends</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="mb-4">
                  <div className="flex space-x-2">
                    {(['mentions', 'sentiment', 'engagement', 'reach'] as const).map((metric) => (
                      <Button
                        key={metric}
                        variant={selectedMetric === metric ? "default" : "outline"}
                        size="sm"
                        onClick={() => setSelectedMetric(metric)}
                      >
                        {metric.charAt(0).toUpperCase() + metric.slice(1)}
                      </Button>
                    ))}
                  </div>
                </div>
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={campaign.daily_metrics}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Area 
                      type="monotone" 
                      dataKey={selectedMetric} 
                      stroke="#3b82f6" 
                      fill="#3b82f6" 
                      fillOpacity={0.2}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Platform Distribution</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={platformData}
                      cx="50%"
                      cy="50%"
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="mentions"
                      label={({ platform, mentions }) => `${platform}: ${mentions}`}
                    >
                      {platformData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="kpis" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>KPI Performance vs Targets</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {kpiComparison.map((kpi, index) => (
                  <div key={index} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="font-medium">{kpi.metric}</span>
                      <div className="flex items-center space-x-2">
                        <span className="text-2xl font-bold">
                          {kpi.unit === '%' ? kpi.current.toFixed(1) : kpi.current.toLocaleString()}{kpi.unit}
                        </span>
                        <span className="text-sm text-muted-foreground">
                          / {kpi.unit === '%' ? kpi.target.toFixed(1) : kpi.target.toLocaleString()}{kpi.unit}
                        </span>
                        {kpi.current >= kpi.target ? (
                          <TrendingUp className="h-4 w-4 text-green-500" />
                        ) : (
                          <TrendingDown className="h-4 w-4 text-red-500" />
                        )}
                      </div>
                    </div>
                    <Progress value={(kpi.current / kpi.target) * 100} className="h-3" />
                    <p className="text-xs text-muted-foreground">
                      {((kpi.current / kpi.target) * 100).toFixed(1)}% of target achieved
                    </p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="content" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Top Performing Content</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {campaign.top_content.map((content, index) => (
                  <div key={index} className="border rounded-lg p-4 space-y-3">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h4 className="font-medium">{content.content}</h4>
                        <p className="text-sm text-muted-foreground">{content.platform}</p>
                      </div>
                      <Badge variant="outline">{(content.sentiment * 100).toFixed(1)}% sentiment</Badge>
                    </div>
                    <div className="grid grid-cols-3 gap-4 text-sm">
                      <div className="flex items-center space-x-2">
                        <Eye className="h-4 w-4 text-muted-foreground" />
                        <span>{content.reach.toLocaleString()} reach</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Heart className="h-4 w-4 text-muted-foreground" />
                        <span>{content.engagement.toFixed(1)}% engagement</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Share className="h-4 w-4 text-muted-foreground" />
                        <span>Platform: {content.platform}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="regional" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Regional Performance</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <BarChart data={campaign.regional_performance} layout="horizontal">
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" />
                  <YAxis dataKey="region" type="category" width={120} />
                  <Bar dataKey="mentions" fill="#3b82f6" name="Mentions" />
                </BarChart>
              </ResponsiveContainer>
              <div className="mt-6 space-y-4">
                {campaign.regional_performance.map((region, index) => (
                  <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                    <div className="flex items-center space-x-3">
                      <MapPin className="h-4 w-4 text-muted-foreground" />
                      <span className="font-medium">{region.region}</span>
                    </div>
                    <div className="text-right space-y-1">
                      <div className="flex items-center space-x-4 text-sm">
                        <span>{region.mentions.toLocaleString()} mentions</span>
                        <span>{(region.sentiment * 100).toFixed(1)}% sentiment</span>
                        <span>{region.engagement.toFixed(1)}% engagement</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}