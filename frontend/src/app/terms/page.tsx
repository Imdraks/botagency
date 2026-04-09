"use client";

import Link from "next/link";
import { ArrowLeft } from "lucide-react";

export default function TermsPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      <div className="container mx-auto px-4 py-12 max-w-4xl">
        <Link 
          href="/"
          className="inline-flex items-center gap-2 text-purple-300 hover:text-white mb-8"
        >
          <ArrowLeft className="h-4 w-4" />
          Retour à l'accueil
        </Link>

        <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-8 text-white">
          <h1 className="text-3xl font-bold mb-8">Conditions Générales d'Utilisation</h1>
          
          <div className="space-y-6 text-gray-200">
            <section>
              <h2 className="text-xl font-semibold text-white mb-3">1. Objet</h2>
              <p>
                Les présentes Conditions Générales d'Utilisation (CGU) régissent l'accès et 
                l'utilisation de la plateforme Radar, accessible à l'adresse https://radarapp.fr.
                En utilisant notre service, vous acceptez ces conditions dans leur intégralité.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-white mb-3">2. Description du service</h2>
              <p>
                Radar est une plateforme de gestion d'opportunités événementielles destinée aux 
                professionnels de l'industrie musicale. Le service permet de :
              </p>
              <ul className="list-disc list-inside mt-2 space-y-1">
                <li>Détecter et suivre des opportunités (festivals, événements, appels d'offres)</li>
                <li>Gérer des projets et des livrables</li>
                <li>Organiser des fichiers via l'intégration Google Drive</li>
                <li>Synchroniser des événements avec Google Calendar</li>
                <li>Collaborer en équipe au sein d'espaces de travail partagés</li>
              </ul>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-white mb-3">3. Accès au service</h2>
              <p>
                L'accès à Radar nécessite la création d'un compte utilisateur. 
                Vous pouvez vous inscrire via :
              </p>
              <ul className="list-disc list-inside mt-2 space-y-1">
                <li>Un compte email avec mot de passe</li>
                <li>L'authentification Google OAuth</li>
              </ul>
              <p className="mt-2">
                Vous êtes responsable de la confidentialité de vos identifiants 
                et de toutes les activités effectuées sous votre compte.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-white mb-3">4. Utilisation des API Google</h2>
              <p>
                Notre application utilise les API Google conformément aux 
                <a 
                  href="https://developers.google.com/terms/api-services-user-data-policy" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-purple-300 hover:text-white ml-1"
                >
                  Règles relatives aux données utilisateur des services API Google
                </a>.
              </p>
              <ul className="list-disc list-inside mt-2 space-y-1">
                <li><strong>Google Drive</strong> : Création de dossiers pour organiser vos projets</li>
                <li><strong>Google Calendar</strong> : Création d'événements pour vos deadlines</li>
              </ul>
              <p className="mt-2">
                Ces intégrations sont optionnelles et activées uniquement avec votre consentement explicite.
                Vous pouvez révoquer ces accès à tout moment depuis les paramètres de votre compte.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-white mb-3">5. Propriété intellectuelle</h2>
              <p>
                Le contenu de la plateforme (interface, logos, textes, code source) est protégé 
                par le droit d'auteur. Vous conservez tous les droits sur les données que vous 
                importez dans Radar.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-white mb-3">6. Responsabilités</h2>
              <p>
                Radar s'engage à fournir un service de qualité et sécurisé. Cependant :
              </p>
              <ul className="list-disc list-inside mt-2 space-y-1">
                <li>Le service est fourni "tel quel", sans garantie de disponibilité permanente</li>
                <li>Nous ne sommes pas responsables des contenus que vous publiez</li>
                <li>Les interruptions pour maintenance seront annoncées à l'avance si possible</li>
              </ul>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-white mb-3">7. Protection des données</h2>
              <p>
                Nous traitons vos données personnelles conformément au RGPD et à notre 
                <Link href="/privacy" className="text-purple-300 hover:text-white ml-1">
                  Politique de Confidentialité
                </Link>.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-white mb-3">8. Résiliation</h2>
              <p>
                Vous pouvez supprimer votre compte à tout moment depuis les paramètres. 
                Nous nous réservons le droit de suspendre ou supprimer un compte en cas 
                de violation de ces conditions.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-white mb-3">9. Modifications</h2>
              <p>
                Ces conditions peuvent être modifiées à tout moment. Les utilisateurs seront 
                informés des changements significatifs par email ou notification dans l'application.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-white mb-3">10. Droit applicable</h2>
              <p>
                Ces conditions sont régies par le droit français. Tout litige sera soumis 
                aux tribunaux compétents de Paris.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-white mb-3">11. Contact</h2>
              <p>
                Pour toute question concernant ces conditions :
              </p>
              <p className="mt-2">
                <strong>Email</strong> : contact@radarapp.fr<br />
                <strong>Site</strong> : https://radarapp.fr
              </p>
              <p className="mt-2">
                Voir également nos{" "}
                <Link href="/legal" className="text-purple-300 hover:text-white">
                  Mentions Légales
                </Link>{" "}et notre{" "}
                <Link href="/privacy" className="text-purple-300 hover:text-white">
                  Politique de Confidentialité
                </Link>.
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
