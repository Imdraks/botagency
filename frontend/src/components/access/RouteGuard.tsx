"use client";

import { useEffect, useState } from "react";
import { useSubscriptionStore, Feature, Addon } from "@/store/subscriptionStore";
import { useAuthStore } from "@/store/auth";
import ModuleNotActivated from "./ModuleNotActivated";

// Mapping from route to module info
const MODULE_INFO: Record<string, { name: string; pack?: string; addon?: Addon; adminOnly?: boolean }> = {
  // Radar Business (addon)
  "/clients": { name: "Radar Business", addon: "radar_business" },
  "/devis": { name: "Radar Business", addon: "radar_business" },
  "/factures": { name: "Radar Business", addon: "radar_business" },
  
  // Radar Discovery (talents pack)
  "/discovery": { name: "Radar Discovery", pack: "talents" },
  "/artist-history": { name: "Radar Discovery", pack: "talents" },
  "/comparison": { name: "Radar Discovery", pack: "talents" },
  
  // Radar Analytics (intelligence pack)
  "/cockpit": { name: "Radar Analytics", pack: "intelligence" },
  "/analytics": { name: "Radar Analytics", pack: "intelligence" },
  "/map": { name: "Radar Analytics", pack: "intelligence" },
  "/competitive": { name: "Radar Analytics", pack: "intelligence" },
  
  // Radar Intelligence (intelligence pack)
  "/shortlist": { name: "Radar Intelligence", pack: "intelligence" },
  "/scoring": { name: "Radar Intelligence", pack: "intelligence" },
  "/profiles": { name: "Radar Intelligence", pack: "intelligence" },
  "/predictions": { name: "Radar Intelligence", pack: "intelligence" },
  
  // Radar Data (admin only)
  "/sources": { name: "Radar Data", adminOnly: true },
  "/source-health": { name: "Radar Data", adminOnly: true },
};

interface RouteGuardProps {
  children: React.ReactNode;
  pathname: string;
}

export function RouteGuard({ children, pathname }: RouteGuardProps) {
  const { subscription } = useSubscriptionStore();
  const { user } = useAuthStore();
  const [isAllowed, setIsAllowed] = useState<boolean | null>(null);
  const [moduleName, setModuleName] = useState<string>("");

  useEffect(() => {
    // Find matching module info
    const moduleKey = Object.keys(MODULE_INFO).find(
      (key) => pathname === key || pathname.startsWith(key + "/")
    );

    if (!moduleKey) {
      // No restriction for this route
      setIsAllowed(true);
      return;
    }

    const moduleInfo = MODULE_INFO[moduleKey];
    setModuleName(moduleInfo.name);

    const isAdmin = user?.role === "admin" || user?.is_superuser === true;

    // Check admin-only
    if (moduleInfo.adminOnly && !isAdmin) {
      setIsAllowed(false);
      return;
    }

    // Check addon requirement
    if (moduleInfo.addon) {
      const addons = subscription?.addons || [];
      if (!addons.includes(moduleInfo.addon)) {
        setIsAllowed(false);
        return;
      }
    }

    // Check pack requirement
    if (moduleInfo.pack) {
      const packs = subscription?.enabled_packs || [];
      if (!packs.includes(moduleInfo.pack)) {
        setIsAllowed(false);
        return;
      }
    }

    setIsAllowed(true);
  }, [pathname, subscription, user]);

  // Loading state
  if (isAllowed === null) {
    return (
      <div className="min-h-[50vh] flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600" />
      </div>
    );
  }

  // Access denied
  if (!isAllowed) {
    return <ModuleNotActivated moduleName={moduleName} />;
  }

  // Access granted
  return <>{children}</>;
}

/**
 * Hook to check if a specific module is accessible
 */
export function useModuleAccess(moduleKey: keyof typeof MODULE_INFO) {
  const { subscription } = useSubscriptionStore();
  const { user } = useAuthStore();

  const moduleInfo = MODULE_INFO[moduleKey];
  if (!moduleInfo) return { isAllowed: true, moduleName: "" };

  const isAdmin = user?.role === "admin" || user?.is_superuser === true;

  // Check admin-only
  if (moduleInfo.adminOnly && !isAdmin) {
    return { isAllowed: false, moduleName: moduleInfo.name };
  }

  // Check addon requirement
  if (moduleInfo.addon) {
    const addons = subscription?.addons || [];
    if (!addons.includes(moduleInfo.addon)) {
      return { isAllowed: false, moduleName: moduleInfo.name };
    }
  }

  // Check pack requirement
  if (moduleInfo.pack) {
    const packs = subscription?.enabled_packs || [];
    if (!packs.includes(moduleInfo.pack)) {
      return { isAllowed: false, moduleName: moduleInfo.name };
    }
  }

  return { isAllowed: true, moduleName: moduleInfo.name };
}

export default RouteGuard;
