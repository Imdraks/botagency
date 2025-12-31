// CollectionHistoryView.swift
// Artist analysis history with batch analysis feature

import SwiftUI

struct CollectionHistoryView: View {
    @StateObject private var viewModel = CollectionHistoryViewModel()
    @EnvironmentObject private var appState: AppState
    
    @State private var showArtistAnalysis = false
    @State private var showBatchAnalysis = false
    @State private var selectedAnalysis: ArtistAnalysis?
    
    var body: some View {
        NavigationStack {
            ZStack {
                Color(.systemGroupedBackground)
                    .ignoresSafeArea()
                
                if viewModel.isLoading && viewModel.analyses.isEmpty {
                    HistorySkeletonView()
                } else if viewModel.analyses.isEmpty && !viewModel.isLoading {
                    EmptyStateView(
                        icon: "music.note.list",
                        title: "Aucune analyse",
                        message: "Analysez des artistes pour voir leur historique ici.",
                        actionTitle: "Analyser un artiste"
                    ) {
                        showArtistAnalysis = true
                    }
                } else {
                    ScrollView {
                        VStack(spacing: 16) {
                            // Stats Summary
                            StatsSummary(viewModel: viewModel)
                            
                            // Quick actions
                            QuickAnalysisActions(
                                showSingle: $showArtistAnalysis,
                                showBatch: $showBatchAnalysis
                            )
                            
                            // Analysis list
                            LazyVStack(spacing: 12) {
                                ForEach(viewModel.analyses) { analysis in
                                    ArtistAnalysisCard(analysis: analysis)
                                        .onTapGesture {
                                            selectedAnalysis = analysis
                                        }
                                }
                            }
                            .padding(.horizontal)
                        }
                        .padding(.vertical)
                    }
                    .refreshable {
                        await viewModel.refresh()
                    }
                }
            }
            .navigationTitle("Historique")
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Menu {
                        Button {
                            showArtistAnalysis = true
                        } label: {
                            Label("Analyser un artiste", systemImage: "person.badge.plus")
                        }
                        
                        Button {
                            showBatchAnalysis = true
                        } label: {
                            Label("Analyse par lot", systemImage: "person.3")
                        }
                        
                        Divider()
                        
                        Button {
                            viewModel.exportToCSV()
                        } label: {
                            Label("Exporter CSV", systemImage: "tablecells")
                        }
                    } label: {
                        Image(systemName: "plus.circle.fill")
                    }
                }
            }
            .sheet(isPresented: $showArtistAnalysis) {
                ArtistAnalysisSheet()
            }
            .sheet(isPresented: $showBatchAnalysis) {
                BatchAnalysisSheet(viewModel: viewModel)
            }
            .sheet(item: $selectedAnalysis) { analysis in
                AnalysisDetailView(analysis: analysis)
            }
        }
        .task {
            await viewModel.loadInitial()
        }
    }
}

// MARK: - Stats Summary
struct StatsSummary: View {
    @ObservedObject var viewModel: CollectionHistoryViewModel
    
    var body: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 12) {
                SummaryCard(
                    title: "Artistes analysés",
                    value: "\(viewModel.uniqueArtistsCount)",
                    icon: "person.2.fill",
                    color: .blue
                )
                
                SummaryCard(
                    title: "Score IA moyen",
                    value: "\(viewModel.averageScore)%",
                    icon: "brain",
                    color: .purple
                )
                
                SummaryCard(
                    title: "Cachet total",
                    value: viewModel.totalFeeRange,
                    icon: "eurosign.circle.fill",
                    color: .green
                )
                
                SummaryCard(
                    title: "Ce mois",
                    value: "\(viewModel.thisMonthCount)",
                    icon: "calendar",
                    color: .orange
                )
            }
            .padding(.horizontal)
        }
    }
}

struct SummaryCard: View {
    let title: String
    let value: String
    let icon: String
    let color: Color
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: icon)
                    .font(.caption)
                    .foregroundStyle(color)
                
                Spacer()
            }
            
            Text(value)
                .font(.title3.weight(.bold))
            
            Text(title)
                .font(.caption)
                .foregroundStyle(.secondary)
        }
        .padding(12)
        .frame(width: 130)
        .background {
            RoundedRectangle(cornerRadius: 12, style: .continuous)
                .fill(.regularMaterial)
        }
    }
}

// MARK: - Quick Analysis Actions
struct QuickAnalysisActions: View {
    @Binding var showSingle: Bool
    @Binding var showBatch: Bool
    
    var body: some View {
        HStack(spacing: 12) {
            Button {
                showSingle = true
            } label: {
                HStack {
                    Image(systemName: "person.badge.plus")
                    Text("Analyser")
                }
                .font(.subheadline.weight(.medium))
                .foregroundStyle(.white)
                .frame(maxWidth: .infinity)
                .padding(.vertical, 12)
                .background {
                    RoundedRectangle(cornerRadius: 12, style: .continuous)
                        .fill(Color.accentColor.gradient)
                }
            }
            
            Button {
                showBatch = true
            } label: {
                HStack {
                    Image(systemName: "person.3")
                    Text("Lot")
                }
                .font(.subheadline.weight(.medium))
                .foregroundStyle(.primary)
                .frame(maxWidth: .infinity)
                .padding(.vertical, 12)
                .background {
                    RoundedRectangle(cornerRadius: 12, style: .continuous)
                        .fill(Color(.secondarySystemBackground))
                }
            }
        }
        .padding(.horizontal)
    }
}

// MARK: - Artist Analysis Card
struct ArtistAnalysisCard: View {
    let analysis: ArtistAnalysis
    
    var body: some View {
        GlassCard(style: .card, padding: 0, cornerRadius: 16) {
            HStack(spacing: 12) {
                // Artist image
                AsyncImage(url: URL(string: analysis.imageUrl ?? "")) { phase in
                    switch phase {
                    case .success(let image):
                        image
                            .resizable()
                            .aspectRatio(contentMode: .fill)
                    case .failure, .empty:
                        ZStack {
                            Color.gray.opacity(0.3)
                            Image(systemName: "music.mic")
                                .font(.title2)
                                .foregroundStyle(.secondary)
                        }
                    @unknown default:
                        Color.gray.opacity(0.3)
                    }
                }
                .frame(width: 70, height: 70)
                .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
                
                // Info
                VStack(alignment: .leading, spacing: 6) {
                    Text(analysis.artistName)
                        .font(.headline)
                        .lineLimit(1)
                    
                    HStack(spacing: 8) {
                        // Genre
                        if let genre = analysis.mainGenre {
                            Text(genre)
                                .font(.caption)
                                .padding(.horizontal, 8)
                                .padding(.vertical, 3)
                                .background {
                                    Capsule()
                                        .fill(Color.accentColor.opacity(0.15))
                                }
                        }
                        
                        // Popularity
                        if let popularity = analysis.popularity {
                            HStack(spacing: 2) {
                                Image(systemName: "chart.line.uptrend.xyaxis")
                                    .font(.caption2)
                                Text("\(popularity)%")
                                    .font(.caption)
                            }
                            .foregroundStyle(.green)
                        }
                    }
                    
                    // Fee range
                    if let feeMin = analysis.feeMin, let feeMax = analysis.feeMax {
                        Text("\(formatCurrency(feeMin)) - \(formatCurrency(feeMax))")
                            .font(.caption.weight(.medium))
                            .foregroundStyle(.secondary)
                    }
                }
                
                Spacer()
                
                // Score
                VStack(spacing: 4) {
                    ScoreBadge(analysis.score ?? 0, size: .medium)
                    
                    Text(formatRelativeDate(analysis.createdAt))
                        .font(.caption2)
                        .foregroundStyle(.tertiary)
                }
            }
            .padding(12)
        }
    }
    
    private func formatCurrency(_ value: Double) -> String {
        let formatter = NumberFormatter()
        formatter.numberStyle = .currency
        formatter.currencyCode = "EUR"
        formatter.maximumFractionDigits = 0
        return formatter.string(from: NSNumber(value: value)) ?? "\(Int(value))€"
    }
    
    private func formatRelativeDate(_ date: Date?) -> String {
        guard let date = date else { return "" }
        let formatter = RelativeDateTimeFormatter()
        formatter.unitsStyle = .abbreviated
        return formatter.localizedString(for: date, relativeTo: Date())
    }
}

// MARK: - Artist Analysis Sheet
struct ArtistAnalysisSheet: View {
    @Environment(\.dismiss) private var dismiss
    @State private var artistName = ""
    @State private var isAnalyzing = false
    @State private var result: ArtistAnalysis?
    @State private var error: String?
    
    var body: some View {
        NavigationStack {
            VStack(spacing: 24) {
                // Search field
                VStack(alignment: .leading, spacing: 8) {
                    Text("Nom de l'artiste")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                    
                    GlassTextField(
                        "Ex: Stromae, Aya Nakamura...",
                        text: $artistName,
                        icon: "magnifyingglass",
                        submitLabel: .search,
                        onSubmit: {
                            analyzeArtist()
                        }
                    )
                }
                .padding(.horizontal)
                
                // Result or loading
                if isAnalyzing {
                    VStack(spacing: 16) {
                        ProgressView()
                            .scaleEffect(1.2)
                        
                        Text("Analyse en cours...")
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                        
                        Text("Recherche sur Spotify, analyse IA...")
                            .font(.caption)
                            .foregroundStyle(.tertiary)
                    }
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else if let result = result {
                    AnalysisResultView(analysis: result)
                } else if let error = error {
                    VStack(spacing: 12) {
                        Image(systemName: "exclamationmark.triangle")
                            .font(.largeTitle)
                            .foregroundStyle(.orange)
                        
                        Text(error)
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                            .multilineTextAlignment(.center)
                    }
                    .padding()
                } else {
                    VStack(spacing: 16) {
                        Image(systemName: "music.mic")
                            .font(.system(size: 60))
                            .foregroundStyle(.secondary)
                        
                        Text("Entrez le nom d'un artiste pour lancer l'analyse IA")
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                            .multilineTextAlignment(.center)
                    }
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                    .padding()
                }
                
                Spacer()
                
                // Analyze button
                GlassButton(
                    "Analyser",
                    icon: "brain",
                    isLoading: isAnalyzing
                ) {
                    analyzeArtist()
                }
                .disabled(artistName.isEmpty)
                .padding(.horizontal)
                .padding(.bottom)
            }
            .navigationTitle("Analyser un artiste")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button { dismiss() } label: {
                        Image(systemName: "xmark.circle.fill")
                            .foregroundStyle(.secondary)
                    }
                }
            }
        }
    }
    
    private func analyzeArtist() {
        guard !artistName.isEmpty else { return }
        
        isAnalyzing = true
        error = nil
        result = nil
        
        Task {
            do {
                let endpoint = Endpoint(
                    path: "intelligence/artist-analysis",
                    method: .post,
                    body: ["artist_name": artistName]
                )
                
                result = try await NetworkService.shared.request(
                    endpoint,
                    responseType: ArtistAnalysis.self
                )
            } catch {
                self.error = error.localizedDescription
            }
            
            isAnalyzing = false
        }
    }
}

// MARK: - Analysis Result View
struct AnalysisResultView: View {
    let analysis: ArtistAnalysis
    
    var body: some View {
        ScrollView {
            VStack(spacing: 16) {
                // Artist header
                HStack(spacing: 16) {
                    AsyncImage(url: URL(string: analysis.imageUrl ?? "")) { phase in
                        switch phase {
                        case .success(let image):
                            image.resizable().aspectRatio(contentMode: .fill)
                        default:
                            Color.gray.opacity(0.3)
                        }
                    }
                    .frame(width: 80, height: 80)
                    .clipShape(RoundedRectangle(cornerRadius: 16))
                    
                    VStack(alignment: .leading, spacing: 4) {
                        Text(analysis.artistName)
                            .font(.title2.weight(.bold))
                        
                        if let genre = analysis.mainGenre {
                            Text(genre)
                                .font(.subheadline)
                                .foregroundStyle(.secondary)
                        }
                    }
                    
                    Spacer()
                    
                    ScoreBadge(analysis.score ?? 0, size: .large)
                }
                .padding()
                .background {
                    RoundedRectangle(cornerRadius: 16, style: .continuous)
                        .fill(.regularMaterial)
                }
                
                // Stats grid
                LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 12) {
                    AnalysisStatCard(
                        title: "Popularité",
                        value: "\(analysis.popularity ?? 0)%",
                        icon: "chart.line.uptrend.xyaxis",
                        color: .green
                    )
                    
                    AnalysisStatCard(
                        title: "Followers",
                        value: formatNumber(analysis.followers ?? 0),
                        icon: "person.2",
                        color: .blue
                    )
                    
                    AnalysisStatCard(
                        title: "Cachet min",
                        value: formatCurrency(analysis.feeMin ?? 0),
                        icon: "eurosign.circle",
                        color: .orange
                    )
                    
                    AnalysisStatCard(
                        title: "Cachet max",
                        value: formatCurrency(analysis.feeMax ?? 0),
                        icon: "eurosign.circle.fill",
                        color: .green
                    )
                }
                
                // Predictions
                if let predictions = analysis.predictions, !predictions.isEmpty {
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Prédictions")
                            .font(.headline)
                        
                        ForEach(predictions, id: \.period) { prediction in
                            HStack {
                                Text(prediction.period)
                                    .font(.subheadline)
                                
                                Spacer()
                                
                                Text(prediction.growth >= 0 ? "+\(Int(prediction.growth * 100))%" : "\(Int(prediction.growth * 100))%")
                                    .font(.subheadline.weight(.bold))
                                    .foregroundStyle(prediction.growth >= 0 ? .green : .red)
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
            .padding()
        }
    }
    
    private func formatNumber(_ value: Int) -> String {
        if value >= 1_000_000 {
            return String(format: "%.1fM", Double(value) / 1_000_000)
        } else if value >= 1_000 {
            return String(format: "%.1fK", Double(value) / 1_000)
        }
        return "\(value)"
    }
    
    private func formatCurrency(_ value: Double) -> String {
        let formatter = NumberFormatter()
        formatter.numberStyle = .currency
        formatter.currencyCode = "EUR"
        formatter.maximumFractionDigits = 0
        return formatter.string(from: NSNumber(value: value)) ?? "\(Int(value))€"
    }
}

struct AnalysisStatCard: View {
    let title: String
    let value: String
    let icon: String
    let color: Color
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: icon)
                    .foregroundStyle(color)
                Spacer()
            }
            
            Text(value)
                .font(.title3.weight(.bold))
            
            Text(title)
                .font(.caption)
                .foregroundStyle(.secondary)
        }
        .padding(12)
        .background {
            RoundedRectangle(cornerRadius: 12, style: .continuous)
                .fill(Color(.secondarySystemBackground))
        }
    }
}

// MARK: - Batch Analysis Sheet
struct BatchAnalysisSheet: View {
    @ObservedObject var viewModel: CollectionHistoryViewModel
    @Environment(\.dismiss) private var dismiss
    @State private var artistsText = ""
    @State private var analyses: [BatchAnalysisItem] = []
    @State private var isAnalyzing = false
    @State private var currentIndex = 0
    
    var artistNames: [String] {
        artistsText
            .components(separatedBy: .newlines)
            .map { $0.trimmingCharacters(in: .whitespaces) }
            .filter { !$0.isEmpty }
    }
    
    var body: some View {
        NavigationStack {
            VStack(spacing: 16) {
                // Input area
                VStack(alignment: .leading, spacing: 8) {
                    HStack {
                        Text("Artistes à analyser")
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                        
                        Spacer()
                        
                        Text("\(artistNames.count) artiste(s)")
                            .font(.caption)
                            .foregroundStyle(.tertiary)
                    }
                    
                    TextEditor(text: $artistsText)
                        .frame(height: 120)
                        .padding(8)
                        .background {
                            RoundedRectangle(cornerRadius: 12, style: .continuous)
                                .fill(Color(.secondarySystemBackground))
                        }
                    
                    Text("Un artiste par ligne")
                        .font(.caption)
                        .foregroundStyle(.tertiary)
                }
                .padding(.horizontal)
                .disabled(isAnalyzing)
                
                // Progress
                if isAnalyzing {
                    VStack(spacing: 8) {
                        ProgressView(value: Double(currentIndex), total: Double(artistNames.count))
                            .tint(.accentColor)
                        
                        Text("Analyse \(currentIndex + 1) sur \(artistNames.count)")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                    .padding(.horizontal)
                }
                
                // Results list
                if !analyses.isEmpty {
                    ScrollView {
                        LazyVStack(spacing: 8) {
                            ForEach(analyses) { item in
                                BatchAnalysisRow(item: item)
                            }
                        }
                        .padding(.horizontal)
                    }
                }
                
                Spacer()
                
                // Action button
                GlassButton(
                    isAnalyzing ? "Analyse en cours..." : "Lancer l'analyse",
                    icon: "brain",
                    isLoading: isAnalyzing
                ) {
                    startBatchAnalysis()
                }
                .disabled(artistNames.isEmpty || isAnalyzing)
                .padding(.horizontal)
                .padding(.bottom)
            }
            .navigationTitle("Analyse par lot")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button { dismiss() } label: {
                        Image(systemName: "xmark.circle.fill")
                            .foregroundStyle(.secondary)
                    }
                    .disabled(isAnalyzing)
                }
            }
        }
    }
    
    private func startBatchAnalysis() {
        isAnalyzing = true
        analyses = artistNames.map { BatchAnalysisItem(artistName: $0, status: .pending) }
        currentIndex = 0
        
        Task {
            for (index, name) in artistNames.enumerated() {
                currentIndex = index
                analyses[index].status = .analyzing
                
                do {
                    let endpoint = Endpoint(
                        path: "intelligence/artist-analysis",
                        method: .post,
                        body: ["artist_name": name]
                    )
                    
                    let result = try await NetworkService.shared.request(
                        endpoint,
                        responseType: ArtistAnalysis.self
                    )
                    
                    analyses[index].status = .completed
                    analyses[index].result = result
                } catch {
                    analyses[index].status = .failed
                    analyses[index].error = error.localizedDescription
                }
                
                // Small delay between requests
                try? await Task.sleep(nanoseconds: 500_000_000)
            }
            
            isAnalyzing = false
            await viewModel.refresh()
        }
    }
}

struct BatchAnalysisItem: Identifiable {
    let id = UUID()
    let artistName: String
    var status: BatchStatus
    var result: ArtistAnalysis?
    var error: String?
}

enum BatchStatus {
    case pending, analyzing, completed, failed
}

struct BatchAnalysisRow: View {
    let item: BatchAnalysisItem
    
    var body: some View {
        HStack {
            // Status icon
            Group {
                switch item.status {
                case .pending:
                    Image(systemName: "clock")
                        .foregroundStyle(.secondary)
                case .analyzing:
                    ProgressView()
                        .scaleEffect(0.8)
                case .completed:
                    Image(systemName: "checkmark.circle.fill")
                        .foregroundStyle(.green)
                case .failed:
                    Image(systemName: "xmark.circle.fill")
                        .foregroundStyle(.red)
                }
            }
            .frame(width: 24)
            
            // Name
            Text(item.artistName)
                .font(.subheadline)
            
            Spacer()
            
            // Result
            if let result = item.result {
                ScoreBadge(result.score ?? 0, size: .small)
            } else if let error = item.error {
                Text("Erreur")
                    .font(.caption)
                    .foregroundStyle(.red)
            }
        }
        .padding(12)
        .background {
            RoundedRectangle(cornerRadius: 10, style: .continuous)
                .fill(Color(.secondarySystemBackground))
        }
    }
}

// MARK: - Analysis Detail View
struct AnalysisDetailView: View {
    let analysis: ArtistAnalysis
    @Environment(\.dismiss) private var dismiss
    
    var body: some View {
        NavigationStack {
            ScrollView {
                AnalysisResultView(analysis: analysis)
            }
            .navigationTitle(analysis.artistName)
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button { dismiss() } label: {
                        Image(systemName: "xmark.circle.fill")
                            .foregroundStyle(.secondary)
                    }
                }
            }
        }
    }
}

// MARK: - Skeleton View
struct HistorySkeletonView: View {
    var body: some View {
        ScrollView {
            VStack(spacing: 16) {
                // Stats skeleton
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 12) {
                        ForEach(0..<4, id: \.self) { _ in
                            SkeletonView(height: 90, cornerRadius: 12)
                                .frame(width: 130)
                        }
                    }
                    .padding(.horizontal)
                }
                
                // Actions skeleton
                HStack(spacing: 12) {
                    SkeletonView(height: 44, cornerRadius: 12)
                    SkeletonView(height: 44, cornerRadius: 12)
                }
                .padding(.horizontal)
                
                // Cards skeleton
                ForEach(0..<5, id: \.self) { _ in
                    HStack(spacing: 12) {
                        SkeletonView(height: 70, cornerRadius: 12)
                            .frame(width: 70)
                        
                        VStack(alignment: .leading, spacing: 8) {
                            SkeletonView(height: 16)
                                .frame(width: 150)
                            SkeletonView(height: 12)
                                .frame(width: 100)
                            SkeletonView(height: 10)
                                .frame(width: 80)
                        }
                        
                        Spacer()
                        
                        SkeletonView(height: 28, cornerRadius: 14)
                            .frame(width: 50)
                    }
                    .padding(12)
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

// MARK: - ViewModel
@MainActor
final class CollectionHistoryViewModel: ObservableObject {
    @Published var analyses: [ArtistAnalysis] = []
    @Published var isLoading = false
    @Published var error: Error?
    
    var uniqueArtistsCount: Int {
        Set(analyses.map { $0.artistName }).count
    }
    
    var averageScore: Int {
        guard !analyses.isEmpty else { return 0 }
        let sum = analyses.compactMap { $0.score }.reduce(0, +)
        return Int(sum / Double(analyses.count))
    }
    
    var totalFeeRange: String {
        let minFees = analyses.compactMap { $0.feeMin }
        let maxFees = analyses.compactMap { $0.feeMax }
        
        guard !minFees.isEmpty else { return "N/A" }
        
        let totalMin = minFees.reduce(0, +)
        let totalMax = maxFees.reduce(0, +)
        
        return "\(formatCurrency(totalMin)) - \(formatCurrency(totalMax))"
    }
    
    var thisMonthCount: Int {
        let calendar = Calendar.current
        let now = Date()
        return analyses.filter { analysis in
            guard let date = analysis.createdAt else { return false }
            return calendar.isDate(date, equalTo: now, toGranularity: .month)
        }.count
    }
    
    func loadInitial() async {
        guard analyses.isEmpty else { return }
        await refresh()
    }
    
    func refresh() async {
        isLoading = true
        
        do {
            let endpoint = Endpoint(path: "artist-history")
            let response = try await NetworkService.shared.request(
                endpoint,
                responseType: ArtistHistoryResponse.self
            )
            analyses = response.analyses
        } catch {
            self.error = error
            Logger.error("Failed to fetch artist history: \(error)")
        }
        
        isLoading = false
    }
    
    func exportToCSV() {
        Logger.info("Exporting to CSV...")
        // TODO: Implement CSV export
    }
    
    private func formatCurrency(_ value: Double) -> String {
        let formatter = NumberFormatter()
        formatter.numberStyle = .currency
        formatter.currencyCode = "EUR"
        formatter.maximumFractionDigits = 0
        return formatter.string(from: NSNumber(value: value)) ?? "\(Int(value))€"
    }
}

// MARK: - Response Models
struct ArtistHistoryResponse: Codable {
    let analyses: [ArtistAnalysis]
    let statistics: ArtistStatistics?
}

struct ArtistStatistics: Codable {
    let totalAnalyses: Int
    let uniqueArtists: Int
    let avgScore: Double?
    let avgFeeMin: Double?
    let avgFeeMax: Double?
    let totalFeeMin: Double?
    let totalFeeMax: Double?
}

// MARK: - Preview
#Preview {
    CollectionHistoryView()
        .environmentObject(AppState())
}
