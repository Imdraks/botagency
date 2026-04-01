"use client";

import { useState } from "react";
import { Landmark, MoreVertical, RefreshCw, Pause, Play, Trash2, Settings2, ExternalLink } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { BankStatusBadge } from "./BankStatusBadge";
import type { BankConnection } from "@/store/bankingStore";
import { useBankingStore } from "@/store/bankingStore";

// ============================================================================
// BANK CARD - One card per bank connection
// ============================================================================

interface BankCardProps {
  connection: BankConnection;
  onSelect: (connectionId: number) => void;
  isAdmin: boolean;
}

export function BankCard({ connection, onSelect, isAdmin }: BankCardProps) {
  const { triggerSync, suspendConnection, resumeConnection, deleteConnection, isSyncing } =
    useBankingStore();
  const [confirmDelete, setConfirmDelete] = useState(false);
  const syncing = isSyncing[connection.id] || false;

  const canSync =
    connection.status === "CONNECTED" || connection.status === "SYNC_ERROR";
  const isSuspended = connection.status === "SUSPENDED";

  const handleSync = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (canSync) {
      await triggerSync(connection.id);
    }
  };

  const handleDelete = async () => {
    const ok = await deleteConnection(connection.id);
    if (ok) setConfirmDelete(false);
  };

  const formatDate = (d?: string | null) => {
    if (!d) return "—";
    return new Date(d).toLocaleDateString("fr-FR", {
      day: "2-digit",
      month: "short",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const formatBalance = (b?: number | null) => {
    if (b == null) return "—";
    return new Intl.NumberFormat("fr-FR", {
      style: "currency",
      currency: "EUR",
    }).format(b);
  };

  return (
    <div
      onClick={() => onSelect(connection.id)}
      className={cn(
        "group relative rounded-xl border bg-white dark:bg-slate-900 p-5 transition-all duration-150 cursor-pointer",
        "hover:shadow-md hover:border-purple-200 dark:hover:border-purple-800/50",
        "border-gray-200 dark:border-slate-700/50",
      )}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-3 mb-4">
        <div className="flex items-center gap-3 min-w-0">
          {/* Bank logo / fallback */}
          {connection.provider === "revolut" ? (
            <img src="/revolut-logo.webp" alt="Revolut" className="w-10 h-10 rounded-xl flex-shrink-0" />
          ) : connection.bank_logo_url ? (
            <img
              src={connection.bank_logo_url}
              alt={connection.bank_name}
              className="w-10 h-10 rounded-lg object-contain bg-gray-50 dark:bg-slate-800 p-1"
            />
          ) : (
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-purple-500 to-blue-600 flex items-center justify-center flex-shrink-0">
              <Landmark className="h-5 w-5 text-white" />
            </div>
          )}
          <div className="min-w-0">
            <h3 className="text-sm font-semibold text-gray-900 dark:text-white truncate">
              {connection.bank_name}
            </h3>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              {connection.accounts_count} compte{connection.accounts_count !== 1 ? "s" : ""}
              {connection.provider && ` · via ${connection.provider}`}
            </p>
          </div>
        </div>

        {/* Actions menu (admin only) */}
        {isAdmin && (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity"
                onClick={(e) => e.stopPropagation()}
              >
                <MoreVertical className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-48">
              {canSync && (
                <DropdownMenuItem
                  onClick={(e) => {
                    e.stopPropagation();
                    triggerSync(connection.id);
                  }}
                >
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Synchroniser
                </DropdownMenuItem>
              )}
              <DropdownMenuItem
                onClick={(e) => {
                  e.stopPropagation();
                  onSelect(connection.id);
                }}
              >
                <Settings2 className="h-4 w-4 mr-2" />
                Paramètres
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              {isSuspended ? (
                <DropdownMenuItem
                  onClick={(e) => {
                    e.stopPropagation();
                    resumeConnection(connection.id);
                  }}
                >
                  <Play className="h-4 w-4 mr-2" />
                  Reprendre
                </DropdownMenuItem>
              ) : (
                <DropdownMenuItem
                  onClick={(e) => {
                    e.stopPropagation();
                    suspendConnection(connection.id);
                  }}
                >
                  <Pause className="h-4 w-4 mr-2" />
                  Suspendre
                </DropdownMenuItem>
              )}
              <DropdownMenuSeparator />
              <DropdownMenuItem
                onClick={(e) => {
                  e.stopPropagation();
                  setConfirmDelete(true);
                }}
                className="text-red-600 dark:text-red-400"
              >
                <Trash2 className="h-4 w-4 mr-2" />
                Supprimer
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        )}
      </div>

      {/* Status + Balance */}
      <div className="flex items-center justify-between mb-3">
        <BankStatusBadge status={connection.status} size="sm" />
        {connection.total_balance != null && (
          <span className="text-sm font-bold text-gray-900 dark:text-white">
            {formatBalance(connection.total_balance)}
          </span>
        )}
      </div>

      {/* Sync info */}
      <div className="flex items-center justify-between text-xs text-gray-400 dark:text-gray-500">
        <span>
          Dernière sync : {formatDate(connection.last_sync_at)}
        </span>
        {canSync && isAdmin && (
          <Button
            variant="ghost"
            size="sm"
            className="h-6 px-2 text-xs"
            onClick={handleSync}
            disabled={syncing}
          >
            <RefreshCw className={cn("h-3 w-3 mr-1", syncing && "animate-spin")} />
            {syncing ? "Sync…" : "Sync"}
          </Button>
        )}
      </div>

      {/* Consent warning */}
      {connection.consent_expires_at && (
        (() => {
          const daysLeft = Math.ceil(
            (new Date(connection.consent_expires_at).getTime() - Date.now()) / (1000 * 60 * 60 * 24)
          );
          if (daysLeft <= 14 && daysLeft > 0) {
            return (
              <div className="mt-3 px-3 py-2 rounded-lg bg-amber-50 dark:bg-amber-900/20 text-amber-700 dark:text-amber-400 text-xs">
                ⚠️ Consentement expire dans {daysLeft} jour{daysLeft > 1 ? "s" : ""}
              </div>
            );
          }
          if (daysLeft <= 0) {
            return (
              <div className="mt-3 px-3 py-2 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400 text-xs">
                🔴 Consentement expiré – Reconnexion nécessaire
              </div>
            );
          }
          return null;
        })()
      )}

      {/* Delete confirmation */}
      {confirmDelete && (
        <div
          className="absolute inset-0 bg-white/95 dark:bg-slate-900/95 rounded-xl flex flex-col items-center justify-center gap-3 z-10"
          onClick={(e) => e.stopPropagation()}
        >
          <p className="text-sm text-gray-700 dark:text-gray-300 text-center px-4">
            Supprimer la connexion à <strong>{connection.bank_name}</strong> ?
            <br />
            <span className="text-xs text-gray-500">Cette action est irréversible.</span>
          </p>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={() => setConfirmDelete(false)}>
              Annuler
            </Button>
            <Button variant="destructive" size="sm" onClick={handleDelete}>
              Supprimer
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
