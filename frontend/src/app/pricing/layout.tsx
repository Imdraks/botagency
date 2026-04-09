import { Metadata } from "next";

export const metadata: Metadata = {
  title: "Abonnements & Tarifs",
  description:
    "Découvrez les packs Radar : Core, Business, Talents et Intelligence. Pipeline, facturation, découverte artistes et analytics pour votre agence de production musicale.",
  alternates: {
    canonical: "/pricing",
  },
  openGraph: {
    title: "Abonnements & Tarifs | Radar",
    description:
      "Découvrez les packs Radar pour piloter votre agence. Essai gratuit, sans engagement.",
    url: "/pricing",
  },
};

export default function PricingLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
