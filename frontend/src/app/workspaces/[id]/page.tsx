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
} from 'lucide-react';
import Link from 'next/link';
import { AppLayout, ProtectedRoute } from "@/components/layout";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
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

const roleLabels: Record<string, { label: string; icon: React.ReactNode; color: string }> = {
  admin: { label: 'Admin', icon: <Shield className="h-3 w-3" />, color: 'bg-red-100 text-red-700' },
  member: { label: 'Membre', icon: <User className="h-3 w-3" />, color: 'bg-blue-100 text-blue-700' },
  viewer: { label: 'Viewer', icon: <Eye className="h-3 w-3" />, color: 'bg-gray-100 text-gray-700' },
};

export default function WorkspaceDetailPage() {
  return (
    <ProtectedRoute>
      <AppLayout>
        <WorkspaceDetailContent />
      </AppLayout>
    </ProtectedRoute>
  );
}

function WorkspaceDetailContent() {
  const params = useParams();
  const router = useRouter();
  const workspaceId = params.id as string;
  
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [invites, setInvites] = useState<WorkspaceInvite[]>([]);
  const [loading, setLoading] = useState(true);
  const [adding, setAdding] = useState(false);
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [newEmail, setNewEmail] = useState('');
  const [newRole, setNewRole] = useState<'admin' | 'member' | 'viewer'>('member');
  const [isAdmin, setIsAdmin] = useState(false);

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

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      {/* Header */}
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
    </div>
  );
}
