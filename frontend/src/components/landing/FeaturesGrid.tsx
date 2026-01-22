"use client";

import {
  LayoutGrid,
  FolderKanban,
  FileBox,
  Calendar,
  Sparkles,
  Users,
  BarChart3,
  Bell,
} from "lucide-react";

const features = [
  {
    icon: LayoutGrid,
    title: "Pipeline Kanban",
    description: "Visualisez tous vos deals en un coup d'œil. Drag & drop intuitif.",
  },
  {
    icon: FolderKanban,
    title: "Projets & Livrables",
    description: "Suivez l'avancement, gérez les validations clients en temps réel.",
  },
  {
    icon: FileBox,
    title: "Assets centralisés",
    description: "Tous vos fichiers clients au même endroit. Liens et documents.",
  },
  {
    icon: Calendar,
    title: "Calendrier & Deadlines",
    description: "Vue planning des échéances. Synchro Google Calendar.",
  },
  {
    icon: Sparkles,
    title: "Daily Picks IA",
    description: "Chaque jour, l'IA vous suggère les leads les plus prometteurs.",
  },
  {
    icon: BarChart3,
    title: "Scoring intelligent",
    description: "Priorisez automatiquement vos opportunités selon vos critères.",
  },
  {
    icon: Users,
    title: "Gestion d'équipe",
    description: "Rôles et permissions. Chaque membre voit ce qui le concerne.",
  },
  {
    icon: Bell,
    title: "Notifications",
    description: "Alertes deadlines, nouveaux leads, validations en attente.",
  },
];

export function FeaturesGrid() {
  return (
    <section id="produit" className="py-24 bg-white">
      <div className="container mx-auto px-6">
        {/* Header */}
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-purple-100 rounded-full text-sm text-purple-600 mb-4">
            Fonctionnalités
          </div>
          <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
            Tout pour piloter votre agence
          </h2>
          <p className="text-gray-600 max-w-2xl mx-auto">
            Une plateforme pensée pour les agences qui veulent gagner du temps et garder le contrôle.
          </p>
        </div>

        {/* Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {features.map((feature, index) => (
            <div
              key={feature.title}
              className="group bg-white border border-gray-200 rounded-2xl p-6 hover:border-purple-300 hover:shadow-lg transition-all duration-300"
            >
              {/* Icon */}
              <div className="h-12 w-12 rounded-xl bg-gradient-to-r from-purple-100 to-pink-100 flex items-center justify-center mb-4 group-hover:from-purple-200 group-hover:to-pink-200 transition-colors">
                <feature.icon className="h-6 w-6 text-purple-600" />
              </div>

              {/* Content */}
              <h3 className="text-lg font-semibold text-gray-900 mb-2">{feature.title}</h3>
              <p className="text-gray-600 text-sm leading-relaxed">{feature.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
