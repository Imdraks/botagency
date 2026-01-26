"use client";

import { useState } from "react";
import { Filter, ChevronDown, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Slider } from "@/components/ui/slider";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";

export interface FeedFilters {
  timing: string[];
  scoreRange: [number, number];
  listenersRange: [number, number];
  recommendation: string[];
  country?: string;
}

interface FeedFiltersBarProps {
  filters: FeedFilters;
  onFiltersChange: (filters: FeedFilters) => void;
  onReset: () => void;
}

const TIMING_OPTIONS = [
  { value: "IMMINENT", label: "< 1 mois", color: "bg-red-100 text-red-800" },
  { value: "1_3M", label: "1-3 mois", color: "bg-orange-100 text-orange-800" },
  { value: "3_6M", label: "3-6 mois", color: "bg-yellow-100 text-yellow-800" },
  { value: "6_12M", label: "6-12 mois", color: "bg-blue-100 text-blue-800" },
  { value: "LONG", label: "> 12 mois", color: "bg-gray-100 text-gray-800" },
];

const RECOMMENDATION_OPTIONS = [
  { value: "SIGN", label: "🎯 À signer" },
  { value: "WATCH", label: "👀 À suivre" },
  { value: "PASS", label: "⏸️ Passer" },
];

const LISTENERS_PRESETS = [
  { label: "< 10K", min: 0, max: 10000 },
  { label: "10K-50K", min: 10000, max: 50000 },
  { label: "50K-100K", min: 50000, max: 100000 },
  { label: "100K-500K", min: 100000, max: 500000 },
  { label: "> 500K", min: 500000, max: 10000000 },
];

const formatListeners = (num: number): string => {
  if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
  if (num >= 1000) return `${(num / 1000).toFixed(0)}K`;
  return num.toString();
};

export function FeedFiltersBar({
  filters,
  onFiltersChange,
  onReset,
}: FeedFiltersBarProps) {
  const [isOpen, setIsOpen] = useState(false);

  const activeFiltersCount =
    filters.timing.length +
    filters.recommendation.length +
    (filters.scoreRange[0] > 0 || filters.scoreRange[1] < 100 ? 1 : 0) +
    (filters.listenersRange[0] > 0 || filters.listenersRange[1] < 10000000 ? 1 : 0);

  const toggleTiming = (value: string) => {
    const newTiming = filters.timing.includes(value)
      ? filters.timing.filter((t) => t !== value)
      : [...filters.timing, value];
    onFiltersChange({ ...filters, timing: newTiming });
  };

  const toggleRecommendation = (value: string) => {
    const newRec = filters.recommendation.includes(value)
      ? filters.recommendation.filter((r) => r !== value)
      : [...filters.recommendation, value];
    onFiltersChange({ ...filters, recommendation: newRec });
  };

  return (
    <div className="flex items-center gap-2 flex-wrap">
      {/* Main filter popover */}
      <Popover open={isOpen} onOpenChange={setIsOpen}>
        <PopoverTrigger asChild>
          <Button variant="outline" className="gap-2">
            <Filter className="h-4 w-4" />
            Filtres
            {activeFiltersCount > 0 && (
              <Badge variant="secondary" className="ml-1">
                {activeFiltersCount}
              </Badge>
            )}
            <ChevronDown className="h-4 w-4" />
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-80" align="start">
          <div className="space-y-4">
            {/* Timing filters */}
            <div>
              <Label className="text-sm font-medium">Timing (fenêtre de signature)</Label>
              <div className="flex flex-wrap gap-1 mt-2">
                {TIMING_OPTIONS.map((option) => (
                  <Badge
                    key={option.value}
                    variant={filters.timing.includes(option.value) ? "default" : "outline"}
                    className={`cursor-pointer transition-colors ${
                      filters.timing.includes(option.value) ? "" : "opacity-60 hover:opacity-100"
                    }`}
                    onClick={() => toggleTiming(option.value)}
                  >
                    {option.label}
                  </Badge>
                ))}
              </div>
            </div>

            {/* Score range */}
            <div>
              <Label className="text-sm font-medium">
                Score: {filters.scoreRange[0]} - {filters.scoreRange[1]}
              </Label>
              <Slider
                value={filters.scoreRange}
                onValueChange={(value) =>
                  onFiltersChange({ ...filters, scoreRange: value as [number, number] })
                }
                min={0}
                max={100}
                step={5}
                className="mt-2"
              />
            </div>

            {/* Listeners range */}
            <div>
              <Label className="text-sm font-medium">
                Auditeurs mensuels: {formatListeners(filters.listenersRange[0])} -{" "}
                {formatListeners(filters.listenersRange[1])}
              </Label>
              <div className="flex flex-wrap gap-1 mt-2">
                {LISTENERS_PRESETS.map((preset) => (
                  <Badge
                    key={preset.label}
                    variant={
                      filters.listenersRange[0] === preset.min &&
                      filters.listenersRange[1] === preset.max
                        ? "default"
                        : "outline"
                    }
                    className="cursor-pointer"
                    onClick={() =>
                      onFiltersChange({
                        ...filters,
                        listenersRange: [preset.min, preset.max],
                      })
                    }
                  >
                    {preset.label}
                  </Badge>
                ))}
              </div>
            </div>

            {/* Recommendation filters */}
            <div>
              <Label className="text-sm font-medium">Recommandation</Label>
              <div className="space-y-2 mt-2">
                {RECOMMENDATION_OPTIONS.map((option) => (
                  <div key={option.value} className="flex items-center gap-2">
                    <Checkbox
                      id={option.value}
                      checked={filters.recommendation.includes(option.value)}
                      onCheckedChange={() => toggleRecommendation(option.value)}
                    />
                    <Label htmlFor={option.value} className="cursor-pointer">
                      {option.label}
                    </Label>
                  </div>
                ))}
              </div>
            </div>

            {/* Reset button */}
            <Button
              variant="ghost"
              size="sm"
              className="w-full"
              onClick={() => {
                onReset();
                setIsOpen(false);
              }}
            >
              <X className="h-4 w-4 mr-1" />
              Réinitialiser les filtres
            </Button>
          </div>
        </PopoverContent>
      </Popover>

      {/* Active filters badges */}
      {filters.timing.map((t) => {
        const option = TIMING_OPTIONS.find((o) => o.value === t);
        return (
          <Badge
            key={t}
            variant="secondary"
            className="gap-1 cursor-pointer hover:bg-destructive hover:text-destructive-foreground"
            onClick={() => toggleTiming(t)}
          >
            {option?.label}
            <X className="h-3 w-3" />
          </Badge>
        );
      })}

      {filters.recommendation.map((r) => {
        const option = RECOMMENDATION_OPTIONS.find((o) => o.value === r);
        return (
          <Badge
            key={r}
            variant="secondary"
            className="gap-1 cursor-pointer hover:bg-destructive hover:text-destructive-foreground"
            onClick={() => toggleRecommendation(r)}
          >
            {option?.label}
            <X className="h-3 w-3" />
          </Badge>
        );
      })}
    </div>
  );
}
