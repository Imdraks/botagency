/**
 * Banking Store - State management for Connexions Bancaires
 * ==========================================================
 */

import { create } from 'zustand';
import api from '@/lib/api';

// ============================================================================
// TYPES
// ============================================================================

export type BankConnectionStatus =
  | 'NOT_CONNECTED'
  | 'CONNECTING'
  | 'CONNECTED'
  | 'SYNC_ERROR'
  | 'CONSENT_EXPIRED'
  | 'ACTION_REQUIRED'
  | 'SUSPENDED'
  | 'REVOKED';

export type BankAccountType =
  | 'CHECKING'
  | 'SAVINGS'
  | 'BUSINESS'
  | 'JOINT'
  | 'CREDIT_CARD'
  | 'LOAN'
  | 'OTHER';

export type SyncStatus = 'RUNNING' | 'SUCCESS' | 'PARTIAL' | 'FAILED' | 'CANCELLED';
export type SyncTrigger = 'MANUAL' | 'SCHEDULED' | 'WEBHOOK' | 'RECONNECT';

export interface BankConnection {
  id: number;
  workspace_id: number;
  bank_name: string;
  bank_code?: string | null;
  bank_logo_url?: string | null;
  bank_country: string;
  provider?: string | null;
  status: BankConnectionStatus;
  status_message?: string | null;
  connected_at?: string | null;
  last_sync_at?: string | null;
  next_sync_at?: string | null;
  consent_expires_at?: string | null;
  auto_sync_enabled: boolean;
  sync_frequency_hours: number;
  connected_by_id?: number | null;
  accounts_count: number;
  total_balance?: number | null;
  created_at: string;
  updated_at: string;
}

export interface BankAccount {
  id: number;
  connection_id: number;
  workspace_id: number;
  account_name: string;
  account_number_masked?: string | null;
  iban_masked?: string | null;
  account_type: BankAccountType;
  currency: string;
  balance?: number | null;
  available_balance?: number | null;
  balance_updated_at?: string | null;
  is_active: boolean;
  is_visible: boolean;
  display_color?: string | null;
  display_order: number;
  created_at: string;
  updated_at: string;
}

export interface BankConsent {
  id: number;
  connection_id: number;
  consent_type: 'AISP' | 'PISP';
  status: 'PENDING' | 'ACTIVE' | 'EXPIRED' | 'REVOKED' | 'REJECTED';
  granted_at?: string | null;
  expires_at?: string | null;
  days_until_expiry?: number | null;
  created_at: string;
}

export interface BankSyncLog {
  id: number;
  connection_id: number;
  status: SyncStatus;
  trigger: SyncTrigger;
  started_at: string;
  completed_at?: string | null;
  duration_ms?: number | null;
  accounts_synced: number;
  transactions_fetched: number;
  error_code?: string | null;
  error_message?: string | null;
  triggered_by_id?: number | null;
  created_at: string;
}

export interface BankConnectionDetail extends BankConnection {
  accounts: BankAccount[];
  recent_syncs: BankSyncLog[];
  active_consent?: BankConsent | null;
}

export interface BankingDashboard {
  banking_enabled: boolean;
  total_connections: number;
  active_connections: number;
  total_accounts: number;
  connections: BankConnection[];
  total_balances: Record<string, number>;
  status_summary: Record<string, number>;
  expiring_consents: number;
  last_sync_at?: string | null;
}

// ============================================================================
// REVOLUT TYPES
// ============================================================================

export interface RevolutStatus {
  connected: boolean;
  connection_id?: number | null;
  status?: string | null;
  status_message?: string | null;
  accounts_count: number;
  last_sync_at?: string | null;
  connected_at?: string | null;
}

export interface RevolutTransactionLeg {
  leg_id?: string | null;
  account_id?: string | null;
  amount?: number | null;
  currency?: string | null;
  description?: string | null;
  balance?: number | null;
  bill_amount?: number | null;
  bill_currency?: string | null;
}

export interface RevolutMerchant {
  name?: string | null;
  city?: string | null;
  country?: string | null;
  category_code?: string | null;
}

export interface RevolutTransaction {
  id: string;
  type: string;
  state: string;
  request_id?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
  completed_at?: string | null;
  reference?: string | null;
  legs: RevolutTransactionLeg[];
  merchant?: RevolutMerchant | null;
}

export interface RevolutTransactionsResponse {
  transactions: RevolutTransaction[];
  total: number;
  account_id?: string | null;
  from_date?: string | null;
  to_date?: string | null;
}

// ============================================================================
// STORE
// ============================================================================

interface BankingState {
  // Data
  dashboard: BankingDashboard | null;
  connections: BankConnection[];
  selectedConnection: BankConnectionDetail | null;
  accounts: BankAccount[];
  
  // Revolut
  revolutStatus: RevolutStatus | null;
  revolutTransactions: RevolutTransaction[];
  revolutTransactionsLoading: boolean;
  
  // UI state
  isLoading: boolean;
  error: string | null;
  isSyncing: Record<number, boolean>; // connection_id → syncing

  // Actions
  fetchDashboard: () => Promise<void>;
  fetchConnections: () => Promise<void>;
  fetchConnectionDetail: (connectionId: number) => Promise<void>;
  fetchAccounts: (connectionId?: number) => Promise<void>;
  
  createConnection: (data: {
    bank_name: string;
    bank_code?: string;
    bank_logo_url?: string;
    bank_country?: string;
    provider?: string;
  }) => Promise<BankConnection | null>;
  
  updateConnection: (connectionId: number, data: {
    auto_sync_enabled?: boolean;
    sync_frequency_hours?: number;
  }) => Promise<boolean>;
  
  deleteConnection: (connectionId: number) => Promise<boolean>;
  suspendConnection: (connectionId: number) => Promise<boolean>;
  resumeConnection: (connectionId: number) => Promise<boolean>;
  
  triggerSync: (connectionId: number) => Promise<boolean>;
  
  updateAccount: (accountId: number, data: {
    account_name?: string;
    is_visible?: boolean;
    display_color?: string;
    display_order?: number;
  }) => Promise<boolean>;
  
  // Revolut Actions
  fetchRevolutStatus: () => Promise<void>;
  connectRevolut: () => Promise<string | null>; // returns consent_url
  completeRevolutOAuth: (code: string) => Promise<boolean>;
  syncRevolut: () => Promise<boolean>;
  fetchRevolutTransactions: (params?: {
    from_date?: string;
    to_date?: string;
    account_id?: string;
    count?: number;
  }) => Promise<void>;
  disconnectRevolut: () => Promise<boolean>;
  
  reset: () => void;
}

const initialState = {
  dashboard: null,
  connections: [],
  selectedConnection: null,
  accounts: [],
  revolutStatus: null,
  revolutTransactions: [],
  revolutTransactionsLoading: false,
  isLoading: false,
  error: null,
  isSyncing: {},
};

export const useBankingStore = create<BankingState>()((set, get) => ({
  ...initialState,

  fetchDashboard: async () => {
    set({ isLoading: true, error: null });
    try {
      const { data } = await api.get('/banking/dashboard');
      set({ dashboard: data, connections: data.connections, isLoading: false });
    } catch (err: any) {
      set({
        error: err?.response?.data?.detail || 'Erreur lors du chargement',
        isLoading: false,
      });
    }
  },

  fetchConnections: async () => {
    set({ isLoading: true, error: null });
    try {
      const { data } = await api.get('/banking/connections');
      set({ connections: data.connections, isLoading: false });
    } catch (err: any) {
      set({
        error: err?.response?.data?.detail || 'Erreur lors du chargement',
        isLoading: false,
      });
    }
  },

  fetchConnectionDetail: async (connectionId: number) => {
    set({ isLoading: true, error: null });
    try {
      const { data } = await api.get(`/banking/connections/${connectionId}`);
      set({ selectedConnection: data, isLoading: false });
    } catch (err: any) {
      set({
        error: err?.response?.data?.detail || 'Erreur lors du chargement',
        isLoading: false,
      });
    }
  },

  fetchAccounts: async (connectionId?: number) => {
    try {
      const params = connectionId ? { connection_id: connectionId } : {};
      const { data } = await api.get('/banking/accounts', { params });
      set({ accounts: data.accounts });
    } catch (err: any) {
      console.error('Failed to fetch accounts:', err);
    }
  },

  createConnection: async (connData) => {
    set({ isLoading: true, error: null });
    try {
      const { data } = await api.post('/banking/connections', connData);
      // Refresh list
      get().fetchConnections();
      set({ isLoading: false });
      return data;
    } catch (err: any) {
      set({
        error: err?.response?.data?.detail || 'Erreur lors de la création',
        isLoading: false,
      });
      return null;
    }
  },

  updateConnection: async (connectionId, updateData) => {
    try {
      await api.patch(`/banking/connections/${connectionId}`, updateData);
      get().fetchConnections();
      return true;
    } catch (err: any) {
      set({ error: err?.response?.data?.detail || 'Erreur lors de la mise à jour' });
      return false;
    }
  },

  deleteConnection: async (connectionId) => {
    try {
      await api.delete(`/banking/connections/${connectionId}`);
      set((state) => ({
        connections: state.connections.filter((c) => c.id !== connectionId),
        selectedConnection:
          state.selectedConnection?.id === connectionId ? null : state.selectedConnection,
      }));
      return true;
    } catch (err: any) {
      set({ error: err?.response?.data?.detail || 'Erreur lors de la suppression' });
      return false;
    }
  },

  suspendConnection: async (connectionId) => {
    try {
      await api.post(`/banking/connections/${connectionId}/suspend`);
      get().fetchConnections();
      return true;
    } catch (err: any) {
      set({ error: err?.response?.data?.detail || 'Erreur' });
      return false;
    }
  },

  resumeConnection: async (connectionId) => {
    try {
      await api.post(`/banking/connections/${connectionId}/resume`);
      get().fetchConnections();
      return true;
    } catch (err: any) {
      set({ error: err?.response?.data?.detail || 'Erreur' });
      return false;
    }
  },

  triggerSync: async (connectionId) => {
    set((state) => ({
      isSyncing: { ...state.isSyncing, [connectionId]: true },
    }));
    try {
      await api.post(`/banking/connections/${connectionId}/sync`);
      // Refresh after a short delay to see updated status
      setTimeout(() => {
        get().fetchConnections();
        set((state) => ({
          isSyncing: { ...state.isSyncing, [connectionId]: false },
        }));
      }, 2000);
      return true;
    } catch (err: any) {
      set((state) => ({
        error: err?.response?.data?.detail || 'Erreur de synchronisation',
        isSyncing: { ...state.isSyncing, [connectionId]: false },
      }));
      return false;
    }
  },

  updateAccount: async (accountId, updateData) => {
    try {
      await api.patch(`/banking/accounts/${accountId}`, updateData);
      get().fetchAccounts();
      return true;
    } catch (err: any) {
      set({ error: err?.response?.data?.detail || 'Erreur' });
      return false;
    }
  },

  // ========================================================================
  // REVOLUT ACTIONS
  // ========================================================================

  fetchRevolutStatus: async () => {
    try {
      const { data } = await api.get('/banking/revolut/status');
      set({ revolutStatus: data });
    } catch (err: any) {
      console.error('Failed to fetch Revolut status:', err);
    }
  },

  connectRevolut: async () => {
    set({ isLoading: true, error: null });
    try {
      const { data } = await api.post('/banking/revolut/connect');
      set({ isLoading: false });
      return data.consent_url as string;
    } catch (err: any) {
      set({
        error: err?.response?.data?.detail || 'Erreur lors de la connexion Revolut',
        isLoading: false,
      });
      return null;
    }
  },

  completeRevolutOAuth: async (code: string) => {
    set({ isLoading: true, error: null });
    try {
      const { data } = await api.post('/banking/revolut/callback', { code });
      set({ isLoading: false });
      // Refresh everything
      get().fetchDashboard();
      get().fetchRevolutStatus();
      return true;
    } catch (err: any) {
      set({
        error: err?.response?.data?.detail || 'Erreur OAuth Revolut',
        isLoading: false,
      });
      return false;
    }
  },

  syncRevolut: async () => {
    set({ isLoading: true, error: null });
    try {
      await api.post('/banking/revolut/sync');
      set({ isLoading: false });
      // Refresh data
      get().fetchDashboard();
      get().fetchRevolutStatus();
      return true;
    } catch (err: any) {
      set({
        error: err?.response?.data?.detail || 'Erreur de synchronisation Revolut',
        isLoading: false,
      });
      return false;
    }
  },

  fetchRevolutTransactions: async (params) => {
    set({ revolutTransactionsLoading: true });
    try {
      const { data } = await api.get('/banking/revolut/transactions', { params });
      set({
        revolutTransactions: data.transactions || [],
        revolutTransactionsLoading: false,
      });
    } catch (err: any) {
      console.error('Failed to fetch Revolut transactions:', err);
      set({ revolutTransactionsLoading: false });
    }
  },

  disconnectRevolut: async () => {
    set({ isLoading: true, error: null });
    try {
      await api.delete('/banking/revolut/disconnect');
      set({
        revolutStatus: { connected: false, accounts_count: 0 },
        revolutTransactions: [],
        isLoading: false,
      });
      get().fetchDashboard();
      return true;
    } catch (err: any) {
      set({
        error: err?.response?.data?.detail || 'Erreur de déconnexion',
        isLoading: false,
      });
      return false;
    }
  },

  reset: () => set(initialState),
}));
