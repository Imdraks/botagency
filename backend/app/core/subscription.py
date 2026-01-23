"""
Subscription Plans & Packs Configuration
=========================================

This module defines the complete subscription system for Radar:
- Plans: MINI, STANDARD, PREMIUM
- Packs: Core, Clients, Leads, Talents, Intelligence
- Add-ons: Radar Business
- Feature mapping for navigation gating
"""
from enum import Enum
from typing import Dict, List, Set, Optional
from dataclasses import dataclass, field


# ============================================================================
# PLANS
# ============================================================================

class Plan(str, Enum):
    MINI = "mini"
    STANDARD = "standard"
    PREMIUM = "premium"


# ============================================================================
# PACKS
# ============================================================================

class Pack(str, Enum):
    CORE = "core"           # Pipeline, Projets, Production, Assets, Calendrier, Cockpit
    CLIENTS = "clients"     # Clients, Dossiers, Daily Picks
    LEADS = "leads"         # Leads, Kanban Leads, Scoring
    TALENTS = "talents"     # Artistes, Profils, Découverte, Comparaison, Carte
    INTELLIGENCE = "intelligence"  # Analytics, Veille Concur., Prédictions IA


class Addon(str, Enum):
    RADAR_BUSINESS = "radar_business"  # CRM étendu, Devis, Factures


# ============================================================================
# FEATURES (mapped to packs)
# ============================================================================

class Feature(str, Enum):
    # Core
    COCKPIT = "cockpit"
    PIPELINE = "pipeline"
    PROJECTS = "projects"
    PRODUCTION = "production"
    ASSETS = "assets"
    CALENDAR = "calendar"
    
    # Clients
    CLIENTS = "clients"
    DOSSIERS = "dossiers"
    DAILY_PICKS = "daily_picks"
    
    # Leads
    LEADS = "leads"
    KANBAN_LEADS = "kanban_leads"
    SCORING = "scoring"
    
    # Talents
    ARTISTS = "artists"
    PROFILES = "profiles"
    DISCOVERY = "discovery"
    COMPARISON = "comparison"
    MAP = "map"
    
    # Intelligence
    ANALYTICS = "analytics"
    COMPETITOR_WATCH = "competitor_watch"
    AI_PREDICTIONS = "ai_predictions"
    
    # Radar Business (addon)
    CRM_EXTENDED = "crm_extended"
    QUOTES = "quotes"
    INVOICES = "invoices"
    
    # Admin only (always available to admins)
    SOURCES = "sources"
    SOURCE_HEALTH = "source_health"


# ============================================================================
# PACK → FEATURES MAPPING
# ============================================================================

PACK_FEATURES: Dict[Pack, Set[Feature]] = {
    Pack.CORE: {
        Feature.COCKPIT,
        Feature.PIPELINE,
        Feature.PROJECTS,
        Feature.PRODUCTION,
        Feature.ASSETS,
        Feature.CALENDAR,
    },
    Pack.CLIENTS: {
        Feature.CLIENTS,
        Feature.DOSSIERS,
        Feature.DAILY_PICKS,
    },
    Pack.LEADS: {
        Feature.LEADS,
        Feature.KANBAN_LEADS,
        Feature.SCORING,
    },
    Pack.TALENTS: {
        Feature.ARTISTS,
        Feature.PROFILES,
        Feature.DISCOVERY,
        Feature.COMPARISON,
        Feature.MAP,
    },
    Pack.INTELLIGENCE: {
        Feature.ANALYTICS,
        Feature.COMPETITOR_WATCH,
        Feature.AI_PREDICTIONS,
    },
}

ADDON_FEATURES: Dict[Addon, Set[Feature]] = {
    Addon.RADAR_BUSINESS: {
        Feature.CRM_EXTENDED,
        Feature.QUOTES,
        Feature.INVOICES,
    },
}

# Admin-only features (not gated by packs)
ADMIN_ONLY_FEATURES: Set[Feature] = {
    Feature.SOURCES,
    Feature.SOURCE_HEALTH,
}


# ============================================================================
# PLAN CONFIGURATION
# ============================================================================

@dataclass
class PlanConfig:
    """Configuration for a subscription plan"""
    name: str
    display_name: str
    description: str
    price_monthly: int  # in euros
    included_packs: List[Pack]
    included_addons: List[Addon]
    max_seats: int
    features_bullets: List[str]


PLAN_CONFIGS: Dict[Plan, PlanConfig] = {
    Plan.MINI: PlanConfig(
        name="mini",
        display_name="Mini",
        description="L'essentiel pour piloter ton agence.",
        price_monthly=29,
        included_packs=[Pack.CORE, Pack.CLIENTS],
        included_addons=[],
        max_seats=3,
        features_bullets=[
            "Cockpit + Pipeline + Projets + Production",
            "Gestion clients et dossiers",
            "Daily Picks pour ne rien oublier",
        ],
    ),
    Plan.STANDARD: PlanConfig(
        name="standard",
        display_name="Standard",
        description="Le plan que 80% des agences choisissent.",
        price_monthly=79,
        included_packs=[Pack.CORE, Pack.CLIENTS, Pack.LEADS, Pack.TALENTS],
        included_addons=[],
        max_seats=10,
        features_bullets=[
            "Tout Mini inclus",
            "Leads + Kanban + Scoring",
            "Artistes, Profils, Découverte, Comparaison",
        ],
    ),
    Plan.PREMIUM: PlanConfig(
        name="premium",
        display_name="Premium",
        description="Radar complet. Zéro limite.",
        price_monthly=149,
        included_packs=[Pack.CORE, Pack.CLIENTS, Pack.LEADS, Pack.TALENTS, Pack.INTELLIGENCE],
        included_addons=[Addon.RADAR_BUSINESS],
        max_seats=999,  # Unlimited
        features_bullets=[
            "Tout Standard inclus",
            "Analytics, Veille Concur., Prédictions IA",
            "Radar Business inclus (devis + factures)",
        ],
    ),
}


# ============================================================================
# ADDON CONFIGURATION
# ============================================================================

@dataclass
class AddonConfig:
    """Configuration for an add-on"""
    name: str
    display_name: str
    description: str
    price_monthly: int
    features: List[str]
    included_in_plans: List[Plan]  # Plans where it's included for free


ADDON_CONFIGS: Dict[Addon, AddonConfig] = {
    Addon.RADAR_BUSINESS: AddonConfig(
        name="radar_business",
        display_name="Radar Business",
        description="Devis + Factures conformes 2026. Intégré à tes clients et projets.",
        price_monthly=49,
        features=[
            "Création et envoi de devis",
            "Facturation conforme 2026",
            "Historique commercial enrichi",
        ],
        included_in_plans=[Plan.PREMIUM],
    ),
}


# ============================================================================
# SEAT PRICING
# ============================================================================

EXTRA_SEAT_PRICE = 15  # €/month per additional seat


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_plan_packs(plan: Plan) -> List[Pack]:
    """Get packs included in a plan"""
    return PLAN_CONFIGS[plan].included_packs


def get_plan_addons(plan: Plan) -> List[Addon]:
    """Get addons included for free in a plan"""
    return PLAN_CONFIGS[plan].included_addons


def get_plan_features(plan: Plan, addons: List[Addon] = None) -> Set[Feature]:
    """Get all features available for a plan + addons"""
    features = set()
    
    # Features from included packs
    for pack in PLAN_CONFIGS[plan].included_packs:
        features.update(PACK_FEATURES.get(pack, set()))
    
    # Features from included addons (free in plan)
    for addon in PLAN_CONFIGS[plan].included_addons:
        features.update(ADDON_FEATURES.get(addon, set()))
    
    # Features from purchased addons
    if addons:
        for addon in addons:
            if isinstance(addon, str):
                addon = Addon(addon)
            features.update(ADDON_FEATURES.get(addon, set()))
    
    return features


def get_pack_from_feature(feature: Feature) -> Optional[Pack]:
    """Find which pack contains a feature"""
    for pack, pack_features in PACK_FEATURES.items():
        if feature in pack_features:
            return pack
    return None


def get_addon_from_feature(feature: Feature) -> Optional[Addon]:
    """Find which addon contains a feature"""
    for addon, addon_features in ADDON_FEATURES.items():
        if feature in addon_features:
            return addon
    return None


def is_feature_available(
    feature: Feature,
    plan: Plan,
    addons: List[Addon] = None,
    is_admin: bool = False
) -> bool:
    """Check if a feature is available for a given plan/addons combination"""
    # Admin-only features
    if feature in ADMIN_ONLY_FEATURES:
        return is_admin
    
    available_features = get_plan_features(plan, addons)
    return feature in available_features


def get_upgrade_message(feature: Feature, current_plan: Plan) -> str:
    """Get upgrade message for a locked feature"""
    pack = get_pack_from_feature(feature)
    addon = get_addon_from_feature(feature)
    
    if addon:
        addon_config = ADDON_CONFIGS[addon]
        if current_plan in addon_config.included_in_plans:
            return "Disponible avec votre plan"
        return f"Disponible avec l'add-on {addon_config.display_name}"
    
    if pack:
        # Find minimum plan that includes this pack
        for plan in [Plan.MINI, Plan.STANDARD, Plan.PREMIUM]:
            if pack in PLAN_CONFIGS[plan].included_packs:
                if plan.value > current_plan.value:
                    return f"Disponible avec le plan {PLAN_CONFIGS[plan].display_name}"
                break
    
    return "Passez à un plan supérieur"


# ============================================================================
# FEATURE TO ROUTE MAPPING (for navigation gating)
# ============================================================================

FEATURE_ROUTES: Dict[str, Feature] = {
    # Core
    "/cockpit": Feature.COCKPIT,
    "/pipeline": Feature.PIPELINE,
    "/projects": Feature.PROJECTS,
    "/production": Feature.PRODUCTION,
    "/assets": Feature.ASSETS,
    "/calendar": Feature.CALENDAR,
    "/today": Feature.COCKPIT,  # Today is part of Cockpit
    
    # Clients
    "/clients": Feature.CLIENTS,
    "/dossiers": Feature.DOSSIERS,
    
    # Leads
    "/leads": Feature.LEADS,
    "/opportunities": Feature.LEADS,
    
    # Talents
    "/artists": Feature.ARTISTS,
    "/profiles": Feature.PROFILES,
    "/discovery": Feature.DISCOVERY,
    "/comparison": Feature.COMPARISON,
    "/map": Feature.MAP,
    
    # Intelligence
    "/analytics": Feature.ANALYTICS,
    "/competitor-watch": Feature.COMPETITOR_WATCH,
    "/predictions": Feature.AI_PREDICTIONS,
    
    # Radar Business
    "/quotes": Feature.QUOTES,
    "/invoices": Feature.INVOICES,
    
    # Admin
    "/sources": Feature.SOURCES,
    "/source-health": Feature.SOURCE_HEALTH,
}


# ============================================================================
# NAVIGATION ITEMS CONFIG (for sidebar rendering)
# ============================================================================

@dataclass
class NavItem:
    """Navigation item configuration"""
    label: str
    path: str
    icon: str
    feature: Optional[Feature] = None
    admin_only: bool = False
    badge: Optional[str] = None


NAV_SECTIONS = {
    "main": [
        NavItem("Aujourd'hui", "/today", "CalendarDays", Feature.COCKPIT),
        NavItem("Cockpit", "/cockpit", "LayoutDashboard", Feature.COCKPIT),
        NavItem("Inbox", "/inbox", "Inbox", Feature.COCKPIT),
    ],
    "business": [
        NavItem("Pipeline", "/pipeline", "TrendingUp", Feature.PIPELINE),
        NavItem("Clients", "/clients", "Users", Feature.CLIENTS),
        NavItem("Leads", "/leads", "Target", Feature.LEADS),
    ],
    "production": [
        NavItem("Projets", "/projects", "FolderKanban", Feature.PROJECTS),
        NavItem("Production", "/production", "Clapperboard", Feature.PRODUCTION),
        NavItem("Assets", "/assets", "Image", Feature.ASSETS),
        NavItem("Calendrier", "/calendar", "Calendar", Feature.CALENDAR),
    ],
    "talents": [
        NavItem("Artistes", "/artists", "Music", Feature.ARTISTS),
        NavItem("Découverte", "/discovery", "Sparkles", Feature.DISCOVERY),
        NavItem("Profils", "/profiles", "UserCircle", Feature.PROFILES),
        NavItem("Comparaison", "/comparison", "GitCompare", Feature.COMPARISON),
    ],
    "intelligence": [
        NavItem("Analytics", "/analytics", "BarChart3", Feature.ANALYTICS),
        NavItem("Veille", "/competitor-watch", "Eye", Feature.COMPETITOR_WATCH),
        NavItem("Prédictions", "/predictions", "Brain", Feature.AI_PREDICTIONS),
    ],
    "admin": [
        NavItem("Sources", "/sources", "Database", Feature.SOURCES, admin_only=True),
        NavItem("Source Health", "/source-health", "Activity", Feature.SOURCE_HEALTH, admin_only=True),
    ],
}
