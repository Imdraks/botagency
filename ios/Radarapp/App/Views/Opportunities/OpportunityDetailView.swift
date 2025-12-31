// OpportunityDetailView.swift
// Detailed view for a single opportunity with Liquid Glass design

import SwiftUI

struct OpportunityDetailView: View {
    let opportunity: Opportunity
    
    @StateObject private var viewModel: OpportunityDetailViewModel
    @Environment(\.dismiss) private var dismiss
    @EnvironmentObject private var appState: AppState
    
    init(opportunity: Opportunity) {
        self.opportunity = opportunity
        self._viewModel = StateObject(wrappedValue: OpportunityDetailViewModel(opportunity: opportunity))
    }
    
    var body: some View {
        NavigationStack {
            ZStack {
                // Gradient background
                LinearGradient(
                    colors: [scoreColor.opacity(0.3), Color(.systemBackground)],
                    startPoint: .top,
                    endPoint: .center
                )
                .ignoresSafeArea()
                
                ScrollView {
                    VStack(spacing: 20) {
                        // Header Card
                        HeaderSection(opportunity: opportunity)
                        
                        // Quick Actions
                        QuickActionsSection(viewModel: viewModel)
                        
                        // Details sections
                        if let description = opportunity.description, !description.isEmpty {
                            DescriptionSection(text: description)
                        }
                        
                        if let contactInfo = opportunity.contactInfo {
                            ContactSection(contact: contactInfo)
                        }
                        
                        if let documents = opportunity.documents, !documents.isEmpty {
                            DocumentsSection(documents: documents)
                        }
                        
                        if let evidence = opportunity.evidence, !evidence.isEmpty {
                            EvidenceSection(evidence: evidence)
                        }
                        
                        // Metadata
                        MetadataSection(opportunity: opportunity)
                    }
                    .padding()
                }
            }
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    Button { dismiss() } label: {
                        Image(systemName: "xmark.circle.fill")
                            .foregroundStyle(.secondary)
                    }
                }
                
                ToolbarItem(placement: .topBarTrailing) {
                    Menu {
                        Button {
                            viewModel.shareOpportunity()
                        } label: {
                            Label("Partager", systemImage: "square.and.arrow.up")
                        }
                        
                        if let url = opportunity.sourceUrl {
                            Button {
                                viewModel.openSourceURL(url)
                            } label: {
                                Label("Voir la source", systemImage: "globe")
                            }
                        }
                        
                        Divider()
                        
                        Button(role: .destructive) {
                            viewModel.archiveOpportunity()
                        } label: {
                            Label("Archiver", systemImage: "archivebox")
                        }
                    } label: {
                        Image(systemName: "ellipsis.circle")
                    }
                }
            }
        }
    }
    
    private var scoreColor: Color {
        let score = opportunity.scorePercentage
        switch score {
        case 80...100: return .green
        case 60..<80: return .blue
        case 40..<60: return .orange
        default: return .red
        }
    }
}

// MARK: - Header Section
struct HeaderSection: View {
    let opportunity: Opportunity
    
    var body: some View {
        GlassCard(style: .elevated, padding: 20, cornerRadius: 24) {
            VStack(alignment: .leading, spacing: 16) {
                // Score & Status
                HStack {
                    ScoreBadge(opportunity.scorePercentage, size: .large)
                    
                    Spacer()
                    
                    if let status = opportunity.status {
                        StatusBadge(status: status)
                    }
                }
                
                // Title
                Text(opportunity.title)
                    .font(.title2.weight(.bold))
                
                // Organization
                if let organization = opportunity.organization {
                    HStack(spacing: 8) {
                        Image(systemName: "building.2")
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                        
                        Text(organization)
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                    }
                }
                
                Divider()
                
                // Key info grid
                LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 16) {
                    // Location
                    if let location = opportunity.location ?? opportunity.region {
                        InfoCell(
                            icon: "mappin.circle.fill",
                            title: "Localisation",
                            value: location,
                            color: .blue
                        )
                    }
                    
                    // Budget
                    InfoCell(
                        icon: "eurosign.circle.fill",
                        title: "Budget",
                        value: opportunity.budgetDisplay,
                        color: .green
                    )
                    
                    // Deadline
                    if let deadline = opportunity.deadline {
                        InfoCell(
                            icon: "calendar.circle.fill",
                            title: "Deadline",
                            value: formatDate(deadline),
                            color: deadlineColor(for: opportunity.deadlineStatus)
                        )
                    }
                    
                    // Source
                    if let source = opportunity.source {
                        InfoCell(
                            icon: "globe.europe.africa.fill",
                            title: "Source",
                            value: source,
                            color: .purple
                        )
                    }
                }
                
                // Tags
                if let tags = opportunity.tags, !tags.isEmpty {
                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack(spacing: 8) {
                            ForEach(tags, id: \.self) { tag in
                                Text(tag)
                                    .font(.caption.weight(.medium))
                                    .padding(.horizontal, 12)
                                    .padding(.vertical, 6)
                                    .background {
                                        Capsule()
                                            .fill(Color.accentColor.opacity(0.15))
                                    }
                            }
                        }
                    }
                }
            }
        }
    }
    
    private func formatDate(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.dateStyle = .medium
        formatter.locale = Locale(identifier: "fr_FR")
        return formatter.string(from: date)
    }
    
    private func deadlineColor(for status: DeadlineStatus) -> Color {
        switch status {
        case .passed: return .gray
        case .urgent: return .red
        case .soon: return .orange
        case .normal, .none: return .blue
        }
    }
}

// MARK: - Info Cell
struct InfoCell: View {
    let icon: String
    let title: String
    let value: String
    let color: Color
    
    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: icon)
                .font(.title3)
                .foregroundStyle(color)
                .frame(width: 32)
            
            VStack(alignment: .leading, spacing: 2) {
                Text(title)
                    .font(.caption)
                    .foregroundStyle(.secondary)
                
                Text(value)
                    .font(.subheadline.weight(.medium))
                    .lineLimit(1)
            }
            
            Spacer()
        }
    }
}

// MARK: - Quick Actions Section
struct QuickActionsSection: View {
    @ObservedObject var viewModel: OpportunityDetailViewModel
    
    var body: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 12) {
                QuickActionButton(
                    icon: "star.fill",
                    title: "Intéressé",
                    color: .orange,
                    isSelected: viewModel.isInterested
                ) {
                    viewModel.toggleInterested()
                }
                
                QuickActionButton(
                    icon: "paperplane.fill",
                    title: "Candidater",
                    color: .green,
                    isSelected: viewModel.hasApplied
                ) {
                    viewModel.markAsApplied()
                }
                
                QuickActionButton(
                    icon: "brain",
                    title: "Analyse IA",
                    color: .purple,
                    isSelected: false
                ) {
                    viewModel.requestAIAnalysis()
                }
                
                QuickActionButton(
                    icon: "note.text",
                    title: "Notes",
                    color: .blue,
                    isSelected: false
                ) {
                    viewModel.showNotes = true
                }
            }
        }
    }
}

struct QuickActionButton: View {
    let icon: String
    let title: String
    let color: Color
    let isSelected: Bool
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            VStack(spacing: 8) {
                Image(systemName: icon)
                    .font(.title2)
                    .foregroundStyle(isSelected ? .white : color)
                
                Text(title)
                    .font(.caption.weight(.medium))
                    .foregroundStyle(isSelected ? .white : .primary)
            }
            .frame(width: 80, height: 80)
            .background {
                RoundedRectangle(cornerRadius: 16, style: .continuous)
                    .fill(isSelected ? color : color.opacity(0.15))
            }
        }
    }
}

// MARK: - Description Section
struct DescriptionSection: View {
    let text: String
    @State private var isExpanded = false
    
    var body: some View {
        GlassCard {
            VStack(alignment: .leading, spacing: 12) {
                HStack {
                    Label("Description", systemImage: "doc.text")
                        .font(.headline)
                    
                    Spacer()
                    
                    if text.count > 300 {
                        Button {
                            withAnimation(.spring(response: 0.3)) {
                                isExpanded.toggle()
                            }
                        } label: {
                            Image(systemName: isExpanded ? "chevron.up" : "chevron.down")
                                .foregroundStyle(.secondary)
                        }
                    }
                }
                
                Text(text)
                    .font(.body)
                    .lineLimit(isExpanded ? nil : 5)
            }
        }
    }
}

// MARK: - Contact Section
struct ContactSection: View {
    let contact: ContactInfo
    
    var body: some View {
        GlassCard {
            VStack(alignment: .leading, spacing: 16) {
                Label("Contact", systemImage: "person.crop.circle")
                    .font(.headline)
                
                VStack(alignment: .leading, spacing: 12) {
                    if let name = contact.name {
                        ContactRow(icon: "person", text: name)
                    }
                    
                    if let role = contact.role {
                        ContactRow(icon: "briefcase", text: role)
                    }
                    
                    if let email = contact.email {
                        Button {
                            if let url = URL(string: "mailto:\(email)") {
                                UIApplication.shared.open(url)
                            }
                        } label: {
                            ContactRow(icon: "envelope", text: email, isAction: true)
                        }
                    }
                    
                    if let phone = contact.phone {
                        Button {
                            if let url = URL(string: "tel:\(phone)") {
                                UIApplication.shared.open(url)
                            }
                        } label: {
                            ContactRow(icon: "phone", text: phone, isAction: true)
                        }
                    }
                }
            }
        }
    }
}

struct ContactRow: View {
    let icon: String
    let text: String
    var isAction: Bool = false
    
    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: icon)
                .font(.subheadline)
                .foregroundStyle(.secondary)
                .frame(width: 24)
            
            Text(text)
                .font(.subheadline)
                .foregroundStyle(isAction ? .accentColor : .primary)
            
            Spacer()
            
            if isAction {
                Image(systemName: "chevron.right")
                    .font(.caption)
                    .foregroundStyle(.tertiary)
            }
        }
    }
}

// MARK: - Documents Section
struct DocumentsSection: View {
    let documents: [Document]
    
    var body: some View {
        GlassCard {
            VStack(alignment: .leading, spacing: 16) {
                Label("Documents", systemImage: "doc.on.doc")
                    .font(.headline)
                
                ForEach(documents) { doc in
                    HStack {
                        Image(systemName: documentIcon(for: doc.type))
                            .foregroundStyle(.accentColor)
                        
                        VStack(alignment: .leading) {
                            Text(doc.name)
                                .font(.subheadline)
                                .lineLimit(1)
                            
                            if !doc.sizeDisplay.isEmpty {
                                Text(doc.sizeDisplay)
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                            }
                        }
                        
                        Spacer()
                        
                        Image(systemName: "arrow.down.circle")
                            .foregroundStyle(.secondary)
                    }
                    
                    if doc.id != documents.last?.id {
                        Divider()
                    }
                }
            }
        }
    }
    
    private func documentIcon(for type: String?) -> String {
        switch type?.lowercased() {
        case "pdf": return "doc.richtext"
        case "doc", "docx": return "doc.text"
        case "xls", "xlsx": return "tablecells"
        default: return "doc"
        }
    }
}

// MARK: - Evidence Section
struct EvidenceSection: View {
    let evidence: [Evidence]
    @State private var expanded = false
    
    var body: some View {
        GlassCard {
            VStack(alignment: .leading, spacing: 16) {
                HStack {
                    Label("Preuves & Sources", systemImage: "checkmark.seal")
                        .font(.headline)
                    
                    Spacer()
                    
                    Text("\(evidence.count)")
                        .font(.caption.weight(.bold))
                        .padding(.horizontal, 8)
                        .padding(.vertical, 4)
                        .background {
                            Capsule()
                                .fill(Color.green.opacity(0.2))
                        }
                }
                
                ForEach(evidence.prefix(expanded ? evidence.count : 3)) { item in
                    VStack(alignment: .leading, spacing: 8) {
                        Text(item.snippet)
                            .font(.subheadline)
                            .lineLimit(expanded ? nil : 2)
                        
                        HStack {
                            if let source = item.source {
                                Text(source)
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                            }
                            
                            Spacer()
                            
                            if let confidence = item.confidence {
                                Text("\(Int(confidence * 100))% confiance")
                                    .font(.caption.weight(.medium))
                                    .foregroundStyle(.green)
                            }
                        }
                    }
                    .padding(12)
                    .background {
                        RoundedRectangle(cornerRadius: 8, style: .continuous)
                            .fill(Color(.secondarySystemBackground))
                    }
                }
                
                if evidence.count > 3 {
                    Button {
                        withAnimation { expanded.toggle() }
                    } label: {
                        Text(expanded ? "Voir moins" : "Voir tout (\(evidence.count))")
                            .font(.subheadline.weight(.medium))
                    }
                }
            }
        }
    }
}

// MARK: - Metadata Section
struct MetadataSection: View {
    let opportunity: Opportunity
    
    var body: some View {
        GlassCard(style: .default, padding: 16) {
            VStack(spacing: 8) {
                if let created = opportunity.createdAt {
                    HStack {
                        Text("Créé le")
                            .foregroundStyle(.secondary)
                        Spacer()
                        Text(formatDate(created))
                    }
                    .font(.caption)
                }
                
                if let updated = opportunity.updatedAt {
                    HStack {
                        Text("Mis à jour")
                            .foregroundStyle(.secondary)
                        Spacer()
                        Text(formatDate(updated))
                    }
                    .font(.caption)
                }
                
                if let clusters = opportunity.clusterCount, clusters > 0 {
                    HStack {
                        Text("Opportunités similaires")
                            .foregroundStyle(.secondary)
                        Spacer()
                        Text("\(clusters)")
                    }
                    .font(.caption)
                }
            }
        }
    }
    
    private func formatDate(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.dateStyle = .short
        formatter.timeStyle = .short
        formatter.locale = Locale(identifier: "fr_FR")
        return formatter.string(from: date)
    }
}

// MARK: - ViewModel
@MainActor
final class OpportunityDetailViewModel: ObservableObject {
    let opportunity: Opportunity
    
    @Published var isInterested = false
    @Published var hasApplied = false
    @Published var showNotes = false
    
    init(opportunity: Opportunity) {
        self.opportunity = opportunity
        self.isInterested = opportunity.status == .interested
        self.hasApplied = opportunity.status == .applied
    }
    
    func toggleInterested() {
        isInterested.toggle()
        updateStatus(isInterested ? .interested : .reviewed)
    }
    
    func markAsApplied() {
        hasApplied = true
        updateStatus(.applied)
    }
    
    func requestAIAnalysis() {
        Logger.info("Requesting AI analysis for opportunity \(opportunity.id)")
        // TODO: Implement AI analysis request
    }
    
    func shareOpportunity() {
        let text = """
        \(opportunity.title)
        \(opportunity.organization ?? "")
        \(opportunity.budgetDisplay)
        """
        
        let activityVC = UIActivityViewController(
            activityItems: [text],
            applicationActivities: nil
        )
        
        if let windowScene = UIApplication.shared.connectedScenes.first as? UIWindowScene,
           let window = windowScene.windows.first,
           let rootVC = window.rootViewController {
            rootVC.present(activityVC, animated: true)
        }
    }
    
    func openSourceURL(_ urlString: String) {
        guard let url = URL(string: urlString) else { return }
        UIApplication.shared.open(url)
    }
    
    func archiveOpportunity() {
        updateStatus(.rejected)
    }
    
    private func updateStatus(_ status: OpportunityStatus) {
        Task {
            do {
                let endpoint = Endpoint(
                    path: "opportunities/\(opportunity.id)/status",
                    method: .patch,
                    body: ["status": status.rawValue]
                )
                _ = try await NetworkService.shared.request(endpoint, responseType: Opportunity.self)
                Logger.info("Updated opportunity \(opportunity.id) status to \(status)")
            } catch {
                Logger.error("Failed to update status: \(error)")
            }
        }
    }
}

// MARK: - Preview
#Preview {
    OpportunityDetailView(opportunity: Opportunity(
        id: 1,
        title: "Festival International de Jazz - Appel à artistes 2025",
        description: "Le Festival International de Jazz recherche des artistes émergents pour sa programmation 2025. Budget conséquent pour les artistes sélectionnés.",
        source: "Culture.gouv.fr",
        sourceUrl: "https://example.com",
        organization: "Mairie de Paris",
        location: "Paris",
        region: "Île-de-France",
        budgetMin: 5000,
        budgetMax: 15000,
        deadline: Date().addingTimeInterval(86400 * 14),
        score: 0.87,
        status: .new,
        tags: ["Jazz", "Festival", "Musique", "2025"],
        hasContact: true,
        hasDeadline: true,
        contactInfo: ContactInfo(name: "Marie Dupont", email: "contact@festival.fr", phone: "01 23 45 67 89", organization: "Festival Jazz", role: "Directrice artistique"),
        documents: nil,
        extractedFields: nil,
        evidence: [
            Evidence(snippet: "Budget alloué de 5000€ à 15000€ par artiste", url: nil, source: "Page officielle", confidence: 0.95),
            Evidence(snippet: "Date limite de candidature: dans 2 semaines", url: nil, source: "PDF Appel", confidence: 0.88)
        ],
        clusterCount: 3,
        createdAt: Date().addingTimeInterval(-86400 * 2),
        updatedAt: Date(),
        assignedTo: nil
    ))
    .environmentObject(AppState())
}
