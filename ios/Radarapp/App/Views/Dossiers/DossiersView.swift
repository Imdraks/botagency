// DossiersView.swift
// Dossiers list with AI analysis results and Liquid Glass design

import SwiftUI

struct DossiersView: View {
    @StateObject private var viewModel = DossiersViewModel()
    @EnvironmentObject private var appState: AppState
    
    @State private var selectedDossier: Dossier?
    @State private var showNewDossier = false
    
    var body: some View {
        NavigationStack {
            ZStack {
                Color(.systemGroupedBackground)
                    .ignoresSafeArea()
                
                if viewModel.isLoading && viewModel.dossiers.isEmpty {
                    DossiersSkeletonView()
                } else if viewModel.dossiers.isEmpty && !viewModel.isLoading {
                    EmptyStateView(
                        icon: "folder.badge.plus",
                        title: "Aucun dossier",
                        message: "Créez un nouveau dossier pour analyser des entités avec l'IA.",
                        actionTitle: "Créer un dossier"
                    ) {
                        showNewDossier = true
                    }
                } else {
                    ScrollView {
                        LazyVStack(spacing: 16) {
                            // Filter tabs
                            DossierFilterTabs(viewModel: viewModel)
                                .padding(.horizontal)
                            
                            // Dossiers list
                            ForEach(viewModel.filteredDossiers) { dossier in
                                DossierCard(dossier: dossier)
                                    .onTapGesture {
                                        selectedDossier = dossier
                                    }
                                    .padding(.horizontal)
                            }
                        }
                        .padding(.vertical)
                    }
                    .refreshable {
                        await viewModel.refresh()
                    }
                }
            }
            .navigationTitle("Dossiers")
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button {
                        showNewDossier = true
                    } label: {
                        Image(systemName: "plus.circle.fill")
                    }
                }
            }
            .sheet(item: $selectedDossier) { dossier in
                DossierDetailView(dossier: dossier)
            }
            .sheet(isPresented: $showNewDossier) {
                NewDossierSheet()
            }
        }
        .task {
            await viewModel.loadInitial()
        }
    }
}

// MARK: - Filter Tabs
struct DossierFilterTabs: View {
    @ObservedObject var viewModel: DossiersViewModel
    
    var body: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 8) {
                FilterChip(
                    title: "Tous",
                    count: viewModel.dossiers.count,
                    isSelected: viewModel.selectedFilter == nil
                ) {
                    viewModel.selectedFilter = nil
                }
                
                ForEach(DossierStatus.allCases, id: \.self) { status in
                    FilterChip(
                        title: status.displayName,
                        count: viewModel.countForStatus(status),
                        isSelected: viewModel.selectedFilter == status,
                        color: status.color
                    ) {
                        viewModel.selectedFilter = status
                    }
                }
            }
        }
    }
}

struct FilterChip: View {
    let title: String
    let count: Int
    let isSelected: Bool
    var color: Color = .accentColor
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            HStack(spacing: 6) {
                Text(title)
                    .font(.subheadline.weight(.medium))
                
                if count > 0 {
                    Text("\(count)")
                        .font(.caption.weight(.bold))
                        .padding(.horizontal, 6)
                        .padding(.vertical, 2)
                        .background {
                            Capsule()
                                .fill(isSelected ? Color.white.opacity(0.3) : Color.secondary.opacity(0.2))
                        }
                }
            }
            .foregroundStyle(isSelected ? .white : .primary)
            .padding(.horizontal, 16)
            .padding(.vertical, 10)
            .background {
                Capsule()
                    .fill(isSelected ? color : Color(.secondarySystemBackground))
            }
        }
    }
}

// MARK: - Dossier Card
struct DossierCard: View {
    let dossier: Dossier
    
    var body: some View {
        GlassCard(style: .card, padding: 0, cornerRadius: 20) {
            VStack(alignment: .leading, spacing: 0) {
                // Header with status indicator
                HStack(spacing: 12) {
                    // Status indicator
                    Circle()
                        .fill(statusColor)
                        .frame(width: 10, height: 10)
                    
                    VStack(alignment: .leading, spacing: 2) {
                        Text(dossier.title)
                            .font(.headline)
                            .lineLimit(1)
                        
                        if let entity = dossier.entity {
                            Text(entity)
                                .font(.subheadline)
                                .foregroundStyle(.secondary)
                        }
                    }
                    
                    Spacer()
                    
                    // Confidence badge
                    if dossier.confidence != nil {
                        ConfidenceBadge(confidence: dossier.confidencePercentage)
                    }
                }
                .padding(16)
                
                // Brief preview
                if let brief = dossier.briefShort {
                    Text(brief)
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                        .lineLimit(2)
                        .padding(.horizontal, 16)
                        .padding(.bottom, 12)
                }
                
                Divider()
                    .padding(.horizontal, 16)
                
                // Footer with metadata
                HStack {
                    // Status label
                    if let status = dossier.status {
                        DossierStatusBadge(status: status)
                    }
                    
                    Spacer()
                    
                    // Enrichment indicator
                    if dossier.enrichedViaWeb == true {
                        HStack(spacing: 4) {
                            Image(systemName: "globe")
                                .font(.caption)
                            Text("Enrichi")
                                .font(.caption)
                        }
                        .foregroundStyle(.green)
                    }
                    
                    // Date
                    if let date = dossier.createdAt {
                        Text(formatRelativeDate(date))
                            .font(.caption)
                            .foregroundStyle(.tertiary)
                    }
                }
                .padding(16)
                
                // Processing indicator
                if dossier.status == .processing {
                    ProgressView()
                        .frame(maxWidth: .infinity)
                        .padding(.bottom, 12)
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
    
    private func formatRelativeDate(_ date: Date) -> String {
        let formatter = RelativeDateTimeFormatter()
        formatter.unitsStyle = .abbreviated
        return formatter.localizedString(for: date, relativeTo: Date())
    }
}

// MARK: - Confidence Badge
struct ConfidenceBadge: View {
    let confidence: Int
    
    var body: some View {
        HStack(spacing: 4) {
            Image(systemName: "brain")
                .font(.caption2)
            
            Text("\(confidence)%")
                .font(.caption.weight(.bold))
        }
        .foregroundStyle(confidenceColor)
        .padding(.horizontal, 8)
        .padding(.vertical, 4)
        .background {
            Capsule()
                .fill(confidenceColor.opacity(0.15))
        }
    }
    
    private var confidenceColor: Color {
        switch confidence {
        case 80...100: return .green
        case 60..<80: return .blue
        case 40..<60: return .orange
        default: return .red
        }
    }
}

// MARK: - Dossier Status Badge
struct DossierStatusBadge: View {
    let status: DossierStatus
    
    var body: some View {
        HStack(spacing: 4) {
            statusIcon
                .font(.caption)
            
            Text(status.displayName)
                .font(.caption.weight(.medium))
        }
        .foregroundStyle(status.color)
    }
    
    @ViewBuilder
    private var statusIcon: some View {
        switch status {
        case .pending:
            Image(systemName: "clock")
        case .processing:
            ProgressView()
                .scaleEffect(0.7)
        case .ready:
            Image(systemName: "checkmark.circle.fill")
        case .failed:
            Image(systemName: "xmark.circle.fill")
        }
    }
}

// MARK: - Skeleton View
struct DossiersSkeletonView: View {
    var body: some View {
        ScrollView {
            VStack(spacing: 16) {
                // Filter tabs skeleton
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 8) {
                        ForEach(0..<4, id: \.self) { _ in
                            SkeletonView(height: 36, cornerRadius: 18)
                                .frame(width: 90)
                        }
                    }
                    .padding(.horizontal)
                }
                
                // Cards skeleton
                ForEach(0..<5, id: \.self) { _ in
                    VStack(alignment: .leading, spacing: 12) {
                        HStack {
                            Circle()
                                .fill(Color.gray.opacity(0.2))
                                .frame(width: 10, height: 10)
                            
                            VStack(alignment: .leading, spacing: 6) {
                                SkeletonView(height: 16)
                                    .frame(width: 180)
                                SkeletonView(height: 12)
                                    .frame(width: 100)
                            }
                            
                            Spacer()
                            
                            SkeletonView(height: 24, cornerRadius: 12)
                                .frame(width: 60)
                        }
                        
                        SkeletonView(height: 14)
                            .frame(width: 250)
                        
                        SkeletonView(height: 1)
                        
                        HStack {
                            SkeletonView(height: 20, cornerRadius: 10)
                                .frame(width: 80)
                            Spacer()
                            SkeletonView(height: 12)
                                .frame(width: 60)
                        }
                    }
                    .padding(16)
                    .background {
                        RoundedRectangle(cornerRadius: 20, style: .continuous)
                            .fill(.regularMaterial)
                    }
                    .padding(.horizontal)
                }
            }
            .padding(.vertical)
        }
    }
}

// MARK: - New Dossier Sheet
struct NewDossierSheet: View {
    @Environment(\.dismiss) private var dismiss
    @State private var title = ""
    @State private var entity = ""
    @State private var objective = ""
    @State private var isLoading = false
    
    var body: some View {
        NavigationStack {
            Form {
                Section("Informations") {
                    TextField("Titre du dossier", text: $title)
                    TextField("Entité (artiste, organisation...)", text: $entity)
                }
                
                Section("Objectif de recherche") {
                    TextEditor(text: $objective)
                        .frame(minHeight: 100)
                }
                
                Section {
                    Text("L'IA va rechercher et analyser les informations disponibles sur l'entité spécifiée.")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }
            .navigationTitle("Nouveau dossier")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    Button("Annuler") { dismiss() }
                }
                
                ToolbarItem(placement: .topBarTrailing) {
                    Button {
                        createDossier()
                    } label: {
                        if isLoading {
                            ProgressView()
                        } else {
                            Text("Créer")
                                .bold()
                        }
                    }
                    .disabled(title.isEmpty || entity.isEmpty || isLoading)
                }
            }
        }
    }
    
    private func createDossier() {
        isLoading = true
        
        Task {
            do {
                let body = [
                    "title": title,
                    "entity": entity,
                    "objective": objective
                ]
                
                let endpoint = Endpoint(path: "dossiers", method: .post, body: body)
                _ = try await NetworkService.shared.request(endpoint, responseType: Dossier.self)
                
                dismiss()
            } catch {
                Logger.error("Failed to create dossier: \(error)")
                isLoading = false
            }
        }
    }
}

// MARK: - Dossier Status Extension
extension DossierStatus {
    var displayName: String {
        switch self {
        case .pending: return "En attente"
        case .processing: return "Analyse..."
        case .ready: return "Prêt"
        case .failed: return "Échec"
        }
    }
    
    var color: Color {
        switch self {
        case .pending: return .orange
        case .processing: return .blue
        case .ready: return .green
        case .failed: return .red
        }
    }
}

// MARK: - ViewModel
@MainActor
final class DossiersViewModel: ObservableObject {
    @Published var dossiers: [Dossier] = []
    @Published var isLoading = false
    @Published var selectedFilter: DossierStatus?
    @Published var error: Error?
    
    var filteredDossiers: [Dossier] {
        guard let filter = selectedFilter else { return dossiers }
        return dossiers.filter { $0.status == filter }
    }
    
    func countForStatus(_ status: DossierStatus) -> Int {
        dossiers.filter { $0.status == status }.count
    }
    
    func loadInitial() async {
        guard dossiers.isEmpty else { return }
        await refresh()
    }
    
    func refresh() async {
        isLoading = true
        
        do {
            let endpoint = Endpoint(path: "dossiers")
            let response = try await NetworkService.shared.request(
                endpoint,
                responseType: PaginatedResponse<Dossier>.self
            )
            dossiers = response.items
        } catch {
            self.error = error
            Logger.error("Failed to fetch dossiers: \(error)")
        }
        
        isLoading = false
    }
}

// MARK: - Preview
#Preview {
    DossiersView()
        .environmentObject(AppState())
}
