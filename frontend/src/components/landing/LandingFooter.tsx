"use client";

import Link from "next/link";
import { Radar } from "lucide-react";

const footerLinks = {
  produit: [
    { label: "Fonctionnalités", href: "#produit" },
    { label: "Intégrations", href: "#integrations" },
    { label: "Sécurité", href: "#securite" },
    { label: "FAQ", href: "#faq" },
  ],
  legal: [
    { label: "Confidentialité", href: "/privacy" },
    { label: "CGU", href: "/terms" },
  ],
};

export function LandingFooter() {
  return (
    <footer className="bg-slate-900 border-t border-white/10">
      <div className="container mx-auto px-6 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-10">
          {/* Brand */}
          <div className="md:col-span-2">
            <Link href="/" className="flex items-center gap-3 mb-4">
              <div className="h-10 w-10 bg-gradient-to-r from-purple-500 to-pink-500 rounded-xl flex items-center justify-center">
                <Radar className="h-6 w-6 text-white" />
              </div>
              <span className="text-2xl font-bold text-white">Radar</span>
            </Link>
            <p className="text-gray-400 max-w-sm mb-6">
              Le cockpit pour piloter votre agence. Pipeline, projets, production, assets — unifié avec Google Workspace.
            </p>
            <div className="flex items-center gap-4 text-sm text-gray-500">
              <span>🇫🇷 Made in France</span>
              <span>•</span>
              <span>RGPD Conforme</span>
            </div>
          </div>

          {/* Produit */}
          <div>
            <h4 className="text-white font-semibold mb-4">Produit</h4>
            <ul className="space-y-3">
              {footerLinks.produit.map((link) => (
                <li key={link.href}>
                  <a
                    href={link.href}
                    className="text-gray-400 hover:text-white transition-colors text-sm"
                  >
                    {link.label}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          {/* Légal */}
          <div>
            <h4 className="text-white font-semibold mb-4">Légal</h4>
            <ul className="space-y-3">
              {footerLinks.legal.map((link) => (
                <li key={link.href}>
                  <Link
                    href={link.href}
                    className="text-gray-400 hover:text-white transition-colors text-sm"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Bottom */}
        <div className="mt-12 pt-8 border-t border-white/10 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-sm text-gray-500">
            © {new Date().getFullYear()} Radar. Tous droits réservés.
          </p>
          <div className="flex items-center gap-2">
            <div className="h-2 w-2 bg-green-500 rounded-full animate-pulse" />
            <span className="text-sm text-gray-400">Tous les systèmes opérationnels</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
