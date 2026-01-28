"use client";

import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Search,
  Music,
  Users,
  ExternalLink,
  Loader2,
  AlertCircle,
  CheckCircle,
  Clock,
  TrendingUp,
  Disc3,
  RefreshCw,
  ChevronRight,
  Plus,
  Sparkles,
} from "lucide-react";
import { AppLayout, ProtectedRoute } from "@/components/layout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "sonner";
import Link from "next/link";
import { api } from "@/lib/api";

// ============================================================================
// TYPES
// ============================================================================

interface SpotifyArtistResult {
  spotify_id: string;
  name: string;
  image_url?: string;
  followers: number;
  popularity: number;
  genres: string[];
  monthly_listeners?: number;
  monthly_listeners_source: string;
  spotify_url?: string;
  label?: string;
  management?: string;
  social_stats?: {
    spotify_followers?: number;
    youtube_subscribers?: number;
    instagram_followers?: number;
    tiktok_followers?: number;
  };
}

interface SpotifyJobResponse {
  id: string;
  query: string;
  status: string;
  current_step: string;
  progress: number;
  results_count: number;
  started_at?: string;
  completed_at?: string;
  error_message?: string;
}

interface SpotifySearchResultsResponse {
  job: SpotifyJobResponse;
  results: SpotifyArtistResult[];
}

interface SpotifyQueueResponse {
  jobs: SpotifyJobResponse[];
  running: number;
  pending: number;
  completed_24h: number;
}

// ============================================================================
// API FUNCTIONS
// ============================================================================

const createSpotifySearch = async (query: string, limit: number = 10): Promise<SpotifyJobResponse> => {
  const response = await api.post("/spotify-search/search", { query, limit });
  return response.data;
};

const fetchSpotifyJob = async (jobId: string): Promise<SpotifySearchResultsResponse> => {
  const response = await api.get(`/spotify-search/job/${jobId}`);
  return response.data;
};

const fetchSpotifyQueue = async (): Promise<SpotifyQueueResponse> => {
  const response = await api.get("/spotify-search/queue");
  return response.data;
};

// ============================================================================
// COMPONENTS
// ============================================================================

function formatNumber(num: number | undefined): string {
  if (!num) return "N/A";
  if (num >= 1_000_000) return `${(num / 1_000_000).toFixed(1)}M`;
  if (num >= 1_000) return `${(num / 1_000).toFixed(1)}K`;
  return num.toString();
}

function getStatusColor(status: string): string {
  switch (status) {
    case "DONE":
      return "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400";
    case "RUNNING":
      return "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400";
    case "QUEUED":
      return "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400";
    case "FAILED":
      return "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400";
    default:
      return "bg-gray-100 text-gray-700 dark:bg-gray-900/30 dark:text-gray-400";
  }
}

function getStatusIcon(status: string) {
  switch (status) {
    case "DONE":
      return <CheckCircle className="h-4 w-4" />;
    case "RUNNING":
      return <Loader2 className="h-4 w-4 animate-spin" />;
    case "QUEUED":
      return <Clock className="h-4 w-4" />;
    case "FAILED":
      return <AlertCircle className="h-4 w-4" />;
    default:
      return <Clock className="h-4 w-4" />;
  }
}

function ArtistCard({ artist }: { artist: SpotifyArtistResult }) {
  return (
    <Card className="group hover:shadow-lg transition-all duration-200 border-l-4 border-l-green-500">
      <CardContent className="p-4">
        <div className="flex items-start gap-4">
          {/* Artist Image */}
          <div className="relative">
            {artist.image_url ? (
              <img
                src={artist.image_url}
                alt={artist.name}
                className="w-16 h-16 rounded-lg object-cover"
              />
            ) : (
              <div className="w-16 h-16 rounded-lg bg-gradient-to-br from-green-500 to-emerald-600 flex items-center justify-center">
                <Music className="h-8 w-8 text-white" />
              </div>
            )}
            {/* Popularity badge */}
            <div className="absolute -bottom-1 -right-1 bg-green-500 text-white text-xs font-bold rounded-full w-6 h-6 flex items-center justify-center">
              {artist.popularity}
            </div>
          </div>

          {/* Artist Info */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <h3 className="font-semibold text-lg truncate">{artist.name}</h3>
              {artist.spotify_url && (
                <a
                  href={artist.spotify_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-green-500 hover:text-green-600"
                >
                  <ExternalLink className="h-4 w-4" />
                </a>
              )}
            </div>

            {/* Genres */}
            {artist.genres.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-1">
                {artist.genres.slice(0, 3).map((genre) => (
                  <Badge key={genre} variant="secondary" className="text-xs">
                    {genre}
                  </Badge>
                ))}
                {artist.genres.length > 3 && (
                  <Badge variant="outline" className="text-xs">
                    +{artist.genres.length - 3}
                  </Badge>
                )}
              </div>
            )}

            {/* Metrics */}
            <div className="grid grid-cols-2 gap-2 mt-3">
              <div className="flex items-center gap-1 text-sm">
                <Users className="h-4 w-4 text-muted-foreground" />
                <span className="font-medium">{formatNumber(artist.followers)}</span>
                <span className="text-xs text-muted-foreground">followers</span>
              </div>
              <div className="flex items-center gap-1 text-sm">
                <TrendingUp className="h-4 w-4 text-muted-foreground" />
                <span className="font-medium">{formatNumber(artist.monthly_listeners)}</span>
                <span className="text-xs text-muted-foreground">
                  listeners
                  {artist.monthly_listeners_source === "estimated" && " (est.)"}
                </span>
              </div>
            </div>

            {/* Label & Management */}
            {(artist.label || artist.management) && (
              <div className="flex flex-wrap gap-2 mt-2">
                {artist.label && (
                  <Badge variant="outline" className="text-xs">
                    <Disc3 className="h-3 w-3 mr-1" />
                    {artist.label}
                  </Badge>
                )}
                {artist.management && (
                  <Badge variant="outline" className="text-xs">
                    {artist.management}
                  </Badge>
                )}
              </div>
            )}
          </div>

          {/* Actions */}
          <div className="flex flex-col gap-2">
            <Button size="sm" variant="outline" asChild>
              <Link href={`/artist-history?search=${encodeURIComponent(artist.name)}`}>
                <Sparkles className="h-4 w-4 mr-1" />
                Analyser
              </Link>
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function JobQueueItem({ job, onClick }: { job: SpotifyJobResponse; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="w-full text-left p-3 rounded-lg border hover:bg-muted/50 transition-colors"
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Badge className={getStatusColor(job.status)}>
            {getStatusIcon(job.status)}
          </Badge>
          <span className="font-medium truncate max-w-[150px]">{job.query}</span>
        </div>
        <ChevronRight className="h-4 w-4 text-muted-foreground" />
      </div>
      {job.status === "RUNNING" && (
        <div className="mt-2">
          <div className="flex items-center justify-between text-xs text-muted-foreground mb-1">
            <span>{job.current_step}</span>
            <span>{job.progress}%</span>
          </div>
          <div className="h-1.5 bg-muted rounded-full overflow-hidden">
            <div
              className="h-full bg-green-500 transition-all duration-300"
              style={{ width: `${job.progress}%` }}
            />
          </div>
        </div>
      )}
      {job.status === "DONE" && job.results_count > 0 && (
        <p className="text-xs text-muted-foreground mt-1">
          {job.results_count} résultat(s)
        </p>
      )}
    </button>
  );
}

function ResultsSkeleton() {
  return (
    <div className="space-y-4">
      {Array.from({ length: 5 }).map((_, i) => (
        <Card key={i}>
          <CardContent className="p-4">
            <div className="flex items-start gap-4">
              <Skeleton className="w-16 h-16 rounded-lg" />
              <div className="flex-1 space-y-2">
                <Skeleton className="h-5 w-40" />
                <Skeleton className="h-4 w-60" />
                <div className="flex gap-2">
                  <Skeleton className="h-4 w-20" />
                  <Skeleton className="h-4 w-20" />
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

// ============================================================================
// MAIN PAGE
// ============================================================================

function SpotifySearchPage() {
  const queryClient = useQueryClient();
  const [searchQuery, setSearchQuery] = useState("");
  const [activeJobId, setActiveJobId] = useState<string | null>(null);

  // Queue query
  const queueQuery = useQuery({
    queryKey: ["spotify-queue"],
    queryFn: fetchSpotifyQueue,
    refetchInterval: 3000,
  });

  // Active job results
  const jobQuery = useQuery({
    queryKey: ["spotify-job", activeJobId],
    queryFn: () => (activeJobId ? fetchSpotifyJob(activeJobId) : null),
    enabled: !!activeJobId,
    refetchInterval: (data) => {
      if (data?.state?.data?.job?.status === "RUNNING" || data?.state?.data?.job?.status === "QUEUED") {
        return 2000;
      }
      return false;
    },
  });

  // Search mutation
  const searchMutation = useMutation({
    mutationFn: (query: string) => createSpotifySearch(query),
    onSuccess: (data) => {
      toast.success("🎵 Recherche Spotify lancée !");
      setActiveJobId(data.id);
      queryClient.invalidateQueries({ queryKey: ["spotify-queue"] });
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || "Erreur lors de la recherche");
    },
  });

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim().length >= 2) {
      searchMutation.mutate(searchQuery.trim());
    }
  };

  // Auto-select latest running job
  useEffect(() => {
    if (!activeJobId && queueQuery.data?.jobs.length) {
      const runningJob = queueQuery.data.jobs.find(
        (j) => j.status === "RUNNING" || j.status === "QUEUED"
      );
      if (runningJob) {
        setActiveJobId(runningJob.id);
      }
    }
  }, [queueQuery.data, activeJobId]);

  return (
    <AppLayout>
      <ProtectedRoute>
        <div className="container mx-auto py-6 px-4">
          {/* Header */}
          <div className="mb-6">
            <div className="flex items-center gap-3 mb-2">
              <div className="p-2 bg-green-100 dark:bg-green-900/30 rounded-lg">
                <Music className="h-6 w-6 text-green-600" />
              </div>
              <div>
                <h1 className="text-2xl font-bold">Spotify Search</h1>
                <p className="text-muted-foreground">
                  Recherchez des artistes sur Spotify avec enrichissement automatique
                </p>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
            {/* Main content */}
            <div className="lg:col-span-3 space-y-6">
              {/* Search bar */}
              <Card>
                <CardContent className="p-4">
                  <form onSubmit={handleSearch} className="flex gap-3">
                    <div className="relative flex-1">
                      <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                      <Input
                        type="text"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        placeholder="Rechercher un artiste sur Spotify..."
                        className="pl-9"
                        disabled={searchMutation.isPending}
                      />
                    </div>
                    <Button
                      type="submit"
                      disabled={searchMutation.isPending || searchQuery.trim().length < 2}
                      className="bg-green-600 hover:bg-green-700"
                    >
                      {searchMutation.isPending ? (
                        <Loader2 className="h-4 w-4 animate-spin mr-2" />
                      ) : (
                        <Search className="h-4 w-4 mr-2" />
                      )}
                      Rechercher
                    </Button>
                  </form>
                </CardContent>
              </Card>

              {/* Active search indicator */}
              {(queueQuery.data?.running ?? 0) > 0 && (
                <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
                  <div className="flex items-center gap-3">
                    <Loader2 className="h-5 w-5 text-green-600 animate-spin" />
                    <div>
                      <h4 className="text-sm font-medium text-green-800 dark:text-green-300">
                        Recherche en cours...
                      </h4>
                      <p className="text-sm text-green-600 dark:text-green-400">
                        {queueQuery.data?.running} recherche(s) active(s)
                      </p>
                    </div>
                    <div className="ml-auto flex gap-2">
                      <Badge className="bg-green-100 text-green-700">
                        <span className="animate-pulse">●</span>
                        <span className="ml-1">{jobQuery.data?.job?.current_step || "SEARCH"}</span>
                      </Badge>
                      {jobQuery.data?.job && (
                        <span className="text-sm text-green-600">{jobQuery.data.job.progress}%</span>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* Pending searches */}
              {(queueQuery.data?.pending ?? 0) > 0 && (
                <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
                  <div className="flex items-center gap-3">
                    <Clock className="h-5 w-5 text-yellow-600" />
                    <p className="text-sm text-yellow-800 dark:text-yellow-300">
                      {queueQuery.data?.pending} recherche(s) en attente
                    </p>
                  </div>
                </div>
              )}

              {/* Results */}
              {jobQuery.isLoading && activeJobId && <ResultsSkeleton />}

              {jobQuery.data?.results && jobQuery.data.results.length > 0 && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <h3 className="font-semibold text-lg">
                      Résultats pour "{jobQuery.data.job.query}"
                    </h3>
                    <Badge variant="outline">
                      {jobQuery.data.results.length} artiste(s)
                    </Badge>
                  </div>
                  {jobQuery.data.results.map((artist) => (
                    <ArtistCard key={artist.spotify_id} artist={artist} />
                  ))}
                </div>
              )}

              {jobQuery.data?.job?.status === "DONE" && jobQuery.data.results.length === 0 && (
                <div className="text-center py-12">
                  <AlertCircle className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                  <h3 className="text-lg font-semibold mb-2">Aucun résultat</h3>
                  <p className="text-muted-foreground">
                    Aucun artiste trouvé pour "{jobQuery.data.job.query}"
                  </p>
                </div>
              )}

              {!activeJobId && !searchMutation.isPending && (
                <div className="text-center py-16">
                  <div className="w-20 h-20 bg-gradient-to-br from-green-100 to-emerald-100 dark:from-green-900/30 dark:to-emerald-900/30 rounded-full flex items-center justify-center mx-auto mb-6">
                    <Music className="h-10 w-10 text-green-500" />
                  </div>
                  <h3 className="text-xl font-semibold mb-3">Recherchez sur Spotify</h3>
                  <p className="text-muted-foreground max-w-md mx-auto">
                    Entrez le nom d'un artiste pour lancer une recherche Spotify avec enrichissement automatique (monthly listeners, label, réseaux sociaux).
                  </p>
                </div>
              )}
            </div>

            {/* Sidebar - Queue */}
            <div className="space-y-4">
              <Card>
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-base">Historique</CardTitle>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => queryClient.invalidateQueries({ queryKey: ["spotify-queue"] })}
                    >
                      <RefreshCw className="h-4 w-4" />
                    </Button>
                  </div>
                </CardHeader>
                <CardContent className="space-y-2">
                  {queueQuery.isLoading ? (
                    <div className="space-y-2">
                      {Array.from({ length: 3 }).map((_, i) => (
                        <Skeleton key={i} className="h-12 w-full" />
                      ))}
                    </div>
                  ) : queueQuery.data?.jobs.length === 0 ? (
                    <p className="text-sm text-muted-foreground text-center py-4">
                      Aucune recherche récente
                    </p>
                  ) : (
                    queueQuery.data?.jobs.slice(0, 10).map((job) => (
                      <JobQueueItem
                        key={job.id}
                        job={job}
                        onClick={() => setActiveJobId(job.id)}
                      />
                    ))
                  )}
                </CardContent>
              </Card>

              {/* Stats */}
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-base">Statistiques</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 gap-3 text-center">
                    <div className="p-3 bg-muted rounded-lg">
                      <div className="text-2xl font-bold text-green-600">
                        {queueQuery.data?.completed_24h || 0}
                      </div>
                      <div className="text-xs text-muted-foreground">Terminées (24h)</div>
                    </div>
                    <div className="p-3 bg-muted rounded-lg">
                      <div className="text-2xl font-bold text-blue-600">
                        {queueQuery.data?.running || 0}
                      </div>
                      <div className="text-xs text-muted-foreground">En cours</div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </ProtectedRoute>
    </AppLayout>
  );
}

export default SpotifySearchPage;
