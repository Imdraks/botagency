"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  TrendingUp,
  TrendingDown,
  Calendar,
  Target,
  DollarSign,
  BarChart3,
  PieChart,
  ArrowUpRight,
  ArrowDownRight,
  Clock,
  Trophy,
  Loader2,
  AlertTriangle,
  Lightbulb,
  Activity,
  Download,
  FileText,
  ChevronRight,
} from "lucide-react";
import { analyticsApi } from "@/lib/api";

// Types
interface TimelineData {
  period: string;
  data: Array<{
    date: string;
    new: number;
    won: number;
    lost: number;
    total_value: number;
  }>;
  trend: number;
  trend_label: string;
}

interface ConversionData {
  period: string;
  global: {
    total: number;
    won: number;
    lost: number;
    pending: number;
    conversion_rate: number;
  };
  by_category: Array<{
    category: string;
    total: number;
    won: number;
    lost: number;
    rate: number | null;
  }>;
  by_source: Array<{
    source: string;
    total: number;
    won: number;
    lost: number;
    rate: number | null;
  }>;
}

interface KpisData {
  today_new: number;
  week_new: number;
  week_trend: string;
  month_value: number;
  high_score_pending: number;
  urgent_deadlines: number;
  avg_score: number;
  updated_at: string;
}

interface ComparisonData {
  current_period: {
    label: string;
    count: number;
    won: number;
    lost: number;
    value: number;
    conversion_rate: number;
  };
  previous_period: {
    label: string;
    count: number;
    won: number;
    lost: number;
    value: number;
    conversion_rate: number;
  };
  changes: {
    count: number;
    value: number;
    conversion_rate: number;
  };
}

interface HeatmapData {
  data: Array<{
    month: string;
    label: string;
    count: number;
    value: number;
    high_priority: number;
  }>;
  hottest_month: { label: string; count: number } | null;
  total_upcoming: number;
  total_value: number;
}

interface Signal {
  type: string;
  priority: string;
  icon: string;
  title: string;
  description: string;
  opportunity_id: number | null;
  metadata: Record<string, unknown>;
}

interface SignalsData {
  count: number;
  signals: Signal[];
  summary: {
    stale: number;
    deadline_risk: number;
    high_value_untouched: number;
  };
  updated_at: string;
}

interface Insight {
  type: string;
  icon: string;
  title: string;
  description: string;
  metric: string;
  category: string;
}

interface InsightsData {
  insights: Insight[];
  updated_at: string;
}

interface PredictionPeriod {
  period: string;
  days: number;
  total_opportunities: number;
  total_value: number;
  weighted_value: number;
  high_probability: number;
  medium_probability: number;
  low_probability: number;
}

interface PredictionsSummaryData {
  predictions: PredictionPeriod[];
  top_likely_wins: Array<{
    id: number;
    title: string;
    score: number;
    probability: number;
    budget: number | null;
    deadline: string | null;
  }>;
  total_pipeline: number;
  updated_at: string;
}

export default function AnalyticsPage() {
  const [timelinePeriod, setTimelinePeriod] = useState<"7d" | "30d" | "90d" | "12m">("30d");
  const [conversionPeriod, setConversionPeriod] = useState<"7d" | "30d" | "90d" | "all">("30d");

  // Queries
  const { data: kpis, isLoading: kpisLoading } = useQuery<KpisData>({
    queryKey: ["analytics", "kpis"],
    queryFn: analyticsApi.getKpis,
    refetchInterval: 60000, // Refresh every minute
  });

  const { data: comparison, isLoading: comparisonLoading } = useQuery<ComparisonData>({
    queryKey: ["analytics", "comparison"],
    queryFn: analyticsApi.getComparison,
  });

  const { data: timeline, isLoading: timelineLoading } = useQuery<TimelineData>({
    queryKey: ["analytics", "timeline", timelinePeriod],
    queryFn: () => analyticsApi.getTimeline(timelinePeriod),
  });

  const { data: conversion, isLoading: conversionLoading } = useQuery<ConversionData>({
    queryKey: ["analytics", "conversion", conversionPeriod],
    queryFn: () => analyticsApi.getConversion(conversionPeriod),
  });

  const { data: heatmap, isLoading: heatmapLoading } = useQuery<HeatmapData>({
    queryKey: ["analytics", "heatmap"],
    queryFn: analyticsApi.getDeadlineHeatmap,
  });

  const { data: signals } = useQuery<SignalsData>({
    queryKey: ["analytics", "signals"],
    queryFn: analyticsApi.getSignals,
    refetchInterval: 120000,
  });

  const { data: insights } = useQuery<InsightsData>({
    queryKey: ["analytics", "insights"],
    queryFn: analyticsApi.getInsights,
  });

  const { data: predictionsSummary } = useQuery<PredictionsSummaryData>({
    queryKey: ["analytics", "predictions-summary"],
    queryFn: analyticsApi.getPredictionsSummary,
  });

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat("fr-FR", {
      style: "currency",
      currency: "EUR",
      maximumFractionDigits: 0,
    }).format(value);
  };

  const getChangeColor = (value: number) => {
    if (value > 0) return "text-green-600";
    if (value < 0) return "text-red-600";
    return "text-gray-600";
  };

  const getChangeIcon = (value: number) => {
    if (value > 0) return <ArrowUpRight className="h-4 w-4" />;
    if (value < 0) return <ArrowDownRight className="h-4 w-4" />;
    return null;
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">📊 Analytics</h1>
          <p className="text-muted-foreground">
            Tableaux de bord, signaux et prédictions
          </p>
        </div>
        <div className="flex items-center gap-2">
          {kpis && (
            <Badge variant="outline" className="text-xs">
              Mis à jour: {new Date(kpis.updated_at).toLocaleTimeString("fr-FR")}
            </Badge>
          )}
          <a href="/advanced-features/export/opportunities" target="_blank">
            <Button variant="outline" size="sm" className="gap-1">
              <Download className="h-4 w-4" />
              Exporter
            </Button>
          </a>
          <a href="/advanced-features/reports/weekly" target="_blank">
            <Button variant="outline" size="sm" className="gap-1">
              <FileText className="h-4 w-4" />
              Rapport
            </Button>
          </a>
        </div>
      </div>

      {/* KPIs Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-muted-foreground">Aujourd&apos;hui</p>
                <p className="text-2xl font-bold">{kpis?.today_new ?? "-"}</p>
              </div>
              <Calendar className="h-8 w-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-muted-foreground">Cette semaine</p>
                <div className="flex items-center gap-1">
                  <p className="text-2xl font-bold">{kpis?.week_new ?? "-"}</p>
                  <span className={kpis?.week_trend === "↑" ? "text-green-500" : "text-red-500"}>
                    {kpis?.week_trend}
                  </span>
                </div>
              </div>
              <TrendingUp className="h-8 w-8 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-muted-foreground">Valeur du mois</p>
                <p className="text-2xl font-bold">
                  {kpis ? formatCurrency(kpis.month_value) : "-"}
                </p>
              </div>
              <DollarSign className="h-8 w-8 text-yellow-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-muted-foreground">Score &gt;70</p>
                <p className="text-2xl font-bold">{kpis?.high_score_pending ?? "-"}</p>
              </div>
              <Target className="h-8 w-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-muted-foreground">Urgentes (7j)</p>
                <p className="text-2xl font-bold text-orange-600">
                  {kpis?.urgent_deadlines ?? "-"}
                </p>
              </div>
              <Clock className="h-8 w-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-muted-foreground">Score moyen</p>
                <p className="text-2xl font-bold">{kpis?.avg_score ?? "-"}</p>
              </div>
              <BarChart3 className="h-8 w-8 text-indigo-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Comparison Card */}
      {comparison && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5" />
              Comparaison période
            </CardTitle>
            <CardDescription>
              {comparison.current_period.label} vs {comparison.previous_period.label}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center p-4 bg-muted rounded-lg">
                <p className="text-sm text-muted-foreground">Nouvelles opportunités</p>
                <p className="text-3xl font-bold">{comparison.current_period.count}</p>
                <div className={`flex items-center justify-center gap-1 ${getChangeColor(comparison.changes.count)}`}>
                  {getChangeIcon(comparison.changes.count)}
                  <span>{comparison.changes.count > 0 ? "+" : ""}{comparison.changes.count}%</span>
                </div>
              </div>

              <div className="text-center p-4 bg-muted rounded-lg">
                <p className="text-sm text-muted-foreground">Valeur totale</p>
                <p className="text-3xl font-bold">{formatCurrency(comparison.current_period.value)}</p>
                <div className={`flex items-center justify-center gap-1 ${getChangeColor(comparison.changes.value)}`}>
                  {getChangeIcon(comparison.changes.value)}
                  <span>{comparison.changes.value > 0 ? "+" : ""}{comparison.changes.value}%</span>
                </div>
              </div>

              <div className="text-center p-4 bg-muted rounded-lg">
                <p className="text-sm text-muted-foreground">Taux de conversion</p>
                <p className="text-3xl font-bold">{comparison.current_period.conversion_rate}%</p>
                <div className={`flex items-center justify-center gap-1 ${getChangeColor(comparison.changes.conversion_rate)}`}>
                  {getChangeIcon(comparison.changes.conversion_rate)}
                  <span>{comparison.changes.conversion_rate > 0 ? "+" : ""}{comparison.changes.conversion_rate} pts</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Timeline Chart */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5" />
                Évolution temporelle
              </CardTitle>
              <div className="flex gap-1">
                {(["7d", "30d", "90d", "12m"] as const).map((p) => (
                  <Button
                    key={p}
                    variant={timelinePeriod === p ? "default" : "outline"}
                    size="sm"
                    onClick={() => setTimelinePeriod(p)}
                  >
                    {p}
                  </Button>
                ))}
              </div>
            </div>
            {timeline && (
              <CardDescription className="flex items-center gap-2">
                Tendance: 
                <span className={timeline.trend > 0 ? "text-green-600 font-bold" : "text-red-600 font-bold"}>
                  {timeline.trend_label} {timeline.trend > 0 ? "+" : ""}{timeline.trend}%
                </span>
              </CardDescription>
            )}
          </CardHeader>
          <CardContent>
            {timelineLoading ? (
              <div className="flex items-center justify-center h-48">
                <Loader2 className="h-8 w-8 animate-spin" />
              </div>
            ) : timeline?.data.length ? (
              <div className="space-y-2">
                {timeline.data.slice(-10).map((d) => (
                  <div key={d.date} className="flex items-center gap-2">
                    <span className="text-xs w-20 text-muted-foreground">{d.date}</span>
                    <div className="flex-1 h-6 bg-muted rounded overflow-hidden flex">
                      <div
                        className="h-full bg-blue-500"
                        style={{ width: `${(d.new / Math.max(...timeline.data.map(x => x.new), 1)) * 100}%` }}
                      />
                    </div>
                    <span className="text-sm font-medium w-8">{d.new}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-center text-muted-foreground py-8">Pas de données</p>
            )}
          </CardContent>
        </Card>

        {/* Conversion Rates */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <PieChart className="h-5 w-5" />
                Taux de conversion
              </CardTitle>
              <div className="flex gap-1">
                {(["7d", "30d", "90d", "all"] as const).map((p) => (
                  <Button
                    key={p}
                    variant={conversionPeriod === p ? "default" : "outline"}
                    size="sm"
                    onClick={() => setConversionPeriod(p)}
                  >
                    {p === "all" ? "Tout" : p}
                  </Button>
                ))}
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {conversionLoading ? (
              <div className="flex items-center justify-center h-48">
                <Loader2 className="h-8 w-8 animate-spin" />
              </div>
            ) : conversion ? (
              <div className="space-y-4">
                {/* Global rate */}
                <div className="text-center p-4 bg-gradient-to-r from-green-500/10 to-blue-500/10 rounded-lg">
                  <p className="text-4xl font-bold text-green-600">
                    {conversion.global.conversion_rate}%
                  </p>
                  <p className="text-sm text-muted-foreground">
                    {conversion.global.won} gagnées / {conversion.global.won + conversion.global.lost} décidées
                  </p>
                </div>

                {/* By category */}
                <div>
                  <p className="text-sm font-medium mb-2">Par catégorie</p>
                  <div className="space-y-1">
                    {conversion.by_category.slice(0, 5).map((cat) => (
                      <div key={cat.category} className="flex items-center justify-between text-sm">
                        <span className="capitalize">{cat.category}</span>
                        <span className="font-medium">
                          {cat.rate !== null ? `${cat.rate}%` : "-"}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <p className="text-center text-muted-foreground py-8">Pas de données</p>
            )}
          </CardContent>
        </Card>

        {/* Deadline Heatmap */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Calendar className="h-5 w-5" />
              Heatmap des deadlines
            </CardTitle>
            {heatmap?.hottest_month && (
              <CardDescription>
                🔥 Mois le plus chargé: {heatmap.hottest_month.label} ({heatmap.hottest_month.count} opportunités)
              </CardDescription>
            )}
          </CardHeader>
          <CardContent>
            {heatmapLoading ? (
              <div className="flex items-center justify-center h-48">
                <Loader2 className="h-8 w-8 animate-spin" />
              </div>
            ) : heatmap?.data.length ? (
              <div className="grid grid-cols-4 gap-2">
                {heatmap.data.map((month) => {
                  const intensity = month.count / Math.max(...heatmap.data.map(m => m.count), 1);
                  return (
                    <div
                      key={month.month}
                      className="p-3 rounded-lg text-center transition-all hover:scale-105"
                      style={{
                        backgroundColor: `rgba(59, 130, 246, ${0.1 + intensity * 0.5})`,
                      }}
                    >
                      <p className="text-xs font-medium">{month.label}</p>
                      <p className="text-lg font-bold">{month.count}</p>
                      {month.high_priority > 0 && (
                        <Badge variant="destructive" className="text-xs mt-1">
                          {month.high_priority} ⭐
                        </Badge>
                      )}
                    </div>
                  );
                })}
              </div>
            ) : (
              <p className="text-center text-muted-foreground py-8">Pas de deadlines à venir</p>
            )}
          </CardContent>
        </Card>

        {/* Top Performers placeholder */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Trophy className="h-5 w-5" />
              Top performers
            </CardTitle>
            <CardDescription>Sources et catégories les plus performantes</CardDescription>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="sources">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="sources">Sources</TabsTrigger>
                <TabsTrigger value="categories">Catégories</TabsTrigger>
              </TabsList>
              <TabsContent value="sources" className="space-y-2 mt-4">
                {conversion?.by_source.slice(0, 5).map((source, idx) => (
                  <div key={source.source} className="flex items-center justify-between p-2 bg-muted rounded">
                    <div className="flex items-center gap-2">
                      <span className="text-lg font-bold text-muted-foreground">#{idx + 1}</span>
                      <span className="font-medium">{source.source}</span>
                    </div>
                    <Badge variant={source.rate && source.rate > 50 ? "default" : "secondary"}>
                      {source.rate !== null ? `${source.rate}%` : "-"}
                    </Badge>
                  </div>
                ))}
              </TabsContent>
              <TabsContent value="categories" className="space-y-2 mt-4">
                {conversion?.by_category.slice(0, 5).map((cat, idx) => (
                  <div key={cat.category} className="flex items-center justify-between p-2 bg-muted rounded">
                    <div className="flex items-center gap-2">
                      <span className="text-lg font-bold text-muted-foreground">#{idx + 1}</span>
                      <span className="font-medium capitalize">{cat.category}</span>
                    </div>
                    <Badge variant={cat.rate && cat.rate > 50 ? "default" : "secondary"}>
                      {cat.rate !== null ? `${cat.rate}%` : "-"}
                    </Badge>
                  </div>
                ))}
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      </div>

      {/* ============================================================ */}
      {/* SIGNAUX FAIBLES & ALERTES */}
      {/* ============================================================ */}
      {signals && signals.count > 0 && (
        <Card className="border-orange-200 bg-orange-50/30">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-orange-600" />
              Signaux faibles
              <Badge variant="destructive" className="ml-2">{signals.count}</Badge>
            </CardTitle>
            <CardDescription>
              Anomalies et risques détectés automatiquement — {signals.summary.stale} stagnante(s),{" "}
              {signals.summary.deadline_risk} deadline(s) à risque,{" "}
              {signals.summary.high_value_untouched} opportunité(s) haute valeur non traitée(s)
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {signals.signals.map((signal, idx) => (
                <div
                  key={idx}
                  className={`flex items-start gap-3 p-3 rounded-lg border ${
                    signal.priority === "critical"
                      ? "border-red-300 bg-red-50"
                      : signal.priority === "high"
                      ? "border-orange-300 bg-orange-50"
                      : "border-yellow-200 bg-yellow-50"
                  }`}
                >
                  <span className="text-xl">{signal.icon}</span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <p className="font-medium text-sm">{signal.title}</p>
                      <Badge
                        variant={signal.priority === "critical" ? "destructive" : "outline"}
                        className="text-xs shrink-0"
                      >
                        {signal.priority}
                      </Badge>
                    </div>
                    <p className="text-xs text-muted-foreground truncate mt-1">
                      {signal.description}
                    </p>
                    {signal.opportunity_id && (
                      <a
                        href={`/opportunities/${signal.opportunity_id}`}
                        className="text-xs text-blue-600 hover:underline flex items-center gap-1 mt-1"
                      >
                        Voir <ChevronRight className="h-3 w-3" />
                      </a>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* ============================================================ */}
      {/* PRÉDICTIONS 30/60/90 JOURS */}
      {/* ============================================================ */}
      {predictionsSummary && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5 text-purple-600" />
              Prédictions pipeline
            </CardTitle>
            <CardDescription>
              Estimation du pipeline sur 30, 60 et 90 jours — {predictionsSummary.total_pipeline} opportunités actives
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              {predictionsSummary.predictions.map((pred) => (
                <div key={pred.period} className="p-4 rounded-lg bg-gradient-to-br from-purple-50 to-indigo-50 border border-purple-100">
                  <div className="flex items-center justify-between mb-3">
                    <p className="font-bold text-lg text-purple-900">{pred.period}</p>
                    <Badge variant="outline">{pred.total_opportunities} opps</Badge>
                  </div>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Valeur totale</span>
                      <span className="font-medium">{formatCurrency(pred.total_value)}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Valeur pondérée</span>
                      <span className="font-bold text-purple-700">{formatCurrency(pred.weighted_value)}</span>
                    </div>
                    <div className="flex gap-1 mt-2">
                      {pred.high_probability > 0 && (
                        <Badge className="bg-green-100 text-green-800 hover:bg-green-100">
                          {pred.high_probability} fort
                        </Badge>
                      )}
                      {pred.medium_probability > 0 && (
                        <Badge className="bg-yellow-100 text-yellow-800 hover:bg-yellow-100">
                          {pred.medium_probability} moyen
                        </Badge>
                      )}
                      {pred.low_probability > 0 && (
                        <Badge className="bg-gray-100 text-gray-600 hover:bg-gray-100">
                          {pred.low_probability} faible
                        </Badge>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {predictionsSummary.top_likely_wins.length > 0 && (
              <div>
                <p className="text-sm font-medium mb-3">🎯 Meilleures chances de gain</p>
                <div className="space-y-2">
                  {predictionsSummary.top_likely_wins.map((opp) => (
                    <a
                      key={opp.id}
                      href={`/opportunities/${opp.id}`}
                      className="flex items-center justify-between p-2 rounded-lg bg-muted hover:bg-muted/80 transition-colors"
                    >
                      <div className="flex items-center gap-3 min-w-0">
                        <div className="flex items-center justify-center w-10 h-10 rounded-full bg-green-100 text-green-700 font-bold text-sm shrink-0">
                          {opp.probability}%
                        </div>
                        <div className="min-w-0">
                          <p className="font-medium text-sm truncate">{opp.title}</p>
                          <p className="text-xs text-muted-foreground">
                            Score: {opp.score}
                            {opp.deadline && ` • Deadline: ${new Date(opp.deadline).toLocaleDateString("fr-FR")}`}
                          </p>
                        </div>
                      </div>
                      {opp.budget && (
                        <span className="text-sm font-medium text-green-700 shrink-0 ml-2">
                          {formatCurrency(opp.budget)}
                        </span>
                      )}
                    </a>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* ============================================================ */}
      {/* INSIGHTS AUTOMATIQUES */}
      {/* ============================================================ */}
      {insights && insights.insights.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Lightbulb className="h-5 w-5 text-yellow-600" />
              Insights
            </CardTitle>
            <CardDescription>Analyse automatique de vos données</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {insights.insights.map((insight, idx) => (
                <div key={idx} className="p-4 rounded-lg border bg-card hover:shadow-sm transition-shadow">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-xl">{insight.icon}</span>
                    <p className="font-medium text-sm">{insight.title}</p>
                  </div>
                  <p
                    className="text-sm text-muted-foreground"
                    dangerouslySetInnerHTML={{
                      __html: insight.description
                        .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>"),
                    }}
                  />
                  <div className="mt-3">
                    <Badge variant="secondary" className="text-xs">
                      {insight.metric}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
