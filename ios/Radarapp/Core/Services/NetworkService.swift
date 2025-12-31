// NetworkService.swift
// Networking layer with async/await, retry logic, and cancellation support

import Foundation
import Combine

// MARK: - Network Service
@MainActor
final class NetworkService: ObservableObject {
    static let shared = NetworkService()
    
    private let session: URLSession
    private var activeTasks: [String: Task<Any, Error>] = [:]
    
    private init() {
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = Environment.current.requestTimeout
        config.timeoutIntervalForResource = Environment.current.resourceTimeout
        config.waitsForConnectivity = true
        config.requestCachePolicy = .reloadIgnoringLocalCacheData
        
        self.session = URLSession(configuration: config)
    }
    
    // MARK: - Request Execution
    func request<T: Decodable>(
        _ endpoint: Endpoint,
        responseType: T.Type,
        retryCount: Int = 0
    ) async throws -> T {
        let request = try await buildRequest(for: endpoint)
        
        Logger.debug("Request: \(endpoint.method.rawValue) \(endpoint.path)")
        
        do {
            let (data, response) = try await session.data(for: request)
            
            guard let httpResponse = response as? HTTPURLResponse else {
                throw NetworkError.unknown("Invalid response type")
            }
            
            Logger.debug("Response: \(httpResponse.statusCode) for \(endpoint.path)")
            
            // Handle response codes
            switch httpResponse.statusCode {
            case 200...299:
                return try decode(data, as: T.self)
                
            case 401:
                // Token expired, try to refresh
                try await AuthService.shared.refreshTokenIfNeeded()
                // Retry the request once
                if retryCount == 0 {
                    return try await self.request(endpoint, responseType: responseType, retryCount: 1)
                }
                throw NetworkError.unauthorized
                
            case 404:
                throw NetworkError.notFound
                
            case 429:
                throw NetworkError.rateLimited
                
            case 500...599:
                throw NetworkError.serverError(httpResponse.statusCode)
                
            default:
                throw NetworkError.unknown("HTTP \(httpResponse.statusCode)")
            }
            
        } catch let error as NetworkError {
            throw error
        } catch is DecodingError {
            throw NetworkError.decodingError
        } catch {
            // Retry logic for transient errors
            if retryCount < Environment.current.maxRetryAttempts && isRetryableError(error) {
                let delay = calculateRetryDelay(attempt: retryCount)
                Logger.warning("Retrying in \(delay)s... (attempt \(retryCount + 1))")
                try await Task.sleep(nanoseconds: UInt64(delay * 1_000_000_000))
                return try await self.request(endpoint, responseType: responseType, retryCount: retryCount + 1)
            }
            
            if (error as NSError).code == NSURLErrorNotConnectedToInternet {
                throw NetworkError.noConnection
            } else if (error as NSError).code == NSURLErrorTimedOut {
                throw NetworkError.timeout
            }
            
            throw NetworkError.unknown(error.localizedDescription)
        }
    }
    
    // MARK: - Cancellable Request
    func cancellableRequest<T: Decodable>(
        _ endpoint: Endpoint,
        responseType: T.Type,
        taskId: String
    ) async throws -> T {
        // Cancel existing task with same ID
        cancelTask(id: taskId)
        
        let task = Task<Any, Error> {
            try await request(endpoint, responseType: responseType)
        }
        
        activeTasks[taskId] = task
        
        defer {
            activeTasks.removeValue(forKey: taskId)
        }
        
        let result = try await task.value
        return result as! T
    }
    
    func cancelTask(id: String) {
        if let task = activeTasks[id] {
            task.cancel()
            activeTasks.removeValue(forKey: id)
            Logger.debug("Cancelled task: \(id)")
        }
    }
    
    func cancelAllTasks() {
        activeTasks.values.forEach { $0.cancel() }
        activeTasks.removeAll()
    }
    
    // MARK: - Request Building
    private func buildRequest(for endpoint: Endpoint) async throws -> URLRequest {
        guard let url = endpoint.url else {
            throw NetworkError.invalidURL
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = endpoint.method.rawValue
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("application/json", forHTTPHeaderField: "Accept")
        
        // Add auth token if available
        if let token = await AuthService.shared.accessToken {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        
        // Add custom headers
        for (key, value) in endpoint.headers {
            request.setValue(value, forHTTPHeaderField: key)
        }
        
        // Add body
        if let body = endpoint.body {
            request.httpBody = try JSONEncoder().encode(body)
        }
        
        return request
    }
    
    // MARK: - Decoding
    private func decode<T: Decodable>(_ data: Data, as type: T.Type) throws -> T {
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .custom { decoder in
            let container = try decoder.singleValueContainer()
            let dateString = try container.decode(String.self)
            
            // Try ISO8601 with fractional seconds
            let formatter = ISO8601DateFormatter()
            formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
            if let date = formatter.date(from: dateString) {
                return date
            }
            
            // Try without fractional seconds
            formatter.formatOptions = [.withInternetDateTime]
            if let date = formatter.date(from: dateString) {
                return date
            }
            
            throw DecodingError.dataCorruptedError(in: container, debugDescription: "Cannot decode date: \(dateString)")
        }
        decoder.keyDecodingStrategy = .convertFromSnakeCase
        
        return try decoder.decode(T.self, from: data)
    }
    
    // MARK: - Retry Logic
    private func isRetryableError(_ error: Error) -> Bool {
        let nsError = error as NSError
        let retryableCodes = [
            NSURLErrorNetworkConnectionLost,
            NSURLErrorTimedOut,
            NSURLErrorCannotConnectToHost,
            NSURLErrorNotConnectedToInternet
        ]
        return retryableCodes.contains(nsError.code)
    }
    
    private func calculateRetryDelay(attempt: Int) -> TimeInterval {
        let delay = Environment.current.initialRetryDelay * pow(2.0, Double(attempt))
        return min(delay, Environment.current.maxRetryDelay)
    }
}

// MARK: - Endpoint Definition
struct Endpoint {
    let path: String
    let method: HTTPMethod
    let queryItems: [URLQueryItem]
    let headers: [String: String]
    let body: (any Encodable)?
    
    init(
        path: String,
        method: HTTPMethod = .get,
        queryItems: [URLQueryItem] = [],
        headers: [String: String] = [:],
        body: (any Encodable)? = nil
    ) {
        self.path = path
        self.method = method
        self.queryItems = queryItems
        self.headers = headers
        self.body = body
    }
    
    var url: URL? {
        var components = URLComponents(url: Environment.current.fullAPIURL.appendingPathComponent(path), resolvingAgainstBaseURL: true)
        if !queryItems.isEmpty {
            components?.queryItems = queryItems
        }
        return components?.url
    }
}

// MARK: - HTTP Method
enum HTTPMethod: String {
    case get = "GET"
    case post = "POST"
    case put = "PUT"
    case patch = "PATCH"
    case delete = "DELETE"
}

// MARK: - Body Wrapper
struct AnyEncodable: Encodable {
    private let _encode: (Encoder) throws -> Void
    
    init<T: Encodable>(_ wrapped: T) {
        self._encode = wrapped.encode
    }
    
    func encode(to encoder: Encoder) throws {
        try _encode(encoder)
    }
}
