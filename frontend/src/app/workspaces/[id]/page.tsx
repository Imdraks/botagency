'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { 
  ArrowLeft,
  Plus, 
  Loader2, 
  Mail,
  Trash2,
  Check,
  Clock,
  Users,
  Shield,
  Eye,
  User,
  Package,
  Zap,
  Building2,
  Rocket,
  Crown,
  Save,
} from 'lucide-react';
import Link from 'next/link';
import { AdminLayout, ProtectedRoute } from "@/components/layout";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { useSubscriptionStore } from "@/store/subscriptionStore";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { format } from 'date-fns';
import { fr } from 'date-fns/locale';
import { toast } from 'sonner';

interface WorkspaceInvite {
  id: number;
  workspace_id: number;
  email: string;
  role: 'admin' | 'member' | 'viewer';
  claimed: boolean;
  claimed_at?: string;
  created_at: string;
}

interface Workspace {
  id: number;
  name: string;
  owner_user_id: number;
  owner_name?: string;
  drive_url?: string;
  members_count: number;
  created_at: string;
}

interface WorkspaceSubscription {
  workspace_id: number;
  workspace_name: string;
  plan: string;
  plan_display_name: string;
  enabled_packs: string[];
  addons: string[];
  max_seats: number;
  current_seats: number;
  available_features: string[];
}

const PLANS = [
  { value: 'mini', label: 'Mini', icon: Zap, color: 'bg-blue-100 text-blue-700', packs: ['core', 'clients'] },
  { value: 'standard', label: 'Standard', icon: Building2, color: 'bg-purple-100 text-purple-700', packs: ['core', 'clients', 'leads', 'talents'] },
  { value: 'premium', label: 'Premium', icon: Rocket, color: 'bg-orange-100 text-orange-700', packs: ['core', 'clients', 'leads', 'talents', 'intelligence'] },
];

const PACKS = [
  { value: 'core', label: 'Core', description: 'Cockpit, Pipeline, Projets, Production, Assets, Calendrier', minPlan: 'mini' },
  { value: 'clients', label: 'Clients', description: 'Gestion des clients, Dossiers, Daily Picks', minPlan: 'mini' },
  { value: 'leads', label: 'Leads', description: 'Leads, Kanban, Scoring', minPlan: 'standard' },
  { value: 'talents', label: 'Talents', description: 'Artistes, Profils, Découverte, Comparaison, Map', minPlan: 'standard' },
  { value: 'intelligence', label: 'Intelligence', description: 'Analytics, Veille concurrentielle, Prédictions IA', minPlan: 'premium' },
];

const ADDONS = [
  { value: 'radar_business', label: 'Radar Business', description: 'CRM étendu, Devis, Factures', includedIn: 'premium' },
];

const roleLabels: Record<string, { label: string; icon: React.ReactNode; color: string }> = {
  admin: { label: 'Admin', icon: <Shield className="h-3 w-3" />, color: 'bg-red-100 text-red-700' },
  member: { label: 'Membre', icon: <User className="h-3 w-3" />, color: 'bg-blue-100 text-blue-700' },
  viewer: { label: 'Viewer', icon: <Eye className="h-3 w-3" />, color: 'bg-gray-100 text-gray-700' },
};

export default function WorkspaceDetailPage() {
  return (
    <ProtectedRoute requiredRoles={['admin']}>
      <AdminLayout>
        <WorkspaceDetailContent />
      </AdminLayout>
    </ProtectedRoute>
  );
}

function WorkspaceDetailContent() {
  const params = useParams();
  const router = useRouter();
  const workspaceId = params.id as string;
  const { fetchSubscription: refreshGlobalSubscription } = useSubscriptionStore();
  
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [subscription, setSubscription] = useState<WorkspaceSubscription | null>(null);
  // Local edit state for subscription changes
  const [editPlan, setEditPlan] = useState<string | null>(null);
  const [editAddons, setEditAddons] = useState<string[] | null>(null);
  const [invites, setInvites] = useState<WorkspaceInvite[]>([]);
  const [loading, setLoading] = useState(true);
  const [adding, setAdding] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [savingSubscription, setSavingSubscription] = useState(false);
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [newEmail, setNewEmail] = useState('');
  const [newRole, setNewRole] = useState<'admin' | 'member' | 'viewer'>('member');
  const [isAdmin, setIsAdmin] = useState<boolean | null>(null); // null = loading

  useEffect(() => {
    // Check admin role
    const token = localStorage.getItem('access_token');
    if (token) {
      try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        setIsAdmin(payload.role === 'admin');
      } catch (e) {}
    }
    
    fetchWorkspace();
    fetchInvites();
    fetchSubscription();
  }, [workspaceId]);

  const fetchWorkspace = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const res = await fetch(`/api/v1/workspaces/${workspaceId}`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setWorkspace(data);
      }
    } catch (err) {
      console.error('Failed to fetch workspace', err);
    }
  };

  const fetchSubscription = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const res = await fetch(`/api/v1/subscription/admin/workspace/${workspaceId}`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setSubscription(data);
        // Reset local edit states
        setEditPlan(null);
        setEditAddons(null);
      }
    } catch (err) {
      console.error('Failed to fetch subscription', err);
    }
  };

  // Check if there are unsaved changes
  const hasChanges = () => {
    if (!subscription) return false;
    if (editPlan !== null && editPlan !== subscription.plan) return true;
    if (editAddons !== null && JSON.stringify(editAddons) !== JSON.stringify(subscription.addons)) return true;
    return false;
  };

  // Get current values (local edit or saved)
  const currentPlan = editPlan ?? subscription?.plan ?? 'standard';
  const currentAddons = editAddons ?? subscription?.addons ?? [];

  const saveSubscriptionChanges = async () => {
    if (!hasChanges()) return;
    
    setSavingSubscription(true);
    try {
      const token = localStorage.getItem('access_token');
      const updates: any = {};
      
      if (editPlan !== null) {
        updates.plan = editPlan;
      }
      if (editAddons !== null) {
        updates.addons = editAddons;
      }
      
      const res = await fetch(`/api/v1/subscription/admin/workspace/${workspaceId}`, {
        method: 'PATCH',
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updates),
      });
      if (res.ok) {
        const data = await res.json();
        setSubscription(data);
        // Reset local edit states
        setEditPlan(null);
        setEditAddons(null);
        // Refresh global subscription store so navigation updates
        refreshGlobalSubscription(parseInt(workspaceId));
        toast.success('Abonnement mis à jour avec succès !');
      } else {
        const error = await res.json();
        toast.error(error.detail || 'Erreur');
      }
    } catch (err) {
      toast.error('Erreur de mise à jour');
    } finally {
      setSavingSubscription(false);
    }
  };

  const toggleAddonLocal = (addonValue: string) => {
    const addons = editAddons ?? subscription?.addons ?? [];
    const newAddons = addons.includes(addonValue)
      ? addons.filter(a => a !== addonValue)
      : [...addons, addonValue];
    setEditAddons(newAddons);
  };

  const changePlanLocal = (planValue: string) => {
    setEditPlan(planValue);
    // When changing plan, also update addons if Premium (auto-include radar_business)
    if (planValue === 'premium') {
      const addons = editAddons ?? subscription?.addons ?? [];
      if (!addons.includes('radar_business')) {
        setEditAddons([...addons, 'radar_business']);
      }
    }
  };

  // Legacy functions for backward compatibility (now unused)
  const updateSubscription = async (updates: Partial<WorkspaceSubscription>) => {
    setSavingSubscription(true);
    try {
      const token = localStorage.getItem('access_token');
      const res = await fetch(`/api/v1/subscription/admin/workspace/${workspaceId}`, {
        method: 'PATCH',
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updates),
      });
      if (res.ok) {
        const data = await res.json();
        setSubscription(data);
        refreshGlobalSubscription(parseInt(workspaceId));
        toast.success('Abonnement mis à jour');
      } else {
        const error = await res.json();
        toast.error(error.detail || 'Erreur');
      }
    } catch (err) {
      toast.error('Erreur de mise à jour');
    } finally {
      setSavingSubscription(false);
    }
  };

  const togglePack = (packValue: string) => {
    if (!subscription) return;
    const currentPacks = subscription.enabled_packs || [];
    const newPacks = currentPacks.includes(packValue)
      ? currentPacks.filter(p => p !== packValue)
      : [...currentPacks, packValue];
    updateSubscription({ enabled_packs: newPacks } as any);
  };

  const toggleAddon = (addonValue: string) => {
    if (!subscription) return;
    const currentAddons = subscription.addons || [];
    const newAddons = currentAddons.includes(addonValue)
      ? currentAddons.filter(a => a !== addonValue)
      : [...currentAddons, addonValue];
    updateSubscription({ addons: newAddons } as any);
  };

  const changePlan = (planValue: string) => {
    updateSubscription({ plan: planValue } as any);
  };

  const fetchInvites = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const res = await fetch(`/api/v1/workspaces/${workspaceId}/invites`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setInvites(data.items || []);
      }
    } catch (err) {
      console.error('Failed to fetch invites', err);
    } finally {
      setLoading(false);
    }
  };

  const addInvite = async () => {
    if (!newEmail.trim()) return;
    
    setAdding(true);
    try {
      const token = localStorage.getItem('access_token');
      const res = await fetch(`/api/v1/workspaces/${workspaceId}/invites`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email: newEmail.trim().toLowerCase(), role: newRole }),
      });
      
      if (res.ok) {
        toast.success('Email autorisé ajouté !');
        setShowAddDialog(false);
        setNewEmail('');
        setNewRole('member');
        fetchInvites();
      } else {
        const error = await res.json();
        toast.error(error.detail || 'Erreur');
      }
    } catch (err) {
      toast.error('Erreur');
    } finally {
      setAdding(false);
    }
  };

  const removeInvite = async (inviteId: number) => {
    try {
      const token = localStorage.getItem('access_token');
      const res = await fetch(`/api/v1/workspaces/${workspaceId}/invites/${inviteId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` },
      });
      
      if (res.ok) {
        toast.success('Email retiré');
        fetchInvites();
      } else {
        toast.error('Erreur');
      }
    } catch (err) {
      toast.error('Erreur');
    }
  };

  const deleteWorkspace = async () => {
    setDeleting(true);
    try {
      const token = localStorage.getItem('access_token');
      const res = await fetch(`/api/v1/workspaces/${workspaceId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` },
      });
      
      if (res.ok) {
        toast.success('Workspace supprimé');
        router.push('/workspaces');
      } else {
        const error = await res.json();
        toast.error(error.detail || 'Erreur de suppression');
      }
    } catch (err) {
      toast.error('Erreur de suppression');
    } finally {
      setDeleting(false);
      setShowDeleteDialog(false);
    }
  };

  // Show loading while checking admin status
  if (isAdmin === null || loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    );
  }

  if (!isAdmin) {
    return (
      <div className="p-6 max-w-4xl mx-auto">
        <Card className="border-red-200 bg-red-50">
          <CardContent className="pt-6">
            <div className="text-center">
              <Shield className="h-12 w-12 mx-auto text-red-500 mb-4" />
              <h2 className="text-xl font-semibold text-red-800">Accès réservé aux administrateurs</h2>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/workspaces">
            <Button variant="ghost" size="icon">
              <ArrowLeft className="h-5 w-5" />
            </Button>
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              {workspace?.name || 'Workspace'}
            </h1>
            <p className="text-gray-500 dark:text-gray-400">
              Gérer les emails autorisés
            </p>
          </div>
        </div>
        <Button 
          variant="destructive" 
          onClick={() => setShowDeleteDialog(true)}
        >
          <Trash2 className="h-4 w-4 mr-2" />
          Supprimer l'instance
        </Button>
      </div>

      {/* Subscription Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Crown className="h-5 w-5 text-yellow-500" />
            Abonnement & Options
            {savingSubscription && <Loader2 className="h-4 w-4 animate-spin text-blue-500" />}
          </CardTitle>
          <CardDescription>
            Gérez le plan, les packs et les add-ons de ce workspace
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Plan Selection */}
          <div className="space-y-3">
            <Label className="text-sm font-medium">Plan</Label>
            <div className="flex gap-2">
              {PLANS.map((plan) => {
                const Icon = plan.icon;
                const isActive = currentPlan === plan.value;
                return (
                  <button
                    key={plan.value}
                    onClick={() => changePlanLocal(plan.value)}
                    disabled={savingSubscription}
                    className={`flex-1 flex items-center justify-center gap-2 p-3 rounded-lg border-2 transition-all ${
                      isActive 
                        ? 'border-blue-500 bg-blue-50 dark:bg-blue-950' 
                        : 'border-gray-200 hover:border-gray-300 dark:border-gray-700'
                    }`}
                  >
                    <Icon className={`h-5 w-5 ${isActive ? 'text-blue-600' : 'text-gray-400'}`} />
                    <span className={isActive ? 'font-semibold text-blue-700' : 'text-gray-600 dark:text-gray-300'}>
                      {plan.label}
                    </span>
                    {isActive && <Check className="h-4 w-4 text-blue-600" />}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Packs */}
          <div className="space-y-3">
            <Label className="text-sm font-medium">Packs activés (selon le plan)</Label>
            <div className="grid gap-3">
              {PACKS.map((pack) => {
                const isEnabled = subscription?.enabled_packs?.includes(pack.value);
                const currentPlan = PLANS.find(p => p.value === subscription?.plan);
                const includedInPlan = currentPlan?.packs?.includes(pack.value) || false;
                return (
                  <div
                    key={pack.value}
                    className={`flex items-center justify-between p-3 rounded-lg ${
                      isEnabled ? 'bg-green-50 dark:bg-green-950 border border-green-200' : 'bg-gray-50 dark:bg-gray-800'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <Package className={`h-5 w-5 ${isEnabled ? 'text-green-600' : 'text-gray-400'}`} />
                      <div>
                        <div className="flex items-center gap-2">
                          <p className="font-medium">{pack.label}</p>
                          {includedInPlan && (
                            <Badge variant="outline" className="text-xs bg-blue-50 text-blue-600 border-blue-200">
                              Inclus dans {currentPlan?.label}
                            </Badge>
                          )}
                        </div>
                        <p className="text-sm text-gray-500">{pack.description}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {isEnabled ? (
                        <Check className="h-5 w-5 text-green-600" />
                      ) : (
                        <span className="text-sm text-gray-400">Non inclus</span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Add-ons */}
          <div className="space-y-3">
            <Label className="text-sm font-medium">Add-ons</Label>
            <div className="grid gap-3">
              {ADDONS.map((addon) => {
                const isEnabled = currentAddons.includes(addon.value);
                const includedInPremium = currentPlan === 'premium';
                return (
                  <div
                    key={addon.value}
                    className={`flex items-center justify-between p-3 rounded-lg ${
                      isEnabled ? 'bg-yellow-50 dark:bg-yellow-950 border border-yellow-200' : 'bg-gray-50 dark:bg-gray-800'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <Zap className={`h-5 w-5 ${isEnabled ? 'text-yellow-600' : 'text-gray-400'}`} />
                      <div>
                        <div className="flex items-center gap-2">
                          <p className="font-medium">{addon.label}</p>
                          {includedInPremium && (
                            <Badge variant="outline" className="text-xs bg-orange-50 text-orange-600 border-orange-200">
                              Inclus dans Premium
                            </Badge>
                          )}
                        </div>
                        <p className="text-sm text-gray-500">{addon.description}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Switch
                        checked={isEnabled}
                        onCheckedChange={() => toggleAddonLocal(addon.value)}
                        disabled={savingSubscription}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Seats info */}
          {subscription && (
            <div className="flex items-center gap-4 p-3 bg-blue-50 dark:bg-blue-950 rounded-lg">
              <Users className="h-5 w-5 text-blue-600" />
              <div>
                <p className="font-medium text-blue-900 dark:text-blue-100">
                  {subscription.current_seats} / {subscription.max_seats} sièges utilisés
                </p>
                <p className="text-sm text-blue-600">
                  {subscription.max_seats - subscription.current_seats} sièges disponibles
                </p>
              </div>
            </div>
          )}

          {/* Save Button */}
          {hasChanges() && (
            <div className="flex justify-end pt-4 border-t">
              <Button 
                onClick={saveSubscriptionChanges}
                disabled={savingSubscription}
                className="bg-green-600 hover:bg-green-700"
              >
                {savingSubscription ? (
                  <>
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                    Enregistrement...
                  </>
                ) : (
                  <>
                    <Save className="h-4 w-4 mr-2" />
                    Enregistrer les modifications
                  </>
                )}
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Info Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            Emails Autorisés
          </CardTitle>
          <CardDescription>
            Les utilisateurs avec ces emails seront automatiquement ajoutés à ce workspace lors de leur connexion.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Add Button */}
          <Button onClick={() => setShowAddDialog(true)}>
            <Plus className="h-4 w-4 mr-2" />
            Ajouter un Email
          </Button>

          {/* Invites List */}
          {invites.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <Mail className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>Aucun email autorisé</p>
              <p className="text-sm">Ajoutez des emails pour autoriser l'accès à ce workspace</p>
            </div>
          ) : (
            <div className="space-y-2">
              {invites.map((invite) => (
                <div
                  key={invite.id}
                  className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    <Mail className="h-5 w-5 text-gray-400" />
                    <div>
                      <p className="font-medium">{invite.email}</p>
                      <div className="flex items-center gap-2 text-sm text-gray-500">
                        <Badge variant="outline" className={roleLabels[invite.role].color}>
                          {roleLabels[invite.role].icon}
                          <span className="ml-1">{roleLabels[invite.role].label}</span>
                        </Badge>
                        {invite.claimed ? (
                          <span className="flex items-center gap-1 text-green-600">
                            <Check className="h-3 w-3" />
                            Utilisé
                          </span>
                        ) : (
                          <span className="flex items-center gap-1 text-orange-500">
                            <Clock className="h-3 w-3" />
                            En attente
                          </span>
                        )}
                        <span className="text-gray-400">
                          Ajouté le {format(new Date(invite.created_at), 'dd MMM yyyy', { locale: fr })}
                        </span>
                      </div>
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="text-red-500 hover:text-red-700 hover:bg-red-50"
                    onClick={() => removeInvite(invite.id)}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Add Dialog */}
      <Dialog open={showAddDialog} onOpenChange={setShowAddDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Ajouter un Email Autorisé</DialogTitle>
            <DialogDescription>
              L'utilisateur avec cet email sera automatiquement ajouté au workspace lors de sa connexion.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="exemple@email.com"
                value={newEmail}
                onChange={(e) => setNewEmail(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="role">Rôle dans le workspace</Label>
              <Select value={newRole} onValueChange={(v: any) => setNewRole(v)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="admin">
                    <div className="flex items-center gap-2">
                      <Shield className="h-4 w-4 text-red-500" />
                      Admin - Accès complet
                    </div>
                  </SelectItem>
                  <SelectItem value="member">
                    <div className="flex items-center gap-2">
                      <User className="h-4 w-4 text-blue-500" />
                      Membre - Lecture/Écriture
                    </div>
                  </SelectItem>
                  <SelectItem value="viewer">
                    <div className="flex items-center gap-2">
                      <Eye className="h-4 w-4 text-gray-500" />
                      Viewer - Lecture seule
                    </div>
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowAddDialog(false)}>
              Annuler
            </Button>
            <Button onClick={addInvite} disabled={adding || !newEmail.trim()}>
              {adding && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
              Ajouter
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="text-red-600">Supprimer l'instance</DialogTitle>
            <DialogDescription>
              Êtes-vous sûr de vouloir supprimer le workspace <strong>"{workspace?.name}"</strong> ?
              <br /><br />
              Cette action est <strong className="text-red-600">irréversible</strong> et supprimera :
              <ul className="list-disc list-inside mt-2 text-sm">
                <li>Tous les emails autorisés</li>
                <li>Tous les membres associés</li>
                <li>Toutes les configurations</li>
              </ul>
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDeleteDialog(false)}>
              Annuler
            </Button>
            <Button variant="destructive" onClick={deleteWorkspace} disabled={deleting}>
              {deleting && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
              Supprimer définitivement
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
