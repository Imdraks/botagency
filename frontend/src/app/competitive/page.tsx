"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
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
  Bell,
  Trophy,
  DollarSign,
  PieChart,
  Target,
  AlertTriangle,
  Users,
  TrendingUp,
  Loader2,
  Search,
} from "lucide-react";
import { competitiveApi } from "@/lib/api";

// Types
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

interface Mention {
  competitor_id: number;
  competitor_name: string;
  keyword_matched: string;
  opportunity: {
    id: number;
    title: string;
    organization: string;
    status: string | null;
    budget: number | null;
    created_at: string;
  };
}

interface MentionsData {
  period: string;
  mentions: Mention[];
  by_competitor: Array<{
    name: string;
    count: number;
    recent: Mention[];
  }>;
  total: number;
  message?: string;
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

interface PricingData {
  global: {
    count: number;
    min: number;
    max: number;
    avg: number;
    median: number;
  };
  by_category: Array<{
    category: string;
    count: number;
    min: number;
    max: number;
    avg: number;
    median: number;
    p25: number;
    p75: number;
  }>;
  insights: string[];
}

interface Alert {
  type: string;
  priority: string;
  competitor?: string;
  message: string;
  opportunity_id?: number;
  opportunity_title?: string;
  created_at: string;
}

interface AlertsData {
  alerts: Alert[];
  total: number;
  last_check: string;
  message?: string;
}

interface MarketShareData {
  period: string;
  overall: {
    count_share: number;
    value_share: number;
    won_count: number;
    total_count: number;
    won_value: number;
    total_value: number;
  };
  by_category: Array<{
    category: string;
    count_share: number;
    value_share: number;
    won: number;
    total: number;
  }>;
  insights: string[];
}

export default function CompetitivePage() {
  const queryClient = useQueryClient();
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);
  const [newCompetitor, setNewCompetitor] = useState({ name: "", keywords: "" });
  const [mentionsPeriod, setMentionsPeriod] = useState<"7d" | "30d" | "90d">("30d");

  // Queries
  const { data: competitors, isLoading: competitorsLoading } = useQuery<Competitor[]>({
    queryKey: ["competitive", "competitors"],
    queryFn: competitiveApi.getCompetitors,
  });

  const { data: mentions, isLoading: mentionsLoading } = useQuery<MentionsData>({
    queryKey: ["competitive", "mentions", mentionsPeriod],
    queryFn: () => competitiveApi.getMentions(mentionsPeriod),
  });

  const { data: winners, isLoading: winnersLoading } = useQuery<WinnersData>({
    queryKey: ["competitive", "winners"],
    queryFn: () => competitiveApi.getWinnersAnalysis("90d"),
  });

  const { data: pricing, isLoading: pricingLoading } = useQuery<PricingData>({
    queryKey: ["competitive", "pricing"],
    queryFn: () => competitiveApi.getPricingBenchmark(),
  });

  const { data: alerts, isLoading: alertsLoading } = useQuery<AlertsData>({
    queryKey: ["competitive", "alerts"],
    queryFn: competitiveApi.getAlerts,
    refetchInterval: 60000,
  });

  const { data: marketShare, isLoading: marketShareLoading } = useQuery<MarketShareData>({
    queryKey: ["competitive", "market-share"],
    queryFn: () => competitiveApi.getMarketShare("90d"),
  });

  // Mutations
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

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat("fr-FR", {
      style: "currency",
      currency: "EUR",
      maximumFractionDigits: 0,
    }).format(value);
  };

  const handleAddCompetitor = () => {
    if (!newCompetitor.name.trim()) return;
    
    const keywords = newCompetitor.keywords
      .split(",")
      .map(k => k.trim())
      .filter(k => k.length > 0);
    
    addMutation.mutate({
      name: newCompetitor.name.trim(),
      keywords: keywords.length > 0 ? keywords : [newCompetitor.name.toLowerCase()],
    });
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">🎯 Veille Compétitive</h1>
          <p className="text-muted-foreground">
            Surveillez vos concurrents et analysez le marché
          </p>
        </div>
        {alerts && alerts.total > 0 && (
          <Badge variant="destructive" className="animate-pulse">
            {alerts.total} alerte{alerts.total > 1 ? "s" : ""}
          </Badge>
        )}
      </div>

      {/* Alerts Banner */}
      {alerts && alerts.alerts.length > 0 && (
        <Card className="border-orange-500 bg-orange-50 dark:bg-orange-950/20">
          <CardContent className="pt-4">
            <div className="flex items-start gap-3">
              <Bell className="h-5 w-5 text-orange-500 mt-0.5" />
              <div className="flex-1">
                <p className="font-medium text-orange-700 dark:text-orange-400">
                  Alertes récentes
                </p>
                <div className="space-y-1 mt-2">
                  {alerts.alerts.slice(0, 3).map((alert, idx) => (
                    <p key={idx} className="text-sm">
                      {alert.message}
                    </p>
                  ))}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Market Share Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-muted-foreground">Part de marché (volume)</p>
                <p className="text-3xl font-bold text-blue-600">
                  {marketShare?.overall.count_share ?? 0}%
                </p>
              </div>
              <PieChart className="h-8 w-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-muted-foreground">Part de marché (valeur)</p>
                <p className="text-3xl font-bold text-green-600">
                  {marketShare?.overall.value_share ?? 0}%
                </p>
              </div>
              <DollarSign className="h-8 w-8 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-muted-foreground">Concurrents surveillés</p>
                <p className="text-3xl font-bold">{competitors?.length ?? 0}</p>
              </div>
              <Eye className="h-8 w-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-muted-foreground">Mentions détectées</p>
                <p className="text-3xl font-bold text-orange-600">{mentions?.total ?? 0}</p>
              </div>
              <Search className="h-8 w-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="competitors" className="space-y-4">
        <TabsList>
          <TabsTrigger value="competitors">Concurrents</TabsTrigger>
          <TabsTrigger value="mentions">Mentions</TabsTrigger>
          <TabsTrigger value="winners">Analyse Gagnants</TabsTrigger>
          <TabsTrigger value="pricing">Benchmark Prix</TabsTrigger>
        </TabsList>

        {/* Competitors Tab */}
        <TabsContent value="competitors">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <Users className="h-5 w-5" />
                    Concurrents surveillés
                  </CardTitle>
                  <CardDescription>
                    Ajoutez des concurrents pour surveiller leurs mentions
                  </CardDescription>
                </div>
                <Dialog open={isAddDialogOpen} onOpenChange={setIsAddDialogOpen}>
                  <DialogTrigger asChild>
                    <Button>
                      <Plus className="h-4 w-4 mr-2" />
                      Ajouter
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>Ajouter un concurrent</DialogTitle>
                      <DialogDescription>
                        Surveillez les mentions de ce concurrent dans les opportunités
                      </DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4 py-4">
                      <div>
                        <label className="text-sm font-medium">Nom du concurrent</label>
                        <Input
                          placeholder="Ex: Agence XYZ"
                          value={newCompetitor.name}
                          onChange={(e) => setNewCompetitor({ ...newCompetitor, name: e.target.value })}
                        />
                      </div>
                      <div>
                        <label className="text-sm font-medium">Mots-clés (optionnel)</label>
                        <Input
                          placeholder="Ex: xyz, agence-xyz, xyz-events"
                          value={newCompetitor.keywords}
                          onChange={(e) => setNewCompetitor({ ...newCompetitor, keywords: e.target.value })}
                        />
                        <p className="text-xs text-muted-foreground mt-1">
                          Séparez les mots-clés par des virgules
                        </p>
                      </div>
                    </div>
                    <DialogFooter>
                      <Button variant="outline" onClick={() => setIsAddDialogOpen(false)}>
                        Annuler
                      </Button>
                      <Button onClick={handleAddCompetitor} disabled={addMutation.isPending}>
                        {addMutation.isPending ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          "Ajouter"
                        )}
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
                      <TableHead>Actions</TableHead>
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
                              <Badge variant="outline" className="text-xs">
                                +{comp.keywords.length - 3}
                              </Badge>
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
                  <Users className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                  <p className="text-muted-foreground">
                    Aucun concurrent surveillé
                  </p>
                  <p className="text-sm text-muted-foreground">
                    Ajoutez des concurrents pour commencer la veille
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Mentions Tab */}
        <TabsContent value="mentions">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <Search className="h-5 w-5" />
                  Mentions détectées
                </CardTitle>
                <div className="flex gap-1">
                  {(["7d", "30d", "90d"] as const).map((p) => (
                    <Button
                      key={p}
                      variant={mentionsPeriod === p ? "default" : "outline"}
                      size="sm"
                      onClick={() => setMentionsPeriod(p)}
                    >
                      {p}
                    </Button>
                  ))}
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {mentionsLoading ? (
                <div className="flex items-center justify-center h-32">
                  <Loader2 className="h-8 w-8 animate-spin" />
                </div>
              ) : mentions?.mentions.length ? (
                <div className="space-y-3">
                  {mentions.mentions.slice(0, 20).map((mention, idx) => (
                    <div
                      key={idx}
                      className="flex items-start gap-3 p-3 bg-muted rounded-lg"
                    >
                      <AlertTriangle className="h-5 w-5 text-orange-500 mt-0.5" />
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <Badge>{mention.competitor_name}</Badge>
                          <span className="text-xs text-muted-foreground">
                            via &quot;{mention.keyword_matched}&quot;
                          </span>
                        </div>
                        <p className="font-medium">{mention.opportunity.title}</p>
                        <p className="text-sm text-muted-foreground">
                          {mention.opportunity.organization}
                          {mention.opportunity.budget && (
                            <span> • {formatCurrency(mention.opportunity.budget)}</span>
                          )}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <Search className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                  <p className="text-muted-foreground">
                    {mentions?.message || "Aucune mention détectée"}
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Winners Tab */}
        <TabsContent value="winners">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Trophy className="h-5 w-5" />
                Analyse des gagnants
              </CardTitle>
              <CardDescription>
                Qui remporte le plus d&apos;opportunités ?
              </CardDescription>
            </CardHeader>
            <CardContent>
              {winnersLoading ? (
                <div className="flex items-center justify-center h-32">
                  <Loader2 className="h-8 w-8 animate-spin" />
                </div>
              ) : winners ? (
                <div className="space-y-6">
                  {/* Insights */}
                  {winners.insights.length > 0 && (
                    <div className="p-4 bg-blue-50 dark:bg-blue-950/20 rounded-lg">
                      {winners.insights.map((insight, idx) => (
                        <p key={idx} className="text-sm">{insight}</p>
                      ))}
                    </div>
                  )}

                  {/* Top Winners */}
                  <div>
                    <h3 className="font-medium mb-3">🏆 Top gagnants</h3>
                    <div className="space-y-2">
                      {winners.top_winners.slice(0, 10).map((winner, idx) => (
                        <div
                          key={winner.organization}
                          className="flex items-center justify-between p-3 bg-muted rounded-lg"
                        >
                          <div className="flex items-center gap-3">
                            <span className="text-2xl font-bold text-muted-foreground">
                              #{idx + 1}
                            </span>
                            <div>
                              <p className="font-medium">{winner.organization}</p>
                              <div className="flex gap-1 mt-1">
                                {winner.categories.slice(0, 3).map((cat) => (
                                  <Badge key={cat} variant="outline" className="text-xs">
                                    {cat}
                                  </Badge>
                                ))}
                              </div>
                            </div>
                          </div>
                          <div className="text-right">
                            <p className="font-bold">{winner.wins} victoires</p>
                            <p className="text-sm text-muted-foreground">
                              {formatCurrency(winner.total_value)}
                            </p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Potential Competitors */}
                  {winners.potential_competitors.length > 0 && (
                    <div>
                      <h3 className="font-medium mb-3 flex items-center gap-2">
                        <AlertTriangle className="h-4 w-4 text-orange-500" />
                        Concurrents potentiels à surveiller
                      </h3>
                      <div className="flex flex-wrap gap-2">
                        {winners.potential_competitors.map((comp) => (
                          <Badge
                            key={comp.organization}
                            variant="outline"
                            className="cursor-pointer hover:bg-muted"
                            onClick={() => {
                              setNewCompetitor({ name: comp.organization, keywords: "" });
                              setIsAddDialogOpen(true);
                            }}
                          >
                            <Plus className="h-3 w-3 mr-1" />
                            {comp.organization} ({comp.wins} wins)
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <p className="text-center text-muted-foreground py-8">
                  Pas assez de données
                </p>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Pricing Tab */}
        <TabsContent value="pricing">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <DollarSign className="h-5 w-5" />
                Benchmark des prix
              </CardTitle>
              <CardDescription>
                Analyse des budgets par catégorie
              </CardDescription>
            </CardHeader>
            <CardContent>
              {pricingLoading ? (
                <div className="flex items-center justify-center h-32">
                  <Loader2 className="h-8 w-8 animate-spin" />
                </div>
              ) : pricing ? (
                <div className="space-y-6">
                  {/* Global stats */}
                  <div className="grid grid-cols-4 gap-4">
                    <div className="text-center p-4 bg-muted rounded-lg">
                      <p className="text-xs text-muted-foreground">Minimum</p>
                      <p className="text-xl font-bold">{formatCurrency(pricing.global.min)}</p>
                    </div>
                    <div className="text-center p-4 bg-muted rounded-lg">
                      <p className="text-xs text-muted-foreground">Médiane</p>
                      <p className="text-xl font-bold">{formatCurrency(pricing.global.median)}</p>
                    </div>
                    <div className="text-center p-4 bg-muted rounded-lg">
                      <p className="text-xs text-muted-foreground">Moyenne</p>
                      <p className="text-xl font-bold">{formatCurrency(pricing.global.avg)}</p>
                    </div>
                    <div className="text-center p-4 bg-muted rounded-lg">
                      <p className="text-xs text-muted-foreground">Maximum</p>
                      <p className="text-xl font-bold">{formatCurrency(pricing.global.max)}</p>
                    </div>
                  </div>

                  {/* Insights */}
                  {pricing.insights.length > 0 && (
                    <div className="p-4 bg-yellow-50 dark:bg-yellow-950/20 rounded-lg">
                      {pricing.insights.map((insight, idx) => (
                        <p key={idx} className="text-sm">{insight}</p>
                      ))}
                    </div>
                  )}

                  {/* By category */}
                  <div>
                    <h3 className="font-medium mb-3">Par catégorie</h3>
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Catégorie</TableHead>
                          <TableHead className="text-right">Min</TableHead>
                          <TableHead className="text-right">Médiane</TableHead>
                          <TableHead className="text-right">Max</TableHead>
                          <TableHead className="text-right">Nb</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {pricing.by_category.map((cat) => (
                          <TableRow key={cat.category}>
                            <TableCell className="font-medium capitalize">
                              {cat.category}
                            </TableCell>
                            <TableCell className="text-right">
                              {formatCurrency(cat.min)}
                            </TableCell>
                            <TableCell className="text-right">
                              {formatCurrency(cat.median)}
                            </TableCell>
                            <TableCell className="text-right">
                              {formatCurrency(cat.max)}
                            </TableCell>
                            <TableCell className="text-right">
                              <Badge variant="secondary">{cat.count}</Badge>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                </div>
              ) : (
                <p className="text-center text-muted-foreground py-8">
                  Pas assez de données
                </p>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
