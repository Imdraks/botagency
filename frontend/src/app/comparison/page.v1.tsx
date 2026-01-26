"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import {
  GitCompare,
  Plus,
  Trash2,
  Crown,
  Shield,
  TrendingUp,
  DollarSign,
  Star,
  Sparkles,
  ArrowRight,
  Check,
  X,
} from "lucide-react";
import { AppLayout, ProtectedRoute } from "@/components/layout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { api } from "@/lib/api";

// Types
interface ArtistInput {
  id: number;
  artist_name: string;
  spotify_monthly_listeners: string;
  spotify_followers: string;
  youtube_subscribers: string;
  instagram_followers: string;
  tiktok_followers: string;
  genre: string;
  country: string;
}

interface ComparisonResult {
  artists: string[];
  scores: Record<string, number>;
  tiers: Record<string, string>;
  trends: Record<string, string>;
  fees: Record<string, { min: number; max: number; optimal: number }>;
  best_value: string;
  highest_potential: string;
  lowest_risk: string;
}

// Helper functions
const getTierColor = (tier: string) => {
  const colors: Record<string, string> = {
    superstar: "bg-gradient-to-r from-yellow-400 to-orange-500",
    major: "bg-gradient-to-r from-purple-500 to-pink-500",
    established: "bg-gradient-to-r from-blue-500 to-cyan-500",
    rising: "bg-gradient-to-r from-green-400 to-emerald-500",
    emerging: "bg-gradient-to-r from-teal-400 to-cyan-400",
    underground: "bg-gray-500",
  };
  return colors[tier] || "bg-gray-500";
};

const getTrendIcon = (trend: string) => {
  if (["explosive", "rapid", "strong"].includes(trend)) {
    return <TrendingUp className="h-4 w-4 text-green-500" />;
  } else if (["declining", "falling"].includes(trend)) {
    return <TrendingUp className="h-4 w-4 text-red-500 rotate-180" />;
  }
  return <ArrowRight className="h-4 w-4 text-yellow-500" />;
};

const getTrendLabel = (trend: string) => {
  const labels: Record<string, string> = {
    explosive: "🚀 Explosif",
    rapid: "📈 Rapide",
    strong: "💪 Fort",
    moderate: "📊 Modéré",
    stable: "➡️ Stable",
    declining: "📉 Déclin",
    falling: "⬇️ Chute",
  };
  return labels[trend] || trend;
};

const formatCurrency = (num: number) => {
  return num.toLocaleString() + "€";
};

// Components
function ArtistInputCard({
  artist,
  onUpdate,
  onRemove,
  canRemove,
}: {
  artist: ArtistInput;
  onUpdate: (field: keyof ArtistInput, value: string) => void;
  onRemove: () => void;
  canRemove: boolean;
}) {
  return (
    <Card className="relative">
      {canRemove && (
        <Button
          variant="ghost"
          size="icon"
          className="absolute top-2 right-2 text-red-500 hover:text-red-600 hover:bg-red-50"
          onClick={onRemove}
        >
          <Trash2 className="h-4 w-4" />
        </Button>
      )}
      <CardHeader className="pb-4">
        <CardTitle className="text-lg">Artiste {artist.id}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <Label>Nom *</Label>
          <Input
            value={artist.artist_name}
            onChange={(e) => onUpdate("artist_name", e.target.value)}
            placeholder="Ex: Aya Nakamura"
          />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <Label className="text-xs">Genre</Label>
            <Select
              value={artist.genre}
              onValueChange={(v) => onUpdate("genre", v)}
            >
              <SelectTrigger className="h-9">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="pop">Pop</SelectItem>
                <SelectItem value="hip-hop">Hip-Hop</SelectItem>
                <SelectItem value="rap">Rap</SelectItem>
                <SelectItem value="electronic">Electronic</SelectItem>
                <SelectItem value="r&b">R&B</SelectItem>
                <SelectItem value="rock">Rock</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label className="text-xs">Pays</Label>
            <Select
              value={artist.country}
              onValueChange={(v) => onUpdate("country", v)}
            >
              <SelectTrigger className="h-9">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="FR">France</SelectItem>
                <SelectItem value="BE">Belgique</SelectItem>
                <SelectItem value="CH">Suisse</SelectItem>
                <SelectItem value="US">USA</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
        <div>
          <Label className="text-xs">Auditeurs Spotify</Label>
          <Input
            type="number"
            value={artist.spotify_monthly_listeners}
            onChange={(e) => onUpdate("spotify_monthly_listeners", e.target.value)}
            placeholder="500000"
            className="h-9"
          />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <Label className="text-xs">Followers Spotify</Label>
            <Input
              type="number"
              value={artist.spotify_followers}
              onChange={(e) => onUpdate("spotify_followers", e.target.value)}
              placeholder="100000"
              className="h-9"
            />
          </div>
          <div>
            <Label className="text-xs">YouTube</Label>
            <Input
              type="number"
              value={artist.youtube_subscribers}
              onChange={(e) => onUpdate("youtube_subscribers", e.target.value)}
              placeholder="200000"
              className="h-9"
            />
          </div>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <Label className="text-xs">Instagram</Label>
            <Input
              type="number"
              value={artist.instagram_followers}
              onChange={(e) => onUpdate("instagram_followers", e.target.value)}
              placeholder="150000"
              className="h-9"
            />
          </div>
          <div>
            <Label className="text-xs">TikTok</Label>
            <Input
              type="number"
              value={artist.tiktok_followers}
              onChange={(e) => onUpdate("tiktok_followers", e.target.value)}
              placeholder="300000"
              className="h-9"
            />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function ComparisonResultCard({ result }: { result: ComparisonResult }) {
  // Find max score for relative sizing
  const maxScore = Math.max(...Object.values(result.scores));

  return (
    <div className="space-y-6 animate-in fade-in-0 slide-in-from-bottom-4">
      {/* Winner Badges */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 border-green-200 dark:border-green-800">
          <CardContent className="pt-6 text-center">
            <DollarSign className="h-10 w-10 text-green-600 mx-auto mb-2" />
            <p className="text-sm text-green-700 dark:text-green-300">Meilleur rapport qualité/prix</p>
            <p className="text-xl font-bold text-green-800 dark:text-green-200">{result.best_value}</p>
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-purple-50 to-pink-50 dark:from-purple-900/20 dark:to-pink-900/20 border-purple-200 dark:border-purple-800">
          <CardContent className="pt-6 text-center">
            <TrendingUp className="h-10 w-10 text-purple-600 mx-auto mb-2" />
            <p className="text-sm text-purple-700 dark:text-purple-300">Plus fort potentiel</p>
            <p className="text-xl font-bold text-purple-800 dark:text-purple-200">{result.highest_potential}</p>
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-blue-50 to-cyan-50 dark:from-blue-900/20 dark:to-cyan-900/20 border-blue-200 dark:border-blue-800">
          <CardContent className="pt-6 text-center">
            <Shield className="h-10 w-10 text-blue-600 mx-auto mb-2" />
            <p className="text-sm text-blue-700 dark:text-blue-300">Risque le plus faible</p>
            <p className="text-xl font-bold text-blue-800 dark:text-blue-200">{result.lowest_risk}</p>
          </CardContent>
        </Card>
      </div>

      {/* Comparison Table */}
      <Card>
        <CardHeader>
          <CardTitle>Comparaison détaillée</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-3 px-4">Artiste</th>
                  <th className="text-center py-3 px-4">Score</th>
                  <th className="text-center py-3 px-4">Tier</th>
                  <th className="text-center py-3 px-4">Tendance</th>
                  <th className="text-right py-3 px-4">Cachet estimé</th>
                  <th className="text-center py-3 px-4">Badges</th>
                </tr>
              </thead>
              <tbody>
                {result.artists.map((artist) => (
                  <tr key={artist} className="border-b hover:bg-muted/50">
                    <td className="py-4 px-4">
                      <span className="font-medium">{artist}</span>
                    </td>
                    <td className="py-4 px-4">
                      <div className="flex items-center justify-center gap-2">
                        <div className="w-24 h-3 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-gradient-to-r from-purple-500 to-pink-500 rounded-full"
                            style={{ width: `${(result.scores[artist] / maxScore) * 100}%` }}
                          />
                        </div>
                        <span className="font-bold text-sm">{result.scores[artist].toFixed(0)}</span>
                      </div>
                    </td>
                    <td className="py-4 px-4 text-center">
                      <Badge className={`${getTierColor(result.tiers[artist])} text-white`}>
                        {result.tiers[artist].toUpperCase()}
                      </Badge>
                    </td>
                    <td className="py-4 px-4 text-center">
                      <div className="flex items-center justify-center gap-1">
                        {getTrendIcon(result.trends[artist])}
                        <span className="text-sm">{getTrendLabel(result.trends[artist])}</span>
                      </div>
                    </td>
                    <td className="py-4 px-4 text-right">
                      <div className="text-sm">
                        <span className="font-medium">
                          {formatCurrency(result.fees[artist].optimal)}
                        </span>
                        <span className="text-muted-foreground block text-xs">
                          ({formatCurrency(result.fees[artist].min)} - {formatCurrency(result.fees[artist].max)})
                        </span>
                      </div>
                    </td>
                    <td className="py-4 px-4">
                      <div className="flex justify-center gap-1">
                        {artist === result.best_value && (
                          <Badge variant="outline" className="text-green-600 border-green-300">
                            <DollarSign className="h-3 w-3 mr-1" />
                            Value
                          </Badge>
                        )}
                        {artist === result.highest_potential && (
                          <Badge variant="outline" className="text-purple-600 border-purple-300">
                            <Star className="h-3 w-3 mr-1" />
                            Potentiel
                          </Badge>
                        )}
                        {artist === result.lowest_risk && (
                          <Badge variant="outline" className="text-blue-600 border-blue-300">
                            <Shield className="h-3 w-3 mr-1" />
                            Safe
                          </Badge>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Visual Score Comparison */}
      <Card>
        <CardHeader>
          <CardTitle>Scores comparés</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {result.artists
              .sort((a, b) => result.scores[b] - result.scores[a])
              .map((artist, index) => (
                <div key={artist} className="flex items-center gap-4">
                  <div className="w-8 h-8 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 flex items-center justify-center text-white font-bold text-sm">
                    {index + 1}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-medium">{artist}</span>
                      <span className="font-bold">{result.scores[artist].toFixed(0)}/100</span>
                    </div>
                    <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all duration-1000 ${
                          index === 0
                            ? "bg-gradient-to-r from-yellow-400 to-orange-500"
                            : index === 1
                            ? "bg-gradient-to-r from-gray-300 to-gray-400"
                            : "bg-gradient-to-r from-orange-300 to-orange-400"
                        }`}
                        style={{ width: `${result.scores[artist]}%` }}
                      />
                    </div>
                  </div>
                  {index === 0 && <Crown className="h-6 w-6 text-yellow-500" />}
                </div>
              ))}
          </div>
        </CardContent>
      </Card>

      {/* Fee Comparison */}
      <Card>
        <CardHeader>
          <CardTitle>Comparaison des cachets</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {result.artists.map((artist) => (
              <div
                key={artist}
                className={`rounded-lg p-4 ${
                  artist === result.best_value
                    ? "bg-gradient-to-br from-green-100 to-emerald-100 dark:from-green-900/30 dark:to-emerald-900/30 border-2 border-green-300 dark:border-green-700"
                    : "bg-muted"
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="font-medium">{artist}</span>
                  {artist === result.best_value && (
                    <Badge className="bg-green-500 text-white">Best Value</Badge>
                  )}
                </div>
                <div className="text-2xl font-bold">
                  {formatCurrency(result.fees[artist].optimal)}
                </div>
                <div className="text-sm text-muted-foreground">
                  Range: {formatCurrency(result.fees[artist].min)} - {formatCurrency(result.fees[artist].max)}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// Main Component
function ArtistComparisonContent() {
  const [artists, setArtists] = useState<ArtistInput[]>([
    {
      id: 1,
      artist_name: "",
      spotify_monthly_listeners: "",
      spotify_followers: "",
      youtube_subscribers: "",
      instagram_followers: "",
      tiktok_followers: "",
      genre: "pop",
      country: "FR",
    },
    {
      id: 2,
      artist_name: "",
      spotify_monthly_listeners: "",
      spotify_followers: "",
      youtube_subscribers: "",
      instagram_followers: "",
      tiktok_followers: "",
      genre: "pop",
      country: "FR",
    },
  ]);

  const [result, setResult] = useState<ComparisonResult | null>(null);

  const addArtist = () => {
    if (artists.length >= 5) return;
    setArtists([
      ...artists,
      {
        id: Math.max(...artists.map((a) => a.id)) + 1,
        artist_name: "",
        spotify_monthly_listeners: "",
        spotify_followers: "",
        youtube_subscribers: "",
        instagram_followers: "",
        tiktok_followers: "",
        genre: "pop",
        country: "FR",
      },
    ]);
  };

  const removeArtist = (id: number) => {
    setArtists(artists.filter((a) => a.id !== id));
  };

  const updateArtist = (id: number, field: keyof ArtistInput, value: string) => {
    setArtists(artists.map((a) => (a.id === id ? { ...a, [field]: value } : a)));
  };

  const compareMutation = useMutation({
    mutationFn: async () => {
      const artistsData = artists
        .filter((a) => a.artist_name.trim())
        .map((a) => ({
          artist_name: a.artist_name,
          spotify_monthly_listeners: parseInt(a.spotify_monthly_listeners) || 0,
          spotify_followers: parseInt(a.spotify_followers) || 0,
          youtube_subscribers: parseInt(a.youtube_subscribers) || 0,
          instagram_followers: parseInt(a.instagram_followers) || 0,
          tiktok_followers: parseInt(a.tiktok_followers) || 0,
          genre: a.genre,
          country: a.country,
        }));

      const response = await api.post("/ai/compare", { artists: artistsData });
      return response.data;
    },
    onSuccess: (data) => {
      setResult(data);
    },
  });

  const validArtists = artists.filter((a) => a.artist_name.trim()).length;

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="p-3 rounded-xl bg-gradient-to-r from-orange-500 to-red-500">
          <GitCompare className="h-8 w-8 text-white" />
        </div>
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-orange-600 to-red-600 bg-clip-text text-transparent">
            Comparaison Artistes
          </h1>
          <p className="text-muted-foreground">
            Comparez jusqu'à 5 artistes côte à côte pour prendre la meilleure décision
          </p>
        </div>
      </div>

      {/* Artist Inputs */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {artists.map((artist) => (
          <ArtistInputCard
            key={artist.id}
            artist={artist}
            onUpdate={(field, value) => updateArtist(artist.id, field, value)}
            onRemove={() => removeArtist(artist.id)}
            canRemove={artists.length > 2}
          />
        ))}

        {/* Add Artist Button */}
        {artists.length < 5 && (
          <Card className="border-dashed border-2 flex items-center justify-center min-h-[300px] cursor-pointer hover:border-primary transition-colors"
            onClick={addArtist}
          >
            <div className="text-center text-muted-foreground">
              <Plus className="h-10 w-10 mx-auto mb-2" />
              <p>Ajouter un artiste</p>
              <p className="text-xs">(max 5)</p>
            </div>
          </Card>
        )}
      </div>

      {/* Compare Button */}
      <Button
        className="w-full bg-gradient-to-r from-orange-500 to-red-500 hover:from-orange-600 hover:to-red-600"
        size="lg"
        onClick={() => compareMutation.mutate()}
        disabled={validArtists < 2 || compareMutation.isPending}
      >
        {compareMutation.isPending ? (
          <>
            <Sparkles className="mr-2 h-5 w-5 animate-spin" />
            Analyse en cours...
          </>
        ) : (
          <>
            <GitCompare className="mr-2 h-5 w-5" />
            Comparer {validArtists} artistes
          </>
        )}
      </Button>

      {validArtists < 2 && (
        <p className="text-center text-sm text-muted-foreground">
          Remplissez au moins 2 artistes pour lancer la comparaison
        </p>
      )}

      {/* Results */}
      {result && <ComparisonResultCard result={result} />}
    </div>
  );
}

export default function ArtistComparisonPage() {
  return (
    <ProtectedRoute>
      <AppLayout>
        <ArtistComparisonContent />
      </AppLayout>
    </ProtectedRoute>
  );
}
