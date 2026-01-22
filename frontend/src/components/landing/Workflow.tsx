"use client";

import { Target, Sparkles, Rocket, CheckCircle2, Send } from "lucide-react";

const steps = [
  {
    step: "01",
    icon: Target,
    title: "Capturer",
    description: "Centralisez vos leads depuis toutes vos sources : formulaires, emails, recommandations.",
    color: "from-blue-500 to-cyan-500",
  },
  {
    step: "02",
    icon: Sparkles,
    title: "Qualifier",
    description: "Scorez automatiquement vos opportunités grâce à l'IA. Focus sur les meilleurs prospects.",
    color: "from-purple-500 to-pink-500",
  },
  {
    step: "03",
    icon: Rocket,
    title: "Convertir",
    description: "Transformez vos deals en projets clients en un clic. Toutes les infos suivent.",
    color: "from-orange-500 to-red-500",
  },
  {
    step: "04",
    icon: CheckCircle2,
    title: "Produire",
    description: "Gérez vos livrables, cycles de validation et versions. Rien ne se perd.",
    color: "from-green-500 to-emerald-500",
  },
  {
    step: "05",
    icon: Send,
    title: "Livrer",
    description: "Assets centralisés, fichiers Google Drive organisés. Livraison propre et traçée.",
    color: "from-indigo-500 to-purple-500",
  },
];

export function Workflow() {
  return (
    <section id="workflow" className="py-24 bg-gray-50 relative overflow-hidden">
      {/* Background decoration */}
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-purple-50/50 to-transparent" />
      
      <div className="container mx-auto px-6 relative z-10">
        {/* Header */}
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-purple-100 rounded-full text-sm text-purple-600 mb-4">
            Workflow
          </div>
          <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
            Du lead à la livraison en{" "}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-600 to-pink-600">
              5 étapes
            </span>
          </h2>
          <p className="text-gray-600 max-w-2xl mx-auto">
            Un workflow pensé pour les agences. Fini les infos éparpillées entre 10 outils.
          </p>
        </div>

        {/* Steps */}
        <div className="relative">
          {/* Connection Line - Desktop */}
          <div className="hidden lg:block absolute top-24 left-[10%] right-[10%] h-0.5 bg-gradient-to-r from-blue-500 via-purple-500 to-indigo-500 opacity-30" />

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-6 lg:gap-4">
            {steps.map((step, index) => (
              <div key={step.step} className="relative group">
                {/* Card */}
                <div className="bg-white border border-gray-200 rounded-2xl p-6 h-full hover:border-purple-300 hover:shadow-lg transition-all duration-300 hover:-translate-y-1">
                  {/* Step Number */}
                  <div className="flex items-center justify-between mb-4">
                    <span className="text-5xl font-bold text-gray-100 group-hover:text-gray-200 transition-colors">
                      {step.step}
                    </span>
                    <div
                      className={`h-12 w-12 rounded-xl bg-gradient-to-r ${step.color} flex items-center justify-center`}
                    >
                      <step.icon className="h-6 w-6 text-white" />
                    </div>
                  </div>

                  {/* Content */}
                  <h3 className="text-xl font-semibold text-gray-900 mb-2">{step.title}</h3>
                  <p className="text-gray-600 text-sm leading-relaxed">{step.description}</p>
                </div>

                {/* Arrow - Mobile/Tablet */}
                {index < steps.length - 1 && (
                  <div className="lg:hidden flex justify-center my-4">
                    <svg
                      className="h-6 w-6 text-purple-500/50"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M19 14l-7 7m0 0l-7-7m7 7V3"
                      />
                    </svg>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
