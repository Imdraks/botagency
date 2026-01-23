'use client';

import React, { useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  Crown,
  Check,
  X,
  Sparkles,
  Zap,
  Rocket,
  Users,
  ChevronRight,
  Shield,
  Star,
  ArrowRight,
  Loader2,
  Package,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { 
  useSubscriptionStore, 
  Plan, 
  Pack,
  Addon,
  PLAN_CONFIGS 
} from '@/store/subscriptionStore';
import { useAuthStore } from '@/store/auth';
import { toast } from 'sonner';

// ============================================================================
// TYPES
// ============================================================================

interface PlanCardProps {
  plan: Plan;
  config: typeof PLAN_CONFIGS[Plan];
  isCurrentPlan: boolean;
  onSelect: () => void;
  isLoading: boolean;
}

interface PackBadgeProps {
  pack: Pack;
  included: boolean;
}

// ============================================================================
// PACK LABELS & ICONS
// ============================================================================

const PACK_LABELS: Record<Pack, string> = {
  core: 'Core',
  clients: 'Clients',
  leads: 'Leads',
  talents: 'Talents',
  intelligence: 'Intelligence',
};

const PACK_DESCRIPTIONS: Record<Pack, string> = {
  core: 'Pipeline, Projets, Production, Assets, Calendrier',
  clients: 'CRM, Dossiers clients, Historique',
  leads: 'Daily Picks, Kanban, Scoring',
  talents: 'Artistes, Profils, Découverte, Comparaison',
  intelligence: 'Analytics, Veille, Prédictions IA, Carte',
};

// ============================================================================
// COMPONENTS
// ============================================================================

function PackBadge({ pack, included }: PackBadgeProps) {
  return (
    <div className={`
      flex items-center gap-2 px-3 py-2 rounded-lg text-sm
      ${included 
        ? 'bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400 border border-green-200 dark:border-green-800' 
        : 'bg-gray-50 dark:bg-gray-800 text-gray-400 border border-gray-200 dark:border-gray-700'
      }
    `}>
      {included ? (
        <Check className="h-4 w-4" />
      ) : (
        <X className="h-4 w-4" />
      )}
      <span>{PACK_LABELS[pack]}</span>
    </div>
  );
}

function PlanCard({ plan, config, isCurrentPlan, onSelect, isLoading }: PlanCardProps) {
  const planIcons: Record<Plan, React.ReactNode> = {
    mini: <Zap className="h-6 w-6" />,
    standard: <Star className="h-6 w-6" />,
    premium: <Crown className="h-6 w-6" />,
  };
  
  const planColors: Record<Plan, string> = {
    mini: 'from-blue-500 to-cyan-500',
    standard: 'from-purple-500 to-pink-500',
    premium: 'from-amber-500 to-orange-500',
  };
  
  const isRecommended = plan === 'standard';
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="relative"
    >
      {isRecommended && (
        <div className="absolute -top-3 left-1/2 -translate-x-1/2 z-10">
          <Badge className="bg-gradient-to-r from-purple-600 to-pink-500 text-white border-0 px-4 py-1">
            <Sparkles className="h-3 w-3 mr-1" />
            Recommandé
          </Badge>
        </div>
      )}
      
      <Card className={`
        relative overflow-hidden
        ${isRecommended ? 'border-2 border-purple-500 dark:border-purple-400 shadow-xl shadow-purple-500/10' : ''}
        ${isCurrentPlan ? 'ring-2 ring-green-500 dark:ring-green-400' : ''}
      `}>
        {isCurrentPlan && (
          <div className="absolute top-4 right-4">
            <Badge variant="secondary" className="bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400">
              Plan actuel
            </Badge>
          </div>
        )}
        
        <CardHeader className="pb-4">
          <div className={`
            h-14 w-14 rounded-2xl flex items-center justify-center mb-4
            bg-gradient-to-br ${planColors[plan]} text-white shadow-lg
          `}>
            {planIcons[plan]}
          </div>
          
          <CardTitle className="text-2xl capitalize">{plan}</CardTitle>
          <CardDescription>{config.description}</CardDescription>
        </CardHeader>
        
        <CardContent className="space-y-6">
          {/* Seats */}
          <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
            <Users className="h-4 w-4" />
            <span>Jusqu'à {config.maxSeats} {config.maxSeats === 1 ? 'utilisateur' : 'utilisateurs'}</span>
          </div>
          
          {/* Packs included */}
          <div className="space-y-2">
            <p className="text-sm font-medium text-gray-900 dark:text-white">Packs inclus :</p>
            <div className="flex flex-wrap gap-2">
              {(['core', 'clients', 'leads', 'talents', 'intelligence'] as Pack[]).map((pack) => (
                <PackBadge 
                  key={pack} 
                  pack={pack} 
                  included={config.packs.includes(pack)} 
                />
              ))}
            </div>
          </div>
          
          {/* Features highlight */}
          <div className="space-y-2">
            <p className="text-sm font-medium text-gray-900 dark:text-white">Points clés :</p>
            <ul className="space-y-2">
              {config.highlights.map((highlight, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-gray-600 dark:text-gray-400">
                  <Check className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                  <span>{highlight}</span>
                </li>
              ))}
            </ul>
          </div>
          
          {/* CTA */}
          {isCurrentPlan ? (
            <Button
              variant="outline"
              disabled
              className="w-full mt-4"
            >
              Plan actuel
            </Button>
          ) : (
            <Button
              onClick={onSelect}
              disabled={isLoading}
              className={`
                w-full mt-4
                ${isRecommended
                  ? 'bg-gradient-to-r from-purple-600 to-pink-500 hover:from-purple-700 hover:to-pink-600 text-white'
                  : ''
                }
              `}
              variant={isRecommended ? 'default' : 'outline'}
            >
              {isLoading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Changement...
                </>
              ) : (
                <>
                  Sélectionner
                  <ArrowRight className="h-4 w-4 ml-2" />
                </>
              )}
            </Button>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}

// ============================================================================
// MAIN PAGE
// ============================================================================

export default function SubscriptionPage() {
  const { 
    subscription, 
    isLoading, 
    fetchSubscription, 
    changePlan,
    toggleAddon,
    togglePack 
  } = useSubscriptionStore();
  const { user } = useAuthStore();
  const [changingPlan, setChangingPlan] = React.useState<Plan | null>(null);
  const [togglingPack, setTogglingPack] = React.useState<Pack | null>(null);
  
  const isAdmin = user?.role === 'admin';
  
  useEffect(() => {
    fetchSubscription();
  }, [fetchSubscription]);
  
  const handlePlanChange = async (plan: Plan) => {
    if (!isAdmin) {
      toast.error('Seuls les admins peuvent changer de plan');
      return;
    }
    
    setChangingPlan(plan);
    try {
      await changePlan(plan);
      toast.success(`Plan changé vers ${plan}`);
    } catch (error) {
      toast.error('Erreur lors du changement de plan');
    } finally {
      setChangingPlan(null);
    }
  };
  
  const handlePackToggle = async (pack: Pack) => {
    if (!isAdmin) {
      toast.error('Seuls les admins peuvent gérer les packs');
      return;
    }
    
    if (pack === 'core') {
      toast.error('Le pack Core ne peut pas être désactivé');
      return;
    }
    
    const isCurrentlyEnabled = subscription?.enabled_packs?.includes(pack);
    
    setTogglingPack(pack);
    try {
      await togglePack(pack, !isCurrentlyEnabled);
      toast.success(`Pack ${pack} ${isCurrentlyEnabled ? 'désactivé' : 'activé'}`);
    } catch (error) {
      toast.error('Erreur lors de la mise à jour du pack');
    } finally {
      setTogglingPack(null);
    }
  };
  
  const handleAddonToggle = async (addon: Addon) => {
    if (!isAdmin) {
      toast.error('Seuls les admins peuvent gérer les add-ons');
      return;
    }
    
    const isCurrentlyEnabled = subscription?.addons?.includes(addon);
    
    try {
      await toggleAddon(addon, !isCurrentlyEnabled);
      toast.success('Add-on mis à jour');
    } catch (error) {
      toast.error('Erreur lors de la mise à jour de l\'add-on');
    }
  };
  
  const currentPlan = subscription?.plan || 'standard';
  const hasRadarBusiness = subscription?.addons?.includes('radar_business') || currentPlan === 'premium';
  
  if (isLoading && !subscription) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Loader2 className="h-8 w-8 animate-spin text-purple-500" />
      </div>
    );
  }
  
  return (
    <div className="max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div className="text-center">
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            Plans & Tarifs
          </h1>
          <p className="text-gray-500 dark:text-gray-400 max-w-2xl mx-auto">
            Choisissez le plan qui correspond à vos besoins. Tous les plans incluent 
            les fonctionnalités de base et des mises à jour régulières.
          </p>
        </motion.div>
      </div>
      
      {/* Current subscription info */}
      {subscription && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-gradient-to-r from-purple-50 to-pink-50 dark:from-purple-900/20 dark:to-pink-900/20 rounded-2xl p-6 border border-purple-100 dark:border-purple-800"
        >
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <p className="text-sm text-purple-600 dark:text-purple-400 font-medium">Votre abonnement</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white capitalize">
                Plan {subscription.plan}
              </p>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {subscription.enabled_packs.length} pack(s) actif(s) • {subscription.max_seats} place(s)
              </p>
            </div>
            
            <div className="flex items-center gap-2">
              <Shield className="h-5 w-5 text-green-500" />
              <span className="text-sm text-green-600 dark:text-green-400 font-medium">
                Actif
              </span>
            </div>
          </div>
        </motion.div>
      )}
      
      {/* Plans grid */}
      <div className="grid md:grid-cols-3 gap-6">
        {(['mini', 'standard', 'premium'] as Plan[]).map((plan) => (
          <PlanCard
            key={plan}
            plan={plan}
            config={PLAN_CONFIGS[plan]}
            isCurrentPlan={currentPlan === plan}
            onSelect={() => handlePlanChange(plan)}
            isLoading={changingPlan === plan}
          />
        ))}
      </div>
      
      {/* Radar Business Add-on */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
      >
        <Card className={`
          relative overflow-hidden
          ${hasRadarBusiness ? 'border-amber-300 dark:border-amber-600' : ''}
        `}>
          <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-amber-200/30 to-orange-200/30 dark:from-amber-600/10 dark:to-orange-600/10 blur-3xl" />
          
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="h-12 w-12 rounded-xl bg-gradient-to-br from-amber-500 to-orange-500 flex items-center justify-center text-white shadow-lg">
                  <Rocket className="h-6 w-6" />
                </div>
                <div>
                  <CardTitle className="flex items-center gap-2">
                    Radar Business
                    {currentPlan === 'premium' && (
                      <Badge variant="secondary" className="bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400">
                        Inclus Premium
                      </Badge>
                    )}
                  </CardTitle>
                  <CardDescription>
                    Fonctionnalités CRM avancées pour les agences
                  </CardDescription>
                </div>
              </div>
              
              {currentPlan === 'premium' && (
                <Badge variant="secondary" className="bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400">
                  Inclus
                </Badge>
              )}
            </div>
          </CardHeader>
          
          <CardContent>
            <div className="grid sm:grid-cols-3 gap-4 mb-6">
              <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                <Check className="h-4 w-4 text-green-500" />
                <span>Génération de devis</span>
              </div>
              <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                <Check className="h-4 w-4 text-green-500" />
                <span>Factures automatiques</span>
              </div>
              <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                <Check className="h-4 w-4 text-green-500" />
                <span>Suivi des paiements</span>
              </div>
            </div>
            
            {currentPlan !== 'premium' && !hasRadarBusiness && (
              <Button
                asChild
                className="bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600"
              >
                <a href="mailto:contact@radarapp.fr?subject=Demande%20Radar%20Business">
                  Contactez-nous
                  <ChevronRight className="h-4 w-4 ml-2" />
                </a>
              </Button>
            )}
            {hasRadarBusiness && currentPlan !== 'premium' && (
              <Badge variant="secondary" className="bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400">
                Actif
              </Badge>
            )}
          </CardContent>
        </Card>
      </motion.div>
      
      {/* Packs detail */}
      <div className="space-y-4">
        <h2 className="text-xl font-bold text-gray-900 dark:text-white">
          Packs activés
        </h2>
        
        <div className="space-y-3">
          {(['core', 'clients', 'leads', 'talents', 'intelligence'] as Pack[]).map((pack) => {
            const isEnabled = subscription?.enabled_packs?.includes(pack) ?? false;
            const isCore = pack === 'core';
            const isToggling = togglingPack === pack;
            
            return (
              <Card 
                key={pack}
                className={`transition-all ${isEnabled ? 'border-green-200 dark:border-green-800 bg-green-50/50 dark:bg-green-900/10' : ''}`}
              >
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className={`p-2 rounded-lg ${isEnabled ? 'bg-green-100 dark:bg-green-900/30' : 'bg-gray-100 dark:bg-gray-800'}`}>
                        <Package className={`h-5 w-5 ${isEnabled ? 'text-green-600 dark:text-green-400' : 'text-gray-400'}`} />
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-gray-900 dark:text-white">
                            {PACK_LABELS[pack]}
                          </span>
                          {isCore && (
                            <Badge variant="secondary" className="text-[10px]">
                              Obligatoire
                            </Badge>
                          )}
                        </div>
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                          {PACK_DESCRIPTIONS[pack]}
                        </p>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-3">
                      {isToggling ? (
                        <Loader2 className="h-4 w-4 animate-spin text-gray-400" />
                      ) : isEnabled ? (
                        <Check className="h-5 w-5 text-green-500" />
                      ) : null}
                      
                      <Switch
                        checked={isEnabled}
                        onCheckedChange={() => handlePackToggle(pack)}
                        disabled={isCore || !isAdmin || isToggling}
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </div>
      
      {/* Admin notice */}
      {!isAdmin && (
        <div className="text-center p-4 bg-amber-50 dark:bg-amber-900/20 rounded-lg border border-amber-200 dark:border-amber-800">
          <p className="text-sm text-amber-700 dark:text-amber-400">
            Seuls les administrateurs peuvent modifier l'abonnement du workspace.
          </p>
        </div>
      )}
    </div>
  );
}
