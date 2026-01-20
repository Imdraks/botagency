"""
Pydantic Schemas for Workspace
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum


class WorkspaceRole(str, Enum):
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


# ============================================================================
# WORKSPACE
# ============================================================================

class WorkspaceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)


class WorkspaceCreate(WorkspaceBase):
    """Create a new workspace"""
    drive_root_folder_id: Optional[str] = None
    templates_folder_id: Optional[str] = None
    brief_template_doc_id: Optional[str] = None
    report_template_sheet_id: Optional[str] = None
    devis_template_doc_id: Optional[str] = None
    calendar_id: Optional[str] = None


class WorkspaceUpdate(BaseModel):
    """Update workspace settings"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    drive_root_folder_id: Optional[str] = None
    templates_folder_id: Optional[str] = None
    brief_template_doc_id: Optional[str] = None
    report_template_sheet_id: Optional[str] = None
    devis_template_doc_id: Optional[str] = None
    calendar_id: Optional[str] = None
    settings: Optional[dict] = None


class WorkspaceMemberResponse(BaseModel):
    id: int
    user_id: int
    role: WorkspaceRole
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    user_avatar: Optional[str] = None
    invited_at: Optional[datetime] = None
    accepted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class WorkspaceResponse(BaseModel):
    id: int
    name: str
    owner_user_id: int
    owner_name: Optional[str] = None
    
    # Google Drive
    drive_root_folder_id: Optional[str] = None
    drive_url: Optional[str] = None
    templates_folder_id: Optional[str] = None
    
    # Templates
    brief_template_doc_id: Optional[str] = None
    report_template_sheet_id: Optional[str] = None
    devis_template_doc_id: Optional[str] = None
    
    # Calendar
    calendar_id: Optional[str] = None
    
    # Settings
    settings: Optional[dict] = None
    
    # Members count
    members_count: int = 0
    
    # Timestamps
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WorkspaceDetailResponse(WorkspaceResponse):
    """Detailed response with members"""
    members: List[WorkspaceMemberResponse] = []


class WorkspaceListResponse(BaseModel):
    items: List[WorkspaceResponse]
    total: int


# ============================================================================
# WORKSPACE MEMBER
# ============================================================================

class WorkspaceMemberCreate(BaseModel):
    """Add a member to workspace"""
    user_email: str = Field(..., description="Email of user to invite")
    role: WorkspaceRole = WorkspaceRole.MEMBER


class WorkspaceMemberUpdate(BaseModel):
    """Update member role"""
    role: WorkspaceRole


# ============================================================================
# GOOGLE DRIVE STRUCTURE
# ============================================================================

class DriveStructureRequest(BaseModel):
    """Request to create/verify Drive structure"""
    create_if_missing: bool = True


class DriveStructureResponse(BaseModel):
    """Response with Drive folder structure"""
    success: bool
    root_folder_id: Optional[str] = None
    root_folder_url: Optional[str] = None
    folders: dict = {}  # {"Clients": "folder_id", "Templates": "folder_id", ...}
    errors: List[str] = []


class DriveFolderCreate(BaseModel):
    """Create a folder in Drive"""
    name: str
    parent_folder_id: Optional[str] = None


class DriveDocCreate(BaseModel):
    """Create a Doc from template"""
    template_id: str
    name: str
    parent_folder_id: Optional[str] = None
