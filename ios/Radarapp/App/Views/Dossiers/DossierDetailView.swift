// DossierDetailView.swift
// Detailed view for AI-generated dossier with rich content

import SwiftUI

struct DossierDetailView: View {
    let dossier: Dossier
    
    @Environment(\.dismiss) private var dismiss
    @State private var selectedTab = 0
    
    var body: some View {
        NavigationStack {
            ZStack {
                // Background gradient based on status
                LinearGradient(
                    colors: [statusColor.opacity(0.2), Color(.systemBackground)],
                    startPoint: .top,
                    endPoint: .center
                )
                .ignoresSafeArea()
                
                ScrollView {
                    VStack(spacing: 20) {
                        // Header
                        DossierHeaderCard(dossier: dossier)
                        
                        // Tab selector
                        TabSelector(selectedTab: $selectedTab, tabs: ["Résumé", "Timeline", "Contacts", "Sources"])
                        
                        // Tab content
                        Group {
                            switch selectedTab {
                            case 0:
                                BriefSection(dossier: dossier)
                            case 1:
                                TimelineSection(timeline: dossier.timeline ?? [])
                            case 2:
                                ContactsSection(contacts: dossier.contacts ?? [])
                            case 3:
                                SourcesSection(sources: dossier.sources ?? [], evidence: dossier.evidence ?? [])
                            default:
                                EmptyView()
                            }
                        }
                        .animation(.easeInOut(duration: 0.2), value: selectedTab)
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
                            refreshDossier()
                        } label: {
                            Label("Actualiser", systemImage: "arrow.clockwise")
                        }
                        
                        Button {
                            shareDossier()
                        } label: {
                            Label("Partager", systemImage: "square.and.arrow.up")
                        }
                        
                        Button {
                            exportAsPDF()
                        } label: {
                            Label("Exporter PDF", systemImage: "doc.richtext")
                        }
                    } label: {
                        Image(systemName: "ellipsis.circle")
                    }
                }
            }
        }
    }
    
    private var statusColor: Color {
        switch dossier.status {
        case .pending: return .orange
        case .processing: return .blue
        case .ready: return .green
        case .failed: return .red
        case .none: return .gray
        }
    }
    
    private func refreshDossier() {
        Logger.info("Refreshing dossier \(dossier.id)")
    }
    
    private func shareDossier() {
        Logger.info("Sharing dossier \(dossier.id)")
    }
    
    private func exportAsPDF() {
        Logger.info("Exporting dossier \(dossier.id) as PDF")
    }
}

// MARK: - Tab Selector
struct TabSelector: View {
    @Binding var selectedTab: Int
    let tabs: [String]
    
    @Namespace private var animation
    
    var body: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 4) {
                ForEach(Array(tabs.enumerated()), id: \.offset) { index, tab in
                    Button {
                        withAnimation(.spring(response: 0.3, dampingFraction: 0.7)) {
                            selectedTab = index
                        }
                    } label: {
                        Text(tab)
                            .font(.subheadline.weight(selectedTab == index ? .semibold : .regular))
                            .foregroundStyle(selectedTab == index ? .white : .primary)
                            .padding(.horizontal, 16)
                            .padding(.vertical, 10)
                            .background {
                                if selectedTab == index {
                                    Capsule()
                                        .fill(Color.accentColor)
                                        .matchedGeometryEffect(id: "tab", in: animation)
                                }
                            }
                    }
                }
            }
            .padding(4)
            .background {
                Capsule()
                    .fill(Color(.secondarySystemBackground))
            }
        }
    }
}

// MARK: - Dossier Header Card
struct DossierHeaderCard: View {
    let dossier: Dossier
    
    var body: some View {
        GlassCard(style: .elevated, padding: 20, cornerRadius: 24) {
            VStack(alignment: .leading, spacing: 16) {
                // Status & Confidence
                HStack {
                    if let status = dossier.status {
                        DossierStatusBadge(status: status)
                    }
                    
                    Spacer()
                    
                    if dossier.confidence != nil {
                        ConfidenceBadge(confidence: dossier.confidencePercentage)
                    }
                }
                
                // Title & Entity
                VStack(alignment: .leading, spacing: 4) {
                    Text(dossier.title)
                        .font(.title2.weight(.bold))
                    
                    if let entity = dossier.entity {
                        HStack(spacing: 6) {
                            Image(systemName: "person.circle.fill")
                                .foregroundStyle(.secondary)
                            
                            Text(entity)
                                .foregroundStyle(.secondary)
                        }
                        .font(.subheadline)
                    }
                }
                
                // Objective
                if let objective = dossier.objective {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Objectif")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                        
                        Text(objective)
                            .font(.subheadline)
                    }
                    .padding(12)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .background {
                        RoundedRectangle(cornerRadius: 12, style: .continuous)
                            .fill(Color(.secondarySystemBackground))
                    }
                }
                
                // Stats row
                HStack(spacing: 24) {
                    StatItem(
                        icon: "person.2",
                        value: "\(dossier.contacts?.count ?? 0)",
                        label: "Contacts"
                    )
                    
                    StatItem(
                        icon: "calendar",
                        value: "\(dossier.timeline?.count ?? 0)",
                        label: "Événements"
                    )
                    
                    StatItem(
                        icon: "doc.text",
                        value: "\(dossier.documents?.count ?? 0)",
                        label: "Documents"
                    )
                    
                    if dossier.enrichedViaWeb == true {
                        StatItem(
                            icon: "globe",
                            value: "✓",
                            label: "Web"
                        )
                    }
                }
            }
        }
    }
}

struct StatItem: View {
    let icon: String
    let value: String
    let label: String
    
    var body: some View {
        VStack(spacing: 4) {
            HStack(spacing: 4) {
                Image(systemName: icon)
                    .font(.caption)
                    .foregroundStyle(.secondary)
                
                Text(value)
                    .font(.headline)
            }
            
            Text(label)
                .font(.caption2)
                .foregroundStyle(.tertiary)
        }
    }
}

// MARK: - Brief Section
struct BriefSection: View {
    let dossier: Dossier
    @State private var showFullBrief = false
    
    var body: some View {
        VStack(spacing: 16) {
            // Short brief
            if let shortBrief = dossier.briefShort {
                GlassCard {
                    VStack(alignment: .leading, spacing: 12) {
                        HStack {
                            Label("Résumé", systemImage: "text.alignleft")
                                .font(.headline)
                            
                            Spacer()
                            
                            Image(systemName: "sparkles")
                                .foregroundStyle(.purple)
                        }
                        
                        Text(shortBrief)
                            .font(.body)
                    }
                }
            }
            
            // Long brief (expandable)
            if let longBrief = dossier.briefLong {
                GlassCard {
                    VStack(alignment: .leading, spacing: 12) {
                        Button {
                            withAnimation(.spring(response: 0.3)) {
                                showFullBrief.toggle()
                            }
                        } label: {
                            HStack {
                                Label("Analyse détaillée", systemImage: "doc.richtext")
                                    .font(.headline)
                                    .foregroundStyle(.primary)
                                
                                Spacer()
                                
                                Image(systemName: showFullBrief ? "chevron.up" : "chevron.down")
                                    .foregroundStyle(.secondary)
                            }
                        }
                        
                        if showFullBrief {
                            Divider()
                            
                            Text(longBrief)
                                .font(.body)
                        }
                    }
                }
            }
            
            // Score breakdown if available
            if let score = dossier.score {
                ScoreBreakdownCard(score: score)
            }
        }
    }
}

struct ScoreBreakdownCard: View {
    let score: Double
    
    var body: some View {
        GlassCard {
            VStack(alignment: .leading, spacing: 16) {
                HStack {
                    Label("Score de pertinence", systemImage: "chart.bar")
                        .font(.headline)
                    
                    Spacer()
                    
                    Text("\(Int(score * 100))%")
                        .font(.title2.weight(.bold))
                        .foregroundStyle(.green)
                }
                
                // Score bar
                GeometryReader { geometry in
                    ZStack(alignment: .leading) {
                        RoundedRectangle(cornerRadius: 4)
                            .fill(Color(.systemGray5))
                            .frame(height: 8)
                        
                        RoundedRectangle(cornerRadius: 4)
                            .fill(
                                LinearGradient(
                                    colors: [.green, .blue],
                                    startPoint: .leading,
                                    endPoint: .trailing
                                )
                            )
                            .frame(width: geometry.size.width * score, height: 8)
                    }
                }
                .frame(height: 8)
            }
        }
    }
}

// MARK: - Timeline Section
struct TimelineSection: View {
    let timeline: [TimelineEvent]
    
    var body: some View {
        if timeline.isEmpty {
            GlassCard {
                VStack(spacing: 12) {
                    Image(systemName: "calendar.badge.clock")
                        .font(.largeTitle)
                        .foregroundStyle(.secondary)
                    
                    Text("Aucun événement")
                        .font(.headline)
                    
                    Text("Aucun événement n'a été identifié pour cette entité.")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                        .multilineTextAlignment(.center)
                }
                .frame(maxWidth: .infinity)
                .padding(.vertical, 20)
            }
        } else {
            VStack(spacing: 0) {
                ForEach(Array(timeline.enumerated()), id: \.element.id) { index, event in
                    TimelineEventRow(event: event, isLast: index == timeline.count - 1)
                }
            }
            .padding()
            .background {
                GlassBackground(style: .card, cornerRadius: 16)
            }
        }
    }
}

struct TimelineEventRow: View {
    let event: TimelineEvent
    let isLast: Bool
    
    var body: some View {
        HStack(alignment: .top, spacing: 16) {
            // Timeline indicator
            VStack(spacing: 0) {
                Circle()
                    .fill(event.importance == "high" ? Color.orange : Color.accentColor)
                    .frame(width: 12, height: 12)
                
                if !isLast {
                    Rectangle()
                        .fill(Color(.separator))
                        .frame(width: 2)
                        .frame(maxHeight: .infinity)
                }
            }
            
            // Content
            VStack(alignment: .leading, spacing: 6) {
                if let date = event.date {
                    Text(formatDate(date))
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
                
                Text(event.title)
                    .font(.subheadline.weight(.medium))
                
                if let description = event.description {
                    Text(description)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }
            .padding(.bottom, isLast ? 0 : 20)
            
            Spacer()
        }
    }
    
    private func formatDate(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.dateStyle = .medium
        formatter.locale = Locale(identifier: "fr_FR")
        return formatter.string(from: date)
    }
}

// MARK: - Contacts Section
struct ContactsSection: View {
    let contacts: [RankedContact]
    
    var body: some View {
        if contacts.isEmpty {
            GlassCard {
                VStack(spacing: 12) {
                    Image(systemName: "person.2.slash")
                        .font(.largeTitle)
                        .foregroundStyle(.secondary)
                    
                    Text("Aucun contact")
                        .font(.headline)
                    
                    Text("Aucun contact n'a été identifié pour cette entité.")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                        .multilineTextAlignment(.center)
                }
                .frame(maxWidth: .infinity)
                .padding(.vertical, 20)
            }
        } else {
            VStack(spacing: 12) {
                ForEach(contacts) { contact in
                    RankedContactCard(contact: contact)
                }
            }
        }
    }
}

struct RankedContactCard: View {
    let contact: RankedContact
    
    var body: some View {
        GlassCard {
            HStack(spacing: 16) {
                // Avatar
                ZStack {
                    Circle()
                        .fill(Color.accentColor.gradient)
                        .frame(width: 50, height: 50)
                    
                    Text(initials)
                        .font(.headline)
                        .foregroundStyle(.white)
                }
                
                // Info
                VStack(alignment: .leading, spacing: 4) {
                    HStack {
                        Text(contact.name ?? "Inconnu")
                            .font(.headline)
                        
                        if let rank = contact.rank {
                            Text("#\(rank)")
                                .font(.caption.weight(.bold))
                                .foregroundStyle(.white)
                                .padding(.horizontal, 6)
                                .padding(.vertical, 2)
                                .background {
                                    Capsule()
                                        .fill(rankColor(rank))
                                }
                        }
                    }
                    
                    if let role = contact.role {
                        Text(role)
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                    }
                    
                    if let relevance = contact.relevance {
                        HStack(spacing: 4) {
                            Image(systemName: "star.fill")
                                .font(.caption2)
                            Text("\(Int(relevance * 100))% pertinence")
                                .font(.caption)
                        }
                        .foregroundStyle(.orange)
                    }
                }
                
                Spacer()
                
                // Actions
                VStack(spacing: 8) {
                    if contact.email != nil {
                        Button {
                            if let email = contact.email, let url = URL(string: "mailto:\(email)") {
                                UIApplication.shared.open(url)
                            }
                        } label: {
                            Image(systemName: "envelope.fill")
                                .foregroundStyle(.accentColor)
                        }
                    }
                    
                    if contact.phone != nil {
                        Button {
                            if let phone = contact.phone, let url = URL(string: "tel:\(phone)") {
                                UIApplication.shared.open(url)
                            }
                        } label: {
                            Image(systemName: "phone.fill")
                                .foregroundStyle(.green)
                        }
                    }
                }
            }
        }
    }
    
    private var initials: String {
        let parts = (contact.name ?? "?").components(separatedBy: " ")
        if parts.count >= 2 {
            return String(parts[0].prefix(1) + parts[1].prefix(1)).uppercased()
        }
        return String((contact.name ?? "?").prefix(2)).uppercased()
    }
    
    private func rankColor(_ rank: Int) -> Color {
        switch rank {
        case 1: return .yellow
        case 2: return .gray
        case 3: return .orange
        default: return .blue
        }
    }
}

// MARK: - Sources Section
struct SourcesSection: View {
    let sources: [String]
    let evidence: [Evidence]
    
    var body: some View {
        VStack(spacing: 16) {
            // Sources list
            if !sources.isEmpty {
                GlassCard {
                    VStack(alignment: .leading, spacing: 12) {
                        Label("Sources utilisées", systemImage: "link")
                            .font(.headline)
                        
                        ForEach(sources, id: \.self) { source in
                            HStack {
                                Image(systemName: "globe")
                                    .foregroundStyle(.secondary)
                                
                                Text(source)
                                    .font(.subheadline)
                                    .lineLimit(1)
                                
                                Spacer()
                                
                                Image(systemName: "arrow.up.right")
                                    .font(.caption)
                                    .foregroundStyle(.tertiary)
                            }
                            .padding(.vertical, 4)
                        }
                    }
                }
            }
            
            // Evidence
            if !evidence.isEmpty {
                GlassCard {
                    VStack(alignment: .leading, spacing: 12) {
                        Label("Preuves extraites", systemImage: "checkmark.seal")
                            .font(.headline)
                        
                        ForEach(evidence) { item in
                            VStack(alignment: .leading, spacing: 6) {
                                Text(item.snippet)
                                    .font(.subheadline)
                                
                                HStack {
                                    if let source = item.source {
                                        Text(source)
                                            .font(.caption)
                                            .foregroundStyle(.secondary)
                                    }
                                    
                                    Spacer()
                                    
                                    if let confidence = item.confidence {
                                        Text("\(Int(confidence * 100))%")
                                            .font(.caption.weight(.bold))
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
                    }
                }
            }
        }
    }
}

// MARK: - Preview
#Preview {
    DossierDetailView(dossier: Dossier(
        id: 1,
        title: "Analyse: Festival Jazz Paris 2025",
        objective: "Identifier les opportunités de partenariat et les contacts clés",
        entity: "Festival Jazz Paris",
        status: .ready,
        briefShort: "Le Festival Jazz Paris est un événement annuel majeur attirant plus de 50 000 visiteurs. Budget estimé de plusieurs millions d'euros.",
        briefLong: "Analyse détaillée complète avec historique, contacts, et recommandations stratégiques...",
        confidence: 0.87,
        score: 0.82,
        contacts: [
            RankedContact(id: 1, name: "Marie Dupont", role: "Directrice artistique", email: "marie@festival.fr", phone: "0123456789", rank: 1, relevance: 0.95),
            RankedContact(id: 2, name: "Pierre Martin", role: "Responsable partenariats", email: "pierre@festival.fr", phone: nil, rank: 2, relevance: 0.78)
        ],
        timeline: [
            TimelineEvent(id: 1, title: "Création du festival", date: Date().addingTimeInterval(-86400 * 365 * 5), description: "Première édition avec 10 000 visiteurs", importance: "high"),
            TimelineEvent(id: 2, title: "Extension internationale", date: Date().addingTimeInterval(-86400 * 365 * 2), description: "Partenariats avec festivals européens", importance: "medium")
        ],
        documents: nil,
        sources: ["festivalJazzParis.fr", "culture.gouv.fr", "lemonde.fr"],
        evidence: [
            Evidence(snippet: "Budget 2024: 2.5M€ dont 800K€ pour les artistes", url: nil, source: "Rapport annuel", confidence: 0.92)
        ],
        enrichedViaWeb: true,
        createdAt: Date().addingTimeInterval(-86400),
        updatedAt: Date()
    ))
    .environmentObject(AppState())
}
