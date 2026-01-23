'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { 
  FileCheck, ArrowLeft, Edit2, Trash2, Plus, Save, Send, Check, 
  Building2, User, Calendar, Clock, CreditCard, AlertTriangle, DollarSign
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
import { Progress } from '@/components/ui/progress';
import { toast } from 'sonner';

interface InvoiceItem {
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

interface Invoice {
  id: number;
  reference: string;
  title: string;
  description?: string;
  status: 'DRAFT' | 'SENT' | 'PAID' | 'PARTIAL' | 'OVERDUE' | 'CANCELLED';
  issue_date: string;
  due_date?: string;
  paid_date?: string;
  client_id?: number;
  client?: Client;
  subtotal: number;
  tax_rate: number;
  tax_amount: number;
  discount_percent: number;
  discount_amount: number;
  total: number;
  amount_paid: number;
  payment_method?: string;
  terms?: string;
  notes?: string;
  items: InvoiceItem[];
  source_quote_id?: number;
  created_at: string;
}

const STATUS_CONFIG = {
  DRAFT: { label: 'Brouillon', color: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200' },
  SENT: { label: 'Envoyée', color: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200' },
  PAID: { label: 'Payée', color: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' },
  PARTIAL: { label: 'Partielle', color: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200' },
  OVERDUE: { label: 'En retard', color: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200' },
  CANCELLED: { label: 'Annulée', color: 'bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-400' },
};

const PAYMENT_METHODS = {
  BANK_TRANSFER: 'Virement bancaire',
  CHECK: 'Chèque',
  CARD: 'Carte bancaire',
  CASH: 'Espèces',
  OTHER: 'Autre',
};

export default function InvoiceDetailPage() {
  const router = useRouter();
  const params = useParams();
  const invoiceId = params.id as string;
  
  const [invoice, setInvoice] = useState<Invoice | null>(null);
  const [clients, setClients] = useState<Client[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [editing, setEditing] = useState(false);
  const [showAddItemDialog, setShowAddItemDialog] = useState(false);
  const [showPaymentDialog, setShowPaymentDialog] = useState(false);
  
  // Edit form
  const [editForm, setEditForm] = useState({
    title: '',
    description: '',
    client_id: '',
    due_date: '',
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

  // Payment form
  const [payment, setPayment] = useState({
    amount: '',
    method: 'BANK_TRANSFER',
  });

  const fetchInvoice = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const res = await fetch(`/api/v1/billing/invoices/${invoiceId}`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setInvoice(data);
        setEditForm({
          title: data.title || '',
          description: data.description || '',
          client_id: data.client_id ? String(data.client_id) : '',
          due_date: data.due_date || '',
          tax_rate: String(data.tax_rate || 20),
          discount_percent: String(data.discount_percent || 0),
          terms: data.terms || '',
          notes: data.notes || '',
        });
      } else {
        toast.error('Facture non trouvée');
        router.push('/factures');
      }
    } catch (err) {
      console.error('Failed to fetch invoice', err);
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
    fetchInvoice();
    fetchClients();
  }, [invoiceId]);

  const saveInvoice = async () => {
    setSaving(true);
    try {
      const token = localStorage.getItem('access_token');
      const res = await fetch(`/api/v1/billing/invoices/${invoiceId}`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          title: editForm.title,
          description: editForm.description || null,
          client_id: editForm.client_id ? parseInt(editForm.client_id) : null,
          due_date: editForm.due_date || null,
          tax_rate: parseFloat(editForm.tax_rate),
          discount_percent: parseFloat(editForm.discount_percent),
          terms: editForm.terms || null,
          notes: editForm.notes || null,
        }),
      });
      
      if (res.ok) {
        toast.success('Facture mise à jour');
        setEditing(false);
        fetchInvoice();
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
      const res = await fetch(`/api/v1/billing/invoices/${invoiceId}/items`, {
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
          position: invoice?.items.length || 0,
        }),
      });
      
      if (res.ok) {
        toast.success('Ligne ajoutée');
        setShowAddItemDialog(false);
        setNewItem({ description: '', quantity: '1', unit: 'unité', unit_price: '' });
        fetchInvoice();
      } else {
        const error = await res.json();
        toast.error(error.detail || 'Erreur');
      }
    } catch (err) {
      toast.error('Erreur de connexion');
    }
  };

  const deleteItem = async (itemId: number) => {
    if (!confirm('Supprimer cette ligne ?')) return;
    
    try {
      const token = localStorage.getItem('access_token');
      const res = await fetch(`/api/v1/billing/invoices/${invoiceId}/items/${itemId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` },
      });
      
      if (res.ok) {
        toast.success('Ligne supprimée');
        fetchInvoice();
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
      const res = await fetch(`/api/v1/billing/invoices/${invoiceId}`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ status }),
      });
      
      if (res.ok) {
        toast.success('Statut mis à jour');
        fetchInvoice();
      } else {
        const error = await res.json();
        toast.error(error.detail || 'Erreur');
      }
    } catch (err) {
      toast.error('Erreur de connexion');
    }
  };

  const recordPayment = async () => {
    if (!payment.amount) {
      toast.error('Montant requis');
      return;
    }
    
    try {
      const token = localStorage.getItem('access_token');
      const res = await fetch(`/api/v1/billing/invoices/${invoiceId}/payment`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          amount_paid: parseFloat(payment.amount),
          payment_method: payment.method,
        }),
      });
      
      if (res.ok) {
        toast.success('Paiement enregistré');
        setShowPaymentDialog(false);
        setPayment({ amount: '', method: 'BANK_TRANSFER' });
        fetchInvoice();
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

  if (!invoice) {
    return null;
  }

  const isEditable = invoice.status !== 'PAID' && invoice.status !== 'CANCELLED';
  const remaining = Number(invoice.total) - Number(invoice.amount_paid);
  const paymentProgress = Number(invoice.total) > 0 
    ? (Number(invoice.amount_paid) / Number(invoice.total)) * 100 
    : 0;

  return (
    <ProtectedRoute>
      <AppLayoutWithOnboarding>
        <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" onClick={() => router.push('/factures')}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Retour
          </Button>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                {invoice.reference}
              </h1>
              <Badge className={STATUS_CONFIG[invoice.status].color}>
                {STATUS_CONFIG[invoice.status].label}
              </Badge>
            </div>
            <p className="text-gray-500 dark:text-gray-400">{invoice.title}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {invoice.status === 'DRAFT' && (
            <Button variant="outline" onClick={() => updateStatus('SENT')}>
              <Send className="h-4 w-4 mr-2" />
              Marquer envoyée
            </Button>
          )}
          {['SENT', 'PARTIAL', 'OVERDUE'].includes(invoice.status) && (
            <Button 
              onClick={() => {
                setPayment({ amount: String(remaining), method: 'BANK_TRANSFER' });
                setShowPaymentDialog(true);
              }}
              className="bg-green-600 hover:bg-green-700"
            >
              <CreditCard className="h-4 w-4 mr-2" />
              Enregistrer paiement
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
          {/* Invoice Info */}
          {editing ? (
            <Card>
              <CardHeader>
                <CardTitle>Informations de la facture</CardTitle>
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
                    <Label>Date d'échéance</Label>
                    <Input
                      type="date"
                      value={editForm.due_date}
                      onChange={(e) => setEditForm({ ...editForm, due_date: e.target.value })}
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
                    placeholder="Conditions de paiement..."
                  />
                </div>
                <div className="space-y-2">
                  <Label>Notes internes</Label>
                  <Textarea
                    value={editForm.notes}
                    onChange={(e) => setEditForm({ ...editForm, notes: e.target.value })}
                  />
                </div>
                <div className="flex justify-end">
                  <Button onClick={saveInvoice} disabled={saving}>
                    <Save className="h-4 w-4 mr-2" />
                    {saving ? 'Enregistrement...' : 'Enregistrer'}
                  </Button>
                </div>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>{invoice.title}</CardTitle>
                  <div className="text-sm text-gray-500 space-x-4">
                    <span>
                      <Calendar className="h-4 w-4 inline mr-1" />
                      {formatDate(invoice.issue_date)}
                    </span>
                    {invoice.due_date && (
                      <span className={invoice.status === 'OVERDUE' ? 'text-red-600' : ''}>
                        <Clock className="h-4 w-4 inline mr-1" />
                        Échéance: {formatDate(invoice.due_date)}
                      </span>
                    )}
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                {invoice.description && (
                  <p className="text-gray-600 dark:text-gray-300 mb-4">{invoice.description}</p>
                )}
                {invoice.terms && (
                  <div className="mt-4 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                    <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Conditions:</p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">{invoice.terms}</p>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Items Table */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Lignes de la facture</CardTitle>
                {isEditable && invoice.status === 'DRAFT' && (
                  <Button size="sm" onClick={() => setShowAddItemDialog(true)}>
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
                    {isEditable && invoice.status === 'DRAFT' && <TableHead className="w-[50px]"></TableHead>}
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {invoice.items.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={isEditable ? 6 : 5} className="text-center py-8 text-gray-500">
                        Aucune ligne
                      </TableCell>
                    </TableRow>
                  ) : (
                    invoice.items.map((item) => (
                      <TableRow key={item.id}>
                        <TableCell>{item.description}</TableCell>
                        <TableCell className="text-right">{item.quantity}</TableCell>
                        <TableCell>{item.unit}</TableCell>
                        <TableCell className="text-right">{formatCurrency(Number(item.unit_price))}</TableCell>
                        <TableCell className="text-right font-medium">{formatCurrency(Number(item.line_total))}</TableCell>
                        {isEditable && invoice.status === 'DRAFT' && (
                          <TableCell>
                            <Button 
                              variant="ghost" 
                              size="icon"
                              onClick={() => deleteItem(item.id)}
                              className="text-red-600 hover:text-red-700"
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </TableCell>
                        )}
                      </TableRow>
                    ))
                  )}
                </TableBody>
                {invoice.items.length > 0 && (
                  <TableFooter>
                    <TableRow>
                      <TableCell colSpan={isEditable && invoice.status === 'DRAFT' ? 4 : 3} className="text-right font-medium">
                        Sous-total HT
                      </TableCell>
                      <TableCell className="text-right font-medium">
                        {formatCurrency(Number(invoice.subtotal))}
                      </TableCell>
                      {isEditable && invoice.status === 'DRAFT' && <TableCell />}
                    </TableRow>
                    {Number(invoice.discount_amount) > 0 && (
                      <TableRow>
                        <TableCell colSpan={isEditable && invoice.status === 'DRAFT' ? 4 : 3} className="text-right text-red-600">
                          Remise ({invoice.discount_percent}%)
                        </TableCell>
                        <TableCell className="text-right text-red-600">
                          -{formatCurrency(Number(invoice.discount_amount))}
                        </TableCell>
                        {isEditable && invoice.status === 'DRAFT' && <TableCell />}
                      </TableRow>
                    )}
                    <TableRow>
                      <TableCell colSpan={isEditable && invoice.status === 'DRAFT' ? 4 : 3} className="text-right">
                        TVA ({invoice.tax_rate}%)
                      </TableCell>
                      <TableCell className="text-right">
                        {formatCurrency(Number(invoice.tax_amount))}
                      </TableCell>
                      {isEditable && invoice.status === 'DRAFT' && <TableCell />}
                    </TableRow>
                    <TableRow className="bg-gray-50 dark:bg-gray-800">
                      <TableCell colSpan={isEditable && invoice.status === 'DRAFT' ? 4 : 3} className="text-right font-bold text-lg">
                        Total TTC
                      </TableCell>
                      <TableCell className="text-right font-bold text-lg">
                        {formatCurrency(Number(invoice.total))}
                      </TableCell>
                      {isEditable && invoice.status === 'DRAFT' && <TableCell />}
                    </TableRow>
                  </TableFooter>
                )}
              </Table>
            </CardContent>
          </Card>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Payment Status Card */}
          <Card className={invoice.status === 'PAID' ? 'border-green-200 bg-green-50 dark:bg-green-950' : ''}>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <DollarSign className="h-5 w-5" />
                Paiement
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <div className="flex justify-between text-sm mb-2">
                  <span>Progression</span>
                  <span>{paymentProgress.toFixed(0)}%</span>
                </div>
                <Progress value={paymentProgress} className="h-2" />
              </div>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-gray-500">Montant total</span>
                  <span className="font-medium">{formatCurrency(Number(invoice.total))}</span>
                </div>
                <div className="flex justify-between text-green-600">
                  <span>Payé</span>
                  <span className="font-medium">{formatCurrency(Number(invoice.amount_paid))}</span>
                </div>
                {remaining > 0 && (
                  <div className="flex justify-between text-orange-600">
                    <span>Reste à payer</span>
                    <span className="font-medium">{formatCurrency(remaining)}</span>
                  </div>
                )}
              </div>
              {invoice.payment_method && (
                <div className="pt-2 border-t">
                  <span className="text-sm text-gray-500">Mode de paiement: </span>
                  <span className="text-sm">{PAYMENT_METHODS[invoice.payment_method as keyof typeof PAYMENT_METHODS]}</span>
                </div>
              )}
              {invoice.paid_date && (
                <div>
                  <span className="text-sm text-gray-500">Date de paiement: </span>
                  <span className="text-sm">{formatDate(invoice.paid_date)}</span>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Client Card */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                {invoice.client?.company_name ? (
                  <Building2 className="h-5 w-5" />
                ) : (
                  <User className="h-5 w-5" />
                )}
                Client
              </CardTitle>
            </CardHeader>
            <CardContent>
              {invoice.client ? (
                <div className="space-y-2">
                  <p className="font-medium">{invoice.client.company_name || invoice.client.name}</p>
                  {invoice.client.company_name && (
                    <p className="text-sm text-gray-500">{invoice.client.name}</p>
                  )}
                  {invoice.client.email && (
                    <p className="text-sm text-gray-600 dark:text-gray-400">{invoice.client.email}</p>
                  )}
                  {invoice.client.phone && (
                    <p className="text-sm text-gray-600 dark:text-gray-400">{invoice.client.phone}</p>
                  )}
                  {invoice.client.address_line1 && (
                    <div className="text-sm text-gray-600 dark:text-gray-400 pt-2 border-t">
                      <p>{invoice.client.address_line1}</p>
                      <p>{invoice.client.postal_code} {invoice.client.city}</p>
                    </div>
                  )}
                </div>
              ) : (
                <p className="text-gray-500">Aucun client sélectionné</p>
              )}
            </CardContent>
          </Card>

          {/* Overdue Warning */}
          {invoice.status === 'OVERDUE' && (
            <Card className="border-red-200 bg-red-50 dark:bg-red-950">
              <CardContent className="p-4">
                <div className="flex items-center gap-2 text-red-700 dark:text-red-300">
                  <AlertTriangle className="h-5 w-5" />
                  <span className="font-medium">Facture en retard</span>
                </div>
                <p className="text-sm text-red-600 dark:text-red-400 mt-1">
                  L'échéance était le {invoice.due_date && formatDate(invoice.due_date)}
                </p>
              </CardContent>
            </Card>
          )}

          {/* Source Quote */}
          {invoice.source_quote_id && (
            <Card className="border-blue-200 bg-blue-50 dark:bg-blue-950">
              <CardContent className="p-4">
                <div className="flex items-center gap-2 text-blue-700 dark:text-blue-300">
                  <FileCheck className="h-5 w-5" />
                  <span>Créée depuis un devis</span>
                </div>
                <Button 
                  variant="link" 
                  className="text-blue-700 p-0 mt-2"
                  onClick={() => router.push(`/devis/${invoice.source_quote_id}`)}
                >
                  Voir le devis →
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
              Ajoutez une prestation ou un produit à la facture
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

      {/* Payment Dialog */}
      <Dialog open={showPaymentDialog} onOpenChange={setShowPaymentDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Enregistrer un paiement</DialogTitle>
            <DialogDescription>
              Reste à payer: {formatCurrency(remaining)}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Montant payé *</Label>
              <Input
                type="number"
                step="0.01"
                placeholder="0.00"
                value={payment.amount}
                onChange={(e) => setPayment({ ...payment, amount: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label>Mode de paiement</Label>
              <Select 
                value={payment.method} 
                onValueChange={(v) => setPayment({ ...payment, method: v })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="BANK_TRANSFER">Virement bancaire</SelectItem>
                  <SelectItem value="CHECK">Chèque</SelectItem>
                  <SelectItem value="CARD">Carte bancaire</SelectItem>
                  <SelectItem value="CASH">Espèces</SelectItem>
                  <SelectItem value="OTHER">Autre</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowPaymentDialog(false)}>
              Annuler
            </Button>
            <Button onClick={recordPayment} className="bg-green-600 hover:bg-green-700">
              <Check className="h-4 w-4 mr-2" />
              Enregistrer
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
        </div>
      </AppLayoutWithOnboarding>
    </ProtectedRoute>
  );
}
