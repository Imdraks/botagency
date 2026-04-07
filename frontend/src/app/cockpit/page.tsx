"use client";

import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import Link from "next/link";
import {
  Activity,
  Calendar,
  Loader2,
  MapPin,
  RefreshCw,
  TrendingUp,
  Radio,
  Target,
  ArrowRight,
  Clock,
  BarChart3,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { AppLayout, ProtectedRoute } from "@/components/layout";
import { analyticsV2Api } from "@/lib/api";

// ── Types ──

interface CockpitData {
  signals_count: number;
  kpis: {
    events_30d: number;
    artists_moving: number;
    active_cities: number;
    qualified_opportunities: number;
  };
  movements: {
    type: string;
    icon: string;
    text: string;
    timestamp: string | null;
    artist_name?: string;
    city?: string;
  }[];
  upcoming: {
    artist_name: string;
    venue: string;
    city: string;
    date: string | null;
    date_label: string;
    days_until: number;
    event_type: string;
  }[];
  data_quality: {
    total_artists: number;
    scored_pct: number;
    fee_estimated_pct: number;
    event_coverage_pct: number;
  };
  hotspots: {
    city: string;
    count: number;
    lat: number;
    lng: number;
  }[];
}

// ── Helpers ──

function timeAgo(ts: string | null): string {
  if (!ts) return "";
  const diff = Date.now() - new Date(ts).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 60) return `il y a ${mins}min`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `il y a ${hours}h`;
  return `il y a ${Math.floor(hours / 24)}j`;
}

const MOVEMENT_ICONS: Record<string, typeof TrendingUp> = {
  "trending-up": TrendingUp,
  calendar: Calendar,
  "map-pin": MapPin,
};

function urgencyColor(days: number): string {
  if (days <= 3) return "text-red-600 bg-red-50 dark:bg-red-950/30";
  if (days <= 7) return "text-orange-600 bg-orange-50 dark:bg-orange-950/30";
  return "text-muted-foreground bg-muted";
}

// ── Components ──

function SignalPulse({ count }: { count: number }) {
  return (
    <div className={`rounded-xl border p-5 ${count > 0 ? "bg-indigo-50 border-indigo-200 dark:bg-indigo-950/20 dark:border-indigo-800" : "bg-muted/30 border-border"}`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className={`h-10 w-10 rounded-full flex items-center justify-center ${count > 0 ? "bg-indigo-100 dark:bg-indigo-900" : "bg-muted"}`}>
            <Radio className={`h-5 w-5 ${count > 0 ? "text-indigo-600" : "text-muted-foreground"}`} />
          </div>
          <div>
            <p className="text-sm font-medium text-muted-foreground">Signaux détectés</p>
            <p className={`text-3xl font-bold ${count > 0 ? "text-indigo-700 dark:text-indigo-400" : "text-muted-foreground"}`}>
              {count}
            </p>
          </div>
        </div>
        {count > 0 ? (
          <p className="text-sm text-indigo-600 dark:text-indigo-400">
            {count} artiste{count > 1 ? "s" : ""} en mouvement cette semaine
          </p>
        ) : (
          <p className="text-sm text-muted-foreground">Le marché est calme — aucun mouvement notable.</p>
        )}
      </div>
    </div>
  );
}

function KpiCard({
  icon: Icon,
  label,
  value,
  color,
  href,
}: {
  icon: typeof Activity;
  label: string;
  value: number;
  color: string;
  href?: string;
}) {
  const content = (
    <Card className="hover:shadow-md transition-shadow">
      <CardContent className="p-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-medium text-muted-foreground">{label}</span>
          <div className="h-8 w-8 rounded-lg flex items-center justify-center" style={{ backgroundColor: `${color}15` }}>
            <Icon className="h-4 w-4" style={{ color }} />
          </div>
        </div>
        <p className="text-2xl font-bold">{value}</p>
        {href && (
          <span className="flex items-center gap-1 mt-1 text-xs" style={{ color }}>
            Voir <ArrowRight className="h-3 w-3" />
          </span>
        )}
      </CardContent>
    </Card>
  );
  return href ? <Link href={href}>{content}</Link> : content;
}

function MovementTimeline({ movements }: { movements: CockpitData["movements"] }) {
  if (movements.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground text-sm">
        Aucun mouvement récent détecté.
      </div>
    );
  }
  return (
    <div className="space-y-3">
      {movements.map((m, i) => {
        const Icon = MOVEMENT_ICONS[m.icon] || Activity;
        return (
          <motion.div
            key={i}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.05 }}
            className="flex items-start gap-3 p-3 rounded-lg hover:bg-muted/50 transition-colors"
          >
            <div className="h-8 w-8 rounded-full bg-muted flex-shrink-0 flex items-center justify-center mt-0.5">
              <Icon className="h-4 w-4 text-muted-foreground" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm leading-snug">{m.text}</p>
              {m.timestamp && (
                <p className="text-[10px] text-muted-foreground mt-0.5">{timeAgo(m.timestamp)}</p>
              )}
            </div>
          </motion.div>
        );
      })}
    </div>
  );
}

function HotspotsMini({ hotspots }: { hotspots: CockpitData["hotspots"] }) {
  if (hotspots.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground text-sm">
        Aucune zone active détectée.
      </div>
    );
  }
  const max = Math.max(...hotspots.map((h) => h.count), 1);
  return (
    <div className="space-y-2">
      {hotspots.slice(0, 6).map((h) => (
        <div key={h.city} className="flex items-center gap-2">
          <MapPin className="h-3 w-3 text-muted-foreground flex-shrink-0" />
          <span className="text-sm flex-1 truncate">{h.city}</span>
          <div className="w-20 h-2 rounded-full bg-muted overflow-hidden">
            <div
              className="h-full rounded-full bg-indigo-500"
              style={{ width: `${(h.count / max) * 100}%` }}
            />
          </div>
          <span className="text-xs text-muted-foreground w-6 text-right">{h.count}</span>
        </div>
      ))}
      <Link href="/map" className="flex items-center gap-1 text-xs text-indigo-600 hover:underline mt-2">
        Ouvrir la carte <ArrowRight className="h-3 w-3" />
      </Link>
    </div>
  );
}

function DataQualityBar({ quality }: { quality: CockpitData["data_quality"] }) {
  const items = [
    { label: "Scorés", pct: quality.scored_pct, color: "#6366f1" },
    { label: "Cachet estimé", pct: quality.fee_estimated_pct, color: "#f59e0b" },
    { label: "Événement réel", pct: quality.event_coverage_pct, color: "#10b981" },
  ];
  return (
    <div className="rounded-xl border p-4">
      <div className="flex items-center justify-between mb-3">
        <p className="text-sm font-medium">Qualité des données</p>
        <span className="text-xs text-muted-foreground">{quality.total_artists} artistes</span>
      </div>
      <div className="space-y-3">
        {items.map((it) => (
          <div key={it.label} className="space-y-1">
            <div className="flex items-center justify-between">
              <span className="text-xs text-muted-foreground">{it.label}</span>
              <span className="text-xs font-medium">{it.pct}%</span>
            </div>
            <div className="h-1.5 rounded-full bg-muted overflow-hidden">
              <div
                className="h-full rounded-full transition-all"
                style={{ width: `${it.pct}%`, backgroundColor: it.color }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Main ──

function CockpitContent() {
  const { data, isLoading, refetch } = useQuery<CockpitData>({
    queryKey: ["analytics-v2", "cockpit"],
    queryFn: () => analyticsV2Api.getCockpit(),
    refetchInterval: 120_000,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  const kpis = data?.kpis;

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Cockpit</h1>
          <p className="text-sm text-muted-foreground">Tour de contrôle — marché et opportunités</p>
        </div>
        <Button onClick={() => refetch()} variant="ghost" size="sm">
          <RefreshCw className="h-4 w-4" />
        </Button>
      </div>

      {/* Signal pulse */}
      <SignalPulse count={data?.signals_count || 0} />

      {/* KPIs */}
      {kpis && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <KpiCard icon={Calendar} label="Événements (30j)" value={kpis.events_30d} color="#ec4899" href="/map" />
          <KpiCard icon={TrendingUp} label="Artistes en mouvement" value={kpis.artists_moving} color="#10b981" href="/discovery" />
          <KpiCard icon={MapPin} label="Zones actives" value={kpis.active_cities} color="#6366f1" href="/map" />
          <KpiCard icon={Target} label="Opportunités qualifiées" value={kpis.qualified_opportunities} color="#f59e0b" href="/intelligence" />
        </div>
      )}

      {/* Main grid: movements + hotspots */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Mouvements récents</CardTitle>
          </CardHeader>
          <CardContent>
            <MovementTimeline movements={data?.movements || []} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Zones actives</CardTitle>
          </CardHeader>
          <CardContent>
            <HotspotsMini hotspots={data?.hotspots || []} />
          </CardContent>
        </Card>
      </div>

      {/* Upcoming events */}
      {(data?.upcoming?.length || 0) > 0 && (
        <Card>
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm">Prochains événements</CardTitle>
              <Link href="/map" className="text-xs text-indigo-600 hover:underline flex items-center gap-1">
                Voir tout <ArrowRight className="h-3 w-3" />
              </Link>
            </div>
          </CardHeader>
          <CardContent>
            <div className="divide-y">
              {data?.upcoming?.map((ev, i) => (
                <div key={i} className="flex items-center gap-4 py-3 first:pt-0 last:pb-0">
                  <div className={`px-2 py-1 rounded text-xs font-bold ${urgencyColor(ev.days_until)}`}>
                    J-{ev.days_until}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{ev.artist_name}</p>
                    <p className="text-xs text-muted-foreground truncate">
                      {ev.venue} · {ev.city}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs font-medium">{ev.date_label}</p>
                    <Badge variant="outline" className="text-[10px]">{ev.event_type}</Badge>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Data quality */}
      {data?.data_quality && <DataQualityBar quality={data.data_quality} />}
    </div>
  );
}

export default function CockpitPage() {
  return (
    <ProtectedRoute>
      <AppLayout>
        <CockpitContent />
      </AppLayout>
    </ProtectedRoute>
  );
}
