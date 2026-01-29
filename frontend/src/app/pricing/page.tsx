"use client";

import { useState } from "react";
import Link from "next/link";
import {
  Radar,
  Check,
  X,
  ChevronDown,
  Zap,
  Building2,
  Rocket,
  Shield,
  Headphones,
  RefreshCcw,
  Layers,
  Search,
  BarChart3,
  Brain,
  Briefcase,
  Database,
  ArrowRight,
  Sparkles,
  Users,
  Calendar,
  FileText,
  Eye,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

// ============================================================================
// DATA
// ============================================================================

const PLANS = [
  {
    id: "mini",
    name: "Radar Mini",
    tagline: "S'organiser et exécuter",
    description: "Pour les petites équipes qui centralisent leurs opérations",
    monthlyPrice: 9.99,
    yearlyPrice: 7.99,
    packs: ["Core"],
    features: [
      "Pipeline commercial unifié",
      "Gestion des projets",
      "Calendrier équipe",
      "Intégration Google Workspace",
      "3 membres par workspace",
    ],
    cta: "Démarrer avec Mini",
    highlight: false,
    color: "blue",
  },
  {
    id: "standard",
    name: "Radar Standard",
    tagline: "Piloter et décider",
    description: "Pour les agences structurées qui veulent de la visibilité",
    monthlyPrice: 19.99,
    yearlyPrice: 15.99,
    packs: ["Core", "Discovery", "Analytics", "Spotify Search"],
    features: [
      "Tout de Mini +",
      "Prospection artistes",
      "Comparaison & shortlists",
      "Recherche Spotify avec IA",
      "Tableaux de bord analytics",
      "10 membres par workspace",
    ],
    cta: "Choisir Standard",
    highlight: true,
    color: "purple",
  },
  {
    id: "premium",
    name: "Radar Premium",
    tagline: "La machine complète",
    description: "Pour les agences avancées avec IA et gestion client",
    monthlyPrice: 39.99,
    yearlyPrice: 31.99,
    packs: ["Core", "Discovery", "Analytics", "Intelligence", "Business", "Data", "Spotify Search"],
    features: [
      "Tout de Standard +",
      "Analyse IA complète (SWOT, prédictions)",
      "Scoring prédictif artistes",
      "Intelligence booking",
      "Devis & factures",
      "Membres illimités",
    ],
    cta: "Passer en Premium",
    highlight: false,
    color: "orange",
  },
];

const PACKS = [
  {
    id: "Core",
    name: "Radar Core",
    tagline: "Exécution quotidienne",
    icon: Layers,
    color: "purple",
    description: "La base pour gérer votre agence au quotidien.",
    features: ["Pipeline & leads", "Projets & production", "Calendrier unifié"],
  },
  {
    id: "Discovery",
    name: "Radar Discovery",
    tagline: "Explorer & comparer",
    icon: Search,
    color: "blue",
    description: "Trouvez les artistes parfaits pour vos projets.",
    features: ["Recherche artistes", "Comparaison", "Shortlists partagées"],
  },
  {
    id: "SpotifySearch",
    name: "Spotify Search IA",
    tagline: "Analyse IA d'artistes",
    icon: Brain,
    color: "green",
    description: "Scan web complet + Intelligence Artificielle.",
    features: ["Score IA global", "Analyse SWOT", "Prédictions 30/90/180j", "Intelligence booking"],
  },
  {
    id: "Analytics",
    name: "Radar Analytics",
    tagline: "Piloter l'agence",
    icon: BarChart3,
    color: "green",
    description: "Visualisez la performance de votre agence.",
    features: ["Tableaux de bord", "Métriques clés", "Rapports exportables"],
  },
  {
    id: "Intelligence",
    name: "Radar Intelligence",
    tagline: "Recommandations & scoring",
    icon: Brain,
    color: "orange",
    description: "L'IA au service de vos décisions.",
    features: ["Scoring prédictif", "Suggestions artistes", "Insights automatiques"],
  },
  {
    id: "Business",
    name: "Radar Business",
    tagline: "Clients, devis, factures",
    icon: Briefcase,
    color: "pink",
    description: "Gérez la paperasse client sans quitter Radar.",
    features: ["Gestion clients", "Devis en 1 clic", "Factures & suivi"],
  },
  {
    id: "Data",
    name: "Radar Data",
    tagline: "Sources & monitoring",
    icon: Database,
    color: "gray",
    description: "Pour les admins qui veulent tout contrôler.",
    features: ["Sources de données", "Monitoring santé", "Admin avancé"],
    adminOnly: true,
  },
];

const COMPARISON_DATA = [
  {
    category: "Radar Core",
    features: [
      { name: "Pipeline commercial", mini: true, standard: true, premium: true },
      { name: "Gestion des projets", mini: true, standard: true, premium: true },
      { name: "Calendrier unifié", mini: true, standard: true, premium: true },
      { name: "Intégration Google Workspace", mini: true, standard: true, premium: true },
    ],
  },
  {
    category: "Radar Discovery",
    features: [
      { name: "Recherche artistes", mini: false, standard: true, premium: true },
      { name: "Comparaison profils", mini: false, standard: true, premium: true },
      { name: "Shortlists partagées", mini: false, standard: true, premium: true },
    ],
  },
  {
    category: "Spotify Search IA",
    features: [
      { name: "Recherche artistes Spotify", mini: false, standard: true, premium: true },
      { name: "Score IA global (0-100)", mini: false, standard: true, premium: true },
      { name: "Analyse SWOT", mini: false, standard: "basique", premium: true },
      { name: "Prédictions 30/90/180 jours", mini: false, standard: false, premium: true },
      { name: "Intelligence booking", mini: false, standard: false, premium: true },
      { name: "Cachet estimé & optimal", mini: false, standard: true, premium: true },
    ],
  },
  {
    category: "Radar Analytics",
    features: [
      { name: "Dashboard cockpit", mini: false, standard: true, premium: true },
      { name: "Métriques & KPIs", mini: false, standard: true, premium: true },
      { name: "Rapports exportables", mini: false, standard: true, premium: true },
    ],
  },
  {
    category: "Radar Intelligence",
    features: [
      { name: "Scoring prédictif", mini: false, standard: "add-on", premium: true },
      { name: "Recommandations IA", mini: false, standard: "add-on", premium: true },
      { name: "Insights automatiques", mini: false, standard: "add-on", premium: true },
    ],
  },
  {
    category: "Radar Business",
    features: [
      { name: "Gestion clients", mini: false, standard: "add-on", premium: true },
      { name: "Devis & factures", mini: false, standard: "add-on", premium: true },
      { name: "Suivi paiements", mini: false, standard: "add-on", premium: true },
    ],
  },
  {
    category: "Radar Data",
    features: [
      { name: "Sources de données", mini: false, standard: false, premium: "admin" },
      { name: "Monitoring santé", mini: false, standard: false, premium: "admin" },
    ],
  },
  {
    category: "Limites",
    features: [
      { name: "Membres par workspace", mini: "3", standard: "10", premium: "Illimité" },
      { name: "Workspaces", mini: "1", standard: "3", premium: "Illimité" },
      { name: "Stockage assets", mini: "5 Go", standard: "50 Go", premium: "Illimité" },
    ],
  },
];

const ADD_ONS = [
  {
    id: "intelligence",
    name: "Radar Intelligence",
    description: "Ajoutez les recommandations IA et le scoring prédictif à votre plan Standard.",
    price: 49,
    icon: Brain,
  },
  {
    id: "business",
    name: "Radar Business",
    description: "Gérez vos clients, devis et factures directement dans Radar.",
    price: 39,
    icon: Briefcase,
  },
];

const FAQ_ITEMS = [
  {
    question: "Radar est-il accessible à tous ?",
    answer:
      "Non, Radar est une plateforme privée réservée aux agences de production sélectionnées. L'accès se fait sur demande et validation. Nous privilégions la qualité à la quantité pour garantir une expérience optimale.",
  },
  {
    question: "Puis-je changer de plan à tout moment ?",
    answer:
      "Oui, vous pouvez upgrader ou downgrader votre plan à tout moment. Le changement prend effet immédiatement et la facturation est ajustée au prorata.",
  },
  {
    question: "Un pack non activé est-il visible dans l'interface ?",
    answer:
      "Non. Seuls les packs activés pour votre workspace apparaissent dans la navigation. L'interface reste épurée et adaptée à votre usage réel.",
  },
  {
    question: "Qui peut activer ou désactiver les packs ?",
    answer:
      "Seuls les administrateurs du workspace peuvent gérer les packs. Les membres voient uniquement les fonctionnalités activées pour eux.",
  },
  {
    question: "Comment fonctionne l'intégration Google Workspace ?",
    answer:
      "Radar se connecte nativement à Google Drive, Docs et Calendar. Vos assets sont synchronisés, vos événements apparaissent dans le calendrier unifié, et vous pouvez créer des documents directement depuis l'app.",
  },
  {
    question: "Radar remplace-t-il un CRM ou un outil de facturation ?",
    answer:
      "Radar peut remplacer votre CRM basique pour la gestion du pipeline. Avec le pack Business, vous pouvez également gérer vos devis et factures. Pour des besoins comptables avancés, l'export vers votre logiciel reste possible.",
  },
  {
    question: "Puis-je activer Radar Business sans passer en Premium ?",
    answer:
      "Oui ! Radar Business est disponible en add-on pour les abonnements Standard. Contactez-nous pour l'activer sur votre workspace.",
  },
  {
    question: "Quel support est disponible ?",
    answer:
      "Tous les plans incluent un support par email. Les plans Standard et Premium bénéficient d'un support prioritaire. Premium inclut également un onboarding personnalisé.",
  },
];

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

function PlanCard({
  plan,
  isYearly,
}: {
  plan: (typeof PLANS)[0];
  isYearly: boolean;
}) {
  const price = isYearly ? plan.yearlyPrice : plan.monthlyPrice;
  const colorClasses = {
    blue: {
      bg: "bg-blue-50",
      border: "border-blue-200",
      badge: "bg-blue-100 text-blue-700",
      button: "bg-blue-600 hover:bg-blue-700 text-white",
      check: "text-blue-600",
    },
    purple: {
      bg: "bg-purple-50",
      border: "border-purple-300",
      badge: "bg-purple-100 text-purple-700",
      button: "bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white",
      check: "text-purple-600",
    },
    orange: {
      bg: "bg-orange-50",
      border: "border-orange-200",
      badge: "bg-orange-100 text-orange-700",
      button: "bg-orange-600 hover:bg-orange-700 text-white",
      check: "text-orange-600",
    },
  };

  const colors = colorClasses[plan.color as keyof typeof colorClasses];

  return (
    <div
      className={cn(
        "relative rounded-2xl p-8 border-2 transition-all hover:shadow-lg",
        colors.bg,
        colors.border,
        plan.highlight && "ring-2 ring-purple-500 ring-offset-4 scale-105 shadow-xl"
      )}
    >
      {plan.highlight && (
        <div className="absolute -top-4 left-1/2 -translate-x-1/2">
          <Badge className="bg-purple-600 text-white px-4 py-1 text-sm">
            Recommandé
          </Badge>
        </div>
      )}

      {/* Header */}
      <div className="mb-6">
        <h3 className="text-2xl font-bold text-gray-900 mb-1">{plan.name}</h3>
        <p className="text-gray-600 font-medium">{plan.tagline}</p>
      </div>

      {/* Price */}
      <div className="mb-6">
        <div className="flex items-baseline gap-1">
          <span className="text-4xl font-bold text-gray-900">{price.toFixed(2).replace('.', ',')}€</span>
          <span className="text-gray-500">/mois</span>
        </div>
        {isYearly && (
          <p className="text-sm text-gray-500 mt-1">
            Facturé {(price * 12).toFixed(2).replace('.', ',')}€/an
          </p>
        )}
      </div>

      {/* Packs */}
      <div className="flex flex-wrap gap-2 mb-6">
        {plan.packs.map((pack) => (
          <Badge key={pack} className={colors.badge}>
            {pack}
          </Badge>
        ))}
      </div>

      {/* Features */}
      <ul className="space-y-3 mb-8">
        {plan.features.map((feature) => (
          <li key={feature} className="flex items-start gap-3">
            <Check className={cn("w-5 h-5 mt-0.5 shrink-0", colors.check)} />
            <span className="text-gray-700 text-sm">{feature}</span>
          </li>
        ))}
      </ul>

      {/* CTA */}
      <Link href="/login">
        <Button className={cn("w-full py-6 text-base font-semibold", colors.button)}>
          {plan.cta}
        </Button>
      </Link>

      <p className="text-xs text-gray-500 text-center mt-4">
        Activation par administrateur du Workspace
      </p>
    </div>
  );
}

function PackCard({ pack }: { pack: (typeof PACKS)[0] }) {
  const Icon = pack.icon;
  const colorClasses = {
    purple: "bg-purple-100 text-purple-600",
    blue: "bg-blue-100 text-blue-600",
    green: "bg-green-100 text-green-600",
    orange: "bg-orange-100 text-orange-600",
    pink: "bg-pink-100 text-pink-600",
    gray: "bg-gray-100 text-gray-600",
  };

  return (
    <div className="bg-white rounded-xl p-6 border border-gray-200 hover:border-purple-300 hover:shadow-md transition-all">
      <div className="flex items-center gap-3 mb-4">
        <div className={cn("p-2 rounded-lg", colorClasses[pack.color as keyof typeof colorClasses])}>
          <Icon className="w-5 h-5" />
        </div>
        <div>
          <h4 className="font-semibold text-gray-900">{pack.name}</h4>
          <p className="text-sm text-gray-500">{pack.tagline}</p>
        </div>
        {pack.adminOnly && (
          <Badge variant="outline" className="ml-auto text-xs">
            Admin
          </Badge>
        )}
      </div>
      <p className="text-sm text-gray-600 mb-4">{pack.description}</p>
      <ul className="space-y-2">
        {pack.features.map((feature) => (
          <li key={feature} className="flex items-center gap-2 text-sm text-gray-700">
            <Check className="w-4 h-4 text-green-500" />
            {feature}
          </li>
        ))}
      </ul>
    </div>
  );
}

function ComparisonTable() {
  const renderCell = (value: boolean | string) => {
    if (value === true) {
      return <Check className="w-5 h-5 text-green-600 mx-auto" />;
    }
    if (value === false) {
      return <X className="w-5 h-5 text-gray-300 mx-auto" />;
    }
    if (value === "add-on") {
      return <span className="text-xs text-orange-600 font-medium">Add-on</span>;
    }
    if (value === "admin") {
      return <span className="text-xs text-gray-500">Admin only</span>;
    }
    return <span className="text-sm font-medium text-gray-900">{value}</span>;
  };

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="border-b border-gray-200">
            <th className="text-left py-4 px-4 font-medium text-gray-500 w-1/3"></th>
            <th className="text-center py-4 px-4 font-semibold text-gray-900">Mini</th>
            <th className="text-center py-4 px-4 font-semibold text-purple-600 bg-purple-50 rounded-t-lg">
              Standard
              <Badge className="ml-2 bg-purple-600 text-white text-xs">Recommandé</Badge>
            </th>
            <th className="text-center py-4 px-4 font-semibold text-gray-900">Premium</th>
          </tr>
        </thead>
        <tbody>
          {COMPARISON_DATA.map((section) => (
            <>
              <tr key={section.category} className="bg-gray-50">
                <td
                  colSpan={4}
                  className="py-3 px-4 font-semibold text-gray-900 text-sm"
                >
                  {section.category}
                </td>
              </tr>
              {section.features.map((feature, idx) => (
                <tr
                  key={feature.name}
                  className={cn(
                    "border-b border-gray-100",
                    idx % 2 === 0 ? "bg-white" : "bg-gray-50/50"
                  )}
                >
                  <td className="py-3 px-4 text-sm text-gray-700">{feature.name}</td>
                  <td className="py-3 px-4 text-center">{renderCell(feature.mini)}</td>
                  <td className="py-3 px-4 text-center bg-purple-50/50">
                    {renderCell(feature.standard)}
                  </td>
                  <td className="py-3 px-4 text-center">{renderCell(feature.premium)}</td>
                </tr>
              ))}
            </>
          ))}
        </tbody>
      </table>
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
                "w-5 h-5 text-gray-500 transition-transform",
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
          <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold text-gray-900 mb-6">
            Choisissez le plan adapté{" "}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-600 to-pink-600">
              à votre agence
            </span>
          </h1>
          <p className="text-xl text-gray-600 mb-4 max-w-2xl mx-auto">
            Activez uniquement les packs nécessaires, par Workspace.
          </p>
          <p className="text-sm text-gray-500 mb-10">
            Radar est une plateforme privée. L'accès est validé par notre équipe.
          </p>

          {/* Toggle */}
          <PricingToggle isYearly={isYearly} onToggle={() => setIsYearly(!isYearly)} />

          {/* Quick links */}
          <div className="flex items-center justify-center gap-4 mt-8">
            <a href="#comparison">
              <Button variant="outline" className="border-gray-300">
                <Eye className="w-4 h-4 mr-2" />
                Comparer les plans
              </Button>
            </a>
            <Link href="/login">
              <Button className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white">
                Demander l'accès
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Pricing Cards */}
      <section className="py-16 bg-white">
        <div className="container mx-auto px-6">
          <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto items-start">
            {PLANS.map((plan) => (
              <PlanCard key={plan.id} plan={plan} isYearly={isYearly} />
            ))}
          </div>

          {/* Reassurance */}
          <div className="flex flex-wrap items-center justify-center gap-8 mt-16 text-sm text-gray-600">
            <div className="flex items-center gap-2">
              <RefreshCcw className="w-5 h-5 text-green-600" />
              Changez de plan à tout moment
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

      {/* Packs Section */}
      <section className="py-20 bg-gray-50">
        <div className="container mx-auto px-6">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Packs Radar
            </h2>
            <p className="text-gray-600 max-w-xl mx-auto">
              Chaque pack peut être activé ou désactivé par les administrateurs du Workspace.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-5xl mx-auto">
            {PACKS.map((pack) => (
              <PackCard key={pack.id} pack={pack} />
            ))}
          </div>
        </div>
      </section>

      {/* Comparison Table */}
      <section id="comparison" className="py-20 bg-white">
        <div className="container mx-auto px-6">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Comparatif détaillé
            </h2>
            <p className="text-gray-600">
              Retrouvez toutes les fonctionnalités par plan.
            </p>
          </div>

          <div className="max-w-5xl mx-auto bg-white rounded-2xl border border-gray-200 overflow-hidden">
            <ComparisonTable />
          </div>
        </div>
      </section>

      {/* Add-ons */}
      <section className="py-20 bg-gray-50">
        <div className="container mx-auto px-6">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Options
            </h2>
            <p className="text-gray-600">
              Ajoutez des packs supplémentaires à votre abonnement Standard.
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-6 max-w-3xl mx-auto">
            {ADD_ONS.map((addon) => {
              const Icon = addon.icon;
              return (
                <div
                  key={addon.id}
                  className="bg-white rounded-xl p-6 border border-gray-200 hover:border-purple-300 transition-all"
                >
                  <div className="flex items-center gap-4 mb-4">
                    <div className="p-3 rounded-lg bg-purple-100 text-purple-600">
                      <Icon className="w-6 h-6" />
                    </div>
                    <div>
                      <h4 className="font-semibold text-gray-900">{addon.name}</h4>
                      <p className="text-sm text-gray-500">+{addon.price}€/mois</p>
                    </div>
                  </div>
                  <p className="text-sm text-gray-600">{addon.description}</p>
                </div>
              );
            })}
          </div>

          <p className="text-center text-sm text-gray-500 mt-8">
            Activation par administrateur du Workspace
          </p>
        </div>
      </section>

      {/* FAQ */}
      <section className="py-20 bg-white">
        <div className="container mx-auto px-6">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
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
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-gray-900 mb-6">
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
              <Link href="/demo">
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
