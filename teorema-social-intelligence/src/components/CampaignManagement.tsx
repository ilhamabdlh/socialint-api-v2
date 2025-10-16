import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Textarea } from "./ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select";
import { Badge } from "./ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogTrigger } from "./ui/dialog";
import { Label } from "./ui/label";
import { Campaign, campaigns as mockCampaigns } from "../lib/mock-data";
import { Plus, Search, Eye, Edit, Trash2, Calendar, Target, Users, Loader2, Play } from "lucide-react";
import { campaignAPI, type CampaignCreate, type CampaignResponse } from "../lib/api-client";
import { toast } from "sonner";
import { AnalysisNotification } from "./ui/analysis-notification";

interface CampaignManagementProps {
  onSelectCampaign: (campaign: Campaign) => void;
}

export function CampaignManagement({ onSelectCampaign }: CampaignManagementProps) {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [filterStatus, setFilterStatus] = useState("all");
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [editingCampaign, setEditingCampaign] = useState<Campaign | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingList, setIsLoadingList] = useState(true);
  const [analyzingCampaignId, setAnalyzingCampaignId] = useState<string | null>(null);
  const [notificationState, setNotificationState] = useState<{
    isOpen: boolean;
    campaignName: string;
    type: 'started' | 'completed' | 'failed';
  }>({
    isOpen: false,
    campaignName: '',
    type: 'started'
  });

  const handleCloseNotification = () => {
    console.log('🔧 handleCloseNotification called');
    setNotificationState({
      isOpen: false,
      campaignName: '',
      type: 'started'
    });
    console.log('🔧 Notification state updated to closed');
  };

  // Platform options with proper case values
  const platformOptions = [
    { value: 'tiktok', label: 'TikTok' },
    { value: 'instagram', label: 'Instagram' },
    { value: 'twitter', label: 'X/Twitter' },
    { value: 'youtube', label: 'YouTube' }
  ];

  // Handle platform selection
  const handlePlatformChange = (platform: string, checked: boolean) => {
    if (checked) {
      setFormData({
        ...formData,
        selectedPlatforms: [...formData.selectedPlatforms, platform],
        platformUrls: {
          ...formData.platformUrls,
          [platform]: formData.platformUrls[platform] || ''
        }
      });
    } else {
      setFormData({
        ...formData,
        selectedPlatforms: formData.selectedPlatforms.filter(p => p !== platform),
        platformUrls: {
          ...formData.platformUrls,
          [platform]: ''
        }
      });
    }
  };

  // Handle platform URL changes
  const handlePlatformUrlChange = (platform: string, urls: string) => {
    setFormData({
      ...formData,
      platformUrls: {
        ...formData.platformUrls,
        [platform]: urls
      }
    });
  };

  // Get max date (1 year from now)
  const getMaxDate = () => {
    const maxDate = new Date();
    maxDate.setFullYear(maxDate.getFullYear() + 1);
    return maxDate.toISOString().split('T')[0];
  };

  // Form state for creating/editing campaigns
  const [formData, setFormData] = useState({
    name: "",
    description: "",
    brand_name: "hufagripp",
    keywords: "",
    postUrls: "",
    type: "product_launch" as Campaign['type'],
    status: "draft" as Campaign['status'],
    start_date: "",
    end_date: "",
    target_audience: "",
    platforms: "",
    selectedPlatforms: [] as string[],
    platformUrls: {} as Record<string, string>
  });

  // Load campaigns from API on mount
  useEffect(() => {
    loadCampaigns();
  }, [filterStatus]);

  const loadCampaigns = async (showLoading: boolean = true) => {
    try {
      if (showLoading) {
        setIsLoadingList(true);
      }
      const params = filterStatus !== "all" ? { status: filterStatus } : undefined;
      const response = await campaignAPI.list(params);
      
      // Convert API response to Campaign format
      const convertedCampaigns: Campaign[] = response.map((c: CampaignResponse) => ({
        id: c.id,
        name: c.campaign_name,
        description: c.description,
        postUrls: [], // Will be populated from post_urls_count
        type: c.campaign_type as Campaign['type'],
        status: c.status as Campaign['status'],
        created_date: c.created_at.split('T')[0],
        start_date: c.start_date.split('T')[0],
        end_date: c.end_date.split('T')[0],
        target_audience: c.target_audiences,
        platforms: c.platforms
      }));
      
      setCampaigns(convertedCampaigns);
    } catch (error) {
      console.error('Error loading campaigns:', error);
      toast.error('Failed to load campaigns', {
        description: error instanceof Error ? error.message : 'Unknown error'
      });
      // Fallback to mock data if API fails
      setCampaigns(mockCampaigns);
    } finally {
      if (showLoading) {
        setIsLoadingList(false);
      }
    }
  };

  // Silent refresh function that doesn't show loading state
  const refreshCampaigns = async () => {
    await loadCampaigns(false);
  };

  const resetForm = () => {
    setFormData({
      name: "",
      description: "",
      brand_name: "hufagripp",
      keywords: "",
      postUrls: "",
      type: "product_launch",
      status: "draft",
      start_date: "",
      end_date: "",
      target_audience: "",
      platforms: "",
      selectedPlatforms: [],
      platformUrls: {}
    });
  };

  const handleCreate = async () => {
    try {
      setIsLoading(true);
      
      // Parse form data - combine all platform URLs
      const allUrls: string[] = [];
      Object.values(formData.platformUrls).forEach((urls: string) => {
        if (urls.trim()) {
          allUrls.push(...urls.split('\n').filter(url => url.trim()));
        }
      });
      
      const postUrls = allUrls.map(url => ({
        url: url.trim(),
        platform: 'tiktok', // Will be determined by URL analysis
        title: formData.name
      }));

      const campaignData: CampaignCreate = {
        campaign_name: formData.name,
        description: formData.description,
        campaign_type: formData.type,
        brand_name: formData.brand_name,
        keywords: formData.keywords.split(',').map(k => k.trim()).filter(k => k),
        target_audiences: formData.target_audience.split(',').map(a => a.trim()).filter(a => a),
        platforms: formData.selectedPlatforms as any,
        post_urls: postUrls,
        start_date: new Date(formData.start_date).toISOString(),
        end_date: new Date(formData.end_date).toISOString(),
        auto_analysis_enabled: true,
        analysis_frequency: "daily",
        tags: [formData.type],
        created_by: "dashboard_user"
      };

      await campaignAPI.create(campaignData);
      
      toast.success('Campaign created successfully!', {
        description: `${formData.name} has been created and will start on ${formData.start_date}`
      });
      
      setIsCreateDialogOpen(false);
      resetForm();
      loadCampaigns(); // Reload campaigns list
    } catch (error) {
      console.error('Error creating campaign:', error);
      toast.error('Failed to create campaign', {
        description: error instanceof Error ? error.message : 'Unknown error'
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleEdit = (campaign: Campaign) => {
    setEditingCampaign(campaign);
    setFormData({
      name: campaign.name,
      description: campaign.description,
      brand_name: "hufagripp",
      keywords: "",
      postUrls: campaign.postUrls.join('\n'),
      type: campaign.type,
      status: campaign.status,
      start_date: campaign.start_date,
      end_date: campaign.end_date,
      target_audience: campaign.target_audience.join(', '),
      platforms: campaign.platforms.join(', ')
    });
  };

  const handleUpdate = async () => {
    if (!editingCampaign) return;

    try {
      setIsLoading(true);

      const updateData = {
        description: formData.description,
        campaign_type: formData.type,
        status: formData.status as any,
        keywords: formData.keywords.split(',').map(k => k.trim()).filter(k => k),
        target_audiences: formData.target_audience.split(',').map(a => a.trim()).filter(a => a),
        platforms: formData.platforms.split(',').map(p => p.trim()).filter(p => p) as any,
        start_date: new Date(formData.start_date).toISOString(),
        end_date: new Date(formData.end_date).toISOString(),
        tags: [formData.type]
      };

      await campaignAPI.update(editingCampaign.name, updateData);
      
      toast.success('Campaign updated successfully!', {
        description: `${editingCampaign.name} has been updated`
      });
      
      setEditingCampaign(null);
      resetForm();
      loadCampaigns(); // Reload campaigns list
    } catch (error) {
      console.error('Error updating campaign:', error);
      toast.error('Failed to update campaign', {
        description: error instanceof Error ? error.message : 'Unknown error'
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async (campaignId: string) => {
    const campaign = campaigns.find(c => c.id === campaignId);
    if (!campaign) return;

    if (window.confirm(`Are you sure you want to delete "${campaign.name}"? This action will archive the campaign.`)) {
      try {
        await campaignAPI.delete(campaign.name);
        
        toast.success('Campaign deleted successfully!', {
          description: `${campaign.name} has been archived`
        });
        
        loadCampaigns(); // Reload campaigns list
      } catch (error) {
        console.error('Error deleting campaign:', error);
        toast.error('Failed to delete campaign', {
          description: error instanceof Error ? error.message : 'Unknown error'
        });
      }
    }
  };

  const handleAnalyzeNow = async (campaignId: string) => {
    const campaign = campaigns.find(c => c.id === campaignId);
    if (!campaign) return;

    try {
      setAnalyzingCampaignId(campaignId);

      // Show "started" popup immediately when trigger-analysis is clicked
      setNotificationState({
        isOpen: true,
        campaignName: campaign.name,
        type: 'started'
      });

      // Call API to trigger analysis
      const result = await campaignAPI.triggerAnalysis(campaign.name);
      console.log('🔧 Trigger analysis API response:', result);
      
      // Note: Background process will handle the actual analysis
      // The popup will show "started" and user can close it
      // When background process completes, it should trigger another notification
      
      // Refresh campaigns to reflect potential status change
      refreshCampaigns();
      
    } catch (error: any) {
      console.error('Error analyzing campaign:', error);
      
      // Show "failed" popup
      setNotificationState({
        isOpen: true,
        campaignName: campaign.name,
        type: 'failed'
      });
    } finally {
      setAnalyzingCampaignId(null);
    }
  };

  const filteredCampaigns = campaigns.filter(campaign => {
    const matchesSearch = campaign.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         campaign.description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = filterStatus === "all" || campaign.status === filterStatus;
    return matchesSearch && matchesStatus;
  });

  const getStatusColor = (status: Campaign['status']) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800 border-green-300';
      case 'paused': return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      case 'completed': return 'bg-blue-100 text-blue-800 border-blue-300';
      case 'draft': return 'bg-gray-100 text-gray-800 border-gray-300';
      default: return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  const getTypeColor = (type: Campaign['type']) => {
    switch (type) {
      case 'product_launch': return 'bg-purple-100 text-purple-800 border-purple-300';
      case 'brand_awareness': return 'bg-blue-100 text-blue-800 border-blue-300';
      case 'feature_highlight': return 'bg-green-100 text-green-800 border-green-300';
      case 'crisis_response': return 'bg-red-100 text-red-800 border-red-300';
      default: return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header and Controls */}
      <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">Campaign Management</h3>
          <p className="text-sm text-muted-foreground">Create and manage your monitoring campaigns</p>
        </div>
        
        <Dialog 
          open={isCreateDialogOpen || !!editingCampaign} 
          onOpenChange={(open: boolean) => {
            if (!open) {
              setIsCreateDialogOpen(false);
              setEditingCampaign(null);
              resetForm();
            }
          }}
        >
          <DialogTrigger asChild>
            <Button onClick={() => setIsCreateDialogOpen(true)} className="flex items-center gap-2">
              <Plus className="h-4 w-4" />
              New Campaign
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>{editingCampaign ? 'Edit Campaign' : 'Create New Campaign'}</DialogTitle>
              <DialogDescription>
                {editingCampaign ? 'Update campaign details and settings' : 'Set up a new campaign for monitoring post URLs and tracking sentiment'}
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Campaign Name</Label>
                  <Input
                    id="name"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="Enter campaign name"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="type">Campaign Type</Label>
                  <Select value={formData.type} onValueChange={(value: Campaign['type']) => setFormData({ ...formData, type: value })}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="product_launch">Product Launch</SelectItem>
                      <SelectItem value="brand_awareness">Brand Awareness</SelectItem>
                      <SelectItem value="feature_highlight">Feature Highlight</SelectItem>
                      <SelectItem value="crisis_response">Crisis Response</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Describe the purpose and goals of this campaign"
                  rows={3}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="brand_name">Brand Name</Label>
                  <Input
                    id="brand_name"
                    value={formData.brand_name}
                    onChange={(e) => setFormData({ ...formData, brand_name: e.target.value })}
                    placeholder="hufagripp"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="keywords">Keywords (comma-separated)</Label>
                  <Input
                    id="keywords"
                    value={formData.keywords}
                    onChange={(e) => setFormData({ ...formData, keywords: e.target.value })}
                    placeholder="hufagrip, hufagripp, obat batuk"
                  />
                </div>
              </div>
              
              {/* Platform Selection */}
              <div className="space-y-2">
                <Label>Platforms</Label>
                <div className="grid grid-cols-2 gap-2">
                  {platformOptions.map((platform) => (
                    <div key={platform.value} className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        id={`platform-${platform.value}`}
                        checked={formData.selectedPlatforms.includes(platform.value)}
                        onChange={(e) => handlePlatformChange(platform.value, e.target.checked)}
                        className="rounded border-gray-300"
                      />
                      <Label htmlFor={`platform-${platform.value}`} className="text-sm">
                        {platform.label}
                      </Label>
                    </div>
                  ))}
                </div>
              </div>

              {/* Platform-specific URL fields */}
              {formData.selectedPlatforms.map((platform) => {
                const platformLabel = platformOptions.find(p => p.value === platform)?.label || platform;
                return (
                  <div key={platform} className="space-y-2">
                    <Label htmlFor={`urls-${platform}`}>
                      {platformLabel} URLs (one per line)
                    </Label>
                    <Textarea
                      id={`urls-${platform}`}
                      value={formData.platformUrls[platform] || ''}
                      onChange={(e) => handlePlatformUrlChange(platform, e.target.value)}
                      placeholder={`Enter ${platformLabel} URLs, one per line...`}
                      rows={3}
                    />
                  </div>
                );
              })}
              
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="start_date">Start Date</Label>
                  <Input
                    id="start_date"
                    type="date"
                    value={formData.start_date}
                    onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                    max={getMaxDate()}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="end_date">End Date</Label>
                  <Input
                    id="end_date"
                    type="date"
                    value={formData.end_date}
                    onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                    max={getMaxDate()}
                  />
                </div>
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="target_audience">Target Audience (comma-separated)</Label>
                <Input
                  id="target_audience"
                  value={formData.target_audience}
                  onChange={(e) => setFormData({ ...formData, target_audience: e.target.value })}
                  placeholder="Tech Enthusiasts, EV Adopters, Tesla Owners"
                />
              </div>
              
              {/* Status Display - Read Only */}
              <div className="space-y-2">
                <Label>Status</Label>
                <div className="flex items-center space-x-2">
                  <Badge 
                    variant={formData.status === 'active' ? 'default' : 
                             formData.status === 'completed' ? 'secondary' : 'outline'}
                    className="text-sm"
                  >
                    {formData.status === 'active' ? 'Active' :
                     formData.status === 'completed' ? 'Completed' : 'Draft'}
                  </Badge>
                  <span className="text-xs text-muted-foreground">
                    {formData.status === 'active' ? 'Analysis ongoing or date range not finished' :
                     formData.status === 'completed' ? 'Analysis completed' : 'Ready to start'}
                  </span>
                </div>
              </div>
            </div>
            <div className="flex justify-end gap-2">
              <Button 
                variant="outline" 
                onClick={() => {
                  setIsCreateDialogOpen(false);
                  setEditingCampaign(null);
                  resetForm();
                }}
                disabled={isLoading}
              >
                Cancel
              </Button>
              <Button 
                onClick={editingCampaign ? handleUpdate : handleCreate}
                disabled={isLoading}
              >
                {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                {editingCampaign ? 'Update' : 'Create'} Campaign
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* Search and Filter */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search campaigns..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>
        <Select value={filterStatus} onValueChange={setFilterStatus}>
          <SelectTrigger className="w-full sm:w-48">
            <SelectValue placeholder="Filter by status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="active">Active</SelectItem>
            <SelectItem value="paused">Paused</SelectItem>
            <SelectItem value="completed">Completed</SelectItem>
            <SelectItem value="draft">Draft</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Loading State */}
      {isLoadingList && (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Loader2 className="h-12 w-12 text-muted-foreground mb-4 animate-spin" />
            <p className="text-muted-foreground">Loading campaigns...</p>
          </CardContent>
        </Card>
      )}

      {/* Campaigns Grid */}
      {!isLoadingList && (
        <>
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {filteredCampaigns.map((campaign) => (
          <Card key={campaign.id} className="hover:shadow-md transition-shadow">
            <CardHeader className="pb-3">
              <div className="flex items-start justify-between">
                <div className="space-y-1">
                  <CardTitle className="text-base">{campaign.name}</CardTitle>
                  <div className="flex gap-2">
                    <Badge variant="outline" className={getStatusColor(campaign.status)}>
                      {campaign.status}
                    </Badge>
                    <Badge variant="outline" className={getTypeColor(campaign.type)}>
                      {campaign.type.replace('_', ' ')}
                    </Badge>
                  </div>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm text-muted-foreground line-clamp-2">
                {campaign.description}
              </p>
              
              <div className="space-y-2 text-sm">
                <div className="flex items-center gap-2">
                  <Calendar className="h-4 w-4 text-muted-foreground" />
                  <span>{campaign.start_date} to {campaign.end_date}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Target className="h-4 w-4 text-muted-foreground" />
                  <span>{campaign.postUrls.length} post URLs</span>
                </div>
                <div className="flex items-center gap-2">
                  <Users className="h-4 w-4 text-muted-foreground" />
                  <span>{campaign.target_audience.length} audiences</span>
                </div>
              </div>

              {/* Post URLs Preview */}
              <div className="space-y-2">
                <h5 className="text-xs font-medium text-muted-foreground">Sample Posts:</h5>
                <div className="space-y-1">
                  {campaign.postUrls.slice(0, 2).map((url, index) => (
                    <div key={index} className="text-xs p-2 bg-muted rounded text-muted-foreground truncate">
                      {url}
                    </div>
                  ))}
                  {campaign.postUrls.length > 2 && (
                    <div className="text-xs text-muted-foreground">
                      +{campaign.postUrls.length - 2} more posts
                    </div>
                  )}
                </div>
              </div>

              <div className="flex justify-between items-center pt-2">
                <div className="flex gap-1">
                  {campaign.platforms.slice(0, 3).map((platform, index) => (
                    <Badge key={index} variant="secondary" className="text-xs">
                      {platform}
                    </Badge>
                  ))}
                  {campaign.platforms.length > 3 && (
                    <Badge variant="secondary" className="text-xs">
                      +{campaign.platforms.length - 3}
                    </Badge>
                  )}
                </div>
                
                <div className="flex gap-1">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => onSelectCampaign(campaign)}
                    className="h-8 w-8 p-0"
                    title="View Details"
                  >
                    <Eye className="h-4 w-4" />
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleAnalyzeNow(campaign.id)}
                    className="h-8 w-8 p-0 text-green-600 hover:text-green-700 hover:bg-green-50"
                    // 2. campaign/brand/content yang bisa dilakukan trigger-analysis hanya yang memiliki status active, paused, draft saja
                    disabled={
                      analyzingCampaignId === campaign.id || 
                      !['active', 'paused', 'draft'].includes(campaign.status.toLowerCase())
                    }
                    title={
                      !['active', 'paused', 'draft'].includes(campaign.status.toLowerCase()) 
                        ? `Analysis not allowed for ${campaign.status} campaigns` 
                        : "Analyze Now"
                    }
                  >
                    {analyzingCampaignId === campaign.id ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Play className="h-4 w-4" />
                    )}
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleEdit(campaign)}
                    className="h-8 w-8 p-0"
                    title="Edit Campaign"
                  >
                    <Edit className="h-4 w-4" />
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleDelete(campaign.id)}
                    className="h-8 w-8 p-0 text-destructive hover:text-destructive"
                    title="Delete Campaign"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
            ))}
          </div>

          {filteredCampaigns.length === 0 && (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-12">
                <Target className="h-12 w-12 text-muted-foreground mb-4" />
                <h3 className="text-lg font-semibold mb-2">No campaigns found</h3>
                <p className="text-muted-foreground text-center mb-4">
                  {searchTerm || filterStatus !== "all" 
                    ? "Try adjusting your search or filter criteria" 
                    : "Create your first campaign to start monitoring"}
                </p>
                {!searchTerm && filterStatus === "all" && (
                  <Button onClick={() => setIsCreateDialogOpen(true)} className="flex items-center gap-2">
                    <Plus className="h-4 w-4" />
                    Create Campaign
                  </Button>
                )}
              </CardContent>
            </Card>
          )}
        </>
      )}

      {/* Custom Analysis Notification */}
      <AnalysisNotification
        isOpen={notificationState.isOpen}
        onClose={handleCloseNotification}
        campaignName={notificationState.campaignName}
        type={notificationState.type}
      />
    </div>
  );
}