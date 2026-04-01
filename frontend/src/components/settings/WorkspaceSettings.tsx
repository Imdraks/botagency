"use client";

import { useEffect, useState, useCallback } from "react";
import {
  Building2,
  Users,
  Landmark,
  Plus,
  Trash2,
  Crown,
  Shield,
  Eye,
  RefreshCw,
  UserPlus,
  MoreVertical,
  Save,
  AlertTriangle,
  Loader2,
  Settings2,
  ChevronRight,
  Lock,
  Mail,
  KeyRound,
  Copy,
  Check,
  Clock,
  MailPlus,
  CheckCircle2,
} from "lucide-react";
import { cn } from "@/lib/utils";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { useAuthStore } from "@/store/auth";
import { useBankingStore } from "@/store/bankingStore";
import { BankCard, ConnectBankDialog, BankStatusBadge, SyncStatusBadge } from "@/components/banking";

// ============================================================================
// TYPES
// ============================================================================

interface WorkspaceMember {
  id: number;
  user_id: number;
  role: "admin" | "member" | "viewer";
  user_name: string | null;
  user_email: string | null;
  user_avatar: string | null;
  invited_at: string | null;
  accepted_at: string | null;
}

interface WorkspaceDetail {
  id: number;
  name: string;
  owner_user_id: number;
  owner_name: string | null;
  drive_root_folder_id: string | null;
  drive_url: string | null;
  templates_folder_id: string | null;
  calendar_id: string | null;
  settings: Record<string, any> | null;
  members_count: number;
  members: WorkspaceMember[];
  created_at: string;
  updated_at: string;
}

interface InviteEmail {
  id: number;
  workspace_id: number;
  email: string;
  role: "admin" | "member" | "viewer";
  claimed: boolean;
  claimed_at: string | null;
  created_at: string;
}

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export function WorkspaceSettings() {
  const { user } = useAuthStore();
  const [workspace, setWorkspace] = useState<WorkspaceDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState("general");

  // Determine workspace ID from localStorage
  const workspaceId =
    typeof window !== "undefined"
      ? localStorage.getItem("current_workspace_id")
      : null;

  // Determine if user is workspace admin
  const isOwner = workspace?.owner_user_id === user?.id;
  const memberEntry = workspace?.members.find((m) => m.user_id === user?.id);
  const isWsAdmin = isOwner || memberEntry?.role === "admin" || user?.is_superuser === true;

  const fetchWorkspace = useCallback(async () => {
    if (!workspaceId) return;
    setIsLoading(true);
    setError(null);
    try {
      const { data } = await api.get(`/workspaces/${workspaceId}`);
      setWorkspace(data);
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Impossible de charger l'espace de travail");
    } finally {
      setIsLoading(false);
    }
  }, [workspaceId]);

  useEffect(() => {
    fetchWorkspace();
  }, [fetchWorkspace]);

  if (!workspaceId) {
    return (
      <Card>
        <CardContent className="py-12 text-center text-sm text-gray-400">
          Aucun espace de travail sélectionné.
        </CardContent>
      </Card>
    );
  }

  if (isLoading) {
    return (
      <Card>
        <CardContent className="py-12 flex items-center justify-center gap-2 text-sm text-gray-400">
          <Loader2 className="h-4 w-4 animate-spin" />
          Chargement…
        </CardContent>
      </Card>
    );
  }

  if (error || !workspace) {
    return (
      <Card>
        <CardContent className="py-12 text-center text-sm text-red-500">
          {error || "Erreur inconnue"}
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="flex-wrap h-auto gap-1">
          <TabsTrigger value="general" className="text-xs">
            <Building2 className="h-3.5 w-3.5 mr-1.5" />
            Général
          </TabsTrigger>
          <TabsTrigger value="members" className="text-xs">
            <Users className="h-3.5 w-3.5 mr-1.5" />
            Membres
          </TabsTrigger>
          <TabsTrigger value="banking" className="text-xs">
            <Landmark className="h-3.5 w-3.5 mr-1.5" />
            Banques
          </TabsTrigger>
        </TabsList>

        <TabsContent value="general">
          <GeneralSection
            workspace={workspace}
            isAdmin={isWsAdmin}
            onUpdated={fetchWorkspace}
          />
        </TabsContent>

        <TabsContent value="members">
          <MembersSection
            workspace={workspace}
            isAdmin={isWsAdmin}
            isSuperUser={user?.is_superuser === true}
            currentUserId={user?.id || 0}
            onUpdated={fetchWorkspace}
          />
        </TabsContent>

        <TabsContent value="banking">
          <BankingSection isAdmin={isWsAdmin} />
        </TabsContent>
      </Tabs>
    </div>
  );
}

// ============================================================================
// GENERAL SECTION
// ============================================================================

function GeneralSection({
  workspace,
  isAdmin,
  onUpdated,
}: {
  workspace: WorkspaceDetail;
  isAdmin: boolean;
  onUpdated: () => void;
}) {
  const [name, setName] = useState(workspace.name);
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleSave = async () => {
    if (!name.trim()) return;
    setSaving(true);
    try {
      await api.patch(`/workspaces/${workspace.id}`, { name: name.trim() });
      setSuccess(true);
      onUpdated();
      setTimeout(() => setSuccess(false), 2000);
    } catch (err) {
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Building2 className="h-5 w-5 text-purple-600" />
          Informations de l&apos;espace de travail
        </CardTitle>
        <CardDescription>
          Paramètres généraux de votre espace de travail
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Workspace Name */}
        <div className="space-y-2">
          <Label htmlFor="ws_name">Nom de l&apos;espace de travail</Label>
          <div className="flex items-center gap-2">
            <Input
              id="ws_name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              disabled={!isAdmin}
              placeholder="Mon Agence"
            />
            {isAdmin && (
              <Button onClick={handleSave} disabled={saving || !name.trim() || name === workspace.name} size="sm">
                {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
              </Button>
            )}
          </div>
          {success && (
            <p className="text-xs text-emerald-600">✓ Enregistré</p>
          )}
        </div>

        {/* Info Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <InfoBlock label="Propriétaire" value={workspace.owner_name || "—"} />
          <InfoBlock label="Membres" value={`${workspace.members_count} utilisateur${workspace.members_count > 1 ? "s" : ""}`} />
          <InfoBlock label="Créé le" value={formatDate(workspace.created_at)} />
          <InfoBlock label="Dernière modification" value={formatDate(workspace.updated_at)} />
        </div>

        {/* Google Drive */}
        {workspace.drive_url && (
          <div className="rounded-lg border border-gray-200 dark:border-slate-700 p-4">
            <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Google Drive
            </p>
            <a
              href={workspace.drive_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-purple-600 hover:underline"
            >
              Ouvrir le dossier Drive →
            </a>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function InfoBlock({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg bg-gray-50 dark:bg-slate-800/50 px-4 py-3">
      <p className="text-xs text-gray-400 mb-0.5">{label}</p>
      <p className="text-sm font-medium text-gray-900 dark:text-white">{value}</p>
    </div>
  );
}

// ============================================================================
// MEMBERS SECTION
// ============================================================================

function MembersSection({
  workspace,
  isAdmin,
  isSuperUser,
  currentUserId,
  onUpdated,
}: {
  workspace: WorkspaceDetail;
  isAdmin: boolean;
  isSuperUser: boolean;
  currentUserId: number;
  onUpdated: () => void;
}) {
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [addEmail, setAddEmail] = useState("");
  const [addRole, setAddRole] = useState<"admin" | "member" | "viewer">("member");
  const [addAuthProvider, setAddAuthProvider] = useState<"credentials" | "google">("credentials");
  const [addPassword, setAddPassword] = useState("");
  const [isAdding, setIsAdding] = useState(false);
  const [addError, setAddError] = useState<string | null>(null);

  // Reset password state
  const [showResetDialog, setShowResetDialog] = useState(false);
  const [resetMember, setResetMember] = useState<WorkspaceMember | null>(null);
  const [isResetting, setIsResetting] = useState(false);
  const [generatedPassword, setGeneratedPassword] = useState<string | null>(null);
  const [resetError, setResetError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  // Invite (authorized emails) state
  const [invites, setInvites] = useState<InviteEmail[]>([]);
  const [invitesLoading, setInvitesLoading] = useState(false);
  const [showInviteDialog, setShowInviteDialog] = useState(false);
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState<"admin" | "member" | "viewer">("member");
  const [isInviting, setIsInviting] = useState(false);
  const [inviteError, setInviteError] = useState<string | null>(null);

  // Fetch invites
  const fetchInvites = useCallback(async () => {
    if (!isAdmin) return;
    setInvitesLoading(true);
    try {
      const { data } = await api.get(`/workspaces/${workspace.id}/invites`);
      setInvites(data.items || []);
    } catch (err) {
      console.error("Failed to fetch invites", err);
    } finally {
      setInvitesLoading(false);
    }
  }, [workspace.id, isAdmin]);

  useEffect(() => {
    fetchInvites();
  }, [fetchInvites]);

  const handleAddInvite = async () => {
    if (!inviteEmail.trim()) return;
    setIsInviting(true);
    setInviteError(null);
    try {
      await api.post(`/workspaces/${workspace.id}/invites`, {
        email: inviteEmail.trim().toLowerCase(),
        role: inviteRole,
      });
      setInviteEmail("");
      setInviteRole("member");
      setShowInviteDialog(false);
      fetchInvites();
    } catch (err: any) {
      setInviteError(err?.response?.data?.detail || "Erreur lors de l'ajout");
    } finally {
      setIsInviting(false);
    }
  };

  const handleRemoveInvite = async (inviteId: number) => {
    try {
      await api.delete(`/workspaces/${workspace.id}/invites/${inviteId}`);
      fetchInvites();
    } catch (err) {
      console.error(err);
    }
  };

  const handleResetPassword = async (member: WorkspaceMember) => {
    setResetMember(member);
    setGeneratedPassword(null);
    setResetError(null);
    setCopied(false);
    setShowResetDialog(true);
  };

  const confirmResetPassword = async () => {
    if (!resetMember) return;
    setIsResetting(true);
    setResetError(null);
    try {
      const { data } = await api.post(
        `/workspaces/${workspace.id}/members/${resetMember.id}/reset-password`,
        {}
      );
      setGeneratedPassword(data.generated_password);
    } catch (err: any) {
      setResetError(err?.response?.data?.detail || "Erreur lors de la réinitialisation");
    } finally {
      setIsResetting(false);
    }
  };

  const copyPassword = () => {
    if (generatedPassword) {
      navigator.clipboard.writeText(generatedPassword);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleAddMember = async () => {
    if (!addEmail.trim()) return;
    if (isSuperUser && addAuthProvider === "credentials" && addPassword.length < 6) {
      setAddError("Le mot de passe doit contenir au moins 6 caractères");
      return;
    }
    setIsAdding(true);
    setAddError(null);
    try {
      const payload: Record<string, string> = {
        user_email: addEmail.trim().toLowerCase(),
        role: addRole,
      };
      if (isSuperUser) {
        payload.auth_provider = addAuthProvider;
        if (addAuthProvider === "credentials") {
          payload.password = addPassword;
        }
      }
      await api.post(`/workspaces/${workspace.id}/members`, payload);
      setAddEmail("");
      setAddRole("member");
      setAddAuthProvider("credentials");
      setAddPassword("");
      setShowAddDialog(false);
      onUpdated();
    } catch (err: any) {
      setAddError(err?.response?.data?.detail || "Erreur lors de l'ajout");
    } finally {
      setIsAdding(false);
    }
  };

  const handleUpdateRole = async (memberId: number, newRole: string) => {
    try {
      await api.patch(`/workspaces/${workspace.id}/members/${memberId}`, {
        role: newRole,
      });
      onUpdated();
    } catch (err) {
      console.error(err);
    }
  };

  const handleRemoveMember = async (memberId: number) => {
    if (!confirm("Êtes-vous sûr de vouloir retirer ce membre ?")) return;
    try {
      await api.delete(`/workspaces/${workspace.id}/members/${memberId}`);
      onUpdated();
    } catch (err) {
      console.error(err);
    }
  };

  const roleIcon = (role: string) => {
    switch (role) {
      case "admin": return <Shield className="h-3.5 w-3.5 text-purple-600" />;
      case "member": return <Users className="h-3.5 w-3.5 text-blue-600" />;
      case "viewer": return <Eye className="h-3.5 w-3.5 text-gray-400" />;
      default: return null;
    }
  };

  const roleLabel = (role: string) => {
    switch (role) {
      case "admin": return "Admin";
      case "member": return "Membre";
      case "viewer": return "Lecteur";
      default: return role;
    }
  };

  const roleBadgeColor = (role: string) => {
    switch (role) {
      case "admin": return "bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400";
      case "member": return "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400";
      case "viewer": return "bg-gray-100 text-gray-600 dark:bg-slate-700 dark:text-gray-400";
      default: return "";
    }
  };

  return (
    <>
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Users className="h-5 w-5 text-blue-600" />
                Membres de l&apos;espace
              </CardTitle>
              <CardDescription>
                {workspace.members_count} membre{workspace.members_count > 1 ? "s" : ""}
              </CardDescription>
            </div>
            {isAdmin && (
              <Button size="sm" onClick={() => setShowAddDialog(true)}>
                <UserPlus className="h-4 w-4 mr-2" />
                Ajouter
              </Button>
            )}
          </div>
        </CardHeader>
        <CardContent>
          <div className="divide-y divide-gray-100 dark:divide-slate-800">
            {/* Owner row */}
            <div className="flex items-center justify-between py-3">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-full bg-gradient-to-br from-amber-400 to-orange-500 flex items-center justify-center flex-shrink-0">
                  <Crown className="h-4 w-4 text-white" />
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-900 dark:text-white">
                    {workspace.owner_name || "Propriétaire"}
                  </p>
                  <p className="text-xs text-gray-400">Propriétaire</p>
                </div>
              </div>
              <span className={cn(
                "inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium",
                "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400"
              )}>
                <Crown className="h-3 w-3" />
                Propriétaire
              </span>
            </div>

            {/* Members */}
            {workspace.members.map((member) => (
              <div key={member.id} className="flex items-center justify-between py-3">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-full bg-gray-100 dark:bg-slate-800 flex items-center justify-center flex-shrink-0">
                    {member.user_avatar ? (
                      <img
                        src={member.user_avatar}
                        alt=""
                        className="w-9 h-9 rounded-full object-cover"
                      />
                    ) : (
                      <span className="text-sm font-medium text-gray-500">
                        {(member.user_name || member.user_email || "?")
                          .charAt(0)
                          .toUpperCase()}
                      </span>
                    )}
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-900 dark:text-white">
                      {member.user_name || member.user_email}
                    </p>
                    {member.user_email && member.user_name && (
                      <p className="text-xs text-gray-400">{member.user_email}</p>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <span className={cn(
                    "inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium",
                    roleBadgeColor(member.role)
                  )}>
                    {roleIcon(member.role)}
                    {roleLabel(member.role)}
                  </span>

                  {isAdmin && member.user_id !== currentUserId && (
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon" className="h-8 w-8">
                          <MoreVertical className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end" className="w-44">
                        <DropdownMenuItem onClick={() => handleUpdateRole(member.id, "admin")}>
                          <Shield className="h-4 w-4 mr-2 text-purple-600" />
                          Passer Admin
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={() => handleUpdateRole(member.id, "member")}>
                          <Users className="h-4 w-4 mr-2 text-blue-600" />
                          Passer Membre
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={() => handleUpdateRole(member.id, "viewer")}>
                          <Eye className="h-4 w-4 mr-2 text-gray-400" />
                          Passer Lecteur
                        </DropdownMenuItem>
                        {isSuperUser && (
                          <>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem onClick={() => handleResetPassword(member)}>
                              <KeyRound className="h-4 w-4 mr-2 text-amber-600" />
                              Réinitialiser le mot de passe
                            </DropdownMenuItem>
                          </>
                        )}
                        <DropdownMenuSeparator />
                        <DropdownMenuItem
                          onClick={() => handleRemoveMember(member.id)}
                          className="text-red-600 dark:text-red-400"
                        >
                          <Trash2 className="h-4 w-4 mr-2" />
                          Retirer
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  )}
                </div>
              </div>
            ))}

            {workspace.members.length === 0 && (
              <div className="py-6 text-center text-sm text-gray-400">
                Aucun membre ajouté. Invitez votre équipe !
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Authorized Emails Section */}
      {isAdmin && (
        <Card className="mt-4">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <MailPlus className="h-5 w-5 text-purple-600" />
                  Emails Autorisés
                </CardTitle>
                <CardDescription>
                  Les utilisateurs avec ces emails seront automatiquement ajoutés à ce workspace lors de leur connexion.
                </CardDescription>
              </div>
              <Button size="sm" onClick={() => setShowInviteDialog(true)}>
                <Plus className="h-4 w-4 mr-2" />
                Ajouter un Email
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {invitesLoading ? (
              <div className="py-6 flex items-center justify-center gap-2 text-sm text-gray-400">
                <Loader2 className="h-4 w-4 animate-spin" />
                Chargement…
              </div>
            ) : invites.length === 0 ? (
              <div className="py-6 text-center text-sm text-gray-400">
                Aucun email autorisé. Ajoutez des emails pour permettre l&apos;accès automatique.
              </div>
            ) : (
              <div className="divide-y divide-gray-100 dark:divide-slate-800">
                {invites.map((invite) => (
                  <div key={invite.id} className="flex items-center justify-between py-3">
                    <div className="flex items-center gap-3">
                      <div className="w-9 h-9 rounded-full bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center flex-shrink-0">
                        <Mail className="h-4 w-4 text-purple-600 dark:text-purple-400" />
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-900 dark:text-white">
                          {invite.email}
                        </p>
                        <div className="flex items-center gap-2 mt-0.5">
                          <span className={cn(
                            "inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full text-[10px] font-medium",
                            roleBadgeColor(invite.role)
                          )}>
                            {roleIcon(invite.role)}
                            {roleLabel(invite.role)}
                          </span>
                          {invite.claimed ? (
                            <span className="inline-flex items-center gap-1 text-[10px] text-emerald-600 dark:text-emerald-400">
                              <CheckCircle2 className="h-3 w-3" />
                              Activé
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 text-[10px] text-amber-600 dark:text-amber-400">
                              <Clock className="h-3 w-3" />
                              En attente
                            </span>
                          )}
                          <span className="text-[10px] text-gray-400">
                            Ajouté le {new Date(invite.created_at).toLocaleDateString("fr-FR", { day: "numeric", month: "long", year: "numeric" })}
                          </span>
                        </div>
                      </div>
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8 text-red-500 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-950/30"
                      onClick={() => handleRemoveInvite(invite.id)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Add Invite Dialog */}
      <Dialog open={showInviteDialog} onOpenChange={setShowInviteDialog}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <MailPlus className="h-5 w-5 text-purple-600" />
              Ajouter un Email Autorisé
            </DialogTitle>
            <DialogDescription>
              L&apos;utilisateur avec cet email sera automatiquement ajouté au workspace lors de sa connexion.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Email</Label>
              <Input
                type="email"
                placeholder="exemple@email.com"
                value={inviteEmail}
                onChange={(e) => setInviteEmail(e.target.value)}
                autoFocus
              />
            </div>

            <div className="space-y-2">
              <Label>Rôle dans le workspace</Label>
              <Select value={inviteRole} onValueChange={(v) => setInviteRole(v as any)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="admin">
                    <span className="flex items-center gap-2">
                      <Shield className="h-3.5 w-3.5 text-purple-600" />
                      Admin
                    </span>
                  </SelectItem>
                  <SelectItem value="member">
                    <span className="flex items-center gap-2">
                      <Users className="h-3.5 w-3.5 text-blue-600" />
                      Membre - Lecture/Écriture
                    </span>
                  </SelectItem>
                  <SelectItem value="viewer">
                    <span className="flex items-center gap-2">
                      <Eye className="h-3.5 w-3.5 text-gray-400" />
                      Lecteur
                    </span>
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>

            {inviteError && (
              <p className="text-sm text-red-500 flex items-center gap-1">
                <AlertTriangle className="h-3.5 w-3.5" />
                {inviteError}
              </p>
            )}
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowInviteDialog(false)}>
              Annuler
            </Button>
            <Button
              onClick={handleAddInvite}
              disabled={!inviteEmail.trim() || isInviting}
            >
              {isInviting ? (
                <Loader2 className="h-4 w-4 animate-spin mr-2" />
              ) : (
                <Plus className="h-4 w-4 mr-2" />
              )}
              Ajouter
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Add Member Dialog */}
      <Dialog open={showAddDialog} onOpenChange={setShowAddDialog}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <UserPlus className="h-5 w-5 text-blue-600" />
              Ajouter un membre
            </DialogTitle>
            <DialogDescription>
              {isSuperUser
                ? "Invitez un utilisateur existant ou créez un nouveau compte."
                : "Invitez un utilisateur existant par son adresse email."}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Email</Label>
              <Input
                type="email"
                placeholder="utilisateur@email.com"
                value={addEmail}
                onChange={(e) => setAddEmail(e.target.value)}
                autoFocus
              />
            </div>

            <div className="space-y-2">
              <Label>Rôle</Label>
              <Select value={addRole} onValueChange={(v) => setAddRole(v as any)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="admin">Admin</SelectItem>
                  <SelectItem value="member">Membre</SelectItem>
                  <SelectItem value="viewer">Lecteur</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {isSuperUser && (
              <>
                <div className="space-y-2">
                  <Label>Type de compte</Label>
                  <Select value={addAuthProvider} onValueChange={(v) => setAddAuthProvider(v as "credentials" | "google")}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="credentials">
                        <span className="flex items-center gap-2">
                          <Lock className="h-3.5 w-3.5" />
                          Email &amp; mot de passe
                        </span>
                      </SelectItem>
                      <SelectItem value="google">
                        <span className="flex items-center gap-2">
                          <Mail className="h-3.5 w-3.5" />
                          Compte Google (SSO)
                        </span>
                      </SelectItem>
                    </SelectContent>
                  </Select>
                  <p className="text-xs text-gray-400">
                    {addAuthProvider === "google"
                      ? "L'utilisateur se connectera via Google Sign-In."
                      : "L'utilisateur se connectera avec un email et un mot de passe."}
                  </p>
                </div>

                {addAuthProvider === "credentials" && (
                  <div className="space-y-2">
                    <Label>Mot de passe temporaire</Label>
                    <Input
                      type="password"
                      placeholder="Min. 6 caractères"
                      value={addPassword}
                      onChange={(e) => setAddPassword(e.target.value)}
                    />
                  </div>
                )}
              </>
            )}

            {addError && (
              <p className="text-sm text-red-500 flex items-center gap-1">
                <AlertTriangle className="h-3.5 w-3.5" />
                {addError}
              </p>
            )}
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowAddDialog(false)}>
              Annuler
            </Button>
            <Button
              onClick={handleAddMember}
              disabled={!addEmail.trim() || isAdding}
            >
              {isAdding ? (
                <Loader2 className="h-4 w-4 animate-spin mr-2" />
              ) : (
                <UserPlus className="h-4 w-4 mr-2" />
              )}
              Ajouter
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Reset Password Dialog */}
      <Dialog open={showResetDialog} onOpenChange={(open) => {
        if (!open) {
          setShowResetDialog(false);
          setGeneratedPassword(null);
          setResetError(null);
        }
      }}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <KeyRound className="h-5 w-5 text-amber-600" />
              Réinitialiser le mot de passe
            </DialogTitle>
            <DialogDescription>
              {generatedPassword
                ? "Le nouveau mot de passe a été généré. Transmettez-le à l'utilisateur."
                : `Générer un nouveau mot de passe pour ${resetMember?.user_name || resetMember?.user_email || "cet utilisateur"} ?`}
            </DialogDescription>
          </DialogHeader>

          {!generatedPassword && !resetError && (
            <div className="py-2">
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Un mot de passe aléatoire sera généré. L&apos;utilisateur devra l&apos;utiliser pour se reconnecter.
              </p>
            </div>
          )}

          {generatedPassword && (
            <div className="space-y-3">
              <div className="rounded-lg border border-amber-200 dark:border-amber-800 bg-amber-50 dark:bg-amber-950/30 p-4">
                <p className="text-xs text-amber-600 dark:text-amber-400 mb-1 font-medium">Nouveau mot de passe :</p>
                <div className="flex items-center gap-2">
                  <code className="flex-1 text-lg font-mono font-bold text-amber-800 dark:text-amber-300 select-all">
                    {generatedPassword}
                  </code>
                  <Button variant="outline" size="icon" className="h-8 w-8 shrink-0" onClick={copyPassword}>
                    {copied ? <Check className="h-4 w-4 text-emerald-600" /> : <Copy className="h-4 w-4" />}
                  </Button>
                </div>
              </div>
              <p className="text-xs text-gray-400 flex items-center gap-1">
                <AlertTriangle className="h-3 w-3" />
                Ce mot de passe ne sera plus affiché après fermeture.
              </p>
            </div>
          )}

          {resetError && (
            <p className="text-sm text-red-500 flex items-center gap-1">
              <AlertTriangle className="h-3.5 w-3.5" />
              {resetError}
            </p>
          )}

          <DialogFooter>
            {!generatedPassword ? (
              <>
                <Button variant="outline" onClick={() => setShowResetDialog(false)}>
                  Annuler
                </Button>
                <Button
                  onClick={confirmResetPassword}
                  disabled={isResetting}
                  className="bg-amber-600 hover:bg-amber-700 text-white"
                >
                  {isResetting ? (
                    <Loader2 className="h-4 w-4 animate-spin mr-2" />
                  ) : (
                    <KeyRound className="h-4 w-4 mr-2" />
                  )}
                  Générer un nouveau mot de passe
                </Button>
              </>
            ) : (
              <Button onClick={() => setShowResetDialog(false)}>
                Fermer
              </Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}

// ============================================================================
// BANKING SECTION
// ============================================================================

function BankingSection({ isAdmin }: { isAdmin: boolean }) {
  const {
    dashboard,
    connections,
    selectedConnection,
    isLoading,
    error,
    fetchDashboard,
    fetchConnectionDetail,
    isSyncing,
    triggerSync,
    updateConnection,
  } = useBankingStore();

  const [selectedId, setSelectedId] = useState<number | null>(null);

  useEffect(() => {
    fetchDashboard();
  }, [fetchDashboard]);

  useEffect(() => {
    if (selectedId) {
      fetchConnectionDetail(selectedId);
    }
  }, [selectedId, fetchConnectionDetail]);

  const formatCurrency = (val: number) =>
    new Intl.NumberFormat("fr-FR", { style: "currency", currency: "EUR" }).format(val);

  const formatDateShort = (d?: string | null) => {
    if (!d) return "—";
    return new Date(d).toLocaleDateString("fr-FR", {
      day: "2-digit",
      month: "short",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  // Not enabled
  if (dashboard && !dashboard.banking_enabled) {
    return (
      <Card>
        <CardContent className="py-12 text-center">
          <div className="w-14 h-14 rounded-2xl bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center mx-auto mb-4">
            <Landmark className="h-7 w-7 text-purple-600 dark:text-purple-400" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
            Connexions bancaires
          </h3>
          <p className="text-sm text-gray-500 dark:text-gray-400 max-w-md mx-auto">
            Cette fonctionnalité n&apos;est pas activée pour votre espace de travail.
            Souscrivez à l&apos;addon <strong>Radar Business</strong> pour en bénéficier.
          </p>
        </CardContent>
      </Card>
    );
  }

  // Detail view for selected connection
  if (selectedId && selectedConnection) {
    return (
      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <Button variant="ghost" size="sm" onClick={() => setSelectedId(null)}>
              ← Retour
            </Button>
            <div className="flex items-center gap-2">
              {selectedConnection.bank_logo_url ? (
                <img
                  src={selectedConnection.bank_logo_url}
                  alt=""
                  className="w-8 h-8 rounded-lg object-contain bg-gray-50 dark:bg-slate-800 p-0.5"
                />
              ) : (
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-500 to-blue-600 flex items-center justify-center">
                  <Landmark className="h-4 w-4 text-white" />
                </div>
              )}
              <div>
                <CardTitle className="text-base">{selectedConnection.bank_name}</CardTitle>
                <div className="flex items-center gap-2 mt-0.5">
                  <BankStatusBadge status={selectedConnection.status} size="sm" />
                </div>
              </div>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Accounts */}
          <div>
            <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-3">
              Comptes ({selectedConnection.accounts.length})
            </h4>
            {selectedConnection.accounts.length > 0 ? (
              <div className="space-y-2">
                {selectedConnection.accounts.map((acc) => (
                  <div key={acc.id} className="flex items-center justify-between px-3 py-2.5 rounded-lg bg-gray-50 dark:bg-slate-800/50">
                    <div className="flex items-center gap-2.5 min-w-0">
                      <div
                        className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                        style={{ backgroundColor: acc.display_color || "#8B5CF6" }}
                      />
                      <div className="min-w-0">
                        <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                          {acc.account_name}
                        </p>
                        <p className="text-xs text-gray-400">
                          {acc.account_type} · {acc.currency}
                          {acc.iban_masked && ` · ${acc.iban_masked}`}
                        </p>
                      </div>
                    </div>
                    <p className="text-sm font-bold text-gray-900 dark:text-white">
                      {acc.balance != null ? formatCurrency(acc.balance) : "—"}
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-400 text-center py-4">Aucun compte. Lancez une synchronisation.</p>
            )}
          </div>

          {/* Sync + Settings for admin */}
          {isAdmin && (
            <div className="space-y-4">
              {/* Sync button */}
              {(selectedConnection.status === "CONNECTED" || selectedConnection.status === "SYNC_ERROR") && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => triggerSync(selectedConnection.id)}
                  disabled={isSyncing[selectedConnection.id]}
                >
                  <RefreshCw className={cn("h-4 w-4 mr-1", isSyncing[selectedConnection.id] && "animate-spin")} />
                  {isSyncing[selectedConnection.id] ? "Synchronisation…" : "Synchroniser"}
                </Button>
              )}

              {/* Auto sync toggle */}
              <div className="flex items-center justify-between p-3 rounded-lg bg-gray-50 dark:bg-slate-800">
                <div>
                  <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    Synchronisation auto
                  </p>
                  <p className="text-xs text-gray-400">
                    Toutes les {selectedConnection.sync_frequency_hours}h
                  </p>
                </div>
                <button
                  onClick={() =>
                    updateConnection(selectedConnection.id, {
                      auto_sync_enabled: !selectedConnection.auto_sync_enabled,
                    })
                  }
                  className={cn(
                    "relative w-11 h-6 rounded-full transition-colors",
                    selectedConnection.auto_sync_enabled ? "bg-purple-600" : "bg-gray-300 dark:bg-gray-600",
                  )}
                >
                  <span
                    className={cn(
                      "absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white shadow transition-transform",
                      selectedConnection.auto_sync_enabled && "translate-x-5",
                    )}
                  />
                </button>
              </div>

              {/* Recent syncs */}
              {selectedConnection.recent_syncs.length > 0 && (
                <div>
                  <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-2">
                    Dernières synchronisations
                  </h4>
                  <div className="space-y-1.5">
                    {selectedConnection.recent_syncs.slice(0, 5).map((sync) => (
                      <div key={sync.id} className="flex items-center justify-between px-3 py-2 rounded-lg bg-gray-50 dark:bg-slate-800/50 text-xs">
                        <div className="flex items-center gap-2">
                          <SyncStatusBadge status={sync.status} />
                          <span className="text-gray-500">{formatDateShort(sync.started_at)}</span>
                        </div>
                        <span className="text-gray-400">
                          {sync.accounts_synced} comptes
                          {sync.duration_ms != null && ` · ${(sync.duration_ms / 1000).toFixed(1)}s`}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    );
  }

  // List view
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Landmark className="h-5 w-5 text-purple-600" />
              Connexions bancaires
            </CardTitle>
            <CardDescription>
              {connections.length} banque{connections.length !== 1 ? "s" : ""} connectée{connections.length !== 1 ? "s" : ""}
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => fetchDashboard()}
              disabled={isLoading}
            >
              <RefreshCw className={cn("h-4 w-4", isLoading && "animate-spin")} />
            </Button>
            {isAdmin && <ConnectBankDialog />}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {/* Summary stats */}
        {dashboard && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
            <MiniStat label="Connectées" value={dashboard.active_connections} />
            <MiniStat label="Comptes" value={dashboard.total_accounts} />
            <MiniStat
              label="Solde EUR"
              value={
                dashboard.total_balances["EUR"]
                  ? formatCurrency(dashboard.total_balances["EUR"])
                  : "—"
              }
            />
            <MiniStat
              label="Dernière sync"
              value={dashboard.last_sync_at ? formatDateShort(dashboard.last_sync_at) : "Jamais"}
            />
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="mb-4 px-3 py-2 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 text-sm flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 flex-shrink-0" />
            {error}
          </div>
        )}

        {/* Consent alerts */}
        {dashboard && dashboard.expiring_consents > 0 && (
          <div className="mb-4 px-3 py-2 rounded-lg bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800/50 text-amber-700 dark:text-amber-400 text-sm flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 flex-shrink-0" />
            {dashboard.expiring_consents} consentement{dashboard.expiring_consents > 1 ? "s" : ""}{" "}
            expire{dashboard.expiring_consents > 1 ? "nt" : ""} bientôt.
          </div>
        )}

        {/* Connections */}
        {isLoading && connections.length === 0 ? (
          <div className="flex items-center justify-center py-8 text-gray-400 text-sm">
            <Loader2 className="h-4 w-4 animate-spin mr-2" />
            Chargement…
          </div>
        ) : connections.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {connections.map((conn) => (
              <BankCard
                key={conn.id}
                connection={conn}
                onSelect={(id) => setSelectedId(id)}
                isAdmin={isAdmin}
              />
            ))}
          </div>
        ) : (
          <div className="py-10 text-center">
            <div className="w-12 h-12 rounded-2xl bg-gray-100 dark:bg-slate-800 flex items-center justify-center mx-auto mb-3">
              <Landmark className="h-6 w-6 text-gray-400" />
            </div>
            <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-1">
              Aucune banque connectée
            </h3>
            <p className="text-xs text-gray-500 dark:text-gray-400 max-w-xs mx-auto mb-4">
              Connectez votre première banque pour centraliser la vue de vos comptes professionnels.
            </p>
            {isAdmin && <ConnectBankDialog />}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function MiniStat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-lg bg-gray-50 dark:bg-slate-800/50 px-3 py-2.5 text-center">
      <p className="text-[10px] uppercase tracking-wider text-gray-400 mb-0.5">{label}</p>
      <p className="text-sm font-bold text-gray-900 dark:text-white">{value}</p>
    </div>
  );
}

// ============================================================================
// HELPERS
// ============================================================================

function formatDate(d?: string | null) {
  if (!d) return "—";
  return new Date(d).toLocaleDateString("fr-FR", {
    day: "2-digit",
    month: "long",
    year: "numeric",
  });
}
