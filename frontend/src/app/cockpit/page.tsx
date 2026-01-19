'use client';

import { useState, useEffect } from 'react';
import { 
  CheckCircle2, 
  AlertTriangle, 
  TrendingUp,
  Clock,
  Users,
  FileCheck,
  DollarSign,
  ArrowRight,
  Loader2,
  RefreshCw
} from 'lucide-react';
import Link from 'next/link';
import { AppLayoutWithOnboarding, ProtectedRoute } from "@/components/layout";

interface TodoItem {
  id: number;
  type: string;
  title: string;
  subtitle?: string;
  due_date?: string;
  priority?: string;
  client_name?: string;
  project_name?: string;
  link?: string;
}

interface UrgencyItem {
  id: number;
  type: string;
  title: string;
  subtitle?: string;
  deadline?: string;
  days_remaining?: number;
  client_name?: string;
  project_name?: string;
  severity: string;
}

interface BusinessItem {
  id: number;
  type: string;
  title: string;
  subtitle?: string;
  value?: number;
  client_name?: string;
  status?: string;
  days_waiting?: number;
}

interface DashboardData {
  todos: TodoItem[];
  todos_count: number;
  urgencies: UrgencyItem[];
  urgencies_count: number;
  business: BusinessItem[];
  business_count: number;
  active_projects: number;
  pending_validations: number;
  hot_leads: number;
  monthly_revenue: number;
}

export default function CockpitPage() {
  return (
    <ProtectedRoute>
      <AppLayoutWithOnboarding>
        <CockpitContent />
      </AppLayoutWithOnboarding>
    </ProtectedRoute>
  );
}

function CockpitContent() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);

  const fetchDashboard = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('/api/v1/agency/dashboard', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      
      if (!response.ok) throw new Error('Failed to fetch dashboard');
      
      const result = await response.json();
      setData(result);
      setError(null);
    } catch (err) {
      setError('Erreur de chargement du dashboard');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const generateFollowups = async () => {
    setGenerating(true);
    try {
      const token = localStorage.getItem('access_token');
      await fetch('/api/v1/agency/tasks/generate-followups', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      // Refresh dashboard
      await fetchDashboard();
    } catch (err) {
      console.error('Failed to generate followups:', err);
    } finally {
      setGenerating(false);
    }
  };

  useEffect(() => {
    fetchDashboard();
  }, []);

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: 'EUR',
      minimumFractionDigits: 0,
    }).format(value);
  };

  const getPriorityColor = (priority?: string) => {
    switch (priority) {
      case 'high': return 'text-red-600 bg-red-50';
      case 'medium': return 'text-amber-600 bg-amber-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  const getSeverityColor = (severity: string) => {
    return severity === 'danger' 
      ? 'border-red-500 bg-red-50' 
      : 'border-amber-500 bg-amber-50';
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'followup': return <Clock className="h-4 w-4 text-blue-500" />;
      case 'validation': return <FileCheck className="h-4 w-4 text-purple-500" />;
      case 'task': return <CheckCircle2 className="h-4 w-4 text-green-500" />;
      case 'hot_lead': return <TrendingUp className="h-4 w-4 text-orange-500" />;
      case 'quote_sent': return <DollarSign className="h-4 w-4 text-blue-500" />;
      default: return <Clock className="h-4 w-4 text-gray-500" />;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="h-8 w-8 animate-spin text-purple-600" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600 mb-4">{error}</p>
        <button
          onClick={fetchDashboard}
          className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
        >
          Réessayer
        </button>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Cockpit</h1>
          <p className="text-gray-600">Vue d'ensemble de votre activité</p>
        </div>
        <button
          onClick={generateFollowups}
          disabled={generating}
          className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50"
        >
          {generating ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <RefreshCw className="h-4 w-4" />
          )}
          Générer les relances
        </button>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-50 rounded-lg">
              <Users className="h-5 w-5 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Projets actifs</p>
              <p className="text-2xl font-bold">{data?.active_projects || 0}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-purple-50 rounded-lg">
              <FileCheck className="h-5 w-5 text-purple-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Validations</p>
              <p className="text-2xl font-bold">{data?.pending_validations || 0}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-orange-50 rounded-lg">
              <TrendingUp className="h-5 w-5 text-orange-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Leads chauds</p>
              <p className="text-2xl font-bold">{data?.hot_leads || 0}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-green-50 rounded-lg">
              <DollarSign className="h-5 w-5 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">CA du mois</p>
              <p className="text-2xl font-bold">{formatCurrency(data?.monthly_revenue || 0)}</p>
            </div>
          </div>
        </div>
      </div>

      {/* 3 Blocks Layout */}
      <div className="grid grid-cols-3 gap-6">
        {/* Block A: À faire aujourd'hui */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100">
          <div className="p-4 border-b border-gray-100">
            <div className="flex items-center justify-between">
              <h2 className="font-semibold text-gray-900 flex items-center gap-2">
                <CheckCircle2 className="h-5 w-5 text-green-500" />
                À faire aujourd'hui
              </h2>
              <span className="text-sm text-gray-500">{data?.todos_count || 0} items</span>
            </div>
          </div>
          <div className="divide-y divide-gray-50 max-h-96 overflow-y-auto">
            {data?.todos.length === 0 ? (
              <div className="p-6 text-center text-gray-500">
                <CheckCircle2 className="h-8 w-8 mx-auto mb-2 text-green-300" />
                <p>Rien à faire ! 🎉</p>
              </div>
            ) : (
              data?.todos.map((item) => (
                <div
                  key={`todo-${item.id}-${item.type}`}
                  className="p-4 hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-start gap-3">
                    {getTypeIcon(item.type)}
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-gray-900 truncate">{item.title}</p>
                      {item.subtitle && (
                        <p className="text-sm text-gray-500 truncate">{item.subtitle}</p>
                      )}
                      {item.client_name && (
                        <p className="text-xs text-gray-400 mt-1">{item.client_name}</p>
                      )}
                    </div>
                    {item.priority && (
                      <span className={`text-xs px-2 py-1 rounded-full ${getPriorityColor(item.priority)}`}>
                        {item.priority}
                      </span>
                    )}
                  </div>
                  {item.link && (
                    <Link
                      href={item.link}
                      className="mt-2 flex items-center text-sm text-purple-600 hover:text-purple-700"
                    >
                      Voir <ArrowRight className="h-3 w-3 ml-1" />
                    </Link>
                  )}
                </div>
              ))
            )}
          </div>
        </div>

        {/* Block B: Urgences */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100">
          <div className="p-4 border-b border-gray-100">
            <div className="flex items-center justify-between">
              <h2 className="font-semibold text-gray-900 flex items-center gap-2">
                <AlertTriangle className="h-5 w-5 text-amber-500" />
                Urgences
              </h2>
              <span className="text-sm text-gray-500">{data?.urgencies_count || 0} items</span>
            </div>
          </div>
          <div className="divide-y divide-gray-50 max-h-96 overflow-y-auto">
            {data?.urgencies.length === 0 ? (
              <div className="p-6 text-center text-gray-500">
                <CheckCircle2 className="h-8 w-8 mx-auto mb-2 text-green-300" />
                <p>Aucune urgence</p>
              </div>
            ) : (
              data?.urgencies.map((item) => (
                <div
                  key={`urgency-${item.id}-${item.type}`}
                  className={`p-4 border-l-4 ${getSeverityColor(item.severity)}`}
                >
                  <div className="flex items-start gap-3">
                    <AlertTriangle className={`h-4 w-4 ${
                      item.severity === 'danger' ? 'text-red-500' : 'text-amber-500'
                    }`} />
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-gray-900 truncate">{item.title}</p>
                      {item.subtitle && (
                        <p className="text-sm text-gray-500 truncate">{item.subtitle}</p>
                      )}
                      {item.client_name && (
                        <p className="text-xs text-gray-400 mt-1">{item.client_name}</p>
                      )}
                    </div>
                    {item.days_remaining !== undefined && item.days_remaining !== null && (
                      <span className={`text-xs font-medium px-2 py-1 rounded-full ${
                        item.days_remaining <= 1 ? 'bg-red-100 text-red-700' : 'bg-amber-100 text-amber-700'
                      }`}>
                        {item.days_remaining}j
                      </span>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Block C: Business */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100">
          <div className="p-4 border-b border-gray-100">
            <div className="flex items-center justify-between">
              <h2 className="font-semibold text-gray-900 flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-blue-500" />
                Business
              </h2>
              <span className="text-sm text-gray-500">{data?.business_count || 0} items</span>
            </div>
          </div>
          <div className="divide-y divide-gray-50 max-h-96 overflow-y-auto">
            {data?.business.length === 0 ? (
              <div className="p-6 text-center text-gray-500">
                <TrendingUp className="h-8 w-8 mx-auto mb-2 text-gray-300" />
                <p>Aucun lead en cours</p>
              </div>
            ) : (
              data?.business.map((item) => (
                <Link
                  key={`business-${item.id}-${item.type}`}
                  href="/pipeline"
                  className="block p-4 hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-start gap-3">
                    {getTypeIcon(item.type)}
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-gray-900 truncate">{item.title}</p>
                      {item.subtitle && (
                        <p className="text-sm text-gray-500 truncate">{item.subtitle}</p>
                      )}
                      {item.client_name && (
                        <p className="text-xs text-gray-400 mt-1">{item.client_name}</p>
                      )}
                    </div>
                    {item.value && (
                      <span className="text-sm font-semibold text-green-600">
                        {formatCurrency(item.value)}
                      </span>
                    )}
                  </div>
                </Link>
              ))
            )}
          </div>
          <div className="p-4 border-t border-gray-100">
            <Link
              href="/pipeline"
              className="text-sm text-purple-600 hover:text-purple-700 flex items-center justify-center gap-1"
            >
              Voir le pipeline complet <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
