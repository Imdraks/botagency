"use client";

import * as React from "react";
import { useCallback, useEffect, useState, useMemo } from "react";
import { Slider } from "@/components/ui/slider";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { cn, formatCurrency } from "@/lib/utils";
import { BudgetBucket } from "@/lib/types";

interface BudgetFilterProps {
  min: number;
  max: number;
  histogram: BudgetBucket[];
  value: [number, number];
  onChange: (value: [number, number]) => void;
  className?: string;
}

/**
 * Budget Filter Component
 * 
 * Features:
 * - Mini histogram showing budget distribution
 * - Dual-handle range slider (min/max)
 * - Two input fields for Min and Max EUR, synchronized with slider
 */
export function BudgetFilter({
  min,
  max,
  histogram,
  value,
  onChange,
  className,
}: BudgetFilterProps) {
  const [localMin, setLocalMin] = useState(value[0].toString());
  const [localMax, setLocalMax] = useState(value[1].toString());

  // Sync local state with props
  useEffect(() => {
    setLocalMin(value[0].toString());
    setLocalMax(value[1].toString());
  }, [value]);

  // Calculate max count for histogram scaling
  const maxCount = useMemo(() => {
    return Math.max(...histogram.map((b) => b.count), 1);
  }, [histogram]);

  // Handle slider change
  const handleSliderChange = useCallback(
    (newValue: number[]) => {
      const [newMin, newMax] = newValue;
      onChange([newMin, newMax]);
    },
    [onChange]
  );

  // Handle input change for min
  const handleMinChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const inputValue = e.target.value.replace(/\D/g, "");
      setLocalMin(inputValue);
    },
    []
  );

  // Handle input change for max
  const handleMaxChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const inputValue = e.target.value.replace(/\D/g, "");
      setLocalMax(inputValue);
    },
    []
  );

  // Commit min value on blur
  const handleMinBlur = useCallback(() => {
    const numValue = parseInt(localMin) || min;
    const clampedValue = Math.max(min, Math.min(numValue, value[1]));
    setLocalMin(clampedValue.toString());
    if (clampedValue !== value[0]) {
      onChange([clampedValue, value[1]]);
    }
  }, [localMin, min, value, onChange]);

  // Commit max value on blur
  const handleMaxBlur = useCallback(() => {
    const numValue = parseInt(localMax) || max;
    const clampedValue = Math.min(max, Math.max(numValue, value[0]));
    setLocalMax(clampedValue.toString());
    if (clampedValue !== value[1]) {
      onChange([value[0], clampedValue]);
    }
  }, [localMax, max, value, onChange]);

  // Handle Enter key
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent, type: "min" | "max") => {
      if (e.key === "Enter") {
        if (type === "min") {
          handleMinBlur();
        } else {
          handleMaxBlur();
        }
      }
    },
    [handleMinBlur, handleMaxBlur]
  );

  // Calculate if a bucket is within the selected range
  const isInRange = useCallback(
    (bucket: BudgetBucket) => {
      return bucket.min >= value[0] && bucket.max <= value[1];
    },
    [value]
  );

  return (
    <div className={cn("space-y-3", className)}>
      <Label className="text-sm font-medium">Budget</Label>
      
      {/* Histogram */}
      <div className="relative h-16 w-full">
        <div className="absolute inset-0 flex items-end gap-px">
          {histogram.map((bucket, index) => {
            const height = (bucket.count / maxCount) * 100;
            const inRange = isInRange(bucket);
            
            return (
              <div
                key={index}
                className="flex-1 relative group"
                title={`${formatCurrency(bucket.min)} - ${formatCurrency(bucket.max)}: ${bucket.count} opportunité${bucket.count > 1 ? "s" : ""}`}
              >
                <div
                  className={cn(
                    "w-full rounded-t transition-colors duration-200",
                    inRange ? "bg-primary" : "bg-muted-foreground/20"
                  )}
                  style={{ height: `${Math.max(height, 2)}%` }}
                />
                {/* Hover tooltip */}
                <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-popover border rounded text-xs whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10">
                  <div className="font-medium">{bucket.count} opp.</div>
                  <div className="text-muted-foreground">
                    {formatCurrency(bucket.min)} - {formatCurrency(bucket.max)}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Dual Range Slider */}
      <Slider
        min={min}
        max={max}
        step={Math.max(1, Math.floor((max - min) / 100))}
        value={value}
        onValueChange={handleSliderChange}
        className="w-full"
      />

      {/* Min/Max display */}
      <div className="flex justify-between text-xs text-muted-foreground">
        <span>{formatCurrency(min)}</span>
        <span>{formatCurrency(max)}</span>
      </div>

      {/* Input fields */}
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-1">
          <Label htmlFor="budget-min" className="text-xs text-muted-foreground">
            Min (EUR)
          </Label>
          <div className="relative">
            <Input
              id="budget-min"
              type="text"
              inputMode="numeric"
              value={localMin}
              onChange={handleMinChange}
              onBlur={handleMinBlur}
              onKeyDown={(e) => handleKeyDown(e, "min")}
              className="pr-8"
            />
            <span className="absolute right-3 top-1/2 -translate-y-1/2 text-sm text-muted-foreground">
              €
            </span>
          </div>
        </div>
        <div className="space-y-1">
          <Label htmlFor="budget-max" className="text-xs text-muted-foreground">
            Max (EUR)
          </Label>
          <div className="relative">
            <Input
              id="budget-max"
              type="text"
              inputMode="numeric"
              value={localMax}
              onChange={handleMaxChange}
              onBlur={handleMaxBlur}
              onKeyDown={(e) => handleKeyDown(e, "max")}
              className="pr-8"
            />
            <span className="absolute right-3 top-1/2 -translate-y-1/2 text-sm text-muted-foreground">
              €
            </span>
          </div>
        </div>
      </div>

      {/* Selected range summary */}
      <div className="text-center text-sm font-medium text-primary">
        {formatCurrency(value[0])} - {formatCurrency(value[1])}
      </div>
    </div>
  );
}

// Default export for convenience
export default BudgetFilter;
