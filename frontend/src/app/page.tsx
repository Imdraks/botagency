import {
  LandingHeader,
  Hero,
  Workflow,
  FeaturesGrid,
  Integrations,
  Security,
  FAQ,
  FinalCTA,
  LandingFooter,
} from "@/components/landing";

export const metadata = {
  title: "Radar - Le cockpit pour piloter votre agence",
  description:
    "Pipeline, projets, production, assets, calendrier — unifié avec Google Workspace. La plateforme tout-en-un pour les agences.",
  keywords: ["agence", "gestion de projet", "pipeline", "CRM", "Google Workspace", "production"],
  openGraph: {
    title: "Radar - Le cockpit pour piloter votre agence",
    description:
      "Pipeline, projets, production, assets, calendrier — unifié avec Google Workspace.",
    type: "website",
    locale: "fr_FR",
    siteName: "Radar",
  },
};

export default function HomePage() {
  return (
    <main className="min-h-screen bg-slate-900">
      <LandingHeader />
      <Hero />
      <Workflow />
      <FeaturesGrid />
      <Integrations />
      <Security />
      <FAQ />
      <FinalCTA />
      <LandingFooter />
    </main>
  );
}
