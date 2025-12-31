// NewCollectionView.swift
// Create new collection from RSS/HTML sources

import SwiftUI

struct NewCollectionView: View {
    @StateObject private var viewModel = NewCollectionViewModel()
    @EnvironmentObject private var appState: AppState
    
    var body: some View {
        NavigationStack {
            ZStack {
                Color(.systemGroupedBackground)
                    .ignoresSafeArea()
                
                ScrollView {
                    VStack(spacing: 24) {
                        // Header illustration
                        CollectionHeader()
                        
                        // Source type selector
                        SourceTypeSelector(viewModel: viewModel)
                        
                        // Source configuration based on type
                        switch viewModel.sourceType {
                        case .rss:
                            RSSSourceForm(viewModel: viewModel)
                        case .html:
                            HTMLSourceForm(viewModel: viewModel)
                        case .email:
                            EmailSourceForm(viewModel: viewModel)
                        case .api:
                            APISourceForm(viewModel: viewModel)
                        }
                        
                        // Collection options
                        CollectionOptionsSection(viewModel: viewModel)
                        
                        // Submit button
                        GlassButton(
                            "Lancer la collecte",
                            icon: "antenna.radiowaves.left.and.right",
                            isLoading: viewModel.isLoading
                        ) {
                            viewModel.startCollection()
                        }
                        .padding(.horizontal)
                        .disabled(!viewModel.isValid)
                    }
                    .padding(.vertical)
                }
            }
            .navigationTitle("Nouvelle collecte")
            .alert("Erreur", isPresented: $viewModel.showError) {
                Button("OK") {}
            } message: {
                Text(viewModel.errorMessage)
            }
            .alert("Succès", isPresented: $viewModel.showSuccess) {
                Button("OK") {
                    viewModel.reset()
                }
            } message: {
                Text("La collecte a été lancée avec succès. Les résultats apparaîtront dans l'onglet Opportunités.")
            }
        }
    }
}

// MARK: - Collection Header
struct CollectionHeader: View {
    var body: some View {
        VStack(spacing: 12) {
            ZStack {
                Circle()
                    .fill(
                        LinearGradient(
                            colors: [.blue, .purple],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )
                    .frame(width: 80, height: 80)
                
                Image(systemName: "plus.circle.fill")
                    .font(.system(size: 36))
                    .foregroundStyle(.white)
            }
            .shadow(color: .purple.opacity(0.3), radius: 20, x: 0, y: 10)
            
            VStack(spacing: 4) {
                Text("Ajouter une source")
                    .font(.title2.weight(.bold))
                
                Text("Configurez une nouvelle source de collecte d'opportunités")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
                    .multilineTextAlignment(.center)
            }
            .padding(.horizontal)
        }
        .padding(.vertical, 20)
    }
}

// MARK: - Source Type Selector
struct SourceTypeSelector: View {
    @ObservedObject var viewModel: NewCollectionViewModel
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Type de source")
                .font(.headline)
                .padding(.horizontal)
            
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 12) {
                    ForEach(SourceType.allCases) { type in
                        SourceTypeCard(
                            type: type,
                            isSelected: viewModel.sourceType == type
                        ) {
                            withAnimation(.spring(response: 0.3)) {
                                viewModel.sourceType = type
                            }
                        }
                    }
                }
                .padding(.horizontal)
            }
        }
    }
}

struct SourceTypeCard: View {
    let type: SourceType
    let isSelected: Bool
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            VStack(spacing: 12) {
                Image(systemName: type.icon)
                    .font(.title)
                    .foregroundStyle(isSelected ? .white : type.color)
                
                VStack(spacing: 2) {
                    Text(type.title)
                        .font(.subheadline.weight(.semibold))
                    
                    Text(type.subtitle)
                        .font(.caption2)
                        .foregroundStyle(isSelected ? .white.opacity(0.8) : .secondary)
                }
            }
            .foregroundStyle(isSelected ? .white : .primary)
            .frame(width: 100, height: 110)
            .background {
                RoundedRectangle(cornerRadius: 16, style: .continuous)
                    .fill(isSelected ? type.color : Color(.secondarySystemBackground))
            }
            .overlay {
                if isSelected {
                    RoundedRectangle(cornerRadius: 16, style: .continuous)
                        .strokeBorder(.white.opacity(0.3), lineWidth: 1)
                }
            }
        }
    }
}

// MARK: - Source Type Enum
enum SourceType: String, CaseIterable, Identifiable {
    case rss = "RSS"
    case html = "HTML"
    case email = "EMAIL"
    case api = "API"
    
    var id: String { rawValue }
    
    var title: String {
        switch self {
        case .rss: return "Flux RSS"
        case .html: return "Page Web"
        case .email: return "Email"
        case .api: return "API"
        }
    }
    
    var subtitle: String {
        switch self {
        case .rss: return "Automatique"
        case .html: return "Scraping"
        case .email: return "Gmail/IMAP"
        case .api: return "REST/JSON"
        }
    }
    
    var icon: String {
        switch self {
        case .rss: return "dot.radiowaves.up.forward"
        case .html: return "globe"
        case .email: return "envelope"
        case .api: return "curlybraces"
        }
    }
    
    var color: Color {
        switch self {
        case .rss: return .orange
        case .html: return .blue
        case .email: return .red
        case .api: return .purple
        }
    }
}

// MARK: - RSS Source Form
struct RSSSourceForm: View {
    @ObservedObject var viewModel: NewCollectionViewModel
    
    var body: some View {
        GlassCard {
            VStack(alignment: .leading, spacing: 16) {
                Label("Configuration RSS", systemImage: "dot.radiowaves.up.forward")
                    .font(.headline)
                
                // URL field
                VStack(alignment: .leading, spacing: 6) {
                    Text("URL du flux RSS")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                    
                    GlassTextField(
                        "https://example.com/rss.xml",
                        text: $viewModel.rssUrl,
                        icon: "link",
                        keyboardType: .URL
                    )
                    .textInputAutocapitalization(.never)
                    .autocorrectionDisabled()
                }
                
                // Name field
                VStack(alignment: .leading, spacing: 6) {
                    Text("Nom de la source")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                    
                    GlassTextField(
                        "Culture.gouv.fr",
                        text: $viewModel.sourceName,
                        icon: "tag"
                    )
                }
                
                // Validate button
                Button {
                    viewModel.validateRSSUrl()
                } label: {
                    HStack {
                        if viewModel.isValidating {
                            ProgressView()
                                .scaleEffect(0.8)
                        } else {
                            Image(systemName: viewModel.isRSSValid ? "checkmark.circle.fill" : "questionmark.circle")
                        }
                        
                        Text(viewModel.isRSSValid ? "Flux valide" : "Valider le flux")
                    }
                    .font(.subheadline.weight(.medium))
                    .foregroundStyle(viewModel.isRSSValid ? .green : .accentColor)
                }
            }
        }
        .padding(.horizontal)
    }
}

// MARK: - HTML Source Form
struct HTMLSourceForm: View {
    @ObservedObject var viewModel: NewCollectionViewModel
    
    var body: some View {
        GlassCard {
            VStack(alignment: .leading, spacing: 16) {
                Label("Configuration Web", systemImage: "globe")
                    .font(.headline)
                
                // URL field
                VStack(alignment: .leading, spacing: 6) {
                    Text("URL de la page")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                    
                    GlassTextField(
                        "https://example.com/opportunities",
                        text: $viewModel.htmlUrl,
                        icon: "link",
                        keyboardType: .URL
                    )
                    .textInputAutocapitalization(.never)
                    .autocorrectionDisabled()
                }
                
                // CSS Selector (optional)
                VStack(alignment: .leading, spacing: 6) {
                    HStack {
                        Text("Sélecteur CSS")
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                        
                        Text("(optionnel)")
                            .font(.caption)
                            .foregroundStyle(.tertiary)
                    }
                    
                    GlassTextField(
                        ".opportunity-card, article.item",
                        text: $viewModel.cssSelector,
                        icon: "chevron.left.forwardslash.chevron.right"
                    )
                    .textInputAutocapitalization(.never)
                    .autocorrectionDisabled()
                }
                
                // Name field
                VStack(alignment: .leading, spacing: 6) {
                    Text("Nom de la source")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                    
                    GlassTextField(
                        "Site officiel",
                        text: $viewModel.sourceName,
                        icon: "tag"
                    )
                }
            }
        }
        .padding(.horizontal)
    }
}

// MARK: - Email Source Form
struct EmailSourceForm: View {
    @ObservedObject var viewModel: NewCollectionViewModel
    
    var body: some View {
        GlassCard {
            VStack(alignment: .leading, spacing: 16) {
                Label("Configuration Email", systemImage: "envelope")
                    .font(.headline)
                
                // Provider selector
                VStack(alignment: .leading, spacing: 6) {
                    Text("Fournisseur")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                    
                    Picker("Provider", selection: $viewModel.emailProvider) {
                        Text("Gmail").tag("gmail")
                        Text("Outlook").tag("outlook")
                        Text("IMAP").tag("imap")
                    }
                    .pickerStyle(.segmented)
                }
                
                // Email field
                VStack(alignment: .leading, spacing: 6) {
                    Text("Adresse email")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                    
                    GlassTextField(
                        "vous@gmail.com",
                        text: $viewModel.email,
                        icon: "envelope",
                        keyboardType: .emailAddress
                    )
                    .textContentType(.emailAddress)
                    .textInputAutocapitalization(.never)
                    .autocorrectionDisabled()
                }
                
                // Filter keywords
                VStack(alignment: .leading, spacing: 6) {
                    Text("Mots-clés de filtre")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                    
                    GlassTextField(
                        "appel à projets, subvention, festival",
                        text: $viewModel.emailKeywords,
                        icon: "magnifyingglass"
                    )
                }
                
                // OAuth button for Gmail
                if viewModel.emailProvider == "gmail" {
                    Button {
                        viewModel.authenticateGmail()
                    } label: {
                        HStack {
                            Image(systemName: "g.circle.fill")
                            Text("Connecter Gmail")
                        }
                        .font(.subheadline.weight(.medium))
                        .foregroundStyle(.white)
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 12)
                        .background {
                            RoundedRectangle(cornerRadius: 10, style: .continuous)
                                .fill(Color.red.gradient)
                        }
                    }
                }
            }
        }
        .padding(.horizontal)
    }
}

// MARK: - API Source Form
struct APISourceForm: View {
    @ObservedObject var viewModel: NewCollectionViewModel
    
    var body: some View {
        GlassCard {
            VStack(alignment: .leading, spacing: 16) {
                Label("Configuration API", systemImage: "curlybraces")
                    .font(.headline)
                
                // URL field
                VStack(alignment: .leading, spacing: 6) {
                    Text("URL de l'API")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                    
                    GlassTextField(
                        "https://api.example.com/v1/opportunities",
                        text: $viewModel.apiUrl,
                        icon: "link",
                        keyboardType: .URL
                    )
                    .textInputAutocapitalization(.never)
                    .autocorrectionDisabled()
                }
                
                // Headers
                VStack(alignment: .leading, spacing: 6) {
                    HStack {
                        Text("Headers (JSON)")
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                        
                        Text("(optionnel)")
                            .font(.caption)
                            .foregroundStyle(.tertiary)
                    }
                    
                    TextEditor(text: $viewModel.apiHeaders)
                        .frame(height: 80)
                        .font(.system(.caption, design: .monospaced))
                        .padding(8)
                        .background {
                            RoundedRectangle(cornerRadius: 8, style: .continuous)
                                .fill(Color(.secondarySystemBackground))
                        }
                }
                
                // Name field
                VStack(alignment: .leading, spacing: 6) {
                    Text("Nom de la source")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                    
                    GlassTextField(
                        "API Custom",
                        text: $viewModel.sourceName,
                        icon: "tag"
                    )
                }
            }
        }
        .padding(.horizontal)
    }
}

// MARK: - Collection Options Section
struct CollectionOptionsSection: View {
    @ObservedObject var viewModel: NewCollectionViewModel
    
    var body: some View {
        GlassCard {
            VStack(alignment: .leading, spacing: 16) {
                Label("Options", systemImage: "gearshape")
                    .font(.headline)
                
                // Frequency
                VStack(alignment: .leading, spacing: 6) {
                    Text("Fréquence de collecte")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                    
                    Picker("Frequency", selection: $viewModel.frequency) {
                        Text("Toutes les heures").tag("hourly")
                        Text("Quotidien").tag("daily")
                        Text("Hebdomadaire").tag("weekly")
                        Text("Mensuel").tag("monthly")
                        Text("Manuel").tag("manual")
                    }
                    .pickerStyle(.menu)
                }
                
                Divider()
                
                // Auto-scoring
                Toggle(isOn: $viewModel.autoScore) {
                    VStack(alignment: .leading, spacing: 2) {
                        Text("Scoring automatique")
                            .font(.subheadline)
                        
                        Text("L'IA attribue un score de pertinence")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                }
                
                // Deduplication
                Toggle(isOn: $viewModel.deduplication) {
                    VStack(alignment: .leading, spacing: 2) {
                        Text("Déduplication")
                            .font(.subheadline)
                        
                        Text("Évite les doublons avec les sources existantes")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                }
                
                // AI Enrichment
                Toggle(isOn: $viewModel.aiEnrichment) {
                    VStack(alignment: .leading, spacing: 2) {
                        Text("Enrichissement IA")
                            .font(.subheadline)
                        
                        Text("Extrait contacts, budgets, dates automatiquement")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                }
            }
        }
        .padding(.horizontal)
    }
}

// MARK: - ViewModel
@MainActor
final class NewCollectionViewModel: ObservableObject {
    // Source type
    @Published var sourceType: SourceType = .rss
    
    // RSS fields
    @Published var rssUrl = ""
    @Published var isRSSValid = false
    @Published var isValidating = false
    
    // HTML fields
    @Published var htmlUrl = ""
    @Published var cssSelector = ""
    
    // Email fields
    @Published var emailProvider = "gmail"
    @Published var email = ""
    @Published var emailKeywords = ""
    
    // API fields
    @Published var apiUrl = ""
    @Published var apiHeaders = "{\n  \"Authorization\": \"Bearer YOUR_TOKEN\"\n}"
    
    // Common fields
    @Published var sourceName = ""
    
    // Options
    @Published var frequency = "daily"
    @Published var autoScore = true
    @Published var deduplication = true
    @Published var aiEnrichment = true
    
    // State
    @Published var isLoading = false
    @Published var showError = false
    @Published var errorMessage = ""
    @Published var showSuccess = false
    
    var isValid: Bool {
        switch sourceType {
        case .rss:
            return !rssUrl.isEmpty && !sourceName.isEmpty && isRSSValid
        case .html:
            return !htmlUrl.isEmpty && !sourceName.isEmpty
        case .email:
            return !email.isEmpty && email.contains("@")
        case .api:
            return !apiUrl.isEmpty && !sourceName.isEmpty
        }
    }
    
    func validateRSSUrl() {
        guard !rssUrl.isEmpty else { return }
        
        isValidating = true
        
        Task {
            do {
                let endpoint = Endpoint(
                    path: "sources/validate",
                    method: .post,
                    body: ["url": rssUrl, "type": "RSS"]
                )
                
                struct ValidationResponse: Codable {
                    let valid: Bool
                    let title: String?
                }
                
                let response = try await NetworkService.shared.request(
                    endpoint,
                    responseType: ValidationResponse.self
                )
                
                isRSSValid = response.valid
                if sourceName.isEmpty, let title = response.title {
                    sourceName = title
                }
            } catch {
                isRSSValid = false
                errorMessage = "Impossible de valider le flux RSS"
                showError = true
            }
            
            isValidating = false
        }
    }
    
    func authenticateGmail() {
        Logger.info("Gmail OAuth requested")
        // TODO: Implement Gmail OAuth flow
    }
    
    func startCollection() {
        isLoading = true
        
        Task {
            do {
                var config: [String: Any] = [
                    "name": sourceName,
                    "type": sourceType.rawValue,
                    "frequency": frequency,
                    "auto_score": autoScore,
                    "deduplication": deduplication,
                    "ai_enrichment": aiEnrichment
                ]
                
                switch sourceType {
                case .rss:
                    config["url"] = rssUrl
                case .html:
                    config["url"] = htmlUrl
                    config["css_selector"] = cssSelector
                case .email:
                    config["provider"] = emailProvider
                    config["email"] = email
                    config["keywords"] = emailKeywords
                case .api:
                    config["url"] = apiUrl
                    config["headers"] = apiHeaders
                }
                
                let endpoint = Endpoint(
                    path: "sources",
                    method: .post,
                    body: config
                )
                
                _ = try await NetworkService.shared.request(endpoint, responseType: Source.self)
                
                showSuccess = true
            } catch {
                errorMessage = error.localizedDescription
                showError = true
            }
            
            isLoading = false
        }
    }
    
    func reset() {
        sourceType = .rss
        rssUrl = ""
        htmlUrl = ""
        cssSelector = ""
        email = ""
        emailKeywords = ""
        apiUrl = ""
        sourceName = ""
        isRSSValid = false
    }
}

// MARK: - Source Model
struct Source: Codable, Identifiable {
    let id: Int
    let name: String
    let type: String
    let url: String?
    let isActive: Bool
    let lastFetch: Date?
    let itemCount: Int?
}

// MARK: - Preview
#Preview {
    NewCollectionView()
        .environmentObject(AppState())
}
