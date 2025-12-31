// AuthService.swift
// Authentication service with Keychain storage

import Foundation
import Security
import Combine

@MainActor
final class AuthService: ObservableObject {
    static let shared = AuthService()
    
    @Published private(set) var isAuthenticated: Bool = false
    @Published private(set) var currentUser: User?
    @Published private(set) var isLoading: Bool = false
    
    private(set) var accessToken: String?
    private var refreshToken: String?
    
    private let keychainService = "fr.radarapp.ios"
    private let accessTokenKey = "access_token"
    private let refreshTokenKey = "refresh_token"
    
    private init() {
        loadTokens()
    }
    
    // MARK: - Authentication
    func login(email: String, password: String) async throws {
        isLoading = true
        defer { isLoading = false }
        
        let endpoint = Endpoint(
            path: "auth/login",
            method: .post,
            body: LoginRequest(email: email, password: password)
        )
        
        let response = try await NetworkService.shared.request(endpoint, responseType: AuthResponse.self)
        
        await handleAuthResponse(response)
    }
    
    func logout() {
        accessToken = nil
        refreshToken = nil
        currentUser = nil
        isAuthenticated = false
        
        deleteFromKeychain(key: accessTokenKey)
        deleteFromKeychain(key: refreshTokenKey)
        
        Logger.info("User logged out")
    }
    
    func refreshTokenIfNeeded() async throws {
        guard let refreshToken = refreshToken else {
            throw AuthError.noToken
        }
        
        let endpoint = Endpoint(
            path: "auth/refresh",
            method: .post,
            body: RefreshRequest(refreshToken: refreshToken)
        )
        
        do {
            let response = try await NetworkService.shared.request(endpoint, responseType: AuthResponse.self)
            await handleAuthResponse(response)
        } catch {
            // Refresh failed, logout
            logout()
            throw AuthError.tokenExpired
        }
    }
    
    func fetchCurrentUser() async throws {
        guard isAuthenticated else { return }
        
        let endpoint = Endpoint(path: "users/me")
        currentUser = try await NetworkService.shared.request(endpoint, responseType: User.self)
    }
    
    // MARK: - Token Management
    private func handleAuthResponse(_ response: AuthResponse) async {
        accessToken = response.accessToken
        refreshToken = response.refreshToken
        isAuthenticated = true
        
        saveToKeychain(key: accessTokenKey, value: response.accessToken)
        if let refresh = response.refreshToken {
            saveToKeychain(key: refreshTokenKey, value: refresh)
        }
        
        // Fetch user profile
        try? await fetchCurrentUser()
        
        Logger.info("User authenticated successfully")
    }
    
    private func loadTokens() {
        accessToken = loadFromKeychain(key: accessTokenKey)
        refreshToken = loadFromKeychain(key: refreshTokenKey)
        isAuthenticated = accessToken != nil
        
        if isAuthenticated {
            Logger.info("Loaded tokens from Keychain")
            Task {
                try? await fetchCurrentUser()
            }
        }
    }
    
    // MARK: - Keychain Operations
    private func saveToKeychain(key: String, value: String) {
        guard let data = value.data(using: .utf8) else { return }
        
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: keychainService,
            kSecAttrAccount as String: key,
            kSecValueData as String: data,
            kSecAttrAccessible as String: kSecAttrAccessibleAfterFirstUnlock
        ]
        
        // Delete existing item
        SecItemDelete(query as CFDictionary)
        
        // Add new item
        let status = SecItemAdd(query as CFDictionary, nil)
        
        if status != errSecSuccess {
            Logger.error("Failed to save to Keychain: \(status)")
        }
    }
    
    private func loadFromKeychain(key: String) -> String? {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: keychainService,
            kSecAttrAccount as String: key,
            kSecReturnData as String: true,
            kSecMatchLimit as String: kSecMatchLimitOne
        ]
        
        var result: AnyObject?
        let status = SecItemCopyMatching(query as CFDictionary, &result)
        
        guard status == errSecSuccess,
              let data = result as? Data,
              let value = String(data: data, encoding: .utf8) else {
            return nil
        }
        
        return value
    }
    
    private func deleteFromKeychain(key: String) {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: keychainService,
            kSecAttrAccount as String: key
        ]
        
        SecItemDelete(query as CFDictionary)
    }
}

// MARK: - Request/Response Models
struct LoginRequest: Codable {
    let email: String
    let password: String
}

struct RefreshRequest: Codable {
    let refreshToken: String
}

struct AuthResponse: Codable {
    let accessToken: String
    let refreshToken: String?
    let tokenType: String
    let expiresIn: Int?
}
