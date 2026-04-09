"use client";

import Link from "next/link";
import { ArrowLeft } from "lucide-react";

export default function LegalPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      <div className="container mx-auto px-4 py-12 max-w-4xl">
        <Link 
          href="/"
          className="inline-flex items-center gap-2 text-purple-300 hover:text-white mb-8"
        >
          <ArrowLeft className="h-4 w-4" />
          Retour à l&apos;accueil
        </Link>

        <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-8 text-white">
          <h1 className="text-3xl font-bold mb-8">Mentions Légales</h1>
          
          <div className="space-y-6 text-gray-200">
            <section>
              <h2 className="text-xl font-semibold text-white mb-3">1. Éditeur du site</h2>
              <p>Le site https://radarapp.fr est édité par :</p>
              <ul className="list-none mt-2 space-y-1">
                <li><strong>Raison sociale</strong> : [À COMPLÉTER] — SASU</li>
                <li><strong>Siège social</strong> : [À COMPLÉTER]</li>
                <li><strong>SIRET</strong> : [À COMPLÉTER]</li>
                <li><strong>RCS</strong> : [À COMPLÉTER]</li>
                <li><strong>Capital social</strong> : [À COMPLÉTER]</li>
                <li><strong>Président</strong> : [À COMPLÉTER]</li>
                <li><strong>Directeur de la publication</strong> : [À COMPLÉTER]</li>
                <li><strong>Email</strong> : contact@radarapp.fr</li>
              </ul>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-white mb-3">2. Hébergeur</h2>
              <p>Le site est hébergé par :</p>
              <ul className="list-none mt-2 space-y-1">
                <li><strong>OVH SAS</strong></li>
                <li>2 rue Kellermann — 59100 Roubaix, France</li>
                <li>Téléphone : 1007</li>
                <li>Site : <a href="https://www.ovhcloud.com" target="_blank" rel="noopener noreferrer" className="text-purple-300 hover:text-white">www.ovhcloud.com</a></li>
              </ul>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-white mb-3">3. Propriété intellectuelle</h2>
              <p>
                L&apos;ensemble du contenu du site (textes, images, graphismes, logo, icônes, logiciels, 
                base de données) est la propriété exclusive de l&apos;éditeur ou de ses partenaires et est 
                protégé par les lois françaises et internationales relatives à la propriété intellectuelle.
              </p>
              <p className="mt-2">
                Toute reproduction, représentation, modification, publication ou adaptation de tout ou 
                partie des éléments du site, quel que soit le moyen ou le procédé utilisé, est interdite 
                sans autorisation écrite préalable.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-white mb-3">4. Protection des données personnelles</h2>
              <p>
                Conformément au Règlement Général sur la Protection des Données (RGPD) et à la loi 
                Informatique et Libertés du 6 janvier 1978 modifiée, vous disposez d&apos;un droit d&apos;accès, 
                de rectification, de suppression et de portabilité de vos données personnelles.
              </p>
              <p className="mt-2">
                Pour plus d&apos;informations, consultez notre{" "}
                <Link href="/privacy" className="text-purple-300 hover:text-white">
                  Politique de Confidentialité
                </Link>.
              </p>
              <p className="mt-2">
                Pour exercer vos droits, contactez-nous à : <strong>contact@radarapp.fr</strong>
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-white mb-3">5. Cookies</h2>
              <p>
                Le site utilise des cookies essentiels au fonctionnement du service (authentification, 
                préférences utilisateur) ainsi que des cookies analytiques (Google Analytics) soumis 
                à votre consentement via le bandeau de gestion des cookies.
              </p>
              <p className="mt-2">
                Pour en savoir plus, consultez notre{" "}
                <Link href="/privacy" className="text-purple-300 hover:text-white">
                  Politique de Confidentialité
                </Link>.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-white mb-3">6. Responsabilité</h2>
              <p>
                L&apos;éditeur s&apos;efforce de fournir des informations aussi précises que possible. 
                Toutefois, il ne pourra être tenu responsable des omissions, des inexactitudes 
                et des carences dans la mise à jour, qu&apos;elles soient de son fait ou du fait 
                des tiers partenaires qui lui fournissent ces informations.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-white mb-3">7. Droit applicable</h2>
              <p>
                Les présentes mentions légales sont régies par le droit français. En cas de litige, 
                les tribunaux français seront seuls compétents.
              </p>
            </section>

            <p className="mt-8 text-sm text-gray-400">
              Dernière mise à jour : 9 avril 2026
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
