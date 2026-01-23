"""
Subscription API - Plans, Packs & Features
==========================================

Endpoints for managing workspace subscriptions, checking feature access,
and handling plan upgrades/downgrades.
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.api.deps import get_db, get_current_user, get_current_admin_user
from app.db.models.workspace import Workspace, WorkspaceMember
from app.db.models.user import User
from app.core.subscription import (
    Plan, Pack, Addon, Feature,
    PLAN_CONFIGS, ADDON_CONFIGS, PACK_FEATURES, ADDON_FEATURES,
    get_plan_features, get_workspace_features, is_feature_available, get_upgrade_message,
    EXTRA_SEAT_PRICE, NAV_SECTIONS, ADMIN_ONLY_FEATURES
)
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/subscription", tags=["Subscription"])


# ============================================================================
# SCHEMAS
# ============================================================================

class PlanInfo(BaseModel):
    name: str
    display_name: str
    description: str
    price_monthly: int
    included_packs: List[str]
    included_addons: List[str]
    max_seats: int
    features_bullets: List[str]
    is_current: bool = False
    is_recommended: bool = False


class AddonInfo(BaseModel):
    name: str
    display_name: str
    description: str
    price_monthly: int
    features: List[str]
    is_active: bool = False
    included_in_plan: bool = False


class FeatureAccess(BaseModel):
    feature: str
    available: bool
    locked_reason: Optional[str] = None
    upgrade_path: Optional[str] = None


class WorkspaceSubscription(BaseModel):
    workspace_id: int
    workspace_name: str
    plan: str
    plan_display_name: str
    enabled_packs: List[str]
    addons: List[str]
    max_seats: int
    current_seats: int
    available_features: List[str]
    plan_expires_at: Optional[str] = None


class NavItemResponse(BaseModel):
    label: str
    path: str
    icon: str
    available: bool
    locked: bool
    admin_only: bool
    upgrade_message: Optional[str] = None


class NavigationResponse(BaseModel):
    sections: Dict[str, List[NavItemResponse]]


class ChangePlanRequest(BaseModel):
    plan: str


class ToggleAddonRequest(BaseModel):
    addon: str
    enable: bool


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_workspace_for_user(
    db: Session,
    user: User,
    workspace_id: Optional[int] = None
) -> Workspace:
    """Get workspace for user, checking membership"""
    if workspace_id:
        workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    else:
        # Get first workspace user is member of
        member = db.query(WorkspaceMember).filter(
            WorkspaceMember.user_id == user.id
        ).first()
        if member:
            workspace = db.query(Workspace).filter(Workspace.id == member.workspace_id).first()
        else:
            workspace = None
    
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace non trouvé")
    
    # Check user is member
    is_member = db.query(WorkspaceMember).filter(
        WorkspaceMember.workspace_id == workspace.id,
        WorkspaceMember.user_id == user.id
    ).first()
    
    if not is_member and workspace.owner_user_id != user.id:
        raise HTTPException(status_code=403, detail="Accès non autorisé à ce workspace")
    
    return workspace


def is_workspace_admin(db: Session, user: User, workspace: Workspace) -> bool:
    """Check if user is admin of workspace"""
    if workspace.owner_user_id == user.id:
        return True
    
    member = db.query(WorkspaceMember).filter(
        WorkspaceMember.workspace_id == workspace.id,
        WorkspaceMember.user_id == user.id
    ).first()
    
    return member and member.role.value == "admin"


# ============================================================================
# PUBLIC ENDPOINTS (No auth required)
# ============================================================================

@router.get("/plans", response_model=List[PlanInfo])
async def get_available_plans():
    """
    📋 Get All Available Plans
    
    Returns all subscription plans with their features and pricing.
    Public endpoint - no auth required.
    """
    plans = []
    for plan, config in PLAN_CONFIGS.items():
        plans.append(PlanInfo(
            name=config.name,
            display_name=config.display_name,
            description=config.description,
            price_monthly=config.price_monthly,
            included_packs=[p.value for p in config.included_packs],
            included_addons=[a.value for a in config.included_addons],
            max_seats=config.max_seats,
            features_bullets=config.features_bullets,
            is_current=False,
            is_recommended=(plan == Plan.STANDARD),
        ))
    return plans


@router.get("/addons", response_model=List[AddonInfo])
async def get_available_addons():
    """
    📦 Get All Available Add-ons
    
    Returns all add-ons with their features and pricing.
    Public endpoint - no auth required.
    """
    addons = []
    for addon, config in ADDON_CONFIGS.items():
        addons.append(AddonInfo(
            name=config.name,
            display_name=config.display_name,
            description=config.description,
            price_monthly=config.price_monthly,
            features=config.features,
            is_active=False,
            included_in_plan=False,
        ))
    return addons


# ============================================================================
# AUTHENTICATED ENDPOINTS
# ============================================================================

@router.get("/current", response_model=WorkspaceSubscription)
async def get_current_subscription(
    workspace_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    📊 Get Current Workspace Subscription
    
    Returns the subscription details for the current workspace.
    """
    workspace = get_workspace_for_user(db, current_user, workspace_id)
    
    # Get current seat count
    seat_count = db.query(WorkspaceMember).filter(
        WorkspaceMember.workspace_id == workspace.id
    ).count()
    
    # Get plan config
    plan = Plan(workspace.plan) if workspace.plan else Plan.STANDARD
    plan_config = PLAN_CONFIGS.get(plan, PLAN_CONFIGS[Plan.STANDARD])
    
    # Calculate available features from workspace's actual enabled_packs and addons
    # This respects the workspace's specific configuration, not just the plan defaults
    features = get_workspace_features(
        workspace.enabled_packs or [],
        workspace.addons or []
    )
    
    return WorkspaceSubscription(
        workspace_id=workspace.id,
        workspace_name=workspace.name,
        plan=workspace.plan or "standard",
        plan_display_name=plan_config.display_name,
        enabled_packs=workspace.enabled_packs or [],
        addons=workspace.addons or [],
        max_seats=workspace.max_seats or plan_config.max_seats,
        current_seats=seat_count,
        available_features=[f.value for f in features],
        plan_expires_at=workspace.plan_expires_at.isoformat() if workspace.plan_expires_at else None,
    )


@router.get("/features/{feature}", response_model=FeatureAccess)
async def check_feature_access(
    feature: str,
    workspace_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    🔐 Check Feature Access
    
    Check if a specific feature is available for the current workspace.
    """
    workspace = get_workspace_for_user(db, current_user, workspace_id)
    is_admin = is_workspace_admin(db, current_user, workspace)
    
    try:
        feature_enum = Feature(feature)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Feature inconnue: {feature}")
    
    plan = Plan(workspace.plan) if workspace.plan else Plan.STANDARD
    addons = [Addon(a) for a in (workspace.addons or [])]
    
    available = is_feature_available(feature_enum, plan, addons, is_admin)
    
    if available:
        return FeatureAccess(feature=feature, available=True)
    else:
        return FeatureAccess(
            feature=feature,
            available=False,
            locked_reason="Fonctionnalité non disponible avec votre plan actuel",
            upgrade_path=get_upgrade_message(feature_enum, plan),
        )


@router.get("/navigation", response_model=NavigationResponse)
async def get_navigation_config(
    workspace_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    🧭 Get Navigation Configuration
    
    Returns the navigation items with their availability status
    based on the current workspace subscription.
    """
    workspace = get_workspace_for_user(db, current_user, workspace_id)
    is_admin = is_workspace_admin(db, current_user, workspace)
    
    plan = Plan(workspace.plan) if workspace.plan else Plan.STANDARD
    addons = [Addon(a) for a in (workspace.addons or [])]
    available_features = get_plan_features(plan, addons)
    
    result = {}
    
    for section_name, items in NAV_SECTIONS.items():
        section_items = []
        for item in items:
            # Skip admin-only items for non-admins
            if item.admin_only and not is_admin:
                continue
            
            # Determine availability
            if item.feature:
                if item.feature in ADMIN_ONLY_FEATURES:
                    available = is_admin
                    locked = not is_admin
                else:
                    available = item.feature in available_features
                    locked = not available
            else:
                available = True
                locked = False
            
            section_items.append(NavItemResponse(
                label=item.label,
                path=item.path,
                icon=item.icon,
                available=available,
                locked=locked,
                admin_only=item.admin_only,
                upgrade_message=get_upgrade_message(item.feature, plan) if locked and item.feature else None,
            ))
        
        if section_items:
            result[section_name] = section_items
    
    return NavigationResponse(sections=result)


# ============================================================================
# ADMIN ENDPOINTS (Workspace admin only)
# ============================================================================

@router.post("/change-plan", response_model=WorkspaceSubscription)
async def change_plan(
    request: ChangePlanRequest,
    workspace_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    ⬆️ Change Subscription Plan
    
    Upgrade or downgrade the workspace plan.
    Only workspace admins can change the plan.
    """
    workspace = get_workspace_for_user(db, current_user, workspace_id)
    
    if not is_workspace_admin(db, current_user, workspace):
        raise HTTPException(status_code=403, detail="Seuls les admins peuvent changer le plan")
    
    try:
        new_plan = Plan(request.plan)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Plan inconnu: {request.plan}")
    
    plan_config = PLAN_CONFIGS[new_plan]
    
    # Update workspace
    old_plan = workspace.plan
    workspace.plan = new_plan.value
    workspace.enabled_packs = [p.value for p in plan_config.included_packs]
    workspace.max_seats = plan_config.max_seats
    
    # If upgrading to premium, add included addons
    if new_plan == Plan.PREMIUM:
        workspace.addons = [a.value for a in plan_config.included_addons]
    
    db.commit()
    db.refresh(workspace)
    
    logger.info(f"Workspace {workspace.id} plan changed: {old_plan} -> {new_plan.value}")
    
    # Return updated subscription
    return await get_current_subscription(workspace.id, db, current_user)


@router.post("/toggle-addon", response_model=WorkspaceSubscription)
async def toggle_addon(
    request: ToggleAddonRequest,
    workspace_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    📦 Toggle Add-on
    
    Enable or disable an add-on for the workspace.
    Only workspace admins can manage add-ons.
    """
    workspace = get_workspace_for_user(db, current_user, workspace_id)
    
    if not is_workspace_admin(db, current_user, workspace):
        raise HTTPException(status_code=403, detail="Seuls les admins peuvent gérer les add-ons")
    
    try:
        addon = Addon(request.addon)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Add-on inconnu: {request.addon}")
    
    # Check if addon is already included in plan
    plan = Plan(workspace.plan) if workspace.plan else Plan.STANDARD
    if addon in PLAN_CONFIGS[plan].included_addons:
        raise HTTPException(
            status_code=400, 
            detail=f"L'add-on {addon.value} est déjà inclus dans votre plan {plan.value}"
        )
    
    current_addons = workspace.addons or []
    
    if request.enable:
        if addon.value not in current_addons:
            current_addons.append(addon.value)
            logger.info(f"Workspace {workspace.id}: addon {addon.value} enabled")
    else:
        if addon.value in current_addons:
            current_addons.remove(addon.value)
            logger.info(f"Workspace {workspace.id}: addon {addon.value} disabled")
    
    workspace.addons = current_addons
    db.commit()
    db.refresh(workspace)
    
    return await get_current_subscription(workspace.id, db, current_user)


# ============================================================================
# SUPER ADMIN ENDPOINTS - Manage any workspace
# ============================================================================

class AdminUpdateSubscriptionRequest(BaseModel):
    plan: Optional[str] = None
    enabled_packs: Optional[List[str]] = None
    addons: Optional[List[str]] = None
    max_seats: Optional[int] = None


@router.get("/admin/workspace/{workspace_id}", response_model=WorkspaceSubscription)
async def admin_get_workspace_subscription(
    workspace_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    """
    🔑 [ADMIN] Get workspace subscription details
    """
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace non trouvé")
    
    # Count seats
    members_count = db.query(WorkspaceMember).filter(
        WorkspaceMember.workspace_id == workspace_id
    ).count()
    
    plan = Plan(workspace.plan) if workspace.plan else Plan.STANDARD
    # Use workspace's actual enabled_packs and addons
    available_features = [f.value for f in get_workspace_features(
        workspace.enabled_packs or [],
        workspace.addons or []
    )]
    
    return WorkspaceSubscription(
        workspace_id=workspace.id,
        workspace_name=workspace.name,
        plan=workspace.plan or "standard",
        plan_display_name=PLAN_CONFIGS[plan].display_name,
        enabled_packs=workspace.enabled_packs or [],
        addons=workspace.addons or [],
        max_seats=workspace.max_seats or 10,
        current_seats=members_count,
        available_features=available_features,
        plan_expires_at=workspace.plan_expires_at.isoformat() if workspace.plan_expires_at else None
    )


@router.post("/admin/migrate-workspaces")
async def admin_migrate_all_workspaces(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    """
    🔑 [ADMIN] Migrate all workspaces to have correct packs based on their plan
    
    This is a one-time migration for workspaces created before the subscription system.
    It applies the default packs/addons for each workspace's current plan.
    """
    workspaces = db.query(Workspace).all()
    migrated = []
    
    for workspace in workspaces:
        old_packs = workspace.enabled_packs or []
        old_addons = workspace.addons or []
        
        # Get plan config
        plan = Plan(workspace.plan) if workspace.plan else Plan.STANDARD
        plan_config = PLAN_CONFIGS[plan]
        
        # Apply plan's default packs and addons
        workspace.enabled_packs = [p.value for p in plan_config.included_packs]
        workspace.addons = [a.value for a in plan_config.included_addons]
        workspace.max_seats = workspace.max_seats or plan_config.max_seats
        
        migrated.append({
            "workspace_id": workspace.id,
            "workspace_name": workspace.name,
            "plan": workspace.plan,
            "old_packs": old_packs,
            "new_packs": workspace.enabled_packs,
            "old_addons": old_addons,
            "new_addons": workspace.addons,
        })
    
    db.commit()
    
    logger.info(f"Admin {admin.id} migrated {len(migrated)} workspaces")
    
    return {
        "message": f"Migré {len(migrated)} workspaces",
        "migrated": migrated
    }


@router.patch("/admin/workspace/{workspace_id}", response_model=WorkspaceSubscription)
async def admin_update_workspace_subscription(
    workspace_id: int,
    request: AdminUpdateSubscriptionRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    """
    🔑 [ADMIN] Update workspace subscription
    
    Allows super admin to modify any workspace's plan, packs, addons, seats.
    When changing plan, automatically applies the plan's default packs and addons.
    """
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace non trouvé")
    
    if request.plan is not None:
        try:
            new_plan = Plan(request.plan)
            workspace.plan = request.plan
            
            # Auto-apply plan's default packs and addons
            plan_config = PLAN_CONFIGS[new_plan]
            workspace.enabled_packs = [p.value for p in plan_config.included_packs]
            workspace.addons = [a.value for a in plan_config.included_addons]
            workspace.max_seats = plan_config.max_seats
            
            logger.info(f"Plan changed to {request.plan}, applied packs: {workspace.enabled_packs}, addons: {workspace.addons}")
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Plan inconnu: {request.plan}")
    
    # Allow manual override of packs (after plan change)
    if request.enabled_packs is not None:
        valid_packs = [p.value for p in Pack]
        for pack in request.enabled_packs:
            if pack not in valid_packs:
                raise HTTPException(status_code=400, detail=f"Pack inconnu: {pack}")
        workspace.enabled_packs = request.enabled_packs
    
    if request.addons is not None:
        valid_addons = [a.value for a in Addon]
        for addon in request.addons:
            if addon not in valid_addons:
                raise HTTPException(status_code=400, detail=f"Addon inconnu: {addon}")
        workspace.addons = request.addons
    
    if request.max_seats is not None:
        if request.max_seats < 1:
            raise HTTPException(status_code=400, detail="Le nombre de sièges doit être >= 1")
        workspace.max_seats = request.max_seats
    
    db.commit()
    db.refresh(workspace)
    
    logger.info(f"Admin {admin.id} updated workspace {workspace_id} subscription")
    
    return await admin_get_workspace_subscription(workspace_id, db, admin)


@router.get("/pricing", response_model=Dict[str, Any])
async def get_pricing_info():
    """
    💰 Get Pricing Information
    
    Returns complete pricing information for plans and add-ons.
    Public endpoint.
    """
    return {
        "plans": {
            plan.value: {
                "name": config.display_name,
                "price": config.price_monthly,
                "max_seats": config.max_seats,
                "description": config.description,
                "bullets": config.features_bullets,
            }
            for plan, config in PLAN_CONFIGS.items()
        },
        "addons": {
            addon.value: {
                "name": config.display_name,
                "price": config.price_monthly,
                "description": config.description,
                "included_in": [p.value for p in config.included_in_plans],
            }
            for addon, config in ADDON_CONFIGS.items()
        },
        "extra_seat_price": EXTRA_SEAT_PRICE,
        "currency": "EUR",
    }
