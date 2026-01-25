'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { 
  Receipt, ArrowLeft, Edit2, Trash2, Plus, Save, Send, Check, X,
  Building2, User, Calendar, Clock, FileText, ArrowRight, Printer, Download, Eye, Pencil, Cloud, ExternalLink
} from 'lucide-react';
import { AppLayoutWithOnboarding, ProtectedRoute } from "@/components/layout";
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
  TableFooter,
} from '@/components/ui/table';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Separator } from '@/components/ui/separator';
import { toast } from 'sonner';

interface QuoteItem {
  id: number;
  position: number;
  description: string;
  quantity: number;
  unit: string;
  unit_price: number;
  line_total: number;
}

interface Client {
  id: number;
  name: string;
  email?: string;
  phone?: string;
  company_name?: string;
  address_line1?: string;
  city?: string;
  postal_code?: string;
}

interface Quote {
  id: number;
  reference: string;
  title: string;
  description?: string;
  status: 'DRAFT' | 'SENT' | 'ACCEPTED' | 'REJECTED' | 'EXPIRED' | 'INVOICED';
  issue_date: string;
  validity_date?: string;
  client_id?: number;
  client?: Client;
  subtotal: number;
  tax_rate: number;
  tax_amount: number;
  discount_percent: number;
  discount_amount: number;
  total: number;
  terms?: string;
  notes?: string;
  items: QuoteItem[];
  invoice_id?: number;
  created_at: string;
}

const STATUS_CONFIG = {
  DRAFT: { label: 'Brouillon', color: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200' },
  SENT: { label: 'Envoyé', color: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200' },
  ACCEPTED: { label: 'Accepté', color: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' },
  REJECTED: { label: 'Refusé', color: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200' },
  EXPIRED: { label: 'Expiré', color: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200' },
  INVOICED: { label: 'Facturé', color: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200' },
};

export default function QuoteDetailPage() {
  const router = useRouter();
  const params = useParams();
  const quoteId = params.id as string;
  
  const [quote, setQuote] = useState<Quote | null>(null);
  const [clients, setClients] = useState<Client[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [editing, setEditing] = useState(false);
  const [showAddItemDialog, setShowAddItemDialog] = useState(false);
  const [showConvertDialog, setShowConvertDialog] = useState(false);
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  const [generatingPdf, setGeneratingPdf] = useState(false);
  const [savingToDrive, setSavingToDrive] = useState(false);
  const [driveLink, setDriveLink] = useState<string | null>(null);
  const [editingItemId, setEditingItemId] = useState<number | null>(null);
  const [showEditItemDialog, setShowEditItemDialog] = useState(false);
  const [editItem, setEditItem] = useState({
    description: '',
    quantity: '1',
    unit: 'unité',
    unit_price: '',
  });
  
  // Edit form
  const [editForm, setEditForm] = useState({
    title: '',
    description: '',
    client_id: '',
    validity_date: '',
    tax_rate: '20',
    discount_percent: '0',
    terms: '',
    notes: '',
  });

  // New item form
  const [newItem, setNewItem] = useState({
    description: '',
    quantity: '1',
    unit: 'unité',
    unit_price: '',
  });

  // Convert form
  const [convertForm, setConvertForm] = useState({
    due_days: 30,
    notes: '',
  });

  const fetchQuote = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const res = await fetch(`/api/v1/billing/quotes/${quoteId}`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setQuote(data);
        setEditForm({
          title: data.title || '',
          description: data.description || '',
          client_id: data.client_id ? String(data.client_id) : '',
          validity_date: data.validity_date || '',
          tax_rate: String(data.tax_rate || 20),
          discount_percent: String(data.discount_percent || 0),
          terms: data.terms || '',
          notes: data.notes || '',
        });
      } else {
        toast.error('Devis non trouvé');
        router.push('/devis');
      }
    } catch (err) {
      console.error('Failed to fetch quote', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchClients = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const res = await fetch('/api/v1/billing/clients', {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setClients(data);
      }
    } catch (err) {
      console.error('Failed to fetch clients', err);
    }
  };

  useEffect(() => {
    fetchQuote();
    fetchClients();
  }, [quoteId]);

  const saveQuote = async () => {
    setSaving(true);
    try {
      const token = localStorage.getItem('access_token');
      const res = await fetch(`/api/v1/billing/quotes/${quoteId}`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          title: editForm.title,
          description: editForm.description || null,
          client_id: editForm.client_id ? parseInt(editForm.client_id) : null,
          validity_date: editForm.validity_date || null,
          tax_rate: parseFloat(editForm.tax_rate),
          discount_percent: parseFloat(editForm.discount_percent),
          terms: editForm.terms || null,
          notes: editForm.notes || null,
        }),
      });
      
      if (res.ok) {
        toast.success('Devis mis à jour');
        setEditing(false);
        // Reset PDF car les données ont changé
        if (pdfUrl) {
          window.URL.revokeObjectURL(pdfUrl);
          setPdfUrl(null);
        }
        setDriveLink(null);
        fetchQuote();
      } else {
        const error = await res.json();
        toast.error(error.detail || 'Erreur');
      }
    } catch (err) {
      toast.error('Erreur de connexion');
    } finally {
      setSaving(false);
    }
  };

  const addItem = async () => {
    if (!newItem.description || !newItem.unit_price) {
      toast.error('Description et prix requis');
      return;
    }
    
    try {
      const token = localStorage.getItem('access_token');
      const res = await fetch(`/api/v1/billing/quotes/${quoteId}/items`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          description: newItem.description,
          quantity: parseFloat(newItem.quantity),
          unit: newItem.unit,
          unit_price: parseFloat(newItem.unit_price),
          position: quote?.items.length || 0,
        }),
      });
      
      if (res.ok) {
        toast.success('Ligne ajoutée');
        setShowAddItemDialog(false);
        setNewItem({ description: '', quantity: '1', unit: 'unité', unit_price: '' });
        // Reset PDF car les données ont changé
        if (pdfUrl) {
          window.URL.revokeObjectURL(pdfUrl);
          setPdfUrl(null);
        }
        setDriveLink(null);
        fetchQuote();
      } else {
        const error = await res.json();
        toast.error(error.detail || 'Erreur');
      }
    } catch (err) {
      toast.error('Erreur de connexion');
    }
  };

  const deleteItem = async (itemId: number) => {
    try {
      const token = localStorage.getItem('access_token');
      const res = await fetch(`/api/v1/billing/quotes/${quoteId}/items/${itemId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` },
      });
      
      if (res.ok) {
        toast.success('Ligne supprimée');
        // Reset PDF car les données ont changé
        if (pdfUrl) {
          window.URL.revokeObjectURL(pdfUrl);
          setPdfUrl(null);
        }
        setDriveLink(null);
        fetchQuote();
      } else {
        const error = await res.json();
        toast.error(error.detail || 'Erreur');
      }
    } catch (err) {
      toast.error('Erreur de connexion');
    }
  };

  const openEditItemDialog = (item: QuoteItem) => {
    setEditingItemId(item.id);
    setEditItem({
      description: item.description,
      quantity: String(item.quantity),
      unit: item.unit,
      unit_price: String(item.unit_price),
    });
    setShowEditItemDialog(true);
  };

  const updateItem = async () => {
    if (!editingItemId || !editItem.description || !editItem.unit_price) {
      toast.error('Description et prix requis');
      return;
    }
    
    try {
      const token = localStorage.getItem('access_token');
      const res = await fetch(`/api/v1/billing/quotes/${quoteId}/items/${editingItemId}`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          description: editItem.description,
          quantity: parseFloat(editItem.quantity),
          unit: editItem.unit,
          unit_price: parseFloat(editItem.unit_price),
        }),
      });
      
      if (res.ok) {
        toast.success('Ligne mise à jour');
        setShowEditItemDialog(false);
        setEditingItemId(null);
        // Reset PDF car les données ont changé
        if (pdfUrl) {
          window.URL.revokeObjectURL(pdfUrl);
          setPdfUrl(null);
        }
        setDriveLink(null);
        fetchQuote();
      } else {
        const error = await res.json();
        toast.error(error.detail || 'Erreur');
      }
    } catch (err) {
      toast.error('Erreur de connexion');
    }
  };

  const updateStatus = async (status: string) => {
    try {
      const token = localStorage.getItem('access_token');
      const res = await fetch(`/api/v1/billing/quotes/${quoteId}`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ status }),
      });
      
      if (res.ok) {
        toast.success('Statut mis à jour');
        // Reset PDF car les données ont changé
        if (pdfUrl) {
          window.URL.revokeObjectURL(pdfUrl);
          setPdfUrl(null);
        }
        setDriveLink(null);
        fetchQuote();
      } else {
        const error = await res.json();
        toast.error(error.detail || 'Erreur');
      }
    } catch (err) {
      toast.error('Erreur de connexion');
    }
  };

  const convertToInvoice = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const dueDate = new Date();
      dueDate.setDate(dueDate.getDate() + convertForm.due_days);
      
      const res = await fetch(`/api/v1/billing/quotes/${quoteId}/convert`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          due_date: dueDate.toISOString().split('T')[0],
          notes: convertForm.notes || null,
        }),
      });
      
      if (res.ok) {
        const invoice = await res.json();
        toast.success('Devis converti en facture');
        router.push(`/factures/${invoice.id}`);
      } else {
        const error = await res.json();
        toast.error(error.detail || 'Erreur');
      }
    } catch (err) {
      toast.error('Erreur de connexion');
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(amount);
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('fr-FR');
  };

  const generatePdf = async () => {
    setGeneratingPdf(true);
    try {
      const token = localStorage.getItem('access_token');
      const res = await fetch(`/api/v1/billing/quotes/${quoteId}/pdf`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      
      if (res.ok) {
        const blob = await res.blob();
        // Revoke old URL if exists
        if (pdfUrl) {
          window.URL.revokeObjectURL(pdfUrl);
        }
        const url = window.URL.createObjectURL(blob);
        setPdfUrl(url);
        toast.success('PDF généré avec succès');
      } else {
        const error = await res.json();
        toast.error(error.detail || 'Erreur de génération du PDF');
      }
    } catch (err) {
      toast.error('Erreur de connexion');
    } finally {
      setGeneratingPdf(false);
    }
  };

  const viewPdf = () => {
    if (pdfUrl) {
      window.open(pdfUrl, '_blank');
    }
  };

  const downloadPdf = () => {
    if (pdfUrl) {
      const a = document.createElement('a');
      a.href = pdfUrl;
      a.download = `${quote?.reference || 'devis'}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    }
  };

  const saveToDrive = async () => {
    setSavingToDrive(true);
    try {
      const token = localStorage.getItem('access_token');
      const res = await fetch(`/api/v1/billing/quotes/${quoteId}/pdf/drive`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
      });
      
      if (res.ok) {
        const data = await res.json();
        setDriveLink(data.web_view_link);
        // Reset local PDF since it's now on Drive
        if (pdfUrl) {
          window.URL.revokeObjectURL(pdfUrl);
          setPdfUrl(null);
        }
        toast.success('PDF sauvegardé sur Google Drive');
      } else {
        const error = await res.json();
        toast.error(error.detail || 'Erreur de sauvegarde sur Drive');
      }
    } catch (err) {
      toast.error('Erreur de connexion');
    } finally {
      setSavingToDrive(false);
    }
  };

  const openDriveLink = () => {
    if (driveLink) {
      window.open(driveLink, '_blank');
    }
  };

  if (loading) {
    return (
      <ProtectedRoute>
        <AppLayoutWithOnboarding>
          <div className="p-6 flex items-center justify-center">
            <div className="text-gray-500">Chargement...</div>
          </div>
        </AppLayoutWithOnboarding>
      </ProtectedRoute>
    );
  }

  if (!quote) {
    return null;
  }

  const isEditable = quote.status === 'DRAFT' || quote.status === 'SENT';

  return (
    <ProtectedRoute>
      <AppLayoutWithOnboarding>
        <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" onClick={() => router.push('/devis')}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Retour
          </Button>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                {quote.reference}
              </h1>
              <Badge className={STATUS_CONFIG[quote.status].color}>
                {STATUS_CONFIG[quote.status].label}
              </Badge>
            </div>
            <p className="text-gray-500 dark:text-gray-400">{quote.title}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {quote.status === 'DRAFT' && (
            <Button variant="outline" onClick={() => updateStatus('SENT')}>
              <Send className="h-4 w-4 mr-2" />
              Marquer envoyé
            </Button>
          )}
          {quote.status === 'SENT' && (
            <>
              <Button variant="outline" onClick={() => updateStatus('ACCEPTED')} className="text-green-600">
                <Check className="h-4 w-4 mr-2" />
                Accepté
              </Button>
              <Button variant="outline" onClick={() => updateStatus('REJECTED')} className="text-red-600">
                <X className="h-4 w-4 mr-2" />
                Refusé
              </Button>
            </>
          )}
          {!pdfUrl ? (
            <Button variant="outline" onClick={generatePdf} disabled={generatingPdf}>
              <FileText className="h-4 w-4 mr-2" />
              {generatingPdf ? 'Génération...' : 'Générer PDF'}
            </Button>
          ) : (
            <>
              <Button variant="outline" onClick={viewPdf}>
                <Eye className="h-4 w-4 mr-2" />
                Voir PDF
              </Button>
              <Button variant="outline" onClick={downloadPdf}>
                <Download className="h-4 w-4 mr-2" />
                Télécharger
              </Button>
              <Button variant="outline" onClick={saveToDrive} disabled={savingToDrive}>
                <Cloud className="h-4 w-4 mr-2" />
                {savingToDrive ? 'Sauvegarde...' : 'Sauver sur Drive'}
              </Button>
            </>
          )}
          {driveLink && (
            <Button variant="outline" onClick={openDriveLink}>
              <ExternalLink className="h-4 w-4 mr-2" />
              Voir sur Drive
            </Button>
          )}
          {quote.status === 'ACCEPTED' && (
            <Button onClick={() => setShowConvertDialog(true)} className="bg-purple-600 hover:bg-purple-700">
              <ArrowRight className="h-4 w-4 mr-2" />
              Convertir en facture
            </Button>
          )}
          {isEditable && (
            <Button variant="outline" onClick={() => setEditing(!editing)}>
              <Edit2 className="h-4 w-4 mr-2" />
              {editing ? 'Annuler' : 'Modifier'}
            </Button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Quote Info */}
          {editing ? (
            <Card>
              <CardHeader>
                <CardTitle>Informations du devis</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Titre</Label>
                    <Input
                      value={editForm.title}
                      onChange={(e) => setEditForm({ ...editForm, title: e.target.value })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Client</Label>
                    <Select 
                      value={editForm.client_id} 
                      onValueChange={(v) => setEditForm({ ...editForm, client_id: v })}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Sélectionner" />
                      </SelectTrigger>
                      <SelectContent>
                        {clients.map((client) => (
                          <SelectItem key={client.id} value={client.id.toString()}>
                            {client.company_name || client.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Description</Label>
                  <Textarea
                    value={editForm.description}
                    onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
                  />
                </div>
                <div className="grid grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <Label>Date validité</Label>
                    <Input
                      type="date"
                      value={editForm.validity_date}
                      onChange={(e) => setEditForm({ ...editForm, validity_date: e.target.value })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>TVA (%)</Label>
                    <Input
                      type="number"
                      step="0.01"
                      value={editForm.tax_rate}
                      onChange={(e) => setEditForm({ ...editForm, tax_rate: e.target.value })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Remise (%)</Label>
                    <Input
                      type="number"
                      step="0.01"
                      value={editForm.discount_percent}
                      onChange={(e) => setEditForm({ ...editForm, discount_percent: e.target.value })}
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Conditions</Label>
                  <Textarea
                    value={editForm.terms}
                    onChange={(e) => setEditForm({ ...editForm, terms: e.target.value })}
                    placeholder="Conditions de paiement, délais..."
                  />
                </div>
                <div className="space-y-2">
                  <Label>Notes internes</Label>
                  <Textarea
                    value={editForm.notes}
                    onChange={(e) => setEditForm({ ...editForm, notes: e.target.value })}
                    placeholder="Notes (non visibles par le client)"
                  />
                </div>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>{quote.title}</CardTitle>
                  <div className="text-sm text-gray-500">
                    <Calendar className="h-4 w-4 inline mr-1" />
                    {formatDate(quote.issue_date)}
                    {quote.validity_date && (
                      <span className="ml-4">
                        <Clock className="h-4 w-4 inline mr-1" />
                        Valide jusqu'au {formatDate(quote.validity_date)}
                      </span>
                    )}
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                {quote.description && (
                  <p className="text-gray-600 dark:text-gray-300 mb-4">{quote.description}</p>
                )}
                {quote.terms && (
                  <div className="mt-4 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                    <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Conditions:</p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">{quote.terms}</p>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Items Table */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Lignes du devis</CardTitle>
                {editing && (
                  <Button 
                    size="sm" 
                    onClick={() => setShowAddItemDialog(true)}
                    className="bg-emerald-500 hover:bg-emerald-600"
                  >
                    <Plus className="h-4 w-4 mr-2" />
                    Ajouter une ligne
                  </Button>
                )}
              </div>
            </CardHeader>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[50%]">Description</TableHead>
                    <TableHead className="text-right">Qté</TableHead>
                    <TableHead>Unité</TableHead>
                    <TableHead className="text-right">Prix unit.</TableHead>
                    <TableHead className="text-right">Total</TableHead>
                    {isEditable && <TableHead className="w-[100px]"></TableHead>}
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {quote.items.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={isEditable ? 6 : 5} className="text-center py-8 text-gray-500">
                        Aucune ligne. Ajoutez des prestations au devis.
                      </TableCell>
                    </TableRow>
                  ) : (
                    quote.items.map((item) => (
                      <TableRow key={item.id}>
                        <TableCell>{item.description}</TableCell>
                        <TableCell className="text-right">{item.quantity}</TableCell>
                        <TableCell>{item.unit}</TableCell>
                        <TableCell className="text-right">{formatCurrency(Number(item.unit_price))}</TableCell>
                        <TableCell className="text-right font-medium">{formatCurrency(Number(item.line_total))}</TableCell>
                        {isEditable && (
                          <TableCell>
                            <div className="flex gap-1">
                              <Button 
                                variant="ghost" 
                                size="icon"
                                onClick={() => openEditItemDialog(item)}
                                className="text-blue-600 hover:text-blue-700"
                              >
                                <Pencil className="h-4 w-4" />
                              </Button>
                              <Button 
                                variant="ghost" 
                                size="icon"
                                onClick={() => deleteItem(item.id)}
                                className="text-red-600 hover:text-red-700"
                              >
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            </div>
                          </TableCell>
                        )}
                      </TableRow>
                    ))
                  )}
                </TableBody>
                {quote.items.length > 0 && (
                  <TableFooter>
                    <TableRow>
                      <TableCell colSpan={isEditable ? 4 : 3} className="text-right font-medium">
                        Sous-total HT
                      </TableCell>
                      <TableCell className="text-right font-medium">
                        {formatCurrency(Number(quote.subtotal))}
                      </TableCell>
                      {isEditable && <TableCell />}
                    </TableRow>
                    {Number(quote.discount_amount) > 0 && (
                      <TableRow>
                        <TableCell colSpan={isEditable ? 4 : 3} className="text-right text-red-600">
                          Remise ({quote.discount_percent}%)
                        </TableCell>
                        <TableCell className="text-right text-red-600">
                          -{formatCurrency(Number(quote.discount_amount))}
                        </TableCell>
                        {isEditable && <TableCell />}
                      </TableRow>
                    )}
                    <TableRow>
                      <TableCell colSpan={isEditable ? 4 : 3} className="text-right">
                        TVA ({quote.tax_rate}%)
                      </TableCell>
                      <TableCell className="text-right">
                        {formatCurrency(Number(quote.tax_amount))}
                      </TableCell>
                      {isEditable && <TableCell />}
                    </TableRow>
                    <TableRow className="bg-gray-50 dark:bg-gray-800">
                      <TableCell colSpan={isEditable ? 4 : 3} className="text-right font-bold text-lg">
                        Total TTC
                      </TableCell>
                      <TableCell className="text-right font-bold text-lg">
                        {formatCurrency(Number(quote.total))}
                      </TableCell>
                      {isEditable && <TableCell />}
                    </TableRow>
                  </TableFooter>
                )}
              </Table>
            </CardContent>
          </Card>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Client Card */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <User className="h-5 w-5" />
                Client
              </CardTitle>
            </CardHeader>
            <CardContent>
              {(() => {
                // En mode édition, utiliser le client de editForm, sinon celui du quote
                const selectedClientId = editing ? editForm.client_id : quote.client_id?.toString();
                const displayClient = selectedClientId 
                  ? clients.find(c => c.id.toString() === selectedClientId) || quote.client
                  : quote.client;
                
                if (displayClient) {
                  return (
                    <div className="space-y-2">
                      <p className="font-medium">{displayClient.company_name || displayClient.name}</p>
                      {displayClient.company_name && (
                        <p className="text-sm text-gray-500">{displayClient.name}</p>
                      )}
                      {displayClient.email && (
                        <p className="text-sm text-gray-600 dark:text-gray-400">{displayClient.email}</p>
                      )}
                      {displayClient.phone && (
                        <p className="text-sm text-gray-600 dark:text-gray-400">{displayClient.phone}</p>
                      )}
                      {displayClient.address_line1 && (
                        <div className="text-sm text-gray-600 dark:text-gray-400 pt-2 border-t">
                          <p>{displayClient.address_line1}</p>
                          <p>{displayClient.postal_code} {displayClient.city}</p>
                        </div>
                      )}
                    </div>
                  );
                }
                return <p className="text-gray-500">Aucun client sélectionné</p>;
              })()}
            </CardContent>
          </Card>

          {/* Summary Card */}
          <Card>
            <CardHeader>
              <CardTitle>Résumé</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-500">Sous-total HT</span>
                <span>{formatCurrency(Number(quote.subtotal))}</span>
              </div>
              {Number(quote.discount_amount) > 0 && (
                <div className="flex justify-between text-red-600">
                  <span>Remise ({quote.discount_percent}%)</span>
                  <span>-{formatCurrency(Number(quote.discount_amount))}</span>
                </div>
              )}
              <div className="flex justify-between">
                <span className="text-gray-500">TVA ({quote.tax_rate}%)</span>
                <span>{formatCurrency(Number(quote.tax_amount))}</span>
              </div>
              <Separator />
              <div className="flex justify-between text-lg font-bold">
                <span>Total TTC</span>
                <span>{formatCurrency(Number(quote.total))}</span>
              </div>
            </CardContent>
          </Card>

          {/* Invoice Link */}
          {quote.invoice_id && (
            <Card className="border-purple-200 bg-purple-50 dark:bg-purple-950">
              <CardContent className="p-4">
                <div className="flex items-center gap-2 text-purple-700 dark:text-purple-300">
                  <FileText className="h-5 w-5" />
                  <span>Ce devis a été converti en facture</span>
                </div>
                <Button 
                  variant="link" 
                  className="text-purple-700 p-0 mt-2"
                  onClick={() => router.push(`/factures/${quote.invoice_id}`)}
                >
                  Voir la facture →
                </Button>
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      {/* Add Item Dialog */}
      <Dialog open={showAddItemDialog} onOpenChange={setShowAddItemDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Ajouter une ligne</DialogTitle>
            <DialogDescription>
              Ajoutez une prestation ou un produit au devis
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Description *</Label>
              <Textarea
                placeholder="Description de la prestation..."
                value={newItem.description}
                onChange={(e) => setNewItem({ ...newItem, description: e.target.value })}
              />
            </div>
            <div className="grid grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label>Quantité</Label>
                <Input
                  type="number"
                  step="0.01"
                  value={newItem.quantity}
                  onChange={(e) => setNewItem({ ...newItem, quantity: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label>Unité</Label>
                <Select 
                  value={newItem.unit} 
                  onValueChange={(v) => setNewItem({ ...newItem, unit: v })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="unité">Unité</SelectItem>
                    <SelectItem value="heure">Heure</SelectItem>
                    <SelectItem value="jour">Jour</SelectItem>
                    <SelectItem value="forfait">Forfait</SelectItem>
                    <SelectItem value="mois">Mois</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Prix unitaire HT *</Label>
                <Input
                  type="number"
                  step="0.01"
                  placeholder="0.00"
                  value={newItem.unit_price}
                  onChange={(e) => setNewItem({ ...newItem, unit_price: e.target.value })}
                />
              </div>
            </div>
            {newItem.quantity && newItem.unit_price && (
              <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <div className="flex justify-between text-sm">
                  <span>Total ligne HT</span>
                  <span className="font-medium">
                    {formatCurrency(parseFloat(newItem.quantity) * parseFloat(newItem.unit_price))}
                  </span>
                </div>
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowAddItemDialog(false)}>
              Annuler
            </Button>
            <Button onClick={addItem}>
              <Plus className="h-4 w-4 mr-2" />
              Ajouter
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Convert to Invoice Dialog */}
      <Dialog open={showConvertDialog} onOpenChange={setShowConvertDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Convertir en facture</DialogTitle>
            <DialogDescription>
              Ce devis sera marqué comme facturé et une nouvelle facture sera créée
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Échéance de paiement (jours)</Label>
              <Input
                type="number"
                min={1}
                value={convertForm.due_days}
                onChange={(e) => setConvertForm({ ...convertForm, due_days: parseInt(e.target.value) || 30 })}
              />
            </div>
            <div className="space-y-2">
              <Label>Notes additionnelles</Label>
              <Textarea
                placeholder="Notes pour la facture..."
                value={convertForm.notes}
                onChange={(e) => setConvertForm({ ...convertForm, notes: e.target.value })}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowConvertDialog(false)}>
              Annuler
            </Button>
            <Button onClick={convertToInvoice} className="bg-purple-600 hover:bg-purple-700">
              <ArrowRight className="h-4 w-4 mr-2" />
              Créer la facture
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Item Dialog */}
      <Dialog open={showEditItemDialog} onOpenChange={setShowEditItemDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Modifier la ligne</DialogTitle>
            <DialogDescription>
              Modifiez les détails de cette ligne du devis
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Description</Label>
              <Input
                placeholder="Description de la prestation"
                value={editItem.description}
                onChange={(e) => setEditItem({ ...editItem, description: e.target.value })}
              />
            </div>
            <div className="grid grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label>Quantité</Label>
                <Input
                  type="number"
                  min={0.01}
                  step={0.01}
                  value={editItem.quantity}
                  onChange={(e) => setEditItem({ ...editItem, quantity: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label>Unité</Label>
                <Select value={editItem.unit} onValueChange={(v) => setEditItem({ ...editItem, unit: v })}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="unité">unité</SelectItem>
                    <SelectItem value="heure">heure</SelectItem>
                    <SelectItem value="jour">jour</SelectItem>
                    <SelectItem value="mois">mois</SelectItem>
                    <SelectItem value="forfait">forfait</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Prix unitaire HT (€)</Label>
                <Input
                  type="number"
                  min={0}
                  step={0.01}
                  value={editItem.unit_price}
                  onChange={(e) => setEditItem({ ...editItem, unit_price: e.target.value })}
                />
              </div>
            </div>
            {editItem.quantity && editItem.unit_price && (
              <div className="text-right text-sm text-gray-500">
                Total ligne: {formatCurrency(parseFloat(editItem.quantity) * parseFloat(editItem.unit_price))}
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowEditItemDialog(false)}>
              Annuler
            </Button>
            <Button onClick={updateItem}>
              <Save className="h-4 w-4 mr-2" />
              Enregistrer
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Barre de confirmation fixe en bas - apparaît uniquement si modifications détectées */}
      {(() => {
        // Détecter si des modifications ont été faites
        const hasChanges = editing && quote && (
          editForm.title !== (quote.title || '') ||
          editForm.description !== (quote.description || '') ||
          editForm.client_id !== (quote.client_id ? String(quote.client_id) : '') ||
          editForm.validity_date !== (quote.validity_date || '') ||
          editForm.tax_rate !== String(quote.tax_rate || 20) ||
          editForm.discount_percent !== String(quote.discount_percent || 0) ||
          editForm.terms !== (quote.terms || '') ||
          editForm.notes !== (quote.notes || '')
        );
        
        return (
          <div 
            className={`fixed bottom-6 left-1/2 transform -translate-x-1/2 z-50 transition-all duration-300 ease-out ${
              hasChanges 
                ? 'opacity-100 translate-y-0' 
                : 'opacity-0 translate-y-8 pointer-events-none'
            }`}
          >
            <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl border border-gray-200 dark:border-gray-700 p-3 flex items-center gap-3 animate-in fade-in slide-in-from-bottom-4 duration-300">
              <Button
                variant="outline"
                onClick={() => setEditing(false)}
                className="h-12 px-6 rounded-xl border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 font-medium"
              >
                <X className="h-5 w-5 mr-2" />
                Annuler
              </Button>
              <Button
                onClick={saveQuote}
                disabled={saving}
                className="h-12 px-6 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-white font-medium shadow-lg shadow-emerald-500/30 transition-all duration-200 hover:scale-105"
              >
                <Save className="h-5 w-5 mr-2" />
                {saving ? 'Enregistrement...' : 'Enregistrer'}
              </Button>
            </div>
          </div>
        );
      })()}
        </div>
      </AppLayoutWithOnboarding>
    </ProtectedRoute>
  );
}
