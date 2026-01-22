"""
Unified Assets API - Single source of truth for all asset operations

This replaces:
- /agency/assets (from agency_tasks.py)
- /agency/projects/{id}/assets (from project_detail.py)

Both the global /assets page and the project assets tab use this API.
"""
from datetime import datetime
from typing import Optional, List
from enum import Enum
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from pydantic import BaseModel

from app.db.session import get_db
from app.db.models.user import User
from app.db.models.agency import Asset, Project, Client, AssetKind
from app.api.deps import get_current_user
from app.services.google_workspace import get_google_workspace_service, TokenExpiredError
from app.core.cache import cache_get

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/assets", tags=["assets"])


# ============================================================================
# SCHEMAS
# ============================================================================

class AssetTypeEnum(str, Enum):
    DRIVE = "DRIVE"
    FIGMA = "FIGMA"
    DROPBOX = "DROPBOX"
    YOUTUBE = "YOUTUBE"
    LINK = "LINK"
    DOC = "DOC"
    SHEET = "SHEET"
    OTHER = "OTHER"


class AssetStatusEnum(str, Enum):
    DRAFT = "DRAFT"
    FINAL = "FINAL"


class AssetCreateRequest(BaseModel):
    project_id: int
    name: str
    url: str
    type: AssetTypeEnum = AssetTypeEnum.LINK
    version: Optional[str] = None
    status: Optional[AssetStatusEnum] = AssetStatusEnum.DRAFT
    drive_file_id: Optional[str] = None
    drive_folder_id: Optional[str] = None


class AssetUpdateRequest(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    type: Optional[AssetTypeEnum] = None
    version: Optional[str] = None
    status: Optional[AssetStatusEnum] = None
    drive_file_id: Optional[str] = None
    drive_folder_id: Optional[str] = None


class AssetResponse(BaseModel):
    id: int
    project_id: int
    name: str
    url: str
    type: str
    version: Optional[str] = None
    status: Optional[str] = None
    drive_file_id: Optional[str] = None
    drive_folder_id: Optional[str] = None
    created_at: datetime
    created_by: Optional[int] = None
    updated_at: Optional[datetime] = None
    
    # Computed fields (joined from project/client)
    project_name: Optional[str] = None
    client_id: Optional[int] = None
    client_name: Optional[str] = None

    class Config:
        from_attributes = True


class AssetListResponse(BaseModel):
    items: List[AssetResponse]
    total: int
    page: int
    limit: int
    has_more: bool


# ============================================================================
# HELPERS
# ============================================================================

def detect_asset_type(url: str) -> str:
    """Auto-detect asset type from URL"""
    url_lower = url.lower()
    
    if 'drive.google.com' in url_lower:
        return 'DRIVE'
    if 'docs.google.com/document' in url_lower:
        return 'DOC'
    if 'docs.google.com/spreadsheets' in url_lower:
        return 'SHEET'
    if 'figma.com' in url_lower:
        return 'FIGMA'
    if 'dropbox.com' in url_lower:
        return 'DROPBOX'
    if 'youtube.com' in url_lower or 'youtu.be' in url_lower:
        return 'YOUTUBE'
    
    return 'LINK'


def asset_to_response(asset: Asset) -> AssetResponse:
    """Convert Asset model to response schema"""
    return AssetResponse(
        id=asset.id,
        project_id=asset.project_id,
        name=asset.name,
        url=asset.url,
        type=asset.type or detect_asset_type(asset.url),
        version=asset.version,
        status=asset.status,
        drive_file_id=asset.drive_file_id,
        drive_folder_id=asset.drive_folder_id,
        created_at=asset.created_at,
        created_by=asset.created_by,
        updated_at=asset.updated_at,
        project_name=asset.project.name if asset.project else None,
        client_id=asset.project.client_id if asset.project else None,
        client_name=asset.project.client.name if asset.project and asset.project.client else None
    )


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("", response_model=AssetListResponse)
async def list_assets(
    project_id: Optional[int] = Query(None, description="Filter by project ID"),
    client_id: Optional[int] = Query(None, description="Filter by client ID"),
    type: Optional[str] = Query(None, description="Filter by asset type (DRIVE, FIGMA, DOC, etc.)"),
    status: Optional[str] = Query(None, description="Filter by status (DRAFT, FINAL)"),
    version: Optional[str] = Query(None, description="Filter by version"),
    q: Optional[str] = Query(None, description="Search query (name, url, project name, client name)"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all assets with filtering and pagination.
    
    Used by:
    - /assets page (global view)
    - /projects/[id] assets tab (project_id pre-set)
    """
    query = db.query(Asset).join(Project).outerjoin(Client, Project.client_id == Client.id)
    
    # Apply filters
    if project_id:
        query = query.filter(Asset.project_id == project_id)
    
    if client_id:
        query = query.filter(Project.client_id == client_id)
    
    if type:
        query = query.filter(Asset.type == type)
    
    if status:
        query = query.filter(Asset.status == status)
    
    if version:
        query = query.filter(Asset.version == version)
    
    if q:
        search_term = f"%{q}%"
        query = query.filter(
            or_(
                Asset.name.ilike(search_term),
                Asset.url.ilike(search_term),
                Project.name.ilike(search_term),
                Client.name.ilike(search_term)
            )
        )
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    offset = (page - 1) * limit
    assets = query.order_by(Asset.created_at.desc()).offset(offset).limit(limit).all()
    
    # Build response
    items = [asset_to_response(a) for a in assets]
    
    return AssetListResponse(
        items=items,
        total=total,
        page=page,
        limit=limit,
        has_more=(offset + len(items)) < total
    )


@router.get("/{asset_id}", response_model=AssetResponse)
async def get_asset(
    asset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a single asset by ID"""
    asset = db.query(Asset).join(Project).outerjoin(Client, Project.client_id == Client.id).filter(
        Asset.id == asset_id
    ).first()
    
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    return asset_to_response(asset)


@router.post("", response_model=AssetResponse, status_code=status.HTTP_201_CREATED)
async def create_asset(
    data: AssetCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new asset.
    
    The asset type will be auto-detected from the URL if not provided.
    """
    # Verify project exists
    project = db.query(Project).filter(Project.id == data.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Auto-detect type if not provided or is default
    asset_type = data.type.value if data.type else detect_asset_type(data.url)
    
    # Check for duplicate (same project + url)
    existing = db.query(Asset).filter(
        Asset.project_id == data.project_id,
        Asset.url == data.url
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An asset with this URL already exists for this project"
        )
    
    asset = Asset(
        project_id=data.project_id,
        workspace_id=project.workspace_id,  # Inherit from project
        name=data.name,
        url=data.url,
        type=asset_type,
        version=data.version,
        status=data.status.value if data.status else "DRAFT",
        drive_file_id=data.drive_file_id,
        drive_folder_id=data.drive_folder_id,
        kind=AssetKind.LINK,  # Legacy field
        created_by=current_user.id,
        created_at=datetime.utcnow()
    )
    
    db.add(asset)
    db.commit()
    db.refresh(asset)
    
    # Reload with joins
    asset = db.query(Asset).join(Project).outerjoin(Client, Project.client_id == Client.id).filter(
        Asset.id == asset.id
    ).first()
    
    return asset_to_response(asset)


@router.patch("/{asset_id}", response_model=AssetResponse)
async def update_asset(
    asset_id: int,
    data: AssetUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an existing asset"""
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    # Update fields if provided
    if data.name is not None:
        asset.name = data.name
    
    if data.url is not None:
        asset.url = data.url
        # Re-detect type if URL changed and type not explicitly set
        if data.type is None:
            asset.type = detect_asset_type(data.url)
    
    if data.type is not None:
        asset.type = data.type.value
    
    if data.version is not None:
        asset.version = data.version
    
    if data.status is not None:
        asset.status = data.status.value
    
    if data.drive_file_id is not None:
        asset.drive_file_id = data.drive_file_id
    
    if data.drive_folder_id is not None:
        asset.drive_folder_id = data.drive_folder_id
    
    asset.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(asset)
    
    # Reload with joins
    asset = db.query(Asset).join(Project).outerjoin(Client, Project.client_id == Client.id).filter(
        Asset.id == asset.id
    ).first()
    
    return asset_to_response(asset)


@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_asset(
    asset_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete an asset and move its Drive file to project's 99_Archive folder"""
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    # Get project archive folder info before deletion
    project = db.query(Project).filter(Project.id == asset.project_id).first()
    drive_file_id = asset.drive_file_id
    archive_folder_id = project.drive_folder_archive if project else None
    user_id = current_user.id
    asset_name = asset.name
    
    db.delete(asset)
    db.commit()
    
    # Move file to archive in background if it has a Drive file
    if drive_file_id and archive_folder_id:
        background_tasks.add_task(
            archive_drive_file,
            user_id=user_id,
            file_id=drive_file_id,
            archive_folder_id=archive_folder_id,
            item_name=asset_name,
            item_type="asset"
        )
    
    return None


async def archive_drive_file(
    user_id: int,
    file_id: str,
    archive_folder_id: str,
    item_name: str,
    item_type: str
):
    """Move a Drive file to the project's archive folder"""
    try:
        token_data = await cache_get(f"google_tokens:{user_id}")
        if not token_data:
            logger.warning(f"No Google token for user {user_id}, cannot archive {item_type}")
            return
        
        service = await get_google_workspace_service(token_data)
        
        # Move file to archive folder
        await service.move_file(
            file_id=file_id,
            new_parent_id=archive_folder_id
        )
        
        logger.info(f"Archived {item_type} '{item_name}' to project archive folder")
        
    except Exception as e:
        logger.error(f"Failed to archive {item_type} {item_name}: {e}")
