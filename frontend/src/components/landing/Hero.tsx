"use client";

import Link from "next/link";
import Image from "next/image";
import { useEffect, useState } from "react";
import { ArrowRight, ArrowDown, Eye } from "lucide-react";
import { Button } from "@/components/ui/button";

export function Hero() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (token) setIsLoggedIn(true);
  }, []);

  return (
    <section className="relative min-h-screen flex items-center pt-24 pb-16 overflow-hidden">
      {/* Background Effects */}
      <div className="absolute inset-0 bg-gradient-to-br from-gray-50 via-white to-gray-50" />
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-purple-100 rounded-full blur-3xl opacity-60" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-pink-100 rounded-full blur-3xl opacity-60" />

      <div className="container mx-auto px-6 relative z-10">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          {/* Left: Content */}
          <div className="text-center lg:text-left">
            {/* Badge */}
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-purple-50 rounded-full text-sm text-purple-600 mb-6">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-purple-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-purple-500"></span>
              </span>
              Pensé pour les agences
            </div>

            {/* Headline */}
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold mb-6 leading-tight text-gray-900 dark:!text-gray-900" style={{ color: '#111827' }}>
              <span style={{ color: '#111827' }}>Le</span>{" "}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-600 to-pink-600" style={{ color: 'transparent', WebkitBackgroundClip: 'text', backgroundClip: 'text' }}>
                cockpit
              </span>{" "}
              <span style={{ color: '#111827' }}>pour piloter votre agence</span>
            </h1>

            {/* Subheadline - Pain → Solution */}
            <p className="text-lg sm:text-xl text-gray-600 mb-4 max-w-xl mx-auto lg:mx-0">
              Centralisez pipeline, projets, production et assets.
            </p>
            <p className="text-lg sm:text-xl text-gray-900 font-medium mb-8 max-w-xl mx-auto lg:mx-0">
              Fin des infos éparpillées entre Drive, Notion et messages.
            </p>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center lg:justify-start">
              <Link href={isLoggedIn ? "/today" : "/login"}>
                <Button
                  size="lg"
                  className="w-full sm:w-auto bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white text-lg px-8 py-6 rounded-xl btn-press"
                >
                  {isLoggedIn ? "Accéder au dashboard" : "Se connecter"}
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Button>
              </Link>
              <a href="#produit">
                <Button
                  size="lg"
                  variant="outline"
                  className="w-full sm:w-auto border-gray-300 text-gray-900 hover:bg-gray-100 text-lg px-8 py-6 rounded-xl btn-press"
                >
                  <Eye className="mr-2 h-5 w-5" />
                  Voir le produit
                </Button>
              </a>
            </div>

            {/* Trust badges - Micro-ligne de confiance */}
            <div className="flex flex-wrap items-center gap-4 mt-10 justify-center lg:justify-start text-sm text-gray-500">
              <span>Pensé pour les agences</span>
              <span className="text-gray-300">•</span>
              <span>Intégré à Google Workspace</span>
              <span className="text-gray-300">•</span>
              <span>RGPD</span>
            </div>
          </div>

          {/* Right: Product Screenshot */}
          <div className="relative">
            <div className="relative bg-white rounded-2xl border border-gray-200 shadow-2xl overflow-hidden card-hover">
              {/* Browser Chrome */}
              <div className="flex items-center gap-2 px-4 py-3 bg-gray-50 border-b border-gray-200">
                <div className="flex gap-1.5">
                  <div className="h-3 w-3 rounded-full bg-red-500/80" />
                  <div className="h-3 w-3 rounded-full bg-yellow-500/80" />
                  <div className="h-3 w-3 rounded-full bg-green-500/80" />
                </div>
                <div className="flex-1 flex justify-center">
                  <div className="px-4 py-1 bg-gray-200 rounded-lg text-xs text-gray-600">
                    radarapp.fr/today
                  </div>
                </div>
              </div>

              {/* Real Screenshot - Dashboard Today */}
              <div className="aspect-[16/10] bg-gradient-to-br from-gray-900 to-gray-800 relative">
                <Image
                  src="/screenshots/dashboard-today.png"
                  alt="Dashboard Radar - Vue Today avec pipeline et projets"
                  fill
                  className="object-cover object-top"
                  priority
                  sizes="(max-width: 768px) 100vw, 50vw"
                />
                {/* Fallback gradient si pas d'image */}
                <div className="absolute inset-0 bg-gradient-to-br from-gray-100 to-gray-50 -z-10">
                  {/* Mock Dashboard Fallback */}
                  <div className="h-full flex flex-col gap-4 p-6">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="h-8 w-8 bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg" />
                        <div className="h-4 w-20 bg-gray-300 rounded" />
                      </div>
                      <div className="flex gap-2">
                        <div className="h-8 w-8 bg-gray-200 rounded-lg" />
                        <div className="h-8 w-8 bg-gray-200 rounded-lg" />
                      </div>
                    </div>
                    <div className="flex-1 grid grid-cols-3 gap-4">
                      <div className="col-span-1 space-y-2">
                        {[...Array(5)].map((_, i) => (
                          <div key={i} className={`h-8 rounded-lg ${i === 0 ? "bg-purple-200" : "bg-gray-200"}`} />
                        ))}
                      </div>
                      <div className="col-span-2 space-y-3">
                        <div className="h-6 w-32 bg-gray-300 rounded" />
                        <div className="grid grid-cols-4 gap-2">
                          {[...Array(4)].map((_, i) => (
                            <div key={i} className="h-16 bg-white rounded-lg p-2 border border-gray-200">
                              <div className="h-3 w-8 bg-gray-300 rounded mb-2" />
                              <div className="h-6 w-12 bg-purple-200 rounded" />
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Floating Elements */}
            <div className="absolute -bottom-4 -left-4 bg-white rounded-xl shadow-xl p-4 flex items-center gap-3 animate-fade-in">
              <div className="h-10 w-10 bg-green-100 rounded-full flex items-center justify-center">
                <svg className="h-5 w-5 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <div>
                <div className="text-sm font-semibold text-gray-900">Deal converti</div>
                <div className="text-xs text-gray-500">Projet créé automatiquement</div>
              </div>
            </div>

            <div className="absolute -top-4 -right-4 bg-white rounded-xl shadow-xl p-4 animate-fade-in">
              <div className="flex items-center gap-2 text-sm">
                <div className="h-8 w-8 bg-purple-100 rounded-full flex items-center justify-center">
                  <span className="text-purple-600 font-bold text-xs">GD</span>
                </div>
                <div className="text-gray-900 font-medium">Synchro Drive</div>
              </div>
            </div>
          </div>
        </div>

        {/* Scroll indicator */}
        <div className="absolute bottom-8 left-1/2 -translate-x-1/2 hidden lg:block">
          <a href="#produit" className="flex flex-col items-center gap-2 text-gray-400 hover:text-gray-600 transition-colors">
            <span className="text-sm">Découvrir</span>
            <ArrowDown className="h-5 w-5 animate-bounce" />
          </a>
        </div>
      </div>
    </section>
  );
}
