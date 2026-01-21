'use client';

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Folder,
  FileText,
  Table,
  Image,
  Video,
  Cloud,
  Link as LinkIcon,
  File,
  ExternalLink,
  Trash2,
  Plus,
  Search,
  Filter,
  MoreHorizontal,
  Copy,
  Eye,
  Loader2,
  X,
  Check,
} from 'lucide-react';
import { toast } from 'sonner';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from '@/components/ui/dropdown-menu';

import {
  assetsApi,
  Asset,
  AssetType,
  AssetStatus,
  AssetFilters,
  AssetCreateRequest,
  ASSET_TYPE_CONFIG,
  ASSET_STATUS_CONFIG,
} from '@/lib/api';

// ============================================================================
// ASSET TYPE ICON COMPONENT
// ============================================================================

const AssetTypeIcon = ({ type, className = 'h-5 w-5' }: { type: AssetType; className?: string }) => {
  const config = ASSET_TYPE_CONFIG[type] || ASSET_TYPE_CONFIG.OTHER;
  
  const icons: Record<string, React.ReactNode> = {
    folder: <Folder className={`${className} ${config.color}`} />,
    'file-text': <FileText className={`${className} ${config.color}`} />,
    table: <Table className={`${className} ${config.color}`} />,
    image: <Image className={`${className} ${config.color}`} />,
    video: <Video className={`${className} ${config.color}`} />,
    cloud: <Cloud className={`${className} ${config.color}`} />,
    link: <LinkIcon className={`${className} ${config.color}`} />,
    file: <File className={`${className} ${config.color}`} />,
  };
  
  return icons[config.icon] || icons.file;
};

// ============================================================================
// ASSET CARD COMPONENT
// ============================================================================

interface AssetCardProps {
  asset: Asset;
  showProject?: boolean;
  onDelete?: (id: number) => void;
  onViewProject?: (projectId: number) => void;
}

export function AssetCard({ asset, showProject = true, onDelete, onViewProject }: AssetCardProps) {
  const [copied, setCopied] = useState(false);
  
  const handleCopyLink = () => {
    navigator.clipboard.writeText(asset.url);
    setCopied(true);
    toast.success('Lien copié !');
    setTimeout(() => setCopied(false), 2000);
  };
  
  const handleOpen = () => {
    window.open(asset.url, '_blank');
  };
  
  const typeConfig = ASSET_TYPE_CONFIG[asset.type] || ASSET_TYPE_CONFIG.OTHER;
  const statusConfig = asset.status ? ASSET_STATUS_CONFIG[asset.status] : null;
  
  return (
    <div className="flex items-center justify-between p-4 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors group">
      <div className="flex items-center gap-4 min-w-0 flex-1">
        {/* Icon */}
        <div className="p-2 bg-gray-50 rounded-lg flex-shrink-0">
          <AssetTypeIcon type={asset.type} className="h-6 w-6" />
        </div>
        
        {/* Info */}
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <h4 className="font-medium text-gray-900 truncate">{asset.name}</h4>
            {asset.version && (
              <Badge variant="outline" className="text-xs flex-shrink-0">
                {asset.version}
              </Badge>
            )}
            {statusConfig && (
              <Badge className={`text-xs flex-shrink-0 ${statusConfig.color}`}>
                {statusConfig.label}
              </Badge>
            )}
          </div>
          
          {showProject && (asset.project_name || asset.client_name) && (
            <div className="flex items-center gap-2 text-sm text-gray-500 mt-0.5">
              {asset.project_name && <span>{asset.project_name}</span>}
              {asset.project_name && asset.client_name && <span>•</span>}
              {asset.client_name && <span className="text-gray-400">{asset.client_name}</span>}
            </div>
          )}
          
          <p className="text-xs text-gray-400 truncate mt-0.5">{asset.url}</p>
        </div>
      </div>
      
      {/* Actions */}
      <div className="flex items-center gap-2 flex-shrink-0 ml-4">
        <Button
          size="sm"
          variant="ghost"
          onClick={handleOpen}
          className="opacity-0 group-hover:opacity-100 transition-opacity"
        >
          <ExternalLink className="h-4 w-4" />
        </Button>
        
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button size="sm" variant="ghost">
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={handleOpen}>
              <ExternalLink className="h-4 w-4 mr-2" />
              Ouvrir
            </DropdownMenuItem>
            <DropdownMenuItem onClick={handleCopyLink}>
              {copied ? <Check className="h-4 w-4 mr-2" /> : <Copy className="h-4 w-4 mr-2" />}
              Copier le lien
            </DropdownMenuItem>
            {showProject && asset.project_id && onViewProject && (
              <DropdownMenuItem onClick={() => onViewProject(asset.project_id)}>
                <Eye className="h-4 w-4 mr-2" />
                Voir le projet
              </DropdownMenuItem>
            )}
            {onDelete && (
              <>
                <DropdownMenuSeparator />
                <DropdownMenuItem 
                  onClick={() => onDelete(asset.id)}
                  className="text-red-600 focus:text-red-600"
                >
                  <Trash2 className="h-4 w-4 mr-2" />
                  Supprimer
                </DropdownMenuItem>
              </>
            )}
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </div>
  );
}

// ============================================================================
// ASSETS FILTERS COMPONENT
// ============================================================================

interface AssetsFiltersProps {
  filters: AssetFilters;
  onFiltersChange: (filters: AssetFilters) => void;
  projects?: Array<{ id: number; name: string }>;
  showProjectFilter?: boolean;
  className?: string;
}

export function AssetsFilters({
  filters,
  onFiltersChange,
  projects = [],
  showProjectFilter = true,
  className = '',
}: AssetsFiltersProps) {
  return (
    <div className={`flex flex-wrap items-center gap-3 ${className}`}>
      {/* Search */}
      <div className="relative flex-1 min-w-[200px]">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
        <Input
          placeholder="Rechercher un asset..."
          value={filters.q || ''}
          onChange={(e) => onFiltersChange({ ...filters, q: e.target.value || undefined, page: 1 })}
          className="pl-10"
        />
      </div>
      
      {/* Project filter */}
      {showProjectFilter && projects.length > 0 && (
        <Select
          value={filters.project_id?.toString() || 'all'}
          onValueChange={(v) => onFiltersChange({ 
            ...filters, 
            project_id: v === 'all' ? undefined : parseInt(v),
            page: 1
          })}
        >
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Tous les projets" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Tous les projets</SelectItem>
            {projects.map((p) => (
              <SelectItem key={p.id} value={p.id.toString()}>
                {p.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      )}
      
      {/* Type filter */}
      <Select
        value={filters.type || 'all'}
        onValueChange={(v) => onFiltersChange({ 
          ...filters, 
          type: v === 'all' ? undefined : v as AssetType,
          page: 1
        })}
      >
        <SelectTrigger className="w-[150px]">
          <SelectValue placeholder="Tous les types" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">Tous les types</SelectItem>
          {Object.entries(ASSET_TYPE_CONFIG).map(([key, config]) => (
            <SelectItem key={key} value={key}>
              {config.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      
      {/* Status filter */}
      <Select
        value={filters.status || 'all'}
        onValueChange={(v) => onFiltersChange({ 
          ...filters, 
          status: v === 'all' ? undefined : v as AssetStatus,
          page: 1
        })}
      >
        <SelectTrigger className="w-[130px]">
          <SelectValue placeholder="Tous" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">Tous statuts</SelectItem>
          {Object.entries(ASSET_STATUS_CONFIG).map(([key, config]) => (
            <SelectItem key={key} value={key}>
              {config.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      
      {/* Clear filters */}
      {(filters.q || filters.type || filters.status || filters.project_id) && (
        <Button
          variant="ghost"
          size="sm"
          onClick={() => onFiltersChange({ page: 1, limit: filters.limit })}
        >
          <X className="h-4 w-4 mr-1" />
          Effacer
        </Button>
      )}
    </div>
  );
}

// ============================================================================
// ADD ASSET DIALOG COMPONENT
// ============================================================================

interface AddAssetDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  projectId?: number;
  projects?: Array<{ id: number; name: string }>;
  onSuccess?: () => void;
}

export function AddAssetDialog({
  open,
  onOpenChange,
  projectId,
  projects = [],
  onSuccess,
}: AddAssetDialogProps) {
  const queryClient = useQueryClient();
  const [formData, setFormData] = useState<AssetCreateRequest>({
    project_id: projectId || 0,
    name: '',
    url: '',
    type: 'LINK',
    status: 'DRAFT',
  });
  
  // Reset form when dialog opens
  React.useEffect(() => {
    if (open) {
      setFormData({
        project_id: projectId || 0,
        name: '',
        url: '',
        type: 'LINK',
        status: 'DRAFT',
      });
    }
  }, [open, projectId]);
  
  const createMutation = useMutation({
    mutationFn: (data: AssetCreateRequest) => assetsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['assets'] });
      toast.success('Asset créé !');
      onOpenChange(false);
      onSuccess?.();
    },
    onError: (error: any) => {
      if (error?.response?.status === 409) {
        toast.error('Cet URL existe déjà pour ce projet');
      } else {
        toast.error('Erreur lors de la création');
      }
    },
  });
  
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.project_id || !formData.name || !formData.url) {
      toast.error('Veuillez remplir tous les champs obligatoires');
      return;
    }
    createMutation.mutate(formData);
  };
  
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Ajouter un asset</DialogTitle>
          <DialogDescription>
            Ajoutez un lien vers une ressource externe (Drive, Figma, Dropbox, etc.)
          </DialogDescription>
        </DialogHeader>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Project selector (if not pre-set) */}
          {!projectId && projects.length > 0 && (
            <div>
              <Label>Projet *</Label>
              <Select
                value={formData.project_id?.toString() || ''}
                onValueChange={(v) => setFormData({ ...formData, project_id: parseInt(v) })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Sélectionner un projet" />
                </SelectTrigger>
                <SelectContent>
                  {projects.map((p) => (
                    <SelectItem key={p.id} value={p.id.toString()}>
                      {p.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}
          
          {/* Name */}
          <div>
            <Label>Nom *</Label>
            <Input
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="Maquette Figma v2"
            />
          </div>
          
          {/* URL */}
          <div>
            <Label>URL *</Label>
            <Input
              value={formData.url}
              onChange={(e) => setFormData({ ...formData, url: e.target.value })}
              placeholder="https://..."
            />
          </div>
          
          <div className="grid grid-cols-3 gap-4">
            {/* Type */}
            <div>
              <Label>Type</Label>
              <Select
                value={formData.type}
                onValueChange={(v) => setFormData({ ...formData, type: v as AssetType })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(ASSET_TYPE_CONFIG).map(([key, config]) => (
                    <SelectItem key={key} value={key}>
                      {config.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            {/* Version */}
            <div>
              <Label>Version</Label>
              <Input
                value={formData.version || ''}
                onChange={(e) => setFormData({ ...formData, version: e.target.value || undefined })}
                placeholder="v1, final..."
              />
            </div>
            
            {/* Status */}
            <div>
              <Label>Statut</Label>
              <Select
                value={formData.status}
                onValueChange={(v) => setFormData({ ...formData, status: v as AssetStatus })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(ASSET_STATUS_CONFIG).map(([key, config]) => (
                    <SelectItem key={key} value={key}>
                      {config.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Annuler
            </Button>
            <Button
              type="submit"
              disabled={createMutation.isPending || !formData.project_id || !formData.name || !formData.url}
              className="bg-purple-600 hover:bg-purple-700"
            >
              {createMutation.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Création...
                </>
              ) : (
                'Ajouter'
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

// ============================================================================
// ASSETS LIST COMPONENT (Main reusable component)
// ============================================================================

interface AssetsListProps {
  projectId?: number;
  showProjectFilter?: boolean;
  showProjectColumn?: boolean;
  projects?: Array<{ id: number; name: string }>;
  onViewProject?: (projectId: number) => void;
  className?: string;
}

export function AssetsList({
  projectId,
  showProjectFilter = true,
  showProjectColumn = true,
  projects = [],
  onViewProject,
  className = '',
}: AssetsListProps) {
  const queryClient = useQueryClient();
  const [filters, setFilters] = useState<AssetFilters>({
    project_id: projectId,
    page: 1,
    limit: 50,
  });
  const [showAddDialog, setShowAddDialog] = useState(false);
  
  // Update filters when projectId prop changes
  React.useEffect(() => {
    if (projectId !== undefined) {
      setFilters(prev => ({ ...prev, project_id: projectId }));
    }
  }, [projectId]);
  
  const { data, isLoading, error } = useQuery({
    queryKey: ['assets', filters],
    queryFn: () => assetsApi.list(filters),
  });
  
  const deleteMutation = useMutation({
    mutationFn: (id: number) => assetsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['assets'] });
      toast.success('Asset supprimé');
    },
    onError: () => {
      toast.error('Erreur lors de la suppression');
    },
  });
  
  const handleDelete = (id: number) => {
    if (window.confirm('Supprimer cet asset ?')) {
      deleteMutation.mutate(id);
    }
  };
  
  if (error) {
    return (
      <div className="text-center py-8 text-red-500">
        Erreur lors du chargement des assets
      </div>
    );
  }
  
  return (
    <div className={className}>
      {/* Filters */}
      <div className="flex items-center justify-between mb-4">
        <AssetsFilters
          filters={filters}
          onFiltersChange={setFilters}
          projects={projects}
          showProjectFilter={showProjectFilter && !projectId}
          className="flex-1"
        />
        
        <Button
          onClick={() => setShowAddDialog(true)}
          className="bg-purple-600 hover:bg-purple-700 ml-4"
        >
          <Plus className="h-4 w-4 mr-2" />
          Ajouter un asset
        </Button>
      </div>
      
      {/* Loading state */}
      {isLoading && (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-purple-500" />
        </div>
      )}
      
      {/* Empty state */}
      {!isLoading && data?.items.length === 0 && (
        <Card className="border-dashed">
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Folder className="h-12 w-12 text-gray-300 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-1">Aucun asset</h3>
            <p className="text-gray-500 mb-4">
              {filters.q || filters.type || filters.status
                ? 'Aucun résultat pour ces filtres'
                : 'Ajoutez des liens vers vos ressources'}
            </p>
            <Button onClick={() => setShowAddDialog(true)} className="bg-purple-600 hover:bg-purple-700">
              <Plus className="h-4 w-4 mr-2" />
              Ajouter un asset
            </Button>
          </CardContent>
        </Card>
      )}
      
      {/* Assets list */}
      {!isLoading && data && data.items.length > 0 && (
        <div className="space-y-2">
          {data.items.map((asset) => (
            <AssetCard
              key={asset.id}
              asset={asset}
              showProject={showProjectColumn && !projectId}
              onDelete={handleDelete}
              onViewProject={onViewProject}
            />
          ))}
          
          {/* Pagination info */}
          {data.total > data.limit && (
            <div className="flex items-center justify-between pt-4 text-sm text-gray-500">
              <span>
                {data.items.length} sur {data.total} assets
              </span>
              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  disabled={filters.page === 1}
                  onClick={() => setFilters({ ...filters, page: (filters.page || 1) - 1 })}
                >
                  Précédent
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  disabled={!data.has_more}
                  onClick={() => setFilters({ ...filters, page: (filters.page || 1) + 1 })}
                >
                  Suivant
                </Button>
              </div>
            </div>
          )}
        </div>
      )}
      
      {/* Add dialog */}
      <AddAssetDialog
        open={showAddDialog}
        onOpenChange={setShowAddDialog}
        projectId={projectId}
        projects={projects}
      />
    </div>
  );
}

export default AssetsList;
