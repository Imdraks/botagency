"use client";

import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea, ScrollBar } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";
import { 
  Sparkles, 
  TrendingUp, 
  Wallet, 
  Music,
  ExternalLink,
  Star,
  RefreshCw,
  Loader2,
} from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";

// Spotify icon component
const SpotifyIcon = ({ className }: { className?: string }) => (
  <svg className={className} viewBox="0 0 24 24" fill="currentColor">
    <path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15 10.561 18.72 12.84c.361.181.54.78.241 1.2zm.12-3.36C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.601.18-1.2.72-1.381 4.26-1.26 11.28-1.02 15.721 1.621.539.3.719 1.02.419 1.56-.299.421-1.02.599-1.559.3z"/>
  </svg>
);

interface ArtistSuggestion {
  name: string;
  real_name?: string;
  genre: string;
  spotify_monthly_listeners: number;
  youtube_subscribers: number;
  instagram_followers: number;
  tiktok_followers: number;
  fee_min: number;
  fee_max: number;
  market_tier: string;
  record_label?: string;
  potential_reason: string;
}

interface SuggestionsResponse {
  emerging: ArtistSuggestion[];
  rising: ArtistSuggestion[];
  budget_friendly: ArtistSuggestion[];
}

function formatNumber(num: number) {
  if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
  if (num >= 1000) return `${(num / 1000).toFixed(0)}K`;
  return num.toString();
}

function getTierColor(tier: string) {
  const colors: Record<string, string> = {
    emerging: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200",
    developing: "bg-cyan-100 text-cyan-800 dark:bg-cyan-900 dark:text-cyan-200",
    established: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200",
    star: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200",
  };
  return colors[tier] || "bg-gray-100 text-gray-800";
}

function getTierLabel(tier: string) {
  const labels: Record<string, string> = {
    emerging: "Émergent",
    developing: "En développement",
    established: "Établi",
    star: "Star",
  };
  return labels[tier] || tier;
}

function ArtistCard({ artist, type, onAnalyze, isAnalyzing }: { 
  artist: ArtistSuggestion; 
  type: "emerging" | "rising" | "budget";
  onAnalyze: (name: string) => void;
  isAnalyzing: boolean;
}) {
  const typeConfig = {
    emerging: { icon: Sparkles, color: "text-purple-500", bg: "bg-purple-50 dark:bg-purple-900/20" },
    rising: { icon: TrendingUp, color: "text-green-500", bg: "bg-green-50 dark:bg-green-900/20" },
    budget: { icon: Wallet, color: "text-blue-500", bg: "bg-blue-50 dark:bg-blue-900/20" },
  };
  
  const config = typeConfig[type];
  const Icon = config.icon;

  return (
    <div className={`flex-shrink-0 w-[280px] p-4 rounded-lg border ${config.bg}`}>
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2">
          <Icon className={`h-4 w-4 ${config.color}`} />
          <span className="font-semibold text-sm truncate max-w-[150px]">{artist.name}</span>
        </div>
        <Badge variant="outline" className="text-xs">
          {artist.genre}
        </Badge>
      </div>
      
      <div className="flex items-center gap-2 mb-3">
        <Badge className={`text-xs ${getTierColor(artist.market_tier)}`}>
          {getTierLabel(artist.market_tier)}
        </Badge>
        <div className="flex items-center gap-1 text-xs text-muted-foreground">
          <SpotifyIcon className="h-3 w-3 text-green-500" />
          {formatNumber(artist.spotify_monthly_listeners)}
        </div>
      </div>
      
      <div className="mb-3">
        <div className="text-lg font-bold text-green-600 dark:text-green-400">
          {artist.fee_min.toLocaleString()}€ - {artist.fee_max.toLocaleString()}€
        </div>
      </div>
      
      <p className="text-xs text-muted-foreground line-clamp-2 mb-3">
        {artist.potential_reason}
      </p>
      
      <div className="flex gap-2">
        <Button 
          variant="default" 
          size="sm" 
          className="flex-1 text-xs"
          onClick={() => onAnalyze(artist.name)}
          disabled={isAnalyzing}
        >
          {isAnalyzing ? (
            <Loader2 className="h-3 w-3 animate-spin mr-1" />
          ) : (
            <RefreshCw className="h-3 w-3 mr-1" />
          )}
          Analyser
        </Button>
        <Button 
          variant="ghost" 
          size="sm" 
          className="px-2"
          onClick={() => window.open(`https://open.spotify.com/search/${encodeURIComponent(artist.name)}`, "_blank")}
        >
          <ExternalLink className="h-3 w-3" />
        </Button>
      </div>
    </div>
  );
}

function ArtistCardSkeleton() {
  return (
    <div className="flex-shrink-0 w-[280px] p-4 rounded-lg border bg-gray-50 dark:bg-gray-900/20">
      <div className="flex items-start justify-between mb-2">
        <Skeleton className="h-4 w-24" />
        <Skeleton className="h-5 w-12" />
      </div>
      <div className="flex items-center gap-2 mb-3">
        <Skeleton className="h-5 w-20" />
        <Skeleton className="h-4 w-12" />
      </div>
      <Skeleton className="h-6 w-32 mb-3" />
      <Skeleton className="h-8 w-full mb-3" />
      <Skeleton className="h-8 w-full" />
    </div>
  );
}

export function EmergingArtistsWidget() {
  const router = useRouter();
  const [analyzingArtist, setAnalyzingArtist] = useState<string | null>(null);
  
  const { data: suggestions, isLoading } = useQuery<SuggestionsResponse>({
    queryKey: ["artist-suggestions"],
    queryFn: async () => {
      const response = await api.get("/artist-history/suggestions/all?limit=8");
      return response.data;
    },
    staleTime: 1000 * 60 * 5, // Cache 5 minutes
  });
  
  // Mutation pour analyser un artiste avec refresh
  const analyzeMutation = useMutation({
    mutationFn: async (artistName: string) => {
      // Lancer l'analyse avec force_refresh
      const response = await api.post("/ingestion/analyze-artist", {
        artist_name: artistName,
        force_refresh: true,
      });
      const taskId = response.data.task_id;
      
      // Polling pour attendre le résultat
      let attempts = 0;
      const maxAttempts = 30; // 30 secondes max
      
      while (attempts < maxAttempts) {
        await new Promise(resolve => setTimeout(resolve, 1000));
        const statusResponse = await api.get(`/ingestion/task/${taskId}`);
        
        if (statusResponse.data.ready) {
          if (statusResponse.data.result) {
            return statusResponse.data.result;
          }
          throw new Error(statusResponse.data.error || "Analyse échouée");
        }
        attempts++;
      }
      
      throw new Error("Timeout: l'analyse prend trop de temps");
    },
    onSuccess: (data, artistName) => {
      // Rediriger vers la page d'historique avec l'artiste
      router.push(`/artist-history?search=${encodeURIComponent(artistName)}`);
    },
    onSettled: () => {
      setAnalyzingArtist(null);
    },
  });
  
  const handleAnalyze = (artistName: string) => {
    setAnalyzingArtist(artistName);
    analyzeMutation.mutate(artistName);
  };

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Star className="h-5 w-5 text-yellow-500" />
              Artistes Suggérés
            </CardTitle>
            <CardDescription>
              Découvrez les talents émergents avec le meilleur potentiel
            </CardDescription>
          </div>
          <Button variant="outline" size="sm" asChild>
            <Link href="/artist-history">
              <Music className="h-4 w-4 mr-2" />
              Tous les artistes
            </Link>
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="emerging" className="w-full">
          <TabsList className="grid w-full grid-cols-3 mb-4">
            <TabsTrigger value="emerging" className="gap-1">
              <Sparkles className="h-3 w-3" />
              <span className="hidden sm:inline">Émergents</span>
            </TabsTrigger>
            <TabsTrigger value="rising" className="gap-1">
              <TrendingUp className="h-3 w-3" />
              <span className="hidden sm:inline">En hausse</span>
            </TabsTrigger>
            <TabsTrigger value="budget" className="gap-1">
              <Wallet className="h-3 w-3" />
              <span className="hidden sm:inline">Petit budget</span>
            </TabsTrigger>
          </TabsList>
          
          <TabsContent value="emerging" className="mt-0">
            <ScrollArea className="w-full whitespace-nowrap">
              <div className="flex gap-4 pb-4">
                {isLoading ? (
                  Array.from({ length: 4 }).map((_, i) => <ArtistCardSkeleton key={i} />)
                ) : suggestions?.emerging.length === 0 ? (
                  <div className="text-center py-8 text-muted-foreground w-full">
                    Aucune suggestion disponible
                  </div>
                ) : (
                  suggestions?.emerging.map((artist, i) => (
                    <ArtistCard 
                      key={i} 
                      artist={artist} 
                      type="emerging" 
                      onAnalyze={handleAnalyze}
                      isAnalyzing={analyzingArtist === artist.name}
                    />
                  ))
                )}
              </div>
              <ScrollBar orientation="horizontal" />
            </ScrollArea>
            <p className="text-xs text-muted-foreground mt-2">
              💡 Artistes émergents avec fort potentiel et cachets abordables
            </p>
          </TabsContent>
          
          <TabsContent value="rising" className="mt-0">
            <ScrollArea className="w-full whitespace-nowrap">
              <div className="flex gap-4 pb-4">
                {isLoading ? (
                  Array.from({ length: 4 }).map((_, i) => <ArtistCardSkeleton key={i} />)
                ) : suggestions?.rising.length === 0 ? (
                  <div className="text-center py-8 text-muted-foreground w-full">
                    Aucune suggestion disponible
                  </div>
                ) : (
                  suggestions?.rising.map((artist, i) => (
                    <ArtistCard 
                      key={i} 
                      artist={artist} 
                      type="rising" 
                      onAnalyze={handleAnalyze}
                      isAnalyzing={analyzingArtist === artist.name}
                    />
                  ))
                )}
              </div>
              <ScrollBar orientation="horizontal" />
            </ScrollArea>
            <p className="text-xs text-muted-foreground mt-2">
              🚀 Artistes en forte progression, proches de devenir établis
            </p>
          </TabsContent>
          
          <TabsContent value="budget" className="mt-0">
            <ScrollArea className="w-full whitespace-nowrap">
              <div className="flex gap-4 pb-4">
                {isLoading ? (
                  Array.from({ length: 4 }).map((_, i) => <ArtistCardSkeleton key={i} />)
                ) : suggestions?.budget_friendly.length === 0 ? (
                  <div className="text-center py-8 text-muted-foreground w-full">
                    Aucune suggestion disponible
                  </div>
                ) : (
                  suggestions?.budget_friendly.map((artist, i) => (
                    <ArtistCard 
                      key={i} 
                      artist={artist} 
                      type="budget" 
                      onAnalyze={handleAnalyze}
                      isAnalyzing={analyzingArtist === artist.name}
                    />
                  ))
                )}
              </div>
              <ScrollBar orientation="horizontal" />
            </ScrollArea>
            <p className="text-xs text-muted-foreground mt-2">
              💰 Meilleur rapport qualité/prix pour les budgets serrés (&lt; 15 000€)
            </p>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}
