// OpportunitiesView.swift
// Main opportunities list with search, filters, and pull-to-refresh

import SwiftUI
import SwiftData

struct OpportunitiesView: View {
    @StateObject private var viewModel = OpportunitiesViewModel()
    @EnvironmentObject private var appState: AppState
    @Environment(\.modelContext) private var modelContext
    
    @State private var showFilters = false
    @State private var selectedOpportunity: Opportunity?
    
    var body: some View {
        NavigationStack {
            ZStack {
                // Background
                Color(.systemGroupedBackground)
                    .ignoresSafeArea()
                
                if viewModel.isLoading && viewModel.opportunities.isEmpty {
                    // Initial loading state
                    OpportunitiesSkeletonView()
                } else if viewModel.opportunities.isEmpty && !viewModel.isLoading {
                    // Empty state
                    EmptyStateView(
                        icon: "magnifyingglass.circle",
                        title: "Aucune opportunité",
                        message: "Aucune opportunité ne correspond à vos critères de recherche.",
                        actionTitle: "Actualiser"
                    ) {
                        Task { await viewModel.refresh() }
                    }
                } else {
                    // Opportunities list
                    ScrollView {
                        LazyVStack(spacing: 12) {
                            // Stats header
                            StatsHeader(viewModel: viewModel)
                                .padding(.horizontal)
                            
                            // Opportunities
                            ForEach(viewModel.opportunities) { opportunity in
                                OpportunityCard(opportunity: opportunity)
                                    .onTapGesture {
                                        selectedOpportunity = opportunity
                                    }
                                    .padding(.horizontal)
                            }
                            
                            // Load more indicator
                            if viewModel.hasMorePages {
                                ProgressView()
                                    .padding()
                                    .onAppear {
                                        Task { await viewModel.loadMore() }
                                    }
                            }
                        }
                        .padding(.vertical)
                    }
                    .refreshable {
                        await viewModel.refresh()
                    }
                }
            }
            .navigationTitle("Opportunités")
            .searchable(
                text: $viewModel.searchQuery,
                placement: .navigationBarDrawer(displayMode: .automatic),
                prompt: "Rechercher..."
            )
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    HStack(spacing: 12) {
                        // Filter button
                        Button {
                            showFilters = true
                        } label: {
                            Image(systemName: viewModel.hasActiveFilters ? "line.3.horizontal.decrease.circle.fill" : "line.3.horizontal.decrease.circle")
                                .foregroundStyle(viewModel.hasActiveFilters ? .accent : .primary)
                        }
                        
                        // Sort menu
                        Menu {
                            ForEach(OpportunitySortOption.allCases) { option in
                                Button {
                                    viewModel.sortOption = option
                                } label: {
                                    HStack {
                                        Text(option.title)
                                        if viewModel.sortOption == option {
                                            Image(systemName: "checkmark")
                                        }
                                    }
                                }
                            }
                        } label: {
                            Image(systemName: "arrow.up.arrow.down.circle")
                        }
                    }
                }
            }
            .sheet(isPresented: $showFilters) {
                FilterSheet(viewModel: viewModel)
            }
            .sheet(item: $selectedOpportunity) { opportunity in
                OpportunityDetailView(opportunity: opportunity)
            }
        }
        .task {
            await viewModel.loadInitial()
        }
    }
}

// MARK: - Stats Header
struct StatsHeader: View {
    @ObservedObject var viewModel: OpportunitiesViewModel
    
    var body: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 12) {
                StatCard(
                    title: "Total",
                    value: "\(viewModel.totalCount)",
                    icon: "doc.text",
                    color: .blue
                )
                
                StatCard(
                    title: "Score > 80%",
                    value: "\(viewModel.highScoreCount)",
                    icon: "star.fill",
                    color: .green
                )
                
                StatCard(
                    title: "Urgent",
                    value: "\(viewModel.urgentCount)",
                    icon: "clock.badge.exclamationmark",
                    color: .orange
                )
                
                StatCard(
                    title: "Nouveau",
                    value: "\(viewModel.newCount)",
                    icon: "sparkle",
                    color: .purple
                )
            }
        }
    }
}

struct StatCard: View {
    let title: String
    let value: String
    let icon: String
    let color: Color
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: icon)
                    .font(.caption.weight(.semibold))
                    .foregroundStyle(color)
                
                Spacer()
                
                Text(value)
                    .font(.title2.weight(.bold))
            }
            
            Text(title)
                .font(.caption)
                .foregroundStyle(.secondary)
        }
        .padding(12)
        .frame(width: 120)
        .background {
            RoundedRectangle(cornerRadius: 12, style: .continuous)
                .fill(.regularMaterial)
        }
    }
}

// MARK: - Opportunity Card
struct OpportunityCard: View {
    let opportunity: Opportunity
    @EnvironmentObject private var appState: AppState
    
    var body: some View {
        GlassCard(style: .card, padding: 0, cornerRadius: 16) {
            VStack(alignment: .leading, spacing: 0) {
                // Header
                HStack(alignment: .top) {
                    VStack(alignment: .leading, spacing: 4) {
                        Text(opportunity.title)
                            .font(.headline)
                            .lineLimit(2)
                        
                        if let organization = opportunity.organization {
                            Text(organization)
                                .font(.subheadline)
                                .foregroundStyle(.secondary)
                        }
                    }
                    
                    Spacer()
                    
                    ScoreBadge(opportunity.scorePercentage)
                }
                .padding(16)
                
                Divider()
                    .padding(.horizontal, 16)
                
                // Details
                VStack(spacing: 12) {
                    // Location & Budget
                    HStack(spacing: 16) {
                        if let location = opportunity.location ?? opportunity.region {
                            Label(location, systemImage: "mappin.circle.fill")
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }
                        
                        Spacer()
                        
                        Text(opportunity.budgetDisplay)
                            .font(.caption.weight(.medium))
                            .foregroundStyle(.green)
                    }
                    
                    // Deadline & Status
                    HStack {
                        if let deadline = opportunity.deadline {
                            DeadlineBadge(deadline: deadline, status: opportunity.deadlineStatus)
                        }
                        
                        Spacer()
                        
                        if let status = opportunity.status {
                            StatusBadge(status: status)
                        }
                    }
                    
                    // Tags
                    if let tags = opportunity.tags, !tags.isEmpty {
                        ScrollView(.horizontal, showsIndicators: false) {
                            HStack(spacing: 6) {
                                ForEach(tags.prefix(5), id: \.self) { tag in
                                    Text(tag)
                                        .font(.caption2.weight(.medium))
                                        .padding(.horizontal, 8)
                                        .padding(.vertical, 4)
                                        .background {
                                            Capsule()
                                                .fill(Color.accentColor.opacity(0.15))
                                        }
                                }
                            }
                        }
                    }
                }
                .padding(16)
            }
        }
    }
}

// MARK: - Deadline Badge
struct DeadlineBadge: View {
    let deadline: Date
    let status: DeadlineStatus
    
    var body: some View {
        HStack(spacing: 4) {
            Image(systemName: statusIcon)
                .font(.caption2)
            
            Text(formattedDeadline)
                .font(.caption.weight(.medium))
        }
        .foregroundStyle(statusColor)
        .padding(.horizontal, 8)
        .padding(.vertical, 4)
        .background {
            Capsule()
                .fill(statusColor.opacity(0.15))
        }
    }
    
    var formattedDeadline: String {
        let formatter = RelativeDateTimeFormatter()
        formatter.unitsStyle = .short
        return formatter.localizedString(for: deadline, relativeTo: Date())
    }
    
    var statusIcon: String {
        switch status {
        case .passed: return "exclamationmark.circle.fill"
        case .urgent: return "clock.badge.exclamationmark"
        case .soon: return "clock"
        case .normal, .none: return "calendar"
        }
    }
    
    var statusColor: Color {
        switch status {
        case .passed: return .gray
        case .urgent: return .red
        case .soon: return .orange
        case .normal, .none: return .blue
        }
    }
}

// MARK: - Skeleton View
struct OpportunitiesSkeletonView: View {
    var body: some View {
        ScrollView {
            VStack(spacing: 12) {
                // Stats skeleton
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 12) {
                        ForEach(0..<4, id: \.self) { _ in
                            SkeletonView(height: 70, cornerRadius: 12)
                                .frame(width: 120)
                        }
                    }
                    .padding(.horizontal)
                }
                
                // Cards skeleton
                ForEach(0..<5, id: \.self) { _ in
                    VStack(alignment: .leading, spacing: 12) {
                        HStack {
                            VStack(alignment: .leading, spacing: 8) {
                                SkeletonView(height: 18)
                                    .frame(width: 200)
                                SkeletonView(height: 14)
                                    .frame(width: 120)
                            }
                            Spacer()
                            SkeletonView(height: 28, cornerRadius: 14)
                                .frame(width: 50)
                        }
                        
                        SkeletonView(height: 1)
                        
                        HStack {
                            SkeletonView(height: 14)
                                .frame(width: 100)
                            Spacer()
                            SkeletonView(height: 14)
                                .frame(width: 80)
                        }
                        
                        HStack(spacing: 8) {
                            ForEach(0..<3, id: \.self) { _ in
                                SkeletonView(height: 22, cornerRadius: 11)
                                    .frame(width: 60)
                            }
                        }
                    }
                    .padding(16)
                    .background {
                        RoundedRectangle(cornerRadius: 16, style: .continuous)
                            .fill(.regularMaterial)
                    }
                    .padding(.horizontal)
                }
            }
            .padding(.vertical)
        }
    }
}

// MARK: - Filter Sheet
struct FilterSheet: View {
    @ObservedObject var viewModel: OpportunitiesViewModel
    @Environment(\.dismiss) private var dismiss
    
    var body: some View {
        NavigationStack {
            Form {
                // Status filter
                Section("Statut") {
                    ForEach(OpportunityStatus.allCases, id: \.self) { status in
                        Toggle(status.displayName, isOn: Binding(
                            get: { viewModel.selectedStatuses.contains(status) },
                            set: { isSelected in
                                if isSelected {
                                    viewModel.selectedStatuses.insert(status)
                                } else {
                                    viewModel.selectedStatuses.remove(status)
                                }
                            }
                        ))
                    }
                }
                
                // Score filter
                Section("Score minimum") {
                    Slider(value: $viewModel.minScore, in: 0...100, step: 10)
                    Text("Score ≥ \(Int(viewModel.minScore))%")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
                
                // Deadline filter
                Section("Deadline") {
                    Toggle("Avec deadline uniquement", isOn: $viewModel.onlyWithDeadline)
                    Toggle("Non expirées uniquement", isOn: $viewModel.excludeExpired)
                }
                
                // Region filter
                Section("Région") {
                    TextField("Filtrer par région...", text: $viewModel.regionFilter)
                }
                
                // Reset
                Section {
                    Button("Réinitialiser les filtres", role: .destructive) {
                        viewModel.resetFilters()
                    }
                }
            }
            .navigationTitle("Filtres")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    Button("Annuler") { dismiss() }
                }
                ToolbarItem(placement: .topBarTrailing) {
                    Button("Appliquer") {
                        Task { await viewModel.applyFilters() }
                        dismiss()
                    }
                    .bold()
                }
            }
        }
    }
}

// MARK: - Sort Options
enum OpportunitySortOption: String, CaseIterable, Identifiable {
    case scoreDesc = "score_desc"
    case scoreAsc = "score_asc"
    case deadlineAsc = "deadline_asc"
    case deadlineDesc = "deadline_desc"
    case dateDesc = "date_desc"
    case dateAsc = "date_asc"
    
    var id: String { rawValue }
    
    var title: String {
        switch self {
        case .scoreDesc: return "Score (décroissant)"
        case .scoreAsc: return "Score (croissant)"
        case .deadlineAsc: return "Deadline (proche)"
        case .deadlineDesc: return "Deadline (lointain)"
        case .dateDesc: return "Plus récent"
        case .dateAsc: return "Plus ancien"
        }
    }
}

// MARK: - ViewModel
@MainActor
final class OpportunitiesViewModel: ObservableObject {
    // Data
    @Published var opportunities: [Opportunity] = []
    @Published var isLoading = false
    @Published var error: Error?
    
    // Search & Filters
    @Published var searchQuery = "" {
        didSet { debounceSearch() }
    }
    @Published var sortOption: OpportunitySortOption = .scoreDesc {
        didSet { Task { await refresh() } }
    }
    @Published var selectedStatuses: Set<OpportunityStatus> = []
    @Published var minScore: Double = 0
    @Published var onlyWithDeadline = false
    @Published var excludeExpired = false
    @Published var regionFilter = ""
    
    // Pagination
    @Published var currentPage = 1
    @Published var totalCount = 0
    @Published var hasMorePages = false
    
    // Stats
    var highScoreCount: Int { opportunities.filter { ($0.score ?? 0) >= 0.8 }.count }
    var urgentCount: Int { opportunities.filter { $0.deadlineStatus == .urgent }.count }
    var newCount: Int { opportunities.filter { $0.status == .new }.count }
    
    var hasActiveFilters: Bool {
        !selectedStatuses.isEmpty || minScore > 0 || onlyWithDeadline || excludeExpired || !regionFilter.isEmpty
    }
    
    private var searchTask: Task<Void, Never>?
    
    // MARK: - Data Loading
    func loadInitial() async {
        guard opportunities.isEmpty else { return }
        await refresh()
    }
    
    func refresh() async {
        currentPage = 1
        isLoading = true
        
        do {
            let response = try await fetchOpportunities(page: 1)
            opportunities = response.items
            totalCount = response.total
            hasMorePages = response.hasMore
        } catch {
            self.error = error
            Logger.error("Failed to fetch opportunities: \(error)")
        }
        
        isLoading = false
    }
    
    func loadMore() async {
        guard hasMorePages && !isLoading else { return }
        
        currentPage += 1
        isLoading = true
        
        do {
            let response = try await fetchOpportunities(page: currentPage)
            opportunities.append(contentsOf: response.items)
            hasMorePages = response.hasMore
        } catch {
            currentPage -= 1
            self.error = error
        }
        
        isLoading = false
    }
    
    func applyFilters() async {
        await refresh()
    }
    
    func resetFilters() {
        selectedStatuses = []
        minScore = 0
        onlyWithDeadline = false
        excludeExpired = false
        regionFilter = ""
    }
    
    private func debounceSearch() {
        searchTask?.cancel()
        searchTask = Task {
            try? await Task.sleep(nanoseconds: UInt64(Environment.current.searchDebounceInterval * 1_000_000_000))
            guard !Task.isCancelled else { return }
            await refresh()
        }
    }
    
    private func fetchOpportunities(page: Int) async throws -> PaginatedResponse<Opportunity> {
        var queryItems: [URLQueryItem] = [
            URLQueryItem(name: "page", value: "\(page)"),
            URLQueryItem(name: "per_page", value: "\(Environment.current.defaultPageSize)"),
            URLQueryItem(name: "sort", value: sortOption.rawValue)
        ]
        
        if !searchQuery.isEmpty {
            queryItems.append(URLQueryItem(name: "q", value: searchQuery))
        }
        
        if minScore > 0 {
            queryItems.append(URLQueryItem(name: "min_score", value: "\(minScore / 100)"))
        }
        
        if !selectedStatuses.isEmpty {
            queryItems.append(URLQueryItem(name: "status", value: selectedStatuses.map(\.rawValue).joined(separator: ",")))
        }
        
        if onlyWithDeadline {
            queryItems.append(URLQueryItem(name: "has_deadline", value: "true"))
        }
        
        if !regionFilter.isEmpty {
            queryItems.append(URLQueryItem(name: "region", value: regionFilter))
        }
        
        let endpoint = Endpoint(path: "opportunities", queryItems: queryItems)
        return try await NetworkService.shared.request(endpoint, responseType: PaginatedResponse<Opportunity>.self)
    }
}

// MARK: - Paginated Response
struct PaginatedResponse<T: Codable>: Codable {
    let items: [T]
    let total: Int
    let page: Int
    let perPage: Int
    let pages: Int
    
    var hasMore: Bool { page < pages }
}

// MARK: - Preview
#Preview {
    OpportunitiesView()
        .environmentObject(AppState())
        .environmentObject(AuthService.shared)
}
