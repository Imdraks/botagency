// RootView.swift
// Root navigation view with authentication state handling

import SwiftUI

struct RootView: View {
    @EnvironmentObject private var authService: AuthService
    @EnvironmentObject private var appState: AppState
    @EnvironmentObject private var networkMonitor: NetworkMonitor
    
    var body: some View {
        ZStack {
            Group {
                if authService.isAuthenticated {
                    MainTabView()
                        .transition(.opacity.combined(with: .scale(scale: 0.95)))
                } else {
                    LoginView()
                        .transition(.opacity.combined(with: .scale(scale: 1.05)))
                }
            }
            .animation(.spring(response: 0.5, dampingFraction: 0.8), value: authService.isAuthenticated)
            
            // Network status banner
            if !networkMonitor.isConnected {
                VStack {
                    OfflineBanner()
                    Spacer()
                }
                .transition(.move(edge: .top).combined(with: .opacity))
            }
            
            // Global loading overlay
            if appState.isLoading {
                LoadingOverlay()
            }
        }
        .animation(.easeInOut(duration: 0.3), value: networkMonitor.isConnected)
        .alert(item: $appState.globalError) { error in
            Alert(
                title: Text("Erreur"),
                message: Text(error.localizedDescription),
                dismissButton: .default(Text("OK"))
            )
        }
    }
}

// MARK: - Main Tab View
struct MainTabView: View {
    @EnvironmentObject private var appState: AppState
    
    var body: some View {
        TabView(selection: $appState.selectedTab) {
            OpportunitiesView()
                .tabItem {
                    Label(AppTab.opportunities.rawValue, systemImage: AppTab.opportunities.icon)
                }
                .tag(AppTab.opportunities)
            
            DossiersView()
                .tabItem {
                    Label(AppTab.dossiers.rawValue, systemImage: AppTab.dossiers.icon)
                }
                .tag(AppTab.dossiers)
            
            NewCollectionView()
                .tabItem {
                    Label(AppTab.newCollection.rawValue, systemImage: AppTab.newCollection.icon)
                }
                .tag(AppTab.newCollection)
            
            CollectionHistoryView()
                .tabItem {
                    Label(AppTab.history.rawValue, systemImage: AppTab.history.icon)
                }
                .tag(AppTab.history)
        }
        .tint(.accentColor)
    }
}

// MARK: - Offline Banner
struct OfflineBanner: View {
    @EnvironmentObject private var appState: AppState
    
    var body: some View {
        HStack(spacing: 8) {
            Image(systemName: "wifi.slash")
                .font(.subheadline.weight(.semibold))
            
            Text("Mode hors-ligne • Données en cache")
                .font(.subheadline.weight(.medium))
            
            Spacer()
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 10)
        .frame(maxWidth: .infinity)
        .background {
            if appState.reduceTransparency {
                Color.orange.opacity(0.9)
            } else {
                GlassBackground(style: .warning)
            }
        }
        .foregroundStyle(.white)
    }
}

// MARK: - Loading Overlay
struct LoadingOverlay: View {
    @EnvironmentObject private var appState: AppState
    
    var body: some View {
        ZStack {
            if appState.reduceTransparency {
                Color.black.opacity(0.4)
            } else {
                Color.black.opacity(0.2)
                    .background(.ultraThinMaterial)
            }
            
            VStack(spacing: 16) {
                ProgressView()
                    .scaleEffect(1.2)
                    .tint(.white)
                
                Text("Chargement...")
                    .font(.subheadline.weight(.medium))
                    .foregroundStyle(.white)
            }
            .padding(32)
            .background {
                RoundedRectangle(cornerRadius: 20, style: .continuous)
                    .fill(.ultraThinMaterial)
            }
        }
        .ignoresSafeArea()
    }
}

// MARK: - Preview
#Preview {
    RootView()
        .environmentObject(AppState())
        .environmentObject(AuthService.shared)
        .environmentObject(NetworkMonitor.shared)
}
