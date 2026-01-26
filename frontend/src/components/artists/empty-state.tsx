"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Music2,
  Sparkles,
  TrendingUp,
  Users,
  ArrowRight,
  Search,
} from "lucide-react";

interface QuickStartExamplesProps {
  onSelect: (example: { name: string; type: string; value: string }) => void;
}

const QUICK_EXAMPLES = [
  {
    name: "PNL",
    type: "NAME",
    value: "PNL",
    genre: "Rap FR",
    description: "Duo phénomène français",
  },
  {
    name: "Damso",
    type: "NAME",
    value: "Damso",
    genre: "Rap Belge",
    description: "Artiste incontournable",
  },
  {
    name: "Aya Nakamura",
    type: "NAME",
    value: "Aya Nakamura",
    genre: "Pop/Afrobeats",
    description: "Artiste francophone #1",
  },
  {
    name: "SDM",
    type: "NAME",
    value: "SDM",
    genre: "Rap FR",
    description: "Étoile montante",
  },
  {
    name: "Tiakola",
    type: "NAME",
    value: "Tiakola",
    genre: "Afro/Rap",
    description: "Phénomène Afro",
  },
  {
    name: "Ninho",
    type: "NAME",
    value: "Ninho",
    genre: "Rap FR",
    description: "Machine à hits",
  },
];

export function QuickStartExamples({ onSelect }: QuickStartExamplesProps) {
  return (
    <div className="w-full max-w-4xl mx-auto">
      <div className="text-center mb-8">
        <div className="inline-flex items-center gap-2 text-sm text-muted-foreground mb-2">
          <Sparkles className="h-4 w-4" />
          <span>Quick Start</span>
        </div>
        <h3 className="text-lg font-medium">Essayez avec ces artistes populaires</h3>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        {QUICK_EXAMPLES.map((example) => (
          <Card
            key={example.name}
            className="group cursor-pointer transition-all hover:shadow-md hover:border-primary/50"
            onClick={() => onSelect(example)}
          >
            <CardContent className="p-4">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="h-10 w-10 rounded-full bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center">
                    <Music2 className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <p className="font-semibold group-hover:text-primary transition-colors">
                      {example.name}
                    </p>
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <Badge variant="secondary" className="text-xs font-normal">
                        {example.genre}
                      </Badge>
                    </div>
                  </div>
                </div>
                <ArrowRight className="h-4 w-4 text-muted-foreground group-hover:text-primary transition-all group-hover:translate-x-1" />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="mt-8 flex flex-col items-center gap-4 text-center">
        <div className="flex items-center gap-6 text-sm text-muted-foreground">
          <div className="flex items-center gap-2">
            <TrendingUp className="h-4 w-4 text-green-500" />
            <span>Tendances de croissance</span>
          </div>
          <div className="flex items-center gap-2">
            <Users className="h-4 w-4 text-blue-500" />
            <span>Données sociales</span>
          </div>
          <div className="flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-amber-500" />
            <span>Score IA</span>
          </div>
        </div>

        <p className="text-sm text-muted-foreground max-w-md">
          Collez une URL Viberate ou Spotify, ou tapez le nom d'un artiste pour lancer une analyse complète.
        </p>
      </div>
    </div>
  );
}

interface EmptyStateProps {
  onQuickStart: (example: { name: string; type: string; value: string }) => void;
}

export function EmptyState({ onQuickStart }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12">
      <div className="relative mb-8">
        <div className="h-24 w-24 rounded-full bg-gradient-to-br from-primary/20 via-primary/10 to-transparent flex items-center justify-center">
          <Search className="h-10 w-10 text-primary/60" />
        </div>
        <div className="absolute -right-2 -bottom-1 h-8 w-8 rounded-full bg-gradient-to-br from-amber-400 to-orange-500 flex items-center justify-center shadow-lg">
          <Sparkles className="h-4 w-4 text-white" />
        </div>
      </div>

      <h2 className="text-2xl font-bold mb-2">Google des Artistes</h2>
      <p className="text-muted-foreground text-center max-w-md mb-8">
        Recherchez n'importe quel artiste par nom ou URL pour obtenir une analyse complète : 
        métriques sociales, tendances, estimation de cachet et recommandations IA.
      </p>

      <QuickStartExamples onSelect={onQuickStart} />
    </div>
  );
}
