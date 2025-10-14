import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Textarea } from "./ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select";
import { Badge } from "./ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogTrigger } from "./ui/dialog";
import { Label } from "./ui/label";
import { Brand, brands as mockBrands } from "../lib/mock-data";
import { Plus, Search, Eye, Edit, Trash2, Building2, Tag, Users } from "lucide-react";

interface BrandManagementProps {
  onSelectBrand: (brand: Brand) => void;
}

export function BrandManagement({ onSelectBrand }: BrandManagementProps) {
  const [brands, setBrands] = useState<Brand[]>(mockBrands);
  const [searchTerm, setSearchTerm] = useState("");
  const [filterStatus, setFilterStatus] = useState("all");
  const [filterCategory, setFilterCategory] = useState("all");
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [editingBrand, setEditingBrand] = useState<Brand | null>(null);

  // Form state for creating/editing brands
  const [formData, setFormData] = useState({
    name: "",
    description: "",
    postUrls: "",
    keywords: "",
    category: "",
    status: "active" as Brand['status'],
    competitors: ""
  });

  const resetForm = () => {
    setFormData({
      name: "",
      description: "",
      postUrls: "",
      keywords: "",
      category: "",
      status: "active",
      competitors: ""
    });
  };

  const handleCreate = () => {
    const newBrand: Brand = {
      id: `brand_${Date.now()}`,
      name: formData.name,
      description: formData.description,
      postUrls: formData.postUrls.split('\n').filter(url => url.trim()),
      keywords: formData.keywords.split(',').map(k => k.trim()).filter(k => k),
      category: formData.category,
      status: formData.status,
      created_date: new Date().toISOString().split('T')[0],
      competitors: formData.competitors.split(',').map(c => c.trim()).filter(c => c)
    };

    setBrands([...brands, newBrand]);
    setIsCreateDialogOpen(false);
    resetForm();
  };

  const handleEdit = (brand: Brand) => {
    setEditingBrand(brand);
    setFormData({
      name: brand.name,
      description: brand.description,
      postUrls: brand.postUrls.join('\n'),
      keywords: brand.keywords.join(', '),
      category: brand.category,
      status: brand.status,
      competitors: brand.competitors.join(', ')
    });
  };

  const handleUpdate = () => {
    if (!editingBrand) return;

    const updatedBrand: Brand = {
      ...editingBrand,
      name: formData.name,
      description: formData.description,
      postUrls: formData.postUrls.split('\n').filter(url => url.trim()),
      keywords: formData.keywords.split(',').map(k => k.trim()).filter(k => k),
      category: formData.category,
      status: formData.status,
      competitors: formData.competitors.split(',').map(c => c.trim()).filter(c => c)
    };

    setBrands(brands.map(b => b.id === editingBrand.id ? updatedBrand : b));
    setEditingBrand(null);
    resetForm();
  };

  const handleDelete = (brandId: string) => {
    setBrands(brands.filter(b => b.id !== brandId));
  };

  const filteredBrands = brands.filter(brand => {
    const matchesSearch = brand.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         brand.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         brand.keywords.some(k => k.toLowerCase().includes(searchTerm.toLowerCase()));
    const matchesStatus = filterStatus === "all" || brand.status === filterStatus;
    const matchesCategory = filterCategory === "all" || brand.category === filterCategory;
    return matchesSearch && matchesStatus && matchesCategory;
  });

  const getStatusColor = (status: Brand['status']) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800 border-green-300';
      case 'inactive': return 'bg-gray-100 text-gray-800 border-gray-300';
      default: return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  const getCategoryColor = (category: string) => {
    const colors = [
      'bg-purple-100 text-purple-800 border-purple-300',
      'bg-blue-100 text-blue-800 border-blue-300',
      'bg-green-100 text-green-800 border-green-300',
      'bg-orange-100 text-orange-800 border-orange-300',
      'bg-pink-100 text-pink-800 border-pink-300'
    ];
    const index = category.length % colors.length;
    return colors[index];
  };

  const uniqueCategories = Array.from(new Set(brands.map(brand => brand.category)));

  return (
    <div className="space-y-6">
      {/* Header and Controls */}
      <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">Brand Management</h3>
          <p className="text-sm text-muted-foreground">Monitor brands with post URLs and keywords</p>
        </div>
        
        <Dialog 
          open={isCreateDialogOpen || !!editingBrand} 
          onOpenChange={(open) => {
            if (!open) {
              setIsCreateDialogOpen(false);
              setEditingBrand(null);
              resetForm();
            }
          }}
        >
          <DialogTrigger asChild>
            <Button onClick={() => setIsCreateDialogOpen(true)} className="flex items-center gap-2">
              <Plus className="h-4 w-4" />
              New Brand
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>{editingBrand ? 'Edit Brand' : 'Create New Brand'}</DialogTitle>
              <DialogDescription>
                {editingBrand ? 'Update brand monitoring settings and keywords' : 'Set up brand monitoring with post URLs and keywords for comprehensive analysis'}
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Brand Name</Label>
                  <Input
                    id="name"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="Enter brand name"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="category">Category</Label>
                  <Input
                    id="category"
                    value={formData.category}
                    onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                    placeholder="e.g., Automotive, Technology, Energy"
                  />
                </div>
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Describe what this brand monitoring focuses on"
                  rows={3}
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="postUrls">Post URLs (one per line)</Label>
                <Textarea
                  id="postUrls"
                  value={formData.postUrls}
                  onChange={(e) => setFormData({ ...formData, postUrls: e.target.value })}
                  placeholder="https://twitter.com/brandname&#10;https://instagram.com/brandname&#10;https://youtube.com/brandname"
                  rows={4}
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="keywords">Keywords (comma-separated)</Label>
                <Textarea
                  id="keywords"
                  value={formData.keywords}
                  onChange={(e) => setFormData({ ...formData, keywords: e.target.value })}
                  placeholder="brand name, product names, related terms, hashtags"
                  rows={3}
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="competitors">Competitors (comma-separated)</Label>
                <Input
                  id="competitors"
                  value={formData.competitors}
                  onChange={(e) => setFormData({ ...formData, competitors: e.target.value })}
                  placeholder="Competitor 1, Competitor 2, Competitor 3"
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="status">Status</Label>
                <Select value={formData.status} onValueChange={(value: Brand['status']) => setFormData({ ...formData, status: value })}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="active">Active</SelectItem>
                    <SelectItem value="inactive">Inactive</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => {
                setIsCreateDialogOpen(false);
                setEditingBrand(null);
                resetForm();
              }}>
                Cancel
              </Button>
              <Button onClick={editingBrand ? handleUpdate : handleCreate}>
                {editingBrand ? 'Update' : 'Create'} Brand
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
            placeholder="Search brands..."
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
            <SelectItem value="active">Active</SelectItem>
            <SelectItem value="inactive">Inactive</SelectItem>
          </SelectContent>
        </Select>
        <Select value={filterCategory} onValueChange={setFilterCategory}>
          <SelectTrigger className="w-full sm:w-40">
            <SelectValue placeholder="Category" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Categories</SelectItem>
            {uniqueCategories.map((category) => (
              <SelectItem key={category} value={category}>{category}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Brands Grid */}
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {filteredBrands.map((brand) => (
          <Card key={brand.id} className="hover:shadow-md transition-shadow">
            <CardHeader className="pb-3">
              <div className="flex items-start justify-between">
                <div className="space-y-1">
                  <CardTitle className="text-base">{brand.name}</CardTitle>
                  <div className="flex gap-2">
                    <Badge variant="outline" className={getStatusColor(brand.status)}>
                      {brand.status}
                    </Badge>
                    <Badge variant="outline" className={getCategoryColor(brand.category)}>
                      {brand.category}
                    </Badge>
                  </div>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm text-muted-foreground line-clamp-2">
                {brand.description}
              </p>
              
              <div className="space-y-2 text-sm">
                <div className="flex items-center gap-2">
                  <Building2 className="h-4 w-4 text-muted-foreground" />
                  <span>{brand.postUrls.length} post URLs</span>
                </div>
                <div className="flex items-center gap-2">
                  <Tag className="h-4 w-4 text-muted-foreground" />
                  <span>{brand.keywords.length} keywords</span>
                </div>
                <div className="flex items-center gap-2">
                  <Users className="h-4 w-4 text-muted-foreground" />
                  <span>{brand.competitors.length} competitors</span>
                </div>
              </div>

              {/* Keywords Preview */}
              <div className="space-y-2">
                <h5 className="text-xs font-medium text-muted-foreground">Keywords:</h5>
                <div className="flex flex-wrap gap-1">
                  {brand.keywords.slice(0, 4).map((keyword, index) => (
                    <Badge key={index} variant="secondary" className="text-xs">
                      {keyword}
                    </Badge>
                  ))}
                  {brand.keywords.length > 4 && (
                    <Badge variant="secondary" className="text-xs">
                      +{brand.keywords.length - 4}
                    </Badge>
                  )}
                </div>
              </div>

              {/* Post URLs Preview */}
              <div className="space-y-2">
                <h5 className="text-xs font-medium text-muted-foreground">Sample Posts:</h5>
                <div className="space-y-1">
                  {brand.postUrls.slice(0, 2).map((url, index) => (
                    <div key={index} className="text-xs p-2 bg-muted rounded text-muted-foreground truncate">
                      {url}
                    </div>
                  ))}
                  {brand.postUrls.length > 2 && (
                    <div className="text-xs text-muted-foreground">
                      +{brand.postUrls.length - 2} more posts
                    </div>
                  )}
                </div>
              </div>

              <div className="flex justify-between items-center pt-2">
                <div className="text-xs text-muted-foreground">
                  Created {brand.created_date}
                </div>
                
                <div className="flex gap-1">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => onSelectBrand(brand)}
                    className="h-8 w-8 p-0"
                  >
                    <Eye className="h-4 w-4" />
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleEdit(brand)}
                    className="h-8 w-8 p-0"
                  >
                    <Edit className="h-4 w-4" />
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleDelete(brand.id)}
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

      {filteredBrands.length === 0 && (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Building2 className="h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">No brands found</h3>
            <p className="text-muted-foreground text-center mb-4">
              {searchTerm || filterStatus !== "all" || filterCategory !== "all"
                ? "Try adjusting your search or filter criteria" 
                : "Create your first brand to start monitoring"}
            </p>
            {!searchTerm && filterStatus === "all" && filterCategory === "all" && (
              <Button onClick={() => setIsCreateDialogOpen(true)} className="flex items-center gap-2">
                <Plus className="h-4 w-4" />
                Create Brand
              </Button>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}