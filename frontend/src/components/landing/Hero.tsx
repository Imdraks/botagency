"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ArrowRight, ArrowDown, Play } from "lucide-react";
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
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-purple-100 rounded-full blur-3xl" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-pink-100 rounded-full blur-3xl" />

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
              Nouveau: Intégration Google Drive automatique
            </div>

            {/* Headline */}
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-gray-900 mb-6 leading-tight">
              Votre{" "}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-600 to-pink-600">
                cockpit
              </span>{" "}
              pour piloter votre agence
            </h1>

            {/* Subheadline */}
            <p className="text-lg sm:text-xl text-gray-600 mb-8 max-w-xl mx-auto lg:mx-0">
              Pipeline + projets + production + assets + calendrier.
              <br />
              <span className="text-gray-900 font-medium">Unifié avec Google Workspace.</span>
            </p>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center lg:justify-start">
              <Link href={isLoggedIn ? "/today" : "/login"}>
                <Button
                  size="lg"
                  className="w-full sm:w-auto bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white text-lg px-8 py-6 rounded-xl"
                >
                  {isLoggedIn ? "Accéder au dashboard" : "Commencer gratuitement"}
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Button>
              </Link>
              <a href="#produit">
                <Button
                  size="lg"
                  variant="outline"
                  className="w-full sm:w-auto border-gray-300 text-gray-900 hover:bg-gray-100 text-lg px-8 py-6 rounded-xl"
                >
                  <Play className="mr-2 h-5 w-5" />
                  Voir le produit
                </Button>
              </a>
            </div>

            {/* Trust badges */}
            <div className="flex flex-wrap items-center gap-6 mt-10 justify-center lg:justify-start text-sm text-gray-500">
              <div className="flex items-center gap-2">
                <div className="h-2 w-2 bg-green-500 rounded-full" />
                RGPD Conforme
              </div>
              <div className="flex items-center gap-2">
                <div className="h-2 w-2 bg-green-500 rounded-full" />
                Hébergé en Europe
              </div>
              <div className="flex items-center gap-2">
                <div className="h-2 w-2 bg-green-500 rounded-full" />
                Made in France 🇫🇷
              </div>
            </div>
          </div>

          {/* Right: Product Preview */}
          <div className="relative">
            <div className="relative bg-white rounded-2xl border border-gray-200 shadow-2xl overflow-hidden">
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

              {/* Screenshot Placeholder */}
              <div className="aspect-[16/10] bg-gradient-to-br from-gray-100 to-gray-50 p-6">
                {/* Mock Dashboard */}
                <div className="h-full flex flex-col gap-4">
                  {/* Top bar */}
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

                  {/* Content Grid */}
                  <div className="flex-1 grid grid-cols-3 gap-4">
                    {/* Sidebar */}
                    <div className="col-span-1 space-y-2">
                      {[...Array(6)].map((_, i) => (
                        <div
                          key={i}
                          className={`h-8 rounded-lg ${i === 0 ? "bg-purple-200" : "bg-gray-200"}`}
                        />
                      ))}
                    </div>

                    {/* Main Content */}
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
                      <div className="grid grid-cols-5 gap-2 mt-4">
                        {[...Array(5)].map((_, i) => (
                          <div key={i} className="space-y-2">
                            <div className="h-4 w-full bg-gray-300 rounded" />
                            {[...Array(3)].map((_, j) => (
                              <div
                                key={j}
                                className="h-12 bg-white rounded-lg border border-gray-200"
                              />
                            ))}
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Floating Elements */}
            <div className="absolute -bottom-4 -left-4 bg-white rounded-xl shadow-xl p-4 flex items-center gap-3">
              <div className="h-10 w-10 bg-green-100 rounded-full flex items-center justify-center">
                <svg className="h-5 w-5 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <div>
                <div className="text-sm font-semibold text-gray-900">Deal converti</div>
                <div className="text-xs text-gray-500">Client: Acme Corp</div>
              </div>
            </div>

            <div className="absolute -top-4 -right-4 bg-white rounded-xl shadow-xl p-4">
              <div className="flex items-center gap-2 text-sm">
                <div className="h-8 w-8 bg-purple-100 rounded-full flex items-center justify-center">
                  <span className="text-purple-600 font-bold">+3</span>
                </div>
                <div className="text-gray-900 font-medium">Nouveaux leads</div>
              </div>
            </div>
          </div>
        </div>

        {/* Scroll indicator */}
        <div className="absolute bottom-8 left-1/2 -translate-x-1/2 hidden lg:block">
          <a
            href="#workflow"
            className="flex flex-col items-center gap-2 text-gray-400 hover:text-white transition-colors"
          >
            <span className="text-sm">Découvrir</span>
            <ArrowDown className="h-5 w-5 animate-bounce" />
          </a>
        </div>
      </div>
    </section>
  );
}
