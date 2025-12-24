"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { api } from "@/lib/api";
import {
  Users,
  TrendingUp,
  TrendingDown,
  Minus,
  Search,
  Star,
  History,
  BarChart2,
  Music,
  Instagram,
  Globe,
  ExternalLink,
} from "lucide-react";

interface ArtistData {
  name: string;
  genres: string[];
  popularity: number;
  followers: number;
  monthlyListeners?: number;
  socialMedia?: {
    instagram?: { followers: number; engagement: number };
    twitter?: { followers: number };
    tiktok?: { followers: number };
  };
  marketValue?: {
    min: number;
    max: number;
    average: number;
  };
  trend: "up" | "down" | "stable";
  events: number;
  lastAnalysis: string;
}

interface ArtistHistory {
  id: string;
  artistName: string;
  analysisDate: string;
  popularity: number;
  followers: number;
  estimatedCacheMin: number;
  estimatedCacheMax: number;
}

// Mock data - in production, this would come from the API
const mockHistory: ArtistHistory[] = [
  {
    id: "1",
    artistName: "PNL",
    analysisDate: new Date(Date.now() - 86400000 * 7).toISOString(),
    popularity: 85,
    followers: 5200000,
    estimatedCacheMin: 80000,
    estimatedCacheMax: 150000,
  },
  {
    id: "2",
    artistName: "Jul",
    analysisDate: new Date(Date.now() - 86400000 * 3).toISOString(),
    popularity: 78,
    followers: 3800000,
    estimatedCacheMin: 50000,
    estimatedCacheMax: 90000,
  },
  {
    id: "3",
    artistName: "Ninho",
    analysisDate: new Date(Date.now() - 86400000 * 1).toISOString(),
    popularity: 82,
    followers: 4100000,
    estimatedCacheMin: 60000,
    estimatedCacheMax: 100000,
  },
];

function formatNumber(num: number): string {
  if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
  if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
  return num.toString();
}

function ArtistCard({ artist }: { artist: ArtistData }) {
  const TrendIcon = artist.trend === "up" ? TrendingUp : artist.trend === "down" ? TrendingDown : Minus;
  const trendColor = artist.trend === "up" ? "text-green-500" : artist.trend === "down" ? "text-red-500" : "text-gray-500";

  return (
    <Card>
      <CardContent className="pt-6">
        <div className="flex justify-between items-start mb-4">
          <div>
            <h3 className="font-semibold text-lg">{artist.name}</h3>
            <div className="flex gap-1 mt-1">
              {artist.genres.slice(0, 3).map((genre) => (
                <Badge key={genre} variant="secondary" className="text-xs">
                  {genre}
                </Badge>
              ))}
            </div>
          </div>
          <div className={`flex items-center gap-1 ${trendColor}`}>
            <TrendIcon className="h-4 w-4" />
            <span className="text-sm font-medium">
              {artist.trend === "up" ? "+12%" : artist.trend === "down" ? "-5%" : "stable"}
            </span>
          </div>
        </div>

        <div className="space-y-3">
          <div>
            <div className="flex justify-between text-sm mb-1">
              <span>Popularité</span>
              <span className="font-medium">{artist.popularity}/100</span>
            </div>
            <Progress value={artist.popularity} className="h-2" />
          </div>

          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-muted-foreground">Followers</p>
              <p className="font-semibold">{formatNumber(artist.followers)}</p>
            </div>
            <div>
              <p className="text-muted-foreground">Évènements</p>
              <p className="font-semibold">{artist.events}</p>
            </div>
          </div>

          {artist.marketValue && (
            <div className="pt-2 border-t">
              <p className="text-sm text-muted-foreground mb-1">Cachet estimé</p>
              <p className="font-semibold text-primary">
                {formatNumber(artist.marketValue.min)}€ - {formatNumber(artist.marketValue.max)}€
              </p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

function ArtistComparison({ artists }: { artists: ArtistData[] }) {
  if (artists.length < 2) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        <BarChart2 className="h-12 w-12 mx-auto mb-4 opacity-20" />
        <p>Sélectionnez au moins 2 artistes pour comparer</p>
      </div>
    );
  }

  const metrics = [
    { key: "popularity", label: "Popularité", format: (v: number) => `${v}/100` },
    { key: "followers", label: "Followers", format: formatNumber },
    { key: "events", label: "Évènements", format: (v: number) => v.toString() },
    {
      key: "marketValue",
      label: "Cachet moyen",
      format: (v: any) => (v ? `${formatNumber(v.average)}€` : "N/A"),
    },
  ];

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Métrique</TableHead>
          {artists.map((a) => (
            <TableHead key={a.name} className="text-center">
              {a.name}
            </TableHead>
          ))}
        </TableRow>
      </TableHeader>
      <TableBody>
        {metrics.map((metric) => {
          const values = artists.map((a) => (a as any)[metric.key]);
          const maxIdx = values.reduce((iMax, x, i, arr) => {
            if (metric.key === "marketValue") {
              return (x?.average ?? 0) > (arr[iMax]?.average ?? 0) ? i : iMax;
            }
            return x > arr[iMax] ? i : iMax;
          }, 0);

          return (
            <TableRow key={metric.key}>
              <TableCell className="font-medium">{metric.label}</TableCell>
              {artists.map((a, idx) => (
                <TableCell
                  key={a.name}
                  className={`text-center ${idx === maxIdx ? "font-bold text-primary" : ""}`}
                >
                  {metric.format((a as any)[metric.key])}
                  {idx === maxIdx && <Star className="h-3 w-3 inline ml-1 text-yellow-500" />}
                </TableCell>
              ))}
            </TableRow>
          );
        })}
      </TableBody>
    </Table>
  );
}

export function ArtistHistory() {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedArtists, setSelectedArtists] = useState<string[]>([]);
  const [history, setHistory] = useState<ArtistHistory[]>(mockHistory);
  const [analyzingArtist, setAnalyzingArtist] = useState<string | null>(null);

  // Mock artist data - would come from API
  const [artistsData, setArtistsData] = useState<Map<string, ArtistData>>(
    new Map([
      [
        "PNL",
        {
          name: "PNL",
          genres: ["Rap FR", "Cloud Rap"],
          popularity: 85,
          followers: 5200000,
          events: 12,
          trend: "up" as const,
          marketValue: { min: 80000, max: 150000, average: 115000 },
          lastAnalysis: new Date().toISOString(),
        },
      ],
      [
        "Jul",
        {
          name: "Jul",
          genres: ["Rap FR", "Pop Urbaine"],
          popularity: 78,
          followers: 3800000,
          events: 45,
          trend: "stable" as const,
          marketValue: { min: 50000, max: 90000, average: 70000 },
          lastAnalysis: new Date().toISOString(),
        },
      ],
      [
        "Ninho",
        {
          name: "Ninho",
          genres: ["Rap FR", "Trap"],
          popularity: 82,
          followers: 4100000,
          events: 28,
          trend: "up" as const,
          marketValue: { min: 60000, max: 100000, average: 80000 },
          lastAnalysis: new Date().toISOString(),
        },
      ],
    ])
  );

  const handleAnalyzeArtist = async () => {
    if (!searchQuery.trim()) return;

    setAnalyzingArtist(searchQuery);

    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 2000));

    const newArtist: ArtistData = {
      name: searchQuery,
      genres: ["Musique"],
      popularity: Math.floor(Math.random() * 40) + 60,
      followers: Math.floor(Math.random() * 2000000) + 100000,
      events: Math.floor(Math.random() * 30),
      trend: ["up", "down", "stable"][Math.floor(Math.random() * 3)] as any,
      marketValue: {
        min: Math.floor(Math.random() * 30000) + 10000,
        max: Math.floor(Math.random() * 50000) + 50000,
        average: Math.floor(Math.random() * 30000) + 35000,
      },
      lastAnalysis: new Date().toISOString(),
    };

    setArtistsData((prev) => new Map(prev).set(searchQuery, newArtist));
    setHistory((prev) => [
      {
        id: crypto.randomUUID(),
        artistName: searchQuery,
        analysisDate: new Date().toISOString(),
        popularity: newArtist.popularity,
        followers: newArtist.followers,
        estimatedCacheMin: newArtist.marketValue!.min,
        estimatedCacheMax: newArtist.marketValue!.max,
      },
      ...prev,
    ]);
    setAnalyzingArtist(null);
    setSearchQuery("");
  };

  const toggleArtistSelection = (name: string) => {
    setSelectedArtists((prev) =>
      prev.includes(name) ? prev.filter((n) => n !== name) : [...prev, name].slice(-4)
    );
  };

  const selectedArtistsData = selectedArtists
    .map((name) => artistsData.get(name))
    .filter(Boolean) as ArtistData[];

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            Analyse & Historique des Artistes
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2 mb-6">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Rechercher un artiste..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleAnalyzeArtist()}
                className="pl-10"
              />
            </div>
            <Button
              onClick={handleAnalyzeArtist}
              disabled={!searchQuery.trim() || !!analyzingArtist}
            >
              {analyzingArtist ? (
                <>
                  <Music className="h-4 w-4 mr-2 animate-pulse" />
                  Analyse en cours...
                </>
              ) : (
                <>
                  <BarChart2 className="h-4 w-4 mr-2" />
                  Analyser
                </>
              )}
            </Button>
          </div>

          <Tabs defaultValue="cards">
            <TabsList>
              <TabsTrigger value="cards">
                <Users className="h-4 w-4 mr-2" />
                Artistes
              </TabsTrigger>
              <TabsTrigger value="compare">
                <BarChart2 className="h-4 w-4 mr-2" />
                Comparateur
              </TabsTrigger>
              <TabsTrigger value="history">
                <History className="h-4 w-4 mr-2" />
                Historique
              </TabsTrigger>
            </TabsList>

            <TabsContent value="cards" className="mt-4">
              {artistsData.size === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <Music className="h-12 w-12 mx-auto mb-4 opacity-20" />
                  <p>Aucun artiste analysé</p>
                  <p className="text-sm mt-1">Recherchez un artiste pour commencer</p>
                </div>
              ) : (
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                  {Array.from(artistsData.values()).map((artist) => (
                    <div
                      key={artist.name}
                      className={`cursor-pointer transition-all ${
                        selectedArtists.includes(artist.name)
                          ? "ring-2 ring-primary rounded-lg"
                          : ""
                      }`}
                      onClick={() => toggleArtistSelection(artist.name)}
                    >
                      <ArtistCard artist={artist} />
                    </div>
                  ))}
                </div>
              )}
              {selectedArtists.length > 0 && (
                <p className="text-sm text-muted-foreground mt-4 text-center">
                  {selectedArtists.length} artiste(s) sélectionné(s) pour comparaison
                </p>
              )}
            </TabsContent>

            <TabsContent value="compare" className="mt-4">
              <ArtistComparison artists={selectedArtistsData} />
            </TabsContent>

            <TabsContent value="history" className="mt-4">
              {history.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <History className="h-12 w-12 mx-auto mb-4 opacity-20" />
                  <p>Aucun historique</p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Artiste</TableHead>
                      <TableHead>Date</TableHead>
                      <TableHead>Popularité</TableHead>
                      <TableHead>Followers</TableHead>
                      <TableHead>Cachet estimé</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {history.map((h) => (
                      <TableRow key={h.id}>
                        <TableCell className="font-medium">{h.artistName}</TableCell>
                        <TableCell>
                          {new Date(h.analysisDate).toLocaleDateString("fr-FR")}
                        </TableCell>
                        <TableCell>{h.popularity}/100</TableCell>
                        <TableCell>{formatNumber(h.followers)}</TableCell>
                        <TableCell>
                          {formatNumber(h.estimatedCacheMin)}€ - {formatNumber(h.estimatedCacheMax)}€
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
}
