"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/auth";

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredRoles?: string[];
}

export function ProtectedRoute({ children, requiredRoles }: ProtectedRouteProps) {
  const router = useRouter();
  const { user, isAuthenticated, isLoading, fetchUser, setGuestUser } = useAuthStore();
  const [mounted, setMounted] = useState(false);
  const [isPublicMode, setIsPublicMode] = useState(false);

  // Wait for client-side mount to check env variable
  useEffect(() => {
    setMounted(true);
    setIsPublicMode(process.env.NEXT_PUBLIC_PUBLIC_MODE === "true");
  }, []);

  useEffect(() => {
    if (!mounted) return;
    
    // In public mode, set guest user if not authenticated
    if (isPublicMode) {
      if (!isAuthenticated) {
        setGuestUser();
      }
    } else {
      fetchUser();
    }
  }, [mounted, isPublicMode, fetchUser, setGuestUser, isAuthenticated]);

  useEffect(() => {
    if (!mounted) return;
    
    // Only redirect to login in private mode
    if (!isPublicMode && !isLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [mounted, isPublicMode, isLoading, isAuthenticated, router]);

  // Check roles (skip for guests in public mode)
  useEffect(() => {
    if (!mounted) return;
    
    if (!isLoading && isAuthenticated && user && requiredRoles?.length) {
      // In public mode, guests can't access role-restricted pages
      if (user.role === "guest") {
        router.push("/unauthorized");
        return;
      }
      if (!requiredRoles.includes(user.role)) {
        router.push("/unauthorized");
      }
    }
  }, [mounted, isLoading, isAuthenticated, user, requiredRoles, router]);

  // Show loading until mounted and auth checked
  if (!mounted || (!isPublicMode && isLoading)) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary" />
      </div>
    );
  }

  // In private mode, require authentication
  if (!isPublicMode && !isAuthenticated) {
    return null;
  }

  return <>{children}</>;
}

export default ProtectedRoute;
