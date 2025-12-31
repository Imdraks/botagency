// AuthService.swift
// Authentication service with Keychain storage

import Foundation
import Security

// MARK: - Auth Errors
enum AuthError: Error, LocalizedError {
    case invalidCredentials
    case networkError
    case noToken
    case tokenExpired
    case unknown
    
    var errorDescription: String? {
        switch self {
        case .invalidCredentials: return "Email ou mot de passe incorrect"
        case .networkError: return "Erreur réseau"
        case .noToken: return "Token manquant"
        case .tokenExpired: return "Session expirée"
        case .unknown: return "Erreur inconnue"
        }
    }
}

// MARK: - Auth Service
@MainActor
final class AuthService: ObservableObject {
    static let shared = AuthService()
    
    @Published private(set) var isAuthenticated: Bool = false
    @Published private(set) var currentUser: User?
    @Published private(set) var isLoading: Bool = false
    
    // Public token property for APIService
    var token: String? { accessToken }
    
    private var accessToken: String?
    private var refreshToken: String?
    
    private let keychainService = "fr.radarapp.ios"
    private let accessTokenKey = "access_token"
    private let refreshTokenKey = "refresh_token"
    private let baseURL = "https://radarapp.fr/api/v1"
    
    private init() {
        loadTokens()
    }
    
    // MARK: - Authentication
    func login(email: String, password: String) async throws {
        isLoading = true
        defer { isLoading = false }
        
        guard let url = URL(string: "\(baseURL)/auth/login") else {
            throw AuthError.networkError
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let body = ["email": email, "password": password]
        request.httpBody = try JSONEncoder().encode(body)
        
        let (data, response) = try await URLSession.shared.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw AuthError.networkError
        }
        
        if httpResponse.statusCode == 401 {
            throw AuthError.invalidCredentials
        }
        
        guard (200...299).contains(httpResponse.statusCode) else {
            throw AuthError.networkError
        }
        
        let decoder = JSONDecoder()
        decoder.keyDecodingStrategy = .convertFromSnakeCase
        let authResponse = try decoder.decode(AuthResponse.self, from: data)
        
        await handleAuthResponse(authResponse)
    }
    
    func logout() {
        accessToken = nil
        refreshToken = nil
        currentUser = nil
        isAuthenticated = false
        
        deleteFromKeychain(key: accessTokenKey)
        deleteFromKeychain(key: refreshTokenKey)
    }
    
    func refreshTokenIfNeeded() async throws {
        guard let refresh = refreshToken else {
            throw AuthError.noToken
        }
        
        guard let url = URL(string: "\(baseURL)/auth/refresh") else {
            throw AuthError.networkError
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let body = ["refresh_token": refresh]
        request.httpBody = try JSONEncoder().encode(body)
        
        do {
            let (data, _) = try await URLSession.shared.data(for: request)
            let decoder = JSONDecoder()
            decoder.keyDecodingStrategy = .convertFromSnakeCase
            let authResponse = try decoder.decode(AuthResponse.self, from: data)
            await handleAuthResponse(authResponse)
        } catch {
            logout()
            throw AuthError.tokenExpired
        }
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
    }
    
    private func loadTokens() {
        accessToken = loadFromKeychain(key: accessTokenKey)
        refreshToken = loadFromKeychain(key: refreshTokenKey)
        isAuthenticated = accessToken != nil
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
        
        SecItemDelete(query as CFDictionary)
        SecItemAdd(query as CFDictionary, nil)
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

// MARK: - Response Models
struct AuthResponse: Codable {
    let accessToken: String
    let refreshToken: String?
    let tokenType: String?
    let expiresIn: Int?
}
