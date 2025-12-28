"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import {
  Activity,
  Server,
  CheckCircle,
  AlertCircle,
  XCircle,
  TrendingUp,
  TrendingDown,
  Minus,
  RefreshCw,
  Loader2,
  Power,
  PowerOff,
  BarChart3,
  Clock,
  FileWarning,
  Copy,
} from "lucide-react";
import { AppLayoutWithOnboarding, ProtectedRoute } from "@/components/layout";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useToast } from "@/components/ui/toaster";
import { sourceHealthApi, sourcesApi } from "@/lib/api";
import type { SourceHealthOverview, SourceHealthSummary, SourceHealthMetrics } from "@/lib/types";

function getHealthColor(score: number): string {
  if (score >= 80) return "text-green-500";
  if (score >= 50) return "text-yellow-500";
  return "text-red-500";
}

function getHealthBgColor(score: number): string {
  if (score >= 80) return "bg-green-500";
  if (score >= 50) return "bg-yellow-500";
  return "bg-red-500";
}

function getStatusIcon(status: "healthy" | "warning" | "critical") {
  switch (status) {
    case "healthy":
      return <CheckCircle className="h-5 w-5 text-green-500" />;
    case "warning":
      return <AlertCircle className="h-5 w-5 text-yellow-500" />;
    case "critical":
      return <XCircle className="h-5 w-5 text-red-500" />;
  }
}

function getTrendIcon(trend: "up" | "down" | "stable") {
  switch (trend) {
    case "up":
      return <TrendingUp className="h-4 w-4 text-green-500" />;
    case "down":
      return <TrendingDown className="h-4 w-4 text-red-500" />;
    case "stable":
      return <Minus className="h-4 w-4 text-gray-400" />;
  }
}

function SourceHealthCard({
  summary,
  onToggle,
  isToggling,
}: {
  summary: SourceHealthSummary;
  onToggle: (sourceId: number, isActive: boolean) => void;
  isToggling: boolean;
}) {
  const { source, current_health, trend, last_7_days_avg, total_opportunities_7d, status } = summary;

  return (
    <Card className={`border-l-4 ${getHealthBgColor(current_health)} hover:shadow-md transition-shadow`}>
      <CardContent className="p-4">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-3">
            {getStatusIcon(status)}
            <div>
              <h3 className="font-semibold">{source.name}</h3>
              <p className="text-sm text-muted-foreground capitalize">
                {source.source_type}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {getTrendIcon(trend)}
            <Switch
              checked={source.is_active}
              onCheckedChange={(checked) => onToggle(source.id, checked)}
              disabled={isToggling}
            />
          </div>
        </div>

        {/* Health score */}
        <div className="mb-4">
          <div className="flex items-center justify-between text-sm mb-1">
            <span>Santé</span>
            <span className={`font-bold ${getHealthColor(current_health)}`}>
              {current_health.toFixed(0)}%
            </span>
          </div>
          <Progress value={current_health} className="h-2" />
        </div>

        {/* Stats grid */}
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <p className="text-muted-foreground">Moy. 7j</p>
            <p className="font-semibold">{last_7_days_avg.toFixed(0)}%</p>
          </div>
          <div>
            <p className="text-muted-foreground">Opportunités 7j</p>
            <p className="font-semibold">{total_opportunities_7d}</p>
          </div>
        </div>

        {/* Last poll */}
        {source.last_polled_at && (
          <div className="mt-3 pt-3 border-t text-xs text-muted-foreground flex items-center gap-1">
            <Clock className="h-3 w-3" />
            Dernière collecte: {new Date(source.last_polled_at).toLocaleString("fr-FR")}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function SourceHealthContent() {
  const queryClient = useQueryClient();
  const { addToast } = useToast();
  const [selectedSourceId, setSelectedSourceId] = useState<number | null>(null);

  // Fetch overview
  const { data: overview, isLoading: overviewLoading } = useQuery<SourceHealthOverview>({
    queryKey: ["source-health", "overview"],
    queryFn: sourceHealthApi.getOverview,
  });

  // Fetch detailed metrics for selected source
  const { data: sourceMetrics, isLoading: metricsLoading } = useQuery<SourceHealthMetrics[]>({
    queryKey: ["source-health", "source", selectedSourceId],
    queryFn: () => sourceHealthApi.getOne(selectedSourceId!, 30),
    enabled: !!selectedSourceId,
  });

  // Toggle source mutation
  const toggleMutation = useMutation({
    mutationFn: ({ sourceId, isActive }: { sourceId: number; isActive: boolean }) =>
      sourceHealthApi.updateSource(sourceId, { is_active: isActive }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["source-health"] });
      queryClient.invalidateQueries({ queryKey: ["sources"] });
      addToast({
        title: "Source mise à jour",
        type: "success",
      });
    },
    onError: () => {
      addToast({
        title: "Erreur",
        description: "Impossible de mettre à jour la source",
        type: "error",
      });
    },
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Activity className="h-8 w-8 text-green-500" />
            Source Health
          </h1>
          <p className="text-muted-foreground">
            Monitoring et qualité de vos sources de données
          </p>
        </div>

        <div className="flex gap-2">
          <Link href="/sources">
            <Button variant="outline">
              <Server className="h-4 w-4 mr-2" />
              Gérer les sources
            </Button>
          </Link>
          <Button
            onClick={() => queryClient.invalidateQueries({ queryKey: ["source-health"] })}
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Actualiser
          </Button>
        </div>
      </div>

      {/* Overview stats */}
      {overviewLoading ? (
        <div className="flex items-center justify-center py-8">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : overview ? (
        <>
          <div className="grid gap-4 md:grid-cols-4">
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-lg ${getHealthBgColor(overview.overall_health)} bg-opacity-20`}>
                    <Activity className={`h-5 w-5 ${getHealthColor(overview.overall_health)}`} />
                  </div>
                  <div>
                    <p className={`text-2xl font-bold ${getHealthColor(overview.overall_health)}`}>
                      {overview.overall_health.toFixed(0)}%
                    </p>
                    <p className="text-sm text-muted-foreground">Santé globale</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-green-100">
                    <CheckCircle className="h-5 w-5 text-green-600" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-green-600">{overview.healthy_count}</p>
                    <p className="text-sm text-muted-foreground">Sources saines</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-yellow-100">
                    <AlertCircle className="h-5 w-5 text-yellow-600" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-yellow-600">{overview.warning_count}</p>
                    <p className="text-sm text-muted-foreground">À surveiller</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-red-100">
                    <XCircle className="h-5 w-5 text-red-600" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-red-600">{overview.critical_count}</p>
                    <p className="text-sm text-muted-foreground">Critiques</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Sources grid */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {overview.sources.map((summary) => (
              <div
                key={summary.source.id}
                onClick={() => setSelectedSourceId(summary.source.id)}
                className="cursor-pointer"
              >
                <SourceHealthCard
                  summary={summary}
                  onToggle={(sourceId, isActive) =>
                    toggleMutation.mutate({ sourceId, isActive })
                  }
                  isToggling={toggleMutation.isPending}
                />
              </div>
            ))}
          </div>

          {overview.sources.length === 0 && (
            <Card>
              <CardContent className="py-12 text-center">
                <Server className="h-12 w-12 mx-auto mb-4 text-muted-foreground opacity-50" />
                <h3 className="font-semibold text-lg mb-2">Aucune source configurée</h3>
                <p className="text-muted-foreground mb-4">
                  Ajoutez des sources pour commencer le monitoring
                </p>
                <Link href="/sources">
                  <Button>
                    Configurer les sources
                  </Button>
                </Link>
              </CardContent>
            </Card>
          )}
        </>
      ) : null}

      {/* Detailed metrics for selected source */}
      {selectedSourceId && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5" />
              Historique détaillé
            </CardTitle>
            <CardDescription>
              Métriques des 30 derniers jours
            </CardDescription>
          </CardHeader>
          <CardContent>
            {metricsLoading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
              </div>
            ) : sourceMetrics && sourceMetrics.length > 0 ? (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Date</TableHead>
                    <TableHead className="text-right">Opportunités</TableHead>
                    <TableHead className="text-right">Doublons</TableHead>
                    <TableHead className="text-right">Score moy.</TableHead>
                    <TableHead className="text-right">Erreurs</TableHead>
                    <TableHead className="text-right">Fraîcheur</TableHead>
                    <TableHead className="text-right">Santé</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {sourceMetrics.slice(0, 14).map((metric) => (
                    <TableRow key={metric.date}>
                      <TableCell>
                        {new Date(metric.date).toLocaleDateString("fr-FR", {
                          day: "numeric",
                          month: "short",
                        })}
                      </TableCell>
                      <TableCell className="text-right">{metric.opportunities_found}</TableCell>
                      <TableCell className="text-right">
                        {metric.duplicates_found > 0 && (
                          <Badge variant="secondary" className="text-xs">
                            <Copy className="h-3 w-3 mr-1" />
                            {metric.duplicates_found}
                          </Badge>
                        )}
                      </TableCell>
                      <TableCell className="text-right">{metric.avg_score.toFixed(0)}%</TableCell>
                      <TableCell className="text-right">
                        {metric.error_rate > 0 ? (
                          <Badge variant="destructive" className="text-xs">
                            {metric.error_rate.toFixed(0)}%
                          </Badge>
                        ) : (
                          <span className="text-green-500">0%</span>
                        )}
                      </TableCell>
                      <TableCell className="text-right">
                        {metric.freshness_hours < 24 ? (
                          <span className="text-green-500">{metric.freshness_hours.toFixed(0)}h</span>
                        ) : (
                          <span className="text-yellow-500">{metric.freshness_hours.toFixed(0)}h</span>
                        )}
                      </TableCell>
                      <TableCell className="text-right">
                        <span className={getHealthColor(metric.health_score)}>
                          {metric.health_score.toFixed(0)}%
                        </span>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            ) : (
              <p className="text-center py-4 text-muted-foreground">
                Pas de données disponibles
              </p>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}

export default function SourceHealthPage() {
  return (
    <ProtectedRoute>
      <AppLayoutWithOnboarding>
        <SourceHealthContent />
      </AppLayoutWithOnboarding>
    </ProtectedRoute>
  );
}
