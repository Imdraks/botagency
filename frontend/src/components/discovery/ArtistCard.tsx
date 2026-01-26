"use client";

import { useState } from "react";
import { RefreshCw, AlertCircle, Clock, ExternalLink, Plus, Sparkles } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import Image from "next/image";

// Types
export interface ArtistReason {
  label: string;
  value?: string;
  impact?: number;
}

export interface ArtistCardData {
  id: number;
  name: string;
  image_url?: string;
  timing_bucket?: string;
  timing_label?: string;
  score: number;
  recommendation?: string;
  monthly_listeners?: number;
  followers?: number;
  velocity?: number;
  acceleration?: number;
  data_quality?: string;
  drivers: ArtistReason[];
  risks: ArtistReason[];
  signals: string[];
  rank_score?: number;
  candidate_type?: string;
  last_enriched_at?: string;
  is_stale: boolean;
}

interface ArtistCardProps {
  artist: ArtistCardData;
  onRefresh?: (artistId: number) => void;
  onAddToComparison?: (artistId: number) => void;
  onViewDetail?: (artistId: number) => void;
  isRefreshing?: boolean;
}

// Helper functions
const formatNumber = (num?: number): string => {
  if (!num) return "-";
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

const getRecommendationBadge = (rec?: string) => {
  if (!rec) return null;
  const styles: Record<string, string> = {
    SIGN: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200",
    WATCH: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200",
    PASS: "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200",
  };
  const labels: Record<string, string> = {
    SIGN: "🎯 À signer",
    WATCH: "👀 À suivre",
    PASS: "⏸️ Passer",
  };
  return (
    <Badge className={styles[rec] || styles.PASS}>
      {labels[rec] || rec}
    </Badge>
  );
};

const getTimingBadge = (bucket?: string, label?: string) => {
  if (!bucket) return null;
  const styles: Record<string, string> = {
    IMMINENT: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200",
    "1_3M": "bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200",
    "3_6M": "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200",
    "6_12M": "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200",
    LONG: "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200",
  };
  return (
    <Badge variant="outline" className={styles[bucket] || ""}>
      <Clock className="h-3 w-3 mr-1" />
      {label || bucket}
    </Badge>
  );
};

const getDataQualityIndicator = (quality?: string) => {
  const colors: Record<string, string> = {
    HIGH: "bg-green-500",
    MEDIUM: "bg-yellow-500",
    LOW: "bg-red-500",
  };
  return (
    <div className="flex items-center gap-1">
      <div className={`w-2 h-2 rounded-full ${colors[quality || "LOW"]}`} />
      <span className="text-xs text-muted-foreground">
        {quality === "HIGH" ? "Données fiables" : quality === "MEDIUM" ? "Données partielles" : "Données limitées"}
      </span>
    </div>
  );
};

export function ArtistCard({
  artist,
  onRefresh,
  onAddToComparison,
  onViewDetail,
  isRefreshing = false,
}: ArtistCardProps) {
  const [isHovered, setIsHovered] = useState(false);

  return (
    <Card
      className={`relative overflow-hidden transition-all duration-300 hover:shadow-lg ${
        artist.is_stale ? "border-yellow-400 dark:border-yellow-600" : ""
      }`}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Stale indicator */}
      {artist.is_stale && (
        <div className="absolute top-0 left-0 right-0 bg-yellow-100 dark:bg-yellow-900/30 px-3 py-1 text-xs text-yellow-800 dark:text-yellow-200 flex items-center gap-1">
          <AlertCircle className="h-3 w-3" />
          Données datant de plus de 24h
        </div>
      )}

      <CardContent className={`p-4 ${artist.is_stale ? "pt-8" : ""}`}>
        {/* Header with image and name */}
        <div className="flex items-start gap-3 mb-3">
          <div className="relative w-16 h-16 rounded-lg overflow-hidden bg-gray-100 dark:bg-gray-800 flex-shrink-0">
            {artist.image_url ? (
              <Image
                src={artist.image_url}
                alt={artist.name}
                fill
                className="object-cover"
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center">
                <Sparkles className="h-6 w-6 text-gray-400" />
              </div>
            )}
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-lg truncate">{artist.name}</h3>
            <div className="flex items-center gap-2 mt-1">
              {getRecommendationBadge(artist.recommendation)}
              {getTimingBadge(artist.timing_bucket, artist.timing_label)}
            </div>
          </div>
          {/* Score */}
          <div className="text-right flex-shrink-0">
            <div className={`text-3xl font-bold ${getScoreColor(artist.score)}`}>
              {artist.score}
            </div>
            <div className="text-xs text-muted-foreground">score</div>
          </div>
        </div>

        {/* Metrics */}
        <div className="grid grid-cols-3 gap-2 mb-3 text-sm">
          <div className="bg-gray-50 dark:bg-gray-800 rounded p-2 text-center">
            <div className="font-semibold">{formatNumber(artist.monthly_listeners)}</div>
            <div className="text-xs text-muted-foreground">Auditeurs</div>
          </div>
          <div className="bg-gray-50 dark:bg-gray-800 rounded p-2 text-center">
            <div className="font-semibold text-green-600">
              {artist.velocity ? `+${(artist.velocity * 100).toFixed(0)}%` : "-"}
            </div>
            <div className="text-xs text-muted-foreground">Croissance</div>
          </div>
          <div className="bg-gray-50 dark:bg-gray-800 rounded p-2 text-center">
            <div className="font-semibold">{formatNumber(artist.followers)}</div>
            <div className="text-xs text-muted-foreground">Followers</div>
          </div>
        </div>

        {/* Drivers (top 2) */}
        {artist.drivers.length > 0 && (
          <div className="space-y-1 mb-3">
            {artist.drivers.slice(0, 2).map((driver, idx) => (
              <div key={idx} className="flex items-center gap-2 text-sm">
                <div className="w-1.5 h-1.5 rounded-full bg-green-500" />
                <span className="text-muted-foreground">{driver.label}</span>
                {driver.value && (
                  <span className="ml-auto font-medium text-green-600">{driver.value}</span>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Signals */}
        {artist.signals.length > 0 && (
          <div className="flex flex-wrap gap-1 mb-3">
            {artist.signals.slice(0, 3).map((signal, idx) => (
              <Badge key={idx} variant="secondary" className="text-xs">
                {signal}
              </Badge>
            ))}
          </div>
        )}

        {/* Data quality */}
        {getDataQualityIndicator(artist.data_quality)}

        {/* Actions (visible on hover) */}
        <div
          className={`flex items-center gap-2 mt-3 pt-3 border-t transition-opacity duration-200 ${
            isHovered ? "opacity-100" : "opacity-0"
          }`}
        >
          {onViewDetail && (
            <Button
              variant="outline"
              size="sm"
              className="flex-1"
              onClick={() => onViewDetail(artist.id)}
            >
              <ExternalLink className="h-4 w-4 mr-1" />
              Détails
            </Button>
          )}
          {onAddToComparison && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => onAddToComparison(artist.id)}
            >
              <Plus className="h-4 w-4" />
            </Button>
          )}
          {onRefresh && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onRefresh(artist.id)}
              disabled={isRefreshing}
            >
              <RefreshCw className={`h-4 w-4 ${isRefreshing ? "animate-spin" : ""}`} />
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
