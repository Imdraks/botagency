"use client";

import { useState, useMemo } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { AppLayout, ProtectedRoute } from "@/components/layout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import { toast } from "sonner";
import { format } from "date-fns";
import { fr } from "date-fns/locale";
import { 
  Search, 
  Trash2, 
  Eye, 
  TrendingUp, 
  TrendingDown, 
  Minus,
  Music,
  Users,
  DollarSign,
  Calendar,
  ChevronLeft,
  ChevronRight,
  BarChart3,
  Youtube,
  Instagram,
  Brain,
  Zap,
  Target,
  Shield,
  AlertTriangle,
  Sparkles,
  LineChart,
  Lightbulb,
  Loader2,
  AtSign,
  CheckCircle,
  CheckCircle2,
  Clock,
  XCircle,
  RefreshCw,
  Play,
  User,
  Mail,
  Building2,
  Globe,
  History,
} from "lucide-react";
import { ArtistPredictionsPanel } from "@/components/artist/ArtistPredictionsPanel";

// ============================================================================
// ICONS
// ============================================================================

const SpotifyIcon = ({ className }: { className?: string }) => (
  <svg className={className} viewBox="0 0 24 24" fill="currentColor">
    <path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15 10.561 18.72 12.84c.361.181.54.78.241 1.2zm.12-3.36C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.601.18-1.2.72-1.381 4.26-1.26 11.28-1.02 15.721 1.621.539.3.719 1.02.419 1.56-.299.421-1.02.599-1.559.3z"/>
  </svg>
);

const TiktokIcon = ({ className }: { className?: string }) => (
  <svg className={className} viewBox="0 0 24 24" fill="currentColor">
    <path d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-5.2 1.74 2.89 2.89 0 0 1 2.31-4.64 2.93 2.93 0 0 1 .88.13V9.4a6.84 6.84 0 0 0-1-.05A6.33 6.33 0 0 0 5 20.1a6.34 6.34 0 0 0 10.86-4.43v-7a8.16 8.16 0 0 0 4.77 1.52v-3.4a4.85 4.85 0 0 1-1-.1z"/>
  </svg>
);

const ViberateIcon = ({ className }: { className?: string }) => (
  <svg className={className} viewBox="0 0 24 24" fill="currentColor">
    <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" fill="none"/>
    <path d="M8 12 L11 15 L16 9" stroke="currentColor" strokeWidth="2" fill="none"/>
  </svg>
);

// ============================================================================
// TYPES
// ============================================================================

type InputType = "NAME" | "SPOTIFY_URL" | "VIBERATE_URL";

interface WebArtistProfile {
  name: string;
  real_name?: string;
  genre: string;
  sub_genres: string[];
  nationality: string;
  birth_year?: number;
  image_url?: string;
  social_metrics: {
    total_followers: number;
    spotify_monthly_listeners: number;
    youtube_subscribers: number;
    youtube_total_views: number;
    instagram_followers: number;
    tiktok_followers: number;
    platforms: Array<{
      platform: string;
      followers: number;
      monthly_listeners: number;
      url?: string;
    }>;
  };
  concerts: {
    upcoming: Array<{
      name: string;
      date?: string;
      venue: string;
      city: string;
      ticket_price_range?: { min?: number; max?: number };
      is_sold_out: boolean;
      source: string;
    }>;
    past: Array<{
      name: string;
      date?: string;
      venue: string;
      city: string;
    }>;
    festivals_played: string[];
  };
  business: {
    record_label?: string;
    management?: string;
    booking_email?: string;
    official_website?: string;
    distributor?: string;
  };
  financials: {
    estimated_fee_min: number;
    estimated_fee_max: number;
    popularity_score: number;
    market_tier: string;
  };
  ai_intelligence?: {
    ai_summary?: string;
    overall_trend?: string;
    risk_score: number;
    opportunity_score: number;
    market_analysis: {
      strengths: string[];
      weaknesses: string[];
      opportunities: string[];
      threats: string[];
    };
    recommendations: string[];
    predictions?: {
      short_term?: { days: number; prediction: string; confidence: number };
      medium_term?: { days: number; prediction: string; confidence: number };
      long_term?: { days: number; prediction: string; confidence: number };
    };
    booking_intelligence?: {
      optimal_fee?: number;
      negotiation_tips?: string[];
      best_booking_window?: string;
      venue_recommendations?: string[];
    };
  };
}

interface TaskResult {
  ready: boolean;
  status: string;
  result?: {
    artist: string;
    status: string;
    result: WebArtistProfile;
    ai_score?: number;
    ai_tier?: string;
  };
  error?: string;
}

interface SearchHistoryItem {
  id: string;
  artist_name: string;
  status: "pending" | "running" | "done" | "error";
  timestamp: Date;
  result?: TaskResult;
}

interface ArtistAnalysis {
  id: number;
  artist_name: string;
  real_name?: string;
  genre?: string;
  image_url?: string;
  spotify_monthly_listeners: number;
  youtube_subscribers: number;
  instagram_followers: number;
  tiktok_followers: number;
  total_followers: number;
  fee_min: number;
  fee_max: number;
  market_tier?: string;
  popularity_score: number;
  record_label?: string;
  management?: string;
  booking_agency?: string;
  booking_email?: string;
  market_trend: string;
  confidence_score: number;
  sources_scanned?: string;
  created_at: string;
  ai_score?: number;
  ai_tier?: string;
}

interface HistoryResponse {
  items: ArtistAnalysis[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

interface Statistics {
  total_analyses: number;
  unique_artists: number;
  avg_fee_min: number;
  avg_fee_max: number;
  total_fee_min: number;
  total_fee_max: number;
  most_searched_artist?: string;
  tier_distribution: Record<string, number>;
  avg_ai_score?: number;
}

// ============================================================================
// HELPERS
// ============================================================================

function formatNumber(num: number | undefined): string {
  if (!num) return "N/A";
  if (num >= 1_000_000) return `${(num / 1_000_000).toFixed(1)}M`;
  if (num >= 1_000) return `${(num / 1_000).toFixed(0)}K`;
  return num.toString();
}

const detectInputType = (value: string): InputType => {
  if (value.includes("open.spotify.com")) return "SPOTIFY_URL";
  if (value.includes("viberate.com")) return "VIBERATE_URL";
  return "NAME";
};

function getTrendIcon(trend: string) {
  switch (trend) {
    case "rising":
    case "explosive":
    case "rapid":
    case "strong":
      return <TrendingUp className="h-4 w-4 text-green-500" />;
    case "declining":
    case "falling":
      return <TrendingDown className="h-4 w-4 text-red-500" />;
    default:
      return <Minus className="h-4 w-4 text-gray-500" />;
  }
}

function getTrendLabel(trend: string) {
  const labels: Record<string, string> = {
    rising: "En hausse 🚀",
    explosive: "Explosive 🔥",
    rapid: "Rapide ⚡",
    strong: "Fort 📈",
    moderate: "Modéré",
    stable: "Stable",
    declining: "En baisse",
    falling: "Chute 📉",
  };
  return labels[trend] || trend;
}

function getTierLabel(tier: string) {
  const tiers: Record<string, { label: string; color: string }> = {
    emerging: { label: "Émergent", color: "bg-blue-100 text-blue-800" },
    underground: { label: "Underground", color: "bg-gray-100 text-gray-800" },
    developing: { label: "En développement", color: "bg-cyan-100 text-cyan-800" },
    rising: { label: "Rising", color: "bg-teal-100 text-teal-800" },
    established: { label: "Établi", color: "bg-green-100 text-green-800" },
    major: { label: "Major", color: "bg-purple-100 text-purple-800" },
    star: { label: "Star", color: "bg-yellow-100 text-yellow-800" },
    superstar: { label: "Superstar", color: "bg-orange-100 text-orange-800" },
    mega_star: { label: "Méga Star", color: "bg-red-100 text-red-800" },
  };
  return tiers[tier] || { label: tier, color: "bg-gray-100 text-gray-800" };
}

const getTierConfig = (tier?: string) => {
  const tiers: Record<string, { label: string; className: string; emoji: string }> = {
    emerging: { label: "Émergent", className: "bg-blue-50 text-blue-700 border-blue-200", emoji: "🌱" },
    developing: { label: "En développement", className: "bg-cyan-50 text-cyan-700 border-cyan-200", emoji: "📈" },
    established: { label: "Établi", className: "bg-green-50 text-green-700 border-green-200", emoji: "✅" },
    star: { label: "Star", className: "bg-yellow-50 text-yellow-700 border-yellow-200", emoji: "⭐" },
    superstar: { label: "Superstar", className: "bg-orange-50 text-orange-700 border-orange-200", emoji: "🌟" },
    mega_star: { label: "Méga Star", className: "bg-red-50 text-red-700 border-red-200", emoji: "👑" },
  };
  return tiers[tier || ""] || { label: tier || "N/A", className: "bg-gray-50 text-gray-700 border-gray-200", emoji: "•" };
};

// ============================================================================
// MAIN PAGE
// ============================================================================

function ArtistPage() {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<"search" | "history">("search");
  
  // ===== SEARCH STATE =====
  const [searchQuery, setSearchQuery] = useState("");
  const [taskId, setTaskId] = useState<string | null>(null);
  const [polling, setPolling] = useState(false);
  const [searchHistory, setSearchHistory] = useState<SearchHistoryItem[]>([]);

  // ===== HISTORY STATE =====
  const [historySearch, setHistorySearch] = useState("");
  const [historyPage, setHistoryPage] = useState(1);
  const [selectedArtist, setSelectedArtist] = useState<ArtistAnalysis | null>(null);

  // ===== SEARCH MUTATION =====
  const analyzeMutation = useMutation({
    mutationFn: async (name: string) => {
      const response = await api.post("/ingestion/analyze-artist", {
        artist_name: name,
        force_refresh: true,
      });
      return response.data;
    },
    onSuccess: (data) => {
      setTaskId(data.task_id);
      setPolling(true);
      toast.success("🧠 Analyse IA lancée !");
      
      setSearchHistory(prev => [{
        id: data.task_id,
        artist_name: searchQuery,
        status: "running",
        timestamp: new Date(),
      }, ...prev.slice(0, 9)]);
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || "Erreur lors de l'analyse");
    },
  });

  // ===== TASK POLLING =====
  const { data: taskStatus } = useQuery<TaskResult>({
    queryKey: ["artist-task", taskId],
    queryFn: async () => {
      const response = await api.get(`/ingestion/task/${taskId}`);
      return response.data;
    },
    enabled: !!taskId && polling,
    refetchInterval: polling ? 2000 : false,
  });

  if (taskStatus?.ready && polling) {
    setPolling(false);
    setSearchHistory(prev => prev.map(item => 
      item.id === taskId 
        ? { ...item, status: taskStatus.error ? "error" : "done", result: taskStatus }
        : item
    ));
    // Refresh history after successful analysis
    queryClient.invalidateQueries({ queryKey: ["artist-history"] });
  }

  // ===== HISTORY QUERY =====
  const { data: historyData, isLoading: historyLoading } = useQuery<HistoryResponse>({
    queryKey: ["artist-history", historyPage, historySearch],
    queryFn: async () => {
      const params = new URLSearchParams({
        page: historyPage.toString(),
        per_page: "10",
      });
      if (historySearch) params.append("search", historySearch);
      const response = await api.get(`/artist-history?${params}`);
      return response.data;
    },
  });

  // ===== STATISTICS QUERY =====
  const { data: stats } = useQuery<Statistics>({
    queryKey: ["artist-stats"],
    queryFn: async () => {
      const response = await api.get("/artist-history/statistics");
      return response.data;
    },
  });

  // ===== HANDLERS =====
  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim().length >= 2) {
      analyzeMutation.mutate(searchQuery.trim());
    }
  };

  const handleReset = () => {
    setTaskId(null);
    setPolling(false);
    setSearchQuery("");
    analyzeMutation.reset();
  };

  const handleSelectHistory = (item: SearchHistoryItem) => {
    if (item.result) {
      setTaskId(item.id);
      setSearchQuery(item.artist_name);
    }
  };

  const profile = taskStatus?.result?.result;
  const aiData = profile?.ai_intelligence;
  const aiScore = taskStatus?.result?.ai_score;

  return (
    <AppLayout>
      <ProtectedRoute>
        <div className="container mx-auto py-6 px-4">
          {/* Header */}
          <div className="mb-6">
            <div className="flex items-center gap-3 mb-2">
              <div className="p-2 bg-gradient-to-br from-purple-100 to-pink-100 dark:from-purple-900/30 dark:to-pink-900/30 rounded-lg">
                <Brain className="h-6 w-6 text-purple-600" />
              </div>
              <div>
                <h1 className="text-2xl font-bold">Artistes</h1>
                <p className="text-muted-foreground">
                  Recherche IA, analyse complète et historique des artistes
                </p>
              </div>
            </div>
          </div>

          {/* Main Tabs */}
          <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as "search" | "history")} className="w-full">
            <TabsList className="grid w-full max-w-md grid-cols-2 mb-6">
              <TabsTrigger value="search" className="flex items-center gap-2">
                <Brain className="h-4 w-4" />
                Recherche IA
              </TabsTrigger>
              <TabsTrigger value="history" className="flex items-center gap-2">
                <History className="h-4 w-4" />
                Historique
              </TabsTrigger>
            </TabsList>

            {/* ===================== TAB: SEARCH ===================== */}
            <TabsContent value="search" className="space-y-6">
              <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
                {/* Main content */}
                <div className="lg:col-span-3 space-y-6">
                  {/* Search bar */}
                  <Card className="border-2 border-purple-200 dark:border-purple-800">
                    <CardContent className="p-4">
                      <form onSubmit={handleSearch} className="flex gap-3">
                        <div className="relative flex-1">
                          <Brain className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-purple-500" />
                          <Input
                            type="text"
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            placeholder="Entrez le nom d'un artiste (ex: PNL, Nekfeu, Aya Nakamura...)"
                            className="pl-11 text-lg h-12"
                            disabled={analyzeMutation.isPending || polling}
                          />
                        </div>
                        <Button
                          type="submit"
                          disabled={analyzeMutation.isPending || polling || searchQuery.trim().length < 2}
                          className="h-12 px-6 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700"
                        >
                          {analyzeMutation.isPending || polling ? (
                            <Loader2 className="h-5 w-5 animate-spin mr-2" />
                          ) : (
                            <Brain className="h-5 w-5 mr-2" />
                          )}
                          Analyser
                        </Button>
                      </form>

                      <div className="mt-3 flex flex-wrap gap-1">
                        <span className="text-xs text-muted-foreground mr-2">Sources :</span>
                        {["Spotify", "YouTube", "Wikipedia", "Discogs", "Songkick", "Bandsintown", "Ticketmaster", "Google"].map(source => (
                          <Badge key={source} variant="outline" className="text-xs">{source}</Badge>
                        ))}
                      </div>
                    </CardContent>
                  </Card>

                  {/* Loading state */}
                  {polling && (
                    <Card className="border-purple-200 dark:border-purple-800">
                      <CardContent className="py-12">
                        <div className="flex flex-col items-center justify-center space-y-4">
                          <div className="relative">
                            <Brain className="h-20 w-20 text-purple-500 animate-pulse" />
                            <Loader2 className="h-10 w-10 animate-spin text-pink-500 absolute -bottom-2 -right-2" />
                          </div>
                          <p className="text-xl font-medium">
                            Analyse IA en cours pour <strong className="text-purple-600">{searchQuery}</strong>
                          </p>
                          <div className="text-sm text-muted-foreground text-center space-y-1">
                            <p>🔍 Scan des sources web (Spotify, YouTube, Viberate...)</p>
                            <p>🧠 Génération des prédictions IA...</p>
                            <p>📊 Calcul du score et analyse SWOT...</p>
                          </div>
                          <div className="w-64">
                            <Progress value={undefined} className="h-2" />
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  )}

                  {/* Results */}
                  {taskStatus?.ready && profile && (
                    <Card>
                      <CardContent className="p-6">
                        <div className="flex justify-between items-start mb-4">
                          <h3 className="text-lg font-semibold">Résultats pour "{profile.name}"</h3>
                          <Button variant="outline" size="sm" onClick={handleReset}>
                            <RefreshCw className="h-4 w-4 mr-2" />
                            Nouvelle recherche
                          </Button>
                        </div>

                        <Tabs defaultValue="overview" className="w-full">
                          <TabsList className="grid w-full grid-cols-4 mb-4">
                            <TabsTrigger value="overview">Aperçu</TabsTrigger>
                            <TabsTrigger value="ai" className="flex items-center gap-1">
                              <Brain className="h-3 w-3" />
                              IA
                            </TabsTrigger>
                            <TabsTrigger value="predictions">Prédictions</TabsTrigger>
                            <TabsTrigger value="booking">Booking</TabsTrigger>
                          </TabsList>

                          {/* Tab: Overview */}
                          <TabsContent value="overview" className="space-y-4">
                            {/* Artist Header with AI Score */}
                            <div className="flex items-center gap-4 p-4 bg-gradient-to-r from-purple-50 to-pink-50 dark:from-purple-900/20 dark:to-pink-900/20 rounded-lg">
                              <div className="relative">
                                <div className="h-20 w-20 rounded-full overflow-hidden flex items-center justify-center bg-purple-200 dark:bg-purple-800">
                                  {profile.image_url ? (
                                    <img 
                                      src={profile.image_url} 
                                      alt={profile.name}
                                      className="h-full w-full object-cover"
                                    />
                                  ) : (
                                    <User className="h-10 w-10 text-purple-600 dark:text-purple-300" />
                                  )}
                                </div>
                                {aiScore && (
                                  <div className={`absolute -bottom-2 -right-2 w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold text-white ${
                                    aiScore >= 80 ? "bg-green-500" :
                                    aiScore >= 60 ? "bg-yellow-500" :
                                    aiScore >= 40 ? "bg-orange-500" :
                                    "bg-red-500"
                                  }`}>
                                    {aiScore.toFixed(0)}
                                  </div>
                                )}
                              </div>
                              <div className="flex-1">
                                <h3 className="text-2xl font-bold">{profile.name}</h3>
                                {profile.real_name && (
                                  <p className="text-sm text-muted-foreground">({profile.real_name})</p>
                                )}
                                <div className="flex flex-wrap gap-1 mt-2">
                                  {profile.genre !== "Unknown" && (
                                    <Badge variant="secondary">{profile.genre}</Badge>
                                  )}
                                  <Badge className={getTierLabel(profile.financials.market_tier).color}>
                                    {getTierLabel(profile.financials.market_tier).label}
                                  </Badge>
                                  {aiData?.overall_trend && (
                                    <Badge variant="outline" className="gap-1">
                                      {getTrendIcon(aiData.overall_trend)}
                                      {getTrendLabel(aiData.overall_trend)}
                                    </Badge>
                                  )}
                                </div>
                              </div>
                            </div>

                            {/* Fee Estimation */}
                            <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-800">
                              <div className="flex items-center justify-between mb-2">
                                <h4 className="font-medium flex items-center gap-2">💰 Cachet estimé</h4>
                                {aiData?.booking_intelligence?.optimal_fee && (
                                  <Badge className="bg-green-600">
                                    Optimal: {aiData.booking_intelligence.optimal_fee.toLocaleString()}€
                                  </Badge>
                                )}
                              </div>
                              <div className="text-3xl font-bold text-green-600 dark:text-green-400">
                                {profile.financials.estimated_fee_min.toLocaleString()}€ - {profile.financials.estimated_fee_max.toLocaleString()}€
                              </div>
                              <div className="mt-2 flex items-center gap-2">
                                <span className="text-sm text-muted-foreground">Score popularité:</span>
                                <Progress value={profile.financials.popularity_score} className="flex-1 h-2" />
                                <span className="text-sm font-medium">{profile.financials.popularity_score.toFixed(0)}/100</span>
                              </div>
                            </div>

                            {/* Social Metrics */}
                            <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                              <h4 className="font-medium mb-3">📊 Métriques Sociales</h4>
                              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                                {profile.social_metrics.spotify_monthly_listeners > 0 && (
                                  <div className="flex items-center gap-2 p-2 bg-white dark:bg-gray-800 rounded">
                                    <SpotifyIcon className="h-5 w-5 text-green-500" />
                                    <div>
                                      <div className="text-sm font-bold">{formatNumber(profile.social_metrics.spotify_monthly_listeners)}</div>
                                      <div className="text-xs text-muted-foreground">auditeurs/mois</div>
                                    </div>
                                  </div>
                                )}
                                {profile.social_metrics.youtube_subscribers > 0 && (
                                  <div className="flex items-center gap-2 p-2 bg-white dark:bg-gray-800 rounded">
                                    <Youtube className="h-5 w-5 text-red-500" />
                                    <div>
                                      <div className="text-sm font-bold">{formatNumber(profile.social_metrics.youtube_subscribers)}</div>
                                      <div className="text-xs text-muted-foreground">abonnés</div>
                                    </div>
                                  </div>
                                )}
                                {profile.social_metrics.instagram_followers > 0 && (
                                  <div className="flex items-center gap-2 p-2 bg-white dark:bg-gray-800 rounded">
                                    <Instagram className="h-5 w-5 text-pink-500" />
                                    <div>
                                      <div className="text-sm font-bold">{formatNumber(profile.social_metrics.instagram_followers)}</div>
                                      <div className="text-xs text-muted-foreground">followers</div>
                                    </div>
                                  </div>
                                )}
                                {profile.social_metrics.tiktok_followers > 0 && (
                                  <div className="flex items-center gap-2 p-2 bg-white dark:bg-gray-800 rounded">
                                    <TiktokIcon className="h-5 w-5" />
                                    <div>
                                      <div className="text-sm font-bold">{formatNumber(profile.social_metrics.tiktok_followers)}</div>
                                      <div className="text-xs text-muted-foreground">followers</div>
                                    </div>
                                  </div>
                                )}
                              </div>
                            </div>

                            {/* Business Info */}
                            {(profile.business.record_label || profile.business.management || profile.business.booking_email) && (
                              <div className="p-4 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
                                <h4 className="font-medium mb-3">🏢 Contacts Business</h4>
                                <div className="space-y-2 text-sm">
                                  {profile.business.record_label && (
                                    <div className="flex items-center gap-2">
                                      <Building2 className="h-4 w-4 text-muted-foreground" />
                                      <span>Label: <strong>{profile.business.record_label}</strong></span>
                                    </div>
                                  )}
                                  {profile.business.management && (
                                    <div className="flex items-center gap-2">
                                      <User className="h-4 w-4 text-muted-foreground" />
                                      <span>Management: <strong>{profile.business.management}</strong></span>
                                    </div>
                                  )}
                                  {profile.business.booking_email && (
                                    <div className="flex items-center gap-2">
                                      <Mail className="h-4 w-4 text-muted-foreground" />
                                      <a href={`mailto:${profile.business.booking_email}`} className="text-blue-600 hover:underline">
                                        {profile.business.booking_email}
                                      </a>
                                    </div>
                                  )}
                                </div>
                              </div>
                            )}

                            {/* Upcoming Concerts */}
                            {profile.concerts.upcoming.length > 0 && (
                              <div className="p-4 bg-orange-50 dark:bg-orange-900/20 rounded-lg">
                                <h4 className="font-medium mb-3">🎤 Prochains concerts</h4>
                                <div className="space-y-2">
                                  {profile.concerts.upcoming.slice(0, 5).map((concert, i) => (
                                    <div key={i} className="flex items-center justify-between p-2 bg-white dark:bg-gray-800 rounded text-sm">
                                      <div>
                                        <span className="font-medium">{concert.name}</span>
                                        <span className="text-muted-foreground"> - {concert.venue}, {concert.city}</span>
                                      </div>
                                      <div className="flex items-center gap-2">
                                        {concert.date && <span className="text-xs">{new Date(concert.date).toLocaleDateString('fr-FR')}</span>}
                                        {concert.is_sold_out && <Badge variant="destructive" className="text-xs">Sold Out</Badge>}
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                          </TabsContent>

                          {/* Tab: AI Intelligence */}
                          <TabsContent value="ai" className="space-y-4">
                            {aiData ? (
                              <>
                                {aiData.ai_summary && (
                                  <div className="p-4 bg-gradient-to-r from-purple-50 to-pink-50 dark:from-purple-900/20 dark:to-pink-900/20 rounded-lg">
                                    <h4 className="font-medium mb-2 flex items-center gap-2">
                                      <Brain className="h-4 w-4 text-purple-500" />
                                      Résumé IA
                                    </h4>
                                    <p className="text-sm">{aiData.ai_summary}</p>
                                  </div>
                                )}

                                {/* SWOT Analysis */}
                                <div className="grid grid-cols-2 gap-3">
                                  {(aiData.market_analysis.strengths?.length ?? 0) > 0 && (
                                    <div className="p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
                                      <h5 className="font-medium text-green-700 text-sm mb-2 flex items-center gap-1">
                                        <Zap className="h-3 w-3" /> Forces
                                      </h5>
                                      <ul className="text-xs space-y-1">
                                        {aiData.market_analysis.strengths?.slice(0, 4).map((s, i) => (
                                          <li key={i} className="flex items-start gap-1">
                                            <span className="text-green-500">✓</span> {s}
                                          </li>
                                        ))}
                                      </ul>
                                    </div>
                                  )}
                                  {(aiData.market_analysis.weaknesses?.length ?? 0) > 0 && (
                                    <div className="p-3 bg-red-50 dark:bg-red-900/20 rounded-lg">
                                      <h5 className="font-medium text-red-700 text-sm mb-2 flex items-center gap-1">
                                        <AlertTriangle className="h-3 w-3" /> Faiblesses
                                      </h5>
                                      <ul className="text-xs space-y-1">
                                        {aiData.market_analysis.weaknesses?.slice(0, 4).map((w, i) => (
                                          <li key={i} className="flex items-start gap-1">
                                            <span className="text-red-500">•</span> {w}
                                          </li>
                                        ))}
                                      </ul>
                                    </div>
                                  )}
                                  {(aiData.market_analysis.opportunities?.length ?? 0) > 0 && (
                                    <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                                      <h5 className="font-medium text-blue-700 text-sm mb-2 flex items-center gap-1">
                                        <Lightbulb className="h-3 w-3" /> Opportunités
                                      </h5>
                                      <ul className="text-xs space-y-1">
                                        {aiData.market_analysis.opportunities?.slice(0, 4).map((o, i) => (
                                          <li key={i} className="flex items-start gap-1">
                                            <span className="text-blue-500">→</span> {o}
                                          </li>
                                        ))}
                                      </ul>
                                    </div>
                                  )}
                                  {(aiData.market_analysis.threats?.length ?? 0) > 0 && (
                                    <div className="p-3 bg-orange-50 dark:bg-orange-900/20 rounded-lg">
                                      <h5 className="font-medium text-orange-700 text-sm mb-2 flex items-center gap-1">
                                        <Shield className="h-3 w-3" /> Menaces
                                      </h5>
                                      <ul className="text-xs space-y-1">
                                        {aiData.market_analysis.threats?.slice(0, 4).map((t, i) => (
                                          <li key={i} className="flex items-start gap-1">
                                            <span className="text-orange-500">!</span> {t}
                                          </li>
                                        ))}
                                      </ul>
                                    </div>
                                  )}
                                </div>

                                {/* Risk & Opportunity Scores */}
                                <div className="grid grid-cols-2 gap-4">
                                  <div className="p-3 border rounded-lg">
                                    <div className="flex items-center justify-between mb-2">
                                      <span className="text-sm font-medium">Score de Risque</span>
                                      <span className={`text-lg font-bold ${
                                        aiData.risk_score < 0.3 ? "text-green-600" :
                                        aiData.risk_score < 0.6 ? "text-yellow-600" : "text-red-600"
                                      }`}>
                                        {(aiData.risk_score * 100).toFixed(0)}%
                                      </span>
                                    </div>
                                    <Progress value={aiData.risk_score * 100} className="h-2" />
                                  </div>
                                  <div className="p-3 border rounded-lg">
                                    <div className="flex items-center justify-between mb-2">
                                      <span className="text-sm font-medium">Score Opportunité</span>
                                      <span className={`text-lg font-bold ${
                                        aiData.opportunity_score > 0.6 ? "text-green-600" :
                                        aiData.opportunity_score > 0.3 ? "text-yellow-600" : "text-red-600"
                                      }`}>
                                        {(aiData.opportunity_score * 100).toFixed(0)}%
                                      </span>
                                    </div>
                                    <Progress value={aiData.opportunity_score * 100} className="h-2" />
                                  </div>
                                </div>

                                {/* AI Recommendations */}
                                {(aiData.recommendations?.length ?? 0) > 0 && (
                                  <div className="p-4 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
                                    <h4 className="font-medium mb-2 flex items-center gap-2">
                                      <Sparkles className="h-4 w-4 text-yellow-500" />
                                      Recommandations IA
                                    </h4>
                                    <ul className="text-sm space-y-2">
                                      {aiData.recommendations?.slice(0, 5).map((rec, i) => (
                                        <li key={i} className="flex items-start gap-2">
                                          <span className="text-yellow-500 font-bold">{i + 1}.</span>
                                          {rec}
                                        </li>
                                      ))}
                                    </ul>
                                  </div>
                                )}
                              </>
                            ) : (
                              <div className="text-center py-8 text-muted-foreground">
                                <Brain className="h-12 w-12 mx-auto mb-4 opacity-50" />
                                <p>Données IA non disponibles pour cet artiste</p>
                              </div>
                            )}
                          </TabsContent>

                          {/* Tab: Predictions - New Component with Snapshots */}
                          <TabsContent value="predictions" className="space-y-4">
                            <ArtistPredictionsPanel 
                              artistName={profile.name} 
                              onRefresh={() => {
                                // Trigger a new analysis
                                setSearchQuery(profile.name);
                                analyzeMutation.mutate(profile.name);
                              }}
                            />
                          </TabsContent>

                          {/* Tab: Booking */}
                          <TabsContent value="booking" className="space-y-4">
                            {aiData?.booking_intelligence ? (
                              <>
                                {aiData.booking_intelligence.optimal_fee && (
                                  <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
                                    <h4 className="font-medium mb-2">💰 Cachet optimal recommandé</h4>
                                    <div className="text-3xl font-bold text-green-600">
                                      {aiData.booking_intelligence.optimal_fee.toLocaleString()}€
                                    </div>
                                  </div>
                                )}

                                {aiData.booking_intelligence.best_booking_window && (
                                  <div className="p-4 border rounded-lg">
                                    <h4 className="font-medium mb-2 flex items-center gap-2">
                                      <Calendar className="h-4 w-4" />
                                      Meilleure période de booking
                                    </h4>
                                    <p>{aiData.booking_intelligence.best_booking_window}</p>
                                  </div>
                                )}

                                {(aiData.booking_intelligence.negotiation_tips?.length ?? 0) > 0 && (
                                  <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                                    <h4 className="font-medium mb-2 flex items-center gap-2">
                                      <Target className="h-4 w-4 text-blue-500" />
                                      Tips de négociation
                                    </h4>
                                    <ul className="text-sm space-y-1">
                                      {aiData.booking_intelligence.negotiation_tips?.map((tip, i) => (
                                        <li key={i} className="flex items-start gap-2">
                                          <span className="text-blue-500">•</span> {tip}
                                        </li>
                                      ))}
                                    </ul>
                                  </div>
                                )}

                                {(aiData.booking_intelligence.venue_recommendations?.length ?? 0) > 0 && (
                                  <div className="p-4 border rounded-lg">
                                    <h4 className="font-medium mb-2 flex items-center gap-2">
                                      <Globe className="h-4 w-4" />
                                      Salles recommandées
                                    </h4>
                                    <div className="flex flex-wrap gap-2">
                                      {aiData.booking_intelligence.venue_recommendations?.map((venue, i) => (
                                        <Badge key={i} variant="secondary">{venue}</Badge>
                                      ))}
                                    </div>
                                  </div>
                                )}
                              </>
                            ) : (
                              <div className="text-center py-8 text-muted-foreground">
                                <Target className="h-12 w-12 mx-auto mb-4 opacity-50" />
                                <p>Données booking non disponibles</p>
                              </div>
                            )}
                          </TabsContent>
                        </Tabs>
                      </CardContent>
                    </Card>
                  )}

                  {/* Empty state */}
                  {!taskId && !polling && (
                    <div className="text-center py-16">
                      <div className="w-24 h-24 bg-gradient-to-br from-purple-100 to-pink-100 dark:from-purple-900/30 dark:to-pink-900/30 rounded-full flex items-center justify-center mx-auto mb-6">
                        <Brain className="h-12 w-12 text-purple-500" />
                      </div>
                      <h3 className="text-xl font-semibold mb-3">Analyse IA d'artiste</h3>
                      <p className="text-muted-foreground max-w-md mx-auto mb-6">
                        Entrez le nom d'un artiste pour lancer un scan web complet avec analyse IA : 
                        données sociales, prédictions, SWOT, stratégie de booking.
                      </p>
                      <div className="grid grid-cols-2 md:grid-cols-3 gap-3 max-w-lg mx-auto text-sm">
                        <div className="flex items-center gap-2 p-2 bg-muted rounded">
                          <CheckCircle className="h-4 w-4 text-green-500" />
                          Score IA global
                        </div>
                        <div className="flex items-center gap-2 p-2 bg-muted rounded">
                          <CheckCircle className="h-4 w-4 text-green-500" />
                          Analyse SWOT
                        </div>
                        <div className="flex items-center gap-2 p-2 bg-muted rounded">
                          <CheckCircle className="h-4 w-4 text-green-500" />
                          Prédictions 30/90/180j
                        </div>
                        <div className="flex items-center gap-2 p-2 bg-muted rounded">
                          <CheckCircle className="h-4 w-4 text-green-500" />
                          Cachet estimé
                        </div>
                        <div className="flex items-center gap-2 p-2 bg-muted rounded">
                          <CheckCircle className="h-4 w-4 text-green-500" />
                          Contacts business
                        </div>
                        <div className="flex items-center gap-2 p-2 bg-muted rounded">
                          <CheckCircle className="h-4 w-4 text-green-500" />
                          Intelligence booking
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                {/* Sidebar - History */}
                <div className="space-y-4">
                  <Card>
                    <CardHeader className="pb-3">
                      <CardTitle className="text-base">Recherches récentes</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-2">
                      {searchHistory.length === 0 ? (
                        <p className="text-sm text-muted-foreground text-center py-4">
                          Aucune recherche récente
                        </p>
                      ) : (
                        searchHistory.map((item) => (
                          <button
                            key={item.id}
                            onClick={() => handleSelectHistory(item)}
                            disabled={item.status === "running"}
                            className="w-full text-left p-3 rounded-lg border hover:bg-muted/50 transition-colors disabled:opacity-50"
                          >
                            <div className="flex items-center justify-between">
                              <div className="flex items-center gap-2">
                                {item.status === "running" ? (
                                  <Loader2 className="h-4 w-4 animate-spin text-purple-500" />
                                ) : item.status === "done" ? (
                                  <CheckCircle className="h-4 w-4 text-green-500" />
                                ) : item.status === "error" ? (
                                  <XCircle className="h-4 w-4 text-red-500" />
                                ) : (
                                  <Clock className="h-4 w-4 text-yellow-500" />
                                )}
                                <span className="font-medium truncate max-w-[150px]">{item.artist_name}</span>
                              </div>
                              <ChevronRight className="h-4 w-4 text-muted-foreground" />
                            </div>
                            <p className="text-xs text-muted-foreground mt-1">
                              {item.timestamp.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}
                            </p>
                          </button>
                        ))
                      )}
                    </CardContent>
                  </Card>

                  {/* Features */}
                  <Card className="bg-gradient-to-br from-purple-50 to-pink-50 dark:from-purple-900/20 dark:to-pink-900/20">
                    <CardHeader className="pb-3">
                      <CardTitle className="text-base flex items-center gap-2">
                        <Brain className="h-4 w-4 text-purple-500" />
                        Fonctionnalités IA
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="text-sm space-y-2">
                      <div className="flex items-center gap-2">
                        <SpotifyIcon className="h-4 w-4 text-green-500" />
                        Données Spotify réelles
                      </div>
                      <div className="flex items-center gap-2">
                        <Youtube className="h-4 w-4 text-red-500" />
                        Stats YouTube
                      </div>
                      <div className="flex items-center gap-2">
                        <Instagram className="h-4 w-4 text-pink-500" />
                        Réseaux sociaux
                      </div>
                      <div className="flex items-center gap-2">
                        <Calendar className="h-4 w-4 text-orange-500" />
                        Concerts & festivals
                      </div>
                      <div className="flex items-center gap-2">
                        <Target className="h-4 w-4 text-blue-500" />
                        Intelligence booking
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </div>
            </TabsContent>

            {/* ===================== TAB: HISTORY ===================== */}
            <TabsContent value="history" className="space-y-6">
              {/* Stats Cards */}
              {stats && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <Card>
                    <CardContent className="pt-6">
                      <div className="flex items-center gap-3">
                        <div className="p-2 bg-purple-100 rounded-lg">
                          <BarChart3 className="h-5 w-5 text-purple-600" />
                        </div>
                        <div>
                          <p className="text-2xl font-bold">{stats.total_analyses}</p>
                          <p className="text-sm text-muted-foreground">Analyses totales</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent className="pt-6">
                      <div className="flex items-center gap-3">
                        <div className="p-2 bg-blue-100 rounded-lg">
                          <Users className="h-5 w-5 text-blue-600" />
                        </div>
                        <div>
                          <p className="text-2xl font-bold">{stats.unique_artists}</p>
                          <p className="text-sm text-muted-foreground">Artistes uniques</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent className="pt-6">
                      <div className="flex items-center gap-3">
                        <div className="p-2 bg-green-100 rounded-lg">
                          <DollarSign className="h-5 w-5 text-green-600" />
                        </div>
                        <div>
                          <p className="text-2xl font-bold">{formatNumber(stats.avg_fee_min)}€</p>
                          <p className="text-sm text-muted-foreground">Cachet moyen min</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent className="pt-6">
                      <div className="flex items-center gap-3">
                        <div className="p-2 bg-orange-100 rounded-lg">
                          <Brain className="h-5 w-5 text-orange-600" />
                        </div>
                        <div>
                          <p className="text-2xl font-bold">{stats.avg_ai_score?.toFixed(0) || "N/A"}</p>
                          <p className="text-sm text-muted-foreground">Score IA moyen</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              )}

              {/* Search and Table */}
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle>Historique des analyses</CardTitle>
                    <div className="relative w-64">
                      <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                      <Input
                        placeholder="Rechercher un artiste..."
                        value={historySearch}
                        onChange={(e) => {
                          setHistorySearch(e.target.value);
                          setHistoryPage(1);
                        }}
                        className="pl-9"
                      />
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  {historyLoading ? (
                    <div className="space-y-3">
                      {[1, 2, 3, 4, 5].map((i) => (
                        <Skeleton key={i} className="h-16 w-full" />
                      ))}
                    </div>
                  ) : historyData?.items.length === 0 ? (
                    <div className="text-center py-12 text-muted-foreground">
                      <History className="h-12 w-12 mx-auto mb-4 opacity-50" />
                      <p>Aucune analyse trouvée</p>
                    </div>
                  ) : (
                    <>
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Artiste</TableHead>
                            <TableHead>Genre</TableHead>
                            <TableHead>Tier</TableHead>
                            <TableHead>Cachet</TableHead>
                            <TableHead>Score IA</TableHead>
                            <TableHead>Date</TableHead>
                            <TableHead className="text-right">Actions</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {historyData?.items.map((artist) => {
                            const tierConfig = getTierConfig(artist.market_tier);
                            return (
                              <TableRow key={artist.id}>
                                <TableCell>
                                  <div className="flex items-center gap-3">
                                    <div className="h-10 w-10 rounded-full bg-purple-100 flex items-center justify-center overflow-hidden">
                                      {artist.image_url ? (
                                        <img src={artist.image_url} alt={artist.artist_name} className="h-full w-full object-cover" />
                                      ) : (
                                        <Music className="h-5 w-5 text-purple-600" />
                                      )}
                                    </div>
                                    <div>
                                      <p className="font-medium">{artist.artist_name}</p>
                                      {artist.record_label && (
                                        <p className="text-xs text-muted-foreground">{artist.record_label}</p>
                                      )}
                                    </div>
                                  </div>
                                </TableCell>
                                <TableCell>{artist.genre || "N/A"}</TableCell>
                                <TableCell>
                                  <Badge className={tierConfig.className}>
                                    {tierConfig.emoji} {tierConfig.label}
                                  </Badge>
                                </TableCell>
                                <TableCell>
                                  {formatNumber(artist.fee_min)}€ - {formatNumber(artist.fee_max)}€
                                </TableCell>
                                <TableCell>
                                  {artist.ai_score ? (
                                    <div className={`inline-flex items-center justify-center w-10 h-10 rounded-full text-sm font-bold text-white ${
                                      artist.ai_score >= 80 ? "bg-green-500" :
                                      artist.ai_score >= 60 ? "bg-yellow-500" :
                                      artist.ai_score >= 40 ? "bg-orange-500" :
                                      "bg-red-500"
                                    }`}>
                                      {artist.ai_score.toFixed(0)}
                                    </div>
                                  ) : (
                                    <span className="text-muted-foreground">N/A</span>
                                  )}
                                </TableCell>
                                <TableCell>
                                  {format(new Date(artist.created_at), "dd/MM/yyyy HH:mm", { locale: fr })}
                                </TableCell>
                                <TableCell className="text-right">
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => setSelectedArtist(artist)}
                                  >
                                    <Eye className="h-4 w-4" />
                                  </Button>
                                </TableCell>
                              </TableRow>
                            );
                          })}
                        </TableBody>
                      </Table>

                      {/* Pagination */}
                      {historyData && historyData.total_pages > 1 && (
                        <div className="flex items-center justify-between mt-4">
                          <p className="text-sm text-muted-foreground">
                            Page {historyData.page} sur {historyData.total_pages} ({historyData.total} résultats)
                          </p>
                          <div className="flex gap-2">
                            <Button
                              variant="outline"
                              size="sm"
                              disabled={historyPage === 1}
                              onClick={() => setHistoryPage(p => p - 1)}
                            >
                              <ChevronLeft className="h-4 w-4" />
                            </Button>
                            <Button
                              variant="outline"
                              size="sm"
                              disabled={historyPage === historyData.total_pages}
                              onClick={() => setHistoryPage(p => p + 1)}
                            >
                              <ChevronRight className="h-4 w-4" />
                            </Button>
                          </div>
                        </div>
                      )}
                    </>
                  )}
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>

          {/* Detail Dialog for History */}
          <Dialog open={!!selectedArtist} onOpenChange={() => setSelectedArtist(null)}>
            <DialogContent className="max-w-2xl">
              <DialogHeader>
                <DialogTitle className="flex items-center gap-3">
                  {selectedArtist?.image_url ? (
                    <img src={selectedArtist.image_url} alt={selectedArtist.artist_name} className="h-12 w-12 rounded-full object-cover" />
                  ) : (
                    <div className="h-12 w-12 rounded-full bg-purple-100 flex items-center justify-center">
                      <Music className="h-6 w-6 text-purple-600" />
                    </div>
                  )}
                  {selectedArtist?.artist_name}
                </DialogTitle>
                <DialogDescription>
                  Analyse du {selectedArtist && format(new Date(selectedArtist.created_at), "dd MMMM yyyy à HH:mm", { locale: fr })}
                </DialogDescription>
              </DialogHeader>
              
              {selectedArtist && (
                <div className="space-y-4 mt-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-4 bg-green-50 rounded-lg">
                      <p className="text-sm text-muted-foreground">Cachet estimé</p>
                      <p className="text-xl font-bold text-green-600">
                        {formatNumber(selectedArtist.fee_min)}€ - {formatNumber(selectedArtist.fee_max)}€
                      </p>
                    </div>
                    <div className="p-4 bg-purple-50 rounded-lg">
                      <p className="text-sm text-muted-foreground">Score IA</p>
                      <p className="text-xl font-bold text-purple-600">
                        {selectedArtist.ai_score?.toFixed(0) || "N/A"}/100
                      </p>
                    </div>
                  </div>

                  <div className="grid grid-cols-4 gap-3">
                    <div className="p-3 border rounded-lg text-center">
                      <SpotifyIcon className="h-5 w-5 text-green-500 mx-auto mb-1" />
                      <p className="text-sm font-bold">{formatNumber(selectedArtist.spotify_monthly_listeners)}</p>
                      <p className="text-xs text-muted-foreground">Spotify</p>
                    </div>
                    <div className="p-3 border rounded-lg text-center">
                      <Youtube className="h-5 w-5 text-red-500 mx-auto mb-1" />
                      <p className="text-sm font-bold">{formatNumber(selectedArtist.youtube_subscribers)}</p>
                      <p className="text-xs text-muted-foreground">YouTube</p>
                    </div>
                    <div className="p-3 border rounded-lg text-center">
                      <Instagram className="h-5 w-5 text-pink-500 mx-auto mb-1" />
                      <p className="text-sm font-bold">{formatNumber(selectedArtist.instagram_followers)}</p>
                      <p className="text-xs text-muted-foreground">Instagram</p>
                    </div>
                    <div className="p-3 border rounded-lg text-center">
                      <TiktokIcon className="h-5 w-5 mx-auto mb-1" />
                      <p className="text-sm font-bold">{formatNumber(selectedArtist.tiktok_followers)}</p>
                      <p className="text-xs text-muted-foreground">TikTok</p>
                    </div>
                  </div>

                  {(selectedArtist.record_label || selectedArtist.management || selectedArtist.booking_email) && (
                    <div className="p-4 bg-gray-50 rounded-lg">
                      <h4 className="font-medium mb-2">Contacts Business</h4>
                      <div className="space-y-1 text-sm">
                        {selectedArtist.record_label && <p>Label: <strong>{selectedArtist.record_label}</strong></p>}
                        {selectedArtist.management && <p>Management: <strong>{selectedArtist.management}</strong></p>}
                        {selectedArtist.booking_email && (
                          <p>Email: <a href={`mailto:${selectedArtist.booking_email}`} className="text-blue-600 hover:underline">{selectedArtist.booking_email}</a></p>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </DialogContent>
          </Dialog>
        </div>
      </ProtectedRoute>
    </AppLayout>
  );
}

export default ArtistPage;
