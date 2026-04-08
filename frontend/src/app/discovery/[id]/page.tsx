"use client";

import { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeft,
  Music2,
  Users,
  TrendingUp,
  Clock,
  AlertCircle,
  ExternalLink,
  RefreshCw,
  Sparkles,
  Plus,
  Loader2,
  CheckCircle2,
} from "lucide-react";
import { AppLayout, ProtectedRoute } from "@/components/layout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Progress } from "@/components/ui/progress";
import Image from "next/image";
import { toast } from "sonner";
import { api } from "@/lib/api";

// ============================================================================
// TYPES
// ============================================================================

interface ArtistReason {
  label: string;
  value?: string;
  impact?: number;
}

interface ArtistDetail {
  id: string;
  name: string;
  normalized_name: string;
  viberate_id?: string;
  spotify_id?: string;
  image_url?: string;
  country?: string;
  city?: string;
  genres: string[];
  score: number;
  timing_bucket?: string;
  recommendation?: string;
  monthly_listeners?: number;
  followers?: number;
  velocity?: number;
  acceleration?: number;
  data_quality?: string;
  drivers: ArtistReason[];
  risks: ArtistReason[];
  patterns: string[];
  signals: string[];
  summary?: string;
  booking_range?: { min: number; max: number };
  last_enriched_at?: string;
  created_at: string;
  is_stale: boolean;
  has_spotify: boolean;
  has_viberate: boolean;
}

// ============================================================================
// HELPERS
// ============================================================================

const formatNumber = (num?: number | null): string => {
  if (num === undefined || num === null) return "-";
  if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
  if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
  return num.toString();
};

const getScoreColor = (score: number): string => {
  if (score >= 80) return "text-green-600 dark:text-green-400";
  if (score >= 60) return "text-blue-600 dark:text-blue-400";
  if (score >= 40) return "text-yellow-600 dark:text-yellow-400";
  return "text-gray-600 dark:text-gray-400";
};

const getScoreBg = (score: number): string => {
  if (score >= 80) return "bg-green-100 dark:bg-green-900/30";
  if (score >= 60) return "bg-blue-100 dark:bg-blue-900/30";
  if (score >= 40) return "bg-yellow-100 dark:bg-yellow-900/30";
  return "bg-gray-100 dark:bg-gray-800";
};

const getRecommendationInfo = (rec?: string) => {
  const map: Record<string, { label: string; style: string }> = {
    SIGN: { label: "🎯 À signer", style: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200" },
    WATCH: { label: "👀 À suivre", style: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200" },
    PASS: { label: "⏸️ Passer", style: "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200" },
  };
  return map[rec || ""] || null;
};

const getTimingLabel = (bucket?: string): string => {
  const map: Record<string, string> = {
    IMMINENT: "Imminent",
    "1_3M": "1-3 mois",
    "3_6M": "3-6 mois",
    "6_12M": "6-12 mois",
    LONG: "Long terme",
  };
  return map[bucket || ""] || "-";
};

const getTimingStyle = (bucket?: string): string => {
  const map: Record<string, string> = {
    IMMINENT: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200",
    "1_3M": "bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200",
    "3_6M": "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200",
    "6_12M": "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200",
    LONG: "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200",
  };
  return map[bucket || ""] || "";
};

// ============================================================================
// PAGE
// ============================================================================

export default function DiscoveryArtistDetailPage() {
  const params = useParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  const artistId = params.id as string;

  const [enrichJobId, setEnrichJobId] = useState<string | null>(null);
  const [enrichStatus, setEnrichStatus] = useState<string | null>(null);
  const [enrichStep, setEnrichStep] = useState<string | null>(null);
  const [enrichProgress, setEnrichProgress] = useState(0);

  const { data: artist, isLoading, error } = useQuery<ArtistDetail>({
    queryKey: ["discovery-artist", artistId],
    queryFn: async () => {
      const res = await api.get(`/discovery/artist/${artistId}`);
      return res.data;
    },
    enabled: !!artistId,
  });

  // Poll enrichment job status
  useEffect(() => {
    if (!enrichJobId) return;
    const interval = setInterval(async () => {
      try {
        const res = await api.get(`/discovery/job/${enrichJobId}`);
        const job = res.data;
        setEnrichStatus(job.status);
        setEnrichStep(job.current_step);
        setEnrichProgress(job.progress);
        if (job.status === "COMPLETED" || job.status === "FAILED") {
          clearInterval(interval);
          if (job.status === "COMPLETED") {
            toast.success("Enrichissement terminé ! Données mises à jour.");
            queryClient.invalidateQueries({ queryKey: ["discovery-artist", artistId] });
          } else {
            toast.error(job.error_message || "Erreur lors de l'enrichissement");
          }
          setTimeout(() => {
            setEnrichJobId(null);
            setEnrichStatus(null);
            setEnrichStep(null);
            setEnrichProgress(0);
          }, 3000);
        }
      } catch {
        // ignore polling errors
      }
    }, 2000);
    return () => clearInterval(interval);
  }, [enrichJobId, artistId, queryClient]);

  const handleEnrich = useCallback(async () => {
    try {
      const res = await api.post(`/discovery/artist/${artistId}/refresh`);
      setEnrichJobId(res.data.id);
      setEnrichStatus("RUNNING");
      setEnrichStep("VIBERATE");
      setEnrichProgress(0);
      toast.info("Enrichissement lancé...");
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Erreur lors du lancement");
    }
  }, [artistId]);

  const handleAddToArtists = useCallback(async () => {
    try {
      const res = await api.post(`/discovery/artist/${artistId}/refresh`);
      setEnrichJobId(res.data.id);
      setEnrichStatus("RUNNING");
      setEnrichStep("VIBERATE");
      setEnrichProgress(0);
      toast.info("Analyse en cours... L'artiste sera ajouté à vos artistes.");
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Erreur lors du lancement");
    }
  }, [artistId]);

  return (
    <ProtectedRoute>
      <AppLayout>
        <div className="container mx-auto p-6 max-w-4xl">
          {/* Back button */}
          <Button
            variant="ghost"
            className="mb-4"
            onClick={() => router.push("/discovery")}
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Retour à la découverte
          </Button>

          {isLoading && (
            <div className="space-y-4">
              <Skeleton className="h-32 w-full" />
              <Skeleton className="h-48 w-full" />
              <Skeleton className="h-48 w-full" />
            </div>
          )}

          {error && (
            <Card>
              <CardContent className="p-8 text-center">
                <AlertCircle className="h-12 w-12 mx-auto text-red-400 mb-4" />
                <h2 className="text-xl font-semibold mb-2">Artiste introuvable</h2>
                <p className="text-muted-foreground mb-4">
                  Cet artiste n&apos;existe pas ou a été supprimé.
                </p>
                <Button onClick={() => router.push("/discovery")}>
                  Retour à la découverte
                </Button>
              </CardContent>
            </Card>
          )}

          {artist && (
            <div className="space-y-6">
              {/* Header Card */}
              <Card>
                <CardContent className="p-6">
                  {artist.is_stale && (
                    <div className="mb-4 bg-yellow-100 dark:bg-yellow-900/30 px-4 py-2 rounded-lg text-sm text-yellow-800 dark:text-yellow-200 flex items-center gap-2">
                      <AlertCircle className="h-4 w-4" />
                      Données datant de plus de 24h
                    </div>
                  )}

                  <div className="flex items-start gap-6">
                    {/* Artist image */}
                    <div className="relative w-24 h-24 rounded-xl overflow-hidden bg-gray-100 dark:bg-gray-800 flex-shrink-0">
                      {artist.image_url ? (
                        <Image
                          src={artist.image_url}
                          alt={artist.name}
                          fill
                          className="object-cover"
                        />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center">
                          <Sparkles className="h-8 w-8 text-gray-400" />
                        </div>
                      )}
                    </div>

                    {/* Artist info */}
                    <div className="flex-1 min-w-0">
                      <h1 className="text-2xl font-bold truncate">{artist.name}</h1>

                      <div className="flex items-center gap-2 mt-2 flex-wrap">
                        {artist.recommendation && getRecommendationInfo(artist.recommendation) && (
                          <Badge className={getRecommendationInfo(artist.recommendation)!.style}>
                            {getRecommendationInfo(artist.recommendation)!.label}
                          </Badge>
                        )}
                        {artist.timing_bucket && (
                          <Badge variant="outline" className={getTimingStyle(artist.timing_bucket)}>
                            <Clock className="h-3 w-3 mr-1" />
                            {getTimingLabel(artist.timing_bucket)}
                          </Badge>
                        )}
                        {artist.country && (
                          <Badge variant="outline">{artist.country}</Badge>
                        )}
                        {artist.genres.map((g) => (
                          <Badge key={g} variant="secondary">{g}</Badge>
                        ))}
                      </div>

                      {/* External links */}
                      <div className="flex items-center gap-3 mt-3">
                        {artist.has_spotify && artist.spotify_id && (
                          <a
                            href={`https://open.spotify.com/artist/${artist.spotify_id}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-sm text-green-600 hover:underline flex items-center gap-1"
                          >
                            <Music2 className="h-3.5 w-3.5" />
                            Spotify
                            <ExternalLink className="h-3 w-3" />
                          </a>
                        )}
                        {artist.has_viberate && artist.viberate_id && (
                          <a
                            href={artist.viberate_id}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-sm text-purple-600 hover:underline flex items-center gap-1"
                          >
                            Viberate
                            <ExternalLink className="h-3 w-3" />
                          </a>
                        )}
                      </div>
                    </div>

                    {/* Score */}
                    <div className={`text-center p-4 rounded-xl ${getScoreBg(artist.score)}`}>
                      <div className={`text-4xl font-bold ${getScoreColor(artist.score)}`}>
                        {artist.score}
                      </div>
                      <div className="text-sm text-muted-foreground mt-1">Score</div>
                      <Progress value={artist.score} className="w-20 mt-2" />
                    </div>
                  </div>

                  {/* Action buttons */}
                  <div className="flex items-center gap-3 mt-5 pt-4 border-t">
                    <Button
                      onClick={handleEnrich}
                      disabled={!!enrichJobId}
                      variant="outline"
                      className="flex-1"
                    >
                      {enrichJobId ? (
                        <>
                          <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                          {enrichStep || "Enrichissement"} ({enrichProgress}%)
                        </>
                      ) : (
                        <>
                          <RefreshCw className="h-4 w-4 mr-2" />
                          Enrichir les données
                        </>
                      )}
                    </Button>
                    <Button
                      onClick={handleAddToArtists}
                      disabled={!!enrichJobId}
                      className="flex-1"
                    >
                      {enrichStatus === "COMPLETED" ? (
                        <>
                          <CheckCircle2 className="h-4 w-4 mr-2" />
                          Ajouté !
                        </>
                      ) : (
                        <>
                          <Plus className="h-4 w-4 mr-2" />
                          Ajouter à mes artistes
                        </>
                      )}
                    </Button>
                  </div>

                  {/* Enrichment progress bar */}
                  {enrichJobId && (
                    <div className="mt-3">
                      <Progress value={enrichProgress} className="h-2" />
                      <p className="text-xs text-muted-foreground mt-1 text-center">
                        {enrichStep === "VIBERATE" && "Récupération des données sociales..."}
                        {enrichStep === "SPOTIFY" && "Scraping Spotify (auditeurs mensuels)..."}
                        {enrichStep === "COMPUTE" && "Calcul du score et des métriques..."}
                        {enrichStatus === "COMPLETED" && "Terminé !"}
                        {enrichStatus === "FAILED" && "Erreur"}
                      </p>
                    </div>
                  )}
                  </div>
                </CardContent>
              </Card>

              {/* Metrics Grid */}
              {(() => {
                const metrics = [
                  artist.monthly_listeners != null && {
                    icon: <Users className="h-5 w-5 mx-auto text-muted-foreground mb-1" />,
                    value: formatNumber(artist.monthly_listeners),
                    label: "Auditeurs mensuels",
                  },
                  artist.followers != null && {
                    icon: <Music2 className="h-5 w-5 mx-auto text-muted-foreground mb-1" />,
                    value: formatNumber(artist.followers),
                    label: "Followers",
                  },
                  artist.velocity != null && {
                    icon: <TrendingUp className="h-5 w-5 mx-auto text-muted-foreground mb-1" />,
                    value: <span className="text-green-600">+{(artist.velocity * 100).toFixed(0)}%</span>,
                    label: "Croissance",
                  },
                  artist.acceleration != null && {
                    icon: <TrendingUp className="h-5 w-5 mx-auto text-muted-foreground mb-1" />,
                    value: `${(artist.acceleration * 100).toFixed(0)}%`,
                    label: "Accélération",
                  },
                ].filter(Boolean) as { icon: React.ReactNode; value: React.ReactNode; label: string }[];

                if (metrics.length === 0) {
                  return (
                    <Card>
                      <CardContent className="p-6 text-center text-muted-foreground">
                        <AlertCircle className="h-5 w-5 mx-auto mb-2" />
                        <p className="text-sm">Données limitées — cliquez sur &quot;Enrichir les données&quot; pour obtenir les métriques complètes.</p>
                      </CardContent>
                    </Card>
                  );
                }

                const cols = metrics.length >= 4 ? "md:grid-cols-4" : metrics.length === 3 ? "md:grid-cols-3" : "md:grid-cols-2";
                return (
                  <div className={`grid grid-cols-2 ${cols} gap-4`}>
                    {metrics.map((m, i) => (
                      <Card key={i}>
                        <CardContent className="p-4 text-center">
                          {m.icon}
                          <div className="text-2xl font-bold">{m.value}</div>
                          <div className="text-xs text-muted-foreground">{m.label}</div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                );
              })()}

              {/* Booking Range */}
              {artist.booking_range && (
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-base">Estimation cachet</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-lg font-semibold">
                      {formatNumber(artist.booking_range.min)} – {formatNumber(artist.booking_range.max)} €
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Drivers & Risks */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {artist.drivers.length > 0 && (
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-base text-green-600">Points forts</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <ul className="space-y-2">
                        {artist.drivers.map((d, i) => (
                          <li key={i} className="flex items-center gap-2 text-sm">
                            <div className="w-2 h-2 rounded-full bg-green-500 flex-shrink-0" />
                            <span>{d.label}</span>
                            {d.value && (
                              <span className="ml-auto font-medium text-green-600">{d.value}</span>
                            )}
                          </li>
                        ))}
                      </ul>
                    </CardContent>
                  </Card>
                )}

                {artist.risks.length > 0 && (
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-base text-red-600">Risques</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <ul className="space-y-2">
                        {artist.risks.map((r, i) => (
                          <li key={i} className="flex items-center gap-2 text-sm">
                            <div className="w-2 h-2 rounded-full bg-red-500 flex-shrink-0" />
                            <span>{r.label}</span>
                            {r.value && (
                              <span className="ml-auto font-medium text-red-600">{r.value}</span>
                            )}
                          </li>
                        ))}
                      </ul>
                    </CardContent>
                  </Card>
                )}
              </div>

              {/* Signals */}
              {artist.signals.length > 0 && (
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-base">Signaux détectés</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex flex-wrap gap-2">
                      {artist.signals.map((s, i) => (
                        <Badge key={i} variant="secondary">{s}</Badge>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Patterns */}
              {artist.patterns.length > 0 && (
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-base">Patterns</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex flex-wrap gap-2">
                      {artist.patterns.map((p, i) => (
                        <Badge key={i} variant="outline">{p}</Badge>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Data quality & timestamps */}
              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between text-sm text-muted-foreground">
                    <div className="flex items-center gap-4">
                      <span>
                        Qualité : <strong>{artist.data_quality || "N/A"}</strong>
                      </span>
                      {artist.last_enriched_at && (
                        <span>
                          Dernière mise à jour : {new Date(artist.last_enriched_at).toLocaleDateString("fr-FR")}
                        </span>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </div>
      </AppLayout>
    </ProtectedRoute>
  );
}
