import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import { TrendingUp, TrendingDown, Users, MessageSquare, Globe } from "lucide-react";
import { overviewMetrics, recentAlerts } from "../lib/mock-data";

export function DashboardOverview() {
  const getSentimentColor = (sentiment: number) => {
    if (sentiment >= 0.7) return "text-green-600";
    if (sentiment >= 0.5) return "text-yellow-600";
    return "text-red-600";
  };

  const getSentimentBadgeVariant = (sentiment: number) => {
    if (sentiment >= 0.7) return "default";
    if (sentiment >= 0.5) return "secondary";
    return "destructive";
  };

  return (
    <div className="space-y-6">
      {/* Key Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Mentions</CardTitle>
            <MessageSquare className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{overviewMetrics.totalMentions.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">Last 30 days</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Sentiment</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${getSentimentColor(overviewMetrics.avgSentiment)}`}>
              {(overviewMetrics.avgSentiment * 100).toFixed(0)}%
            </div>
            <div className="flex items-center space-x-1">
              <TrendingUp className="h-3 w-3 text-green-500" />
              <p className="text-xs text-green-600">{overviewMetrics.sentimentChange} from last week</p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Engagement Rate</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{overviewMetrics.engagementRate}%</div>
            <p className="text-xs text-muted-foreground">Across all platforms</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Topics</CardTitle>
            <Globe className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{overviewMetrics.topCountries.length}</div>
            <p className="text-xs text-muted-foreground">Top countries</p>
          </CardContent>
        </Card>
      </div>

      {/* Recent Alerts */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Alerts</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {recentAlerts.map((alert) => (
            <div key={alert.id} className="flex items-start space-x-3 p-3 rounded-lg border">
              <div className="flex-shrink-0">
                {alert.type === 'positive' && <TrendingUp className="h-5 w-5 text-green-500" />}
                {alert.type === 'negative' && <TrendingDown className="h-5 w-5 text-red-500" />}
                {alert.type === 'neutral' && <MessageSquare className="h-5 w-5 text-blue-500" />}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-foreground">{alert.message}</p>
                <div className="flex items-center space-x-2 mt-1">
                  <Badge variant={alert.impact === 'high' ? 'destructive' : 'secondary'} className="text-xs">
                    {alert.impact} impact
                  </Badge>
                  <span className="text-xs text-muted-foreground">
                    {new Date(alert.timestamp).toLocaleTimeString()}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>

      {/* Top Countries and Peak Hours */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Top Countries</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {overviewMetrics.topCountries.map((country, index) => (
                <div key={country} className="flex items-center justify-between">
                  <span className="text-sm">{country}</span>
                  <Badge variant="outline">#{index + 1}</Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Peak Activity Hours</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {overviewMetrics.peakHours.map((hour, index) => (
                <div key={hour} className="flex items-center justify-between">
                  <span className="text-sm">{hour}</span>
                  <div className="flex items-center space-x-2">
                    <div className="h-2 w-16 bg-primary rounded-full opacity-80" />
                    <span className="text-xs text-muted-foreground">High</span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}