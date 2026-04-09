import { Metadata } from "next";

export const metadata: Metadata = {
  title: "Contact",
  description:
    "Contactez l'équipe Radar. Une question sur nos offres ? Besoin d'une démo personnalisée ? Nous répondons sous 24h.",
  alternates: {
    canonical: "/contact",
  },
  openGraph: {
    title: "Contactez-nous | Radar",
    description:
      "Une question sur Radar ? Notre équipe vous répond sous 24h.",
    url: "/contact",
  },
};

export default function ContactLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
