'use client';

import { useState, useEffect } from 'react';
import {
  FolderOpen,
  Plus,
  Link as LinkIcon,
  FileText,
  MoreHorizontal,
  Loader2,
  X,
  Search,
  ExternalLink,
  Image,
  Video,
  FileAudio,
  File,
  Filter,
} from 'lucide-react';

interface Asset {
  id: number;
  project_id: number;
  kind: string;
  name: string;
  url: string;
  version?: string;
  created_at: string;
  project_name?: string;
  client_name?: string;
}

interface Project {
  id: number;
  name: string;
  client_name?: string;
}

const KIND_ICONS: Record<string, React.ReactNode> = {
  link: <LinkIcon className="h-5 w-5" />,
  file: <FileText className="h-5 w-5" />,
};

export default function AssetsPage() {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [filterProject, setFilterProject] = useState<string>('');
  const [filterKind, setFilterKind] = useState<string>('');
  const [search, setSearch] = useState('');

  // Form state
  const [newAsset, setNewAsset] = useState({
    name: '',
    project_id: '',
    kind: 'link',
    url: '',
    version: '',
  });

  const fetchData = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const params = new URLSearchParams();
      if (filterProject) params.append('project_id', filterProject);
      if (filterKind) params.append('kind', filterKind);
      
      const [assetsRes, projectsRes] = await Promise.all([
        fetch(`/api/v1/agency/assets?${params}`, {
          headers: { 'Authorization': `Bearer ${token}` },
        }),
        fetch('/api/v1/agency/projects', {
          headers: { 'Authorization': `Bearer ${token}` },
        }),
      ]);
      
      if (assetsRes.ok) {
        setAssets(await assetsRes.json());
      }
      if (projectsRes.ok) {
        setProjects(await projectsRes.json());
      }
    } catch (err) {
      console.error('Failed to fetch assets:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [filterProject, filterKind]);

  const handleCreateAsset = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('/api/v1/agency/assets', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...newAsset,
          project_id: parseInt(newAsset.project_id),
        }),
      });
      
      if (response.ok) {
        setShowAddModal(false);
        setNewAsset({ name: '', project_id: '', kind: 'link', url: '', version: '' });
        await fetchData();
      }
    } catch (err) {
      console.error('Failed to create asset:', err);
    }
  };

  const handleDeleteAsset = async (assetId: number) => {
    if (!confirm('Supprimer cet asset ?')) return;
    
    try {
      const token = localStorage.getItem('access_token');
      await fetch(`/api/v1/agency/assets/${assetId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` },
      });
      
      await fetchData();
    } catch (err) {
      console.error('Failed to delete asset:', err);
    }
  };

  const filteredAssets = assets.filter((a) =>
    a.name.toLowerCase().includes(search.toLowerCase()) ||
    (a.project_name && a.project_name.toLowerCase().includes(search.toLowerCase())) ||
    (a.client_name && a.client_name.toLowerCase().includes(search.toLowerCase()))
  );

  const getUrlIcon = (url: string) => {
    if (url.includes('drive.google') || url.includes('docs.google')) {
      return <FileText className="h-8 w-8 text-blue-500" />;
    }
    if (url.includes('figma.com')) {
      return <Image className="h-8 w-8 text-purple-500" />;
    }
    if (url.includes('youtube.com') || url.includes('vimeo.com')) {
      return <Video className="h-8 w-8 text-red-500" />;
    }
    if (url.includes('dropbox.com')) {
      return <FolderOpen className="h-8 w-8 text-blue-600" />;
    }
    return <LinkIcon className="h-8 w-8 text-gray-500" />;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('fr-FR', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="h-8 w-8 animate-spin text-purple-600" />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Assets</h1>
          <p className="text-gray-600">{assets.length} assets</p>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
        >
          <Plus className="h-4 w-4" />
          Ajouter un asset
        </button>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4 flex-wrap">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Rechercher un asset..."
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
          />
        </div>
        
        <select
          value={filterProject}
          onChange={(e) => setFilterProject(e.target.value)}
          className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
        >
          <option value="">Tous les projets</option>
          {projects.map((project) => (
            <option key={project.id} value={project.id}>
              {project.name}
            </option>
          ))}
        </select>
        
        <select
          value={filterKind}
          onChange={(e) => setFilterKind(e.target.value)}
          className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
        >
          <option value="">Tous les types</option>
          <option value="link">Liens</option>
          <option value="file">Fichiers</option>
        </select>
      </div>

      {/* Assets Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {filteredAssets.map((asset) => (
          <div
            key={asset.id}
            className="bg-white rounded-xl border border-gray-100 p-5 hover:shadow-md transition-shadow group"
          >
            <div className="flex items-start justify-between mb-4">
              <div className="p-3 bg-gray-50 rounded-xl">
                {getUrlIcon(asset.url)}
              </div>
              <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                <a
                  href={asset.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="p-1.5 hover:bg-gray-100 rounded text-gray-400 hover:text-gray-600"
                >
                  <ExternalLink className="h-4 w-4" />
                </a>
                <button
                  onClick={() => handleDeleteAsset(asset.id)}
                  className="p-1.5 hover:bg-red-50 rounded text-gray-400 hover:text-red-600"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            </div>
            
            <h3 className="font-medium text-gray-900 mb-1 line-clamp-2">{asset.name}</h3>
            
            {asset.version && (
              <span className="text-xs px-2 py-0.5 bg-purple-50 text-purple-600 rounded mb-2 inline-block">
                v{asset.version}
              </span>
            )}
            
            <div className="mt-3 pt-3 border-t border-gray-100">
              {asset.project_name && (
                <p className="text-sm text-gray-600 truncate">{asset.project_name}</p>
              )}
              {asset.client_name && (
                <p className="text-xs text-gray-400 truncate">{asset.client_name}</p>
              )}
              <p className="text-xs text-gray-400 mt-1">{formatDate(asset.created_at)}</p>
            </div>
          </div>
        ))}
        
        {filteredAssets.length === 0 && (
          <div className="col-span-full text-center py-12 text-gray-500">
            <FolderOpen className="h-12 w-12 mx-auto mb-4 text-gray-300" />
            <p>Aucun asset trouvé</p>
          </div>
        )}
      </div>

      {/* Add Asset Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-lg mx-4">
            <div className="flex items-center justify-between p-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold">Ajouter un asset</h2>
              <button
                onClick={() => setShowAddModal(false)}
                className="p-1 hover:bg-gray-100 rounded"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            
            <form onSubmit={handleCreateAsset} className="p-4 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Nom *
                </label>
                <input
                  type="text"
                  required
                  value={newAsset.name}
                  onChange={(e) => setNewAsset({ ...newAsset, name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                  placeholder="Ex: Logo vectoriel"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Projet *
                </label>
                <select
                  required
                  value={newAsset.project_id}
                  onChange={(e) => setNewAsset({ ...newAsset, project_id: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                >
                  <option value="">Sélectionner un projet</option>
                  {projects.map((project) => (
                    <option key={project.id} value={project.id}>
                      {project.name} {project.client_name && `- ${project.client_name}`}
                    </option>
                  ))}
                </select>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Type
                  </label>
                  <select
                    value={newAsset.kind}
                    onChange={(e) => setNewAsset({ ...newAsset, kind: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                  >
                    <option value="link">Lien</option>
                    <option value="file">Fichier</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Version
                  </label>
                  <input
                    type="text"
                    value={newAsset.version}
                    onChange={(e) => setNewAsset({ ...newAsset, version: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                    placeholder="1.0"
                  />
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  URL *
                </label>
                <input
                  type="url"
                  required
                  value={newAsset.url}
                  onChange={(e) => setNewAsset({ ...newAsset, url: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                  placeholder="https://drive.google.com/..."
                />
              </div>
              
              <div className="flex justify-end gap-3 pt-4 border-t border-gray-200">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg"
                >
                  Annuler
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
                >
                  Ajouter l'asset
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
