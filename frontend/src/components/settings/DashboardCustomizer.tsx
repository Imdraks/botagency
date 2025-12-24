"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  LayoutDashboard,
  GripVertical,
  X,
  Plus,
  TrendingUp,
  Calendar,
  Clock,
  BarChart2,
  PieChart,
  Activity,
  Target,
  Bell,
  Eye,
  Settings,
} from "lucide-react";

interface Widget {
  id: string;
  type: WidgetType;
  title: string;
  size: "small" | "medium" | "large";
  enabled: boolean;
  position: number;
  settings?: Record<string, any>;
}

type WidgetType =
  | "stats"
  | "chart"
  | "recent"
  | "deadlines"
  | "sources"
  | "top_scored"
  | "activity"
  | "notifications"
  | "score_distribution"
  | "budget_overview";

const WIDGET_TYPES: { type: WidgetType; label: string; icon: any; description: string }[] = [
  { type: "stats", label: "Statistiques", icon: BarChart2, description: "Vue d'ensemble des chiffres clés" },
  { type: "chart", label: "Graphique tendance", icon: TrendingUp, description: "Évolution dans le temps" },
  { type: "recent", label: "Récentes", icon: Clock, description: "Dernières opportunités" },
  { type: "deadlines", label: "Deadlines", icon: Calendar, description: "Échéances à venir" },
  { type: "sources", label: "Sources", icon: PieChart, description: "Répartition par source" },
  { type: "top_scored", label: "Top scores", icon: Target, description: "Meilleures opportunités" },
  { type: "activity", label: "Activité", icon: Activity, description: "Actions récentes" },
  { type: "notifications", label: "Notifications", icon: Bell, description: "Alertes et notifications" },
  { type: "score_distribution", label: "Distribution scores", icon: BarChart2, description: "Répartition des scores" },
  { type: "budget_overview", label: "Budgets", icon: TrendingUp, description: "Synthèse des budgets" },
];

const STORAGE_KEY = "dashboard_widgets_config";

const DEFAULT_WIDGETS: Widget[] = [
  { id: "1", type: "stats", title: "Statistiques", size: "large", enabled: true, position: 0 },
  { id: "2", type: "chart", title: "Tendance", size: "medium", enabled: true, position: 1 },
  { id: "3", type: "recent", title: "Récentes", size: "medium", enabled: true, position: 2 },
  { id: "4", type: "deadlines", title: "Deadlines", size: "small", enabled: true, position: 3 },
  { id: "5", type: "sources", title: "Sources", size: "small", enabled: true, position: 4 },
  { id: "6", type: "top_scored", title: "Top Scores", size: "medium", enabled: false, position: 5 },
];

export function DashboardCustomizer() {
  const [widgets, setWidgets] = useState<Widget[]>(DEFAULT_WIDGETS);
  const [isEditMode, setIsEditMode] = useState(false);
  const [addWidgetOpen, setAddWidgetOpen] = useState(false);
  const [editingWidget, setEditingWidget] = useState<Widget | null>(null);
  const [draggedWidget, setDraggedWidget] = useState<string | null>(null);

  // Load from localStorage
  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      try {
        setWidgets(JSON.parse(stored));
      } catch (e) {
        console.error("Failed to parse widget config:", e);
      }
    }
  }, []);

  // Save to localStorage
  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(widgets));
  }, [widgets]);

  const handleToggleWidget = (id: string) => {
    setWidgets((prev) =>
      prev.map((w) => (w.id === id ? { ...w, enabled: !w.enabled } : w))
    );
  };

  const handleRemoveWidget = (id: string) => {
    setWidgets((prev) => prev.filter((w) => w.id !== id));
  };

  const handleAddWidget = (type: WidgetType) => {
    const widgetInfo = WIDGET_TYPES.find((w) => w.type === type);
    if (!widgetInfo) return;

    const newWidget: Widget = {
      id: crypto.randomUUID(),
      type,
      title: widgetInfo.label,
      size: "medium",
      enabled: true,
      position: widgets.length,
    };

    setWidgets((prev) => [...prev, newWidget]);
    setAddWidgetOpen(false);
  };

  const handleUpdateWidget = (updatedWidget: Widget) => {
    setWidgets((prev) =>
      prev.map((w) => (w.id === updatedWidget.id ? updatedWidget : w))
    );
    setEditingWidget(null);
  };

  const handleDragStart = (id: string) => {
    setDraggedWidget(id);
  };

  const handleDragOver = (e: React.DragEvent, targetId: string) => {
    e.preventDefault();
    if (draggedWidget === targetId) return;

    setWidgets((prev) => {
      const draggedIdx = prev.findIndex((w) => w.id === draggedWidget);
      const targetIdx = prev.findIndex((w) => w.id === targetId);
      if (draggedIdx === -1 || targetIdx === -1) return prev;

      const newWidgets = [...prev];
      const [dragged] = newWidgets.splice(draggedIdx, 1);
      newWidgets.splice(targetIdx, 0, dragged);

      return newWidgets.map((w, i) => ({ ...w, position: i }));
    });
  };

  const handleDragEnd = () => {
    setDraggedWidget(null);
  };

  const handleReset = () => {
    setWidgets(DEFAULT_WIDGETS);
  };

  const enabledWidgets = widgets.filter((w) => w.enabled);
  const availableTypes = WIDGET_TYPES.filter(
    (t) => !widgets.some((w) => w.type === t.type)
  );

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <LayoutDashboard className="h-5 w-5" />
            Personnalisation du Dashboard
          </CardTitle>
          <div className="flex items-center gap-2">
            <Button
              variant={isEditMode ? "default" : "outline"}
              size="sm"
              onClick={() => setIsEditMode(!isEditMode)}
            >
              <Settings className="h-4 w-4 mr-2" />
              {isEditMode ? "Terminer" : "Modifier"}
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {isEditMode && (
            <div className="flex justify-between items-center mb-4 p-3 bg-muted rounded-lg">
              <p className="text-sm text-muted-foreground">
                Glissez-déposez les widgets pour les réorganiser
              </p>
              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setAddWidgetOpen(true)}
                  disabled={availableTypes.length === 0}
                >
                  <Plus className="h-4 w-4 mr-2" />
                  Ajouter un widget
                </Button>
                <Button size="sm" variant="ghost" onClick={handleReset}>
                  Réinitialiser
                </Button>
              </div>
            </div>
          )}

          {/* Widget list */}
          <div className="space-y-2">
            {widgets
              .sort((a, b) => a.position - b.position)
              .map((widget) => {
                const widgetInfo = WIDGET_TYPES.find((w) => w.type === widget.type);
                const Icon = widgetInfo?.icon || LayoutDashboard;

                return (
                  <div
                    key={widget.id}
                    draggable={isEditMode}
                    onDragStart={() => handleDragStart(widget.id)}
                    onDragOver={(e) => handleDragOver(e, widget.id)}
                    onDragEnd={handleDragEnd}
                    className={`flex items-center justify-between p-3 border rounded-lg transition-all ${
                      isEditMode ? "cursor-move hover:bg-muted/50" : ""
                    } ${draggedWidget === widget.id ? "opacity-50" : ""} ${
                      !widget.enabled ? "opacity-60" : ""
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      {isEditMode && (
                        <GripVertical className="h-4 w-4 text-muted-foreground" />
                      )}
                      <Icon className="h-5 w-5 text-muted-foreground" />
                      <div>
                        <p className="font-medium">{widget.title}</p>
                        <p className="text-xs text-muted-foreground">
                          {widgetInfo?.description}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <Badge variant="outline" className="text-xs">
                        {widget.size === "small"
                          ? "Petit"
                          : widget.size === "medium"
                          ? "Moyen"
                          : "Grand"}
                      </Badge>
                      
                      <Switch
                        checked={widget.enabled}
                        onCheckedChange={() => handleToggleWidget(widget.id)}
                      />

                      {isEditMode && (
                        <>
                          <Button
                            size="icon"
                            variant="ghost"
                            onClick={() => setEditingWidget(widget)}
                          >
                            <Settings className="h-4 w-4" />
                          </Button>
                          <Button
                            size="icon"
                            variant="ghost"
                            className="text-red-500 hover:text-red-600"
                            onClick={() => handleRemoveWidget(widget.id)}
                          >
                            <X className="h-4 w-4" />
                          </Button>
                        </>
                      )}
                    </div>
                  </div>
                );
              })}
          </div>

          {widgets.length === 0 && (
            <div className="text-center py-8 text-muted-foreground">
              <LayoutDashboard className="h-12 w-12 mx-auto mb-4 opacity-20" />
              <p>Aucun widget configuré</p>
              <Button
                size="sm"
                variant="outline"
                className="mt-2"
                onClick={() => setAddWidgetOpen(true)}
              >
                <Plus className="h-4 w-4 mr-2" />
                Ajouter un widget
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Preview */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Eye className="h-5 w-5" />
            Aperçu du Dashboard
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {enabledWidgets.map((widget) => {
              const Icon = WIDGET_TYPES.find((w) => w.type === widget.type)?.icon || LayoutDashboard;
              const sizeClass =
                widget.size === "large"
                  ? "md:col-span-2 lg:col-span-3"
                  : widget.size === "medium"
                  ? "md:col-span-1 lg:col-span-2"
                  : "";

              return (
                <div
                  key={widget.id}
                  className={`border rounded-lg p-4 bg-muted/30 ${sizeClass}`}
                >
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <Icon className="h-4 w-4" />
                    <span className="text-sm font-medium">{widget.title}</span>
                  </div>
                  <div className="mt-2 h-20 flex items-center justify-center text-muted-foreground/50 text-sm">
                    [Contenu du widget]
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Add Widget Dialog */}
      <Dialog open={addWidgetOpen} onOpenChange={setAddWidgetOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Ajouter un widget</DialogTitle>
          </DialogHeader>
          <div className="grid gap-2 py-4">
            {availableTypes.map((widget) => {
              const Icon = widget.icon;
              return (
                <button
                  key={widget.type}
                  onClick={() => handleAddWidget(widget.type)}
                  className="flex items-center gap-3 p-3 border rounded-lg hover:bg-muted transition-colors text-left"
                >
                  <Icon className="h-5 w-5 text-muted-foreground" />
                  <div>
                    <p className="font-medium">{widget.label}</p>
                    <p className="text-xs text-muted-foreground">{widget.description}</p>
                  </div>
                </button>
              );
            })}
            {availableTypes.length === 0 && (
              <p className="text-center text-muted-foreground py-4">
                Tous les widgets ont déjà été ajoutés
              </p>
            )}
          </div>
        </DialogContent>
      </Dialog>

      {/* Edit Widget Dialog */}
      <Dialog open={!!editingWidget} onOpenChange={() => setEditingWidget(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Modifier le widget</DialogTitle>
          </DialogHeader>
          {editingWidget && (
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Titre</label>
                <Input
                  value={editingWidget.title}
                  onChange={(e) =>
                    setEditingWidget({ ...editingWidget, title: e.target.value })
                  }
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Taille</label>
                <Select
                  value={editingWidget.size}
                  onValueChange={(value: "small" | "medium" | "large") =>
                    setEditingWidget({ ...editingWidget, size: value })
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="small">Petit (1/3)</SelectItem>
                    <SelectItem value="medium">Moyen (2/3)</SelectItem>
                    <SelectItem value="large">Grand (pleine largeur)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditingWidget(null)}>
              Annuler
            </Button>
            <Button onClick={() => editingWidget && handleUpdateWidget(editingWidget)}>
              Enregistrer
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
