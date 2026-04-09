import {
  LandingWrapper,
  LandingHeader,
  Hero,
  Workflow,
  FeaturesGrid,
  WhyRadar,
  Integrations,
  Security,
  FAQ,
  Pricing,
  FinalCTA,
  LandingFooter,
  ForceLightMode,
} from "@/components/landing";

export const metadata = {
  title: "Radar - Le cockpit pour piloter votre agence de production",
  description:
    "Pipeline, projets, facturation, découverte artistes, analytics et veille concurrentielle — unifié avec Google Workspace et Revolut. La plateforme tout-en-un pour les agences de production musicale.",
  keywords: ["agence", "production musicale", "gestion de projet", "pipeline", "CRM", "facturation", "devis", "découverte artistes", "Google Workspace", "analytics", "veille concurrentielle"],
  openGraph: {
    title: "Radar - Le cockpit pour piloter votre agence de production",
    description:
      "Pipeline, projets, facturation, découverte artistes et analytics — unifié avec Google Workspace et Revolut.",
    type: "website",
    locale: "fr_FR",
    siteName: "Radar",
  },
};

export default function HomePage() {
  return (
    <ForceLightMode>
      <LandingWrapper>
        <main className="min-h-screen bg-white text-gray-900">
          <LandingHeader />
          <Hero />
          <FeaturesGrid />
          <WhyRadar />
          <Workflow />
          <Integrations />
          <Security />
          <Pricing />
          <FAQ />
          <FinalCTA />
          <LandingFooter />
        </main>
      </LandingWrapper>
    </ForceLightMode>
  );
}
