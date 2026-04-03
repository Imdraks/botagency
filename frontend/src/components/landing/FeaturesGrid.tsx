"use client";

import {
  Target,
  FolderKanban,
  HardDrive,
  Calendar,
  FileText,
  BarChart3,
  Sparkles,
  Landmark,
} from "lucide-react";

const features = [
  {
    icon: Target,
    title: "Pipeline & Leads",
    description: "Kanban visuel pour suivre vos opportunités du premier contact au closing. Scoring IA automatique.",
  },
  {
    icon: FolderKanban,
    title: "Projets & Tâches",
    description: "Organisez chaque projet client avec ses phases, tâches et échéances. Suivi en temps réel.",
  },
  {
    icon: FileText,
    title: "Devis & Factures",
    description: "Créez vos devis et factures conformes. Export PDF, sauvegarde automatique sur Google Drive.",
  },
  {
    icon: BarChart3,
    title: "Analytics",
    description: "Dashboard complet : KPIs, taux de conversion, heatmap deadlines, top performers.",
  },
  {
    icon: HardDrive,
    title: "Google Drive",
    description: "Arborescence Drive automatique par projet. Templates Docs & Sheets prêts à l'emploi.",
  },
  {
    icon: Calendar,
    title: "Google Calendar",
    description: "Synchronisation bidirectionnelle des deadlines et rendez-vous clients.",
  },
  {
    icon: Sparkles,
    title: "Intelligence IA",
    description: "Scoring automatique des leads, enrichissement de données, suggestions intelligentes.",
  },
  {
    icon: Landmark,
    title: "Transactions",
    description: "Connectez vos comptes bancaires. Suivi des paiements et rapprochement automatique.",
  },
];

export function FeaturesGrid() {
  return (
    <section id="produit" className="py-24 bg-white">
      <div className="container mx-auto px-6">
        {/* Header */}
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-purple-100 rounded-full text-sm text-purple-600 mb-4">
            Plateforme tout-en-un
          </div>
          <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
            Tout ce qu&apos;il faut pour piloter une agence
          </h2>
          <p className="text-gray-600 max-w-2xl mx-auto">
            Un seul outil. Zéro dispersion. Du pipeline à la facturation.
          </p>
        </div>

        {/* Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {features.map((feature) => (
            <div
              key={feature.title}
              className="group bg-white border border-gray-200 rounded-2xl p-6 hover:border-purple-300 hover:shadow-lg transition-all duration-300 card-hover"
            >
              {/* Icon */}
              <div className="h-12 w-12 rounded-xl bg-gradient-to-r from-purple-100 to-purple-50 flex items-center justify-center mb-4 group-hover:from-purple-200 group-hover:to-purple-100 transition-colors">
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
