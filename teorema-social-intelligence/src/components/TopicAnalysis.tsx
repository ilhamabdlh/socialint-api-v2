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
  TreemapChart,
  Treemap,
  Cell,
  ScatterChart,
  Scatter
} from "recharts";
import { topicAnalysis } from "../lib/mock-data";
import { TrendingUp, TrendingDown, Minus, MessageCircle, Hash } from "lucide-react";

export function TopicAnalysis() {
  const getTrendIcon = (trend: 'up' | 'down' | 'stable') => {
    switch (trend) {
      case 'up': return TrendingUp;
      case 'down': return TrendingDown;
      default: return Minus;
    }
  };

  const getTrendColor = (trend: 'up' | 'down' | 'stable') => {
    switch (trend) {
      case 'up': return "text-green-600";
      case 'down': return "text-red-600";
      default: return "text-gray-600";
    }
  };

  const getSentimentColor = (sentiment: number) => {
    if (sentiment >= 0.7) return "bg-green-500";
    if (sentiment >= 0.5) return "bg-yellow-500";
    return "bg-red-500";
  };

  const getSentimentBadgeVariant = (sentiment: number) => {
    if (sentiment >= 0.7) return "default";
    if (sentiment >= 0.5) return "secondary";
    return "destructive";
  };

  // Transform data for treemap
  const treemapData = topicAnalysis.map((topic, index) => ({
    name: topic.topic,
    size: topic.mentions,
    sentiment: topic.sentiment,
    fill: topic.sentiment >= 0.7 ? '#22c55e' : topic.sentiment >= 0.5 ? '#eab308' : '#ef4444'
  }));

  // Transform data for scatter plot (sentiment vs mentions)
  const scatterData = topicAnalysis.map(topic => ({
    x: topic.mentions,
    y: topic.sentiment * 100,
    topic: topic.topic,
    trend: topic.trend
  }));

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-background border border-border rounded-lg p-3 shadow-lg">
          <p className="font-medium">{data.topic || data.name}</p>
          <p className="text-sm">Mentions: {(data.mentions || data.size || data.x)?.toLocaleString()}</p>
          <p className="text-sm">Sentiment: {((data.sentiment || data.y / 100) * 100).toFixed(1)}%</p>
          {data.trend && <p className="text-sm">Trend: {data.trend}</p>}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="space-y-6">
      {/* Topic Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {topicAnalysis.slice(0, 6).map((topic) => {
          const TrendIcon = getTrendIcon(topic.trend);
          return (
            <Card key={topic.topic}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium truncate">{topic.topic}</CardTitle>
                <Hash className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent className="space-y-3">
                <div>
                  <div className="text-xl font-bold">{topic.mentions.toLocaleString()}</div>
                  <p className="text-xs text-muted-foreground">Total mentions</p>
                </div>
                
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span>Sentiment</span>
                    <Badge variant={getSentimentBadgeVariant(topic.sentiment)}>
                      {(topic.sentiment * 100).toFixed(0)}%
                    </Badge>
                  </div>
                  <Progress value={topic.sentiment * 100} className="h-2" />
                </div>

                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-1">
                    <TrendIcon className={`h-3 w-3 ${getTrendColor(topic.trend)}`} />
                    <span className={`text-sm capitalize ${getTrendColor(topic.trend)}`}>
                      {topic.trend}
                    </span>
                  </div>
                  <MessageCircle className="h-4 w-4 text-muted-foreground" />
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Topic Mentions Chart */}
      <Card>
        <CardHeader>
          <CardTitle>Topic Mentions Volume</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={topicAnalysis} layout="horizontal">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" fontSize={12} />
              <YAxis 
                dataKey="topic" 
                type="category" 
                width={120} 
                fontSize={12}
                tickFormatter={(value) => value.length > 15 ? `${value.substring(0, 15)}...` : value}
              />
              <Tooltip content={<CustomTooltip />} />
              <Bar 
                dataKey="mentions" 
                fill="#3b82f6"
                radius={[0, 4, 4, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Topic Treemap */}
      <Card>
        <CardHeader>
          <CardTitle>Topic Distribution by Volume</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={400}>
            <Treemap
              data={treemapData}
              dataKey="size"
              aspectRatio={4/3}
              stroke="#fff"
              strokeWidth={2}
            >
              <Tooltip content={<CustomTooltip />} />
            </Treemap>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Sentiment vs Volume Scatter */}
      <Card>
        <CardHeader>
          <CardTitle>Topic Sentiment vs Volume Analysis</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={400}>
            <ScatterChart data={scatterData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                type="number" 
                dataKey="x" 
                name="Mentions" 
                fontSize={12}
                tickFormatter={(value) => value.toLocaleString()}
              />
              <YAxis 
                type="number" 
                dataKey="y" 
                name="Sentiment" 
                fontSize={12}
                domain={[0, 100]}
                tickFormatter={(value) => `${value}%`}
              />
              <Tooltip content={<CustomTooltip />} />
              <Scatter 
                name="Topics" 
                dataKey="y" 
                fill="#8884d8"
              >
                {scatterData.map((entry, index) => (
                  <Cell 
                    key={`cell-${index}`} 
                    fill={entry.y >= 70 ? '#22c55e' : entry.y >= 50 ? '#eab308' : '#ef4444'} 
                  />
                ))}
              </Scatter>
            </ScatterChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Trending Topics */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-green-600">📈 Trending Up</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {topicAnalysis
              .filter(topic => topic.trend === 'up')
              .sort((a, b) => b.mentions - a.mentions)
              .slice(0, 5)
              .map((topic) => (
                <div key={topic.topic} className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium">{topic.topic}</p>
                    <p className="text-xs text-muted-foreground">
                      {topic.mentions.toLocaleString()} mentions
                    </p>
                  </div>
                  <Badge variant="default">{(topic.sentiment * 100).toFixed(0)}%</Badge>
                </div>
              ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-gray-600">➡️ Stable</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {topicAnalysis
              .filter(topic => topic.trend === 'stable')
              .sort((a, b) => b.mentions - a.mentions)
              .slice(0, 5)
              .map((topic) => (
                <div key={topic.topic} className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium">{topic.topic}</p>
                    <p className="text-xs text-muted-foreground">
                      {topic.mentions.toLocaleString()} mentions
                    </p>
                  </div>
                  <Badge variant="secondary">{(topic.sentiment * 100).toFixed(0)}%</Badge>
                </div>
              ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-red-600">📉 Trending Down</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {topicAnalysis
              .filter(topic => topic.trend === 'down')
              .sort((a, b) => b.mentions - a.mentions)
              .slice(0, 5)
              .map((topic) => (
                <div key={topic.topic} className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium">{topic.topic}</p>
                    <p className="text-xs text-muted-foreground">
                      {topic.mentions.toLocaleString()} mentions
                    </p>
                  </div>
                  <Badge variant="destructive">{(topic.sentiment * 100).toFixed(0)}%</Badge>
                </div>
              ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}