// StorageService.swift
// Local storage service with SwiftData for offline caching

import Foundation
import SwiftData

// MARK: - Storage Service
@MainActor
final class StorageService: ObservableObject {
    static let shared = StorageService()
    
    private var modelContainer: ModelContainer?
    private var modelContext: ModelContext?
    
    private init() {}
    
    func configure(with container: ModelContainer) {
        self.modelContainer = container
        self.modelContext = container.mainContext
    }
    
    // MARK: - Opportunities Cache
    func cacheOpportunities(_ opportunities: [Opportunity], query: String? = nil) async throws {
        guard let context = modelContext else { throw StorageError.saveFailed }
        
        for opportunity in opportunities {
            let cached = CachedOpportunity(from: opportunity, query: query)
            context.insert(cached)
        }
        
        try context.save()
        Logger.debug("Cached \(opportunities.count) opportunities")
    }
    
    func fetchCachedOpportunities(query: String? = nil, limit: Int = 50) async throws -> [Opportunity] {
        guard let context = modelContext else { throw StorageError.fetchFailed }
        
        var descriptor = FetchDescriptor<CachedOpportunity>(
            sortBy: [SortDescriptor(\.cachedAt, order: .reverse)]
        )
        descriptor.fetchLimit = limit
        
        if let query = query {
            descriptor.predicate = #Predicate<CachedOpportunity> { cached in
                cached.searchQuery == query
            }
        }
        
        let cached = try context.fetch(descriptor)
        return cached.map { $0.toOpportunity() }
    }
    
    func getCachedOpportunity(id: Int) async throws -> Opportunity? {
        guard let context = modelContext else { throw StorageError.fetchFailed }
        
        let descriptor = FetchDescriptor<CachedOpportunity>(
            predicate: #Predicate<CachedOpportunity> { $0.id == id }
        )
        
        return try context.fetch(descriptor).first?.toOpportunity()
    }
    
    // MARK: - Dossiers Cache
    func cacheDossiers(_ dossiers: [Dossier]) async throws {
        guard let context = modelContext else { throw StorageError.saveFailed }
        
        for dossier in dossiers {
            let cached = CachedDossier(from: dossier)
            context.insert(cached)
        }
        
        try context.save()
        Logger.debug("Cached \(dossiers.count) dossiers")
    }
    
    func fetchCachedDossiers(limit: Int = 50) async throws -> [Dossier] {
        guard let context = modelContext else { throw StorageError.fetchFailed }
        
        var descriptor = FetchDescriptor<CachedDossier>(
            sortBy: [SortDescriptor(\.cachedAt, order: .reverse)]
        )
        descriptor.fetchLimit = limit
        
        let cached = try context.fetch(descriptor)
        return cached.map { $0.toDossier() }
    }
    
    // MARK: - Collections Cache
    func cacheCollections(_ collections: [Collection]) async throws {
        guard let context = modelContext else { throw StorageError.saveFailed }
        
        for collection in collections {
            let cached = CachedCollection(from: collection)
            context.insert(cached)
        }
        
        try context.save()
        Logger.debug("Cached \(collections.count) collections")
    }
    
    func fetchCachedCollections(limit: Int = 50) async throws -> [Collection] {
        guard let context = modelContext else { throw StorageError.fetchFailed }
        
        var descriptor = FetchDescriptor<CachedCollection>(
            sortBy: [SortDescriptor(\.cachedAt, order: .reverse)]
        )
        descriptor.fetchLimit = limit
        
        let cached = try context.fetch(descriptor)
        return cached.map { $0.toCollection() }
    }
    
    // MARK: - User Preferences
    func savePreferences(_ preferences: UserPreferences) async throws {
        guard let context = modelContext else { throw StorageError.saveFailed }
        
        // Delete existing preferences
        let descriptor = FetchDescriptor<UserPreferences>()
        let existing = try context.fetch(descriptor)
        for pref in existing {
            context.delete(pref)
        }
        
        context.insert(preferences)
        try context.save()
    }
    
    func loadPreferences() async throws -> UserPreferences? {
        guard let context = modelContext else { throw StorageError.fetchFailed }
        
        let descriptor = FetchDescriptor<UserPreferences>()
        return try context.fetch(descriptor).first
    }
    
    // MARK: - Cache Cleanup
    func clearExpiredCache() async throws {
        guard let context = modelContext else { return }
        
        let expirationDate = Date().addingTimeInterval(-Environment.current.cacheExpirationInterval)
        
        // Clear expired opportunities
        let oppDescriptor = FetchDescriptor<CachedOpportunity>(
            predicate: #Predicate<CachedOpportunity> { $0.cachedAt < expirationDate }
        )
        let expiredOpps = try context.fetch(oppDescriptor)
        expiredOpps.forEach { context.delete($0) }
        
        // Clear expired dossiers
        let dosDescriptor = FetchDescriptor<CachedDossier>(
            predicate: #Predicate<CachedDossier> { $0.cachedAt < expirationDate }
        )
        let expiredDos = try context.fetch(dosDescriptor)
        expiredDos.forEach { context.delete($0) }
        
        // Clear expired collections
        let colDescriptor = FetchDescriptor<CachedCollection>(
            predicate: #Predicate<CachedCollection> { $0.cachedAt < expirationDate }
        )
        let expiredCols = try context.fetch(colDescriptor)
        expiredCols.forEach { context.delete($0) }
        
        try context.save()
        
        let total = expiredOpps.count + expiredDos.count + expiredCols.count
        if total > 0 {
            Logger.info("Cleared \(total) expired cache entries")
        }
    }
    
    func clearAllCache() async throws {
        guard let context = modelContext else { return }
        
        try context.delete(model: CachedOpportunity.self)
        try context.delete(model: CachedDossier.self)
        try context.delete(model: CachedCollection.self)
        try context.save()
        
        Logger.info("Cleared all cache")
    }
}
