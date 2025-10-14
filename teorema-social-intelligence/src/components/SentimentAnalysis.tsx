import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar
} from "recharts";
import { sentimentTrends } from "../lib/mock-data";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";

export function SentimentAnalysis() {
  // Calculate current sentiment distribution
  const latestData = sentimentTrends[sentimentTrends.length - 1];
  const sentimentDistribution = [
    { name: 'Positive', value: latestData.positive, color: '#22c55e' },
    { name: 'Neutral', value: latestData.neutral, color: '#6b7280' },
    { name: 'Negative', value: latestData.negative, color: '#ef4444' }
  ];

  const getSentimentTrend = () => {
    const current = sentimentTrends[sentimentTrends.length - 1].overall_score;
    const previous = sentimentTrends[sentimentTrends.length - 8].overall_score;
    const change = ((current - previous) / previous * 100).toFixed(1);
    
    if (current > previous) {
      return { icon: TrendingUp, color: 'text-green-600', change: `+${change}%` };
    } else if (current < previous) {
      return { icon: TrendingDown, color: 'text-red-600', change: `${change}%` };
    } else {
      return { icon: Minus, color: 'text-gray-600', change: '0%' };
    }
  };

  const trend = getSentimentTrend();
  const TrendIcon = trend.icon;

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-background border border-border rounded-lg p-3 shadow-lg">
          <p className="text-sm font-medium">{`Date: ${label}`}</p>
          <p className="text-sm text-green-600">{`Positive: ${payload.find((p: any) => p.dataKey === 'positive')?.value}%`}</p>
          <p className="text-sm text-gray-600">{`Neutral: ${payload.find((p: any) => p.dataKey === 'neutral')?.value}%`}</p>
          <p className="text-sm text-red-600">{`Negative: ${payload.find((p: any) => p.dataKey === 'negative')?.value}%`}</p>
          <p className="text-sm font-medium">{`Overall Score: ${payload.find((p: any) => p.dataKey === 'overall_score')?.value}`}</p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="space-y-6">
      {/* Sentiment Overview */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Current Sentiment Score</CardTitle>
          </CardHeader>
          <CardContent className="text-center">
            <div className="text-4xl font-bold text-green-600 mb-2">
              {(latestData.overall_score * 100).toFixed(0)}%
            </div>
            <div className="flex items-center justify-center space-x-1">
              <TrendIcon className={`h-4 w-4 ${trend.color}`} />
              <span className={`text-sm ${trend.color}`}>{trend.change} from last week</span>
            </div>
            <Badge variant="default" className="mt-2">Positive Trend</Badge>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Sentiment Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie
                  data={sentimentDistribution}
                  cx="50%"
                  cy="50%"
                  innerRadius={40}
                  outerRadius={70}
                  paddingAngle={2}
                  dataKey="value"
                >
                  {sentimentDistribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
            <div className="flex justify-center space-x-4 mt-2">
              {sentimentDistribution.map((item) => (
                <div key={item.name} className="flex items-center space-x-1">
                  <div 
                    className="w-3 h-3 rounded-full" 
                    style={{ backgroundColor: item.color }}
                  />
                  <span className="text-xs">{item.name}: {item.value}%</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Volume by Sentiment</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={[latestData]}>
                <XAxis dataKey="date" hide />
                <YAxis hide />
                <Tooltip />
                <Bar dataKey="positive" fill="#22c55e" name="Positive" />
                <Bar dataKey="neutral" fill="#6b7280" name="Neutral" />
                <Bar dataKey="negative" fill="#ef4444" name="Negative" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Sentiment Trends */}
      <Card>
        <CardHeader>
          <CardTitle>Sentiment Trends (Last 15 Days)</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={400}>
            <LineChart data={sentimentTrends}>
              <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
              <XAxis 
                dataKey="date" 
                fontSize={12}
                tickFormatter={(value) => new Date(value).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
              />
              <YAxis 
                fontSize={12}
                domain={[0, 100]}
              />
              <Tooltip content={<CustomTooltip />} />
              <Line 
                type="monotone" 
                dataKey="positive" 
                stroke="#22c55e" 
                strokeWidth={2}
                name="Positive"
                dot={{ fill: '#22c55e', strokeWidth: 2, r: 4 }}
              />
              <Line 
                type="monotone" 
                dataKey="neutral" 
                stroke="#6b7280" 
                strokeWidth={2}
                name="Neutral"
                dot={{ fill: '#6b7280', strokeWidth: 2, r: 4 }}
              />
              <Line 
                type="monotone" 
                dataKey="negative" 
                stroke="#ef4444" 
                strokeWidth={2}
                name="Negative"
                dot={{ fill: '#ef4444', strokeWidth: 2, r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Overall Sentiment Score Timeline */}
      <Card>
        <CardHeader>
          <CardTitle>Overall Sentiment Score Timeline</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={sentimentTrends}>
              <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
              <XAxis 
                dataKey="date"
                fontSize={12}
                tickFormatter={(value) => new Date(value).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
              />
              <YAxis 
                fontSize={12}
                domain={[0, 1]}
                tickFormatter={(value) => `${(value * 100).toFixed(0)}%`}
              />
              <Tooltip 
                labelFormatter={(label) => `Date: ${label}`}
                formatter={(value: number) => [`${(value * 100).toFixed(1)}%`, 'Sentiment Score']}
              />
              <Line 
                type="monotone" 
                dataKey="overall_score" 
                stroke="#3b82f6" 
                strokeWidth={3}
                dot={{ fill: '#3b82f6', strokeWidth: 2, r: 5 }}
                activeDot={{ r: 7, stroke: '#3b82f6', strokeWidth: 2 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  );
}