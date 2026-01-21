"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { 
  ArrowRight, 
  Zap, 
  Shield, 
  BarChart3, 
  Users, 
  Radar,
  CheckCircle,
  Calendar,
  FolderOpen,
  TrendingUp
} from "lucide-react";

export default function Home() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  useEffect(() => {
    // Vérifier si l'utilisateur est connecté
    const token = localStorage.getItem("access_token");
    if (token) {
      setIsLoggedIn(true);
    }
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Navigation */}
      <nav className="container mx-auto px-6 py-6 flex justify-between items-center">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 bg-gradient-to-r from-purple-500 to-pink-500 rounded-xl flex items-center justify-center">
            <Radar className="h-6 w-6 text-white" />
          </div>
          <span className="text-2xl font-bold text-white">Radar</span>
        </div>
        <div className="flex items-center gap-4">
          <Link 
            href="/privacy" 
            className="text-gray-300 hover:text-white transition-colors"
          >
            Confidentialité
          </Link>
          {isLoggedIn ? (
            <Link 
              href="/today"
              className="px-6 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-medium transition-colors"
            >
              Accéder au Dashboard
            </Link>
          ) : (
            <Link 
              href="/login"
              className="px-6 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-medium transition-colors"
            >
              Se connecter
            </Link>
          )}
        </div>
      </nav>

      {/* Hero Section */}
      <section className="container mx-auto px-6 py-20 text-center">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-5xl md:text-6xl font-bold text-white mb-6">
            Votre <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-pink-400">cockpit</span> pour piloter votre agence
          </h1>
          <p className="text-xl text-gray-300 mb-10 max-w-2xl mx-auto">
            Radar est la plateforme tout-en-un pour gérer vos projets clients, 
            suivre vos opportunités et développer votre agence de manière intelligente.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link 
              href={isLoggedIn ? "/today" : "/login"}
              className="inline-flex items-center gap-2 px-8 py-4 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white rounded-xl font-semibold text-lg transition-all transform hover:scale-105"
            >
              Commencer maintenant
              <ArrowRight className="h-5 w-5" />
            </Link>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="container mx-auto px-6 py-20">
        <h2 className="text-3xl font-bold text-center text-white mb-16">
          Tout ce dont votre agence a besoin
        </h2>
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          <FeatureCard
            icon={<TrendingUp className="h-8 w-8" />}
            title="Suivi des opportunités"
            description="Visualisez et gérez tout votre pipeline commercial depuis une interface intuitive."
          />
          <FeatureCard
            icon={<Users className="h-8 w-8" />}
            title="Gestion des clients"
            description="Centralisez toutes les informations de vos clients et prospects en un seul endroit."
          />
          <FeatureCard
            icon={<BarChart3 className="h-8 w-8" />}
            title="Scoring intelligent"
            description="Priorisez automatiquement vos leads grâce à notre système de scoring IA."
          />
          <FeatureCard
            icon={<Calendar className="h-8 w-8" />}
            title="Intégration Google Calendar"
            description="Synchronisez vos rendez-vous et événements directement depuis votre agenda Google."
          />
          <FeatureCard
            icon={<FolderOpen className="h-8 w-8" />}
            title="Intégration Google Drive"
            description="Organisez automatiquement vos fichiers projets dans des dossiers structurés."
          />
          <FeatureCard
            icon={<Zap className="h-8 w-8" />}
            title="Automatisations"
            description="Automatisez vos workflows et gagnez du temps sur les tâches répétitives."
          />
        </div>
      </section>

      {/* Benefits Section */}
      <section className="container mx-auto px-6 py-20">
        <div className="bg-white/5 backdrop-blur-lg rounded-3xl p-10 md:p-16">
          <div className="grid md:grid-cols-2 gap-12 items-center">
            <div>
              <h2 className="text-3xl font-bold text-white mb-6">
                Pourquoi choisir Radar ?
              </h2>
              <div className="space-y-4">
                <BenefitItem text="Interface intuitive et moderne" />
                <BenefitItem text="Données sécurisées hébergées en Europe" />
                <BenefitItem text="Intégrations natives avec Google Workspace" />
                <BenefitItem text="Collaboration en équipe avec gestion des rôles" />
                <BenefitItem text="Support réactif et accompagnement personnalisé" />
              </div>
            </div>
            <div className="flex justify-center">
              <div className="relative">
                <div className="absolute inset-0 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full blur-3xl opacity-20"></div>
                <div className="relative bg-gradient-to-br from-slate-800 to-slate-900 rounded-2xl p-8 border border-white/10">
                  <div className="grid grid-cols-2 gap-6">
                    <StatCard number="100%" label="Sécurisé" />
                    <StatCard number="24/7" label="Disponible" />
                    <StatCard number="RGPD" label="Conforme" />
                    <StatCard number="🇫🇷" label="Made in France" />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="container mx-auto px-6 py-20 text-center">
        <h2 className="text-3xl font-bold text-white mb-6">
          Prêt à transformer votre agence ?
        </h2>
        <p className="text-gray-300 mb-8 max-w-xl mx-auto">
          Rejoignez les agences qui font confiance à Radar pour piloter leur croissance.
        </p>
        <Link 
          href={isLoggedIn ? "/today" : "/login"}
          className="inline-flex items-center gap-2 px-8 py-4 bg-white text-purple-900 rounded-xl font-semibold text-lg hover:bg-gray-100 transition-all"
        >
          {isLoggedIn ? "Accéder au dashboard" : "Créer un compte gratuitement"}
          <ArrowRight className="h-5 w-5" />
        </Link>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/10">
        <div className="container mx-auto px-6 py-10">
          <div className="flex flex-col md:flex-row justify-between items-center gap-6">
            <div className="flex items-center gap-3">
              <div className="h-8 w-8 bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg flex items-center justify-center">
                <Radar className="h-5 w-5 text-white" />
              </div>
              <span className="text-lg font-semibold text-white">Radar</span>
            </div>
            <div className="flex items-center gap-6 text-gray-400">
              <Link href="/privacy" className="hover:text-white transition-colors">
                Politique de confidentialité
              </Link>
              <span>© 2026 Radar. Tous droits réservés.</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

function FeatureCard({ icon, title, description }: { icon: React.ReactNode; title: string; description: string }) {
  return (
    <div className="bg-white/5 backdrop-blur-lg rounded-2xl p-6 border border-white/10 hover:border-purple-500/50 transition-colors">
      <div className="h-14 w-14 bg-gradient-to-r from-purple-500/20 to-pink-500/20 rounded-xl flex items-center justify-center text-purple-400 mb-4">
        {icon}
      </div>
      <h3 className="text-xl font-semibold text-white mb-2">{title}</h3>
      <p className="text-gray-400">{description}</p>
    </div>
  );
}

function BenefitItem({ text }: { text: string }) {
  return (
    <div className="flex items-center gap-3">
      <CheckCircle className="h-5 w-5 text-green-400 flex-shrink-0" />
      <span className="text-gray-300">{text}</span>
    </div>
  );
}

function StatCard({ number, label }: { number: string; label: string }) {
  return (
    <div className="text-center">
      <div className="text-2xl font-bold text-white">{number}</div>
      <div className="text-sm text-gray-400">{label}</div>
    </div>
  );
}
