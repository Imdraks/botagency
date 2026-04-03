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
  title: "Radar - Le cockpit pour piloter votre agence",
  description:
    "Pipeline, projets, facturation, analytics — unifié avec Google Workspace et Revolut. La plateforme tout-en-un pour les agences.",
  keywords: ["agence", "gestion de projet", "pipeline", "CRM", "facturation", "devis", "Google Workspace", "analytics"],
  openGraph: {
    title: "Radar - Le cockpit pour piloter votre agence",
    description:
      "Pipeline, projets, facturation, analytics — unifié avec Google Workspace et Revolut.",
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
