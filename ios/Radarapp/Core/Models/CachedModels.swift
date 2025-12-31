// CachedModels.swift
// SwiftData models for local caching

import Foundation
import SwiftData

// MARK: - Cached Opportunity
@Model
final class CachedOpportunity {
    @Attribute(.unique) var id: Int
    var title: String
    var descriptionText: String?
    var source: String?
    var sourceUrl: String?
    var organization: String?
    var location: String?
    var region: String?
    var budgetMin: Double?
    var budgetMax: Double?
    var deadline: Date?
    var score: Double?
    var status: String?
    var tagsData: Data?
    var hasContact: Bool
    var hasDeadline: Bool
    var contactInfoData: Data?
    var documentsData: Data?
    var extractedFieldsData: Data?
    var evidenceData: Data?
    var clusterCount: Int?
    var createdAt: Date?
    var updatedAt: Date?
    var assignedTo: Int?
    
    // Cache metadata
    var cachedAt: Date
    var searchQuery: String?
    
    init(from opportunity: Opportunity, query: String? = nil) {
        self.id = opportunity.id
        self.title = opportunity.title
        self.descriptionText = opportunity.description
        self.source = opportunity.source
        self.sourceUrl = opportunity.sourceUrl
        self.organization = opportunity.organization
        self.location = opportunity.location
        self.region = opportunity.region
        self.budgetMin = opportunity.budgetMin
        self.budgetMax = opportunity.budgetMax
        self.deadline = opportunity.deadline
        self.score = opportunity.score
        self.status = opportunity.status?.rawValue
        self.tagsData = try? JSONEncoder().encode(opportunity.tags)
        self.hasContact = opportunity.hasContact ?? false
        self.hasDeadline = opportunity.hasDeadline ?? false
        self.contactInfoData = try? JSONEncoder().encode(opportunity.contactInfo)
        self.documentsData = try? JSONEncoder().encode(opportunity.documents)
        self.extractedFieldsData = try? JSONEncoder().encode(opportunity.extractedFields)
        self.evidenceData = try? JSONEncoder().encode(opportunity.evidence)
        self.clusterCount = opportunity.clusterCount
        self.createdAt = opportunity.createdAt
        self.updatedAt = opportunity.updatedAt
        self.assignedTo = opportunity.assignedTo
        self.cachedAt = Date()
        self.searchQuery = query
    }
    
    func toOpportunity() -> Opportunity {
        let tags = tagsData.flatMap { try? JSONDecoder().decode([String].self, from: $0) }
        let contactInfo = contactInfoData.flatMap { try? JSONDecoder().decode(ContactInfo.self, from: $0) }
        let documents = documentsData.flatMap { try? JSONDecoder().decode([Document].self, from: $0) }
        let extractedFields = extractedFieldsData.flatMap { try? JSONDecoder().decode([String: String].self, from: $0) }
        let evidence = evidenceData.flatMap { try? JSONDecoder().decode([Evidence].self, from: $0) }
        
        return Opportunity(
            id: id,
            title: title,
            description: descriptionText,
            source: source,
            sourceUrl: sourceUrl,
            organization: organization,
            location: location,
            region: region,
            budgetMin: budgetMin,
            budgetMax: budgetMax,
            deadline: deadline,
            score: score,
            status: status.flatMap { OpportunityStatus(rawValue: $0) },
            tags: tags,
            hasContact: hasContact,
            hasDeadline: hasDeadline,
            contactInfo: contactInfo,
            documents: documents,
            extractedFields: extractedFields,
            evidence: evidence,
            clusterCount: clusterCount,
            createdAt: createdAt,
            updatedAt: updatedAt,
            assignedTo: assignedTo
        )
    }
}

// MARK: - Cached Dossier
@Model
final class CachedDossier {
    @Attribute(.unique) var id: Int
    var title: String
    var objective: String?
    var entity: String?
    var status: String?
    var briefShort: String?
    var briefLong: String?
    var confidence: Double?
    var score: Double?
    var contactsData: Data?
    var timelineData: Data?
    var documentsData: Data?
    var sourcesData: Data?
    var evidenceData: Data?
    var enrichedViaWeb: Bool
    var createdAt: Date?
    var updatedAt: Date?
    
    // Cache metadata
    var cachedAt: Date
    
    init(from dossier: Dossier) {
        self.id = dossier.id
        self.title = dossier.title
        self.objective = dossier.objective
        self.entity = dossier.entity
        self.status = dossier.status?.rawValue
        self.briefShort = dossier.briefShort
        self.briefLong = dossier.briefLong
        self.confidence = dossier.confidence
        self.score = dossier.score
        self.contactsData = try? JSONEncoder().encode(dossier.contacts)
        self.timelineData = try? JSONEncoder().encode(dossier.timeline)
        self.documentsData = try? JSONEncoder().encode(dossier.documents)
        self.sourcesData = try? JSONEncoder().encode(dossier.sources)
        self.evidenceData = try? JSONEncoder().encode(dossier.evidence)
        self.enrichedViaWeb = dossier.enrichedViaWeb ?? false
        self.createdAt = dossier.createdAt
        self.updatedAt = dossier.updatedAt
        self.cachedAt = Date()
    }
    
    func toDossier() -> Dossier {
        let contacts = contactsData.flatMap { try? JSONDecoder().decode([RankedContact].self, from: $0) }
        let timeline = timelineData.flatMap { try? JSONDecoder().decode([TimelineEvent].self, from: $0) }
        let documents = documentsData.flatMap { try? JSONDecoder().decode([Document].self, from: $0) }
        let sources = sourcesData.flatMap { try? JSONDecoder().decode([String].self, from: $0) }
        let evidence = evidenceData.flatMap { try? JSONDecoder().decode([Evidence].self, from: $0) }
        
        return Dossier(
            id: id,
            title: title,
            objective: objective,
            entity: entity,
            status: status.flatMap { DossierStatus(rawValue: $0) },
            briefShort: briefShort,
            briefLong: briefLong,
            confidence: confidence,
            score: score,
            contacts: contacts,
            timeline: timeline,
            documents: documents,
            sources: sources,
            evidence: evidence,
            enrichedViaWeb: enrichedViaWeb,
            createdAt: createdAt,
            updatedAt: updatedAt
        )
    }
}

// MARK: - Cached Collection
@Model
final class CachedCollection {
    @Attribute(.unique) var id: Int
    var name: String?
    var type: String?
    var status: String
    var configData: Data?
    var resultsCount: Int?
    var errorMessage: String?
    var duration: Int?
    var logsData: Data?
    var sourcesConsultedData: Data?
    var startedAt: Date?
    var completedAt: Date?
    var createdAt: Date?
    
    // Cache metadata
    var cachedAt: Date
    
    init(from collection: Collection) {
        self.id = collection.id
        self.name = collection.name
        self.type = collection.type?.rawValue
        self.status = collection.status.rawValue
        self.configData = try? JSONEncoder().encode(collection.config)
        self.resultsCount = collection.resultsCount
        self.errorMessage = collection.errorMessage
        self.duration = collection.duration
        self.logsData = try? JSONEncoder().encode(collection.logs)
        self.sourcesConsultedData = try? JSONEncoder().encode(collection.sourcesConsulted)
        self.startedAt = collection.startedAt
        self.completedAt = collection.completedAt
        self.createdAt = collection.createdAt
        self.cachedAt = Date()
    }
    
    func toCollection() -> Collection {
        let config = configData.flatMap { try? JSONDecoder().decode(CollectionConfig.self, from: $0) }
        let logs = logsData.flatMap { try? JSONDecoder().decode([String].self, from: $0) }
        let sourcesConsulted = sourcesConsultedData.flatMap { try? JSONDecoder().decode([String].self, from: $0) }
        
        return Collection(
            id: id,
            name: name,
            type: type.flatMap { CollectionType(rawValue: $0) },
            status: CollectionStatus(rawValue: status) ?? .failed,
            config: config,
            resultsCount: resultsCount,
            errorMessage: errorMessage,
            duration: duration,
            logs: logs,
            sourcesConsulted: sourcesConsulted,
            startedAt: startedAt,
            completedAt: completedAt,
            createdAt: createdAt
        )
    }
}

// MARK: - User Preferences
@Model
final class UserPreferences {
    var lastFiltersData: Data?
    var lastSelectedTab: String?
    var notificationsEnabled: Bool
    var darkModePreference: String? // nil = system, "light", "dark"
    var lastSyncDate: Date?
    
    init() {
        self.notificationsEnabled = true
    }
    
    var lastFilters: OpportunityFilters? {
        get {
            lastFiltersData.flatMap { try? JSONDecoder().decode(OpportunityFilters.self, from: $0) }
        }
        set {
            lastFiltersData = try? JSONEncoder().encode(newValue)
        }
    }
}

// Make OpportunityFilters Codable for persistence
extension OpportunityFilters: Codable {
    enum CodingKeys: String, CodingKey {
        case searchText, scoreMin, scoreMax, budgetMin, budgetMax
        case deadlineFrom, deadlineTo, source, hasContact, hasDeadline, status, sortBy
    }
}
