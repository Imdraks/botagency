"use client";

import { Check, Zap, Building2, Rocket } from "lucide-react";

const plans = [
  {
    name: "Mini",
    description: "Pour les petites structures qui démarrent",
    icon: Zap,
    color: "blue",
    features: [
      "Pipeline commercial",
      "Gestion des projets & tâches",
      "Calendrier unifié",
      "3 utilisateurs max",
      "Intégration Google Workspace",
    ],
    highlight: false,
  },
  {
    name: "Standard",
    description: "Pour les agences en croissance",
    icon: Building2,
    color: "purple",
    features: [
      "Tout de Mini +",
      "Devis & Factures PDF",
      "Sauvegarde Drive auto",
      "Analytics avancés",
      "Scoring IA des leads",
      "10 utilisateurs max",
    ],
    highlight: true,
  },
  {
    name: "Premium",
    description: "Pour les agences ambitieuses",
    icon: Rocket,
    color: "orange",
    features: [
      "Tout de Standard +",
      "Connexion bancaire",
      "Intelligence IA complète",
      "Utilisateurs illimités",
      "API & intégrations",
      "Support prioritaire",
    ],
    highlight: false,
  },
];

const colorClasses = {
  blue: {
    bg: "bg-blue-50",
    border: "border-blue-200",
    icon: "text-blue-600 bg-blue-100",
    button: "bg-blue-600 hover:bg-blue-700 text-white",
    check: "text-blue-600",
  },
  purple: {
    bg: "bg-purple-50",
    border: "border-purple-300",
    icon: "text-purple-600 bg-purple-100",
    button: "bg-purple-600 hover:bg-purple-700 text-white",
    check: "text-purple-600",
  },
  orange: {
    bg: "bg-orange-50",
    border: "border-orange-200",
    icon: "text-orange-600 bg-orange-100",
    button: "bg-orange-600 hover:bg-orange-700 text-white",
    check: "text-orange-600",
  },
};

export function Pricing() {
  return (
    <section id="pricing" className="py-24 bg-gray-50">
      <div className="max-w-7xl mx-auto px-6">
        {/* Header */}
        <div className="text-center mb-16">
          <span className="inline-flex items-center gap-2 bg-purple-100 text-purple-700 px-4 py-2 rounded-full text-sm font-medium mb-4">
            <Zap className="w-4 h-4" />
            Nos offres
          </span>
          <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
            Une offre adaptée à votre agence
          </h2>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Choisissez le plan qui correspond à vos besoins. Tous nos plans incluent un essai gratuit.
          </p>
        </div>

        {/* Plans Grid */}
        <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
          {plans.map((plan) => {
            const colors = colorClasses[plan.color as keyof typeof colorClasses];
            const Icon = plan.icon;
            
            return (
              <div
                key={plan.name}
                className={`relative rounded-2xl p-8 ${colors.bg} border-2 ${colors.border} ${
                  plan.highlight ? "ring-2 ring-purple-500 ring-offset-2 scale-105" : ""
                } transition-all hover:scale-[1.02]`}
              >
                {plan.highlight && (
                  <div className="absolute -top-4 left-1/2 -translate-x-1/2">
                    <span className="bg-purple-600 text-white text-sm font-medium px-4 py-1 rounded-full">
                      Populaire
                    </span>
                  </div>
                )}

                {/* Icon & Name */}
                <div className="flex items-center gap-3 mb-4">
                  <div className={`p-2 rounded-xl ${colors.icon}`}>
                    <Icon className="w-6 h-6" />
                  </div>
                  <h3 className="text-2xl font-bold text-gray-900">{plan.name}</h3>
                </div>

                {/* Description */}
                <p className="text-gray-600 mb-6">{plan.description}</p>

                {/* Features */}
                <ul className="space-y-3 mb-8">
                  {plan.features.map((feature) => (
                    <li key={feature} className="flex items-start gap-3">
                      <Check className={`w-5 h-5 mt-0.5 ${colors.check}`} />
                      <span className="text-gray-700">{feature}</span>
                    </li>
                  ))}
                </ul>

                {/* CTA Button */}
                <a
                  href={`mailto:contact@radarapp.fr?subject=Demande d'information - Plan ${plan.name}`}
                  className={`block w-full text-center py-3 px-6 rounded-xl font-semibold ${colors.button} transition-colors`}
                >
                  Contactez-nous
                </a>
              </div>
            );
          })}
        </div>

        {/* Bottom note */}
        <p className="text-center text-gray-500 mt-12">
          Besoin d&apos;une offre sur mesure ?{" "}
          <a href="mailto:contact@radarapp.fr" className="text-purple-600 hover:underline font-medium">
            Parlons-en
          </a>
        </p>
      </div>
    </section>
  );
}
