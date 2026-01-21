"use client";

import Link from "next/link";
import { ArrowLeft } from "lucide-react";

export default function PrivacyPage() {
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
          <h1 className="text-3xl font-bold mb-8">Politique de Confidentialité</h1>
          
          <div className="space-y-6 text-gray-200">
            <section>
              <h2 className="text-xl font-semibold text-white mb-3">1. Introduction</h2>
              <p>
                Radar ("nous", "notre", "nos") s'engage à protéger la vie privée des utilisateurs 
                de notre plateforme accessible à l'adresse https://radarapp.fr. Cette politique 
                de confidentialité explique comment nous collectons, utilisons et protégeons vos 
                informations personnelles.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-white mb-3">2. Données collectées</h2>
              <p>Nous collectons les types de données suivants :</p>
              <ul className="list-disc list-inside mt-2 space-y-1">
                <li>Informations de compte : nom, adresse e-mail</li>
                <li>Données d'authentification via Google OAuth</li>
                <li>Données d'utilisation de la plateforme</li>
                <li>Informations relatives à vos projets et clients (stockées de manière sécurisée)</li>
              </ul>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-white mb-3">3. Utilisation des données</h2>
              <p>Vos données sont utilisées pour :</p>
              <ul className="list-disc list-inside mt-2 space-y-1">
                <li>Fournir et améliorer nos services</li>
                <li>Authentifier votre accès à la plateforme</li>
                <li>Synchroniser avec Google Drive et Google Calendar (si autorisé)</li>
                <li>Vous envoyer des notifications relatives à votre compte</li>
              </ul>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-white mb-3">4. Intégrations Google</h2>
              <p>
                Notre application utilise les API Google pour les fonctionnalités suivantes :
              </p>
              <ul className="list-disc list-inside mt-2 space-y-1">
                <li><strong>Google OAuth</strong> : Connexion sécurisée à votre compte</li>
                <li><strong>Google Drive</strong> : Stockage et organisation de vos fichiers projets</li>
                <li><strong>Google Calendar</strong> : Synchronisation de vos événements</li>
              </ul>
              <p className="mt-2">
                Nous n'accédons qu'aux données strictement nécessaires au fonctionnement de ces 
                fonctionnalités et ne partageons jamais vos données avec des tiers.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-white mb-3">5. Stockage et sécurité</h2>
              <p>
                Vos données sont stockées sur des serveurs sécurisés situés en Europe. 
                Nous utilisons le chiffrement SSL/TLS pour toutes les communications 
                et appliquons les meilleures pratiques de sécurité pour protéger vos informations.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-white mb-3">6. Vos droits</h2>
              <p>Conformément au RGPD, vous disposez des droits suivants :</p>
              <ul className="list-disc list-inside mt-2 space-y-1">
                <li>Droit d'accès à vos données personnelles</li>
                <li>Droit de rectification</li>
                <li>Droit à l'effacement ("droit à l'oubli")</li>
                <li>Droit à la portabilité des données</li>
                <li>Droit d'opposition au traitement</li>
              </ul>
              <p className="mt-2">
                Pour exercer ces droits, contactez-nous à : contact@radarapp.fr
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-white mb-3">7. Cookies</h2>
              <p>
                Nous utilisons des cookies essentiels pour le fonctionnement de la plateforme 
                (authentification, préférences). Aucun cookie publicitaire ou de tracking 
                n'est utilisé.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-white mb-3">8. Contact</h2>
              <p>
                Pour toute question concernant cette politique de confidentialité, 
                vous pouvez nous contacter à :
              </p>
              <p className="mt-2">
                <strong>Email</strong> : contact@radarapp.fr<br />
                <strong>Site</strong> : https://radarapp.fr
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-white mb-3">9. Modifications</h2>
              <p>
                Cette politique de confidentialité peut être mise à jour occasionnellement. 
                La date de dernière modification est indiquée ci-dessous.
              </p>
              <p className="mt-4 text-sm text-gray-400">
                Dernière mise à jour : 21 janvier 2026
              </p>
            </section>
          </div>
        </div>
      </div>
    </div>
  );
}
