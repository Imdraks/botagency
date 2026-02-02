"use client";

import { useState } from "react";
import Link from "next/link";
import {
  Radar,
  Check,
  ChevronDown,
  Shield,
  Headphones,
  RefreshCcw,
  Layers,
  Search,
  BarChart3,
  Briefcase,
  ArrowRight,
  Sparkles,
  Eye,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

// ============================================================================
// DATA - 4 PACKS SIMPLES (Option A)
// ============================================================================

const PACKS = [
  {
    id: "core",
    name: "Core",
    tagline: "Organiser et centraliser",
    description: "La base pour gérer votre agence au quotidien.",
    monthlyPrice: 7.99,
    icon: Layers,
    color: "blue",
    features: [
      "Workspace collaboratif",
      "Projets & tâches",
      "Fichiers / assets",
      "Collaboration équipe",
      "Notifications",
      "Intégrations de base",
    ],
    highlight: false,
    cta: "Choisir ce pack",
  },
  {
    id: "discovery",
    name: "Discovery",
    tagline: "Repérer et suivre",
    description: "Trouvez et suivez les artistes parfaits pour vos projets.",
    monthlyPrice: 14.99,
    icon: Search,
    color: "green",
    features: [
      "Recherche artistes",
      "Fiches artistes complètes",
      "Watchlists / Shortlists",
      "Comparaisons",
      "Suivi d'évolution",
      "Alertes basiques",
    ],
    highlight: false,
    cta: "Choisir ce pack",
  },
  {
    id: "analytics",
    name: "Analytics",
    tagline: "Mesurer, comprendre, décider",
    description: "Visualisez la performance et prenez les bonnes décisions.",
    monthlyPrice: 23.99,
    icon: BarChart3,
    color: "purple",
    features: [
      "Dashboards & KPIs",
      "Rapports partageables",
      "Exports (CSV/PDF)",
      "Benchmarks",
      "Scoring & signaux faibles",
      "Prédictions 30/60/90 jours",
    ],
    highlight: true,
    includesIntelligence: true,
    cta: "Choisir ce pack",
  },
  {
    id: "business",
    name: "Business",
    tagline: "Transformer en revenus",
    description: "Gérez vos clients, devis et factures sans quitter Radar.",
    monthlyPrice: 33.99,
    icon: Briefcase,
    color: "orange",
    features: [
      "CRM (clients/contacts)",
      "Pipeline (lead → devis → facture)",
      "Templates devis/factures",
      "Suivi paiements",
      "Exports compta",
      "Collaboration & permissions",
    ],
    highlight: false,
    cta: "Choisir ce pack",
  },
];

const FAQ_ITEMS = [
  {
    question: "Radar est-il accessible à tous ?",
    answer:
      "Non, Radar est une plateforme privée réservée aux agences de production sélectionnées. L'accès se fait sur demande et validation. Nous privilégions la qualité à la quantité pour garantir une expérience optimale.",
  },
  {
    question: "Puis-je changer de pack à tout moment ?",
    answer:
      "Oui, vous pouvez upgrader ou downgrader votre pack à tout moment. Le changement prend effet immédiatement et la facturation est ajustée au prorata.",
  },
  {
    question: "Comment fonctionne la facturation annuelle ?",
    answer:
      "L'abonnement annuel vous fait économiser 20% par rapport au paiement mensuel. Vous êtes facturé une fois par an pour l'année complète.",
  },
  {
    question: "Un pack non activé est-il visible dans l'interface ?",
    answer:
      "Non. Seuls les packs activés pour votre workspace apparaissent dans la navigation. L'interface reste épurée et adaptée à votre usage réel.",
  },
  {
    question: "Que comprend Radar Intelligence dans le pack Analytics ?",
    answer:
      "Radar Intelligence inclut le scoring prédictif des artistes, les recommandations automatiques, les prédictions à 30/60/90 jours et les insights pour faciliter vos décisions.",
  },
  {
    question: "Quel support est disponible ?",
    answer:
      "Tous les packs incluent un support par email. Les packs Analytics et Business bénéficient d'un support prioritaire avec un onboarding personnalisé.",
  },
];

// ============================================================================
// UTILS
// ============================================================================

function calculateYearlyPrice(monthlyPrice: number): number {
  // -20% sur le prix mensuel, facturé annuellement
  const yearlyTotal = monthlyPrice * 12 * 0.8;
  return Math.round(yearlyTotal * 100) / 100;
}

function calculateMonthlySavings(monthlyPrice: number): number {
  const yearlyTotal = monthlyPrice * 12;
  const discountedTotal = calculateYearlyPrice(monthlyPrice);
  return Math.round((yearlyTotal - discountedTotal) * 100) / 100;
}

function formatPrice(price: number): string {
  return price.toFixed(2).replace(".", ",");
}

// ============================================================================
// COMPONENTS
// ============================================================================

function PricingToggle({
  isYearly,
  onToggle,
}: {
  isYearly: boolean;
  onToggle: () => void;
}) {
  return (
    <div className="flex items-center justify-center gap-4">
      <span
        className={cn(
          "text-sm font-medium transition-colors",
          !isYearly ? "text-gray-900" : "text-gray-500"
        )}
      >
        Mensuel
      </span>
      <button
        onClick={onToggle}
        className={cn(
          "relative w-16 h-8 rounded-full transition-colors",
          isYearly ? "bg-purple-600" : "bg-gray-300"
        )}
        aria-label="Toggle billing period"
      >
        <div
          className={cn(
            "absolute top-1 w-6 h-6 bg-white rounded-full shadow-md transition-transform",
            isYearly ? "translate-x-9" : "translate-x-1"
          )}
        />
      </button>
      <div className="flex items-center gap-2">
        <span
          className={cn(
            "text-sm font-medium transition-colors",
            isYearly ? "text-gray-900" : "text-gray-500"
          )}
        >
          Annuel
        </span>
        {isYearly && (
          <Badge className="bg-green-100 text-green-700 hover:bg-green-100">
            -20%
          </Badge>
        )}
      </div>
    </div>
  );
}

function PackCard({
  pack,
  isYearly,
}: {
  pack: (typeof PACKS)[0];
  isYearly: boolean;
}) {
  const monthlyPrice = pack.monthlyPrice;
  const yearlyTotal = calculateYearlyPrice(monthlyPrice);
  const savings = calculateMonthlySavings(monthlyPrice);
  
  const displayPrice = isYearly 
    ? Math.round((yearlyTotal / 12) * 100) / 100 
    : monthlyPrice;

  const colorClasses = {
    blue: {
      bg: "bg-blue-50",
      border: "border-blue-200",
      iconBg: "bg-blue-100",
      iconText: "text-blue-600",
      button: "bg-blue-600 hover:bg-blue-700 text-white",
      check: "text-blue-600",
    },
    green: {
      bg: "bg-green-50",
      border: "border-green-200",
      iconBg: "bg-green-100",
      iconText: "text-green-600",
      button: "bg-green-600 hover:bg-green-700 text-white",
      check: "text-green-600",
    },
    purple: {
      bg: "bg-purple-50",
      border: "border-purple-300",
      iconBg: "bg-purple-100",
      iconText: "text-purple-600",
      button: "bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white",
      check: "text-purple-600",
    },
    orange: {
      bg: "bg-orange-50",
      border: "border-orange-200",
      iconBg: "bg-orange-100",
      iconText: "text-orange-600",
      button: "bg-orange-600 hover:bg-orange-700 text-white",
      check: "text-orange-600",
    },
  };

  const colors = colorClasses[pack.color as keyof typeof colorClasses];
  const Icon = pack.icon;

  // Build checkout URL with plan info
  const checkoutUrl = `/login?plan=${pack.id}&billing=${isYearly ? "yearly" : "monthly"}`;

  return (
    <div
      className={cn(
        "relative rounded-2xl p-6 md:p-8 border-2 transition-all hover:shadow-lg flex flex-col h-full",
        colors.bg,
        colors.border,
        pack.highlight && "ring-2 ring-purple-500 ring-offset-4 shadow-xl"
      )}
    >
      {/* Popular badge */}
      {pack.highlight && (
        <div className="absolute -top-4 left-1/2 -translate-x-1/2">
          <Badge className="bg-purple-600 text-white px-4 py-1 text-sm whitespace-nowrap">
            <Sparkles className="w-3 h-3 mr-1" />
            Le plus populaire
          </Badge>
        </div>
      )}

      {/* Header */}
      <div className="mb-4">
        <div className="flex items-center gap-3 mb-3">
          <div className={cn("p-2 rounded-lg", colors.iconBg)}>
            <Icon className={cn("w-5 h-5", colors.iconText)} />
          </div>
          <h3 className="text-xl md:text-2xl font-bold text-gray-900">{pack.name}</h3>
        </div>
        <p className="text-gray-600 font-medium text-sm">{pack.tagline}</p>
      </div>

      {/* Price */}
      <div className="mb-6">
        <div className="flex items-baseline gap-1">
          <span className="text-3xl md:text-4xl font-bold text-gray-900">
            {formatPrice(displayPrice)}€
          </span>
          <span className="text-gray-500">/mois</span>
        </div>
        {isYearly && (
          <div className="mt-2 space-y-1">
            <p className="text-sm text-gray-500">
              Facturé {formatPrice(yearlyTotal)}€/an
            </p>
            <p className="text-sm text-green-600 font-medium">
              Économisez {formatPrice(savings)}€/an
            </p>
          </div>
        )}
      </div>

      {/* Intelligence badge for Analytics */}
      {"includesIntelligence" in pack && pack.includesIntelligence && (
        <div className="mb-4 p-3 bg-purple-100 rounded-lg border border-purple-200">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-purple-600" />
            <span className="text-sm font-semibold text-purple-700">
              Inclut Radar Intelligence
            </span>
          </div>
          <p className="text-xs text-purple-600 mt-1">
            Scoring, prédictions & recommandations
          </p>
        </div>
      )}

      {/* Features */}
      <ul className="space-y-3 mb-8 flex-grow">
        {pack.features.map((feature) => (
          <li key={feature} className="flex items-start gap-3">
            <Check className={cn("w-5 h-5 mt-0.5 shrink-0", colors.check)} />
            <span className="text-gray-700 text-sm">{feature}</span>
          </li>
        ))}
      </ul>

      {/* CTA */}
      <Link href={checkoutUrl} className="mt-auto">
        <Button className={cn("w-full py-6 text-base font-semibold", colors.button)}>
          {pack.cta}
          <ArrowRight className="w-4 h-4 ml-2" />
        </Button>
      </Link>
    </div>
  );
}

function FAQAccordion() {
  const [openIndex, setOpenIndex] = useState<number | null>(null);

  return (
    <div className="space-y-4 max-w-3xl mx-auto">
      {FAQ_ITEMS.map((item, index) => (
        <div
          key={index}
          className="bg-white rounded-xl border border-gray-200 overflow-hidden"
        >
          <button
            onClick={() => setOpenIndex(openIndex === index ? null : index)}
            className="w-full flex items-center justify-between p-6 text-left hover:bg-gray-50 transition-colors"
          >
            <span className="font-medium text-gray-900">{item.question}</span>
            <ChevronDown
              className={cn(
                "w-5 h-5 text-gray-500 transition-transform shrink-0 ml-4",
                openIndex === index && "rotate-180"
              )}
            />
          </button>
          {openIndex === index && (
            <div className="px-6 pb-6 text-gray-600">{item.answer}</div>
          )}
        </div>
      ))}
    </div>
  );
}

// ============================================================================
// MAIN PAGE
// ============================================================================

export default function PricingPage() {
  const [isYearly, setIsYearly] = useState(true);

  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-white/95 backdrop-blur-lg border-b border-gray-200 py-4">
        <div className="container mx-auto px-6 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-3">
            <div className="h-10 w-10 bg-gradient-to-r from-purple-500 to-pink-500 rounded-xl flex items-center justify-center">
              <Radar className="h-6 w-6 text-white" />
            </div>
            <span className="text-2xl font-bold text-gray-900">Radar</span>
          </Link>
          <div className="flex items-center gap-4">
            <Link href="/">
              <Button variant="ghost" className="text-gray-600 hover:text-gray-900">
                Retour au site
              </Button>
            </Link>
            <Link href="/login">
              <Button className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white">
                Demander l'accès
              </Button>
            </Link>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="pt-32 pb-16 bg-gradient-to-b from-gray-50 to-white">
        <div className="container mx-auto px-6 text-center">
          <Badge className="bg-purple-100 text-purple-700 mb-6">
            <Shield className="w-3 h-3 mr-1" />
            Accès réservé aux agences sélectionnées
          </Badge>
          <h1 className="text-3xl md:text-4xl lg:text-5xl font-bold text-gray-900 mb-6">
            Des packs clairs,{" "}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-600 to-pink-600">
              un prix juste
            </span>
          </h1>
          <p className="text-lg md:text-xl text-gray-600 mb-4 max-w-2xl mx-auto">
            Choisissez le pack adapté à vos besoins. Pas de surprise, pas de modules cachés.
          </p>
          <p className="text-sm text-gray-500 mb-10">
            Tous les prix sont HT. Radar est une plateforme privée.
          </p>

          {/* Toggle */}
          <PricingToggle isYearly={isYearly} onToggle={() => setIsYearly(!isYearly)} />
        </div>
      </section>

      {/* Pricing Cards */}
      <section className="py-16 bg-white">
        <div className="container mx-auto px-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 lg:gap-8 max-w-7xl mx-auto">
            {PACKS.map((pack) => (
              <PackCard key={pack.id} pack={pack} isYearly={isYearly} />
            ))}
          </div>

          {/* Reassurance */}
          <div className="flex flex-wrap items-center justify-center gap-6 md:gap-8 mt-16 text-sm text-gray-600">
            <div className="flex items-center gap-2">
              <RefreshCcw className="w-5 h-5 text-green-600" />
              Changez de pack à tout moment
            </div>
            <div className="flex items-center gap-2">
              <Shield className="w-5 h-5 text-green-600" />
              Données sécurisées RGPD
            </div>
            <div className="flex items-center gap-2">
              <Headphones className="w-5 h-5 text-green-600" />
              Support réactif inclus
            </div>
          </div>
        </div>
      </section>

      {/* Comparison Summary */}
      <section className="py-16 bg-gray-50">
        <div className="container mx-auto px-6">
          <div className="text-center mb-12">
            <h2 className="text-2xl md:text-3xl font-bold text-gray-900 mb-4">
              Quel pack choisir ?
            </h2>
            <p className="text-gray-600 max-w-2xl mx-auto">
              Chaque pack correspond à un usage précis. Commencez par ce dont vous avez besoin.
            </p>
          </div>

          <div className="max-w-4xl mx-auto grid md:grid-cols-2 gap-6">
            <div className="bg-white rounded-xl p-6 border border-gray-200">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <Layers className="w-5 h-5 text-blue-600" />
                </div>
                <h3 className="font-semibold text-gray-900">Core</h3>
              </div>
              <p className="text-gray-600 text-sm">
                Pour les équipes qui veulent centraliser leur organisation : projets, tâches, 
                fichiers et collaboration. L'essentiel pour travailler ensemble.
              </p>
            </div>

            <div className="bg-white rounded-xl p-6 border border-gray-200">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2 bg-green-100 rounded-lg">
                  <Search className="w-5 h-5 text-green-600" />
                </div>
                <h3 className="font-semibold text-gray-900">Discovery</h3>
              </div>
              <p className="text-gray-600 text-sm">
                Pour les agences qui prospectent : recherche artistes, fiches détaillées, 
                watchlists et comparaisons pour trouver les bons profils.
              </p>
            </div>

            <div className="bg-white rounded-xl p-6 border border-purple-200 ring-1 ring-purple-200">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2 bg-purple-100 rounded-lg">
                  <BarChart3 className="w-5 h-5 text-purple-600" />
                </div>
                <h3 className="font-semibold text-gray-900">Analytics</h3>
                <Badge className="bg-purple-100 text-purple-700 text-xs">Recommandé</Badge>
              </div>
              <p className="text-gray-600 text-sm">
                Pour piloter et décider : dashboards, KPIs, scoring et prédictions. 
                Inclut Radar Intelligence pour des recommandations éclairées.
              </p>
            </div>

            <div className="bg-white rounded-xl p-6 border border-gray-200">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2 bg-orange-100 rounded-lg">
                  <Briefcase className="w-5 h-5 text-orange-600" />
                </div>
                <h3 className="font-semibold text-gray-900">Business</h3>
              </div>
              <p className="text-gray-600 text-sm">
                Pour gérer la relation client et la facturation : CRM, pipeline commercial, 
                devis, factures et suivi des paiements intégrés.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Comparison Table */}
      <section className="py-20 bg-white">
        <div className="container mx-auto px-6">
          <div className="text-center mb-12">
            <h2 className="text-2xl md:text-3xl font-bold text-gray-900 mb-4">
              Comparer les packs en détail
            </h2>
            <p className="text-gray-600 max-w-2xl mx-auto">
              Toutes les fonctionnalités par pack, pour faire le bon choix.
            </p>
          </div>

          <div className="max-w-6xl mx-auto overflow-x-auto">
            <table className="w-full border-collapse">
              {/* Header */}
              <thead>
                <tr>
                  <th className="text-left p-4 bg-gray-50 border-b border-gray-200 min-w-[200px]">
                    <span className="text-sm font-semibold text-gray-900">Fonctionnalités</span>
                  </th>
                  <th className="p-4 bg-gray-50 border-b border-gray-200 text-center min-w-[140px]">
                    <div className="flex flex-col items-center gap-1">
                      <div className="p-2 bg-blue-100 rounded-lg">
                        <Layers className="w-5 h-5 text-blue-600" />
                      </div>
                      <span className="font-semibold text-gray-900">Core</span>
                      <span className="text-sm text-gray-500">7,99€/mois</span>
                    </div>
                  </th>
                  <th className="p-4 bg-gray-50 border-b border-gray-200 text-center min-w-[140px]">
                    <div className="flex flex-col items-center gap-1">
                      <div className="p-2 bg-green-100 rounded-lg">
                        <Search className="w-5 h-5 text-green-600" />
                      </div>
                      <span className="font-semibold text-gray-900">Discovery</span>
                      <span className="text-sm text-gray-500">14,99€/mois</span>
                    </div>
                  </th>
                  <th className="p-4 bg-purple-50 border-b border-purple-200 text-center min-w-[140px]">
                    <div className="flex flex-col items-center gap-1">
                      <div className="p-2 bg-purple-100 rounded-lg">
                        <BarChart3 className="w-5 h-5 text-purple-600" />
                      </div>
                      <span className="font-semibold text-gray-900">Analytics</span>
                      <span className="text-sm text-gray-500">23,99€/mois</span>
                      <Badge className="bg-purple-100 text-purple-700 text-xs">Populaire</Badge>
                    </div>
                  </th>
                  <th className="p-4 bg-gray-50 border-b border-gray-200 text-center min-w-[140px]">
                    <div className="flex flex-col items-center gap-1">
                      <div className="p-2 bg-orange-100 rounded-lg">
                        <Briefcase className="w-5 h-5 text-orange-600" />
                      </div>
                      <span className="font-semibold text-gray-900">Business</span>
                      <span className="text-sm text-gray-500">33,99€/mois</span>
                    </div>
                  </th>
                </tr>
              </thead>

              <tbody>
                {/* Organisation */}
                <tr>
                  <td colSpan={5} className="bg-gray-100 p-3 text-sm font-semibold text-gray-700 border-b border-gray-200">
                    📁 Organisation & Collaboration
                  </td>
                </tr>
                <tr className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="p-4 text-sm text-gray-700">Workspace collaboratif</td>
                  <td className="p-4 text-center"><Check className="w-5 h-5 text-green-500 mx-auto" /></td>
                  <td className="p-4 text-center"><Check className="w-5 h-5 text-green-500 mx-auto" /></td>
                  <td className="p-4 text-center bg-purple-50/50"><Check className="w-5 h-5 text-green-500 mx-auto" /></td>
                  <td className="p-4 text-center"><Check className="w-5 h-5 text-green-500 mx-auto" /></td>
                </tr>
                <tr className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="p-4 text-sm text-gray-700">Projets & tâches</td>
                  <td className="p-4 text-center"><Check className="w-5 h-5 text-green-500 mx-auto" /></td>
                  <td className="p-4 text-center"><Check className="w-5 h-5 text-green-500 mx-auto" /></td>
                  <td className="p-4 text-center bg-purple-50/50"><Check className="w-5 h-5 text-green-500 mx-auto" /></td>
                  <td className="p-4 text-center"><Check className="w-5 h-5 text-green-500 mx-auto" /></td>
                </tr>
                <tr className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="p-4 text-sm text-gray-700">Gestion des fichiers / assets</td>
                  <td className="p-4 text-center"><Check className="w-5 h-5 text-green-500 mx-auto" /></td>
                  <td className="p-4 text-center"><Check className="w-5 h-5 text-green-500 mx-auto" /></td>
                  <td className="p-4 text-center bg-purple-50/50"><Check className="w-5 h-5 text-green-500 mx-auto" /></td>
                  <td className="p-4 text-center"><Check className="w-5 h-5 text-green-500 mx-auto" /></td>
                </tr>
                <tr className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="p-4 text-sm text-gray-700">Notifications & rappels</td>
                  <td className="p-4 text-center"><Check className="w-5 h-5 text-green-500 mx-auto" /></td>
                  <td className="p-4 text-center"><Check className="w-5 h-5 text-green-500 mx-auto" /></td>
                  <td className="p-4 text-center bg-purple-50/50"><Check className="w-5 h-5 text-green-500 mx-auto" /></td>
                  <td className="p-4 text-center"><Check className="w-5 h-5 text-green-500 mx-auto" /></td>
                </tr>
                <tr className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="p-4 text-sm text-gray-700">Intégrations (Slack, Google...)</td>
                  <td className="p-4 text-center"><span className="text-sm text-gray-500">Base</span></td>
                  <td className="p-4 text-center"><span className="text-sm text-gray-500">Base</span></td>
                  <td className="p-4 text-center bg-purple-50/50"><Check className="w-5 h-5 text-green-500 mx-auto" /></td>
                  <td className="p-4 text-center"><Check className="w-5 h-5 text-green-500 mx-auto" /></td>
                </tr>

                {/* Discovery */}
                <tr>
                  <td colSpan={5} className="bg-gray-100 p-3 text-sm font-semibold text-gray-700 border-b border-gray-200">
                    🔍 Découverte & Suivi Artistes
                  </td>
                </tr>
                <tr className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="p-4 text-sm text-gray-700">Recherche artistes</td>
                  <td className="p-4 text-center"><span className="text-sm text-gray-400">—</span></td>
                  <td className="p-4 text-center"><Check className="w-5 h-5 text-green-500 mx-auto" /></td>
                  <td className="p-4 text-center bg-purple-50/50"><Check className="w-5 h-5 text-green-500 mx-auto" /></td>
                  <td className="p-4 text-center"><Check className="w-5 h-5 text-green-500 mx-auto" /></td>
                </tr>
                <tr className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="p-4 text-sm text-gray-700">Fiches artistes complètes</td>
                  <td className="p-4 text-center"><span className="text-sm text-gray-400">—</span></td>
                  <td className="p-4 text-center"><Check className="w-5 h-5 text-green-500 mx-auto" /></td>
                  <td className="p-4 text-center bg-purple-50/50"><Check className="w-5 h-5 text-green-500 mx-auto" /></td>
                  <td className="p-4 text-center"><Check className="w-5 h-5 text-green-500 mx-auto" /></td>
                </tr>
                <tr className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="p-4 text-sm text-gray-700">Watchlists & Shortlists</td>
                  <td className="p-4 text-center"><span className="text-sm text-gray-400">—</span></td>
                  <td className="p-4 text-center"><Check className="w-5 h-5 text-green-500 mx-auto" /></td>
                  <td className="p-4 text-center bg-purple-50/50"><Check className="w-5 h-5 text-green-500 mx-auto" /></td>
                  <td className="p-4 text-center"><Check className="w-5 h-5 text-green-500 mx-auto" /></td>
                </tr>
                <tr className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="p-4 text-sm text-gray-700">Comparaisons artistes</td>
                  <td className="p-4 text-center"><span className="text-sm text-gray-400">—</span></td>
                  <td className="p-4 text-center"><Check className="w-5 h-5 text-green-500 mx-auto" /></td>
                  <td className="p-4 text-center bg-purple-50/50"><Check className="w-5 h-5 text-green-500 mx-auto" /></td>
                  <td className="p-4 text-center"><Check className="w-5 h-5 text-green-500 mx-auto" /></td>
                </tr>
                <tr className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="p-4 text-sm text-gray-700">Suivi d'évolution</td>
                  <td className="p-4 text-center"><span className="text-sm text-gray-400">—</span></td>
                  <td className="p-4 text-center"><Check className="w-5 h-5 text-green-500 mx-auto" /></td>
                  <td className="p-4 text-center bg-purple-50/50"><Check className="w-5 h-5 text-green-500 mx-auto" /></td>
                  <td className="p-4 text-center"><Check className="w-5 h-5 text-green-500 mx-auto" /></td>
                </tr>
                <tr className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="p-4 text-sm text-gray-700">Alertes & notifications artistes</td>
                  <td className="p-4 text-center"><span className="text-sm text-gray-400">—</span></td>
                  <td className="p-4 text-center"><span className="text-sm text-gray-500">Base</span></td>
                  <td className="p-4 text-center bg-purple-50/50"><Check className="w-5 h-5 text-green-500 mx-auto" /></td>
                  <td className="p-4 text-center"><Check className="w-5 h-5 text-green-500 mx-auto" /></td>
                </tr>

                {/* Analytics */}
                <tr>
                  <td colSpan={5} className="bg-gray-100 p-3 text-sm font-semibold text-gray-700 border-b border-gray-200">
                    📊 Analytics & Reporting
                  </td>
                </tr>
                <tr className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="p-4 text-sm text-gray-700">Dashboards personnalisés</td>
                  <td className="p-4 text-center"><span className="text-sm text-gray-400">—</span></td>
                  <td className="p-4 text-center"><span className="text-sm text-gray-400">—</span></td>
                  <td className="p-4 text-center bg-purple-50/50"><Check className="w-5 h-5 text-green-500 mx-auto" /></td>
                  <td className="p-4 text-center"><Check className="w-5 h-5 text-green-500 mx-auto" /></td>
                </tr>
                <tr className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="p-4 text-sm text-gray-700">KPIs & métriques avancées</td>
                  <td className="p-4 text-center"><span className="text-sm text-gray-400">—</span></td>
                  <td className="p-4 text-center"><span className="text-sm text-gray-400">—</span></td>
                  <td className="p-4 text-center bg-purple-50/50"><Check className="w-5 h-5 text-green-500 mx-auto" /></td>
                  <td className="p-4 text-center"><Check className="w-5 h-5 text-green-500 mx-auto" /></td>
                </tr>
                <tr className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="p-4 text-sm text-gray-700">Rapports partageables</td>
                  <td className="p-4 text-center"><span className="text-sm text-gray-400">—</span></td>
                  <td className="p-4 text-center"><span className="text-sm text-gray-400">—</span></td>
                  <td className="p-4 text-center bg-purple-50/50"><Check className="w-5 h-5 text-green-500 mx-auto" /></td>
                  <td className="p-4 text-center"><Check className="w-5 h-5 text-green-500 mx-auto" /></td>
                </tr>
                <tr className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="p-4 text-sm text-gray-700">Exports CSV / PDF</td>
                  <td className="p-4 text-center"><span className="text-sm text-gray-400">—</span></td>
                  <td className="p-4 text-center"><span className="text-sm text-gray-400">—</span></td>
                  <td className="p-4 text-center bg-purple-50/50"><Check className="w-5 h-5 text-green-500 mx-auto" /></td>
                  <td className="p-4 text-center"><Check className="w-5 h-5 text-green-500 mx-auto" /></td>
                </tr>
                <tr className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="p-4 text-sm text-gray-700">Benchmarks marché</td>
                  <td className="p-4 text-center"><span className="text-sm text-gray-400">—</span></td>
                  <td className="p-4 text-center"><span className="text-sm text-gray-400">—</span></td>
                  <td className="p-4 text-center bg-purple-50/50"><Check className="w-5 h-5 text-green-500 mx-auto" /></td>
                  <td className="p-4 text-center"><Check className="w-5 h-5 text-green-500 mx-auto" /></td>
                </tr>

                {/* Intelligence */}
                <tr>
                  <td colSpan={5} className="bg-purple-100 p-3 text-sm font-semibold text-purple-800 border-b border-purple-200">
                    ✨ Radar Intelligence
                  </td>
                </tr>
                <tr className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="p-4 text-sm text-gray-700">Scoring prédictif artistes</td>
                  <td className="p-4 text-center"><span className="text-sm text-gray-400">—</span></td>
                  <td className="p-4 text-center"><span className="text-sm text-gray-400">—</span></td>
                  <td className="p-4 text-center bg-purple-50/50"><Check className="w-5 h-5 text-green-500 mx-auto" /></td>
                  <td className="p-4 text-center"><Check className="w-5 h-5 text-green-500 mx-auto" /></td>
                </tr>
                <tr className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="p-4 text-sm text-gray-700">Signaux faibles & opportunités</td>
                  <td className="p-4 text-center"><span className="text-sm text-gray-400">—</span></td>
                  <td className="p-4 text-center"><span className="text-sm text-gray-400">—</span></td>
                  <td className="p-4 text-center bg-purple-50/50"><Check className="w-5 h-5 text-green-500 mx-auto" /></td>
                  <td className="p-4 text-center"><Check className="w-5 h-5 text-green-500 mx-auto" /></td>
                </tr>
                <tr className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="p-4 text-sm text-gray-700">Prédictions 30/60/90 jours</td>
                  <td className="p-4 text-center"><span className="text-sm text-gray-400">—</span></td>
                  <td className="p-4 text-center"><span className="text-sm text-gray-400">—</span></td>
                  <td className="p-4 text-center bg-purple-50/50"><Check className="w-5 h-5 text-green-500 mx-auto" /></td>
                  <td className="p-4 text-center"><Check className="w-5 h-5 text-green-500 mx-auto" /></td>
                </tr>
                <tr className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="p-4 text-sm text-gray-700">Recommandations automatiques</td>
                  <td className="p-4 text-center"><span className="text-sm text-gray-400">—</span></td>
                  <td className="p-4 text-center"><span className="text-sm text-gray-400">—</span></td>
                  <td className="p-4 text-center bg-purple-50/50"><Check className="w-5 h-5 text-green-500 mx-auto" /></td>
                  <td className="p-4 text-center"><Check className="w-5 h-5 text-green-500 mx-auto" /></td>
                </tr>

                {/* Business */}
                <tr>
                  <td colSpan={5} className="bg-gray-100 p-3 text-sm font-semibold text-gray-700 border-b border-gray-200">
                    💼 CRM & Facturation
                  </td>
                </tr>
                <tr className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="p-4 text-sm text-gray-700">CRM (clients & contacts)</td>
                  <td className="p-4 text-center"><span className="text-sm text-gray-400">—</span></td>
                  <td className="p-4 text-center"><span className="text-sm text-gray-400">—</span></td>
                  <td className="p-4 text-center bg-purple-50/50"><span className="text-sm text-gray-400">—</span></td>
                  <td className="p-4 text-center"><Check className="w-5 h-5 text-green-500 mx-auto" /></td>
                </tr>
                <tr className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="p-4 text-sm text-gray-700">Pipeline commercial</td>
                  <td className="p-4 text-center"><span className="text-sm text-gray-400">—</span></td>
                  <td className="p-4 text-center"><span className="text-sm text-gray-400">—</span></td>
                  <td className="p-4 text-center bg-purple-50/50"><span className="text-sm text-gray-400">—</span></td>
                  <td className="p-4 text-center"><Check className="w-5 h-5 text-green-500 mx-auto" /></td>
                </tr>
                <tr className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="p-4 text-sm text-gray-700">Devis & factures</td>
                  <td className="p-4 text-center"><span className="text-sm text-gray-400">—</span></td>
                  <td className="p-4 text-center"><span className="text-sm text-gray-400">—</span></td>
                  <td className="p-4 text-center bg-purple-50/50"><span className="text-sm text-gray-400">—</span></td>
                  <td className="p-4 text-center"><Check className="w-5 h-5 text-green-500 mx-auto" /></td>
                </tr>
                <tr className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="p-4 text-sm text-gray-700">Suivi des paiements</td>
                  <td className="p-4 text-center"><span className="text-sm text-gray-400">—</span></td>
                  <td className="p-4 text-center"><span className="text-sm text-gray-400">—</span></td>
                  <td className="p-4 text-center bg-purple-50/50"><span className="text-sm text-gray-400">—</span></td>
                  <td className="p-4 text-center"><Check className="w-5 h-5 text-green-500 mx-auto" /></td>
                </tr>
                <tr className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="p-4 text-sm text-gray-700">Exports comptabilité</td>
                  <td className="p-4 text-center"><span className="text-sm text-gray-400">—</span></td>
                  <td className="p-4 text-center"><span className="text-sm text-gray-400">—</span></td>
                  <td className="p-4 text-center bg-purple-50/50"><span className="text-sm text-gray-400">—</span></td>
                  <td className="p-4 text-center"><Check className="w-5 h-5 text-green-500 mx-auto" /></td>
                </tr>

                {/* Support */}
                <tr>
                  <td colSpan={5} className="bg-gray-100 p-3 text-sm font-semibold text-gray-700 border-b border-gray-200">
                    🛟 Support & Services
                  </td>
                </tr>
                <tr className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="p-4 text-sm text-gray-700">Support email</td>
                  <td className="p-4 text-center"><Check className="w-5 h-5 text-green-500 mx-auto" /></td>
                  <td className="p-4 text-center"><Check className="w-5 h-5 text-green-500 mx-auto" /></td>
                  <td className="p-4 text-center bg-purple-50/50"><Check className="w-5 h-5 text-green-500 mx-auto" /></td>
                  <td className="p-4 text-center"><Check className="w-5 h-5 text-green-500 mx-auto" /></td>
                </tr>
                <tr className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="p-4 text-sm text-gray-700">Support prioritaire</td>
                  <td className="p-4 text-center"><span className="text-sm text-gray-400">—</span></td>
                  <td className="p-4 text-center"><span className="text-sm text-gray-400">—</span></td>
                  <td className="p-4 text-center bg-purple-50/50"><Check className="w-5 h-5 text-green-500 mx-auto" /></td>
                  <td className="p-4 text-center"><Check className="w-5 h-5 text-green-500 mx-auto" /></td>
                </tr>
                <tr className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="p-4 text-sm text-gray-700">Onboarding personnalisé</td>
                  <td className="p-4 text-center"><span className="text-sm text-gray-400">—</span></td>
                  <td className="p-4 text-center"><span className="text-sm text-gray-400">—</span></td>
                  <td className="p-4 text-center bg-purple-50/50"><Check className="w-5 h-5 text-green-500 mx-auto" /></td>
                  <td className="p-4 text-center"><Check className="w-5 h-5 text-green-500 mx-auto" /></td>
                </tr>
                <tr className="hover:bg-gray-50">
                  <td className="p-4 text-sm text-gray-700">Account manager dédié</td>
                  <td className="p-4 text-center"><span className="text-sm text-gray-400">—</span></td>
                  <td className="p-4 text-center"><span className="text-sm text-gray-400">—</span></td>
                  <td className="p-4 text-center bg-purple-50/50"><span className="text-sm text-gray-400">—</span></td>
                  <td className="p-4 text-center"><Check className="w-5 h-5 text-green-500 mx-auto" /></td>
                </tr>
              </tbody>
            </table>
          </div>

          {/* CTA sous le tableau */}
          <div className="mt-12 text-center">
            <Link href="/login">
              <Button className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white px-8 py-3 rounded-xl">
                Demander l'accès
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section className="py-20 bg-gray-50">
        <div className="container mx-auto px-6">
          <div className="text-center mb-12">
            <h2 className="text-2xl md:text-3xl font-bold text-gray-900 mb-4">
              Questions fréquentes
            </h2>
            <p className="text-gray-600">
              Tout ce que vous devez savoir sur les abonnements Radar.
            </p>
          </div>

          <FAQAccordion />
        </div>
      </section>

      {/* Final CTA */}
      <section className="py-24 bg-gradient-to-b from-gray-50 to-white relative overflow-hidden">
        <div className="absolute inset-0">
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-purple-100 rounded-full blur-[120px] opacity-60" />
        </div>

        <div className="container mx-auto px-6 relative z-10">
          <div className="max-w-3xl mx-auto text-center">
            <h2 className="text-2xl sm:text-3xl lg:text-4xl font-bold text-gray-900 mb-6">
              Prêt à centraliser votre agence dans Radar ?
            </h2>
            <p className="text-lg text-gray-600 mb-10">
              Demandez l'accès et découvrez comment Radar peut transformer votre quotidien.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link href="/login">
                <Button
                  size="lg"
                  className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white text-lg px-10 py-6 rounded-xl"
                >
                  Demander l'accès
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Button>
              </Link>
              <Link href="/today">
                <Button
                  size="lg"
                  variant="outline"
                  className="border-gray-300 text-gray-900 hover:bg-gray-100 text-lg px-10 py-6 rounded-xl"
                >
                  <Eye className="mr-2 h-5 w-5" />
                  Voir une démo
                </Button>
              </Link>
            </div>

            <p className="mt-8 text-sm text-gray-500">
              Réponse rapide • Accès réservé aux agences
            </p>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 bg-white border-t border-gray-200">
        <div className="container mx-auto px-6">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="h-8 w-8 bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg flex items-center justify-center">
                <Radar className="h-4 w-4 text-white" />
              </div>
              <span className="font-semibold text-gray-900">Radar</span>
            </div>
            <div className="flex items-center gap-6 text-sm text-gray-500">
              <Link href="/terms" className="hover:text-gray-900">
                Conditions
              </Link>
              <Link href="/privacy" className="hover:text-gray-900">
                Confidentialité
              </Link>
              <span>© 2026 Radar. Tous droits réservés.</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
