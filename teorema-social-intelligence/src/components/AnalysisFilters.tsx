import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select";
import { Badge } from "./ui/badge";
import { Calendar, Filter, RotateCcw } from "lucide-react";
import { Campaign, Brand, Content } from "../lib/mock-data";

export interface FilterState {
  dateRange: {
    start: string;
    end: string;
  };
  platforms: string[];
  posts: string[];
  keywords?: string[];
  entitySpecific?: Record<string, any>;
}

interface AnalysisFiltersProps {
  entity: Campaign | Brand | Content;
  entityType: 'campaign' | 'brand' | 'content';
  filters: FilterState;
  onFiltersChange: (filters: FilterState) => void;
}

export function AnalysisFilters({ entity, entityType, filters, onFiltersChange }: AnalysisFiltersProps) {
  const [localFilters, setLocalFilters] = useState<FilterState>(filters);
  
  // Get the last 30 days as default range
  const getDefaultDateRange = () => {
    const end = new Date();
    const start = new Date();
    start.setDate(start.getDate() - 30);
    
    return {
      start: start.toISOString().split('T')[0],
      end: end.toISOString().split('T')[0]
    };
  };

  // Initialize with default values if not set
  useEffect(() => {
    if (!localFilters.dateRange.start || !localFilters.dateRange.end) {
      const defaultRange = getDefaultDateRange();
      setLocalFilters(prev => ({
        ...prev,
        dateRange: defaultRange
      }));
    }
  }, []);

  const handleFilterChange = (key: keyof FilterState, value: any) => {
    const newFilters = { ...localFilters, [key]: value };
    setLocalFilters(newFilters);
    onFiltersChange(newFilters);
  };

  const handleArrayFilterChange = (key: 'platforms' | 'posts' | 'keywords', item: string, isAdd: boolean) => {
    const currentArray = localFilters[key] || [];
    let newArray: string[];
    
    if (isAdd) {
      newArray = [...currentArray, item];
    } else {
      newArray = currentArray.filter(i => i !== item);
    }
    
    handleFilterChange(key, newArray);
  };

  const resetFilters = () => {
    const defaultFilters: FilterState = {
      dateRange: getDefaultDateRange(),
      platforms: [],
      posts: [],
      ...(entityType === 'brand' && { keywords: [] })
    };
    setLocalFilters(defaultFilters);
    onFiltersChange(defaultFilters);
  };

  // Get available options based on entity type
  const getAvailablePlatforms = () => {
    switch (entityType) {
      case 'campaign':
        return (entity as Campaign).platforms;
      case 'brand':
        // Extract platforms from post URLs
        const brand = entity as Brand;
        const platforms = new Set<string>();
        brand.postUrls.forEach(url => {
          if (url.includes('twitter.com') || url.includes('x.com')) platforms.add('Twitter/X');
          if (url.includes('facebook.com')) platforms.add('Facebook');
          if (url.includes('instagram.com')) platforms.add('Instagram');
          if (url.includes('linkedin.com')) platforms.add('LinkedIn');
          if (url.includes('youtube.com')) platforms.add('YouTube');
          if (url.includes('reddit.com')) platforms.add('Reddit');
          if (url.includes('tiktok.com')) platforms.add('TikTok');
        });
        return Array.from(platforms);
      case 'content':
        return [(entity as Content).platform];
    }
  };

  const getAvailablePosts = () => {
    switch (entityType) {
      case 'campaign':
        return (entity as Campaign).postUrls;
      case 'brand':
        return (entity as Brand).postUrls;
      case 'content':
        return [(entity as Content).postUrl];
    }
  };

  const getAvailableKeywords = () => {
    if (entityType === 'brand') {
      return (entity as Brand).keywords;
    }
    return [];
  };

  const availablePlatforms = getAvailablePlatforms();
  const availablePosts = getAvailablePosts();
  const availableKeywords = getAvailableKeywords();

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Filter className="h-5 w-5" />
            Analysis Filters
          </CardTitle>
          <Button variant="outline" size="sm" onClick={resetFilters}>
            <RotateCcw className="h-4 w-4 mr-2" />
            Reset
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Date Range */}
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <Calendar className="h-4 w-4" />
            <h4 className="font-medium">Date Range</h4>
          </div>
          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="text-xs text-muted-foreground">Start Date</label>
              <Input
                type="date"
                value={localFilters.dateRange.start}
                onChange={(e) => handleFilterChange('dateRange', {
                  ...localFilters.dateRange,
                  start: e.target.value
                })}
              />
            </div>
            <div>
              <label className="text-xs text-muted-foreground">End Date</label>
              <Input
                type="date"
                value={localFilters.dateRange.end}
                onChange={(e) => handleFilterChange('dateRange', {
                  ...localFilters.dateRange,
                  end: e.target.value
                })}
              />
            </div>
          </div>
        </div>

        {/* Platforms Filter */}
        <div className="space-y-3">
          <h4 className="font-medium">Platforms</h4>
          <div className="flex flex-wrap gap-2">
            {availablePlatforms.map((platform) => {
              const isSelected = localFilters.platforms.includes(platform);
              return (
                <Badge
                  key={platform}
                  variant={isSelected ? "default" : "outline"}
                  className="cursor-pointer"
                  onClick={() => handleArrayFilterChange('platforms', platform, !isSelected)}
                >
                  {platform}
                </Badge>
              );
            })}
          </div>
          {localFilters.platforms.length === 0 && (
            <p className="text-xs text-muted-foreground">All platforms selected</p>
          )}
        </div>

        {/* Posts Filter */}
        <div className="space-y-3">
          <h4 className="font-medium">Post URLs</h4>
          <div className="space-y-2 max-h-32 overflow-y-auto">
            {availablePosts.map((post, index) => {
              const isSelected = localFilters.posts.includes(post);
              const shortUrl = post.length > 50 ? post.substring(0, 50) + '...' : post;
              return (
                <div key={index} className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={isSelected}
                    onChange={(e) => handleArrayFilterChange('posts', post, e.target.checked)}
                    className="rounded"
                  />
                  <span className="text-xs">{shortUrl}</span>
                </div>
              );
            })}
          </div>
          {localFilters.posts.length === 0 && (
            <p className="text-xs text-muted-foreground">All posts selected</p>
          )}
        </div>

        {/* Keywords Filter (Brand only) */}
        {entityType === 'brand' && (
          <div className="space-y-3">
            <h4 className="font-medium">Keywords</h4>
            <div className="flex flex-wrap gap-2">
              {availableKeywords.map((keyword) => {
                const isSelected = (localFilters.keywords || []).includes(keyword);
                return (
                  <Badge
                    key={keyword}
                    variant={isSelected ? "default" : "outline"}
                    className="cursor-pointer"
                    onClick={() => handleArrayFilterChange('keywords', keyword, !isSelected)}
                  >
                    {keyword}
                  </Badge>
                );
              })}
            </div>
            {(localFilters.keywords || []).length === 0 && (
              <p className="text-xs text-muted-foreground">All keywords selected</p>
            )}
          </div>
        )}

        {/* Active Filters Summary */}
        <div className="pt-4 border-t">
          <h4 className="font-medium mb-2">Active Filters</h4>
          <div className="space-y-1 text-xs text-muted-foreground">
            <p>Date: {localFilters.dateRange.start} to {localFilters.dateRange.end}</p>
            <p>Platforms: {localFilters.platforms.length === 0 ? 'All' : localFilters.platforms.join(', ')}</p>
            <p>Posts: {localFilters.posts.length === 0 ? 'All' : `${localFilters.posts.length} selected`}</p>
            {entityType === 'brand' && (
              <p>Keywords: {(localFilters.keywords || []).length === 0 ? 'All' : localFilters.keywords?.join(', ')}</p>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}