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
    { label: "Contact", href: "/contact" },
  ],
};

export function LandingFooter() {
  return (
    <footer className="bg-white border-t border-gray-200">
      <div className="container mx-auto px-6 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-10">
          {/* Brand */}
          <div className="md:col-span-2">
            <Link href="/" className="flex items-center gap-3 mb-4">
              <div className="h-10 w-10 bg-gradient-to-r from-purple-500 to-pink-500 rounded-xl flex items-center justify-center">
                <Radar className="h-6 w-6 text-white" />
              </div>
              <span className="text-2xl font-bold text-gray-900">Radar</span>
            </Link>
            <p className="text-gray-600 max-w-sm mb-6">
              Le cockpit pour piloter votre agence. Pipeline, projets, facturation, analytics — unifié avec Google Workspace et vos banques.
            </p>
            <div className="flex items-center gap-4 text-sm text-gray-500">
              <span>Made in France</span>
              <span>•</span>
              <span>RGPD Conforme</span>
              <span>•</span>
              <a
                href="https://www.cloudflare.com"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 text-gray-500 hover:text-gray-700 transition-colors"
                title="Protégé par Cloudflare"
              >
                <svg className="h-4 w-4" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M44.52 40.68H18.6l-.47-1.65c-.26-.9-.15-1.82.3-2.58a3.05 3.05 0 0 1 2.17-1.44l1.77-.23.74-1.63a10.28 10.28 0 0 1 9.42-5.98c3.83 0 7.24 2.12 9 5.45l.63 1.19 1.33.1a5.86 5.86 0 0 1 5.36 4.63l.23 1.1-1.1.23a2.66 2.66 0 0 0-.42.08l-2.54.73z" fill="#F6821F"/>
                  <path d="M48.42 40.68h-3.9l.56-1.62a2.64 2.64 0 0 0-.16-2.22 2.6 2.6 0 0 0-1.88-1.26l-1.92-.24-.8-1.72A11.67 11.67 0 0 0 29.82 27a11.68 11.68 0 0 0-10.87 7.08l-.28.63-1.1.15a4.63 4.63 0 0 0-3.92 3.4c-.14.52-.13 1.04.04 1.5l.12.37a1.56 1.56 0 0 0-.95 1.63c.1.77.8 1.35 1.58 1.35h34a1.54 1.54 0 0 0 1.54-1.2c.12-.56-.12-1.1-.56-1.23z" fill="#FBAD41"/>
                  <path d="M49.9 33.15l-.68.02-.3-.65a7.86 7.86 0 0 0-7.06-4.38c-1.52 0-2.97.43-4.22 1.23l-.6.38-.44-.55a12.22 12.22 0 0 0-.82-.88l1.17-.74a9.6 9.6 0 0 1 4.91-1.35 9.58 9.58 0 0 1 8.7 5.55l.17.38.48-.02c3.03.04 5.42 2.56 5.42 5.6a5.64 5.64 0 0 1-3.36 5.14l-.73-1.45a3.92 3.92 0 0 0 2.37-3.6 3.93 3.93 0 0 0-4.01-3.88z" fill="#F6821F"/>
                </svg>
                Cloudflare
              </a>
            </div>
          </div>

          {/* Produit */}
          <div>
            <h4 className="text-gray-900 font-semibold mb-4">Produit</h4>
            <ul className="space-y-3">
              {footerLinks.produit.map((link) => (
                <li key={link.href}>
                  <a
                    href={link.href}
                    className="text-gray-600 hover:text-gray-900 transition-colors text-sm"
                  >
                    {link.label}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          {/* Légal */}
          <div>
            <h4 className="text-gray-900 font-semibold mb-4">Légal</h4>
            <ul className="space-y-3">
              {footerLinks.legal.map((link) => (
                <li key={link.href}>
                  <Link
                    href={link.href}
                    className="text-gray-600 hover:text-gray-900 transition-colors text-sm"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Bottom */}
        <div className="mt-12 pt-8 border-t border-gray-200 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-sm text-gray-500">
            © {new Date().getFullYear()} Radar. Tous droits réservés.
          </p>
          <div className="flex items-center gap-2">
            <div className="h-2 w-2 bg-green-500 rounded-full animate-pulse" />
            <span className="text-sm text-gray-600">Tous les systèmes opérationnels</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
