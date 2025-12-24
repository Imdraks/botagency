"use client";

import { useEffect } from "react";
import { useOnboarding, OnboardingStep } from "./OnboardingContext";

// Define the onboarding steps for the dashboard
const DASHBOARD_STEPS: OnboardingStep[] = [
  {
    id: "welcome-stats",
    target: "[data-onboarding='stats-cards']",
    title: "Tableau de bord",
    description:
      "Bienvenue ! Ici vous voyez un aperçu de vos opportunités : le nombre total, les nouvelles détectées, les urgentes à traiter et le score moyen de pertinence.",
    position: "bottom",
  },
  {
    id: "opportunities-list",
    target: "[data-onboarding='opportunities-list']",
    title: "Liste des opportunités",
    description:
      "Vos opportunités détectées apparaissent ici avec leur score, deadline et statut. Cliquez sur une opportunité pour voir les détails et prendre action.",
    position: "left",
  },
  {
    id: "search-artist",
    target: "[data-onboarding='search-artist']",
    title: "Recherche intelligente",
    description:
      "Recherchez un artiste pour obtenir son analyse complète : données Spotify, réseaux sociaux, estimation de cachet et score global. Tapez un nom et laissez l'IA faire le reste !",
    position: "bottom",
  },
  {
    id: "emerging-artists",
    target: "[data-onboarding='emerging-artists']",
    title: "Artistes émergents",
    description:
      "Découvrez les artistes en forte croissance détectés automatiquement. Parfait pour identifier les talents avant qu'ils n'explosent !",
    position: "left",
  },
  {
    id: "ingestion-status",
    target: "[data-onboarding='ingestion-status']",
    title: "Sources d'ingestion",
    description:
      "Suivez l'état de vos sources de données : emails, flux RSS, sites web. Les opportunités sont détectées automatiquement à partir de ces sources.",
    position: "left",
  },
  {
    id: "sidebar-nav",
    target: "[data-onboarding='sidebar']",
    title: "Navigation",
    description:
      "Utilisez le menu latéral pour accéder aux différentes sections : opportunités détaillées, sources, historique des artistes analysés et paramètres.",
    position: "right",
  },
  {
    id: "user-menu",
    target: "[data-onboarding='user-menu']",
    title: "Votre compte",
    description:
      "Accédez à vos paramètres, gérez votre profil et retrouvez ce tutoriel à tout moment depuis le menu utilisateur. Bonne exploration ! 🚀",
    position: "bottom",
  },
];

export function DashboardOnboarding() {
  const { setSteps } = useOnboarding();

  useEffect(() => {
    // Set the steps when this component mounts
    setSteps(DASHBOARD_STEPS);
  }, [setSteps]);

  return null; // This component just sets up the steps
}
