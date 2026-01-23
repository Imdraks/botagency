/**
 * Subscription Store - Plans, Packs & Features
 * =============================================
 * 
 * Global state management for subscription features:
 * - Current plan and enabled packs
 * - Feature availability checking
 * - Navigation gating
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

// ============================================================================
// TYPES
// ============================================================================

export type Plan = 'mini' | 'standard' | 'premium';
export type Pack = 'core' | 'clients' | 'leads' | 'talents' | 'intelligence';
export type Addon = 'radar_business';

export type Feature =
  // Core
  | 'cockpit' | 'pipeline' | 'projects' | 'production' | 'assets' | 'calendar'
  // Clients
  | 'clients' | 'dossiers' | 'daily_picks'
  // Leads
  | 'leads' | 'kanban_leads' | 'scoring'
  // Talents
  | 'artists' | 'profiles' | 'discovery' | 'comparison' | 'map'
  // Intelligence
  | 'analytics' | 'competitor_watch' | 'ai_predictions'
  // Radar Business
  | 'crm_extended' | 'quotes' | 'invoices'
  // Admin only
  | 'sources' | 'source_health';

export interface NavItem {
  label: string;
  path: string;
  icon: string;
  available: boolean;
  locked: boolean;
  admin_only: boolean;
  upgrade_message?: string;
}

export interface NavigationSections {
  [section: string]: NavItem[];
}

export interface WorkspaceSubscription {
  workspace_id: number;
  workspace_name: string;
  plan: Plan;
  plan_display_name: string;
  enabled_packs: Pack[];
  addons: Addon[];
  max_seats: number;
  current_seats: number;
  available_features: Feature[];
  plan_expires_at?: string;
}

export interface PlanInfo {
  name: string;
  display_name: string;
  description: string;
  price_monthly: number;
  included_packs: string[];
  included_addons: string[];
  max_seats: number;
  features_bullets: string[];
  is_current: boolean;
  is_recommended: boolean;
}

export interface AddonInfo {
  name: string;
  display_name: string;
  description: string;
  price_monthly: number;
  features: string[];
  is_active: boolean;
  included_in_plan: boolean;
}

// ============================================================================
// FEATURE → ROUTE MAPPING
// ============================================================================

export const FEATURE_ROUTES: Record<string, Feature> = {
  '/cockpit': 'cockpit',
  '/today': 'cockpit',
  '/pipeline': 'pipeline',
  '/projects': 'projects',
  '/production': 'production',
  '/assets': 'assets',
  '/calendar': 'calendar',
  '/clients': 'clients',
  '/dossiers': 'dossiers',
  '/leads': 'leads',
  '/opportunities': 'leads',
  '/artists': 'artists',
  '/profiles': 'profiles',
  '/discovery': 'discovery',
  '/comparison': 'comparison',
  '/map': 'map',
  '/analytics': 'analytics',
  '/competitor-watch': 'competitor_watch',
  '/predictions': 'ai_predictions',
  '/quotes': 'quotes',
  '/invoices': 'invoices',
  '/sources': 'sources',
  '/source-health': 'source_health',
};

// Admin-only features (hidden from non-admins)
export const ADMIN_ONLY_FEATURES: Feature[] = ['sources', 'source_health'];

// ============================================================================
// PLAN CONFIGS (for UI display)
// ============================================================================

export interface PlanConfig {
  description: string;
  price: number;
  maxSeats: number;
  packs: Pack[];
  highlights: string[];
}

export const PLAN_CONFIGS: Record<Plan, PlanConfig> = {
  mini: {
    description: "L'essentiel pour piloter ton agence.",
    price: 29,
    maxSeats: 3,
    packs: ['core', 'clients'],
    highlights: [
      'Cockpit + Pipeline + Projets + Production',
      'Gestion clients et dossiers',
      'Daily Picks pour ne rien oublier',
    ],
  },
  standard: {
    description: 'Le plan que 80% des agences choisissent.',
    price: 79,
    maxSeats: 10,
    packs: ['core', 'clients', 'leads', 'talents'],
    highlights: [
      'Tout Mini inclus',
      'Leads + Kanban + Scoring',
      'Artistes, Profils, Découverte, Comparaison',
    ],
  },
  premium: {
    description: 'Radar complet. Zéro limite.',
    price: 149,
    maxSeats: 999,
    packs: ['core', 'clients', 'leads', 'talents', 'intelligence'],
    highlights: [
      'Tout Standard inclus',
      'Analytics, Veille Concur., Prédictions IA',
      'Radar Business inclus (devis + factures)',
    ],
  },
};

// ============================================================================
// STORE
// ============================================================================

interface SubscriptionState {
  // Current subscription
  subscription: WorkspaceSubscription | null;
  isLoading: boolean;
  error: string | null;
  
  // Navigation
  navigation: NavigationSections | null;
  
  // User role
  isAdmin: boolean;
  
  // Actions
  fetchSubscription: (workspaceId?: number) => Promise<void>;
  fetchNavigation: (workspaceId?: number) => Promise<void>;
  setAdmin: (isAdmin: boolean) => void;
  
  // Feature checking
  hasFeature: (feature: Feature) => boolean;
  canAccessRoute: (path: string) => boolean;
  getUpgradeMessage: (feature: Feature) => string | null;
  
  // Plan management (admin only)
  changePlan: (plan: Plan) => Promise<boolean>;
  toggleAddon: (addon: Addon, enable: boolean) => Promise<boolean>;
  
  // Reset
  reset: () => void;
}

const initialState = {
  subscription: null,
  isLoading: false,
  error: null,
  navigation: null,
  isAdmin: false,
};

export const useSubscriptionStore = create<SubscriptionState>()(
  persist(
    (set, get) => ({
      ...initialState,
      
      fetchSubscription: async (workspaceId?: number) => {
        set({ isLoading: true, error: null });
        try {
          const token = localStorage.getItem('access_token');
          if (!token) {
            set({ isLoading: false });
            return;
          }
          
          const url = workspaceId 
            ? `/api/v1/subscription/current?workspace_id=${workspaceId}`
            : '/api/v1/subscription/current';
          
          const res = await fetch(url, {
            headers: { 'Authorization': `Bearer ${token}` },
          });
          
          if (res.ok) {
            const data = await res.json();
            set({ subscription: data, isLoading: false });
          } else {
            set({ error: 'Failed to fetch subscription', isLoading: false });
          }
        } catch (err) {
          set({ error: 'Network error', isLoading: false });
        }
      },
      
      fetchNavigation: async (workspaceId?: number) => {
        try {
          const token = localStorage.getItem('access_token');
          if (!token) return;
          
          const url = workspaceId 
            ? `/api/v1/subscription/navigation?workspace_id=${workspaceId}`
            : '/api/v1/subscription/navigation';
          
          const res = await fetch(url, {
            headers: { 'Authorization': `Bearer ${token}` },
          });
          
          if (res.ok) {
            const data = await res.json();
            set({ navigation: data.sections });
          }
        } catch (err) {
          console.error('Failed to fetch navigation:', err);
        }
      },
      
      setAdmin: (isAdmin: boolean) => {
        set({ isAdmin });
      },
      
      hasFeature: (feature: Feature): boolean => {
        const { subscription, isAdmin } = get();
        
        // Admin-only features
        if (ADMIN_ONLY_FEATURES.includes(feature)) {
          return isAdmin;
        }
        
        if (!subscription) return false;
        return subscription.available_features.includes(feature);
      },
      
      canAccessRoute: (path: string): boolean => {
        const { hasFeature, isAdmin } = get();
        
        // Get feature for route
        const feature = FEATURE_ROUTES[path];
        if (!feature) return true; // Unknown routes are allowed
        
        // Admin-only routes
        if (ADMIN_ONLY_FEATURES.includes(feature)) {
          return isAdmin;
        }
        
        return hasFeature(feature);
      },
      
      getUpgradeMessage: (feature: Feature): string | null => {
        const { navigation } = get();
        if (!navigation) return null;
        
        // Find the nav item with this feature
        for (const section of Object.values(navigation)) {
          for (const item of section) {
            const itemFeature = FEATURE_ROUTES[item.path];
            if (itemFeature === feature && item.locked) {
              return item.upgrade_message || 'Passez à un plan supérieur';
            }
          }
        }
        
        return null;
      },
      
      changePlan: async (plan: Plan): Promise<boolean> => {
        try {
          const token = localStorage.getItem('access_token');
          const { subscription } = get();
          
          const url = subscription 
            ? `/api/v1/subscription/change-plan?workspace_id=${subscription.workspace_id}`
            : '/api/v1/subscription/change-plan';
          
          const res = await fetch(url, {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ plan }),
          });
          
          if (res.ok) {
            const data = await res.json();
            set({ subscription: data });
            // Refresh navigation
            get().fetchNavigation(data.workspace_id);
            return true;
          }
          return false;
        } catch (err) {
          console.error('Failed to change plan:', err);
          return false;
        }
      },
      
      toggleAddon: async (addon: Addon, enable: boolean): Promise<boolean> => {
        try {
          const token = localStorage.getItem('access_token');
          const { subscription } = get();
          
          const url = subscription 
            ? `/api/v1/subscription/toggle-addon?workspace_id=${subscription.workspace_id}`
            : '/api/v1/subscription/toggle-addon';
          
          const res = await fetch(url, {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ addon, enable }),
          });
          
          if (res.ok) {
            const data = await res.json();
            set({ subscription: data });
            // Refresh navigation
            get().fetchNavigation(data.workspace_id);
            return true;
          }
          return false;
        } catch (err) {
          console.error('Failed to toggle addon:', err);
          return false;
        }
      },
      
      reset: () => {
        set(initialState);
      },
    }),
    {
      name: 'radar-subscription',
      partialize: (state) => ({
        subscription: state.subscription,
        navigation: state.navigation,
        isAdmin: state.isAdmin,
      }),
    }
  )
);

// ============================================================================
// HOOKS
// ============================================================================

/**
 * Hook to check if a feature is available
 */
export function useFeature(feature: Feature): boolean {
  return useSubscriptionStore((state) => state.hasFeature(feature));
}

/**
 * Hook to check if a route is accessible
 */
export function useRouteAccess(path: string): { 
  canAccess: boolean; 
  isLocked: boolean;
  upgradeMessage: string | null;
} {
  const canAccess = useSubscriptionStore((state) => state.canAccessRoute(path));
  const feature = FEATURE_ROUTES[path];
  const upgradeMessage = useSubscriptionStore((state) => 
    feature ? state.getUpgradeMessage(feature) : null
  );
  
  return {
    canAccess,
    isLocked: !canAccess,
    upgradeMessage,
  };
}

/**
 * Hook to get the current plan
 */
export function usePlan(): Plan | null {
  return useSubscriptionStore((state) => state.subscription?.plan || null);
}

/**
 * Hook to check if user is admin
 */
export function useIsAdmin(): boolean {
  return useSubscriptionStore((state) => state.isAdmin);
}
