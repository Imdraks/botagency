"use client";

import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import Link from "next/link";
import {
  BarChart3,
  Calendar,
  Filter,
  Loader2,
  MapPin,
  Music,
  RefreshCw,
  Target,
  TrendingUp,
  Users,
  Zap,
  ArrowRight,
  DollarSign,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { AppLayout, ProtectedRoute } from "@/components/layout";
import { analyticsV2Api } from "@/lib/api";

// ── Types ──

interface TerrainData {
  overview: {
    total_artists: number;
    total_events: number;
    real_events: number;
    contact_coverage_pct: number;
    total_budget_estimated: number;
  };
  by_genre: { name: string; count: number; avg_score: number }[];
  by_zone: { city: string; count: number; density: string }[];
  by_event_type: Record<string, number>;
  by_source: Record<string, number>;
  by_fee_tier: Record<string, number>;
  timeline: { month: string; count: number }[];
  heatmap: { month: string; label: string; count: number }[];
  funnel: {
    detected: number;
    scored: number;
    contact_found: number;
    fee_estimated: number;
    actionable: number;
  };
}

// ── Helpers ──

function formatCurrency(value: number): string {
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M€`;
  if (value >= 1_000) return `${Math.round(value / 1_000)}k€`;
  return `${value}€`;
}

function densityColor(d: string): string {
  if (d === "forte") return "bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-400";
  if (d === "moyenne") return "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400";
  return "bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400";
}

// ── Kpi overview card ──

function OverviewKpi({
  icon: Icon,
  label,
  value,
  sub,
}: {
  icon: typeof BarChart3;
  label: string;
  value: string | number;
  sub?: string;
}) {
  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-center justify-between mb-1">
          <span className="text-xs text-muted-foreground font-medium">{label}</span>
          <Icon className="h-4 w-4 text-muted-foreground" />
        </div>
        <p className="text-2xl font-bold">{value}</p>
        {sub && <p className="text-[11px] text-muted-foreground mt-0.5">{sub}</p>}
      </CardContent>
    </Card>
  );
}

// ── Horizontal bar list ──

function BarList({
  items,
  labelKey,
  valueKey,
  scoreKey,
  maxItems = 10,
}: {
  items: Record<string, unknown>[];
  labelKey: string;
  valueKey: string;
  scoreKey?: string;
  maxItems?: number;
}) {
  const sliced = items.slice(0, maxItems);
  const max = Math.max(...sliced.map((it) => (it[valueKey] as number) || 0), 1);
  return (
    <div className="space-y-2">
      {sliced.map((it, i) => (
        <div key={i} className="flex items-center gap-2">
          <span className="w-28 text-sm truncate">{it[labelKey] as string}</span>
          <div className="flex-1 h-5 rounded bg-muted overflow-hidden relative">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${((it[valueKey] as number) / max) * 100}%` }}
              transition={{ duration: 0.5, delay: i * 0.04 }}
              className="h-full rounded bg-indigo-500"
            />
          </div>
          <span className="text-xs font-medium w-8 text-right">{it[valueKey] as number}</span>
          {scoreKey && (
            <span className="text-[10px] text-muted-foreground w-10 text-right">
              ø{(it[scoreKey] as number) || 0}
            </span>
          )}
        </div>
      ))}
    </div>
  );
}

// ── Donut-like stacked bar for event type / source ──

function StackedBar({ data, colorMap }: { data: Record<string, number>; colorMap?: Record<string, string> }) {
  const entries = Object.entries(data).sort((a, b) => b[1] - a[1]);
  const total = entries.reduce((s, [, v]) => s + v, 0) || 1;
  const colors = colorMap || {};
  const defaultColors = ["#6366f1", "#ec4899", "#f59e0b", "#10b981", "#8b5cf6", "#ef4444", "#06b6d4", "#84cc16"];
  return (
    <div className="space-y-3">
      <div className="flex h-4 rounded-full overflow-hidden bg-muted">
        {entries.map(([key, val], i) => (
          <div
            key={key}
            style={{
              width: `${(val / total) * 100}%`,
              backgroundColor: colors[key] || defaultColors[i % defaultColors.length],
            }}
            className="h-full transition-all"
            title={`${key}: ${val}`}
          />
        ))}
      </div>
      <div className="flex flex-wrap gap-x-4 gap-y-1">
        {entries.map(([key, val], i) => (
          <div key={key} className="flex items-center gap-1.5">
            <div
              className="h-2.5 w-2.5 rounded-full"
              style={{ backgroundColor: colors[key] || defaultColors[i % defaultColors.length] }}
            />
            <span className="text-xs text-muted-foreground">
              {key} <span className="font-medium text-foreground">{val}</span>
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Activity timeline ──

function ActivityTimeline({ data }: { data: { month: string; count: number }[] }) {
  if (data.length === 0) return <p className="text-sm text-muted-foreground text-center py-6">Pas de données</p>;
  const max = Math.max(...data.map((d) => d.count), 1);
  return (
    <div className="flex items-end gap-1 h-32">
      {data.map((d) => (
        <div key={d.month} className="flex-1 flex flex-col items-center gap-1">
          <span className="text-[9px] text-muted-foreground font-medium">{d.count || ""}</span>
          <div className="w-full rounded-t bg-muted relative overflow-hidden" style={{ height: "100%" }}>
            <motion.div
              initial={{ height: 0 }}
              animate={{ height: `${(d.count / max) * 100}%` }}
              transition={{ duration: 0.5 }}
              className="absolute bottom-0 w-full rounded-t bg-indigo-500"
            />
          </div>
          <span className="text-[9px] text-muted-foreground">{d.month.slice(5)}</span>
        </div>
      ))}
    </div>
  );
}

// ── Calendar heatmap ──

function CalendarHeatmap({ data }: { data: { month: string; label: string; count: number }[] }) {
  if (data.length === 0) return <p className="text-sm text-muted-foreground text-center py-6">Pas de données</p>;
  const max = Math.max(...data.map((d) => d.count), 1);
  return (
    <div className="grid grid-cols-4 sm:grid-cols-6 gap-2">
      {data.map((d) => {
        const intensity = d.count / max;
        const bg =
          intensity === 0
            ? "bg-muted"
            : intensity < 0.25
            ? "bg-indigo-100 dark:bg-indigo-950/40"
            : intensity < 0.5
            ? "bg-indigo-200 dark:bg-indigo-900/50"
            : intensity < 0.75
            ? "bg-indigo-400 dark:bg-indigo-700"
            : "bg-indigo-600 dark:bg-indigo-500";
        return (
          <div key={d.month} className={`rounded-lg p-3 text-center ${bg} transition-colors`}>
            <p className="text-[10px] font-medium">{d.label}</p>
            <p className="text-lg font-bold">{d.count}</p>
          </div>
        );
      })}
    </div>
  );
}

// ── Qualification funnel ──

function QualificationFunnel({ funnel }: { funnel: TerrainData["funnel"] }) {
  const steps = [
    { label: "Détectés", value: funnel.detected, color: "#6366f1" },
    { label: "Scorés", value: funnel.scored, color: "#8b5cf6" },
    { label: "Contact trouvé", value: funnel.contact_found, color: "#a78bfa" },
    { label: "Cachet estimé", value: funnel.fee_estimated, color: "#c4b5fd" },
    { label: "Actionnables", value: funnel.actionable, color: "#10b981" },
  ];
  const maxVal = funnel.detected || 1;
  return (
    <div className="space-y-3">
      {steps.map((s, i) => (
        <div key={s.label} className="flex items-center gap-3">
          <span className="w-28 text-sm text-muted-foreground">{s.label}</span>
          <div className="flex-1 h-8 rounded bg-muted overflow-hidden relative">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${(s.value / maxVal) * 100}%` }}
              transition={{ duration: 0.6, delay: i * 0.08 }}
              className="h-full rounded flex items-center px-2"
              style={{ backgroundColor: s.color }}
            >
              <span className="text-xs text-white font-bold">{s.value}</span>
            </motion.div>
          </div>
          <span className="text-xs text-muted-foreground w-10 text-right">
            {maxVal > 0 ? Math.round((s.value / maxVal) * 100) : 0}%
          </span>
        </div>
      ))}
    </div>
  );
}

// ── Fee tier bars ──

function FeeTierBars({ data }: { data: Record<string, number> }) {
  const ordered = ["< 5k", "5-15k", "15-40k", "40-100k", "> 100k"];
  const max = Math.max(...Object.values(data), 1);
  const colors = ["#10b981", "#6366f1", "#8b5cf6", "#ec4899", "#ef4444"];
  return (
    <div className="space-y-2">
      {ordered.map((tier, i) => {
        const val = data[tier] || 0;
        return (
          <div key={tier} className="flex items-center gap-2">
            <span className="w-16 text-xs text-muted-foreground font-medium">{tier}</span>
            <div className="flex-1 h-5 rounded bg-muted overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${(val / max) * 100}%` }}
                transition={{ duration: 0.5, delay: i * 0.05 }}
                className="h-full rounded"
                style={{ backgroundColor: colors[i] }}
              />
            </div>
            <span className="text-xs font-medium w-6 text-right">{val}</span>
          </div>
        );
      })}
    </div>
  );
}

// ── Main ──

function AnalyticsContent() {
  const { data, isLoading, refetch } = useQuery<TerrainData>({
    queryKey: ["analytics-v2", "terrain"],
    queryFn: () => analyticsV2Api.getTerrain(),
    refetchInterval: 120_000,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  const ov = data?.overview;
  const fn = data?.funnel;

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Analytics</h1>
          <p className="text-sm text-muted-foreground">Terrain — structure du marché et couverture</p>
        </div>
        <Button onClick={() => refetch()} variant="ghost" size="sm">
          <RefreshCw className="h-4 w-4" />
        </Button>
      </div>

      {/* Overview KPIs */}
      {ov && (
        <div className="grid grid-cols-2 lg:grid-cols-5 gap-3">
          <OverviewKpi icon={Users} label="Artistes" value={ov.total_artists} />
          <OverviewKpi icon={Calendar} label="Événements" value={ov.total_events} sub={`${ov.real_events} Ticketmaster`} />
          <OverviewKpi icon={Target} label="Couverture contact" value={`${ov.contact_coverage_pct}%`} />
          <OverviewKpi icon={DollarSign} label="Budget estimé" value={formatCurrency(ov.total_budget_estimated)} />
          <OverviewKpi icon={Zap} label="Actionnables" value={fn?.actionable || 0} sub={`sur ${fn?.detected || 0} détectés`} />
        </div>
      )}

      {/* Grid: genres + zones */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm flex items-center gap-2">
                <Music className="h-4 w-4" /> Répartition par genre
              </CardTitle>
              <Link href="/discovery" className="text-xs text-indigo-600 hover:underline flex items-center gap-1">
                Explorer <ArrowRight className="h-3 w-3" />
              </Link>
            </div>
          </CardHeader>
          <CardContent>
            {data?.by_genre && data.by_genre.length > 0 ? (
              <BarList items={data.by_genre} labelKey="name" valueKey="count" scoreKey="avg_score" />
            ) : (
              <p className="text-sm text-muted-foreground text-center py-8">Aucune donnée de genre</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm flex items-center gap-2">
                <MapPin className="h-4 w-4" /> Répartition par zone
              </CardTitle>
              <Link href="/map" className="text-xs text-indigo-600 hover:underline flex items-center gap-1">
                Carte <ArrowRight className="h-3 w-3" />
              </Link>
            </div>
          </CardHeader>
          <CardContent>
            {data?.by_zone && data.by_zone.length > 0 ? (
              <div className="space-y-2">
                {data.by_zone.map((z) => (
                  <div key={z.city} className="flex items-center gap-2">
                    <span className="w-28 text-sm truncate">{z.city}</span>
                    <div className="flex-1 h-5 rounded bg-muted overflow-hidden">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${(z.count / Math.max(...data.by_zone.map((x) => x.count), 1)) * 100}%` }}
                        transition={{ duration: 0.5 }}
                        className="h-full rounded bg-indigo-500"
                      />
                    </div>
                    <span className="text-xs font-medium w-6 text-right">{z.count}</span>
                    <Badge variant="outline" className={`text-[10px] ${densityColor(z.density)}`}>
                      {z.density}
                    </Badge>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground text-center py-8">Aucune donnée de zone</p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Event type & Source */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Type d'événement</CardTitle>
          </CardHeader>
          <CardContent>
            {data?.by_event_type && Object.keys(data.by_event_type).length > 0 ? (
              <StackedBar data={data.by_event_type} />
            ) : (
              <p className="text-sm text-muted-foreground text-center py-6">Aucune donnée</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Source des données</CardTitle>
          </CardHeader>
          <CardContent>
            {data?.by_source && Object.keys(data.by_source).length > 0 ? (
              <StackedBar data={data.by_source} />
            ) : (
              <p className="text-sm text-muted-foreground text-center py-6">Aucune donnée</p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Fee tiers */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm flex items-center gap-2">
            <DollarSign className="h-4 w-4" /> Répartition par cachet estimé
          </CardTitle>
        </CardHeader>
        <CardContent>
          {data?.by_fee_tier ? <FeeTierBars data={data.by_fee_tier} /> : <p className="text-sm text-muted-foreground text-center py-6">Aucune donnée</p>}
        </CardContent>
      </Card>

      {/* Activity timeline + calendar heatmap */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-2">
              <BarChart3 className="h-4 w-4" /> Activité (12 derniers mois)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ActivityTimeline data={data?.timeline || []} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-2">
              <Calendar className="h-4 w-4" /> Calendrier à venir
            </CardTitle>
          </CardHeader>
          <CardContent>
            <CalendarHeatmap data={data?.heatmap || []} />
          </CardContent>
        </Card>
      </div>

      {/* Qualification funnel */}
      {fn && (
        <Card>
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm flex items-center gap-2">
                <Filter className="h-4 w-4" /> Entonnoir de qualification
              </CardTitle>
              <p className="text-xs text-muted-foreground">
                {fn.actionable} artistes actionnables sur {fn.detected} détectés
              </p>
            </div>
          </CardHeader>
          <CardContent>
            <QualificationFunnel funnel={fn} />
          </CardContent>
        </Card>
      )}
    </div>
  );
}

export default function AnalyticsPage() {
  return (
    <ProtectedRoute>
      <AppLayout>
        <AnalyticsContent />
      </AppLayout>
    </ProtectedRoute>
  );
}
