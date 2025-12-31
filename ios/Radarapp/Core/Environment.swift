// Environment.swift
// Environment configuration for different build configurations

import Foundation

enum Environment {
    case development
    case production
    
    // MARK: - Current Environment
    static var current: Environment {
        #if DEV
        return .development
        #elseif PROD
        return .production
        #else
        return .development
        #endif
    }
    
    // MARK: - API Configuration
    var apiBaseURL: URL {
        guard let urlString = Bundle.main.infoDictionary?["API_BASE_URL"] as? String,
              let url = URL(string: urlString.replacingOccurrences(of: "$()", with: "/")) else {
            switch self {
            case .development:
                return URL(string: "http://localhost:8000")!
            case .production:
                return URL(string: "https://radarapp.fr")!
            }
        }
        return url
    }
    
    var apiVersion: String {
        Bundle.main.infoDictionary?["API_VERSION"] as? String ?? "v1"
    }
    
    var fullAPIURL: URL {
        apiBaseURL.appendingPathComponent("api").appendingPathComponent(apiVersion)
    }
    
    // MARK: - Feature Flags
    var isDebugLoggingEnabled: Bool {
        #if DEBUG
        return true
        #else
        return false
        #endif
    }
    
    var isMockDataEnabled: Bool {
        #if DEBUG
        return ProcessInfo.processInfo.arguments.contains("-useMockData")
        #else
        return false
        #endif
    }
    
    // MARK: - Timeouts
    var requestTimeout: TimeInterval { 30 }
    var resourceTimeout: TimeInterval { 60 }
    
    // MARK: - Retry Configuration
    var maxRetryAttempts: Int { 3 }
    var initialRetryDelay: TimeInterval { 1.0 }
    var maxRetryDelay: TimeInterval { 30.0 }
    
    // MARK: - Cache Configuration
    var cacheExpirationInterval: TimeInterval {
        switch self {
        case .development: return 5 * 60 // 5 minutes
        case .production: return 15 * 60 // 15 minutes
        }
    }
    
    // MARK: - Pagination
    var defaultPageSize: Int { 20 }
    var maxPageSize: Int { 100 }
    
    // MARK: - Search
    var searchDebounceInterval: TimeInterval { 0.25 } // 250ms
}

// MARK: - Logger
struct Logger {
    enum Level: String {
        case debug = "🔍 DEBUG"
        case info = "ℹ️ INFO"
        case warning = "⚠️ WARNING"
        case error = "❌ ERROR"
    }
    
    static func log(_ message: String, level: Level = .info, file: String = #file, function: String = #function, line: Int = #line) {
        guard Environment.current.isDebugLoggingEnabled else { return }
        
        let fileName = (file as NSString).lastPathComponent
        let timestamp = ISO8601DateFormatter().string(from: Date())
        print("\(level.rawValue) [\(timestamp)] [\(fileName):\(line)] \(function) → \(message)")
    }
    
    static func debug(_ message: String, file: String = #file, function: String = #function, line: Int = #line) {
        log(message, level: .debug, file: file, function: function, line: line)
    }
    
    static func info(_ message: String, file: String = #file, function: String = #function, line: Int = #line) {
        log(message, level: .info, file: file, function: function, line: line)
    }
    
    static func warning(_ message: String, file: String = #file, function: String = #function, line: Int = #line) {
        log(message, level: .warning, file: file, function: function, line: line)
    }
    
    static func error(_ message: String, file: String = #file, function: String = #function, line: Int = #line) {
        log(message, level: .error, file: file, function: function, line: line)
    }
}
