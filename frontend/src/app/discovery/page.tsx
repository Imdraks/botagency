"use client";

import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Rocket,
  TrendingUp,
  RefreshCw,
  Sparkles,
  LayoutGrid,
  List,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { AppLayout, ProtectedRoute } from "@/components/layout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/components/ui/use-toast";
import { api } from "@/lib/api";
import {
  ArtistCard,
  ArtistCardData,
  JobQueuePanel,
  JobData,
  SearchBar,
  InputType,
  FeedFiltersBar,
  FeedFilters,
} from "@/components/discovery";

// ============================================================================
// TYPES
// ============================================================================

interface FeedResponse {
  artists: ArtistCardData[];
  total: number;
  page: number;
  limit: number;
  has_more: boolean;
}

interface QueueResponse {
  jobs: JobData[];
  running: number;
  pending: number;
  completed_24h: number;
}

interface JobResponse {
  id: number;
  artist_name?: string;
  input_type: string;
  input_value: string;
  status: string;
  current_step: string;
  progress: number;
  started_at: string;
}

// ============================================================================
// DEFAULT VALUES
// ============================================================================

const DEFAULT_FILTERS: FeedFilters = {
  timing: [],
  scoreRange: [0, 100],
  listenersRange: [0, 10000000],
  recommendation: [],
};

// ============================================================================
// API FUNCTIONS
// ============================================================================

const fetchFeed = async (
  feedType: string,
  page: number,
  filters: FeedFilters
): Promise<FeedResponse> => {
  const params = new URLSearchParams();
  params.set("page", page.toString());
  params.set("limit", "20");

  if (filters.timing.length > 0) {
    params.set("timing", filters.timing.join(","));
  }
  if (filters.scoreRange[0] > 0) {
    params.set("score_min", filters.scoreRange[0].toString());
  }
  if (filters.scoreRange[1] < 100) {
    params.set("score_max", filters.scoreRange[1].toString());
  }
  if (filters.listenersRange[0] > 0) {
    params.set("listeners_min", filters.listenersRange[0].toString());
  }
  if (filters.listenersRange[1] < 10000000) {
    params.set("listeners_max", filters.listenersRange[1].toString());
  }
  if (filters.recommendation.length > 0) {
    params.set("recommendation", filters.recommendation.join(","));
  }

  const response = await api.get(`/discovery/feed/${feedType}?${params.toString()}`);
  return response.data;
};

const fetchQueue = async (): Promise<QueueResponse> => {
  const response = await api.get("/discovery/queue");
  return response.data;
};

const searchArtist = async (query: string, inputType: InputType): Promise<JobResponse> => {
  const response = await api.post("/discovery/search", {
    query,
    input_type: inputType,
  });
  return response.data;
};

const refreshArtist = async (artistId: number): Promise<JobResponse> => {
  const response = await api.post(`/discovery/artist/${artistId}/refresh`);
  return response.data;
};

// ============================================================================
// COMPONENTS
// ============================================================================

function FeedSkeleton() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
      {Array.from({ length: 8 }).map((_, i) => (
        <Card key={i}>
          <CardContent className="p-4">
            <div className="flex items-start gap-3 mb-3">
              <Skeleton className="w-16 h-16 rounded-lg" />
              <div className="flex-1">
                <Skeleton className="h-5 w-32 mb-2" />
                <Skeleton className="h-4 w-24" />
              </div>
              <Skeleton className="h-10 w-10 rounded" />
            </div>
            <div className="grid grid-cols-3 gap-2 mb-3">
              <Skeleton className="h-12 rounded" />
              <Skeleton className="h-12 rounded" />
              <Skeleton className="h-12 rounded" />
            </div>
            <Skeleton className="h-4 w-full mb-2" />
            <Skeleton className="h-4 w-3/4" />
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

function EmptyFeed({ feedType }: { feedType: string }) {
  return (
    <div className="text-center py-16">
      <div className="w-16 h-16 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mx-auto mb-4">
        {feedType === "RECOMMENDED" ? (
          <Rocket className="h-8 w-8 text-gray-400" />
        ) : (
          <TrendingUp className="h-8 w-8 text-gray-400" />
        )}
      </div>
      <h3 className="text-lg font-medium mb-2">Aucun artiste trouvé</h3>
      <p className="text-muted-foreground max-w-md mx-auto">
        {feedType === "RECOMMENDED"
          ? "Commencez par rechercher des artistes pour les analyser et construire votre feed de recommandations."
          : "Le feed trending se remplit automatiquement avec les artistes en forte croissance."}
      </p>
    </div>
  );
}

function Pagination({
  page,
  total,
  limit,
  hasMore,
  onPageChange,
}: {
  page: number;
  total: number;
  limit: number;
  hasMore: boolean;
  onPageChange: (page: number) => void;
}) {
  const totalPages = Math.ceil(total / limit);

  return (
    <div className="flex items-center justify-between py-4">
      <div className="text-sm text-muted-foreground">
        Affichage de {(page - 1) * limit + 1}-{Math.min(page * limit, total)} sur {total}
      </div>
      <div className="flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={() => onPageChange(page - 1)}
          disabled={page === 1}
        >
          <ChevronLeft className="h-4 w-4" />
        </Button>
        <span className="text-sm">
          Page {page} / {totalPages}
        </span>
        <Button
          variant="outline"
          size="sm"
          onClick={() => onPageChange(page + 1)}
          disabled={!hasMore}
        >
          <ChevronRight className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}

// ============================================================================
// MAIN PAGE
// ============================================================================

function DiscoveryV3Page() {
  const { toast } = useToast();
  const queryClient = useQueryClient();

  // State
  const [feedType, setFeedType] = useState<"RECOMMENDED" | "TRENDING">("RECOMMENDED");
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState<FeedFilters>(DEFAULT_FILTERS);
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid");

  // Reset page when filters change
  useEffect(() => {
    setPage(1);
  }, [feedType, filters]);

  // Queries
  const feedQuery = useQuery({
    queryKey: ["discovery-feed", feedType, page, filters],
    queryFn: () => fetchFeed(feedType, page, filters),
    staleTime: 60 * 1000, // 60 seconds
    refetchInterval: false,
  });

  const queueQuery = useQuery({
    queryKey: ["discovery-queue"],
    queryFn: fetchQueue,
    staleTime: 3 * 1000, // 3 seconds for active jobs
    refetchInterval: (data) => {
      // Refetch every 3s if there are running jobs
      if (data?.state.data?.running && data.state.data.running > 0) {
        return 3000;
      }
      return false;
    },
  });

  // Mutations
  const searchMutation = useMutation({
    mutationFn: ({ query, inputType }: { query: string; inputType: InputType }) =>
      searchArtist(query, inputType),
    onSuccess: (data) => {
      toast({
        title: "Recherche lancée",
        description: `Job #${data.id} créé pour "${data.input_value}"`,
      });
      // Refetch queue to show new job
      queryClient.invalidateQueries({ queryKey: ["discovery-queue"] });
    },
    onError: (error: any) => {
      const detail = error?.response?.data?.detail;
      if (detail?.code === "ALREADY_EXISTS") {
        toast({
          title: "Artiste existant",
          description: detail.message,
          variant: "destructive",
        });
      } else {
        toast({
          title: "Erreur",
          description: "Une erreur est survenue lors de la recherche",
          variant: "destructive",
        });
      }
    },
  });

  const refreshMutation = useMutation({
    mutationFn: refreshArtist,
    onSuccess: (data) => {
      toast({
        title: "Rafraîchissement lancé",
        description: `Job #${data.id} créé`,
      });
      queryClient.invalidateQueries({ queryKey: ["discovery-queue"] });
    },
  });

  // Handlers
  const handleSearch = (query: string, inputType: InputType) => {
    searchMutation.mutate({ query, inputType });
  };

  const handleRefresh = (artistId: number) => {
    refreshMutation.mutate(artistId);
  };

  const handleAddToComparison = (artistId: number) => {
    // TODO: Open comparison modal or add to shortlist
    toast({
      title: "Ajouter à une shortlist",
      description: "Fonctionnalité à venir",
    });
  };

  const handleViewDetail = (artistId: number) => {
    // TODO: Open detail drawer or navigate
    window.open(`/discovery/${artistId}`, "_blank");
  };

  const resetFilters = () => {
    setFilters(DEFAULT_FILTERS);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3">
            <Sparkles className="h-8 w-8 text-purple-500" />
            Discovery
          </h1>
          <p className="text-muted-foreground mt-1">
            Découvrez les artistes prometteurs grâce à l'analyse automatique
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => feedQuery.refetch()}
            disabled={feedQuery.isRefetching}
          >
            <RefreshCw
              className={`h-4 w-4 mr-1 ${feedQuery.isRefetching ? "animate-spin" : ""}`}
            />
            Actualiser
          </Button>
        </div>
      </div>

      {/* Search bar */}
      <SearchBar
        onSearch={handleSearch}
        isLoading={searchMutation.isPending}
        placeholder="Rechercher un artiste par nom, URL Spotify ou Viberate..."
      />

      {/* Layout: Feed + Queue sidebar */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Main feed area */}
        <div className="lg:col-span-3 space-y-4">
          {/* Tabs + Filters */}
          <div className="flex items-center justify-between flex-wrap gap-4">
            <Tabs
              value={feedType}
              onValueChange={(v) => setFeedType(v as "RECOMMENDED" | "TRENDING")}
            >
              <TabsList>
                <TabsTrigger value="RECOMMENDED" className="gap-2">
                  <Rocket className="h-4 w-4" />
                  Recommandés
                </TabsTrigger>
                <TabsTrigger value="TRENDING" className="gap-2">
                  <TrendingUp className="h-4 w-4" />
                  Trending
                </TabsTrigger>
              </TabsList>
            </Tabs>

            <div className="flex items-center gap-2">
              <FeedFiltersBar
                filters={filters}
                onFiltersChange={setFilters}
                onReset={resetFilters}
              />

              {/* View mode toggle */}
              <div className="border rounded-lg p-1 flex items-center gap-1">
                <Button
                  variant={viewMode === "grid" ? "secondary" : "ghost"}
                  size="sm"
                  className="h-8 w-8 p-0"
                  onClick={() => setViewMode("grid")}
                >
                  <LayoutGrid className="h-4 w-4" />
                </Button>
                <Button
                  variant={viewMode === "list" ? "secondary" : "ghost"}
                  size="sm"
                  className="h-8 w-8 p-0"
                  onClick={() => setViewMode("list")}
                >
                  <List className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>

          {/* Feed content */}
          {feedQuery.isLoading ? (
            <FeedSkeleton />
          ) : feedQuery.isError ? (
            <Card className="p-8 text-center">
              <p className="text-red-500 mb-4">Erreur lors du chargement du feed</p>
              <Button variant="outline" onClick={() => feedQuery.refetch()}>
                Réessayer
              </Button>
            </Card>
          ) : !feedQuery.data || feedQuery.data.artists.length === 0 ? (
            <EmptyFeed feedType={feedType} />
          ) : (
            <>
              <div
                className={
                  viewMode === "grid"
                    ? "grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4"
                    : "space-y-3"
                }
              >
                {feedQuery.data.artists.map((artist) => (
                  <ArtistCard
                    key={artist.id}
                    artist={artist}
                    onRefresh={handleRefresh}
                    onAddToComparison={handleAddToComparison}
                    onViewDetail={handleViewDetail}
                    isRefreshing={refreshMutation.isPending}
                  />
                ))}
              </div>

              {/* Pagination */}
              <Pagination
                page={feedQuery.data.page}
                total={feedQuery.data.total}
                limit={feedQuery.data.limit}
                hasMore={feedQuery.data.has_more}
                onPageChange={setPage}
              />
            </>
          )}
        </div>

        {/* Queue sidebar */}
        <div className="lg:col-span-1">
          <div className="sticky top-4">
            <JobQueuePanel
              jobs={queueQuery.data?.jobs || []}
              runningCount={queueQuery.data?.running || 0}
              pendingCount={queueQuery.data?.pending || 0}
              completedCount={queueQuery.data?.completed_24h || 0}
              isLoading={queueQuery.isLoading}
              onRetry={(jobId) => {
                // TODO: Implement retry
                toast({
                  title: "Retry",
                  description: `Retry job ${jobId}`,
                });
              }}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// EXPORT WITH LAYOUT
// ============================================================================

export default function DiscoveryPage() {
  return (
    <ProtectedRoute>
      <AppLayout>
        <DiscoveryV3Page />
      </AppLayout>
    </ProtectedRoute>
  );
}
