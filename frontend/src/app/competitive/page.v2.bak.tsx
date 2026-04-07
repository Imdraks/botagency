"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
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
import {
  Eye,
  Plus,
  Trash2,
  Trophy,
  Target,
  Users,
  Loader2,
  MapPin,
  Music,
  Calendar,
  ArrowRight,
} from "lucide-react";
import { competitiveApi, analyticsV2Api } from "@/lib/api";
import { AppLayout, ProtectedRoute } from "@/components/layout";

// ── Types ──

interface Competitor {
  id: number;
  name: string;
  keywords: string[];
  website?: string;
  notes?: string;
  is_active: boolean;
  mentions_count: number;
  created_at: string;
}

interface Winner {
  organization: string;
  wins: number;
  total_value: number;
  categories: string[];
  avg_value: number;
}

interface WinnersData {
  period: string;
  total_won: number;
  unique_winners: number;
  top_winners: Winner[];
  potential_competitors: Winner[];
  insights: string[];
}

interface GapsData {
  underserved_zones: {
    city: string;
    scored_artists: number;
    avg_score: number;
    upcoming_events: number;
  }[];
  underrepresented_genres: {
    genre: string;
    growing_artists: number;
    avg_velocity: number;
    upcoming_events: number;
  }[];
  empty_slots: {
    month: string;
    city: string;
  }[];
}

// ── Main ──

function CompetitiveContent() {
  const queryClient = useQueryClient();
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);
  const [newCompetitor, setNewCompetitor] = useState({ name: "", keywords: "" });

  // ── Queries ──

  const { data: competitors, isLoading: competitorsLoading } = useQuery<Competitor[]>({
    queryKey: ["competitive", "competitors"],
    queryFn: competitiveApi.getCompetitors,
  });

  const { data: winners, isLoading: winnersLoading } = useQuery<WinnersData>({
    queryKey: ["competitive", "winners"],
    queryFn: () => competitiveApi.getWinnersAnalysis("90d"),
  });

  const { data: gaps, isLoading: gapsLoading } = useQuery<GapsData>({
    queryKey: ["analytics-v2", "competitive-gaps"],
    queryFn: () => analyticsV2Api.getCompetitiveGaps(),
    refetchInterval: 120_000,
  });

  // ── Mutations ──

  const addMutation = useMutation({
    mutationFn: competitiveApi.addCompetitor,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["competitive"] });
      setIsAddDialogOpen(false);
      setNewCompetitor({ name: "", keywords: "" });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: competitiveApi.deleteCompetitor,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["competitive"] });
    },
  });

  const handleAddCompetitor = () => {
    if (!newCompetitor.name.trim()) return;
    const keywords = newCompetitor.keywords
      .split(",")
      .map((k) => k.trim())
      .filter((k) => k.length > 0);
    addMutation.mutate({
      name: newCompetitor.name.trim(),
      keywords: keywords.length > 0 ? keywords : [newCompetitor.name.toLowerCase()],
    });
  };

  const formatCurrency = (value: number) =>
    new Intl.NumberFormat("fr-FR", { style: "currency", currency: "EUR", maximumFractionDigits: 0 }).format(value);

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Veille Concurrentielle</h1>
          <p className="text-sm text-muted-foreground">
            Concurrents, dynamiques du marché et espaces à prendre
          </p>
        </div>
      </div>

      {/* Overview KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs text-muted-foreground">Concurrents suivis</span>
              <Eye className="h-4 w-4 text-muted-foreground" />
            </div>
            <p className="text-2xl font-bold">{competitors?.length ?? 0}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs text-muted-foreground">Zones sous-couvertes</span>
              <MapPin className="h-4 w-4 text-muted-foreground" />
            </div>
            <p className="text-2xl font-bold text-amber-600">{gaps?.underserved_zones?.length ?? 0}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs text-muted-foreground">Genres en croissance</span>
              <Music className="h-4 w-4 text-muted-foreground" />
            </div>
            <p className="text-2xl font-bold text-indigo-600">{gaps?.underrepresented_genres?.length ?? 0}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs text-muted-foreground">Créneaux vides</span>
              <Calendar className="h-4 w-4 text-muted-foreground" />
            </div>
            <p className="text-2xl font-bold text-rose-600">{gaps?.empty_slots?.length ?? 0}</p>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="competitors" className="space-y-4">
        <TabsList>
          <TabsTrigger value="competitors">Concurrents surveillés</TabsTrigger>
          <TabsTrigger value="market">Activité du marché</TabsTrigger>
          <TabsTrigger value="gaps">Espaces à prendre</TabsTrigger>
        </TabsList>

        {/* ── Tab 1: Concurrents ── */}
        <TabsContent value="competitors">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2 text-sm">
                    <Users className="h-4 w-4" />
                    Concurrents surveillés
                  </CardTitle>
                  <CardDescription className="text-xs">
                    Suivez les acteurs du marché
                  </CardDescription>
                </div>
                <Dialog open={isAddDialogOpen} onOpenChange={setIsAddDialogOpen}>
                  <DialogTrigger asChild>
                    <Button size="sm">
                      <Plus className="h-4 w-4 mr-1" />
                      Ajouter
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>Ajouter un concurrent</DialogTitle>
                      <DialogDescription>
                        Surveillez ce concurrent dans le marché
                      </DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4 py-4">
                      <div>
                        <label className="text-sm font-medium">Nom</label>
                        <Input
                          placeholder="Ex: Live Nation"
                          value={newCompetitor.name}
                          onChange={(e) => setNewCompetitor({ ...newCompetitor, name: e.target.value })}
                        />
                      </div>
                      <div>
                        <label className="text-sm font-medium">Mots-clés (optionnel)</label>
                        <Input
                          placeholder="Ex: livenation, live-nation"
                          value={newCompetitor.keywords}
                          onChange={(e) => setNewCompetitor({ ...newCompetitor, keywords: e.target.value })}
                        />
                        <p className="text-xs text-muted-foreground mt-1">Séparés par virgule</p>
                      </div>
                    </div>
                    <DialogFooter>
                      <Button variant="outline" onClick={() => setIsAddDialogOpen(false)}>
                        Annuler
                      </Button>
                      <Button onClick={handleAddCompetitor} disabled={addMutation.isPending}>
                        {addMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : "Ajouter"}
                      </Button>
                    </DialogFooter>
                  </DialogContent>
                </Dialog>
              </div>
            </CardHeader>
            <CardContent>
              {competitorsLoading ? (
                <div className="flex items-center justify-center h-32">
                  <Loader2 className="h-8 w-8 animate-spin" />
                </div>
              ) : competitors && competitors.length > 0 ? (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Nom</TableHead>
                      <TableHead>Mots-clés</TableHead>
                      <TableHead>Mentions</TableHead>
                      <TableHead></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {competitors.map((comp) => (
                      <TableRow key={comp.id}>
                        <TableCell className="font-medium">{comp.name}</TableCell>
                        <TableCell>
                          <div className="flex flex-wrap gap-1">
                            {comp.keywords.slice(0, 3).map((kw) => (
                              <Badge key={kw} variant="secondary" className="text-xs">
                                {kw}
                              </Badge>
                            ))}
                            {comp.keywords.length > 3 && (
                              <Badge variant="outline" className="text-xs">+{comp.keywords.length - 3}</Badge>
                            )}
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge variant={comp.mentions_count > 0 ? "default" : "secondary"}>
                            {comp.mentions_count}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => deleteMutation.mutate(comp.id)}
                          >
                            <Trash2 className="h-4 w-4 text-red-500" />
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              ) : (
                <div className="text-center py-8">
                  <Users className="h-10 w-10 mx-auto text-muted-foreground mb-3" />
                  <p className="text-muted-foreground text-sm">Aucun concurrent surveillé</p>
                  <p className="text-xs text-muted-foreground">Ajoutez des concurrents pour commencer</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* ── Tab 2: Activité du marché ── */}
        <TabsContent value="market" className="space-y-6">
          {/* Winners */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm flex items-center gap-2">
                <Trophy className="h-4 w-4" />
                Qui gagne sur le terrain ?
              </CardTitle>
            </CardHeader>
            <CardContent>
              {winnersLoading ? (
                <div className="flex items-center justify-center h-32">
                  <Loader2 className="h-8 w-8 animate-spin" />
                </div>
              ) : winners && winners.top_winners.length > 0 ? (
                <div className="space-y-2">
                  {winners.top_winners.slice(0, 8).map((w, i) => (
                    <motion.div
                      key={w.organization}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.04 }}
                      className="flex items-center justify-between p-3 rounded-lg bg-muted/50 hover:bg-muted transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        <span className="text-lg font-bold text-muted-foreground w-6">#{i + 1}</span>
                        <div>
                          <p className="font-medium text-sm">{w.organization}</p>
                          <div className="flex gap-1 mt-0.5">
                            {w.categories.slice(0, 2).map((c) => (
                              <Badge key={c} variant="outline" className="text-[10px]">{c}</Badge>
                            ))}
                          </div>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-bold">{w.wins} victoires</p>
                        <p className="text-xs text-muted-foreground">{formatCurrency(w.total_value)}</p>
                      </div>
                    </motion.div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground text-center py-6">Pas assez de données</p>
              )}
            </CardContent>
          </Card>

          {/* Potential competitors to watch */}
          {winners && winners.potential_competitors.length > 0 && (
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm flex items-center gap-2">
                  <Target className="h-4 w-4" />
                  Concurrents potentiels à surveiller
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {winners.potential_competitors.map((comp) => (
                    <Badge
                      key={comp.organization}
                      variant="outline"
                      className="cursor-pointer hover:bg-muted text-xs py-1.5"
                      onClick={() => {
                        setNewCompetitor({ name: comp.organization, keywords: "" });
                        setIsAddDialogOpen(true);
                      }}
                    >
                      <Plus className="h-3 w-3 mr-1" />
                      {comp.organization} ({comp.wins})
                    </Badge>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Insights */}
          {winners && winners.insights.length > 0 && (
            <Card className="border-indigo-200 dark:border-indigo-800 bg-indigo-50/50 dark:bg-indigo-950/10">
              <CardContent className="pt-4">
                <div className="space-y-1">
                  {winners.insights.map((insight, i) => (
                    <p key={i} className="text-sm">{insight}</p>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* ── Tab 3: Espaces à prendre ── */}
        <TabsContent value="gaps" className="space-y-6">
          {gapsLoading ? (
            <div className="flex items-center justify-center h-32">
              <Loader2 className="h-8 w-8 animate-spin" />
            </div>
          ) : (
            <>
              {/* Underserved zones */}
              <Card>
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-sm flex items-center gap-2">
                      <MapPin className="h-4 w-4" />
                      Zones sous-couvertes
                    </CardTitle>
                    <Link href="/map" className="text-xs text-indigo-600 hover:underline flex items-center gap-1">
                      Carte <ArrowRight className="h-3 w-3" />
                    </Link>
                  </div>
                  <CardDescription className="text-xs">
                    Villes avec des artistes scorés mais peu d&apos;événements prévus
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {gaps?.underserved_zones && gaps.underserved_zones.length > 0 ? (
                    <div className="space-y-2">
                      {gaps.underserved_zones.map((z) => (
                        <motion.div
                          key={z.city}
                          initial={{ opacity: 0 }}
                          animate={{ opacity: 1 }}
                          className="flex items-center justify-between p-3 rounded-lg bg-amber-50/50 dark:bg-amber-950/10 border border-amber-200/50 dark:border-amber-800/30"
                        >
                          <div className="flex items-center gap-3">
                            <MapPin className="h-4 w-4 text-amber-600" />
                            <div>
                              <p className="text-sm font-medium">{z.city}</p>
                              <p className="text-xs text-muted-foreground">
                                {z.scored_artists} artistes scorés · score moyen {z.avg_score}
                              </p>
                            </div>
                          </div>
                          <div className="text-right">
                            <Badge variant="outline" className="text-amber-700 bg-amber-100 dark:bg-amber-900/30">
                              {z.upcoming_events} événement{z.upcoming_events !== 1 ? "s" : ""}
                            </Badge>
                          </div>
                        </motion.div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground text-center py-6">
                      Toutes les zones actives sont bien couvertes
                    </p>
                  )}
                </CardContent>
              </Card>

              {/* Underrepresented genres */}
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <Music className="h-4 w-4" />
                    Genres sous-représentés
                  </CardTitle>
                  <CardDescription className="text-xs">
                    Genres avec des artistes en croissance mais peu d&apos;événements
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {gaps?.underrepresented_genres && gaps.underrepresented_genres.length > 0 ? (
                    <div className="space-y-2">
                      {gaps.underrepresented_genres.map((g) => (
                        <motion.div
                          key={g.genre}
                          initial={{ opacity: 0 }}
                          animate={{ opacity: 1 }}
                          className="flex items-center justify-between p-3 rounded-lg bg-indigo-50/50 dark:bg-indigo-950/10 border border-indigo-200/50 dark:border-indigo-800/30"
                        >
                          <div className="flex items-center gap-3">
                            <Music className="h-4 w-4 text-indigo-600" />
                            <div>
                              <p className="text-sm font-medium capitalize">{g.genre}</p>
                              <p className="text-xs text-muted-foreground">
                                {g.growing_artists} artistes en croissance · vélocité +{g.avg_velocity}%
                              </p>
                            </div>
                          </div>
                          <div className="text-right">
                            <Badge variant="outline" className="text-indigo-700 bg-indigo-100 dark:bg-indigo-900/30">
                              {g.upcoming_events} événement{g.upcoming_events !== 1 ? "s" : ""}
                            </Badge>
                          </div>
                        </motion.div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground text-center py-6">
                      Tous les genres en croissance sont bien couverts
                    </p>
                  )}
                </CardContent>
              </Card>

              {/* Empty slots */}
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <Calendar className="h-4 w-4" />
                    Créneaux vides
                  </CardTitle>
                  <CardDescription className="text-xs">
                    Mois sans événements dans des villes actives
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {gaps?.empty_slots && gaps.empty_slots.length > 0 ? (
                    <div className="flex flex-wrap gap-2">
                      {gaps.empty_slots.map((s, i) => (
                        <Badge
                          key={`${s.month}-${s.city}-${i}`}
                          variant="outline"
                          className="text-xs py-1.5 bg-rose-50 dark:bg-rose-950/10 border-rose-200 dark:border-rose-800/30 text-rose-700 dark:text-rose-400"
                        >
                          <Calendar className="h-3 w-3 mr-1" />
                          {s.month} · {s.city}
                        </Badge>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground text-center py-6">
                      Pas de créneau vide détecté
                    </p>
                  )}
                </CardContent>
              </Card>
            </>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}

export default function CompetitivePage() {
  return (
    <ProtectedRoute>
      <AppLayout>
        <CompetitiveContent />
      </AppLayout>
    </ProtectedRoute>
  );
}
