"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/auth";

// Check if public mode is enabled (no login required)
const isPublicMode = process.env.NEXT_PUBLIC_PUBLIC_MODE === "true";

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredRoles?: string[];
}

export function ProtectedRoute({ children, requiredRoles }: ProtectedRouteProps) {
  const router = useRouter();
  const { user, isAuthenticated, isLoading, fetchUser, setGuestUser } = useAuthStore();

  useEffect(() => {
    // In public mode, set guest user if not authenticated
    if (isPublicMode) {
      if (!isAuthenticated) {
        setGuestUser();
      }
    } else {
      fetchUser();
    }
  }, [fetchUser, setGuestUser, isAuthenticated]);

  useEffect(() => {
    // Only redirect to login in private mode
    if (!isPublicMode && !isLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [isLoading, isAuthenticated, router]);

  // Check roles (skip for guests in public mode)
  useEffect(() => {
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
  }, [isLoading, isAuthenticated, user, requiredRoles, router]);

  // In public mode, don't show loading if we're setting up guest
  if (!isPublicMode && isLoading) {
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
