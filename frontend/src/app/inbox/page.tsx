'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import {
  Inbox,
  Plus,
  Search,
  Filter,
  CheckCircle2,
  ArrowRight,
  Loader2,
  Lightbulb,
  Bug,
  FileText,
  HelpCircle,
  Clock,
  Trash2,
  Archive,
  RefreshCw,
  X,
  Send,
  Tag,
  Calendar,
  User,
  Link as LinkIcon,
} from 'lucide-react';
import Link from 'next/link';
import { AppLayoutWithOnboarding, ProtectedRoute } from "@/components/layout";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
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
import { format, formatDistanceToNow } from 'date-fns';
import { fr } from 'date-fns/locale';
import { toast } from 'sonner';

interface InboxItem {
  id: number;
  workspace_id: number;
  created_by: number;
  creator_name?: string;
  text: string;
  link?: string;
  type: string;
  tags: string[];
  status: string;
  due_date?: string;
  mentioned_client?: string;
  mentioned_project?: string;
  triaged_to_type?: string;
  triaged_to_id?: number;
  created_at: string;
  is_overdue: boolean;
  age_hours: number;
}

interface InboxData {
  items: InboxItem[];
  total: number;
  inbox_count: number;
  triaged_count: number;
  done_count: number;
}

const typeIcons: Record<string, any> = {
  idea: Lightbulb,
  request: HelpCircle,
  bug: Bug,
  content: FileText,
  task: CheckCircle2,
  other: Inbox,
};

const typeColors: Record<string, string> = {
  idea: 'text-yellow-500 bg-yellow-50 dark:bg-yellow-900/20',
  request: 'text-blue-500 bg-blue-50 dark:bg-blue-900/20',
  bug: 'text-red-500 bg-red-50 dark:bg-red-900/20',
  content: 'text-purple-500 bg-purple-50 dark:bg-purple-900/20',
  task: 'text-green-500 bg-green-50 dark:bg-green-900/20',
  other: 'text-gray-500 bg-gray-50 dark:bg-gray-900/20',
};

export default function InboxPage() {
  return (
    <ProtectedRoute>
      <AppLayoutWithOnboarding>
        <InboxContent />
      </AppLayoutWithOnboarding>
    </ProtectedRoute>
  );
}

function InboxContent() {
  const [data, setData] = useState<InboxData | null>(null);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>('inbox');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  
  // Quick capture state
  const [captureText, setCaptureText] = useState('');
  const [captureLink, setCaptureLink] = useState('');
  const [isCapturing, setIsCapturing] = useState(false);
  const [showCaptureExpanded, setShowCaptureExpanded] = useState(false);
  const captureInputRef = useRef<HTMLTextAreaElement>(null);
  
  // Triage modal
  const [triageItem, setTriageItem] = useState<InboxItem | null>(null);
  const [triageTarget, setTriageTarget] = useState<string>('task');
  const [isTriaging, setIsTriaging] = useState(false);

  const workspaceId = typeof window !== 'undefined' 
    ? localStorage.getItem('current_workspace_id') || '1' 
    : '1';

  const fetchInbox = useCallback(async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('access_token');
      const params = new URLSearchParams({
        workspace_id: workspaceId,
        limit: '100',
      });
      
      if (statusFilter && statusFilter !== 'all') {
        params.set('status_filter', statusFilter);
      }
      if (typeFilter && typeFilter !== 'all') {
        params.set('type_filter', typeFilter);
      }
      
      const res = await fetch(`/api/v1/inbox?${params}`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      
      if (!res.ok) throw new Error('Failed to fetch inbox');
      const result = await res.json();
      setData(result);
    } catch (err) {
      console.error(err);
      toast.error('Erreur de chargement');
    } finally {
      setLoading(false);
    }
  }, [workspaceId, statusFilter, typeFilter]);

  useEffect(() => {
    fetchInbox();
  }, [fetchInbox]);

  // Quick capture submit
  const handleCapture = async () => {
    if (!captureText.trim()) return;
    
    setIsCapturing(true);
    try {
      const token = localStorage.getItem('access_token');
      const res = await fetch(`/api/v1/inbox?workspace_id=${workspaceId}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text: captureText,
          link: captureLink || undefined,
        }),
      });
      
      if (!res.ok) throw new Error('Failed to create');
      
      setCaptureText('');
      setCaptureLink('');
      setShowCaptureExpanded(false);
      toast.success('Capturé !');
      fetchInbox();
    } catch (err) {
      toast.error('Erreur de capture');
    } finally {
      setIsCapturing(false);
    }
  };

  // Keyboard shortcut for capture
  const handleCaptureKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      handleCapture();
    }
  };

  // Triage submit
  const handleTriage = async () => {
    if (!triageItem) return;
    
    setIsTriaging(true);
    try {
      const token = localStorage.getItem('access_token');
      const res = await fetch(`/api/v1/inbox/${triageItem.id}/triage`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          target: triageTarget,
          task_title: triageItem.text.slice(0, 200),
        }),
      });
      
      if (!res.ok) throw new Error('Failed to triage');
      
      const result = await res.json();
      toast.success(result.message);
      setTriageItem(null);
      fetchInbox();
    } catch (err) {
      toast.error('Erreur de triage');
    } finally {
      setIsTriaging(false);
    }
  };

  // Quick actions
  const handleMarkDone = async (item: InboxItem) => {
    try {
      const token = localStorage.getItem('access_token');
      await fetch(`/api/v1/inbox/${item.id}/done`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
      });
      toast.success('Marqué comme fait');
      fetchInbox();
    } catch (err) {
      toast.error('Erreur');
    }
  };

  const handleArchive = async (item: InboxItem) => {
    try {
      const token = localStorage.getItem('access_token');
      await fetch(`/api/v1/inbox/${item.id}/archive`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
      });
      toast.success('Archivé');
      fetchInbox();
    } catch (err) {
      toast.error('Erreur');
    }
  };

  const handleDelete = async (item: InboxItem) => {
    if (!confirm('Supprimer cet élément ?')) return;
    
    try {
      const token = localStorage.getItem('access_token');
      await fetch(`/api/v1/inbox/${item.id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` },
      });
      toast.success('Supprimé');
      fetchInbox();
    } catch (err) {
      toast.error('Erreur');
    }
  };

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <Inbox className="h-6 w-6" />
            Inbox
          </h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">
            Capture rapide d'idées, demandes et tâches
          </p>
        </div>
        <Button onClick={fetchInbox} variant="ghost" size="sm">
          <RefreshCw className="h-4 w-4" />
        </Button>
      </div>

      {/* Quick Capture */}
      <Card className="border-2 border-dashed border-blue-200 dark:border-blue-800 bg-blue-50/50 dark:bg-blue-950/20">
        <CardContent className="pt-4">
          <div className="space-y-3">
            <Textarea
              ref={captureInputRef}
              placeholder="Capturer une idée... (ex: @client #projet due:2026-02-01 type:idee)"
              value={captureText}
              onChange={(e) => setCaptureText(e.target.value)}
              onKeyDown={handleCaptureKeyDown}
              onFocus={() => setShowCaptureExpanded(true)}
              className="min-h-[60px] resize-none border-0 bg-transparent focus-visible:ring-0 text-lg placeholder:text-gray-400"
            />
            
            {showCaptureExpanded && (
              <div className="flex items-center gap-3 pt-2 border-t border-blue-200 dark:border-blue-800">
                <div className="flex-1 flex items-center gap-2">
                  <LinkIcon className="h-4 w-4 text-gray-400" />
                  <Input
                    placeholder="Lien (optionnel)"
                    value={captureLink}
                    onChange={(e) => setCaptureLink(e.target.value)}
                    className="h-8 text-sm"
                  />
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      setShowCaptureExpanded(false);
                      setCaptureText('');
                      setCaptureLink('');
                    }}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                  <Button
                    size="sm"
                    onClick={handleCapture}
                    disabled={!captureText.trim() || isCapturing}
                  >
                    {isCapturing ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <>
                        <Send className="h-4 w-4 mr-1" />
                        Capturer
                      </>
                    )}
                  </Button>
                </div>
              </div>
            )}
            
            {!showCaptureExpanded && (
              <div className="flex items-center gap-2 text-xs text-gray-400">
                <Tag className="h-3 w-3" /> @client #projet
                <Calendar className="h-3 w-3 ml-2" /> due:YYYY-MM-DD
                <span className="ml-auto">⌘+Enter pour capturer</span>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Filters */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 bg-gray-100 dark:bg-gray-800 rounded-lg p-1">
          {[
            { value: 'inbox', label: 'Inbox', count: data?.inbox_count },
            { value: 'triaged', label: 'Triés', count: data?.triaged_count },
            { value: 'done', label: 'Faits', count: data?.done_count },
            { value: 'all', label: 'Tous' },
          ].map((tab) => (
            <button
              key={tab.value}
              onClick={() => setStatusFilter(tab.value)}
              className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                statusFilter === tab.value
                  ? 'bg-white dark:bg-gray-700 shadow-sm'
                  : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
              }`}
            >
              {tab.label}
              {tab.count !== undefined && (
                <span className="ml-1 text-xs text-gray-400">({tab.count})</span>
              )}
            </button>
          ))}
        </div>
        
        <Select value={typeFilter} onValueChange={setTypeFilter}>
          <SelectTrigger className="w-[140px]">
            <Filter className="h-4 w-4 mr-2" />
            <SelectValue placeholder="Type" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Tous types</SelectItem>
            <SelectItem value="idea">💡 Idée</SelectItem>
            <SelectItem value="request">❓ Demande</SelectItem>
            <SelectItem value="bug">🐛 Bug</SelectItem>
            <SelectItem value="content">📄 Contenu</SelectItem>
            <SelectItem value="task">✅ Tâche</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Items List */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
        </div>
      ) : data?.items.length === 0 ? (
        <Card className="border-dashed">
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Inbox className="h-12 w-12 text-gray-300 dark:text-gray-600 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
              Inbox vide
            </h3>
            <p className="text-gray-500 text-center max-w-md">
              Capturez vos idées, demandes et tâches ici. Utilisez @client #projet pour tagger.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {data?.items.map((item) => {
            const TypeIcon = typeIcons[item.type] || Inbox;
            const typeColor = typeColors[item.type] || typeColors.other;
            
            return (
              <Card key={item.id} className={`group hover:shadow-md transition-shadow ${
                item.status === 'triaged' ? 'opacity-70' : ''
              }`}>
                <CardContent className="p-4">
                  <div className="flex items-start gap-4">
                    {/* Type Icon */}
                    <div className={`p-2 rounded-lg ${typeColor}`}>
                      <TypeIcon className="h-4 w-4" />
                    </div>
                    
                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      <p className="text-gray-900 dark:text-white">
                        {item.text}
                      </p>
                      
                      <div className="flex items-center gap-3 mt-2 text-xs text-gray-500">
                        <span className="flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          {formatDistanceToNow(new Date(item.created_at), { addSuffix: true, locale: fr })}
                        </span>
                        
                        {item.mentioned_client && (
                          <span className="flex items-center gap-1">
                            <User className="h-3 w-3" />
                            @{item.mentioned_client}
                          </span>
                        )}
                        
                        {item.tags && item.tags.length > 0 && (
                          <span className="flex items-center gap-1">
                            <Tag className="h-3 w-3" />
                            {item.tags.map(t => `#${t}`).join(' ')}
                          </span>
                        )}
                        
                        {item.due_date && (
                          <span className={`flex items-center gap-1 ${item.is_overdue ? 'text-red-500' : ''}`}>
                            <Calendar className="h-3 w-3" />
                            {format(new Date(item.due_date), 'd MMM', { locale: fr })}
                          </span>
                        )}
                        
                        {item.link && (
                          <a href={item.link} target="_blank" rel="noopener noreferrer" className="text-blue-500 hover:underline flex items-center gap-1">
                            <LinkIcon className="h-3 w-3" />
                            Lien
                          </a>
                        )}
                      </div>
                      
                      {/* Triaged info */}
                      {item.status === 'triaged' && item.triaged_to_type && (
                        <div className="mt-2">
                          <Badge variant="secondary" className="text-xs">
                            Trié → {item.triaged_to_type}
                          </Badge>
                        </div>
                      )}
                    </div>
                    
                    {/* Actions */}
                    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                      {item.status === 'inbox' && (
                        <>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => setTriageItem(item)}
                            className="h-8 px-2"
                          >
                            <ArrowRight className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleMarkDone(item)}
                            className="h-8 px-2 text-green-600 hover:text-green-700"
                          >
                            <CheckCircle2 className="h-4 w-4" />
                          </Button>
                        </>
                      )}
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleArchive(item)}
                        className="h-8 px-2"
                      >
                        <Archive className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDelete(item)}
                        className="h-8 px-2 text-red-600 hover:text-red-700"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* Triage Modal */}
      <Dialog open={!!triageItem} onOpenChange={(open) => !open && setTriageItem(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Trier vers...</DialogTitle>
            <DialogDescription>
              Convertir cet élément en action concrète
            </DialogDescription>
          </DialogHeader>
          
          {triageItem && (
            <div className="space-y-4 py-4">
              <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg text-sm">
                {triageItem.text}
              </div>
              
              <div className="grid grid-cols-2 gap-3">
                {[
                  { value: 'task', label: '✅ Tâche', desc: 'Action à faire' },
                  { value: 'deal', label: '💰 Deal', desc: 'Opportunité commerciale' },
                  { value: 'project', label: '📁 Projet', desc: 'Nouveau projet' },
                  { value: 'deliverable', label: '📦 Livrable', desc: 'À livrer' },
                ].map((option) => (
                  <button
                    key={option.value}
                    onClick={() => setTriageTarget(option.value)}
                    className={`p-4 rounded-lg border-2 text-left transition-colors ${
                      triageTarget === option.value
                        ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                        : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'
                    }`}
                  >
                    <p className="font-medium">{option.label}</p>
                    <p className="text-xs text-gray-500">{option.desc}</p>
                  </button>
                ))}
              </div>
            </div>
          )}
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setTriageItem(null)}>
              Annuler
            </Button>
            <Button onClick={handleTriage} disabled={isTriaging}>
              {isTriaging ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Trier'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
