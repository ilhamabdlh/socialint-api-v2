import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import { Progress } from "./ui/progress";
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  RadialBarChart,
  RadialBar,
  Legend
} from "recharts";
import { socialMetrics } from "../lib/mock-data";
import { TrendingUp, TrendingDown, MessageSquare, Heart, Share2 } from "lucide-react";

export function SocialMediaMetrics() {
  const getTrendIcon = (growth: number) => {
    return growth > 0 ? TrendingUp : TrendingDown;
  };

  const getTrendColor = (growth: number) => {
    return growth > 0 ? "text-green-600" : "text-red-600";
  };

  const getSentimentColor = (sentiment: number) => {
    if (sentiment >= 0.7) return "bg-green-500";
    if (sentiment >= 0.5) return "bg-yellow-500";
    return "bg-red-500";
  };

  const getSentimentLevel = (sentiment: number) => {
    if (sentiment >= 0.7) return "Positive";
    if (sentiment >= 0.5) return "Neutral";
    return "Negative";
  };

  const radialData = socialMetrics.map(metric => ({
    ...metric,
    sentimentPercent: metric.sentiment * 100,
    fill: metric.sentiment >= 0.7 ? '#22c55e' : metric.sentiment >= 0.5 ? '#eab308' : '#ef4444'
  }));

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-background border border-border rounded-lg p-3 shadow-lg">
          <p className="font-medium">{data.platform}</p>
          <p className="text-sm">Mentions: {data.mentions.toLocaleString()}</p>
          <p className="text-sm">Sentiment: {(data.sentiment * 100).toFixed(1)}%</p>
          <p className="text-sm">Engagement: {data.engagement.toLocaleString()}</p>
          <p className="text-sm">Growth: {data.growth > 0 ? '+' : ''}{data.growth}%</p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="space-y-6">
      {/* Platform Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {socialMetrics.map((metric) => {
          const TrendIcon = getTrendIcon(metric.growth);
          return (
            <Card key={metric.platform}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">{metric.platform}</CardTitle>
                <MessageSquare className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent className="space-y-3">
                <div>
                  <div className="text-2xl font-bold">{metric.mentions.toLocaleString()}</div>
                  <p className="text-xs text-muted-foreground">Total mentions</p>
                </div>
                
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span>Sentiment</span>
                    <Badge variant={metric.sentiment >= 0.7 ? "default" : metric.sentiment >= 0.5 ? "secondary" : "destructive"}>
                      {getSentimentLevel(metric.sentiment)}
                    </Badge>
                  </div>
                  <Progress value={metric.sentiment * 100} className="h-2" />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <div className="flex items-center space-x-1">
                      <Heart className="h-3 w-3 text-muted-foreground" />
                      <span className="text-sm">{metric.engagement.toLocaleString()}</span>
                    </div>
                    <p className="text-xs text-muted-foreground">Engagement</p>
                  </div>
                  <div className="flex items-center space-x-1">
                    <TrendIcon className={`h-3 w-3 ${getTrendColor(metric.growth)}`} />
                    <span className={`text-sm ${getTrendColor(metric.growth)}`}>
                      {metric.growth > 0 ? '+' : ''}{metric.growth}%
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Platform Comparison Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Mentions by Platform</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={socialMetrics} layout="horizontal">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" fontSize={12} />
                <YAxis dataKey="platform" type="category" width={80} fontSize={12} />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="mentions" fill="#3b82f6" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Sentiment Score by Platform</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <RadialBarChart cx="50%" cy="50%" innerRadius="20%" outerRadius="80%" data={radialData}>
                <RadialBar
                  minAngle={15}
                  clockWise
                  dataKey="sentimentPercent"
                  cornerRadius={10}
                  fill="#8884d8"
                />
                <Legend 
                  iconSize={10} 
                  wrapperStyle={{ fontSize: '12px' }} 
                  formatter={(value, entry) => `${entry.payload.platform}: ${entry.payload.sentimentPercent.toFixed(0)}%`}
                />
                <Tooltip content={<CustomTooltip />} />
              </RadialBarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Engagement Analysis */}
      <Card>
        <CardHeader>
          <CardTitle>Engagement Analysis</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={350}>
            <BarChart data={socialMetrics}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="platform" fontSize={12} />
              <YAxis fontSize={12} />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="engagement" fill="#10b981" name="Total Engagement" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Growth Metrics */}
      <Card>
        <CardHeader>
          <CardTitle>Growth Rates by Platform</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {socialMetrics
              .sort((a, b) => b.growth - a.growth)
              .map((metric) => {
                const TrendIcon = getTrendIcon(metric.growth);
                return (
                  <div key={metric.platform} className="flex items-center justify-between p-3 rounded-lg border">
                    <div className="flex items-center space-x-3">
                      <Share2 className="h-5 w-5 text-muted-foreground" />
                      <div>
                        <p className="font-medium">{metric.platform}</p>
                        <p className="text-sm text-muted-foreground">
                          {metric.mentions.toLocaleString()} mentions
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <TrendIcon className={`h-4 w-4 ${getTrendColor(metric.growth)}`} />
                      <span className={`font-medium ${getTrendColor(metric.growth)}`}>
                        {metric.growth > 0 ? '+' : ''}{metric.growth}%
                      </span>
                    </div>
                  </div>
                );
              })}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}