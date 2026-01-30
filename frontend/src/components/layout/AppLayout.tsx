"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { LucideIcon } from "lucide-react";
import {
  LayoutDashboard,
  Target,
  Settings,
  Rss,
  Users,
  BarChart3,
  LogOut,
  Menu,
  X,
  Calendar,
  Music,
  Search,
  GitCompare,
  ChevronRight,
  Activity,
  Sparkles,
  Sliders,
  HeartPulse,
  TrendingUp,
  Eye,
  Map,
  Brain,
  ChevronDown,
  Briefcase,
  FolderOpen,
  Palette,
  DollarSign,
  Package,
  Sun,
  Inbox,
  Receipt,
  FileCheck,
  Building2,
  Compass,
  Database,
  Home,
} from "lucide-react";
import { useState, useEffect, useCallback, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useAuthStore } from "@/store/auth";
import { useSubscriptionStore, Feature, Addon, Pack } from "@/store/subscriptionStore";
import { ThemeToggle } from "@/components/ui/theme-toggle";
import { NotificationCenter } from "@/components/notifications/NotificationCenter";
import { BackgroundTasksIndicator } from "@/components/tasks/BackgroundTasksIndicator";
import { OnboardingProvider, OnboardingTour, OnboardingTrigger, WelcomeModal } from "@/components/onboarding";
import { MobileBottomNav } from "./MobileBottomNav";

// ============================================================================
// NAVIGATION V4 - Structured by Packs
// ============================================================================
// - Radar Core: Always visible
// - Radar Business: If addon enabled
// - Radar Discovery: If talents pack enabled
// - Radar Analytics: If intelligence pack enabled
// - Radar Intelligence: If intelligence pack enabled
// - Radar Data: Admin only
// - Paramètres: Always visible
// ============================================================================

// Storage key for section expand state
const SECTION_EXPAND_KEY = "radar_section_expand_state";

// Helper to get section expand state from localStorage
const getSectionExpandState = (): Record<string, boolean> => {
  if (typeof window === "undefined") return {};
  try {
    const stored = localStorage.getItem(SECTION_EXPAND_KEY);
    return stored ? JSON.parse(stored) : {};
  } catch {
    return {};
  }
};

// Helper to save section expand state
const saveSectionExpandState = (state: Record<string, boolean>): void => {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(SECTION_EXPAND_KEY, JSON.stringify(state));
  } catch {
    // Ignore storage errors
  }
};

// ============================================================================
// NAVIGATION STRUCTURE BY PACKS
// ============================================================================

interface NavItem {
  name: string;
  href: string;
  icon: LucideIcon;
  isNew?: boolean;
  feature?: Feature;
}

interface NavSection {
  id: string;
  label: string;
  icon: LucideIcon;
  items: NavItem[];
  // Visibility rules
  packRequired?: Pack;        // Pack that must be enabled
  addonRequired?: Addon;      // Addon that must be enabled
  adminOnly?: boolean;        // Only visible to admins
  alwaysVisible?: boolean;    // Always visible (Core, Settings)
}

// Define all navigation sections
const navigationSections: NavSection[] = [
  // ─────────────────────────────────────────────────────────────────────────
  // RADAR CORE - Toujours visible
  // ─────────────────────────────────────────────────────────────────────────
  {
    id: "core",
    label: "Radar Core",
    icon: Home,
    alwaysVisible: true,
    items: [
      { name: "Aujourd'hui", href: "/today", icon: Sun, feature: "cockpit" },
      { name: "Inbox", href: "/inbox", icon: Inbox, feature: "cockpit" },
      { name: "Pipeline", href: "/pipeline", icon: DollarSign, feature: "pipeline" },
      { name: "Projets", href: "/projects", icon: FolderOpen, feature: "projects" },
      { name: "Production", href: "/production", icon: Palette, feature: "production" },
      { name: "Assets", href: "/assets", icon: Package, feature: "assets" },
      { name: "Calendrier", href: "/agency-calendar", icon: Calendar, feature: "calendar" },
      { name: "Clients", href: "/clients", icon: Briefcase, feature: "clients" },
    ],
  },

  // ─────────────────────────────────────────────────────────────────────────
  // RADAR BUSINESS - Si addon activé (Devis & Factures)
  // ─────────────────────────────────────────────────────────────────────────
  {
    id: "business",
    label: "Radar Business",
    icon: Briefcase,
    addonRequired: "radar_business",
    items: [
      { name: "Devis", href: "/devis", icon: Receipt, feature: "quotes" },
      { name: "Factures", href: "/factures", icon: FileCheck, feature: "invoices" },
    ],
  },

  // ─────────────────────────────────────────────────────────────────────────
  // RADAR DISCOVERY - Si pack talents activé (découverte artistes)
  // ─────────────────────────────────────────────────────────────────────────
  {
    id: "discovery",
    label: "Radar Discovery",
    icon: Compass,
    packRequired: "talents",
    items: [
      { name: "Découverte", href: "/discovery", icon: Search, feature: "discovery" },
      { name: "Artistes", href: "/artist", icon: Music, feature: "artists" },
      { name: "Comparaison", href: "/comparison", icon: GitCompare, feature: "comparison" },
    ],
  },

  // ─────────────────────────────────────────────────────────────────────────
  // RADAR ANALYTICS - Si pack intelligence activé
  // ─────────────────────────────────────────────────────────────────────────
  {
    id: "analytics",
    label: "Radar Analytics",
    icon: BarChart3,
    packRequired: "intelligence",
    items: [
      { name: "Cockpit", href: "/cockpit", icon: LayoutDashboard, feature: "cockpit" },
      { name: "Analytics", href: "/analytics", icon: TrendingUp, feature: "analytics" },
      { name: "Carte", href: "/map", icon: Map, feature: "map" },
      { name: "Veille Concur.", href: "/competitive", icon: Eye, feature: "competitor_watch" },
    ],
  },

  // ─────────────────────────────────────────────────────────────────────────
  // RADAR INTELLIGENCE - Si pack intelligence activé
  // ─────────────────────────────────────────────────────────────────────────
  {
    id: "intelligence",
    label: "Radar Intelligence",
    icon: Sparkles,
    packRequired: "intelligence",
    items: [
      { name: "Daily Picks", href: "/shortlist", icon: Sparkles, feature: "daily_picks" },
      { name: "Scoring", href: "/scoring", icon: BarChart3, feature: "scoring" },
      { name: "Profils", href: "/profiles", icon: Sliders, feature: "profiles" },
      { name: "Prédictions IA", href: "/predictions", icon: Brain, feature: "ai_predictions" },
    ],
  },

  // ─────────────────────────────────────────────────────────────────────────
  // RADAR DATA - Admin only
  // ─────────────────────────────────────────────────────────────────────────
  {
    id: "data",
    label: "Radar Data",
    icon: Database,
    adminOnly: true,
    items: [
      { name: "Sources", href: "/sources", icon: Rss, feature: "sources" },
      { name: "Source Health", href: "/source-health", icon: HeartPulse, feature: "source_health" },
    ],
  },

  // ─────────────────────────────────────────────────────────────────────────
  // PARAMÈTRES - Toujours visible
  // ─────────────────────────────────────────────────────────────────────────
  {
    id: "settings",
    label: "Paramètres",
    icon: Settings,
    alwaysVisible: true,
    items: [
      { name: "Paramètres", href: "/settings", icon: Settings },
    ],
  },
];

// Admin-only navigation items (separate from sections)
const adminNavItems: NavItem[] = [
  { name: "Workspace", href: "/workspaces", icon: Building2 },
  { name: "Utilisateurs", href: "/users", icon: Users },
];

const superadminNavItems: NavItem[] = [
  { name: "Logs Activité", href: "/admin/activity", icon: Activity },
];

interface AppLayoutProps {
  children: React.ReactNode;
}

function AppLayoutInner({ children }: AppLayoutProps) {
  const pathname = usePathname();
  const { user, logout } = useAuthStore();
  const { subscription, fetchSubscription, setAdmin } = useSubscriptionStore();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    core: true, // Core always expanded by default
  });

  // Load subscription on mount
  useEffect(() => {
    const workspaceId = localStorage.getItem("current_workspace_id");
    if (workspaceId) {
      fetchSubscription(parseInt(workspaceId));
    } else {
      fetchSubscription();
    }
  }, [fetchSubscription]);

  // Update admin status
  useEffect(() => {
    if (user) {
      setAdmin(user.role === "admin" || user.is_superuser === true);
    }
  }, [user, setAdmin]);

  // Load expanded sections from localStorage
  useEffect(() => {
    const saved = getSectionExpandState();
    if (Object.keys(saved).length > 0) {
      setExpandedSections((prev) => ({ ...prev, ...saved }));
    }
  }, []);

  // Auto-expand section containing current page
  useEffect(() => {
    if (pathname) {
      for (const section of navigationSections) {
        const isInSection = section.items.some(
          (item) => pathname === item.href || pathname.startsWith(item.href + "/")
        );
        if (isInSection && !expandedSections[section.id]) {
          setExpandedSections((prev) => {
            const newState = { ...prev, [section.id]: true };
            saveSectionExpandState(newState);
            return newState;
          });
        }
      }
    }
  }, [pathname, expandedSections]);

  const isAdmin = user?.role === "admin";
  const isSuperuser = user?.is_superuser === true;

  // Toggle section expanded state
  const toggleSection = useCallback((sectionId: string) => {
    setExpandedSections((prev) => {
      const newState = { ...prev, [sectionId]: !prev[sectionId] };
      saveSectionExpandState(newState);
      return newState;
    });
  }, []);

  // Check if a section should be visible
  const isSectionVisible = useCallback(
    (section: NavSection): boolean => {
      // Always visible sections
      if (section.alwaysVisible) return true;

      // Admin-only sections
      if (section.adminOnly && !isAdmin && !isSuperuser) return false;

      // Check addon requirement
      if (section.addonRequired) {
        const addons = subscription?.addons || [];
        if (!addons.includes(section.addonRequired)) return false;
      }

      // Check pack requirement
      if (section.packRequired) {
        const packs = subscription?.enabled_packs || [];
        if (!packs.includes(section.packRequired)) return false;
      }

      return true;
    },
    [subscription, isAdmin, isSuperuser]
  );

  // Get visible sections
  const visibleSections = useMemo(() => {
    return navigationSections.filter(isSectionVisible);
  }, [isSectionVisible]);

  // Find current page for breadcrumb
  const currentPage = useMemo(() => {
    for (const section of navigationSections) {
      const item = section.items.find(
        (item) => pathname === item.href || pathname.startsWith(item.href + "/")
      );
      if (item) return item;
    }
    // Check admin items
    const adminItem = [...adminNavItems, ...superadminNavItems].find(
      (item) => pathname === item.href || pathname.startsWith(item.href + "/")
    );
    return adminItem || null;
  }, [pathname]);

  return (
    <div className="flex h-screen overflow-hidden bg-gray-50 dark:bg-slate-900">
      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/40 dark:bg-black/60 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        data-onboarding="sidebar"
        className={cn(
          "fixed inset-y-0 left-0 z-50 w-64 transform transition-transform duration-200 ease-in-out lg:translate-x-0 lg:static lg:z-auto",
          "bg-white dark:bg-slate-900 border-r border-gray-200 dark:border-slate-700/50 shadow-sm",
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="flex items-center justify-between h-14 px-4 border-b border-gray-200 dark:border-slate-700/50">
            <Link href="/today" className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-purple-600 dark:bg-purple-600 flex items-center justify-center shadow-sm shadow-purple-500/20 dark:shadow-purple-500/30">
                <Target className="h-4 w-4 text-white" />
              </div>
              <span className="text-lg font-bold text-gray-900 dark:text-white tracking-tight">
                Radar
              </span>
            </Link>
            <Button
              variant="ghost"
              size="icon"
              className="lg:hidden text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-800 h-8 w-8"
              onClick={() => setSidebarOpen(false)}
            >
              <X className="h-4 w-4" />
            </Button>
          </div>

          {/* Navigation */}
          <ScrollArea className="flex-1 py-3">
            <nav className="px-3 space-y-1">
              {visibleSections.map((section) => {
                const isExpanded = expandedSections[section.id] ?? false;
                const SectionIcon = section.icon;

                // Single item sections (like Paramètres) - no collapsible
                if (section.items.length === 1 && section.id === "settings") {
                  const item = section.items[0];
                  const isActive = pathname === item.href || pathname.startsWith(item.href + "/");
                  return (
                    <div key={section.id}>
                      <div className="my-2 border-t border-gray-200 dark:border-slate-700/50" />
                      <Link
                        href={item.href}
                        className={cn(
                          "flex items-center gap-2.5 px-3 py-2 rounded-lg text-[13px] font-medium transition-all duration-150",
                          isActive
                            ? "bg-purple-600 dark:bg-purple-600 text-white shadow-md shadow-purple-500/25"
                            : "text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-neutral-800 hover:text-gray-900 dark:hover:text-white"
                        )}
                        onClick={() => setSidebarOpen(false)}
                      >
                        <item.icon
                          className={cn(
                            "h-4 w-4 flex-shrink-0",
                            isActive ? "text-white" : "text-gray-400 dark:text-gray-500"
                          )}
                        />
                        <span className="flex-1">{item.name}</span>
                      </Link>
                    </div>
                  );
                }

                return (
                  <div key={section.id} className="space-y-0.5">
                    {/* Section divider for non-Core sections */}
                    {section.id !== "core" && (
                      <div className="mt-3 mb-1.5 pt-2 border-t border-gray-100 dark:border-slate-800" />
                    )}

                    {/* Section header - collapsible */}
                    <button
                      onClick={() => toggleSection(section.id)}
                      className="w-full flex items-center gap-1.5 px-3 py-1 text-[10px] font-semibold uppercase tracking-wider text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-400 transition-colors"
                    >
                      <SectionIcon className="h-3 w-3" />
                      <span className="flex-1 text-left">{section.label}</span>
                      <ChevronDown
                        className={cn(
                          "h-3 w-3 transition-transform duration-200",
                          isExpanded ? "rotate-180" : ""
                        )}
                      />
                    </button>

                    {/* Section items */}
                    <AnimatePresence initial={false}>
                      {isExpanded && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: "auto", opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          transition={{ duration: 0.15, ease: "easeInOut" }}
                          className="overflow-hidden"
                        >
                          <div className="space-y-0.5 pb-1">
                            {section.items.map((item) => {
                              const isActive =
                                pathname === item.href || pathname.startsWith(item.href + "/");
                              return (
                                <Link
                                  key={item.href}
                                  href={item.href}
                                  className={cn(
                                    "flex items-center gap-2.5 px-3 py-1.5 rounded-lg text-[13px] font-medium transition-all duration-150",
                                    isActive
                                      ? "bg-purple-600 dark:bg-purple-600 text-white shadow-sm shadow-purple-500/20"
                                      : "text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-neutral-800 hover:text-gray-900 dark:hover:text-white"
                                  )}
                                  onClick={() => setSidebarOpen(false)}
                                >
                                  <item.icon
                                    className={cn(
                                      "h-4 w-4 flex-shrink-0",
                                      isActive ? "text-white" : "text-gray-400 dark:text-gray-500"
                                    )}
                                  />
                                  <span className="flex-1">{item.name}</span>
                                  {item.isNew && !isActive && (
                                    <span className="px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wide bg-purple-100 dark:bg-purple-900/50 text-purple-600 dark:text-purple-400 rounded-full">
                                      New
                                    </span>
                                  )}
                                </Link>
                              );
                            })}
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                );
              })}

              {/* Admin Navigation Items */}
              {(isAdmin || isSuperuser) && (
                <>
                  <div className="my-2 pt-2 border-t border-gray-200 dark:border-slate-700/50" />
                  <div className="px-3 py-1 text-[10px] font-semibold uppercase tracking-wider text-gray-400 dark:text-gray-500">
                    Administration
                  </div>
                  {adminNavItems.map((item) => {
                    const isActive = pathname === item.href || pathname.startsWith(item.href + "/");
                    return (
                      <Link
                        key={item.href}
                        href={item.href}
                        className={cn(
                          "flex items-center gap-2.5 px-3 py-1.5 rounded-lg text-[13px] font-medium transition-all duration-150",
                          isActive
                            ? "bg-gray-100 dark:bg-slate-800 text-gray-900 dark:text-white"
                            : "text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-neutral-800 hover:text-gray-900 dark:hover:text-white"
                        )}
                        onClick={() => setSidebarOpen(false)}
                      >
                        <item.icon
                          className={cn(
                            "h-3.5 w-3.5 flex-shrink-0",
                            isActive ? "text-gray-700 dark:text-gray-300" : "text-gray-400 dark:text-gray-500"
                          )}
                        />
                        <span className="flex-1">{item.name}</span>
                      </Link>
                    );
                  })}
                  {isSuperuser &&
                    superadminNavItems.map((item) => {
                      const isActive = pathname === item.href || pathname.startsWith(item.href + "/");
                      return (
                        <Link
                          key={item.href}
                          href={item.href}
                          className={cn(
                            "flex items-center gap-2.5 px-3 py-1.5 rounded-lg text-[13px] font-medium transition-all duration-150",
                            isActive
                              ? "bg-gray-100 dark:bg-slate-800 text-gray-900 dark:text-white"
                              : "text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-neutral-800 hover:text-gray-900 dark:hover:text-white"
                          )}
                          onClick={() => setSidebarOpen(false)}
                        >
                          <item.icon
                            className={cn(
                              "h-3.5 w-3.5 flex-shrink-0",
                              isActive ? "text-gray-700 dark:text-gray-300" : "text-gray-400 dark:text-gray-500"
                            )}
                          />
                          <span className="flex-1">{item.name}</span>
                        </Link>
                      );
                    })}
                </>
              )}
            </nav>
          </ScrollArea>

          {/* User info & Logout */}
          <div className="border-t border-gray-200 dark:border-slate-700/50 p-4" data-onboarding="user-menu">
            <div className="relative flex items-center gap-3 p-3 rounded-xl bg-gray-50 dark:bg-slate-800 mb-3">
              {/* Help button - top right */}
              <div className="absolute -top-2 -right-2">
                <OnboardingTrigger variant="icon" />
              </div>
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-[#0000FF] to-blue-400 dark:from-blue-600 dark:to-blue-500 flex items-center justify-center text-white text-sm font-bold shadow-md">
                {user?.full_name?.charAt(0) || user?.email?.charAt(0) || "U"}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-gray-900 dark:text-white truncate">
                  {user?.full_name || user?.email}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400 capitalize">{user?.role}</p>
              </div>
            </div>
            <Button
              variant="outline"
              size="sm"
              className="w-full h-9 text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-800 border-gray-200 dark:border-gray-700"
              onClick={logout}
            >
              <LogOut className="h-4 w-4 mr-2" />
              Déconnexion
            </Button>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top bar - Desktop */}
        <header className="hidden lg:flex h-16 border-b border-gray-200 dark:border-slate-700/50 bg-white dark:bg-slate-900 items-center justify-between px-6 shadow-sm">
          <div className="flex items-center gap-4">
            {/* Breadcrumb */}
            <div className="flex items-center gap-2 text-sm">
              <span className="text-gray-400 dark:text-gray-500">Radar</span>
              <ChevronRight className="h-4 w-4 text-gray-300 dark:text-gray-600" />
              <span className="text-gray-900 dark:text-white font-semibold">
                {currentPage?.name || "Dashboard"}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <BackgroundTasksIndicator />
            <NotificationCenter />
            <ThemeToggle />
          </div>
        </header>

        {/* Top bar - Mobile (compact) */}
        <header className="lg:hidden h-14 border-b border-gray-200 dark:border-slate-700/50 bg-white/95 dark:bg-slate-900/95 backdrop-blur-lg flex items-center justify-between px-4 sticky top-0 z-40">
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setSidebarOpen(true)}
              className="text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-neutral-800 -ml-2"
            >
              <Menu className="h-5 w-5" />
            </Button>

            <div className="flex items-center gap-2">
              <div className="h-7 w-7 bg-gradient-to-r from-purple-600 to-pink-500 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-xs">R</span>
              </div>
              <span className="text-gray-900 dark:text-white font-bold">
                {currentPage?.name || "Radar"}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-1">
            <NotificationCenter />
            <ThemeToggle />
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto bg-gray-50 dark:bg-slate-950 p-4 sm:p-6 pb-24 lg:pb-6 scroll-touch overscroll-contain">
          <AnimatePresence mode="wait">
            <motion.div
              key={pathname}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.2, ease: "easeInOut" }}
            >
              {children}
            </motion.div>
          </AnimatePresence>
        </main>
      </div>

      {/* Mobile Bottom Navigation */}
      <MobileBottomNav />

      {/* Onboarding Tour */}
      <OnboardingTour />
      <WelcomeModal />
    </div>
  );
}

// Main export - always includes OnboardingProvider
export function AppLayout({ children }: AppLayoutProps) {
  return (
    <OnboardingProvider>
      <AppLayoutInner>{children}</AppLayoutInner>
    </OnboardingProvider>
  );
}

// Alias for backwards compatibility
export function AppLayoutWithOnboarding({ children }: AppLayoutProps) {
  return <AppLayout>{children}</AppLayout>;
}

export default AppLayout;
