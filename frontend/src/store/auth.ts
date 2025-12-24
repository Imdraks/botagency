"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";
import { User } from "@/lib/types";
import { authApi } from "@/lib/api";

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  rememberMe: boolean;
  lastLoginEmail: string | null;
  
  // Actions
  login: (email: string, password: string, rememberMe?: boolean) => Promise<void>;
  logout: () => void;
  fetchUser: () => Promise<void>;
  setUser: (user: User | null) => void;
  setRememberMe: (value: boolean) => void;
  setTokens: (accessToken: string, refreshToken: string) => Promise<void>;
  initializeAuth: () => Promise<void>;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      isAuthenticated: false,
      isLoading: true,
      rememberMe: true,
      lastLoginEmail: null,

      login: async (email: string, password: string, rememberMe = true) => {
        set({ isLoading: true });
        try {
          const response = await authApi.login(email, password);
          localStorage.setItem("access_token", response.access_token);
          localStorage.setItem("refresh_token", response.refresh_token);
          
          // Store remember me preference
          set({ rememberMe, lastLoginEmail: rememberMe ? email : null });
          
          // Fetch user after login
          await get().fetchUser();
        } catch (error) {
          set({ isLoading: false });
          throw error;
        }
      },

      logout: () => {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        set({ user: null, isAuthenticated: false, isLoading: false });
      },

      fetchUser: async () => {
        const token = localStorage.getItem("access_token");
        if (!token) {
          set({ user: null, isAuthenticated: false, isLoading: false });
          return;
        }

        try {
          const user = await authApi.getMe();
          set({ user, isAuthenticated: true, isLoading: false });
        } catch {
          // Try to refresh token before giving up
          const refreshToken = localStorage.getItem("refresh_token");
          if (refreshToken) {
            try {
              const response = await authApi.refresh(refreshToken);
              localStorage.setItem("access_token", response.access_token);
              if (response.refresh_token) {
                localStorage.setItem("refresh_token", response.refresh_token);
              }
              // Retry fetching user
              const user = await authApi.getMe();
              set({ user, isAuthenticated: true, isLoading: false });
              return;
            } catch {
              // Refresh failed
            }
          }
          localStorage.removeItem("access_token");
          localStorage.removeItem("refresh_token");
          set({ user: null, isAuthenticated: false, isLoading: false });
        }
      },

      setUser: (user: User | null) => {
        set({ user, isAuthenticated: !!user });
      },
      
      setRememberMe: (value: boolean) => {
        set({ rememberMe: value });
      },
      
      setTokens: async (accessToken: string, refreshToken: string) => {
        // Store tokens (from SSO callback)
        localStorage.setItem("access_token", accessToken);
        localStorage.setItem("refresh_token", refreshToken);
        // Fetch user info
        await get().fetchUser();
      },

      initializeAuth: async () => {
        const token = localStorage.getItem("access_token");
        if (token) {
          await get().fetchUser();
        } else {
          set({ isLoading: false });
        }
      },
    }),
    {
      name: "auth-storage",
      partialize: (state) => ({ 
        user: state.user, 
        isAuthenticated: state.isAuthenticated,
        rememberMe: state.rememberMe,
        lastLoginEmail: state.lastLoginEmail,
      }),
    }
  )
);
