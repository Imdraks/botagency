"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import {
  Search,
  Rocket,
  TrendingUp,
  Zap,
  AlertCircle,
  Star,
  Clock,
  DollarSign,
  Target,
  Sparkles,
  ChevronRight,
  Eye,
  Activity,
  Music,
  BarChart2,
} from "lucide-react";
import { AppLayout, ProtectedRoute } from "@/components/layout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { api } from "@/lib/api";

// Types
interface DiscoveryPattern {
  pattern_type: string;
  confidence: number;
  description: string;
  impact_score: number;
}

interface EmergingArtist {
  name: string;
  spotify_id: string | null;
  genres: string[];
  monthly_listeners: number;
  spotify_followers: number;
  total_social_followers: number;
  growth_velocity: number;
  acceleration: number;
  signals: string[];
  patterns: DiscoveryPattern[];
  potential_level: string;
  potential_score: number;
  breakout_probability: number;
  discovered_at: string;
  estimated_breakout: string | null;
  why_watch: string[];
  booking_advice: string;
  estimated_current_fee: number;
  estimated_future_fee: number;
}

// Helper functions
const getPotentialColor = (level: string) => {
  const colors: Record<string, string> = {
    explosive: "bg-gradient-to-r from-red-500 to-orange-500 text-white",
    high: "bg-gradient-to-r from-purple-500 to-pink-500 text-white",
    promising: "bg-gradient-to-r from-blue-500 to-cyan-500 text-white",
    moderate: "bg-gradient-to-r from-yellow-500 to-orange-400 text-white",
    low: "bg-gray-500 text-white",
  };
  return colors[level] || "bg-gray-500 text-white";
};

const getPotentialLabel = (level: string) => {
  const labels: Record<string, string> = {
    explosive: "🚀 Explosif",
    high: "⭐ Élevé",
    promising: "💫 Prometteur",
    moderate: "📊 Modéré",
    low: "📉 Faible",
  };
  return labels[level] || level;
};

const getSignalIcon = (signal: string) => {
  const icons: Record<string, React.ReactNode> = {
    viral_growth: <TrendingUp className="h-4 w-4" />,
    playlist_boost: <Music className="h-4 w-4" />,
    media_buzz: <Zap className="h-4 w-4" />,
    social_surge: <Activity className="h-4 w-4" />,
    collab_boost: <Star className="h-4 w-4" />,
    award_nomination: <Star className="h-4 w-4" />,
    label_signing: <Target className="h-4 w-4" />,
  };
  return icons[signal] || <Sparkles className="h-4 w-4" />;
};

const getSignalLabel = (signal: string) => {
  const labels: Record<string, string> = {
    viral_growth: "Croissance virale",
    playlist_boost: "Boost playlist",
    media_buzz: "Buzz médiatique",
    social_surge: "Surge social",
    collab_boost: "Collaboration",
    award_nomination: "Nomination",
    label_signing: "Signature label",
  };
  return labels[signal] || signal;
};

const formatNumber = (num: number) => {
  if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
  if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
  return num.toString();
};

// Components
function PotentialMeter({ score }: { score: number }) {
  const getColor = () => {
    if (score >= 80) return "from-red-500 to-orange-500";
    if (score >= 60) return "from-purple-500 to-pink-500";
    if (score >= 40) return "from-blue-500 to-cyan-500";
    return "from-gray-400 to-gray-500";
  };

  return (
    <div className="relative w-full h-8 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
      <div
        className={`h-full bg-gradient-to-r ${getColor()} transition-all duration-1000 ease-out rounded-full`}
        style={{ width: `${score}%` }}
      />
      <div className="absolute inset-0 flex items-center justify-center">
        <span className="text-sm font-bold text-white drop-shadow-lg">
          {score.toFixed(0)}% Potentiel
        </span>
      </div>
    </div>
  );
}

function BreakoutProbability({ probability }: { probability: number }) {
  const percentage = probability * 100;
  
  return (
    <div className="relative">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium">Probabilité de breakout</span>
        <span className="text-sm font-bold">{percentage.toFixed(0)}%</span>
      </div>
      <div className="w-full h-3 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-1000 ${
            percentage >= 70
              ? "bg-green-500"
              : percentage >= 50
              ? "bg-yellow-500"
              : percentage >= 30
              ? "bg-orange-500"
              : "bg-red-500"
          }`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}

function SignalBadge({ signal }: { signal: string }) {
  const signalColors: Record<string, string> = {
    viral_growth: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200",
    playlist_boost: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200",
    media_buzz: "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200",
    social_surge: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200",
    collab_boost: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200",
    award_nomination: "bg-pink-100 text-pink-800 dark:bg-pink-900 dark:text-pink-200",
    label_signing: "bg-cyan-100 text-cyan-800 dark:bg-cyan-900 dark:text-cyan-200",
  };

  return (
    <Badge className={`flex items-center gap-1 ${signalColors[signal] || ""}`}>
      {getSignalIcon(signal)}
      {getSignalLabel(signal)}
    </Badge>
  );
}

function PatternCard({ pattern }: { pattern: DiscoveryPattern }) {
  return (
    <div className="bg-gradient-to-br from-purple-50 to-pink-50 dark:from-purple-900/20 dark:to-pink-900/20 rounded-lg p-4 border border-purple-200 dark:border-purple-800">
      <div className="flex items-center justify-between mb-2">
        <span className="font-medium capitalize">{pattern.pattern_type.replace("_", " ")}</span>
        <Badge variant="outline">{(pattern.confidence * 100).toFixed(0)}% confiance</Badge>
      </div>
      <p className="text-sm text-muted-foreground">{pattern.description}</p>
      <div className="mt-2">
        <span className="text-xs text-muted-foreground">Impact:</span>
        <Progress value={pattern.impact_score * 100} className="h-2 mt-1" />
      </div>
    </div>
  );
}

function FeeComparison({ current, future }: { current: number; future: number }) {
  const increase = ((future - current) / current) * 100;

  return (
    <div className="grid grid-cols-2 gap-4">
      <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 border border-blue-200 dark:border-blue-800">
        <div className="flex items-center gap-2 text-blue-600 dark:text-blue-400 mb-1">
          <DollarSign className="h-4 w-4" />
          <span className="text-sm">Cachet actuel</span>
        </div>
        <p className="text-2xl font-bold">{current.toLocaleString()}€</p>
      </div>
      <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4 border border-green-200 dark:border-green-800">
        <div className="flex items-center gap-2 text-green-600 dark:text-green-400 mb-1">
          <TrendingUp className="h-4 w-4" />
          <span className="text-sm">Cachet futur (6-12 mois)</span>
        </div>
        <p className="text-2xl font-bold">{future.toLocaleString()}€</p>
        <p className="text-sm text-green-600 dark:text-green-400">
          +{increase.toFixed(0)}% estimé
        </p>
      </div>
    </div>
  );
}

// Main Component
function ArtistDiscoveryContent() {
  const [artistName, setArtistName] = useState("");
  const [monthlyListeners, setMonthlyListeners] = useState("");
  const [spotifyFollowers, setSpotifyFollowers] = useState("");
  const [socialFollowers, setSocialFollowers] = useState("");
  const [genres, setGenres] = useState("");
  const [historicalListeners, setHistoricalListeners] = useState("");

  const [result, setResult] = useState<EmergingArtist | null>(null);

  const discoverMutation = useMutation({
    mutationFn: async () => {
      // Parse historical listeners (comma-separated)
      const historical = historicalListeners
        .split(",")
        .map((s) => parseInt(s.trim()))
        .filter((n) => !isNaN(n));

      const response = await api.post("/ai/discover", {
        artist_name: artistName,
        monthly_listeners: parseInt(monthlyListeners) || 0,
        spotify_followers: parseInt(spotifyFollowers) || 0,
        social_followers: parseInt(socialFollowers) || 0,
        genres: genres.split(",").map((g) => g.trim()).filter(Boolean),
        historical_listeners: historical.length > 0 ? historical : null,
      });
      return response.data;
    },
    onSuccess: (data) => {
      setResult(data);
    },
  });

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="p-3 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-500">
          <Search className="h-8 w-8 text-white" />
        </div>
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-cyan-600 to-blue-600 bg-clip-text text-transparent">
            Découverte Artistes
          </h1>
          <p className="text-muted-foreground">
            Détectez les artistes émergents à fort potentiel avant qu'ils n'explosent
          </p>
        </div>
      </div>

      {/* Info Banner */}
      <div className="bg-gradient-to-r from-cyan-50 to-blue-50 dark:from-cyan-900/20 dark:to-blue-900/20 border border-cyan-200 dark:border-cyan-800 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <Eye className="h-5 w-5 text-cyan-600 mt-0.5" />
          <div>
            <h3 className="font-medium text-cyan-900 dark:text-cyan-100">
              Détection de potentiel IA
            </h3>
            <p className="text-sm text-cyan-700 dark:text-cyan-300">
              Notre algorithme analyse la vélocité de croissance, les patterns de développement,
              et détecte les signaux précurseurs d'un breakout imminent. Bookez avant que les prix n'explosent !
            </p>
          </div>
        </div>
      </div>

      {/* Input Form */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5" />
            Analyser le potentiel
          </CardTitle>
          <CardDescription>
            Entrez les métriques de l'artiste pour évaluer son potentiel d'émergence
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div className="lg:col-span-2">
              <Label htmlFor="artist_name">Nom de l'artiste *</Label>
              <Input
                id="artist_name"
                value={artistName}
                onChange={(e) => setArtistName(e.target.value)}
                placeholder="Ex: Tiakola"
              />
            </div>
            <div>
              <Label htmlFor="genres">Genres (séparés par ,)</Label>
              <Input
                id="genres"
                value={genres}
                onChange={(e) => setGenres(e.target.value)}
                placeholder="Ex: hip-hop, afro"
              />
            </div>
            <div>
              <Label htmlFor="monthly_listeners">Auditeurs mensuels Spotify</Label>
              <Input
                id="monthly_listeners"
                type="number"
                value={monthlyListeners}
                onChange={(e) => setMonthlyListeners(e.target.value)}
                placeholder="Ex: 50000"
              />
            </div>
            <div>
              <Label htmlFor="spotify_followers">Followers Spotify</Label>
              <Input
                id="spotify_followers"
                type="number"
                value={spotifyFollowers}
                onChange={(e) => setSpotifyFollowers(e.target.value)}
                placeholder="Ex: 20000"
              />
            </div>
            <div>
              <Label htmlFor="social_followers">Followers réseaux sociaux (total)</Label>
              <Input
                id="social_followers"
                type="number"
                value={socialFollowers}
                onChange={(e) => setSocialFollowers(e.target.value)}
                placeholder="Ex: 100000"
              />
            </div>
            <div className="lg:col-span-3">
              <Label htmlFor="historical">
                Historique auditeurs (6 derniers mois, séparés par ,)
              </Label>
              <Input
                id="historical"
                value={historicalListeners}
                onChange={(e) => setHistoricalListeners(e.target.value)}
                placeholder="Ex: 10000, 15000, 25000, 40000, 55000, 80000"
              />
              <p className="text-xs text-muted-foreground mt-1">
                Optionnel mais améliore significativement la précision de l'analyse
              </p>
            </div>
          </div>

          <Button
            className="mt-6 w-full bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-600 hover:to-blue-600"
            onClick={() => discoverMutation.mutate()}
            disabled={!artistName || discoverMutation.isPending}
          >
            {discoverMutation.isPending ? (
              <>
                <Sparkles className="mr-2 h-4 w-4 animate-spin" />
                Analyse en cours...
              </>
            ) : (
              <>
                <Search className="mr-2 h-4 w-4" />
                Détecter le potentiel
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      {/* Results */}
      {result && (
        <div className="space-y-6 animate-in fade-in-0 slide-in-from-bottom-4">
          {/* Main Result Card */}
          <Card className="overflow-hidden">
            <div className={`h-2 ${getPotentialColor(result.potential_level)}`} />
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-2xl">{result.name}</CardTitle>
                  <CardDescription className="flex items-center gap-2 mt-1">
                    {result.genres.map((g) => (
                      <Badge key={g} variant="outline">
                        {g}
                      </Badge>
                    ))}
                  </CardDescription>
                </div>
                <Badge className={`text-lg py-2 px-4 ${getPotentialColor(result.potential_level)}`}>
                  {getPotentialLabel(result.potential_level)}
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Potential Score */}
              <PotentialMeter score={result.potential_score} />

              {/* Key Metrics */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-muted rounded-lg p-4 text-center">
                  <p className="text-sm text-muted-foreground">Auditeurs</p>
                  <p className="text-xl font-bold">{formatNumber(result.monthly_listeners)}</p>
                </div>
                <div className="bg-muted rounded-lg p-4 text-center">
                  <p className="text-sm text-muted-foreground">Croissance/mois</p>
                  <p className="text-xl font-bold text-green-600">
                    +{(result.growth_velocity * 100).toFixed(1)}%
                  </p>
                </div>
                <div className="bg-muted rounded-lg p-4 text-center">
                  <p className="text-sm text-muted-foreground">Accélération</p>
                  <p className={`text-xl font-bold ${result.acceleration > 0 ? "text-green-600" : "text-red-600"}`}>
                    {result.acceleration > 0 ? "+" : ""}
                    {(result.acceleration * 100).toFixed(1)}%
                  </p>
                </div>
                <div className="bg-muted rounded-lg p-4 text-center">
                  <p className="text-sm text-muted-foreground">Breakout estimé</p>
                  <p className="text-xl font-bold">{result.estimated_breakout || "N/A"}</p>
                </div>
              </div>

              {/* Breakout Probability */}
              <BreakoutProbability probability={result.breakout_probability} />

              {/* Signals */}
              {result.signals.length > 0 && (
                <div>
                  <h4 className="font-medium mb-3 flex items-center gap-2">
                    <Zap className="h-4 w-4 text-yellow-500" />
                    Signaux détectés
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {result.signals.map((signal) => (
                      <SignalBadge key={signal} signal={signal} />
                    ))}
                  </div>
                </div>
              )}

              {/* Patterns */}
              {result.patterns.length > 0 && (
                <div>
                  <h4 className="font-medium mb-3 flex items-center gap-2">
                    <BarChart2 className="h-4 w-4 text-purple-500" />
                    Patterns de croissance
                  </h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {result.patterns.map((pattern, i) => (
                      <PatternCard key={i} pattern={pattern} />
                    ))}
                  </div>
                </div>
              )}

              {/* Why Watch */}
              <div>
                <h4 className="font-medium mb-3 flex items-center gap-2">
                  <Eye className="h-4 w-4 text-blue-500" />
                  Pourquoi surveiller cet artiste
                </h4>
                <ul className="space-y-2">
                  {result.why_watch.map((reason, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm bg-muted rounded-lg p-3">
                      <ChevronRight className="h-4 w-4 text-blue-500 mt-0.5" />
                      {reason}
                    </li>
                  ))}
                </ul>
              </div>

              {/* Fee Comparison */}
              <div>
                <h4 className="font-medium mb-3 flex items-center gap-2">
                  <DollarSign className="h-4 w-4 text-green-500" />
                  Évolution du cachet estimé
                </h4>
                <FeeComparison
                  current={result.estimated_current_fee}
                  future={result.estimated_future_fee}
                />
              </div>

              {/* Booking Advice */}
              <div className="bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
                <div className="flex items-start gap-3">
                  <Target className="h-5 w-5 text-green-600 mt-0.5" />
                  <div>
                    <h4 className="font-medium text-green-900 dark:text-green-100">
                      Conseil booking
                    </h4>
                    <p className="text-sm text-green-700 dark:text-green-300 mt-1">
                      {result.booking_advice}
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}

export default function ArtistDiscoveryPage() {
  return (
    <ProtectedRoute>
      <AppLayout>
        <ArtistDiscoveryContent />
      </AppLayout>
    </ProtectedRoute>
  );
}
