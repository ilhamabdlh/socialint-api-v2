import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { Separator } from "./ui/separator";
import { Campaign, Brand, Content } from "../lib/mock-data";
import { 
  ExternalLink, 
  Link, 
  Tag, 
  Users, 
  Calendar, 
  Target,
  Building2,
  FileText,
  Globe
} from "lucide-react";

interface EntityDetailsProps {
  entity: Campaign | Brand | Content;
  entityType: 'campaign' | 'brand' | 'content';
}

export function EntityDetails({ entity, entityType }: EntityDetailsProps) {
  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'active': return 'bg-blue-100 text-blue-800 border-blue-300';
      case 'paused': return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      case 'completed': return 'bg-green-100 text-green-800 border-green-300';
      case 'draft': return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      default: return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  const renderCampaignDetails = (campaign: Campaign) => (
    <div className="space-y-6">
      {/* Campaign Info */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Target className="h-5 w-5" />
            Campaign Information
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <h4 className="font-medium mb-2">Type</h4>
              <Badge variant="outline" className="capitalize">
                {campaign.type.replace('_', ' ')}
              </Badge>
            </div>
            <div>
              <h4 className="font-medium mb-2">Status</h4>
              <Badge variant="outline" className={`capitalize ${getStatusColor(campaign.status)}`}>
                {campaign.status}
              </Badge>
            </div>
            <div>
              <h4 className="font-medium mb-2">Start Date</h4>
              <p className="text-sm">{campaign.start_date}</p>
            </div>
            <div>
              <h4 className="font-medium mb-2">End Date</h4>
              <p className="text-sm">{campaign.end_date}</p>
            </div>
          </div>
          
          <Separator />
          
          <div>
            <h4 className="font-medium mb-2">Target Audience</h4>
            <div className="flex flex-wrap gap-2">
              {campaign.target_audience.map((audience, index) => (
                <Badge key={index} variant="secondary">
                  {audience}
                </Badge>
              ))}
            </div>
          </div>
          
          <div>
            <h4 className="font-medium mb-2">Platforms</h4>
            <div className="flex flex-wrap gap-2">
              {campaign.platforms.map((platform, index) => (
                <Badge key={index} variant="outline">
                  {platform}
                </Badge>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Post URLs */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Link className="h-5 w-5" />
            Post URLs ({campaign.postUrls.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {campaign.postUrls.map((url, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-muted rounded-lg">
                <div className="flex-1">
                  <p className="text-sm font-mono break-all">{url}</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    Platform: {getPlatformFromUrl(url)}
                  </p>
                </div>
                <Button size="sm" variant="outline" onClick={() => window.open(url, '_blank')}>
                  <ExternalLink className="h-4 w-4" />
                </Button>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );

  const renderBrandDetails = (brand: Brand) => (
    <div className="space-y-6">
      {/* Brand Info */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Building2 className="h-5 w-5" />
            Brand Information
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <h4 className="font-medium mb-2">Category</h4>
              <Badge variant="outline">{brand.category}</Badge>
            </div>
            <div>
              <h4 className="font-medium mb-2">Status</h4>
              <Badge variant="outline" className="capitalize">
                {brand.status}
              </Badge>
            </div>
            <div>
              <h4 className="font-medium mb-2">Created Date</h4>
              <p className="text-sm">{brand.created_date}</p>
            </div>
          </div>
          
          <Separator />
          
          <div>
            <h4 className="font-medium mb-2">Competitors</h4>
            <div className="flex flex-wrap gap-2">
              {brand.competitors.map((competitor, index) => (
                <Badge key={index} variant="secondary">
                  {competitor}
                </Badge>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Keywords */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Tag className="h-5 w-5" />
            Keywords ({brand.keywords.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            {brand.keywords.map((keyword, index) => (
              <Badge key={index} variant="outline" className="text-sm">
                {keyword}
              </Badge>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Post URLs */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Link className="h-5 w-5" />
            Post URLs ({brand.postUrls.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {brand.postUrls.map((url, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-muted rounded-lg">
                <div className="flex-1">
                  <p className="text-sm font-mono break-all">{url}</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    Platform: {getPlatformFromUrl(url)}
                  </p>
                </div>
                <Button size="sm" variant="outline" onClick={() => window.open(url, '_blank')}>
                  <ExternalLink className="h-4 w-4" />
                </Button>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );

  const renderContentDetails = (content: Content) => (
    <div className="space-y-6">
      {/* Content Info */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Content Information
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <h4 className="font-medium mb-2">Platform</h4>
              <Badge variant="outline">{content.platform}</Badge>
            </div>
            <div>
              <h4 className="font-medium mb-2">Content Type</h4>
              <Badge variant="outline" className="capitalize">
                {content.content_type}
              </Badge>
            </div>
            <div>
              <h4 className="font-medium mb-2">Author</h4>
              <p className="text-sm">{content.author}</p>
            </div>
            <div>
              <h4 className="font-medium mb-2">Publish Date</h4>
              <p className="text-sm">{content.publish_date}</p>
            </div>
            <div>
              <h4 className="font-medium mb-2">Status</h4>
              <Badge variant="outline" className="capitalize">
                {content.status}
              </Badge>
            </div>
          </div>
          
          <Separator />
          
          <div>
            <h4 className="font-medium mb-2">Tags</h4>
            <div className="flex flex-wrap gap-2">
              {content.tags.map((tag, index) => (
                <Badge key={index} variant="secondary">
                  {tag}
                </Badge>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Post URL */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Globe className="h-5 w-5" />
            Content URL
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between p-3 bg-muted rounded-lg">
            <div className="flex-1">
              <p className="text-sm font-mono break-all">{content.postUrl}</p>
              <p className="text-xs text-muted-foreground mt-1">
                Platform: {content.platform}
              </p>
            </div>
            <Button size="sm" variant="outline" onClick={() => window.open(content.postUrl, '_blank')}>
              <ExternalLink className="h-4 w-4" />
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );

  // Helper function to extract platform from URL
  const getPlatformFromUrl = (url: string): string => {
    if (url.includes('twitter.com') || url.includes('x.com')) return 'Twitter/X';
    if (url.includes('facebook.com')) return 'Facebook';
    if (url.includes('instagram.com')) return 'Instagram';
    if (url.includes('linkedin.com')) return 'LinkedIn';
    if (url.includes('youtube.com')) return 'YouTube';
    if (url.includes('reddit.com')) return 'Reddit';
    if (url.includes('tiktok.com')) return 'TikTok';
    return 'Unknown';
  };

  switch (entityType) {
    case 'campaign':
      return renderCampaignDetails(entity as Campaign);
    case 'brand':
      return renderBrandDetails(entity as Brand);
    case 'content':
      return renderContentDetails(entity as Content);
    default:
      return null;
  }
}