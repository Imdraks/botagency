// LoginView.swift
// Authentication view with Liquid Glass design

import SwiftUI
import AuthenticationServices

struct LoginView: View {
    @StateObject private var viewModel = LoginViewModel()
    @EnvironmentObject private var appState: AppState
    
    var body: some View {
        GeometryReader { geometry in
            ZStack {
                // Background gradient
                AnimatedGradientBackground()
                
                ScrollView {
                    VStack(spacing: 0) {
                        Spacer(minLength: geometry.size.height * 0.12)
                        
                        // Logo & Title
                        VStack(spacing: 16) {
                            ZStack {
                                Circle()
                                    .fill(.ultraThinMaterial)
                                    .frame(width: 100, height: 100)
                                
                                Image(systemName: "antenna.radiowaves.left.and.right")
                                    .font(.system(size: 40, weight: .medium))
                                    .foregroundStyle(.white)
                            }
                            .shadow(color: .black.opacity(0.2), radius: 20, x: 0, y: 10)
                            
                            VStack(spacing: 6) {
                                Text("Radarapp")
                                    .font(.largeTitle.weight(.bold))
                                    .foregroundStyle(.white)
                                
                                Text("Détectez les opportunités")
                                    .font(.subheadline)
                                    .foregroundStyle(.white.opacity(0.8))
                            }
                        }
                        .padding(.bottom, 48)
                        
                        // Login Form
                        VStack(spacing: 20) {
                            // Email field
                            GlassTextField(
                                "Email",
                                text: $viewModel.email,
                                icon: "envelope",
                                keyboardType: .emailAddress,
                                submitLabel: .next
                            )
                            .textContentType(.emailAddress)
                            .textInputAutocapitalization(.never)
                            .autocorrectionDisabled()
                            
                            // Password field
                            GlassTextField(
                                "Mot de passe",
                                text: $viewModel.password,
                                icon: "lock",
                                isSecure: true,
                                submitLabel: .go,
                                onSubmit: {
                                    viewModel.login()
                                }
                            )
                            .textContentType(.password)
                            
                            // Forgot password
                            HStack {
                                Spacer()
                                Button {
                                    viewModel.showForgotPassword = true
                                } label: {
                                    Text("Mot de passe oublié ?")
                                        .font(.footnote.weight(.medium))
                                        .foregroundStyle(.white.opacity(0.8))
                                }
                            }
                            
                            // Login button
                            GlassButton(
                                "Se connecter",
                                icon: "arrow.right",
                                style: .primary,
                                isLoading: viewModel.isLoading
                            ) {
                                viewModel.login()
                            }
                            .padding(.top, 8)
                            
                            // Divider
                            HStack {
                                Rectangle()
                                    .fill(.white.opacity(0.3))
                                    .frame(height: 1)
                                
                                Text("ou")
                                    .font(.footnote)
                                    .foregroundStyle(.white.opacity(0.7))
                                    .padding(.horizontal, 16)
                                
                                Rectangle()
                                    .fill(.white.opacity(0.3))
                                    .frame(height: 1)
                            }
                            .padding(.vertical, 8)
                            
                            // Social login buttons
                            VStack(spacing: 12) {
                                // Sign in with Apple
                                SignInWithAppleButton(.signIn) { request in
                                    request.requestedScopes = [.email, .fullName]
                                } onCompletion: { result in
                                    viewModel.handleAppleSignIn(result: result)
                                }
                                .signInWithAppleButtonStyle(.white)
                                .frame(height: 50)
                                .cornerRadius(12)
                                
                                // Sign in with Google
                                Button {
                                    viewModel.signInWithGoogle()
                                } label: {
                                    HStack(spacing: 12) {
                                        Image(systemName: "g.circle.fill")
                                            .font(.title2)
                                        
                                        Text("Continuer avec Google")
                                            .font(.body.weight(.semibold))
                                    }
                                    .foregroundStyle(.primary)
                                    .frame(maxWidth: .infinity)
                                    .frame(height: 50)
                                    .background {
                                        RoundedRectangle(cornerRadius: 12, style: .continuous)
                                            .fill(.white)
                                    }
                                }
                            }
                        }
                        .padding(.horizontal, 32)
                        .padding(.vertical, 32)
                        .background {
                            GlassBackground(style: .elevated, cornerRadius: 32)
                        }
                        .padding(.horizontal, 20)
                        
                        Spacer(minLength: 40)
                        
                        // Footer
                        VStack(spacing: 8) {
                            Text("En continuant, vous acceptez nos")
                                .font(.caption)
                                .foregroundStyle(.white.opacity(0.6))
                            
                            HStack(spacing: 4) {
                                Button("Conditions d'utilisation") {
                                    viewModel.showTerms = true
                                }
                                
                                Text("et")
                                
                                Button("Politique de confidentialité") {
                                    viewModel.showPrivacy = true
                                }
                            }
                            .font(.caption.weight(.medium))
                            .foregroundStyle(.white.opacity(0.8))
                        }
                        .padding(.bottom, 32)
                    }
                    .frame(minHeight: geometry.size.height)
                }
            }
        }
        .ignoresSafeArea(.keyboard)
        .alert("Erreur", isPresented: $viewModel.showError) {
            Button("OK") {}
        } message: {
            Text(viewModel.errorMessage)
        }
        .sheet(isPresented: $viewModel.showForgotPassword) {
            ForgotPasswordSheet()
        }
    }
}

// MARK: - Animated Gradient Background
struct AnimatedGradientBackground: View {
    @State private var animateGradient = false
    
    var body: some View {
        LinearGradient(
            colors: [
                Color(red: 0.1, green: 0.1, blue: 0.3),
                Color(red: 0.2, green: 0.1, blue: 0.4),
                Color(red: 0.1, green: 0.2, blue: 0.5)
            ],
            startPoint: animateGradient ? .topLeading : .bottomLeading,
            endPoint: animateGradient ? .bottomTrailing : .topTrailing
        )
        .ignoresSafeArea()
        .onAppear {
            withAnimation(.easeInOut(duration: 5).repeatForever(autoreverses: true)) {
                animateGradient.toggle()
            }
        }
    }
}

// MARK: - Forgot Password Sheet
struct ForgotPasswordSheet: View {
    @Environment(\.dismiss) private var dismiss
    @State private var email = ""
    @State private var isLoading = false
    @State private var showSuccess = false
    
    var body: some View {
        NavigationStack {
            VStack(spacing: 24) {
                Image(systemName: "envelope.badge.shield.half.filled")
                    .font(.system(size: 60))
                    .foregroundStyle(.accent)
                    .padding(.top, 40)
                
                VStack(spacing: 8) {
                    Text("Réinitialiser le mot de passe")
                        .font(.title2.weight(.bold))
                    
                    Text("Entrez votre email et nous vous enverrons un lien de réinitialisation.")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                        .multilineTextAlignment(.center)
                }
                .padding(.horizontal)
                
                GlassTextField(
                    "Email",
                    text: $email,
                    icon: "envelope",
                    keyboardType: .emailAddress
                )
                .padding(.horizontal)
                .padding(.top, 16)
                
                GlassButton(
                    "Envoyer le lien",
                    icon: "paperplane",
                    isLoading: isLoading
                ) {
                    resetPassword()
                }
                .padding(.horizontal)
                
                Spacer()
            }
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button {
                        dismiss()
                    } label: {
                        Image(systemName: "xmark.circle.fill")
                            .foregroundStyle(.secondary)
                    }
                }
            }
            .alert("Email envoyé", isPresented: $showSuccess) {
                Button("OK") { dismiss() }
            } message: {
                Text("Si un compte existe avec cette adresse, vous recevrez un email de réinitialisation.")
            }
        }
    }
    
    private func resetPassword() {
        guard !email.isEmpty else { return }
        isLoading = true
        
        // Simulate API call
        Task {
            try? await Task.sleep(nanoseconds: 1_500_000_000)
            isLoading = false
            showSuccess = true
        }
    }
}

// MARK: - Login ViewModel
@MainActor
final class LoginViewModel: ObservableObject {
    @Published var email = ""
    @Published var password = ""
    @Published var isLoading = false
    @Published var showError = false
    @Published var errorMessage = ""
    @Published var showForgotPassword = false
    @Published var showTerms = false
    @Published var showPrivacy = false
    
    func login() {
        guard validate() else { return }
        
        isLoading = true
        
        Task {
            do {
                try await AuthService.shared.login(email: email, password: password)
            } catch {
                showError = true
                errorMessage = error.localizedDescription
            }
            isLoading = false
        }
    }
    
    func signInWithGoogle() {
        // TODO: Implement Google Sign-In
        Logger.info("Google Sign-In requested")
    }
    
    func handleAppleSignIn(result: Result<ASAuthorization, Error>) {
        switch result {
        case .success(let authorization):
            if let credential = authorization.credential as? ASAuthorizationAppleIDCredential {
                // Get the identity token
                if let identityToken = credential.identityToken,
                   let tokenString = String(data: identityToken, encoding: .utf8) {
                    Task {
                        await sendAppleTokenToBackend(token: tokenString)
                    }
                }
            }
        case .failure(let error):
            showError = true
            errorMessage = error.localizedDescription
        }
    }
    
    private func sendAppleTokenToBackend(token: String) async {
        // TODO: Implement Apple token exchange with backend
        Logger.info("Apple Sign-In token received")
    }
    
    private func validate() -> Bool {
        if email.isEmpty {
            showError = true
            errorMessage = "Veuillez entrer votre email"
            return false
        }
        
        if !email.contains("@") {
            showError = true
            errorMessage = "Email invalide"
            return false
        }
        
        if password.isEmpty {
            showError = true
            errorMessage = "Veuillez entrer votre mot de passe"
            return false
        }
        
        if password.count < 6 {
            showError = true
            errorMessage = "Le mot de passe doit contenir au moins 6 caractères"
            return false
        }
        
        return true
    }
}

// MARK: - Preview
#Preview {
    LoginView()
        .environmentObject(AppState())
        .environmentObject(AuthService.shared)
}
