'use client';

import { motion } from 'framer-motion';
import Link from 'next/link';
import { 
  FolderKanban, 
  Users, 
  TrendingUp, 
  Bell,
  Search,
  Plus,
  MoreHorizontal,
  Calendar,
  Euro,
  CheckCircle2,
  Clock,
  AlertCircle,
  ArrowRight,
  Zap,
  Mail,
  FileText,
  Target
} from 'lucide-react';

export default function DemoPage() {
  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
        <div className="flex items-center justify-between px-6 py-3">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <div className="h-9 w-9 bg-gradient-to-r from-purple-600 to-pink-500 rounded-xl flex items-center justify-center">
                <span className="text-white font-bold text-lg">R</span>
              </div>
              <span className="font-bold text-xl text-gray-900">Radar</span>
              <span className="text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded-full font-medium">Demo</span>
            </div>
            
            <nav className="hidden md:flex items-center gap-1 ml-8">
              <button className="flex items-center gap-2 px-4 py-2 bg-purple-50 text-purple-700 rounded-lg font-medium text-sm">
                <FolderKanban className="h-4 w-4" />
                Cockpit
              </button>
              <button className="flex items-center gap-2 px-4 py-2 text-gray-600 hover:bg-gray-50 rounded-lg font-medium text-sm">
                <Users className="h-4 w-4" />
                Clients
              </button>
              <button className="flex items-center gap-2 px-4 py-2 text-gray-600 hover:bg-gray-50 rounded-lg font-medium text-sm">
                <TrendingUp className="h-4 w-4" />
                Pipeline
              </button>
            </nav>
          </div>

          <div className="flex items-center gap-3">
            <div className="relative hidden md:block">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input 
                type="text" 
                placeholder="Rechercher..." 
                className="pl-10 pr-4 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm w-64 focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
            </div>
            <button className="relative p-2 text-gray-500 hover:bg-gray-50 rounded-lg">
              <Bell className="h-5 w-5" />
              <span className="absolute top-1 right-1 h-2 w-2 bg-red-500 rounded-full"></span>
            </button>
            <div className="h-9 w-9 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full flex items-center justify-center text-white font-medium text-sm">
              AK
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="p-6">
        {/* Page Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Cockpit</h1>
            <p className="text-gray-500 text-sm">Vue d'ensemble de votre activité</p>
          </div>
          <div className="flex items-center gap-3">
            <button className="flex items-center gap-2 px-4 py-2 border border-gray-200 bg-white rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50">
              <Calendar className="h-4 w-4" />
              Cette semaine
            </button>
            <button className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg text-sm font-medium hover:bg-purple-700">
              <Plus className="h-4 w-4" />
              Nouveau projet
            </button>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-white rounded-xl p-5 border border-gray-100 shadow-sm"
          >
            <div className="flex items-center justify-between mb-3">
              <span className="text-gray-500 text-sm font-medium">Projets actifs</span>
              <div className="h-8 w-8 bg-purple-100 rounded-lg flex items-center justify-center">
                <FolderKanban className="h-4 w-4 text-purple-600" />
              </div>
            </div>
            <div className="text-3xl font-bold text-gray-900">12</div>
            <div className="flex items-center gap-1 mt-1 text-sm">
              <span className="text-green-600 font-medium">+3</span>
              <span className="text-gray-400">ce mois</span>
            </div>
          </motion.div>

          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="bg-white rounded-xl p-5 border border-gray-100 shadow-sm"
          >
            <div className="flex items-center justify-between mb-3">
              <span className="text-gray-500 text-sm font-medium">En attente validation</span>
              <div className="h-8 w-8 bg-orange-100 rounded-lg flex items-center justify-center">
                <Clock className="h-4 w-4 text-orange-600" />
              </div>
            </div>
            <div className="text-3xl font-bold text-orange-500">5</div>
            <div className="flex items-center gap-1 mt-1 text-sm">
              <span className="text-orange-600 font-medium">2 urgents</span>
            </div>
          </motion.div>

          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="bg-white rounded-xl p-5 border border-gray-100 shadow-sm"
          >
            <div className="flex items-center justify-between mb-3">
              <span className="text-gray-500 text-sm font-medium">Leads chauds</span>
              <div className="h-8 w-8 bg-green-100 rounded-lg flex items-center justify-center">
                <Zap className="h-4 w-4 text-green-600" />
              </div>
            </div>
            <div className="text-3xl font-bold text-green-500">8</div>
            <div className="flex items-center gap-1 mt-1 text-sm">
              <span className="text-green-600 font-medium">66 000€</span>
              <span className="text-gray-400">potentiel</span>
            </div>
          </motion.div>

          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="bg-white rounded-xl p-5 border border-gray-100 shadow-sm"
          >
            <div className="flex items-center justify-between mb-3">
              <span className="text-gray-500 text-sm font-medium">CA du mois</span>
              <div className="h-8 w-8 bg-blue-100 rounded-lg flex items-center justify-center">
                <Euro className="h-4 w-4 text-blue-600" />
              </div>
            </div>
            <div className="text-3xl font-bold text-gray-900">47 500€</div>
            <div className="flex items-center gap-1 mt-1 text-sm">
              <span className="text-green-600 font-medium">+18%</span>
              <span className="text-gray-400">vs mois dernier</span>
            </div>
          </motion.div>
        </div>

        {/* Main Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Kanban Columns */}
          <div className="lg:col-span-2 grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* À faire */}
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 }}
              className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden"
            >
              <div className="flex items-center justify-between p-4 border-b border-gray-100">
                <div className="flex items-center gap-2">
                  <div className="h-2 w-2 bg-gray-400 rounded-full"></div>
                  <span className="font-semibold text-gray-700">À faire</span>
                </div>
                <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded-full font-medium">4</span>
              </div>
              <div className="p-3 space-y-3">
                <div className="bg-purple-50 border-l-4 border-purple-500 p-3 rounded-lg">
                  <div className="font-medium text-gray-900 text-sm mb-1">Maquettes V2 - Homepage</div>
                  <div className="text-xs text-gray-500 mb-2">Studio Neon Productions</div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded">Design</span>
                    <span className="text-xs text-gray-400">J+2</span>
                  </div>
                </div>
                <div className="bg-gray-50 border-l-4 border-gray-300 p-3 rounded-lg">
                  <div className="font-medium text-gray-900 text-sm mb-1">Brief créatif</div>
                  <div className="text-xs text-gray-500 mb-2">Agence Pulse Media</div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded">Stratégie</span>
                    <span className="text-xs text-gray-400">J+5</span>
                  </div>
                </div>
                <div className="bg-gray-50 border-l-4 border-gray-300 p-3 rounded-lg">
                  <div className="font-medium text-gray-900 text-sm mb-1">Devis détaillé</div>
                  <div className="text-xs text-gray-500 mb-2">MediaLab Paris</div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs bg-blue-100 text-blue-600 px-2 py-0.5 rounded">Admin</span>
                    <span className="text-xs text-red-500 font-medium">Urgent</span>
                  </div>
                </div>
              </div>
            </motion.div>

            {/* En cours */}
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.6 }}
              className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden"
            >
              <div className="flex items-center justify-between p-4 border-b border-gray-100">
                <div className="flex items-center gap-2">
                  <div className="h-2 w-2 bg-blue-500 rounded-full"></div>
                  <span className="font-semibold text-gray-700">En cours</span>
                </div>
                <span className="text-xs bg-blue-100 text-blue-600 px-2 py-1 rounded-full font-medium">3</span>
              </div>
              <div className="p-3 space-y-3">
                <div className="bg-blue-50 border-l-4 border-blue-500 p-3 rounded-lg">
                  <div className="font-medium text-gray-900 text-sm mb-1">Développement app</div>
                  <div className="text-xs text-gray-500 mb-2">Creative House Agency</div>
                  <div className="flex items-center justify-between">
                    <div className="flex -space-x-2">
                      <div className="h-6 w-6 bg-green-400 rounded-full border-2 border-white text-[10px] flex items-center justify-center text-white font-medium">ML</div>
                      <div className="h-6 w-6 bg-purple-400 rounded-full border-2 border-white text-[10px] flex items-center justify-center text-white font-medium">SK</div>
                    </div>
                    <div className="w-16 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                      <div className="w-3/4 h-full bg-blue-500 rounded-full"></div>
                    </div>
                  </div>
                </div>
                <div className="bg-blue-50 border-l-4 border-blue-500 p-3 rounded-lg">
                  <div className="font-medium text-gray-900 text-sm mb-1">Motion design - Intro</div>
                  <div className="text-xs text-gray-500 mb-2">Studio Lumière</div>
                  <div className="flex items-center justify-between">
                    <div className="flex -space-x-2">
                      <div className="h-6 w-6 bg-orange-400 rounded-full border-2 border-white text-[10px] flex items-center justify-center text-white font-medium">JP</div>
                    </div>
                    <div className="w-16 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                      <div className="w-1/2 h-full bg-blue-500 rounded-full"></div>
                    </div>
                  </div>
                </div>
                <div className="bg-yellow-50 border-l-4 border-yellow-500 p-3 rounded-lg">
                  <div className="font-medium text-gray-900 text-sm mb-1">Révisions client</div>
                  <div className="text-xs text-gray-500 mb-2">Groupe Horizon</div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs bg-yellow-100 text-yellow-700 px-2 py-0.5 rounded">Feedback</span>
                    <AlertCircle className="h-4 w-4 text-yellow-500" />
                  </div>
                </div>
              </div>
            </motion.div>

            {/* Terminé */}
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.7 }}
              className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden"
            >
              <div className="flex items-center justify-between p-4 border-b border-gray-100">
                <div className="flex items-center gap-2">
                  <div className="h-2 w-2 bg-green-500 rounded-full"></div>
                  <span className="font-semibold text-gray-700">Terminé</span>
                </div>
                <span className="text-xs bg-green-100 text-green-600 px-2 py-1 rounded-full font-medium">5</span>
              </div>
              <div className="p-3 space-y-3">
                <div className="bg-green-50 border-l-4 border-green-500 p-3 rounded-lg opacity-80">
                  <div className="font-medium text-gray-900 text-sm mb-1 flex items-center gap-2">
                    Campagne Social Media
                    <CheckCircle2 className="h-4 w-4 text-green-500" />
                  </div>
                  <div className="text-xs text-gray-500 mb-2">Agence Pulse Media</div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-green-600 font-medium">12 500€</span>
                    <span className="text-xs text-gray-400">Hier</span>
                  </div>
                </div>
                <div className="bg-green-50 border-l-4 border-green-500 p-3 rounded-lg opacity-80">
                  <div className="font-medium text-gray-900 text-sm mb-1 flex items-center gap-2">
                    Site vitrine
                    <CheckCircle2 className="h-4 w-4 text-green-500" />
                  </div>
                  <div className="text-xs text-gray-500 mb-2">Maison Éditions</div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-green-600 font-medium">8 000€</span>
                    <span className="text-xs text-gray-400">Lun.</span>
                  </div>
                </div>
              </div>
            </motion.div>
          </div>

          {/* Sidebar */}
          <motion.div 
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.8 }}
            className="space-y-4"
          >
            {/* Pipeline */}
            <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-gray-900">Pipeline</h3>
                <span className="text-sm text-green-600 font-medium">66 000€</span>
              </div>
              <div className="space-y-3">
                <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                  <div>
                    <div className="font-medium text-sm text-gray-900">Refonte e-commerce</div>
                    <div className="text-xs text-gray-500">Retail Plus • 80%</div>
                  </div>
                  <span className="font-semibold text-green-600">25 000€</span>
                </div>
                <div className="flex items-center justify-between p-3 bg-yellow-50 rounded-lg">
                  <div>
                    <div className="font-medium text-sm text-gray-900">App mobile MVP</div>
                    <div className="text-xs text-gray-500">StartupLab • 50%</div>
                  </div>
                  <span className="font-semibold text-yellow-600">18 000€</span>
                </div>
                <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
                  <div>
                    <div className="font-medium text-sm text-gray-900">Brand identity</div>
                    <div className="text-xs text-gray-500">Groupe Nexus • 30%</div>
                  </div>
                  <span className="font-semibold text-blue-600">15 000€</span>
                </div>
                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div>
                    <div className="font-medium text-sm text-gray-900">Consulting UX</div>
                    <div className="text-xs text-gray-500">TechVentures • 20%</div>
                  </div>
                  <span className="font-semibold text-gray-600">8 000€</span>
                </div>
              </div>
            </div>

            {/* Recent Activity */}
            <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-gray-900">Activité récente</h3>
                <button className="text-xs text-purple-600 font-medium">Voir tout</button>
              </div>
              <div className="space-y-3">
                <div className="flex items-start gap-3">
                  <div className="h-8 w-8 bg-green-100 rounded-full flex items-center justify-center flex-shrink-0">
                    <CheckCircle2 className="h-4 w-4 text-green-600" />
                  </div>
                  <div>
                    <div className="text-sm text-gray-900">Deal converti</div>
                    <div className="text-xs text-gray-500">Refonte site Maison Éditions</div>
                    <div className="text-xs text-gray-400">Il y a 2h</div>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <div className="h-8 w-8 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
                    <Mail className="h-4 w-4 text-blue-600" />
                  </div>
                  <div>
                    <div className="text-sm text-gray-900">Email synchronisé</div>
                    <div className="text-xs text-gray-500">Nouveau lead depuis Gmail</div>
                    <div className="text-xs text-gray-400">Il y a 4h</div>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <div className="h-8 w-8 bg-purple-100 rounded-full flex items-center justify-center flex-shrink-0">
                    <FileText className="h-4 w-4 text-purple-600" />
                  </div>
                  <div>
                    <div className="text-sm text-gray-900">Fichier Drive lié</div>
                    <div className="text-xs text-gray-500">Brief_Creative_V2.pdf</div>
                    <div className="text-xs text-gray-400">Hier</div>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </main>

      {/* Demo Banner */}
      <div className="fixed bottom-0 left-0 right-0 bg-gradient-to-r from-purple-600 to-pink-500 text-white py-4 px-6 z-50">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <span className="text-sm font-medium flex items-center gap-1.5"><Target className="h-4 w-4" /> Ceci est une démo interactive de Radar</span>
            <span className="text-sm opacity-80">Données fictives pour illustration</span>
          </div>
          <Link 
            href="/"
            className="flex items-center gap-2 bg-white text-purple-600 px-4 py-2 rounded-lg font-medium text-sm hover:bg-purple-50 transition-colors"
          >
            Créer mon espace
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </div>
    </div>
  );
}
