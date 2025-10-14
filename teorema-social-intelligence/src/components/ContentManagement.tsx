import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Textarea } from "./ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select";
import { Badge } from "./ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogTrigger } from "./ui/dialog";
import { Label } from "./ui/label";
import { Content, contents as mockContents } from "../lib/mock-data";
import { Plus, Search, Eye, Edit, Trash2, FileText, Calendar, User, ExternalLink } from "lucide-react";

interface ContentManagementProps {
  onSelectContent: (content: Content) => void;
}

export function ContentManagement({ onSelectContent }: ContentManagementProps) {
  const [contents, setContents] = useState<Content[]>(mockContents);
  const [searchTerm, setSearchTerm] = useState("");
  const [filterStatus, setFilterStatus] = useState("all");
  const [filterPlatform, setFilterPlatform] = useState("all");
  const [filterContentType, setFilterContentType] = useState("all");
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [editingContent, setEditingContent] = useState<Content | null>(null);

  // Form state for creating/editing content
  const [formData, setFormData] = useState({
    title: "",
    description: "",
    postUrl: "",
    platform: "",
    content_type: "post" as Content['content_type'],
    author: "",
    publish_date: "",
    status: "published" as Content['status'],
    tags: ""
  });

  const resetForm = () => {
    setFormData({
      title: "",
      description: "",
      postUrl: "",
      platform: "",
      content_type: "post",
      author: "",
      publish_date: "",
      status: "published",
      tags: ""
    });
  };

  const handleCreate = () => {
    const newContent: Content = {
      id: `content_${Date.now()}`,
      title: formData.title,
      description: formData.description,
      postUrl: formData.postUrl,
      platform: formData.platform,
      content_type: formData.content_type,
      author: formData.author,
      publish_date: formData.publish_date,
      status: formData.status,
      tags: formData.tags.split(',').map(t => t.trim()).filter(t => t)
    };

    setContents([...contents, newContent]);
    setIsCreateDialogOpen(false);
    resetForm();
  };

  const handleEdit = (content: Content) => {
    setEditingContent(content);
    setFormData({
      title: content.title,
      description: content.description,
      postUrl: content.postUrl,
      platform: content.platform,
      content_type: content.content_type,
      author: content.author,
      publish_date: content.publish_date,
      status: content.status,
      tags: content.tags.join(', ')
    });
  };

  const handleUpdate = () => {
    if (!editingContent) return;

    const updatedContent: Content = {
      ...editingContent,
      title: formData.title,
      description: formData.description,
      postUrl: formData.postUrl,
      platform: formData.platform,
      content_type: formData.content_type,
      author: formData.author,
      publish_date: formData.publish_date,
      status: formData.status,
      tags: formData.tags.split(',').map(t => t.trim()).filter(t => t)
    };

    setContents(contents.map(c => c.id === editingContent.id ? updatedContent : c));
    setEditingContent(null);
    resetForm();
  };

  const handleDelete = (contentId: string) => {
    setContents(contents.filter(c => c.id !== contentId));
  };

  const filteredContents = contents.filter(content => {
    const matchesSearch = content.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         content.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         content.author.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         content.tags.some(t => t.toLowerCase().includes(searchTerm.toLowerCase()));
    const matchesStatus = filterStatus === "all" || content.status === filterStatus;
    const matchesPlatform = filterPlatform === "all" || content.platform === filterPlatform;
    const matchesContentType = filterContentType === "all" || content.content_type === filterContentType;
    return matchesSearch && matchesStatus && matchesPlatform && matchesContentType;
  });

  const getStatusColor = (status: Content['status']) => {
    switch (status) {
      case 'published': return 'bg-green-100 text-green-800 border-green-300';
      case 'draft': return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      case 'archived': return 'bg-gray-100 text-gray-800 border-gray-300';
      default: return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  const getContentTypeColor = (type: Content['content_type']) => {
    switch (type) {
      case 'video': return 'bg-red-100 text-red-800 border-red-300';
      case 'post': return 'bg-blue-100 text-blue-800 border-blue-300';
      case 'article': return 'bg-purple-100 text-purple-800 border-purple-300';
      case 'image': return 'bg-green-100 text-green-800 border-green-300';
      case 'story': return 'bg-orange-100 text-orange-800 border-orange-300';
      default: return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  const getPlatformColor = (platform: string) => {
    switch (platform.toLowerCase()) {
      case 'twitter/x': case 'twitter': return 'bg-blue-100 text-blue-800 border-blue-300';
      case 'youtube': return 'bg-red-100 text-red-800 border-red-300';
      case 'instagram': return 'bg-pink-100 text-pink-800 border-pink-300';
      case 'linkedin': return 'bg-blue-100 text-blue-800 border-blue-300';
      case 'reddit': return 'bg-orange-100 text-orange-800 border-orange-300';
      case 'tiktok': return 'bg-black text-white border-black';
      default: return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  const uniquePlatforms = Array.from(new Set(contents.map(content => content.platform)));

  return (
    <div className="space-y-6">
      {/* Header and Controls */}
      <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">Content Management</h3>
          <p className="text-sm text-muted-foreground">Track individual posts and content pieces</p>
        </div>
        
        <Dialog 
          open={isCreateDialogOpen || !!editingContent} 
          onOpenChange={(open) => {
            if (!open) {
              setIsCreateDialogOpen(false);
              setEditingContent(null);
              resetForm();
            }
          }}
        >
          <DialogTrigger asChild>
            <Button onClick={() => setIsCreateDialogOpen(true)} className="flex items-center gap-2">
              <Plus className="h-4 w-4" />
              New Content
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>{editingContent ? 'Edit Content' : 'Add New Content'}</DialogTitle>
              <DialogDescription>
                {editingContent ? 'Update content details and metadata' : 'Add a new content piece for individual analysis and monitoring'}
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="title">Content Title</Label>
                <Input
                  id="title"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  placeholder="Enter content title"
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Describe the content and its purpose"
                  rows={3}
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="postUrl">Post URL</Label>
                <Input
                  id="postUrl"
                  value={formData.postUrl}
                  onChange={(e) => setFormData({ ...formData, postUrl: e.target.value })}
                  placeholder="https://example.com/post/123"
                />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="platform">Platform</Label>
                  <Input
                    id="platform"
                    value={formData.platform}
                    onChange={(e) => setFormData({ ...formData, platform: e.target.value })}
                    placeholder="e.g., Twitter/X, YouTube, Instagram"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="content_type">Content Type</Label>
                  <Select value={formData.content_type} onValueChange={(value: Content['content_type']) => setFormData({ ...formData, content_type: value })}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="video">Video</SelectItem>
                      <SelectItem value="post">Post</SelectItem>
                      <SelectItem value="article">Article</SelectItem>
                      <SelectItem value="image">Image</SelectItem>
                      <SelectItem value="story">Story</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="author">Author</Label>
                  <Input
                    id="author"
                    value={formData.author}
                    onChange={(e) => setFormData({ ...formData, author: e.target.value })}
                    placeholder="Content creator/author name"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="publish_date">Publish Date</Label>
                  <Input
                    id="publish_date"
                    type="date"
                    value={formData.publish_date}
                    onChange={(e) => setFormData({ ...formData, publish_date: e.target.value })}
                  />
                </div>
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="tags">Tags (comma-separated)</Label>
                <Input
                  id="tags"
                  value={formData.tags}
                  onChange={(e) => setFormData({ ...formData, tags: e.target.value })}
                  placeholder="tag1, tag2, tag3"
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="status">Status</Label>
                <Select value={formData.status} onValueChange={(value: Content['status']) => setFormData({ ...formData, status: value })}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="published">Published</SelectItem>
                    <SelectItem value="draft">Draft</SelectItem>
                    <SelectItem value="archived">Archived</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => {
                setIsCreateDialogOpen(false);
                setEditingContent(null);
                resetForm();
              }}>
                Cancel
              </Button>
              <Button onClick={editingContent ? handleUpdate : handleCreate}>
                {editingContent ? 'Update' : 'Add'} Content
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
            placeholder="Search content..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>
        <Select value={filterStatus} onValueChange={setFilterStatus}>
          <SelectTrigger className="w-full sm:w-32">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="published">Published</SelectItem>
            <SelectItem value="draft">Draft</SelectItem>
            <SelectItem value="archived">Archived</SelectItem>
          </SelectContent>
        </Select>
        <Select value={filterPlatform} onValueChange={setFilterPlatform}>
          <SelectTrigger className="w-full sm:w-40">
            <SelectValue placeholder="Platform" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Platforms</SelectItem>
            {uniquePlatforms.map((platform) => (
              <SelectItem key={platform} value={platform}>{platform}</SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={filterContentType} onValueChange={setFilterContentType}>
          <SelectTrigger className="w-full sm:w-32">
            <SelectValue placeholder="Type" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Types</SelectItem>
            <SelectItem value="video">Video</SelectItem>
            <SelectItem value="post">Post</SelectItem>
            <SelectItem value="article">Article</SelectItem>
            <SelectItem value="image">Image</SelectItem>
            <SelectItem value="story">Story</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Content Grid */}
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {filteredContents.map((content) => (
          <Card key={content.id} className="hover:shadow-md transition-shadow">
            <CardHeader className="pb-3">
              <div className="flex items-start justify-between">
                <div className="space-y-1 flex-1">
                  <CardTitle className="text-base line-clamp-2">{content.title}</CardTitle>
                  <div className="flex gap-2 flex-wrap">
                    <Badge variant="outline" className={getStatusColor(content.status)}>
                      {content.status}
                    </Badge>
                    <Badge variant="outline" className={getContentTypeColor(content.content_type)}>
                      {content.content_type}
                    </Badge>
                  </div>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm text-muted-foreground line-clamp-2">
                {content.description}
              </p>
              
              <div className="space-y-2 text-sm">
                <div className="flex items-center gap-2">
                  <User className="h-4 w-4 text-muted-foreground" />
                  <span>{content.author}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Calendar className="h-4 w-4 text-muted-foreground" />
                  <span>{content.publish_date}</span>
                </div>
                <div className="flex items-center gap-2">
                  <FileText className="h-4 w-4 text-muted-foreground" />
                  <Badge variant="outline" className={getPlatformColor(content.platform)}>
                    {content.platform}
                  </Badge>
                </div>
              </div>

              {/* Tags Preview */}
              <div className="space-y-2">
                <h5 className="text-xs font-medium text-muted-foreground">Tags:</h5>
                <div className="flex flex-wrap gap-1">
                  {content.tags.slice(0, 3).map((tag, index) => (
                    <Badge key={index} variant="secondary" className="text-xs">
                      {tag}
                    </Badge>
                  ))}
                  {content.tags.length > 3 && (
                    <Badge variant="secondary" className="text-xs">
                      +{content.tags.length - 3}
                    </Badge>
                  )}
                </div>
              </div>

              {/* Content URL Preview */}
              <div className="space-y-1">
                <h5 className="text-xs font-medium text-muted-foreground">Content URL:</h5>
                <div className="text-xs p-2 bg-muted rounded text-muted-foreground truncate">
                  {content.postUrl}
                </div>
              </div>

              <div className="flex justify-between items-center pt-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => window.open(content.postUrl, '_blank')}
                  className="flex items-center gap-1 text-xs"
                >
                  <ExternalLink className="h-3 w-3" />
                  View Post
                </Button>
                
                <div className="flex gap-1">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => onSelectContent(content)}
                    className="h-8 w-8 p-0"
                  >
                    <Eye className="h-4 w-4" />
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleEdit(content)}
                    className="h-8 w-8 p-0"
                  >
                    <Edit className="h-4 w-4" />
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleDelete(content.id)}
                    className="h-8 w-8 p-0 text-destructive hover:text-destructive"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {filteredContents.length === 0 && (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <FileText className="h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">No content found</h3>
            <p className="text-muted-foreground text-center mb-4">
              {searchTerm || filterStatus !== "all" || filterPlatform !== "all" || filterContentType !== "all"
                ? "Try adjusting your search or filter criteria" 
                : "Add your first content piece to start monitoring"}
            </p>
            {!searchTerm && filterStatus === "all" && filterPlatform === "all" && filterContentType === "all" && (
              <Button onClick={() => setIsCreateDialogOpen(true)} className="flex items-center gap-2">
                <Plus className="h-4 w-4" />
                Add Content
              </Button>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}