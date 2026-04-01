"use client";

import { cn } from "@/lib/utils";
import type { BankConnectionStatus } from "@/store/bankingStore";

// ============================================================================
// STATUS CONFIGURATION
// ============================================================================

interface StatusConfig {
  label: string;
  color: string;
  bgColor: string;
  dotColor: string;
  pulse?: boolean;
}

const STATUS_MAP: Record<BankConnectionStatus, StatusConfig> = {
  NOT_CONNECTED: {
    label: "Non connecté",
    color: "text-gray-500 dark:text-gray-400",
    bgColor: "bg-gray-100 dark:bg-gray-800",
    dotColor: "bg-gray-400",
  },
  CONNECTING: {
    label: "Connexion en cours…",
    color: "text-blue-600 dark:text-blue-400",
    bgColor: "bg-blue-50 dark:bg-blue-900/30",
    dotColor: "bg-blue-500",
    pulse: true,
  },
  CONNECTED: {
    label: "Connecté",
    color: "text-emerald-600 dark:text-emerald-400",
    bgColor: "bg-emerald-50 dark:bg-emerald-900/30",
    dotColor: "bg-emerald-500",
  },
  SYNC_ERROR: {
    label: "Erreur de sync",
    color: "text-red-600 dark:text-red-400",
    bgColor: "bg-red-50 dark:bg-red-900/30",
    dotColor: "bg-red-500",
  },
  CONSENT_EXPIRED: {
    label: "Consentement expiré",
    color: "text-amber-600 dark:text-amber-400",
    bgColor: "bg-amber-50 dark:bg-amber-900/30",
    dotColor: "bg-amber-500",
  },
  ACTION_REQUIRED: {
    label: "Action requise",
    color: "text-orange-600 dark:text-orange-400",
    bgColor: "bg-orange-50 dark:bg-orange-900/30",
    dotColor: "bg-orange-500",
    pulse: true,
  },
  SUSPENDED: {
    label: "Suspendu",
    color: "text-gray-500 dark:text-gray-400",
    bgColor: "bg-gray-100 dark:bg-gray-800",
    dotColor: "bg-gray-400",
  },
  REVOKED: {
    label: "Révoqué",
    color: "text-red-700 dark:text-red-300",
    bgColor: "bg-red-100 dark:bg-red-900/40",
    dotColor: "bg-red-600",
  },
};

// ============================================================================
// COMPONENT
// ============================================================================

interface BankStatusBadgeProps {
  status: BankConnectionStatus;
  size?: "sm" | "md";
  className?: string;
}

export function BankStatusBadge({ status, size = "md", className }: BankStatusBadgeProps) {
  const config = STATUS_MAP[status] || STATUS_MAP.NOT_CONNECTED;

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full font-medium",
        config.bgColor,
        config.color,
        size === "sm" ? "px-2 py-0.5 text-[10px]" : "px-2.5 py-1 text-xs",
        className,
      )}
    >
      <span
        className={cn(
          "rounded-full flex-shrink-0",
          config.dotColor,
          size === "sm" ? "h-1.5 w-1.5" : "h-2 w-2",
          config.pulse && "animate-pulse",
        )}
      />
      {config.label}
    </span>
  );
}

// ============================================================================
// SYNC STATUS BADGE
// ============================================================================

interface SyncStatusBadgeProps {
  status: string;
  className?: string;
}

const SYNC_STATUS_MAP: Record<string, { label: string; color: string; bg: string }> = {
  RUNNING: { label: "En cours", color: "text-blue-600", bg: "bg-blue-50 dark:bg-blue-900/30" },
  SUCCESS: { label: "Réussi", color: "text-emerald-600", bg: "bg-emerald-50 dark:bg-emerald-900/30" },
  PARTIAL: { label: "Partiel", color: "text-amber-600", bg: "bg-amber-50 dark:bg-amber-900/30" },
  FAILED: { label: "Échoué", color: "text-red-600", bg: "bg-red-50 dark:bg-red-900/30" },
  CANCELLED: { label: "Annulé", color: "text-gray-500", bg: "bg-gray-100 dark:bg-gray-800" },
};

export function SyncStatusBadge({ status, className }: SyncStatusBadgeProps) {
  const config = SYNC_STATUS_MAP[status] || SYNC_STATUS_MAP.FAILED;
  return (
    <span
      className={cn(
        "inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium",
        config.bg,
        config.color,
        className,
      )}
    >
      {config.label}
    </span>
  );
}
