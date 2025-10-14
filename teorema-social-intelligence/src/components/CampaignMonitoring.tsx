import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { Progress } from "./ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  ResponsiveContainer,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell
} from "recharts";
import {
  Play,
  Pause,
  Eye,
  TrendingUp,
  TrendingDown,
  DollarSign,
  Target,
  Users,
  MessageSquare,
  Calendar
} from "lucide-react";
import { campaigns, Campaign } from "../lib/mock-data";

interface CampaignMonitoringProps {
  onSelectCampaign: (campaign: Campaign) => void;
}

export function CampaignMonitoring({ onSelectCampaign }: CampaignMonitoringProps) {
  const [selectedTimeframe, setSelectedTimeframe] = useState<'7d' | '30d' | '90d'>('30d');

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

  const activeCampaigns = campaigns.filter(c => c.status === 'active');
  const totalBudget = campaigns.reduce((sum, c) => sum + c.budget, 0);
  const totalSpent = campaigns.reduce((sum, c) => sum + c.spent, 0);
  const avgSentiment = campaigns.reduce((sum, c) => sum + c.current_performance.sentiment_score, 0) / campaigns.length;

  // Aggregate performance data for charts
  const campaignPerformanceData = campaigns.map(campaign => ({
    name: campaign.name.slice(0, 15) + '...',
    sentiment: campaign.current_performance.sentiment_score * 100,
    mentions: campaign.current_performance.total_mentions,
    engagement: campaign.current_performance.engagement_rate,
    spend: campaign.spent
  }));

  const statusDistribution = [
    { name: 'Active', value: campaigns.filter(c => c.status === 'active').length, color: '#10b981' },
    { name: 'Paused', value: campaigns.filter(c => c.status === 'paused').length, color: '#f59e0b' },
    { name: 'Completed', value: campaigns.filter(c => c.status === 'completed').length, color: '#3b82f6' },
    { name: 'Draft', value: campaigns.filter(c => c.status === 'draft').length, color: '#6b7280' }
  ];

  return (
    <div className="space-y-6">
      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Campaigns</CardTitle>
            <Play className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{activeCampaigns.length}</div>
            <p className="text-xs text-muted-foreground">
              {campaigns.length - activeCampaigns.length} inactive
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Budget</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${(totalBudget / 1000).toFixed(0)}K</div>
            <p className="text-xs text-muted-foreground">
              ${(totalSpent / 1000).toFixed(0)}K spent ({((totalSpent / totalBudget) * 100).toFixed(1)}%)
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Sentiment</CardTitle>
            <Target className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{(avgSentiment * 100).toFixed(1)}%</div>
            <p className="text-xs text-muted-foreground">
              Across all campaigns
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Reach</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {(campaigns.reduce((sum, c) => sum + c.current_performance.reach, 0) / 1000000).toFixed(1)}M
            </div>
            <p className="text-xs text-muted-foreground">
              Combined audience reach
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Campaign Performance Analytics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Campaign Performance Comparison</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={campaignPerformanceData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Bar dataKey="sentiment" fill="#3b82f6" name="Sentiment %" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Campaign Status Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={statusDistribution}
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                  label={({ name, value }) => `${name}: ${value}`}
                >
                  {statusDistribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Campaign List */}
      <Card>
        <CardHeader>
          <CardTitle>Campaign Overview</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {campaigns.map((campaign) => (
              <div key={campaign.id} className="border rounded-lg p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <h3 className="font-semibold">{campaign.name}</h3>
                    <Badge className={getStatusColor(campaign.status)}>
                      {campaign.status.toUpperCase()}
                    </Badge>
                    <Badge className={getTypeColor(campaign.type)}>
                      {formatType(campaign.type)}
                    </Badge>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => onSelectCampaign(campaign)}
                    className="flex items-center space-x-2"
                  >
                    <Eye className="h-4 w-4" />
                    <span>View Details</span>
                  </Button>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <p className="text-muted-foreground">Duration</p>
                    <p className="font-medium">
                      {new Date(campaign.start_date).toLocaleDateString()} - {new Date(campaign.end_date).toLocaleDateString()}
                    </p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Budget Utilization</p>
                    <p className="font-medium">
                      ${(campaign.spent / 1000).toFixed(0)}K / ${(campaign.budget / 1000).toFixed(0)}K
                    </p>
                    <Progress value={(campaign.spent / campaign.budget) * 100} className="mt-1" />
                  </div>
                  <div>
                    <p className="text-muted-foreground">Sentiment Score</p>
                    <div className="flex items-center space-x-2">
                      <p className="font-medium">{(campaign.current_performance.sentiment_score * 100).toFixed(1)}%</p>
                      {campaign.current_performance.sentiment_score >= campaign.primary_kpis.sentiment_target ? (
                        <TrendingUp className="h-4 w-4 text-green-500" />
                      ) : (
                        <TrendingDown className="h-4 w-4 text-red-500" />
                      )}
                    </div>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Total Mentions</p>
                    <div className="flex items-center space-x-2">
                      <p className="font-medium">{campaign.current_performance.total_mentions.toLocaleString()}</p>
                      <MessageSquare className="h-4 w-4 text-muted-foreground" />
                    </div>
                  </div>
                </div>

                <div className="flex items-center justify-between pt-2 border-t">
                  <div className="flex items-center space-x-4 text-sm text-muted-foreground">
                    <span>Platforms: {campaign.platforms.join(', ')}</span>
                    <span>•</span>
                    <span>Reach: {(campaign.current_performance.reach / 1000000).toFixed(1)}M</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    {campaign.status === 'active' && (
                      <Button variant="outline" size="sm">
                        <Pause className="h-4 w-4" />
                      </Button>
                    )}
                    {campaign.status === 'paused' && (
                      <Button variant="outline" size="sm">
                        <Play className="h-4 w-4" />
                      </Button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}