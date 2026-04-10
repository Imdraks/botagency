"use client";

import { Shield, Server, Lock, Users, Eye, FileCheck } from "lucide-react";

const securityFeatures = [
  {
    icon: Server,
    title: "Hébergé en Europe",
    description: "Vos données restent sur des serveurs européens certifiés.",
  },
  {
    icon: Shield,
    title: "RGPD Conforme",
    description: "Respect total de la réglementation européenne sur les données.",
  },
  {
    icon: Lock,
    title: "Chiffrement SSL",
    description: "Toutes les communications sont chiffrées de bout en bout.",
  },
  {
    icon: Users,
    title: "Rôles & Permissions",
    description: "Contrôlez qui voit quoi. Admin, Manager, Viewer.",
  },
  {
    icon: Eye,
    title: "Audit Trail",
    description: "Traçabilité complète des actions sur la plateforme.",
  },
  {
    icon: FileCheck,
    title: "Backups quotidiens",
    description: "Sauvegardes automatiques et restauration possible.",
  },
];

const stats = [
  { value: "100%", label: "Sécurisé" },
  { value: "RGPD", label: "Conforme" },
  { value: "99.9%", label: "Uptime" },
  { value: "FR", label: "Made in France" },
];

export function Security() {
  return (
    <section id="securite" className="py-24 bg-white">
      <div className="container mx-auto px-6">
        {/* Header */}
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-green-100 rounded-full text-sm text-green-700 mb-4">
            <Shield className="h-4 w-4" />
            Sécurité & Conformité
          </div>
          <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
            Vos données en sécurité
          </h2>
          <p className="text-gray-600 max-w-2xl mx-auto">
            Radar est conçu pour les agences qui prennent la sécurité au sérieux.
            Infrastructure robuste, conforme aux standards européens.
          </p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-16">
          {stats.map((stat) => (
            <div
              key={stat.label}
              className="bg-gray-50 border border-gray-200 rounded-xl p-6 text-center"
            >
              <div className="text-3xl font-bold text-gray-900 mb-1">{stat.value}</div>
              <div className="text-sm text-gray-600">{stat.label}</div>
            </div>
          ))}
        </div>

        {/* Features Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {securityFeatures.map((feature) => (
            <div
              key={feature.title}
              className="flex items-start gap-4 bg-gray-50 border border-gray-200 rounded-xl p-5 hover:border-green-300 transition-colors"
            >
              <div className="h-10 w-10 rounded-lg bg-green-100 flex items-center justify-center flex-shrink-0">
                <feature.icon className="h-5 w-5 text-green-700" />
              </div>
              <div>
                <h3 className="text-gray-900 font-semibold mb-1">{feature.title}</h3>
                <p className="text-gray-600 text-sm">{feature.description}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
