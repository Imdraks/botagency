'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { 
  Building2,
  Users,
  FolderOpen,
  Activity,
  Settings,
  Shield,
  BarChart3,
  Mail,
  CheckCircle,
  Clock,
  AlertTriangle,
  Plus,
  Loader2,
} from 'lucide-react';
import Link from 'next/link';
import { ProtectedRoute } from "@/components/layout";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { useAuthStore } from '@/store/auth';

interface DashboardStats {
  total_workspaces: number;
  total_users: number;
  pending_invites: number;
  active_users_today: number;
}

interface Workspace {
  id: number;
  name: string;
  members_count: number;
  owner_name?: string;
}

export default function AdminDashboardPage() {
  return (
    <ProtectedRoute>
      <AdminDashboardContent />
    </ProtectedRoute>
  );
}

function AdminDashboardContent() {
  const router = useRouter();
  const { user } = useAuthStore();
  const [stats, setStats] = useState<DashboardStats>({
    total_workspaces: 0,
    total_users: 0,
    pending_invites: 0,
    active_users_today: 0,
  });
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Redirect non-admin users
    if (user && user.role !== 'admin') {
      router.push('/today');
      return;
    }
    
    fetchData();
  }, [user, router]);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem('access_token');
      
      // Fetch workspaces
      const wsRes = await fetch('/api/v1/workspaces', {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (wsRes.ok) {
        const data = await wsRes.json();
        setWorkspaces(data.items || []);
        setStats(prev => ({ ...prev, total_workspaces: data.total || 0 }));
      }
      
      // Fetch users count
      const usersRes = await fetch('/api/v1/users?limit=1', {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (usersRes.ok) {
        const data = await usersRes.json();
        setStats(prev => ({ ...prev, total_users: data.total || 0 }));
      }
      
    } catch (err) {
      console.error('Failed to fetch admin data', err);
    } finally {
      setLoading(false);
    }
  };

  if (user?.role !== 'admin') {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      {/* Header */}
      <header className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 bg-gradient-to-br from-violet-500 to-purple-600 rounded-xl flex items-center justify-center">
                <Shield className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900 dark:text-white">
                  Panel Admin
                </h1>
                <p className="text-sm text-gray-500">Gestion des instances Radar</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-sm text-gray-500">
                Connecté en tant que <strong>{user?.full_name}</strong>
              </span>
              <Button variant="outline" onClick={() => {
                localStorage.removeItem('access_token');
                router.push('/login');
              }}>
                Déconnexion
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8 space-y-8">
        {/* Stats Cards */}
        <div className="grid gap-4 md:grid-cols-4">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                  <Building2 className="h-6 w-6 text-blue-600" />
                </div>
                <div>
                  <p className="text-2xl font-bold">{stats.total_workspaces}</p>
                  <p className="text-sm text-gray-500">Workspaces</p>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-green-100 dark:bg-green-900/30 rounded-lg">
                  <Users className="h-6 w-6 text-green-600" />
                </div>
                <div>
                  <p className="text-2xl font-bold">{stats.total_users}</p>
                  <p className="text-sm text-gray-500">Utilisateurs</p>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-orange-100 dark:bg-orange-900/30 rounded-lg">
                  <Mail className="h-6 w-6 text-orange-600" />
                </div>
                <div>
                  <p className="text-2xl font-bold">{stats.pending_invites}</p>
                  <p className="text-sm text-gray-500">Invitations en attente</p>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
                  <Activity className="h-6 w-6 text-purple-600" />
                </div>
                <div>
                  <p className="text-2xl font-bold">{stats.active_users_today}</p>
                  <p className="text-sm text-gray-500">Actifs aujourd'hui</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Quick Actions */}
        <div className="grid gap-4 md:grid-cols-3">
          <Link href="/workspaces">
            <Card className="cursor-pointer hover:shadow-md transition-shadow h-full">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FolderOpen className="h-5 w-5 text-blue-600" />
                  Gérer les Workspaces
                </CardTitle>
                <CardDescription>
                  Créer, configurer et gérer les instances des agences
                </CardDescription>
              </CardHeader>
            </Card>
          </Link>
          
          <Link href="/users">
            <Card className="cursor-pointer hover:shadow-md transition-shadow h-full">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Users className="h-5 w-5 text-green-600" />
                  Gérer les Utilisateurs
                </CardTitle>
                <CardDescription>
                  Gérer les comptes et permissions des utilisateurs
                </CardDescription>
              </CardHeader>
            </Card>
          </Link>
          
          <Link href="/admin/activity">
            <Card className="cursor-pointer hover:shadow-md transition-shadow h-full">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Activity className="h-5 w-5 text-purple-600" />
                  Logs d'Activité
                </CardTitle>
                <CardDescription>
                  Voir l'historique des actions sur la plateforme
                </CardDescription>
              </CardHeader>
            </Card>
          </Link>
        </div>

        {/* Workspaces List */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>Workspaces (Instances)</CardTitle>
              <CardDescription>Toutes les agences utilisant Radar</CardDescription>
            </div>
            <Link href="/workspaces">
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                Nouveau Workspace
              </Button>
            </Link>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
              </div>
            ) : workspaces.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <Building2 className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>Aucun workspace créé</p>
              </div>
            ) : (
              <div className="space-y-3">
                {workspaces.map((ws) => (
                  <Link key={ws.id} href={`/workspaces/${ws.id}`}>
                    <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors cursor-pointer">
                      <div className="flex items-center gap-3">
                        <div className="h-10 w-10 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg flex items-center justify-center">
                          <Building2 className="h-5 w-5 text-white" />
                        </div>
                        <div>
                          <p className="font-medium text-gray-900 dark:text-white">{ws.name}</p>
                          <p className="text-sm text-gray-500">
                            {ws.members_count} membre{ws.members_count > 1 ? 's' : ''} • Créé par {ws.owner_name || 'Admin'}
                          </p>
                        </div>
                      </div>
                      <Button variant="ghost" size="sm">
                        Gérer →
                      </Button>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </main>
    </div>
  );
}
