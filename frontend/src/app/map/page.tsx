"use client";

import { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import dynamic from "next/dynamic";
import {
  MapPin,
  Euro,
  TrendingUp,
  Building,
  Clock,
  Filter,
  Layers,
  ChevronRight,
  X,
  ZoomIn,
  ZoomOut,
} from "lucide-react";
import { AppLayout, ProtectedRoute } from "@/components/layout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Slider } from "@/components/ui/slider";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  formatCurrency,
  formatRelativeDate,
  getStatusColor,
  getStatusLabel,
  getScoreColor,
  getScoreBgColor,
} from "@/lib/utils";

// Types
interface MapMarker {
  id: number;
  title: string;
  lat: number;
  lng: number;
  score: number;
  status: string;
  category: string | null;
  budget: number | null;
  deadline: string | null;
  organization: string | null;
  region: string;
}

interface RegionStats {
  name: string;
  lat: number;
  lng: number;
  count: number;
  won: number;
  total_value: number;
  avg_score: number;
}

interface MapData {
  markers: MapMarker[];
  clusters: RegionStats[];
  total: number;
  center: { lat: number; lng: number };
  zoom: number;
}

// API functions
const mapApi = {
  getOpportunities: async (params: {
    status?: string;
    min_score?: number;
  }): Promise<MapData> => {
    const token = localStorage.getItem("token");
    const queryParams = new URLSearchParams();
    if (params.status) queryParams.append("status", params.status);
    if (params.min_score) queryParams.append("min_score", params.min_score.toString());
    
    const response = await fetch(`/api/v1/map/opportunities?${queryParams}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    
    if (!response.ok) {
      // Return mock data if API not ready
      return {
        markers: [],
        clusters: [
          { name: "Île-de-France", lat: 48.8566, lng: 2.3522, count: 45, won: 12, total_value: 2500000, avg_score: 72 },
          { name: "Auvergne-Rhône-Alpes", lat: 45.764, lng: 4.8357, count: 28, won: 8, total_value: 1800000, avg_score: 68 },
          { name: "Provence-Alpes-Côte d'Azur", lat: 43.2965, lng: 5.3698, count: 22, won: 6, total_value: 1200000, avg_score: 65 },
          { name: "Nouvelle-Aquitaine", lat: 44.8378, lng: -0.5792, count: 18, won: 5, total_value: 950000, avg_score: 70 },
          { name: "Occitanie", lat: 43.6047, lng: 1.4442, count: 15, won: 4, total_value: 780000, avg_score: 63 },
          { name: "Hauts-de-France", lat: 49.8941, lng: 2.2958, count: 12, won: 3, total_value: 620000, avg_score: 66 },
          { name: "Grand Est", lat: 48.5734, lng: 7.7521, count: 10, won: 2, total_value: 450000, avg_score: 61 },
          { name: "Bretagne", lat: 48.1173, lng: -1.6778, count: 8, won: 2, total_value: 380000, avg_score: 69 },
          { name: "Pays de la Loire", lat: 47.2184, lng: -1.5536, count: 7, won: 2, total_value: 320000, avg_score: 64 },
          { name: "Normandie", lat: 49.1829, lng: -0.3707, count: 5, won: 1, total_value: 180000, avg_score: 58 },
        ],
        total: 170,
        center: { lat: 46.2276, lng: 2.2137 },
        zoom: 6,
      };
    }
    
    return response.json();
  },
  
  getRegionStats: async (): Promise<RegionStats[]> => {
    const token = localStorage.getItem("token");
    const response = await fetch("/api/v1/map/regions/stats", {
      headers: { Authorization: `Bearer ${token}` },
    });
    
    if (!response.ok) {
      return [];
    }
    
    return response.json();
  },
};

// Simple Map Component without Leaflet (for now, showing stats cards)
function SimpleMapView({ data, selectedRegion, onSelectRegion }: {
  data: MapData;
  selectedRegion: string | null;
  onSelectRegion: (region: string | null) => void;
}) {
  const maxCount = Math.max(...data.clusters.map(c => c.count));
  
  return (
    <div className="relative h-[500px] bg-gradient-to-b from-blue-50 to-blue-100 rounded-lg overflow-hidden border">
      {/* France SVG Placeholder */}
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="relative w-[400px] h-[400px]">
          {/* Region bubbles */}
          {data.clusters.map((region) => {
            const size = Math.max(40, (region.count / maxCount) * 100);
            // Approximate position based on coordinates
            const x = ((region.lng + 5) / 15) * 400;
            const y = ((52 - region.lat) / 12) * 400;
            const isSelected = selectedRegion === region.name;
            
            return (
              <button
                key={region.name}
                className={`absolute transform -translate-x-1/2 -translate-y-1/2 rounded-full flex items-center justify-center transition-all duration-200 hover:scale-110 hover:z-10 ${
                  isSelected 
                    ? 'bg-primary text-primary-foreground ring-4 ring-primary/30 z-10' 
                    : 'bg-white text-foreground shadow-lg hover:shadow-xl'
                }`}
                style={{
                  left: `${x}px`,
                  top: `${y}px`,
                  width: `${size}px`,
                  height: `${size}px`,
                  fontSize: `${Math.max(10, size / 4)}px`,
                }}
                onClick={() => onSelectRegion(isSelected ? null : region.name)}
              >
                <span className="font-bold">{region.count}</span>
              </button>
            );
          })}
        </div>
      </div>
      
      {/* Legend */}
      <div className="absolute bottom-4 left-4 bg-white/90 backdrop-blur-sm rounded-lg p-3 shadow-lg">
        <p className="text-xs font-medium text-muted-foreground mb-2">Légende</p>
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-full bg-primary/20 border-2 border-primary" />
          <span className="text-xs">= 10 leads</span>
        </div>
        <div className="flex items-center gap-2 mt-1">
          <div className="w-10 h-10 rounded-full bg-primary/20 border-2 border-primary" />
          <span className="text-xs">= 40+ leads</span>
        </div>
      </div>
      
      {/* Controls */}
      <div className="absolute top-4 right-4 flex flex-col gap-2">
        <Button variant="secondary" size="icon" className="shadow-lg">
          <ZoomIn className="h-4 w-4" />
        </Button>
        <Button variant="secondary" size="icon" className="shadow-lg">
          <ZoomOut className="h-4 w-4" />
        </Button>
        <Button variant="secondary" size="icon" className="shadow-lg">
          <Layers className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}

// Region detail panel
function RegionPanel({ region, onClose }: { region: RegionStats; onClose: () => void }) {
  const winRate = region.won / region.count * 100;
  
  return (
    <Card className="mt-4 animate-in slide-in-from-bottom-4">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg flex items-center gap-2">
            <MapPin className="h-5 w-5 text-primary" />
            {region.name}
          </CardTitle>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div>
            <p className="text-2xl font-bold">{region.count}</p>
            <p className="text-sm text-muted-foreground">Leads</p>
          </div>
          <div>
            <p className="text-2xl font-bold text-green-600">{region.won}</p>
            <p className="text-sm text-muted-foreground">Gagnés</p>
          </div>
          <div>
            <p className="text-2xl font-bold">{formatCurrency(region.total_value)}</p>
            <p className="text-sm text-muted-foreground">Valeur totale</p>
          </div>
          <div>
            <p className="text-2xl font-bold">{region.avg_score.toFixed(0)}</p>
            <p className="text-sm text-muted-foreground">Score moyen</p>
          </div>
        </div>
        
        {/* Win rate bar */}
        <div className="mt-4">
          <div className="flex items-center justify-between text-sm mb-1">
            <span>Taux de conversion</span>
            <span className="font-medium">{winRate.toFixed(0)}%</span>
          </div>
          <div className="h-2 bg-muted rounded-full overflow-hidden">
            <div 
              className="h-full bg-green-500 rounded-full transition-all"
              style={{ width: `${winRate}%` }}
            />
          </div>
        </div>
        
        <div className="mt-4 flex gap-2">
          <Link href={`/leads?region=${encodeURIComponent(region.name)}`} className="flex-1">
            <Button className="w-full gap-2">
              Voir les leads
              <ChevronRight className="h-4 w-4" />
            </Button>
          </Link>
        </div>
      </CardContent>
    </Card>
  );
}

function MapContent() {
  const [selectedRegion, setSelectedRegion] = useState<string | null>(null);
  const [minScore, setMinScore] = useState<number>(0);
  const [statusFilter, setStatusFilter] = useState<string>("all");

  const { data, isLoading } = useQuery<MapData>({
    queryKey: ["map", "opportunities", minScore, statusFilter],
    queryFn: () => mapApi.getOpportunities({
      min_score: minScore > 0 ? minScore : undefined,
      status: statusFilter !== "all" ? statusFilter : undefined,
    }),
  });

  const selectedRegionData = data?.clusters.find(c => c.name === selectedRegion);

  // Calculate totals
  const totals = data?.clusters.reduce(
    (acc, region) => ({
      leads: acc.leads + region.count,
      won: acc.won + region.won,
      value: acc.value + region.total_value,
    }),
    { leads: 0, won: 0, value: 0 }
  ) || { leads: 0, won: 0, value: 0 };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold">Carte des Opportunités</h1>
          <p className="text-muted-foreground">
            Visualisez la répartition géographique de vos leads
          </p>
        </div>
        
        {/* Stats */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1.5 bg-blue-50 rounded-lg">
            <MapPin className="h-4 w-4 text-blue-600" />
            <span className="text-sm font-medium text-blue-700">{totals.leads} leads</span>
          </div>
          <div className="flex items-center gap-2 px-3 py-1.5 bg-green-50 rounded-lg">
            <TrendingUp className="h-4 w-4 text-green-600" />
            <span className="text-sm font-medium text-green-700">{totals.won} gagnés</span>
          </div>
          <div className="flex items-center gap-2 px-3 py-1.5 bg-purple-50 rounded-lg">
            <Euro className="h-4 w-4 text-purple-600" />
            <span className="text-sm font-medium text-purple-700">{formatCurrency(totals.value)}</span>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-4 p-4 bg-muted/30 rounded-lg">
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm font-medium">Filtres:</span>
        </div>
        
        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground">Score min:</span>
          <div className="w-32">
            <Slider
              value={[minScore]}
              onValueChange={([value]) => setMinScore(value)}
              max={100}
              step={10}
            />
          </div>
          <span className="text-sm font-medium w-8">{minScore}</span>
        </div>
        
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-[150px]">
            <SelectValue placeholder="Statut" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Tous statuts</SelectItem>
            <SelectItem value="new">Nouveau</SelectItem>
            <SelectItem value="in_progress">En cours</SelectItem>
            <SelectItem value="submitted">Soumis</SelectItem>
          </SelectContent>
        </Select>
        
        {(minScore > 0 || statusFilter !== "all") && (
          <Button 
            variant="ghost" 
            size="sm"
            onClick={() => {
              setMinScore(0);
              setStatusFilter("all");
            }}
          >
            Réinitialiser
          </Button>
        )}
      </div>

      {/* Map */}
      {isLoading ? (
        <div className="h-[500px] bg-muted rounded-lg flex items-center justify-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary" />
        </div>
      ) : data ? (
        <SimpleMapView 
          data={data} 
          selectedRegion={selectedRegion}
          onSelectRegion={setSelectedRegion}
        />
      ) : null}

      {/* Selected Region Panel */}
      {selectedRegionData && (
        <RegionPanel 
          region={selectedRegionData} 
          onClose={() => setSelectedRegion(null)} 
        />
      )}

      {/* Region Rankings */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top regions by volume */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Top Régions par Volume</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {data?.clusters
                .sort((a, b) => b.count - a.count)
                .slice(0, 5)
                .map((region, i) => (
                  <div 
                    key={region.name} 
                    className="flex items-center gap-3 p-2 rounded-lg hover:bg-muted/50 cursor-pointer transition-colors"
                    onClick={() => setSelectedRegion(region.name)}
                  >
                    <span className="text-2xl font-bold text-muted-foreground w-8">
                      {i + 1}
                    </span>
                    <div className="flex-1">
                      <p className="font-medium">{region.name}</p>
                      <p className="text-sm text-muted-foreground">
                        {region.count} leads · Score moy: {region.avg_score.toFixed(0)}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="font-medium text-green-600">
                        {formatCurrency(region.total_value)}
                      </p>
                    </div>
                  </div>
                ))}
            </div>
          </CardContent>
        </Card>

        {/* Top regions by win rate */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Meilleures Performances</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {data?.clusters
                .filter(r => r.count >= 5)
                .sort((a, b) => (b.won / b.count) - (a.won / a.count))
                .slice(0, 5)
                .map((region, i) => {
                  const winRate = (region.won / region.count * 100).toFixed(0);
                  return (
                    <div 
                      key={region.name} 
                      className="flex items-center gap-3 p-2 rounded-lg hover:bg-muted/50 cursor-pointer transition-colors"
                      onClick={() => setSelectedRegion(region.name)}
                    >
                      <span className="text-2xl font-bold text-muted-foreground w-8">
                        {i + 1}
                      </span>
                      <div className="flex-1">
                        <p className="font-medium">{region.name}</p>
                        <div className="flex items-center gap-2 mt-1">
                          <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
                            <div 
                              className="h-full bg-green-500 rounded-full"
                              style={{ width: `${winRate}%` }}
                            />
                          </div>
                          <span className="text-sm font-medium text-green-600 w-12">
                            {winRate}%
                          </span>
                        </div>
                      </div>
                      <Badge variant="secondary">
                        {region.won}/{region.count}
                      </Badge>
                    </div>
                  );
                })}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default function MapPage() {
  return (
    <ProtectedRoute>
      <AppLayout>
        <MapContent />
      </AppLayout>
    </ProtectedRoute>
  );
}
