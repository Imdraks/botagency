"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useAuthStore } from "@/store/auth";

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredRoles?: string[];
  allowAdmin?: boolean; // Allow admin to access this page
}

export function ProtectedRoute({ children, requiredRoles, allowAdmin = true }: ProtectedRouteProps) {
  const router = useRouter();
  const pathname = usePathname();
  const { user, isAuthenticated, isLoading, fetchUser } = useAuthStore();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!mounted) return;
    fetchUser();
  }, [mounted, fetchUser]);

  useEffect(() => {
    if (!mounted) return;
    
    // Redirect to login if not authenticated
    if (!isLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [mounted, isLoading, isAuthenticated, router]);

  // Redirect based on role
  useEffect(() => {
    if (!mounted || isLoading || !isAuthenticated || !user) return;
    
    const isAdminPage = pathname.startsWith('/admin') || pathname === '/workspaces' || pathname.startsWith('/workspaces/') || pathname === '/users' || pathname.startsWith('/users/');
    const isAdmin = user.role === 'admin';
    
    // Admin trying to access non-admin pages → redirect to admin dashboard
    if (isAdmin && !isAdminPage && !allowAdmin) {
      router.push("/admin");
      return;
    }
    
    // Non-admin trying to access admin pages → redirect to today
    if (!isAdmin && isAdminPage) {
      router.push("/today");
      return;
    }
    
  }, [mounted, isLoading, isAuthenticated, user, pathname, router, allowAdmin]);

  // Check roles
  useEffect(() => {
    if (!mounted) return;
    
    if (!isLoading && isAuthenticated && user && requiredRoles?.length) {
      if (!requiredRoles.includes(user.role)) {
        router.push("/unauthorized");
      }
    }
  }, [mounted, isLoading, isAuthenticated, user, requiredRoles, router]);

  // Show loading until mounted and auth checked
  if (!mounted || isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary" />
      </div>
    );
  }

  // Require authentication
  if (!isAuthenticated) {
    return null;
  }

  return <>{children}</>;
}

export default ProtectedRoute;
