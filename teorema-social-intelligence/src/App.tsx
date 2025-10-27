import { useState, useEffect } from "react";
import { Badge } from "./components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./components/ui/tabs";
import { CampaignManagement } from "./components/CampaignManagement";
import { BrandManagement } from "./components/BrandManagement";
import { ContentManagement } from "./components/ContentManagement";
import { RealAnalysisView } from "./components/RealAnalysisView";
import { Login } from "./components/Login";
import { Campaign, Brand, Content } from "./lib/mock-data";
import logoSocialInt from "../assets/logo_socialint.png";
import { 
  Calendar,
  RefreshCw,
  Target,
  Building2,
  FileText,
  LogOut,
  User
} from "lucide-react";

export default function App() {
  // Authentication state
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [username, setUsername] = useState("");
  const [name, setName] = useState("");

  const [lastUpdated, setLastUpdated] = useState(new Date());
  const [activeTab, setActiveTab] = useState("campaign-analysis");
  const [activeSubTab, setActiveSubTab] = useState("management");
  
  // Selected entities for analysis
  const [selectedCampaign, setSelectedCampaign] = useState<Campaign | null>(null);
  const [selectedBrand, setSelectedBrand] = useState<Brand | null>(null);
  const [selectedContent, setSelectedContent] = useState<Content | null>(null);

  // Check authentication on mount
  useEffect(() => {
    const storedAuth = localStorage.getItem("isAuthenticated");
    const storedUsername = localStorage.getItem("username");
    const storedName = localStorage.getItem("name");
    
    if (storedAuth === "true" && storedUsername && storedName) {
      setIsAuthenticated(true);
      setUsername(storedUsername);
      setName(storedName);
    }
  }, []);

  const handleLogin = (user: string, fullName: string) => {
    setIsAuthenticated(true);
    setUsername(user);
    setName(fullName);
    localStorage.setItem("isAuthenticated", "true");
    localStorage.setItem("username", user);
    localStorage.setItem("name", fullName);
  };

  const handleLogout = () => {
    setIsAuthenticated(false);
    setUsername("");
    setName("");
    localStorage.removeItem("isAuthenticated");
    localStorage.removeItem("username");
    localStorage.removeItem("name");
    // Reset state
    setSelectedCampaign(null);
    setSelectedBrand(null);
    setSelectedContent(null);
    setActiveTab("campaign-analysis");
    setActiveSubTab("management");
  };

  const handleRefresh = () => {
    setLastUpdated(new Date());
    // In a real app, this would trigger data refresh
  };

  const handleSelectCampaign = (campaign: Campaign) => {
    setSelectedCampaign(campaign);
    setActiveSubTab("analysis");
  };

  const handleSelectBrand = (brand: Brand) => {
    setSelectedBrand(brand);
    setActiveSubTab("analysis");
  };

  const handleSelectContent = (content: Content) => {
    setSelectedContent(content);
    setActiveSubTab("analysis");
  };

  const handleBackToManagement = () => {
    setSelectedCampaign(null);
    setSelectedBrand(null);
    setSelectedContent(null);
    setActiveSubTab("management");
  };

  // Jika belum login, tampilkan halaman login
  if (!isAuthenticated) {
    return <Login onLogin={handleLogin} />;
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="border-b bg-card">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-3">
                <img 
                  src={logoSocialInt} 
                  alt="Social Intelligence Logo" 
                  className="w-10 h-10 object-contain"
                />
                <div>
                  <h1 className="text-2xl font-bold">Social Intelligence Dashboard</h1>
                  <p className="text-sm text-muted-foreground">Comprehensive content, brand, and campaign monitoring</p>
                </div>
              </div>
              <Badge variant="default" className="bg-green-100 text-green-800 border-green-300">
                Live
              </Badge>
            </div>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-3 px-3 py-2 rounded-lg border border-border bg-accent/50">
                <User className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm font-medium">{name}</span>
              </div>
              <div className="flex items-center space-x-2 text-sm text-muted-foreground">
                <Calendar className="h-4 w-4" />
                <span>Last updated: {lastUpdated.toLocaleTimeString()}</span>
              </div>
              <button
                onClick={handleRefresh}
                className="flex items-center space-x-2 px-3 py-2 rounded-lg border border-border hover:bg-accent transition-colors"
              >
                <RefreshCw className="h-4 w-4" />
                <span>Refresh</span>
              </button>
              <button
                onClick={handleLogout}
                className="flex items-center space-x-2 px-3 py-2 rounded-lg border border-red-200 text-red-600 hover:bg-red-50 transition-colors"
              >
                <LogOut className="h-4 w-4" />
                <span>Logout</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Dashboard */}
      <div className="container mx-auto px-6 py-6">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-2 lg:w-fit lg:grid-cols-2 p-0.5">
            <TabsTrigger value="campaign-analysis" className="flex items-center space-x-1.5 px-2 py-1.5">
              <Target className="h-3.5 w-3.5" />
              <span className="text-sm">Campaign Analysis</span>
            </TabsTrigger>
            <TabsTrigger value="brand-analysis" className="flex items-center space-x-1.5 px-2 py-1.5">
              <Building2 className="h-3.5 w-3.5" />
              <span className="text-sm">Brand Analysis</span>
            </TabsTrigger>
            {/* <TabsTrigger value="content-analysis" className="flex items-center space-x-2">
              <FileText className="h-4 w-4" />
              <span>Content Analysis</span>
            </TabsTrigger> */}
          </TabsList>

          <TabsContent value="campaign-analysis" className="space-y-6">
            <Tabs value={activeSubTab} onValueChange={setActiveSubTab} className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-xl font-semibold">Campaign Analysis</h2>
                  <p className="text-sm text-muted-foreground">Monitor and analyze marketing campaigns</p>
                </div>
                <TabsList className="grid grid-cols-2">
                  <TabsTrigger value="management">Management</TabsTrigger>
                  <TabsTrigger value="analysis" disabled={!selectedCampaign}>Analysis</TabsTrigger>
                </TabsList>
              </div>
              
              <TabsContent value="management">
                <CampaignManagement onSelectCampaign={handleSelectCampaign} />
              </TabsContent>
              
              <TabsContent value="analysis">
                {selectedCampaign && (
                  <RealAnalysisView 
                    entity={selectedCampaign}
                    entityType="campaign"
                    onBack={handleBackToManagement}
                  />
                )}
              </TabsContent>
            </Tabs>
          </TabsContent>

          <TabsContent value="brand-analysis" className="space-y-6">
            <Tabs value={activeSubTab} onValueChange={setActiveSubTab} className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-xl font-semibold">Brand Analysis</h2>
                  <p className="text-sm text-muted-foreground">Track brand perception and competitive landscape</p>
                </div>
                <TabsList className="grid grid-cols-2">
                  <TabsTrigger value="management">Management</TabsTrigger>
                  <TabsTrigger value="analysis" disabled={!selectedBrand}>Analysis</TabsTrigger>
                </TabsList>
              </div>
              
              <TabsContent value="management">
                <BrandManagement onSelectBrand={handleSelectBrand} />
              </TabsContent>
              
              <TabsContent value="analysis">
                {selectedBrand && (
                  <RealAnalysisView 
                    entity={selectedBrand}
                    entityType="brand"
                    onBack={handleBackToManagement}
                  />
                )}
              </TabsContent>
            </Tabs>
          </TabsContent>

          {/* <TabsContent value="content-analysis" className="space-y-6">
            <Tabs value={activeSubTab} onValueChange={setActiveSubTab} className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-xl font-semibold">Content Analysis</h2>
                  <p className="text-sm text-muted-foreground">Analyze individual posts and content performance</p>
                </div>
                <TabsList className="grid grid-cols-2">
                  <TabsTrigger value="management">Management</TabsTrigger>
                  <TabsTrigger value="analysis" disabled={!selectedContent}>Analysis</TabsTrigger>
                </TabsList>
              </div>
              
              <TabsContent value="management">
                <ContentManagement onSelectContent={handleSelectContent} />
              </TabsContent>
              
              <TabsContent value="analysis">
                {selectedContent && (
                  <RealAnalysisView 
                    entity={selectedContent}
                    entityType="content"
                    onBack={handleBackToManagement}
                  />
                )}
              </TabsContent>
            </Tabs>
          </TabsContent> */}
        </Tabs>
      </div>

      {/* Footer */}
      <footer className="border-t bg-card mt-12">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between text-sm text-muted-foreground">
            <p>© 2025 Teorema Intelligence. All rights reserved.</p>
            <div className="flex items-center space-x-4">
              <span>Data sources: Twitter/X, Reddit, YouTube, LinkedIn, TikTok, Instagram</span>
              <Badge variant="outline" className="text-xs">
                Beta
              </Badge>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}