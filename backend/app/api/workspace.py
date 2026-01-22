"""
Workspace API - Multi-user workspace management
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.session import get_db
from app.db.models.user import User
from app.db.models.workspace import Workspace, WorkspaceMember, WorkspaceRole, WorkspaceInvite
from app.api.deps import get_current_user
from app.schemas.workspace import (
    WorkspaceCreate, WorkspaceUpdate, WorkspaceResponse, 
    WorkspaceDetailResponse, WorkspaceListResponse,
    WorkspaceMemberCreate, WorkspaceMemberUpdate, WorkspaceMemberResponse,
    DriveStructureRequest, DriveStructureResponse,
    WorkspaceInviteCreate, WorkspaceInviteResponse, WorkspaceInviteListResponse,
)
from app.services.google_workspace import get_google_workspace_service, GoogleAPIError, TokenExpiredError

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


# ============================================================================
# WORKSPACE CRUD
# ============================================================================

@router.get("", response_model=WorkspaceListResponse)
async def list_workspaces(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all workspaces the user has access to.
    Admins can see ALL workspaces.
    Regular users see owned + member workspaces.
    """
    # Admins see all workspaces
    if current_user.role == 'admin':
        all_workspaces = db.query(Workspace).all()
    else:
        # Get owned workspaces
        owned = db.query(Workspace).filter(
            Workspace.owner_user_id == current_user.id
        ).all()
        
        # Get member workspaces
        member_workspace_ids = db.query(WorkspaceMember.workspace_id).filter(
            WorkspaceMember.user_id == current_user.id
        ).subquery()
        
        member_of = db.query(Workspace).filter(
            Workspace.id.in_(member_workspace_ids),
            Workspace.owner_user_id != current_user.id
        ).all()
        
        all_workspaces = owned + member_of
    
    # Build response with member counts
    items = []
    for ws in all_workspaces:
        members_count = db.query(func.count(WorkspaceMember.id)).filter(
            WorkspaceMember.workspace_id == ws.id
        ).scalar() or 0
        
        owner = db.query(User).filter(User.id == ws.owner_user_id).first()
        
        items.append(WorkspaceResponse(
            id=ws.id,
            name=ws.name,
            owner_user_id=ws.owner_user_id,
            owner_name=owner.full_name if owner else None,
            drive_root_folder_id=ws.drive_root_folder_id,
            drive_url=ws.drive_url,
            templates_folder_id=ws.templates_folder_id,
            brief_template_doc_id=ws.brief_template_doc_id,
            report_template_sheet_id=ws.report_template_sheet_id,
            devis_template_doc_id=ws.devis_template_doc_id,
            calendar_id=ws.calendar_id,
            settings=ws.settings,
            members_count=members_count + 1,  # +1 for owner
            created_at=ws.created_at,
            updated_at=ws.updated_at,
        ))
    
    return WorkspaceListResponse(items=items, total=len(items))


@router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    data: WorkspaceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new workspace. Only admins can create workspaces."""
    # Only admins can create workspaces
    if current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seuls les administrateurs peuvent créer des workspaces"
        )
    workspace = Workspace(
        name=data.name,
        owner_user_id=current_user.id,
        drive_root_folder_id=data.drive_root_folder_id,
        templates_folder_id=data.templates_folder_id,
        brief_template_doc_id=data.brief_template_doc_id,
        report_template_sheet_id=data.report_template_sheet_id,
        devis_template_doc_id=data.devis_template_doc_id,
        calendar_id=data.calendar_id,
    )
    
    db.add(workspace)
    db.commit()
    db.refresh(workspace)
    
    return WorkspaceResponse(
        id=workspace.id,
        name=workspace.name,
        owner_user_id=workspace.owner_user_id,
        owner_name=current_user.full_name,
        drive_root_folder_id=workspace.drive_root_folder_id,
        drive_url=workspace.drive_url,
        calendar_id=workspace.calendar_id,
        members_count=1,
        created_at=workspace.created_at,
        updated_at=workspace.updated_at,
    )


@router.get("/{workspace_id}", response_model=WorkspaceDetailResponse)
async def get_workspace(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get workspace details with members"""
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    # Check access - admins can access all workspaces
    if not _user_has_workspace_access(db, current_user.id, workspace_id, current_user.role):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get members
    members = db.query(WorkspaceMember).filter(
        WorkspaceMember.workspace_id == workspace_id
    ).all()
    
    member_responses = []
    for member in members:
        user = db.query(User).filter(User.id == member.user_id).first()
        member_responses.append(WorkspaceMemberResponse(
            id=member.id,
            user_id=member.user_id,
            role=member.role,
            user_name=user.full_name if user else None,
            user_email=user.email if user else None,
            user_avatar=user.avatar_url if user else None,
            invited_at=member.invited_at,
            accepted_at=member.accepted_at,
        ))
    
    owner = db.query(User).filter(User.id == workspace.owner_user_id).first()
    
    return WorkspaceDetailResponse(
        id=workspace.id,
        name=workspace.name,
        owner_user_id=workspace.owner_user_id,
        owner_name=owner.full_name if owner else None,
        drive_root_folder_id=workspace.drive_root_folder_id,
        drive_url=workspace.drive_url,
        templates_folder_id=workspace.templates_folder_id,
        brief_template_doc_id=workspace.brief_template_doc_id,
        report_template_sheet_id=workspace.report_template_sheet_id,
        devis_template_doc_id=workspace.devis_template_doc_id,
        calendar_id=workspace.calendar_id,
        settings=workspace.settings,
        members_count=len(member_responses) + 1,
        members=member_responses,
        created_at=workspace.created_at,
        updated_at=workspace.updated_at,
    )


@router.patch("/{workspace_id}", response_model=WorkspaceResponse)
async def update_workspace(
    workspace_id: int,
    data: WorkspaceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update workspace settings. Only owner or admin can update."""
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    # Check admin access
    if not _user_is_workspace_admin(db, current_user.id, workspace_id, workspace.owner_user_id):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(workspace, field, value)
    
    db.commit()
    db.refresh(workspace)
    
    members_count = db.query(func.count(WorkspaceMember.id)).filter(
        WorkspaceMember.workspace_id == workspace_id
    ).scalar() or 0
    
    return WorkspaceResponse(
        id=workspace.id,
        name=workspace.name,
        owner_user_id=workspace.owner_user_id,
        drive_root_folder_id=workspace.drive_root_folder_id,
        drive_url=workspace.drive_url,
        templates_folder_id=workspace.templates_folder_id,
        brief_template_doc_id=workspace.brief_template_doc_id,
        report_template_sheet_id=workspace.report_template_sheet_id,
        devis_template_doc_id=workspace.devis_template_doc_id,
        calendar_id=workspace.calendar_id,
        settings=workspace.settings,
        members_count=members_count + 1,
        created_at=workspace.created_at,
        updated_at=workspace.updated_at,
    )


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workspace(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete workspace. Only owner or global admin can delete."""
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    # Allow owner or global admin to delete
    if workspace.owner_user_id != current_user.id and current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Only owner or admin can delete workspace")
    
    # Delete related data first
    db.query(WorkspaceMember).filter(WorkspaceMember.workspace_id == workspace_id).delete()
    db.query(WorkspaceInvite).filter(WorkspaceInvite.workspace_id == workspace_id).delete()
    
    db.delete(workspace)
    db.commit()


# ============================================================================
# MEMBERS
# ============================================================================

@router.post("/{workspace_id}/members", response_model=WorkspaceMemberResponse)
async def add_member(
    workspace_id: int,
    data: WorkspaceMemberCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a member to workspace by email"""
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    # Check admin access
    if not _user_is_workspace_admin(db, current_user.id, workspace_id, workspace.owner_user_id):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Find user by email
    user = db.query(User).filter(User.email == data.user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if already member
    existing = db.query(WorkspaceMember).filter(
        WorkspaceMember.workspace_id == workspace_id,
        WorkspaceMember.user_id == user.id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="User is already a member")
    
    if user.id == workspace.owner_user_id:
        raise HTTPException(status_code=400, detail="Cannot add owner as member")
    
    member = WorkspaceMember(
        workspace_id=workspace_id,
        user_id=user.id,
        role=data.role,
        invited_by=current_user.id,
    )
    
    db.add(member)
    db.commit()
    db.refresh(member)
    
    return WorkspaceMemberResponse(
        id=member.id,
        user_id=member.user_id,
        role=member.role,
        user_name=user.full_name,
        user_email=user.email,
        user_avatar=user.avatar_url,
        invited_at=member.invited_at,
        accepted_at=member.accepted_at,
    )


@router.patch("/{workspace_id}/members/{member_id}", response_model=WorkspaceMemberResponse)
async def update_member(
    workspace_id: int,
    member_id: int,
    data: WorkspaceMemberUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update member role"""
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    if not _user_is_workspace_admin(db, current_user.id, workspace_id, workspace.owner_user_id):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    member = db.query(WorkspaceMember).filter(
        WorkspaceMember.id == member_id,
        WorkspaceMember.workspace_id == workspace_id
    ).first()
    
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    member.role = data.role
    db.commit()
    db.refresh(member)
    
    user = db.query(User).filter(User.id == member.user_id).first()
    
    return WorkspaceMemberResponse(
        id=member.id,
        user_id=member.user_id,
        role=member.role,
        user_name=user.full_name if user else None,
        user_email=user.email if user else None,
        user_avatar=user.avatar_url if user else None,
        invited_at=member.invited_at,
        accepted_at=member.accepted_at,
    )


@router.delete("/{workspace_id}/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    workspace_id: int,
    member_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove a member from workspace"""
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    if not _user_is_workspace_admin(db, current_user.id, workspace_id, workspace.owner_user_id):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    member = db.query(WorkspaceMember).filter(
        WorkspaceMember.id == member_id,
        WorkspaceMember.workspace_id == workspace_id
    ).first()
    
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    db.delete(member)
    db.commit()


# ============================================================================
# GOOGLE DRIVE STRUCTURE
# ============================================================================

@router.post("/{workspace_id}/drive/setup", response_model=DriveStructureResponse)
async def setup_drive_structure(
    workspace_id: int,
    data: DriveStructureRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create or verify Google Drive folder structure for workspace.
    Creates: Clients, Projets, Templates, Archive folders.
    """
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    if not _user_is_workspace_admin(db, current_user.id, workspace_id, workspace.owner_user_id):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        service = get_google_workspace_service(current_user.id)
        result = await service.ensure_workspace_structure(
            root_folder_id=workspace.drive_root_folder_id,
            workspace_name=workspace.name,
        )
        
        # Update workspace with folder IDs
        if result["success"]:
            workspace.drive_root_folder_id = result["root_folder_id"]
            if "Templates" in result["folders"]:
                workspace.templates_folder_id = result["folders"]["Templates"]
            db.commit()
        
        return DriveStructureResponse(
            success=result["success"],
            root_folder_id=result["root_folder_id"],
            root_folder_url=f"https://drive.google.com/drive/folders/{result['root_folder_id']}" if result["root_folder_id"] else None,
            folders=result["folders"],
            errors=result["errors"],
        )
        
    except TokenExpiredError:
        raise HTTPException(
            status_code=401,
            detail="Google authorization required. Please reconnect your Google account."
        )
    except GoogleAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get("/{workspace_id}/drive/status")
async def get_drive_status(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Check Google Drive connection and folder structure status"""
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    if not _user_has_workspace_access(db, current_user.id, workspace_id, current_user.role):
        raise HTTPException(status_code=403, detail="Access denied")
    
    status = {
        "connected": False,
        "has_root_folder": workspace.drive_root_folder_id is not None,
        "has_templates_folder": workspace.templates_folder_id is not None,
        "has_brief_template": workspace.brief_template_doc_id is not None,
        "has_report_template": workspace.report_template_sheet_id is not None,
        "root_folder_url": workspace.drive_url,
    }
    
    # Check if user has valid tokens
    try:
        service = get_google_workspace_service(current_user.id)
        await service.get_access_token()
        status["connected"] = True
    except:
        status["connected"] = False
    
    return status


# ============================================================================
# HELPERS
# ============================================================================

def _user_has_workspace_access(db: Session, user_id: int, workspace_id: int, user_role: str = None) -> bool:
    """Check if user has any access to workspace. Global admins have access to all."""
    # Global admins have access to everything
    if user_role == 'admin':
        return True
    
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        return False
    
    if workspace.owner_user_id == user_id:
        return True
    
    member = db.query(WorkspaceMember).filter(
        WorkspaceMember.workspace_id == workspace_id,
        WorkspaceMember.user_id == user_id
    ).first()
    
    return member is not None


def _user_is_workspace_admin(db: Session, user_id: int, workspace_id: int, owner_id: int) -> bool:
    """Check if user is owner or admin of workspace"""
    if user_id == owner_id:
        return True
    
    member = db.query(WorkspaceMember).filter(
        WorkspaceMember.workspace_id == workspace_id,
        WorkspaceMember.user_id == user_id,
        WorkspaceMember.role == WorkspaceRole.ADMIN
    ).first()
    
    return member is not None


def get_user_workspace_role(db: Session, user_id: int, workspace_id: int) -> Optional[str]:
    """Get user's role in workspace"""
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        return None
    
    if workspace.owner_user_id == user_id:
        return "owner"
    
    member = db.query(WorkspaceMember).filter(
        WorkspaceMember.workspace_id == workspace_id,
        WorkspaceMember.user_id == user_id
    ).first()
    
    return member.role.value if member else None


# ============================================================================
# WORKSPACE INVITES (Authorized Emails) - Admin Only
# ============================================================================

@router.get("/{workspace_id}/invites", response_model=WorkspaceInviteListResponse)
async def list_workspace_invites(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all authorized emails for a workspace. Admin only."""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin only")
    
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    invites = db.query(WorkspaceInvite).filter(
        WorkspaceInvite.workspace_id == workspace_id
    ).order_by(WorkspaceInvite.created_at.desc()).all()
    
    return WorkspaceInviteListResponse(
        items=[WorkspaceInviteResponse(
            id=inv.id,
            workspace_id=inv.workspace_id,
            email=inv.email,
            role=inv.role,
            claimed=inv.claimed,
            claimed_at=inv.claimed_at,
            created_at=inv.created_at,
        ) for inv in invites],
        total=len(invites)
    )


@router.post("/{workspace_id}/invites", response_model=WorkspaceInviteResponse, status_code=status.HTTP_201_CREATED)
async def add_workspace_invite(
    workspace_id: int,
    data: WorkspaceInviteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add an authorized email to a workspace and send invitation email. Admin only."""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin only")
    
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    # Check if email already exists
    existing = db.query(WorkspaceInvite).filter(
        WorkspaceInvite.workspace_id == workspace_id,
        WorkspaceInvite.email == data.email.lower()
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Email déjà autorisé pour ce workspace")
    
    invite = WorkspaceInvite(
        workspace_id=workspace_id,
        email=data.email.lower(),
        role=data.role,
        invited_by=current_user.id,
    )
    
    db.add(invite)
    db.commit()
    db.refresh(invite)
    
    # Send invitation email if enabled
    try:
        from app.core.admin_settings import get_admin_setting
        from app.services.email_service import email_service
        
        if get_admin_setting("send_invitation_emails", True) and email_service.is_configured:
            await email_service.send_workspace_invite(
                to_email=invite.email,
                workspace_name=workspace.name,
                inviter_name=current_user.full_name or current_user.email,
                role=invite.role,
            )
    except Exception as e:
        # Log but don't fail if email sending fails
        import logging
        logging.error(f"Failed to send invitation email: {e}")
    
    return WorkspaceInviteResponse(
        id=invite.id,
        workspace_id=invite.workspace_id,
        email=invite.email,
        role=invite.role,
        claimed=invite.claimed,
        claimed_at=invite.claimed_at,
        created_at=invite.created_at,
    )


@router.delete("/{workspace_id}/invites/{invite_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_workspace_invite(
    workspace_id: int,
    invite_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove an authorized email from a workspace. Admin only."""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin only")
    
    invite = db.query(WorkspaceInvite).filter(
        WorkspaceInvite.id == invite_id,
        WorkspaceInvite.workspace_id == workspace_id
    ).first()
    
    if not invite:
        raise HTTPException(status_code=404, detail="Invite not found")
    
    db.delete(invite)
    db.commit()


# ============================================================================
# AUTO-ASSIGN WORKSPACE ON LOGIN
# ============================================================================

def auto_assign_user_to_workspaces(db: Session, user: User) -> List[int]:
    """
    Check if user's email matches any workspace invites.
    If so, add them as a member and mark invite as claimed.
    Returns list of workspace IDs the user was added to.
    """
    from datetime import datetime
    
    invites = db.query(WorkspaceInvite).filter(
        WorkspaceInvite.email == user.email.lower(),
        WorkspaceInvite.claimed == False
    ).all()
    
    workspace_ids = []
    
    for invite in invites:
        # Check if already a member
        existing_member = db.query(WorkspaceMember).filter(
            WorkspaceMember.workspace_id == invite.workspace_id,
            WorkspaceMember.user_id == user.id
        ).first()
        
        if not existing_member:
            # Add as member
            member = WorkspaceMember(
                workspace_id=invite.workspace_id,
                user_id=user.id,
                role=invite.role,
                invited_by=invite.invited_by,
            )
            db.add(member)
            workspace_ids.append(invite.workspace_id)
        
        # Mark invite as claimed
        invite.claimed = True
        invite.claimed_at = datetime.utcnow()
        invite.claimed_by_user_id = user.id
    
    if invites:
        db.commit()
    
    return workspace_ids
