import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import { Progress } from "./ui/progress";
import { 
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  Cell,
  PieChart,
  Pie,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar
} from "recharts";
import { keywordClusters } from "../lib/mock-data";
import { Hash, TrendingUp, Link, Search } from "lucide-react";

export function KeywordClustering() {
  const getSentimentColor = (sentiment: number) => {
    if (sentiment >= 0.7) return "#22c55e";
    if (sentiment >= 0.5) return "#eab308";
    return "#ef4444";
  };

  const getSentimentBadgeVariant = (sentiment: number) => {
    if (sentiment >= 0.7) return "default";
    if (sentiment >= 0.5) return "secondary";
    return "destructive";
  };

  // Transform data for scatter plot (frequency vs sentiment)
  const scatterData = keywordClusters.map(keyword => ({
    x: keyword.frequency,
    y: keyword.sentiment * 100,
    keyword: keyword.keyword,
    relatedCount: keyword.related_terms.length
  }));

  // Transform data for radar chart (top 6 keywords)
  const radarData = keywordClusters
    .slice(0, 6)
    .map(keyword => ({
      keyword: keyword.keyword,
      frequency: (keyword.frequency / Math.max(...keywordClusters.map(k => k.frequency))) * 100,
      sentiment: keyword.sentiment * 100,
      related: keyword.related_terms.length * 25
    }));

  // Data for frequency distribution
  const frequencyData = keywordClusters
    .sort((a, b) => b.frequency - a.frequency)
    .slice(0, 10);

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-background border border-border rounded-lg p-3 shadow-lg">
          <p className="font-medium">{data.keyword}</p>
          <p className="text-sm">Frequency: {(data.frequency || data.x)?.toLocaleString()}</p>
          <p className="text-sm">Sentiment: {((data.sentiment || data.y / 100) * 100).toFixed(1)}%</p>
          <p className="text-sm">Related Terms: {data.relatedCount || data.related_terms?.length}</p>
        </div>
      );
    }
    return null;
  };

  const CustomRadarTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-background border border-border rounded-lg p-3 shadow-lg">
          <p className="font-medium">{label}</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} className="text-sm" style={{ color: entry.color }}>
              {entry.dataKey}: {entry.value.toFixed(1)}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="space-y-6">
      {/* Keyword Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {keywordClusters.slice(0, 4).map((keyword) => (
          <Card key={keyword.keyword}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium capitalize">
                {keyword.keyword.replace('-', ' ')}
              </CardTitle>
              <Hash className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent className="space-y-3">
              <div>
                <div className="text-xl font-bold">{keyword.frequency.toLocaleString()}</div>
                <p className="text-xs text-muted-foreground">Total mentions</p>
              </div>
              
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span>Sentiment</span>
                  <Badge variant={getSentimentBadgeVariant(keyword.sentiment)}>
                    {(keyword.sentiment * 100).toFixed(0)}%
                  </Badge>
                </div>
                <Progress value={keyword.sentiment * 100} className="h-2" />
              </div>

              <div className="flex items-center justify-between text-sm">
                <div className="flex items-center space-x-1">
                  <Link className="h-3 w-3 text-muted-foreground" />
                  <span>{keyword.related_terms.length} related</span>
                </div>
                <TrendingUp className="h-4 w-4 text-green-500" />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Keyword Frequency vs Sentiment Scatter */}
      <Card>
        <CardHeader>
          <CardTitle>Keyword Performance Analysis</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={400}>
            <ScatterChart data={scatterData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                type="number" 
                dataKey="x" 
                name="Frequency" 
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
              <Scatter name="Keywords" dataKey="y" fill="#8884d8">
                {scatterData.map((entry, index) => (
                  <Cell 
                    key={`cell-${index}`} 
                    fill={getSentimentColor(entry.y / 100)} 
                  />
                ))}
              </Scatter>
            </ScatterChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Top Keywords by Frequency */}
      <Card>
        <CardHeader>
          <CardTitle>Top Keywords by Frequency</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={350}>
            <BarChart data={frequencyData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="keyword" 
                fontSize={12}
                angle={-45}
                textAnchor="end"
                height={80}
                tickFormatter={(value) => value.replace('-', ' ')}
              />
              <YAxis fontSize={12} />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="frequency" radius={[4, 4, 0, 0]}>
                {frequencyData.map((entry, index) => (
                  <Cell 
                    key={`cell-${index}`} 
                    fill={getSentimentColor(entry.sentiment)} 
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Keyword Radar Analysis */}
      <Card>
        <CardHeader>
          <CardTitle>Keyword Multi-Dimensional Analysis</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={400}>
            <RadarChart data={radarData}>
              <PolarGrid />
              <PolarAngleAxis dataKey="keyword" fontSize={12} />
              <PolarRadiusAxis 
                angle={90} 
                domain={[0, 100]} 
                fontSize={10}
                tick={false}
              />
              <Radar
                name="Frequency"
                dataKey="frequency"
                stroke="#3b82f6"
                fill="#3b82f6"
                fillOpacity={0.3}
                strokeWidth={2}
              />
              <Radar
                name="Sentiment"
                dataKey="sentiment"
                stroke="#22c55e"
                fill="#22c55e"
                fillOpacity={0.3}
                strokeWidth={2}
              />
              <Radar
                name="Related Terms"
                dataKey="related"
                stroke="#eab308"
                fill="#eab308"
                fillOpacity={0.3}
                strokeWidth={2}
              />
              <Tooltip content={<CustomRadarTooltip />} />
            </RadarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Related Terms Analysis */}
      <Card>
        <CardHeader>
          <CardTitle>Keyword Relationships</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            {keywordClusters.slice(0, 6).map((keyword) => (
              <div key={keyword.keyword} className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Search className="h-4 w-4 text-muted-foreground" />
                    <h4 className="font-medium capitalize">
                      {keyword.keyword.replace('-', ' ')}
                    </h4>
                    <Badge variant="outline">
                      {keyword.frequency.toLocaleString()} mentions
                    </Badge>
                  </div>
                  <Badge variant={getSentimentBadgeVariant(keyword.sentiment)}>
                    {(keyword.sentiment * 100).toFixed(0)}% sentiment
                  </Badge>
                </div>
                <div className="flex flex-wrap gap-2">
                  {keyword.related_terms.map((term) => (
                    <Badge key={term} variant="secondary" className="text-xs">
                      {term}
                    </Badge>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Sentiment Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Sentiment Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={[
                    { 
                      name: 'Positive', 
                      value: keywordClusters.filter(k => k.sentiment >= 0.7).length, 
                      fill: '#22c55e' 
                    },
                    { 
                      name: 'Neutral', 
                      value: keywordClusters.filter(k => k.sentiment >= 0.5 && k.sentiment < 0.7).length, 
                      fill: '#eab308' 
                    },
                    { 
                      name: 'Negative', 
                      value: keywordClusters.filter(k => k.sentiment < 0.5).length, 
                      fill: '#ef4444' 
                    }
                  ]}
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  dataKey="value"
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                >
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Keyword Statistics</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="text-center">
              <div className="text-3xl font-bold">{keywordClusters.length}</div>
              <p className="text-sm text-muted-foreground">Total Keywords</p>
            </div>
            
            <div className="grid grid-cols-2 gap-4 text-center">
              <div>
                <div className="text-xl font-bold text-green-600">
                  {keywordClusters.filter(k => k.sentiment >= 0.7).length}
                </div>
                <p className="text-xs text-muted-foreground">Positive Keywords</p>
              </div>
              <div>
                <div className="text-xl font-bold text-red-600">
                  {keywordClusters.filter(k => k.sentiment < 0.5).length}
                </div>
                <p className="text-xs text-muted-foreground">Negative Keywords</p>
              </div>
            </div>

            <div className="text-center">
              <div className="text-xl font-bold">
                {Math.round(keywordClusters.reduce((acc, k) => acc + k.related_terms.length, 0) / keywordClusters.length)}
              </div>
              <p className="text-xs text-muted-foreground">Avg Related Terms</p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}