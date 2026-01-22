"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ArrowRight, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";

export function FinalCTA() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (token) setIsLoggedIn(true);
  }, []);

  return (
    <section className="py-24 bg-gradient-to-b from-slate-900 to-slate-800 relative overflow-hidden">
      {/* Background effects */}
      <div className="absolute inset-0">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-purple-500/20 rounded-full blur-[120px]" />
      </div>

      <div className="container mx-auto px-6 relative z-10">
        <div className="max-w-3xl mx-auto text-center">
          {/* Icon */}
          <div className="inline-flex items-center justify-center h-16 w-16 rounded-2xl bg-gradient-to-r from-purple-500 to-pink-500 mb-8">
            <Sparkles className="h-8 w-8 text-white" />
          </div>

          {/* Headline */}
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-white mb-6">
            Prêt à centraliser votre agence ?
          </h2>

          {/* Subheadline */}
          <p className="text-lg text-gray-400 mb-10 max-w-xl mx-auto">
            Rejoignez les agences qui ont choisi Radar pour piloter leur croissance.
            Fini les infos éparpillées, place à la clarté.
          </p>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href={isLoggedIn ? "/today" : "/login"}>
              <Button
                size="lg"
                className="w-full sm:w-auto bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white text-lg px-8 py-6 rounded-xl"
              >
                {isLoggedIn ? "Accéder au dashboard" : "Commencer maintenant"}
                <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            </Link>
            <Link href="/login">
              <Button
                size="lg"
                variant="outline"
                className="w-full sm:w-auto border-white/20 text-white hover:bg-white/10 text-lg px-8 py-6 rounded-xl"
              >
                Se connecter
              </Button>
            </Link>
          </div>

          {/* Trust note */}
          <p className="mt-8 text-sm text-gray-500">
            Aucune carte bancaire requise • Configuration en 5 minutes • Support inclus
          </p>
        </div>
      </div>
    </section>
  );
}
