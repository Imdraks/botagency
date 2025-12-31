// RadarappApp.swift
// Main entry point for the Radarapp iOS application
// Architecture: MVVM + Services + Coordinator

import SwiftUI
import SwiftData

@main
struct RadarappApp: App {
    // MARK: - State
    @StateObject private var appState = AppState()
    @StateObject private var authService = AuthService.shared
    @StateObject private var networkMonitor = NetworkMonitor.shared
    
    // MARK: - SwiftData
    let modelContainer: ModelContainer
    
    init() {
        // Initialize SwiftData container
        do {
            let schema = Schema([
                CachedOpportunity.self,
                CachedDossier.self,
                CachedCollection.self,
                UserPreferences.self
            ])
            let modelConfiguration = ModelConfiguration(
                schema: schema,
                isStoredInMemoryOnly: false,
                allowsSave: true
            )
            modelContainer = try ModelContainer(
                for: schema,
                configurations: [modelConfiguration]
            )
        } catch {
            fatalError("Failed to initialize SwiftData: \(error)")
        }
        
        // Configure appearance
        configureAppearance()
    }
    
    var body: some Scene {
        WindowGroup {
            RootView()
                .environmentObject(appState)
                .environmentObject(authService)
                .environmentObject(networkMonitor)
                .modelContainer(modelContainer)
                .preferredColorScheme(appState.colorScheme)
        }
    }
    
    // MARK: - Appearance Configuration
    private func configureAppearance() {
        // Configure navigation bar appearance for Liquid Glass
        let appearance = UINavigationBarAppearance()
        appearance.configureWithDefaultBackground()
        appearance.backgroundEffect = UIBlurEffect(style: .systemThinMaterial)
        appearance.backgroundColor = UIColor.systemBackground.withAlphaComponent(0.7)
        
        UINavigationBar.appearance().standardAppearance = appearance
        UINavigationBar.appearance().compactAppearance = appearance
        UINavigationBar.appearance().scrollEdgeAppearance = appearance
        
        // Tab bar appearance
        let tabAppearance = UITabBarAppearance()
        tabAppearance.configureWithDefaultBackground()
        tabAppearance.backgroundEffect = UIBlurEffect(style: .systemThinMaterial)
        tabAppearance.backgroundColor = UIColor.systemBackground.withAlphaComponent(0.7)
        
        UITabBar.appearance().standardAppearance = tabAppearance
        UITabBar.appearance().scrollEdgeAppearance = tabAppearance
    }
}

// MARK: - App State
@MainActor
final class AppState: ObservableObject {
    @Published var colorScheme: ColorScheme? = nil
    @Published var showOnboarding: Bool = false
    @Published var selectedTab: AppTab = .opportunities
    @Published var isLoading: Bool = false
    @Published var globalError: AppError? = nil
    
    // Accessibility
    @Published var reduceTransparency: Bool = false
    @Published var reduceMotion: Bool = false
    
    init() {
        // Observe accessibility settings
        NotificationCenter.default.addObserver(
            self,
            selector: #selector(accessibilitySettingsChanged),
            name: UIAccessibility.reduceTransparencyStatusDidChangeNotification,
            object: nil
        )
        NotificationCenter.default.addObserver(
            self,
            selector: #selector(accessibilitySettingsChanged),
            name: UIAccessibility.reduceMotionStatusDidChangeNotification,
            object: nil
        )
        
        updateAccessibilitySettings()
    }
    
    @objc private func accessibilitySettingsChanged() {
        updateAccessibilitySettings()
    }
    
    private func updateAccessibilitySettings() {
        reduceTransparency = UIAccessibility.isReduceTransparencyEnabled
        reduceMotion = UIAccessibility.isReduceMotionEnabled
    }
}

// MARK: - App Tabs
enum AppTab: String, CaseIterable, Identifiable {
    case opportunities = "Opportunités"
    case dossiers = "Dossiers"
    case newCollection = "Collecte"
    case history = "Historique"
    
    var id: String { rawValue }
    
    var icon: String {
        switch self {
        case .opportunities: return "magnifyingglass.circle.fill"
        case .dossiers: return "folder.fill"
        case .newCollection: return "plus.circle.fill"
        case .history: return "clock.fill"
        }
    }
    
    var selectedIcon: String {
        switch self {
        case .opportunities: return "magnifyingglass.circle.fill"
        case .dossiers: return "folder.fill"
        case .newCollection: return "plus.circle.fill"
        case .history: return "clock.fill"
        }
    }
}

// MARK: - App Errors
enum AppError: Error, Identifiable, LocalizedError {
    case network(NetworkError)
    case auth(AuthError)
    case storage(StorageError)
    case unknown(String)
    
    var id: String {
        switch self {
        case .network(let error): return "network_\(error.localizedDescription)"
        case .auth(let error): return "auth_\(error.localizedDescription)"
        case .storage(let error): return "storage_\(error.localizedDescription)"
        case .unknown(let message): return "unknown_\(message)"
        }
    }
    
    var errorDescription: String? {
        switch self {
        case .network(let error): return error.localizedDescription
        case .auth(let error): return error.localizedDescription
        case .storage(let error): return error.localizedDescription
        case .unknown(let message): return message
        }
    }
}

// MARK: - Error Types
enum NetworkError: Error, LocalizedError {
    case noConnection
    case timeout
    case serverError(Int)
    case decodingError
    case invalidURL
    case unauthorized
    case notFound
    case rateLimited
    case unknown(String)
    
    var errorDescription: String? {
        switch self {
        case .noConnection: return "Pas de connexion internet"
        case .timeout: return "La requête a expiré"
        case .serverError(let code): return "Erreur serveur (\(code))"
        case .decodingError: return "Erreur de décodage des données"
        case .invalidURL: return "URL invalide"
        case .unauthorized: return "Session expirée"
        case .notFound: return "Ressource non trouvée"
        case .rateLimited: return "Trop de requêtes, veuillez patienter"
        case .unknown(let msg): return msg
        }
    }
}

enum AuthError: Error, LocalizedError {
    case invalidCredentials
    case tokenExpired
    case noToken
    case keychainError
    
    var errorDescription: String? {
        switch self {
        case .invalidCredentials: return "Identifiants invalides"
        case .tokenExpired: return "Session expirée"
        case .noToken: return "Non authentifié"
        case .keychainError: return "Erreur de stockage sécurisé"
        }
    }
}

enum StorageError: Error, LocalizedError {
    case saveFailed
    case fetchFailed
    case deleteFailed
    case migrationFailed
    
    var errorDescription: String? {
        switch self {
        case .saveFailed: return "Échec de sauvegarde"
        case .fetchFailed: return "Échec de récupération"
        case .deleteFailed: return "Échec de suppression"
        case .migrationFailed: return "Échec de migration"
        }
    }
}
