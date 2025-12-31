// Models.swift
// Core domain models for the Radarapp

import Foundation

// MARK: - User
struct User: Codable, Identifiable, Equatable, Sendable {
    let id: Int
    let email: String
    let name: String?
    let role: String?
    let createdAt: Date?
    let lastLogin: Date?
    let isActive: Bool?
    
    var displayName: String {
        name ?? email.components(separatedBy: "@").first ?? email
    }
    
    var initials: String {
        let parts = displayName.components(separatedBy: " ")
        if parts.count >= 2 {
            return String(parts[0].prefix(1) + parts[1].prefix(1)).uppercased()
        }
        return String(displayName.prefix(2)).uppercased()
    }
}

// MARK: - Opportunity
struct Opportunity: Codable, Identifiable, Equatable, Sendable {
    let id: Int
    let title: String
    let description: String?
    let source: String?
    let sourceUrl: String?
    let organization: String?
    let location: String?
    let region: String?
    let budgetMin: Double?
    let budgetMax: Double?
    let deadline: Date?
    let score: Double?
    let status: OpportunityStatus?
    let tags: [String]?
    let hasContact: Bool?
    let hasDeadline: Bool?
    let contactInfo: ContactInfo?
    let documents: [Document]?
    let extractedFields: [String: String]?
    let evidence: [Evidence]?
    let clusterCount: Int?
    let createdAt: Date?
    let updatedAt: Date?
    let assignedTo: Int?
    
    var budgetDisplay: String {
        if let min = budgetMin, let max = budgetMax {
            if min == max {
                return formatCurrency(min)
            }
            return "\(formatCurrency(min)) - \(formatCurrency(max))"
        } else if let min = budgetMin {
            return "À partir de \(formatCurrency(min))"
        } else if let max = budgetMax {
            return "Jusqu'à \(formatCurrency(max))"
        }
        return "Non spécifié"
    }
    
    var scorePercentage: Int {
        Int((score ?? 0) * 100)
    }
    
    var deadlineStatus: DeadlineStatus {
        guard let deadline = deadline else { return .none }
        let daysUntil = Calendar.current.dateComponents([.day], from: Date(), to: deadline).day ?? 0
        
        if daysUntil < 0 { return .passed }
        if daysUntil <= 3 { return .urgent }
        if daysUntil <= 7 { return .soon }
        return .normal
    }
    
    private func formatCurrency(_ value: Double) -> String {
        let formatter = NumberFormatter()
        formatter.numberStyle = .currency
        formatter.currencyCode = "EUR"
        formatter.maximumFractionDigits = 0
        return formatter.string(from: NSNumber(value: value)) ?? "\(Int(value))€"
    }
}

enum OpportunityStatus: String, Codable, CaseIterable, Sendable {
    case new = "new"
    case reviewed = "reviewed"
    case interested = "interested"
    case applied = "applied"
    case rejected = "rejected"
    case won = "won"
    case lost = "lost"
    
    var displayName: String {
        switch self {
        case .new: return "Nouveau"
        case .reviewed: return "Vu"
        case .interested: return "Intéressé"
        case .applied: return "Candidaté"
        case .rejected: return "Rejeté"
        case .won: return "Gagné"
        case .lost: return "Perdu"
        }
    }
    
    var color: String {
        switch self {
        case .new: return "blue"
        case .reviewed: return "gray"
        case .interested: return "orange"
        case .applied: return "purple"
        case .rejected: return "red"
        case .won: return "green"
        case .lost: return "gray"
        }
    }
}

enum DeadlineStatus {
    case none
    case passed
    case urgent
    case soon
    case normal
}

// MARK: - Contact Info
struct ContactInfo: Codable, Equatable, Sendable {
    let name: String?
    let email: String?
    let phone: String?
    let organization: String?
    let role: String?
}

// MARK: - Document
struct Document: Codable, Identifiable, Equatable, Sendable {
    let id: Int
    let name: String
    let url: String?
    let type: String?
    let size: Int?
    
    var sizeDisplay: String {
        guard let size = size else { return "" }
        let formatter = ByteCountFormatter()
        formatter.countStyle = .file
        return formatter.string(fromByteCount: Int64(size))
    }
}

// MARK: - Evidence
struct Evidence: Codable, Identifiable, Equatable, Sendable {
    var id: String { url ?? UUID().uuidString }
    let snippet: String
    let url: String?
    let source: String?
    let confidence: Double?
}

// MARK: - Dossier (IA Result)
struct Dossier: Codable, Identifiable, Equatable, Sendable {
    let id: Int
    let title: String
    let objective: String?
    let entity: String?
    let status: DossierStatus?
    let briefShort: String?
    let briefLong: String?
    let confidence: Double?
    let score: Double?
    let contacts: [RankedContact]?
    let timeline: [TimelineEvent]?
    let documents: [Document]?
    let sources: [String]?
    let evidence: [Evidence]?
    let enrichedViaWeb: Bool?
    let createdAt: Date?
    let updatedAt: Date?
    
    var confidencePercentage: Int {
        Int((confidence ?? 0) * 100)
    }
}

enum DossierStatus: String, Codable, CaseIterable, Sendable {
    case pending = "PENDING"
    case processing = "PROCESSING"
    case ready = "READY"
    case failed = "FAILED"
    
    var displayName: String {
        switch self {
        case .pending: return "En attente"
        case .processing: return "En cours"
        case .ready: return "Prêt"
        case .failed: return "Échec"
        }
    }
}

// MARK: - Ranked Contact
struct RankedContact: Codable, Identifiable, Equatable, Sendable {
    let id: Int
    let name: String?
    let email: String?
    let phone: String?
    let role: String?
    let organization: String?
    let rank: Int?
    let relevance: Double?
}

// MARK: - Timeline Event
struct TimelineEvent: Codable, Identifiable, Equatable, Sendable {
    let id: Int
    let title: String
    let date: Date?
    let description: String?
    let type: String?
    let importance: String?
}

// MARK: - Artist Analysis
struct ArtistAnalysis: Codable, Identifiable, Equatable, Sendable {
    let id: Int
    let artistName: String
    let spotifyId: String?
    let imageUrl: String?
    let mainGenre: String?
    let genres: [String]?
    let popularity: Int?
    let followers: Int?
    let feeMin: Double?
    let feeMax: Double?
    let score: Int?
    let predictions: [ArtistPrediction]?
    let analysis: String?
    let createdAt: Date?
    let updatedAt: Date?
    
    var feeRange: String {
        if let min = feeMin, let max = feeMax {
            return "\(formatCurrency(min)) - \(formatCurrency(max))"
        }
        return "N/A"
    }
    
    private func formatCurrency(_ value: Double) -> String {
        let formatter = NumberFormatter()
        formatter.numberStyle = .currency
        formatter.currencyCode = "EUR"
        formatter.maximumFractionDigits = 0
        return formatter.string(from: NSNumber(value: value)) ?? "\(Int(value))€"
    }
}

// MARK: - Artist Prediction
struct ArtistPrediction: Codable, Equatable, Sendable {
    let period: String
    let growth: Double
    let confidence: Double?
    let factors: [String]?
}

// MARK: - Collection (Search Run)
struct Collection: Codable, Identifiable, Equatable, Sendable {
    let id: Int
    let name: String?
    let type: CollectionType?
    let status: CollectionStatus
    let config: CollectionConfig?
    let resultsCount: Int?
    let errorMessage: String?
    let duration: Int?
    let logs: [String]?
    let sourcesConsulted: [String]?
    let startedAt: Date?
    let completedAt: Date?
    let createdAt: Date?
    
    var durationDisplay: String {
        guard let duration = duration else { return "" }
        if duration < 60 { return "\(duration)s" }
        if duration < 3600 { return "\(duration / 60)m \(duration % 60)s" }
        return "\(duration / 3600)h \(duration % 3600 / 60)m"
    }
}

enum CollectionType: String, Codable, CaseIterable, Sendable {
    case standard = "standard"
    case ai = "ai"
    
    var displayName: String {
        switch self {
        case .standard: return "Standard"
        case .ai: return "IA"
        }
    }
}

enum CollectionStatus: String, Codable, CaseIterable, Sendable {
    case queued = "QUEUED"
    case running = "RUNNING"
    case done = "DONE"
    case failed = "FAILED"
    case cancelled = "CANCELLED"
    
    var displayName: String {
        switch self {
        case .queued: return "En file"
        case .running: return "En cours"
        case .done: return "Terminé"
        case .failed: return "Échec"
        case .cancelled: return "Annulé"
        }
    }
    
    var isActive: Bool {
        self == .queued || self == .running
    }
}

// MARK: - Collection Config
struct CollectionConfig: Codable, Equatable, Sendable {
    // Standard config
    let keywords: [String]?
    let region: String?
    let city: String?
    let budgetMin: Double?
    let budgetMax: Double?
    
    // AI config
    let objective: String?
    let entities: [String]?
    let period: String?
    let requireContact: Bool?
}

// MARK: - Pagination
struct PaginatedResponse<T: Codable>: Codable {
    let items: [T]
    let total: Int
    let page: Int
    let pageSize: Int
    let totalPages: Int
    
    var hasMore: Bool {
        page < totalPages
    }
}

// MARK: - Filter State
struct OpportunityFilters: Equatable, Sendable {
    var searchText: String = ""
    var scoreMin: Double = 0
    var scoreMax: Double = 1
    var budgetMin: Double? = nil
    var budgetMax: Double? = nil
    var deadlineFrom: Date? = nil
    var deadlineTo: Date? = nil
    var source: String? = nil
    var hasContact: Bool? = nil
    var hasDeadline: Bool? = nil
    var status: OpportunityStatus? = nil
    var sortBy: OpportunitySortOption = .scoreDesc
    
    var isActive: Bool {
        !searchText.isEmpty ||
        scoreMin > 0 ||
        scoreMax < 1 ||
        budgetMin != nil ||
        budgetMax != nil ||
        deadlineFrom != nil ||
        deadlineTo != nil ||
        source != nil ||
        hasContact != nil ||
        hasDeadline != nil ||
        status != nil
    }
    
    func toQueryItems() -> [URLQueryItem] {
        var items: [URLQueryItem] = []
        
        if !searchText.isEmpty {
            items.append(URLQueryItem(name: "search", value: searchText))
        }
        if scoreMin > 0 {
            items.append(URLQueryItem(name: "score_min", value: String(scoreMin)))
        }
        if scoreMax < 1 {
            items.append(URLQueryItem(name: "score_max", value: String(scoreMax)))
        }
        if let budgetMin = budgetMin {
            items.append(URLQueryItem(name: "budget_min", value: String(budgetMin)))
        }
        if let budgetMax = budgetMax {
            items.append(URLQueryItem(name: "budget_max", value: String(budgetMax)))
        }
        if let deadlineFrom = deadlineFrom {
            items.append(URLQueryItem(name: "deadline_from", value: ISO8601DateFormatter().string(from: deadlineFrom)))
        }
        if let deadlineTo = deadlineTo {
            items.append(URLQueryItem(name: "deadline_to", value: ISO8601DateFormatter().string(from: deadlineTo)))
        }
        if let source = source {
            items.append(URLQueryItem(name: "source", value: source))
        }
        if let hasContact = hasContact {
            items.append(URLQueryItem(name: "has_contact", value: String(hasContact)))
        }
        if let hasDeadline = hasDeadline {
            items.append(URLQueryItem(name: "has_deadline", value: String(hasDeadline)))
        }
        if let status = status {
            items.append(URLQueryItem(name: "status", value: status.rawValue))
        }
        
        items.append(URLQueryItem(name: "sort", value: sortBy.rawValue))
        
        return items
    }
    
    mutating func reset() {
        self = OpportunityFilters()
    }
}

enum OpportunitySortOption: String, CaseIterable, Sendable {
    case scoreDesc = "score_desc"
    case scoreAsc = "score_asc"
    case deadlineAsc = "deadline_asc"
    case deadlineDesc = "deadline_desc"
    case budgetDesc = "budget_desc"
    case budgetAsc = "budget_asc"
    case createdDesc = "created_desc"
    case createdAsc = "created_asc"
    
    var displayName: String {
        switch self {
        case .scoreDesc: return "Score ↓"
        case .scoreAsc: return "Score ↑"
        case .deadlineAsc: return "Deadline ↑"
        case .deadlineDesc: return "Deadline ↓"
        case .budgetDesc: return "Budget ↓"
        case .budgetAsc: return "Budget ↑"
        case .createdDesc: return "Récent"
        case .createdAsc: return "Ancien"
        }
    }
}
