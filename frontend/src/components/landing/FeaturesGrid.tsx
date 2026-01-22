"use client";

import {
  Target,
  FolderKanban,
  CheckCircle2,
  HardDrive,
  Calendar,
} from "lucide-react";

const features = [
  {
    icon: Target,
    title: "Pipeline & Leads",
    description: "Kanban visuel pour suivre vos opportunités du premier contact au closing.",
  },
  {
    icon: FolderKanban,
    title: "Projets & Livrables",
    description: "Organisez chaque projet client avec ses phases, tâches et échéances.",
  },
  {
    icon: CheckCircle2,
    title: "Production & Validations",
    description: "Cycle de validation client intégré. Commentaires et versions centralisés.",
  },
  {
    icon: HardDrive,
    title: "Assets & Google Drive",
    description: "Arborescence Drive automatique par projet. Templates Docs/Sheets inclus.",
  },
  {
    icon: Calendar,
    title: "Calendrier & Deadlines",
    description: "Vue planning unifiée. Synchronisation bidirectionnelle avec Google Calendar.",
  },
];

export function FeaturesGrid() {
  return (
    <section id="produit" className="py-24 bg-white">
      <div className="container mx-auto px-6">
        {/* Header */}
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-purple-100 rounded-full text-sm text-purple-600 mb-4">
            5 workflows unifiés
          </div>
          <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
            Tout ce qu'il faut pour piloter une agence
          </h2>
          <p className="text-gray-600 max-w-2xl mx-auto">
            Un seul outil. Zéro dispersion.
          </p>
        </div>

        {/* Grid - 5 features max */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-6">
          {features.map((feature) => (
            <div
              key={feature.title}
              className="group bg-white border border-gray-200 rounded-2xl p-6 hover:border-purple-300 hover:shadow-lg transition-all duration-300 card-hover"
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
