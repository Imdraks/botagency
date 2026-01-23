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
  Kanban,
  Music,
  Search,
  GitCompare,
  FileText,
  ChevronRight,
  Bell,
  Activity,
  Sparkles,
  Sliders,
  Clock,
  HeartPulse,
  TrendingUp,
  Eye,
  Map,
  Brain,
  ChevronDown,
  Briefcase,
  FolderOpen,
  Palette,
  Wrench,
  DollarSign,
  Package,
  Sun,
  Inbox,
  Lock,
} from "lucide-react";
import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useAuthStore } from "@/store/auth";
import { useSubscriptionStore, Feature, FEATURE_ROUTES } from "@/store/subscriptionStore";
import { ThemeToggle } from "@/components/ui/theme-toggle";
import { NotificationCenter } from "@/components/notifications/NotificationCenter";
import { BackgroundTasksIndicator } from "@/components/tasks/BackgroundTasksIndicator";
import { OnboardingProvider, OnboardingTour, OnboardingTrigger, WelcomeModal } from "@/components/onboarding";
import { MobileBottomNav } from "./MobileBottomNav";

// Storage key for visited pages
const VISITED_PAGES_KEY = "radar_visited_pages";

// Helper to get visited pages from localStorage
const getVisitedPages = (): string[] => {
  if (typeof window === "undefined") return [];
  try {
    const stored = localStorage.getItem(VISITED_PAGES_KEY);
    return stored ? JSON.parse(stored) : [];
  } catch {
    return [];
  }
};

// Helper to mark a page as visited
const markPageAsVisited = (href: string): void => {
  if (typeof window === "undefined") return;
  try {
    const visited = getVisitedPages();
    if (!visited.includes(href)) {
      visited.push(href);
      localStorage.setItem(VISITED_PAGES_KEY, JSON.stringify(visited));
    }
  } catch {
    // Ignore storage errors
  }
};

// ============================================================================
// NAVIGATION V3 - Daily Agency Hub
// Today & Inbox first = daily adoption
// Core: Pipeline, Projets, Production, Assets, Calendrier
// Outils: groupe replié par défaut
// Admin: visible seulement pour admins
// ============================================================================

// Common navigation item type
interface NavItem {
  name: string;
  href: string;
  icon: LucideIcon;
  isNew?: boolean;
  adminOnly?: boolean;
  superadminOnly?: boolean;
  feature?: Feature; // Feature required to access this page
}

// Main navigation - always visible at top
const mainNavigation: NavItem[] = [
  { name: "Aujourd'hui", href: "/today", icon: Sun, isNew: true, feature: 'cockpit' },
  { name: "Inbox", href: "/inbox", icon: Inbox, isNew: true, feature: 'cockpit' },
  { name: "Pipeline", href: "/pipeline", icon: DollarSign, feature: 'pipeline' },
  { name: "Projets", href: "/projects", icon: FolderOpen, feature: 'projects' },
  { name: "Production", href: "/production", icon: Palette, feature: 'production' },
  { name: "Assets", href: "/assets", icon: Package, feature: 'assets' },
  { name: "Calendrier", href: "/agency-calendar", icon: Calendar, feature: 'calendar' },
];

// Outils navigation (collapsible) - for daily workflows
const toolsNavigation: NavItem[] = [
  { name: "Cockpit", href: "/cockpit", icon: LayoutDashboard, feature: 'cockpit' },
  { name: "Clients", href: "/clients", icon: Briefcase, feature: 'clients' },
  { name: "Daily Picks", href: "/shortlist", icon: Sparkles, feature: 'daily_picks' },
  { name: "Leads", href: "/leads", icon: Target, feature: 'leads' },
  { name: "Dossiers", href: "/dossiers", icon: FileText, feature: 'dossiers' },
  { name: "Kanban Leads", href: "/leads/kanban", icon: Kanban, feature: 'kanban_leads' },
  { name: "Deadlines", href: "/deadlines", icon: Clock, feature: 'projects' },
  { name: "Analytics", href: "/analytics", icon: TrendingUp, feature: 'analytics' },
  { name: "Artistes", href: "/artist-history", icon: Music, feature: 'artists' },
  { name: "Découverte", href: "/discovery", icon: Search, feature: 'discovery' },
  { name: "Comparaison", href: "/comparison", icon: GitCompare, feature: 'comparison' },
  { name: "Carte", href: "/map", icon: Map, feature: 'map' },
  { name: "Veille Concur.", href: "/competitive", icon: Eye, feature: 'competitor_watch' },
];

// Admin Tools navigation (collapsible) - technical/admin only
const adminToolsNavigation: NavItem[] = [
  { name: "Workspaces", href: "/workspaces", icon: FolderOpen, adminOnly: true },
  { name: "Sources", href: "/sources", icon: Rss, adminOnly: true, feature: 'sources' },
  { name: "Source Health", href: "/source-health", icon: HeartPulse, adminOnly: true, feature: 'source_health' },
  { name: "Profils", href: "/profiles", icon: Sliders, adminOnly: true },
  { name: "Scoring", href: "/scoring", icon: BarChart3, adminOnly: true, feature: 'scoring' },
  { name: "Prédictions IA", href: "/predictions", icon: Brain, adminOnly: true, feature: 'ai_predictions' },
];

// Bottom navigation
const adminNavigation: NavItem[] = [
  { name: "Utilisateurs", href: "/users", icon: Users, adminOnly: true },
  { name: "Logs Activité", href: "/admin/activity", icon: Activity, superadminOnly: true },
  { name: "Paramètres", href: "/settings", icon: Settings },
];

// Combined navigation for backward compatibility
const navigation = [...mainNavigation, ...toolsNavigation, ...adminToolsNavigation, ...adminNavigation];

interface AppLayoutProps {
  children: React.ReactNode;
}

function AppLayoutInner({ children }: AppLayoutProps) {
  const pathname = usePathname();
  const { user, logout } = useAuthStore();
  const { subscription, fetchSubscription, hasFeature, setAdmin } = useSubscriptionStore();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [visitedPages, setVisitedPages] = useState<string[]>([]);
  const [toolsExpanded, setToolsExpanded] = useState(false);
  const [adminExpanded, setAdminExpanded] = useState(false);

  // Load subscription on mount
  useEffect(() => {
    const workspaceId = localStorage.getItem('current_workspace_id');
    if (workspaceId) {
      fetchSubscription(parseInt(workspaceId));
    } else {
      fetchSubscription();
    }
  }, [fetchSubscription]);

  // Update admin status
  useEffect(() => {
    if (user) {
      setAdmin(user.role === 'admin' || user.is_superuser === true);
    }
  }, [user, setAdmin]);

  // Load visited pages on mount
  useEffect(() => {
    setVisitedPages(getVisitedPages());
  }, []);

  // Mark current page as visited when pathname changes
  useEffect(() => {
    if (pathname) {
      // Find matching navigation item
      const navItem = navigation.find(
        (item) => pathname === item.href || (item.href !== "/today" && item.href !== "/cockpit" && item.href !== "/dashboard" && pathname.startsWith(item.href))
      );
      if (navItem?.isNew) {
        markPageAsVisited(navItem.href);
        setVisitedPages((prev) => 
          prev.includes(navItem.href) ? prev : [...prev, navItem.href]
        );
      }
      
      // Auto-expand tools if current page is in tools section
      const isToolPage = toolsNavigation.some(
        (item) => pathname === item.href || pathname.startsWith(item.href)
      );
      if (isToolPage) {
        setToolsExpanded(true);
      }
      
      // Auto-expand admin if current page is in admin tools section
      const isAdminToolPage = adminToolsNavigation.some(
        (item) => pathname === item.href || pathname.startsWith(item.href)
      );
      if (isAdminToolPage) {
        setAdminExpanded(true);
      }
    }
  }, [pathname]);

  // Check if a page should show "New" badge
  const shouldShowNewBadge = useCallback((item: { isNew?: boolean; href: string }) => {
    return item.isNew && !visitedPages.includes(item.href);
  }, [visitedPages]);

  // Check if a feature is available
  const isFeatureAvailable = useCallback((item: NavItem): boolean => {
    // No feature requirement = always available
    if (!item.feature) return true;
    // Use the hasFeature from subscription store
    return hasFeature(item.feature);
  }, [hasFeature]);

  const isAdmin = user?.role === "admin";
  const isSuperuser = user?.is_superuser === true;

  // Filter navigation items based on role AND feature availability
  const filterNavItems = useCallback((items: NavItem[]) => {
    return items.filter((item) => {
      // Role check
      if (item.superadminOnly && !isSuperuser) return false;
      if (item.adminOnly && !isAdmin && !isSuperuser) return false;
      // Feature check - show but locked, or hide completely? 
      // For now, show all but we'll mark locked ones
      return true;
    });
  }, [isAdmin, isSuperuser]);

  const filteredMainNavigation = filterNavItems(mainNavigation);
  
  const filteredToolsNavigation = filterNavItems(toolsNavigation);
  
  const filteredAdminToolsNavigation = filterNavItems(adminToolsNavigation);
  
  const filteredAdminNavigation = filterNavItems(adminNavigation);

  const currentPage = [...mainNavigation, ...toolsNavigation, ...adminNavigation].find(item => pathname.startsWith(item.href));

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
          <div className="flex items-center justify-between h-16 px-5 border-b border-gray-200 dark:border-slate-700/50">
            <Link href="/today" className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-purple-600 dark:bg-purple-600 flex items-center justify-center shadow-md shadow-purple-500/20 dark:shadow-purple-500/30">
                <Target className="h-5 w-5 text-white" />
              </div>
              <span className="text-xl font-bold text-gray-900 dark:text-white tracking-tight">
                Radar
              </span>
            </Link>
            <Button
              variant="ghost"
              size="icon"
              className="lg:hidden text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-800"
              onClick={() => setSidebarOpen(false)}
            >
              <X className="h-5 w-5" />
            </Button>
          </div>

          {/* Navigation */}
          <ScrollArea className="flex-1 py-4">
            <nav className="px-3 space-y-1">
              {/* Main Navigation - 7 items */}
              {filteredMainNavigation.map((item: NavItem) => {
                const isActive = pathname === item.href || 
                  (item.href !== "/today" && pathname.startsWith(item.href));
                const isLocked = item.feature && !isFeatureAvailable(item);
                return (
                  <Link
                    key={item.name}
                    href={isLocked ? "#" : item.href}
                    className={cn(
                      "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150",
                      isLocked
                        ? "text-gray-400 dark:text-gray-600 cursor-not-allowed opacity-60"
                        : isActive
                        ? "bg-purple-600 dark:bg-purple-600 text-white shadow-md shadow-purple-500/25"
                        : "text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-neutral-800 hover:text-gray-900 dark:hover:text-white"
                    )}
                    onClick={(e) => {
                      if (isLocked) {
                        e.preventDefault();
                        return;
                      }
                      setSidebarOpen(false);
                    }}
                  >
                    <item.icon className={cn(
                      "h-5 w-5 flex-shrink-0",
                      isLocked ? "text-gray-400" : isActive ? "text-white" : "text-gray-400 dark:text-gray-500"
                    )} />
                    <span className="flex-1">{item.name}</span>
                    {isLocked && (
                      <Lock className="h-4 w-4 text-gray-400" />
                    )}
                    {!isLocked && shouldShowNewBadge(item) && !isActive && (
                      <span className="px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide bg-purple-100 dark:bg-purple-900/50 text-purple-600 dark:text-purple-400 rounded-full">
                        New
                      </span>
                    )}
                  </Link>
                );
              })}
              
              {/* Divider */}
              <div className="my-3 border-t border-gray-200 dark:border-slate-700/50" />
              
              {/* Tools Section - Collapsible - Only for non-admin users */}
              {!isAdmin && (
                <>
                  <button
                    onClick={() => setToolsExpanded(!toolsExpanded)}
                    className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-gray-900 dark:hover:text-white transition-all duration-150"
                  >
                    <Wrench className="h-5 w-5 flex-shrink-0 text-gray-400 dark:text-gray-500" />
                    <span className="flex-1 text-left">Outils</span>
                    <ChevronDown className={cn(
                      "h-4 w-4 text-gray-400 transition-transform duration-200",
                      toolsExpanded ? "rotate-180" : ""
                    )} />
                  </button>
                  
                  {toolsExpanded && (
                    <div className="ml-3 space-y-1 border-l-2 border-gray-100 dark:border-slate-700/50 pl-3">
                      {filteredToolsNavigation.map((item: NavItem) => {
                        const isActive = pathname === item.href || pathname.startsWith(item.href);
                        const isLocked = item.feature && !isFeatureAvailable(item);
                        return (
                          <Link
                            key={item.name}
                            href={isLocked ? "#" : item.href}
                            className={cn(
                              "flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-150",
                              isLocked
                                ? "text-gray-400 dark:text-slate-500 cursor-not-allowed opacity-60"
                                : isActive
                                ? "bg-gray-100 dark:bg-slate-800 text-gray-900 dark:text-white"
                                : "text-gray-500 dark:text-slate-400 hover:bg-gray-50 dark:hover:bg-slate-800/50 hover:text-gray-700 dark:hover:text-slate-200"
                            )}
                            onClick={(e) => {
                              if (isLocked) {
                                e.preventDefault();
                                return;
                              }
                              setSidebarOpen(false);
                            }}
                          >
                            <item.icon className={cn(
                              "h-4 w-4 flex-shrink-0",
                              isLocked ? "text-gray-400" : isActive ? "text-gray-700 dark:text-gray-300" : "text-gray-400 dark:text-gray-500"
                            )} />
                            <span className="flex-1">{item.name}</span>
                            {isLocked && (
                              <Lock className="h-3 w-3 text-gray-400" />
                            )}
                          </Link>
                        );
                      })}
                    </div>
                  )}
                </>
              )}
              
              {/* Admin Tools Section - Collapsible (visible only for admins) */}
              {filteredAdminToolsNavigation.length > 0 && (
                <>
                  <button
                    onClick={() => setAdminExpanded(!adminExpanded)}
                    className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-gray-900 dark:hover:text-white transition-all duration-150"
                  >
                    <Settings className="h-5 w-5 flex-shrink-0 text-gray-400 dark:text-gray-500" />
                    <span className="flex-1 text-left">Admin</span>
                    <ChevronDown className={cn(
                      "h-4 w-4 text-gray-400 transition-transform duration-200",
                      adminExpanded ? "rotate-180" : ""
                    )} />
                  </button>
                  
                  {adminExpanded && (
                    <div className="ml-3 space-y-1 border-l-2 border-gray-100 dark:border-slate-700/50 pl-3">
                      {filteredAdminToolsNavigation.map((item: NavItem) => {
                        const isActive = pathname === item.href || pathname.startsWith(item.href);
                        const isLocked = item.feature && !isFeatureAvailable(item);
                        return (
                          <Link
                            key={item.name}
                            href={isLocked ? "#" : item.href}
                            className={cn(
                              "flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-150",
                              isLocked
                                ? "text-gray-400 dark:text-slate-500 cursor-not-allowed opacity-60"
                                : isActive
                                ? "bg-gray-100 dark:bg-slate-800 text-gray-900 dark:text-white"
                                : "text-gray-500 dark:text-gray-500 hover:bg-gray-50 dark:hover:bg-neutral-800/50 hover:text-gray-700 dark:hover:text-gray-300"
                            )}
                            onClick={(e) => {
                              if (isLocked) {
                                e.preventDefault();
                                return;
                              }
                              setSidebarOpen(false);
                            }}
                          >
                            <item.icon className={cn(
                              "h-4 w-4 flex-shrink-0",
                              isLocked ? "text-gray-400" : isActive ? "text-gray-700 dark:text-gray-300" : "text-gray-400 dark:text-gray-500"
                            )} />
                            <span className="flex-1">{item.name}</span>
                            {isLocked && (
                              <Lock className="h-3 w-3 text-gray-400" />
                            )}
                          </Link>
                        );
                      })}
                    </div>
                  )}
                </>
              )}
              
              {/* Divider */}
              <div className="my-3 border-t border-gray-200 dark:border-slate-700/50" />
              
              {/* Bottom Navigation - Paramètres + Admin items */}
              {filteredAdminNavigation.map((item: NavItem) => {
                const isActive = pathname === item.href || pathname.startsWith(item.href);
                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    className={cn(
                      "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150",
                      isActive
                        ? "bg-gray-100 dark:bg-slate-800 text-gray-900 dark:text-white"
                        : "text-gray-600 dark:text-slate-400 hover:bg-gray-100 dark:hover:bg-slate-800 hover:text-gray-900 dark:hover:text-white"
                    )}
                    onClick={() => setSidebarOpen(false)}
                  >
                    <item.icon className={cn(
                      "h-5 w-5 flex-shrink-0",
                      isActive ? "text-gray-700 dark:text-slate-300" : "text-gray-400 dark:text-slate-500"
                    )} />
                    <span className="flex-1">{item.name}</span>
                  </Link>
                );
              })}
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
                <p className="text-xs text-gray-500 dark:text-gray-400 capitalize">
                  {user?.role}
                </p>
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
