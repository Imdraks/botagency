"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import {
  Landmark,
  RefreshCw,
  AlertTriangle,
  TrendingUp,
  ArrowLeft,
  Wallet,
  Clock,
  ShieldCheck,
  ChevronRight,
  Settings2,
  ExternalLink,
  Unplug,
  ArrowDownUp,
  CreditCard,
  CheckCircle2,
  XCircle,
  Loader2,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { AppLayout } from "@/components/layout/AppLayout";
import { useBankingStore } from "@/store/bankingStore";
import { useAuthStore } from "@/store/auth";
import { BankCard, BankStatusBadge, SyncStatusBadge } from "@/components/banking";
import type { BankConnectionDetail, BankAccount, RevolutTransaction } from "@/store/bankingStore";

// ============================================================================
// MAIN PAGE
// ============================================================================

function BankingPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user } = useAuthStore();
  const {
    dashboard,
    connections,
    selectedConnection,
    accounts,
    isLoading,
    error,
    fetchDashboard,
    fetchConnectionDetail,
    fetchAccounts,
    // Revolut
    revolutStatus,
    revolutTransactions,
    revolutTransactionsLoading,
    fetchRevolutStatus,
    connectRevolut,
    completeRevolutOAuth,
    syncRevolut,
    fetchRevolutTransactions,
    disconnectRevolut,
  } = useBankingStore();

  const [view, setView] = useState<"list" | "detail" | "revolut">("list");
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [revolutConnecting, setRevolutConnecting] = useState(false);
  const [revolutSuccess, setRevolutSuccess] = useState<string | null>(null);

  const isAdmin = user?.role === "admin" || user?.is_superuser === true;

  // Load dashboard + Revolut status on mount
  useEffect(() => {
    fetchDashboard();
    fetchRevolutStatus();
  }, [fetchDashboard, fetchRevolutStatus]);

  // Handle Revolut OAuth callback params
  useEffect(() => {
    const revolutConnected = searchParams.get("revolut_connected");
    const revolutError = searchParams.get("revolut_error");
    const accountsCount = searchParams.get("accounts");

    if (revolutConnected === "true") {
      setRevolutSuccess(`Revolut connecté ! ${accountsCount || 0} compte(s) synchronisé(s).`);
      fetchDashboard();
      fetchRevolutStatus();
      // Clean URL
      router.replace("/banking");
    }
    if (revolutError) {
      useBankingStore.setState({
        error: `Erreur Revolut : ${decodeURIComponent(revolutError)}`,
      });
      router.replace("/banking");
    }
  }, [searchParams, fetchDashboard, fetchRevolutStatus, router]);

  // Load connection detail when selected
  useEffect(() => {
    if (selectedId) {
      fetchConnectionDetail(selectedId);
      setView("detail");
    }
  }, [selectedId, fetchConnectionDetail]);

  const handleSelectConnection = (id: number) => {
    setSelectedId(id);
  };

  const handleBack = () => {
    setSelectedId(null);
    setView("list");
    fetchDashboard();
    fetchRevolutStatus();
  };

  const handleConnectRevolut = async () => {
    setRevolutConnecting(true);
    const url = await connectRevolut();
    setRevolutConnecting(false);
    if (url) {
      window.location.href = url;
    }
  };

  const handleRevolutView = () => {
    setView("revolut");
    fetchRevolutTransactions();
  };

  const formatCurrency = (val: number) =>
    new Intl.NumberFormat("fr-FR", {
      style: "currency",
      currency: "EUR",
    }).format(val);

  const formatDate = (d?: string | null) => {
    if (!d) return "—";
    return new Date(d).toLocaleDateString("fr-FR", {
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  // ─── NOT ENABLED STATE ─────────────────────────────────────────────
  if (dashboard && !dashboard.banking_enabled) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-center px-4">
        <div className="w-16 h-16 rounded-2xl bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center mb-6">
          <Landmark className="h-8 w-8 text-purple-600 dark:text-purple-400" />
        </div>
        <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
          Connexions bancaires
        </h2>
        <p className="text-gray-500 dark:text-gray-400 max-w-md mb-6">
          Cette fonctionnalité n&apos;est pas encore activée pour votre espace de travail.
          Contactez votre administrateur pour l&apos;activer.
        </p>
        <div className="flex items-center gap-2 text-xs text-gray-400">
          <ShieldCheck className="h-4 w-4" />
          Radar Business · Connexions bancaires sécurisées
        </div>
      </div>
    );
  }

  // ─── DETAIL VIEW ───────────────────────────────────────────────────
  if (view === "detail" && selectedConnection) {
    return (
      <ConnectionDetailView
        connection={selectedConnection}
        isAdmin={isAdmin}
        onBack={handleBack}
        formatDate={formatDate}
        formatCurrency={formatCurrency}
      />
    );
  }

  // ─── REVOLUT VIEW ────────────────────────────────────────────────
  if (view === "revolut" && revolutStatus?.connected) {
    return (
      <RevolutDetailView
        revolutStatus={revolutStatus}
        transactions={revolutTransactions}
        transactionsLoading={revolutTransactionsLoading}
        isAdmin={isAdmin}
        onBack={handleBack}
        onSync={syncRevolut}
        onDisconnect={disconnectRevolut}
        onFetchTransactions={fetchRevolutTransactions}
        formatDate={formatDate}
        formatCurrency={formatCurrency}
        isLoading={isLoading}
      />
    );
  }

  // ─── LIST VIEW (DASHBOARD) ────────────────────────────────────────
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <Landmark className="h-6 w-6 text-purple-600" />
            Connexions bancaires
          </h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Vue d&apos;ensemble de vos comptes bancaires connectés
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => fetchDashboard()}
            disabled={isLoading}
          >
            <RefreshCw className={cn("h-4 w-4 mr-1", isLoading && "animate-spin")} />
            Actualiser
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => router.push("/settings")}
          >
            <Settings2 className="h-4 w-4 mr-1" />
            Gérer
          </Button>
        </div>
      </div>

      {/* Error banner */}
      {error && (
        <div className="px-4 py-3 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400 text-sm flex items-center gap-2">
          <AlertTriangle className="h-4 w-4 flex-shrink-0" />
          {error}
        </div>
      )}

      {/* Stats Cards */}
      {dashboard && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            label="Banques connectées"
            value={dashboard.active_connections}
            total={dashboard.total_connections}
            icon={Landmark}
            color="purple"
          />
          <StatCard
            label="Comptes actifs"
            value={dashboard.total_accounts}
            icon={Wallet}
            color="blue"
          />
          <StatCard
            label="Solde total"
            value={
              dashboard.total_balances["EUR"]
                ? formatCurrency(dashboard.total_balances["EUR"])
                : "—"
            }
            icon={TrendingUp}
            color="emerald"
          />
          <StatCard
            label="Dernière sync"
            value={dashboard.last_sync_at ? formatDate(dashboard.last_sync_at) : "Jamais"}
            icon={Clock}
            color="amber"
          />
        </div>
      )}

      {/* Revolut success banner */}
      {revolutSuccess && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="px-4 py-3 rounded-lg bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-200 dark:border-emerald-800/50 text-emerald-700 dark:text-emerald-400 text-sm flex items-center gap-2"
        >
          <CheckCircle2 className="h-4 w-4 flex-shrink-0" />
          {revolutSuccess}
          <button
            onClick={() => setRevolutSuccess(null)}
            className="ml-auto text-emerald-500 hover:text-emerald-700"
          >
            <XCircle className="h-4 w-4" />
          </button>
        </motion.div>
      )}

      {/* Consent alerts */}
      {dashboard && dashboard.expiring_consents > 0 && (
        <div className="px-4 py-3 rounded-lg bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800/50 text-amber-700 dark:text-amber-400 text-sm flex items-center gap-2">
          <AlertTriangle className="h-4 w-4 flex-shrink-0" />
          {dashboard.expiring_consents} consentement{dashboard.expiring_consents > 1 ? "s" : ""}{" "}
          expire{dashboard.expiring_consents > 1 ? "nt" : ""} dans les 14 prochains jours.
          <Button variant="link" size="sm" className="text-amber-700 dark:text-amber-400 px-0">
            Renouveler →
          </Button>
        </div>
      )}

      {/* ── Revolut Section ──────────────────────────────────── */}
      <div className="rounded-xl border border-gray-200 dark:border-slate-700/50 bg-white dark:bg-slate-900 overflow-hidden">
        <div className="px-5 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-[#0075EB] flex items-center justify-center">
              <span className="text-white text-lg font-bold">R</span>
            </div>
            <div>
              <h3 className="text-sm font-semibold text-gray-900 dark:text-white">
                Revolut Business
              </h3>
              <p className="text-xs text-gray-400">
                {revolutStatus?.connected
                  ? `${revolutStatus.accounts_count} compte(s) · Dernière sync ${revolutStatus.last_sync_at ? new Date(revolutStatus.last_sync_at).toLocaleDateString("fr-FR") : "—"}`
                  : "Connectez votre compte Revolut Business"}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {revolutStatus?.connected ? (
              <>
                <span className="flex items-center gap-1.5 text-xs font-medium text-emerald-600 dark:text-emerald-400">
                  <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                  Connecté
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => syncRevolut()}
                  disabled={isLoading}
                >
                  <RefreshCw className={cn("h-3.5 w-3.5 mr-1", isLoading && "animate-spin")} />
                  Sync
                </Button>
                <Button
                  variant="default"
                  size="sm"
                  onClick={handleRevolutView}
                >
                  <ArrowDownUp className="h-3.5 w-3.5 mr-1" />
                  Transactions
                </Button>
              </>
            ) : (
              <Button
                size="sm"
                onClick={handleConnectRevolut}
                disabled={revolutConnecting}
                className="bg-[#0075EB] hover:bg-[#005fc0] text-white"
              >
                {revolutConnecting ? (
                  <Loader2 className="h-3.5 w-3.5 mr-1 animate-spin" />
                ) : (
                  <ExternalLink className="h-3.5 w-3.5 mr-1" />
                )}
                Connecter Revolut
              </Button>
            )}
          </div>
        </div>
      </div>

      {/* Connections Grid */}
      {isLoading && connections.length === 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="h-48 rounded-xl border border-gray-200 dark:border-slate-700/50 bg-gray-50 dark:bg-slate-800/50 animate-pulse"
            />
          ))}
        </div>
      ) : connections.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <AnimatePresence>
            {connections.map((conn) => (
              <motion.div
                key={conn.id}
                layout
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                transition={{ duration: 0.2 }}
              >
                <BankCard
                  connection={conn}
                  onSelect={handleSelectConnection}
                  isAdmin={false}
                />
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      ) : (
        /* Empty state */
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <div className="w-14 h-14 rounded-2xl bg-gray-100 dark:bg-slate-800 flex items-center justify-center mb-4">
            <Landmark className="h-7 w-7 text-gray-400" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-1">
            Aucune banque connectée
          </h3>
          <p className="text-sm text-gray-500 dark:text-gray-400 max-w-sm mb-6">
            Connectez votre première banque pour centraliser la vue de vos comptes professionnels.
          </p>
          <Button
            variant="outline"
            onClick={() => router.push("/settings")}
          >
            <Settings2 className="h-4 w-4 mr-2" />
            Gérer dans les paramètres
          </Button>
        </div>
      )}
    </div>
  );
}

// ============================================================================
// STAT CARD
// ============================================================================

function StatCard({
  label,
  value,
  total,
  icon: Icon,
  color,
}: {
  label: string;
  value: string | number;
  total?: number;
  icon: React.ElementType;
  color: "purple" | "blue" | "emerald" | "amber";
}) {
  const colorMap = {
    purple: "bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400",
    blue: "bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400",
    emerald: "bg-emerald-100 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400",
    amber: "bg-amber-100 dark:bg-amber-900/30 text-amber-600 dark:text-amber-400",
  };

  return (
    <div className="rounded-xl border border-gray-200 dark:border-slate-700/50 bg-white dark:bg-slate-900 p-4">
      <div className="flex items-center gap-3 mb-2">
        <div className={cn("w-9 h-9 rounded-lg flex items-center justify-center", colorMap[color])}>
          <Icon className="h-4 w-4" />
        </div>
        <span className="text-xs font-medium text-gray-500 dark:text-gray-400">{label}</span>
      </div>
      <p className="text-lg font-bold text-gray-900 dark:text-white">
        {value}
        {total !== undefined && (
          <span className="text-sm font-normal text-gray-400 ml-1">/ {total}</span>
        )}
      </p>
    </div>
  );
}

// ============================================================================
// CONNECTION DETAIL VIEW
// ============================================================================

function ConnectionDetailView({
  connection,
  isAdmin,
  onBack,
  formatDate,
  formatCurrency,
}: {
  connection: BankConnectionDetail;
  isAdmin: boolean;
  onBack: () => void;
  formatDate: (d?: string | null) => string;
  formatCurrency: (val: number) => string;
}) {
  const router = useRouter();

  return (
    <div className="space-y-6">
      {/* Back button + Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={onBack}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div className="flex items-center gap-3">
            {connection.bank_logo_url ? (
              <img
                src={connection.bank_logo_url}
                alt=""
                className="w-10 h-10 rounded-lg object-contain bg-gray-50 dark:bg-slate-800 p-1"
              />
            ) : (
              <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-purple-500 to-blue-600 flex items-center justify-center">
                <Landmark className="h-5 w-5 text-white" />
              </div>
            )}
            <div>
              <h1 className="text-xl font-bold text-gray-900 dark:text-white">
                {connection.bank_name}
              </h1>
              <div className="flex items-center gap-2 mt-0.5">
                <BankStatusBadge status={connection.status} size="sm" />
                {connection.provider && (
                  <span className="text-xs text-gray-400">via {connection.provider}</span>
                )}
              </div>
            </div>
          </div>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => router.push("/settings")}
        >
          <Settings2 className="h-4 w-4 mr-1" />
          Gérer
        </Button>
      </div>

      {/* Consent info */}
      {connection.active_consent && (
        <div className="rounded-xl border border-gray-200 dark:border-slate-700/50 bg-white dark:bg-slate-900 p-4">
          <div className="flex items-center gap-2 mb-3">
            <ShieldCheck className="h-4 w-4 text-emerald-600" />
            <h3 className="text-sm font-semibold text-gray-900 dark:text-white">
              Consentement {connection.active_consent.consent_type}
            </h3>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
            <div>
              <span className="text-gray-400">Accordé le</span>
              <p className="font-medium text-gray-700 dark:text-gray-300">
                {formatDate(connection.active_consent.granted_at)}
              </p>
            </div>
            <div>
              <span className="text-gray-400">Expire le</span>
              <p className="font-medium text-gray-700 dark:text-gray-300">
                {formatDate(connection.active_consent.expires_at)}
              </p>
            </div>
            <div>
              <span className="text-gray-400">Jours restants</span>
              <p className={cn(
                "font-medium",
                (connection.active_consent.days_until_expiry ?? 0) <= 14
                  ? "text-amber-600"
                  : "text-emerald-600",
              )}>
                {connection.active_consent.days_until_expiry ?? "—"}
              </p>
            </div>
            <div>
              <span className="text-gray-400">Portée</span>
              <p className="font-medium text-gray-700 dark:text-gray-300">
                {connection.active_consent.scope?.join(", ") || "—"}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Accounts */}
      <div className="rounded-xl border border-gray-200 dark:border-slate-700/50 bg-white dark:bg-slate-900 overflow-hidden">
        <div className="px-4 py-3 border-b border-gray-100 dark:border-slate-800 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-gray-900 dark:text-white">
            Comptes ({connection.accounts.length})
          </h3>
        </div>
        {connection.accounts.length > 0 ? (
          <div className="divide-y divide-gray-100 dark:divide-slate-800">
            {connection.accounts.map((acc) => (
              <div key={acc.id} className="px-4 py-3 flex items-center justify-between">
                <div className="flex items-center gap-3 min-w-0">
                  <div
                    className="w-3 h-3 rounded-full flex-shrink-0"
                    style={{ backgroundColor: acc.display_color || "#8B5CF6" }}
                  />
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                      {acc.account_name}
                    </p>
                    <p className="text-xs text-gray-400">
                      {acc.account_type} · {acc.currency}
                      {acc.iban_masked && ` · ${acc.iban_masked}`}
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-bold text-gray-900 dark:text-white">
                    {acc.balance != null ? formatCurrency(acc.balance) : "—"}
                  </p>
                  {acc.balance_updated_at && (
                    <p className="text-[10px] text-gray-400">
                      {formatDate(acc.balance_updated_at)}
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="px-4 py-8 text-center text-sm text-gray-400">
            Aucun compte découvert. Lancez une synchronisation.
          </div>
        )}
      </div>

      {/* Sync History */}
      <div className="rounded-xl border border-gray-200 dark:border-slate-700/50 bg-white dark:bg-slate-900 overflow-hidden">
        <div className="px-4 py-3 border-b border-gray-100 dark:border-slate-800">
          <h3 className="text-sm font-semibold text-gray-900 dark:text-white">
            Historique de synchronisation
          </h3>
        </div>
        {connection.recent_syncs.length > 0 ? (
          <div className="divide-y divide-gray-100 dark:divide-slate-800">
            {connection.recent_syncs.map((sync) => (
              <div key={sync.id} className="px-4 py-3 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <SyncStatusBadge status={sync.status} />
                  <div>
                    <p className="text-xs text-gray-600 dark:text-gray-300">
                      {formatDate(sync.started_at)}
                    </p>
                    {sync.error_message && (
                      <p className="text-xs text-red-500 mt-0.5">{sync.error_message}</p>
                    )}
                  </div>
                </div>
                <div className="text-right text-xs text-gray-400">
                  <p>{sync.accounts_synced} comptes</p>
                  {sync.duration_ms != null && (
                    <p>{(sync.duration_ms / 1000).toFixed(1)}s</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="px-4 py-8 text-center text-sm text-gray-400">
            Aucune synchronisation
          </div>
        )}
      </div>
    </div>
  );
}

// ============================================================================
// REVOLUT DETAIL VIEW
// ============================================================================

function RevolutDetailView({
  revolutStatus,
  transactions,
  transactionsLoading,
  isAdmin,
  onBack,
  onSync,
  onDisconnect,
  onFetchTransactions,
  formatDate,
  formatCurrency,
  isLoading,
}: {
  revolutStatus: import("@/store/bankingStore").RevolutStatus;
  transactions: RevolutTransaction[];
  transactionsLoading: boolean;
  isAdmin: boolean;
  onBack: () => void;
  onSync: () => Promise<boolean>;
  onDisconnect: () => Promise<boolean>;
  onFetchTransactions: (params?: { from_date?: string; to_date?: string; account_id?: string; count?: number }) => Promise<void>;
  formatDate: (d?: string | null) => string;
  formatCurrency: (val: number) => string;
  isLoading: boolean;
}) {
  const [isSyncing, setIsSyncing] = useState(false);
  const [isDisconnecting, setIsDisconnecting] = useState(false);
  const [txCount, setTxCount] = useState(50);

  const handleSync = async () => {
    setIsSyncing(true);
    await onSync();
    setIsSyncing(false);
  };

  const handleDisconnect = async () => {
    if (!confirm("Déconnecter Revolut ? Tous les comptes liés seront retirés.")) return;
    setIsDisconnecting(true);
    await onDisconnect();
    setIsDisconnecting(false);
    onBack();
  };

  const handleLoadMore = () => {
    const next = txCount + 50;
    setTxCount(next);
    onFetchTransactions({ count: next });
  };

  const stateColors: Record<string, string> = {
    completed: "text-emerald-600 dark:text-emerald-400",
    pending: "text-amber-600 dark:text-amber-400",
    declined: "text-red-600 dark:text-red-400",
    failed: "text-red-600 dark:text-red-400",
    reverted: "text-gray-500",
    created: "text-blue-600 dark:text-blue-400",
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={onBack}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-[#0075EB] flex items-center justify-center">
              <span className="text-white text-lg font-bold">R</span>
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900 dark:text-white">
                Revolut Business
              </h1>
              <div className="flex items-center gap-2 mt-0.5">
                <span className="flex items-center gap-1.5 text-xs text-emerald-600 dark:text-emerald-400">
                  <span className="w-2 h-2 rounded-full bg-emerald-500" />
                  Connecté
                </span>
                <span className="text-xs text-gray-400">
                  · {revolutStatus.accounts_count} compte(s)
                </span>
              </div>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleSync}
            disabled={isSyncing}
          >
            <RefreshCw className={cn("h-3.5 w-3.5 mr-1", isSyncing && "animate-spin")} />
            Synchroniser
          </Button>
          {isAdmin && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleDisconnect}
              disabled={isDisconnecting}
              className="text-red-600 border-red-200 hover:bg-red-50 dark:text-red-400 dark:border-red-800 dark:hover:bg-red-900/20"
            >
              <Unplug className="h-3.5 w-3.5 mr-1" />
              Déconnecter
            </Button>
          )}
        </div>
      </div>

      {/* Info card */}
      <div className="rounded-xl border border-gray-200 dark:border-slate-700/50 bg-white dark:bg-slate-900 p-4">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
          <div>
            <span className="text-gray-400">Comptes</span>
            <p className="font-semibold text-gray-900 dark:text-white text-base">
              {revolutStatus.accounts_count}
            </p>
          </div>
          <div>
            <span className="text-gray-400">Connecté le</span>
            <p className="font-medium text-gray-700 dark:text-gray-300">
              {formatDate(revolutStatus.connected_at)}
            </p>
          </div>
          <div>
            <span className="text-gray-400">Dernière sync</span>
            <p className="font-medium text-gray-700 dark:text-gray-300">
              {formatDate(revolutStatus.last_sync_at)}
            </p>
          </div>
          <div>
            <span className="text-gray-400">Statut</span>
            <p className="font-medium text-emerald-600 dark:text-emerald-400 capitalize">
              {revolutStatus.status || "connected"}
            </p>
          </div>
        </div>
      </div>

      {/* Transactions */}
      <div className="rounded-xl border border-gray-200 dark:border-slate-700/50 bg-white dark:bg-slate-900 overflow-hidden">
        <div className="px-4 py-3 border-b border-gray-100 dark:border-slate-800 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-gray-900 dark:text-white flex items-center gap-2">
            <ArrowDownUp className="h-4 w-4 text-gray-400" />
            Transactions récentes
            {transactions.length > 0 && (
              <span className="ml-1 text-xs font-normal text-gray-400">
                ({transactions.length})
              </span>
            )}
          </h3>
          {transactionsLoading && (
            <Loader2 className="h-4 w-4 text-gray-400 animate-spin" />
          )}
        </div>

        {transactions.length > 0 ? (
          <>
            {/* Transactions table */}
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-xs text-gray-400 border-b border-gray-100 dark:border-slate-800">
                    <th className="px-4 py-2 font-medium">Date</th>
                    <th className="px-4 py-2 font-medium">Type</th>
                    <th className="px-4 py-2 font-medium">Description</th>
                    <th className="px-4 py-2 font-medium">Marchand</th>
                    <th className="px-4 py-2 font-medium text-right">Montant</th>
                    <th className="px-4 py-2 font-medium text-right">Statut</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50 dark:divide-slate-800/50">
                  {transactions.map((tx) => {
                    const mainLeg = tx.legs?.[0];
                    const amount = mainLeg?.amount ?? 0;
                    const currency = mainLeg?.currency ?? "EUR";
                    const isNegative = amount < 0;

                    return (
                      <tr
                        key={tx.id}
                        className="hover:bg-gray-50 dark:hover:bg-slate-800/50 transition-colors"
                      >
                        <td className="px-4 py-2.5 whitespace-nowrap text-gray-600 dark:text-gray-300 text-xs">
                          {tx.completed_at
                            ? new Date(tx.completed_at).toLocaleDateString("fr-FR", { day: "2-digit", month: "short" })
                            : tx.created_at
                              ? new Date(tx.created_at).toLocaleDateString("fr-FR", { day: "2-digit", month: "short" })
                              : "—"}
                        </td>
                        <td className="px-4 py-2.5 whitespace-nowrap">
                          <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-gray-100 dark:bg-slate-800 text-gray-600 dark:text-gray-300">
                            <CreditCard className="h-3 w-3" />
                            {tx.type}
                          </span>
                        </td>
                        <td className="px-4 py-2.5 max-w-[220px] truncate text-gray-700 dark:text-gray-300 text-xs">
                          {mainLeg?.description || tx.reference || "—"}
                        </td>
                        <td className="px-4 py-2.5 whitespace-nowrap text-xs text-gray-500">
                          {tx.merchant?.name || "—"}
                        </td>
                        <td className={cn(
                          "px-4 py-2.5 text-right whitespace-nowrap font-semibold text-xs",
                          isNegative ? "text-red-600 dark:text-red-400" : "text-emerald-600 dark:text-emerald-400",
                        )}>
                          {isNegative ? "" : "+"}{amount.toFixed(2)} {currency}
                        </td>
                        <td className="px-4 py-2.5 text-right">
                          <span className={cn("text-xs font-medium capitalize", stateColors[tx.state] || "text-gray-500")}>
                            {tx.state}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {/* Load more */}
            {transactions.length >= txCount && (
              <div className="px-4 py-3 border-t border-gray-100 dark:border-slate-800 text-center">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleLoadMore}
                  disabled={transactionsLoading}
                >
                  {transactionsLoading ? (
                    <Loader2 className="h-3.5 w-3.5 mr-1 animate-spin" />
                  ) : (
                    <ChevronRight className="h-3.5 w-3.5 mr-1" />
                  )}
                  Charger plus
                </Button>
              </div>
            )}
          </>
        ) : transactionsLoading ? (
          <div className="px-4 py-12 text-center">
            <Loader2 className="h-6 w-6 text-gray-400 animate-spin mx-auto mb-2" />
            <p className="text-sm text-gray-400">Chargement des transactions…</p>
          </div>
        ) : (
          <div className="px-4 py-12 text-center text-sm text-gray-400">
            Aucune transaction trouvée.
          </div>
        )}
      </div>
    </div>
  );
}

// ============================================================================
// PAGE EXPORT
// ============================================================================

export default function BankingPage() {
  return (
    <AppLayout>
      <BankingPageContent />
    </AppLayout>
  );
}
