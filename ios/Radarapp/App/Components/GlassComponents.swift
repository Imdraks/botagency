// GlassComponents.swift
// Liquid Glass UI components for iOS 26 aesthetic

import SwiftUI

// MARK: - Glass Background
struct GlassBackground: View {
    let style: GlassStyle
    let cornerRadius: CGFloat
    
    init(style: GlassStyle = .default, cornerRadius: CGFloat = 20) {
        self.style = style
        self.cornerRadius = cornerRadius
    }
    
    var body: some View {
        ZStack {
            // Blur layer
            RoundedRectangle(cornerRadius: cornerRadius, style: .continuous)
                .fill(.ultraThinMaterial)
            
            // Gradient overlay
            RoundedRectangle(cornerRadius: cornerRadius, style: .continuous)
                .fill(style.gradient)
            
            // Border
            RoundedRectangle(cornerRadius: cornerRadius, style: .continuous)
                .strokeBorder(style.borderGradient, lineWidth: 0.5)
        }
    }
}

enum GlassStyle {
    case `default`
    case primary
    case success
    case warning
    case danger
    case elevated
    case card
    
    var gradient: LinearGradient {
        switch self {
        case .default:
            return LinearGradient(
                colors: [Color.white.opacity(0.1), Color.white.opacity(0.05)],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
        case .primary:
            return LinearGradient(
                colors: [Color.blue.opacity(0.3), Color.blue.opacity(0.1)],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
        case .success:
            return LinearGradient(
                colors: [Color.green.opacity(0.3), Color.green.opacity(0.1)],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
        case .warning:
            return LinearGradient(
                colors: [Color.orange.opacity(0.4), Color.orange.opacity(0.2)],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
        case .danger:
            return LinearGradient(
                colors: [Color.red.opacity(0.3), Color.red.opacity(0.1)],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
        case .elevated:
            return LinearGradient(
                colors: [Color.white.opacity(0.15), Color.white.opacity(0.05)],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
        case .card:
            return LinearGradient(
                colors: [Color.white.opacity(0.08), Color.clear],
                startPoint: .top,
                endPoint: .bottom
            )
        }
    }
    
    var borderGradient: LinearGradient {
        LinearGradient(
            colors: [Color.white.opacity(0.3), Color.white.opacity(0.1)],
            startPoint: .topLeading,
            endPoint: .bottomTrailing
        )
    }
}

// MARK: - Glass Card
struct GlassCard<Content: View>: View {
    let style: GlassStyle
    let padding: CGFloat
    let cornerRadius: CGFloat
    @ViewBuilder let content: () -> Content
    
    init(
        style: GlassStyle = .card,
        padding: CGFloat = 16,
        cornerRadius: CGFloat = 16,
        @ViewBuilder content: @escaping () -> Content
    ) {
        self.style = style
        self.padding = padding
        self.cornerRadius = cornerRadius
        self.content = content
    }
    
    var body: some View {
        content()
            .padding(padding)
            .background {
                GlassBackground(style: style, cornerRadius: cornerRadius)
            }
            .shadow(color: .black.opacity(0.08), radius: 8, x: 0, y: 4)
    }
}

// MARK: - Glass Button
struct GlassButton: View {
    let title: String
    let icon: String?
    let style: GlassButtonStyle
    let isLoading: Bool
    let action: () -> Void
    
    init(
        _ title: String,
        icon: String? = nil,
        style: GlassButtonStyle = .primary,
        isLoading: Bool = false,
        action: @escaping () -> Void
    ) {
        self.title = title
        self.icon = icon
        self.style = style
        self.isLoading = isLoading
        self.action = action
    }
    
    var body: some View {
        Button(action: action) {
            HStack(spacing: 8) {
                if isLoading {
                    ProgressView()
                        .tint(style.foregroundColor)
                        .scaleEffect(0.8)
                } else if let icon = icon {
                    Image(systemName: icon)
                        .font(.body.weight(.semibold))
                }
                
                Text(title)
                    .font(.body.weight(.semibold))
            }
            .foregroundStyle(style.foregroundColor)
            .padding(.horizontal, 20)
            .padding(.vertical, 14)
            .frame(maxWidth: style == .primary ? .infinity : nil)
            .background {
                switch style {
                case .primary:
                    RoundedRectangle(cornerRadius: 14, style: .continuous)
                        .fill(Color.accentColor.gradient)
                case .secondary:
                    GlassBackground(style: .default, cornerRadius: 14)
                case .ghost:
                    Color.clear
                case .danger:
                    RoundedRectangle(cornerRadius: 14, style: .continuous)
                        .fill(Color.red.gradient)
                }
            }
        }
        .disabled(isLoading)
    }
}

enum GlassButtonStyle {
    case primary
    case secondary
    case ghost
    case danger
    
    var foregroundColor: Color {
        switch self {
        case .primary, .danger: return .white
        case .secondary, .ghost: return .primary
        }
    }
}

// MARK: - Glass Text Field
struct GlassTextField: View {
    let placeholder: String
    @Binding var text: String
    let icon: String?
    let isSecure: Bool
    let keyboardType: UIKeyboardType
    let submitLabel: SubmitLabel
    let onSubmit: (() -> Void)?
    
    @FocusState private var isFocused: Bool
    
    init(
        _ placeholder: String,
        text: Binding<String>,
        icon: String? = nil,
        isSecure: Bool = false,
        keyboardType: UIKeyboardType = .default,
        submitLabel: SubmitLabel = .done,
        onSubmit: (() -> Void)? = nil
    ) {
        self.placeholder = placeholder
        self._text = text
        self.icon = icon
        self.isSecure = isSecure
        self.keyboardType = keyboardType
        self.submitLabel = submitLabel
        self.onSubmit = onSubmit
    }
    
    var body: some View {
        HStack(spacing: 12) {
            if let icon = icon {
                Image(systemName: icon)
                    .foregroundStyle(.secondary)
                    .font(.body)
            }
            
            Group {
                if isSecure {
                    SecureField(placeholder, text: $text)
                } else {
                    TextField(placeholder, text: $text)
                }
            }
            .keyboardType(keyboardType)
            .submitLabel(submitLabel)
            .onSubmit {
                onSubmit?()
            }
            .focused($isFocused)
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 14)
        .background {
            RoundedRectangle(cornerRadius: 12, style: .continuous)
                .fill(.regularMaterial)
                .overlay {
                    RoundedRectangle(cornerRadius: 12, style: .continuous)
                        .strokeBorder(
                            isFocused ? Color.accentColor : Color.clear,
                            lineWidth: 2
                        )
                }
        }
        .animation(.easeInOut(duration: 0.2), value: isFocused)
    }
}

// MARK: - Score Badge
struct ScoreBadge: View {
    let score: Int
    let size: BadgeSize
    
    enum BadgeSize {
        case small, medium, large
        
        var font: Font {
            switch self {
            case .small: return .caption.weight(.bold)
            case .medium: return .subheadline.weight(.bold)
            case .large: return .title2.weight(.bold)
            }
        }
        
        var padding: CGFloat {
            switch self {
            case .small: return 6
            case .medium: return 10
            case .large: return 14
            }
        }
    }
    
    init(_ score: Int, size: BadgeSize = .medium) {
        self.score = score
        self.size = size
    }
    
    var scoreColor: Color {
        switch score {
        case 80...100: return .green
        case 60..<80: return .blue
        case 40..<60: return .orange
        default: return .red
        }
    }
    
    var body: some View {
        Text("\(score)%")
            .font(size.font)
            .foregroundStyle(.white)
            .padding(.horizontal, size.padding)
            .padding(.vertical, size.padding * 0.6)
            .background {
                Capsule()
                    .fill(scoreColor.gradient)
            }
    }
}

// MARK: - Status Badge
struct StatusBadge: View {
    let status: OpportunityStatus
    
    var body: some View {
        Text(status.displayName)
            .font(.caption.weight(.semibold))
            .foregroundStyle(statusColor)
            .padding(.horizontal, 10)
            .padding(.vertical, 5)
            .background {
                Capsule()
                    .fill(statusColor.opacity(0.15))
            }
    }
    
    var statusColor: Color {
        switch status {
        case .new: return .blue
        case .reviewed: return .gray
        case .interested: return .orange
        case .applied: return .purple
        case .rejected: return .red
        case .won: return .green
        case .lost: return .gray
        }
    }
}

// MARK: - Shimmer Effect
struct ShimmerModifier: ViewModifier {
    @State private var phase: CGFloat = 0
    
    func body(content: Content) -> some View {
        content
            .overlay {
                GeometryReader { geometry in
                    LinearGradient(
                        colors: [
                            .clear,
                            .white.opacity(0.3),
                            .clear
                        ],
                        startPoint: .leading,
                        endPoint: .trailing
                    )
                    .frame(width: geometry.size.width * 2)
                    .offset(x: -geometry.size.width + (geometry.size.width * 2 * phase))
                }
            }
            .mask(content)
            .onAppear {
                withAnimation(.linear(duration: 1.5).repeatForever(autoreverses: false)) {
                    phase = 1
                }
            }
    }
}

extension View {
    func shimmer() -> some View {
        modifier(ShimmerModifier())
    }
}

// MARK: - Skeleton Loader
struct SkeletonView: View {
    let height: CGFloat
    let cornerRadius: CGFloat
    
    init(height: CGFloat = 20, cornerRadius: CGFloat = 8) {
        self.height = height
        self.cornerRadius = cornerRadius
    }
    
    var body: some View {
        RoundedRectangle(cornerRadius: cornerRadius, style: .continuous)
            .fill(Color.gray.opacity(0.2))
            .frame(height: height)
            .shimmer()
    }
}

// MARK: - Empty State View
struct EmptyStateView: View {
    let icon: String
    let title: String
    let message: String
    let action: (() -> Void)?
    let actionTitle: String?
    
    init(
        icon: String,
        title: String,
        message: String,
        actionTitle: String? = nil,
        action: (() -> Void)? = nil
    ) {
        self.icon = icon
        self.title = title
        self.message = message
        self.action = action
        self.actionTitle = actionTitle
    }
    
    var body: some View {
        VStack(spacing: 20) {
            Image(systemName: icon)
                .font(.system(size: 60))
                .foregroundStyle(.secondary)
            
            VStack(spacing: 8) {
                Text(title)
                    .font(.title3.weight(.semibold))
                
                Text(message)
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
                    .multilineTextAlignment(.center)
            }
            
            if let action = action, let actionTitle = actionTitle {
                GlassButton(actionTitle, icon: "arrow.clockwise", style: .secondary, action: action)
            }
        }
        .padding(40)
    }
}

// MARK: - Pull to Refresh
struct RefreshableModifier: ViewModifier {
    let isRefreshing: Bool
    let onRefresh: () async -> Void
    
    func body(content: Content) -> some View {
        content
            .refreshable {
                await onRefresh()
            }
            .overlay(alignment: .top) {
                if isRefreshing {
                    ProgressView()
                        .padding(.top, 20)
                }
            }
    }
}

// MARK: - Previews
#Preview("Glass Components") {
    ZStack {
        LinearGradient(
            colors: [.blue.opacity(0.3), .purple.opacity(0.3)],
            startPoint: .topLeading,
            endPoint: .bottomTrailing
        )
        .ignoresSafeArea()
        
        ScrollView {
            VStack(spacing: 24) {
                GlassCard {
                    VStack(alignment: .leading, spacing: 12) {
                        HStack {
                            Text("Festival Jazz 2025")
                                .font(.headline)
                            Spacer()
                            ScoreBadge(85)
                        }
                        
                        Text("Paris • 15 Jan 2025")
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                        
                        StatusBadge(status: .interested)
                    }
                }
                
                GlassTextField("Email", text: .constant(""), icon: "envelope")
                
                GlassButton("Connexion", icon: "arrow.right", style: .primary) {}
                
                GlassButton("Annuler", style: .secondary) {}
                
                SkeletonView(height: 100, cornerRadius: 16)
            }
            .padding()
        }
    }
}
