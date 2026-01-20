"""
Google Drive API - Drive/Docs/Sheets operations for entities
"""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.session import get_db
from app.db.models.user import User
from app.db.models.workspace import Workspace
from app.db.models.agency import Client, Project, Deliverable
from app.api.deps import get_current_user
from app.api.workspace import _user_has_workspace_access
from app.services.google_workspace import get_google_workspace_service, GoogleAPIError, TokenExpiredError

router = APIRouter(prefix="/drive", tags=["google-drive"])


# ============================================================================
# SCHEMAS
# ============================================================================

class FolderResponse(BaseModel):
    id: str
    url: str
    name: Optional[str] = None


class DocResponse(BaseModel):
    id: str
    url: str
    name: Optional[str] = None


class CreateFolderRequest(BaseModel):
    name: Optional[str] = None  # Use entity name if not provided


class CreateDocRequest(BaseModel):
    name: Optional[str] = None
    template_id: Optional[str] = None  # Use workspace template if not provided
    replacements: Optional[dict] = None  # {"{{PLACEHOLDER}}": "value"}


# ============================================================================
# CLIENT DRIVE
# ============================================================================

@router.post("/clients/{client_id}/folder", response_model=FolderResponse)
async def create_client_folder(
    client_id: int,
    data: CreateFolderRequest = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create or get Drive folder for client"""
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    if client.workspace_id and not _user_has_workspace_access(db, current_user.id, client.workspace_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Return existing folder if exists
    if client.drive_folder_id:
        return FolderResponse(
            id=client.drive_folder_id,
            url=f"https://drive.google.com/drive/folders/{client.drive_folder_id}",
            name=client.name
        )
    
    # Get workspace for parent folder
    workspace = None
    clients_folder_id = None
    if client.workspace_id:
        workspace = db.query(Workspace).filter(Workspace.id == client.workspace_id).first()
        if workspace and workspace.drive_root_folder_id:
            # Find or create Clients folder
            try:
                service = get_google_workspace_service(current_user.id)
                existing = await service.find_folder_by_name("Clients", workspace.drive_root_folder_id)
                if existing:
                    clients_folder_id = existing["id"]
                else:
                    folder = await service.create_folder("Clients", workspace.drive_root_folder_id)
                    clients_folder_id = folder["id"]
            except TokenExpiredError:
                raise HTTPException(status_code=401, detail="Google authorization required")
            except GoogleAPIError as e:
                raise HTTPException(status_code=e.status_code, detail=e.message)
    
    try:
        service = get_google_workspace_service(current_user.id)
        folder_name = (data and data.name) or client.name
        
        result = await service.ensure_client_folder(folder_name, clients_folder_id)
        
        # Save folder ID to client
        client.drive_folder_id = result["id"]
        db.commit()
        
        return FolderResponse(
            id=result["id"],
            url=result["url"],
            name=folder_name
        )
        
    except TokenExpiredError:
        raise HTTPException(status_code=401, detail="Google authorization required")
    except GoogleAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get("/clients/{client_id}/folder", response_model=Optional[FolderResponse])
async def get_client_folder(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get client Drive folder info"""
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    if client.workspace_id and not _user_has_workspace_access(db, current_user.id, client.workspace_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    if not client.drive_folder_id:
        return None
    
    return FolderResponse(
        id=client.drive_folder_id,
        url=f"https://drive.google.com/drive/folders/{client.drive_folder_id}",
        name=client.name
    )


# ============================================================================
# PROJECT DRIVE
# ============================================================================

@router.post("/projects/{project_id}/folder", response_model=FolderResponse)
async def create_project_folder(
    project_id: int,
    data: CreateFolderRequest = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create or get Drive folder for project with standard subfolders"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project.workspace_id and not _user_has_workspace_access(db, current_user.id, project.workspace_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Return existing folder if exists
    if project.drive_folder_id:
        return FolderResponse(
            id=project.drive_folder_id,
            url=f"https://drive.google.com/drive/folders/{project.drive_folder_id}",
            name=project.name
        )
    
    # Get parent folder (client folder or workspace projects folder)
    parent_folder_id = None
    
    if project.client and project.client.drive_folder_id:
        parent_folder_id = project.client.drive_folder_id
    elif project.workspace_id:
        workspace = db.query(Workspace).filter(Workspace.id == project.workspace_id).first()
        if workspace and workspace.drive_root_folder_id:
            try:
                service = get_google_workspace_service(current_user.id)
                existing = await service.find_folder_by_name("Projets", workspace.drive_root_folder_id)
                if existing:
                    parent_folder_id = existing["id"]
                else:
                    folder = await service.create_folder("Projets", workspace.drive_root_folder_id)
                    parent_folder_id = folder["id"]
            except (TokenExpiredError, GoogleAPIError):
                pass
    
    if not parent_folder_id:
        raise HTTPException(
            status_code=400, 
            detail="No parent folder available. Set up client folder or workspace Drive first."
        )
    
    try:
        service = get_google_workspace_service(current_user.id)
        folder_name = (data and data.name) or project.name
        
        result = await service.ensure_project_folder(folder_name, parent_folder_id)
        
        # Save folder ID to project
        project.drive_folder_id = result["id"]
        db.commit()
        
        return FolderResponse(
            id=result["id"],
            url=result["url"],
            name=folder_name
        )
        
    except TokenExpiredError:
        raise HTTPException(status_code=401, detail="Google authorization required")
    except GoogleAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get("/projects/{project_id}/folder", response_model=Optional[FolderResponse])
async def get_project_folder(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get project Drive folder info"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project.workspace_id and not _user_has_workspace_access(db, current_user.id, project.workspace_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    if not project.drive_folder_id:
        return None
    
    return FolderResponse(
        id=project.drive_folder_id,
        url=f"https://drive.google.com/drive/folders/{project.drive_folder_id}",
        name=project.name
    )


# ============================================================================
# PROJECT BRIEF (Google Doc)
# ============================================================================

@router.post("/projects/{project_id}/brief", response_model=DocResponse)
async def create_project_brief(
    project_id: int,
    data: CreateDocRequest = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create brief document from template for project"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project.workspace_id and not _user_has_workspace_access(db, current_user.id, project.workspace_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Return existing brief if exists
    if project.brief_doc_id:
        return DocResponse(
            id=project.brief_doc_id,
            url=f"https://docs.google.com/document/d/{project.brief_doc_id}/edit",
            name=f"Brief - {project.name}"
        )
    
    # Get template ID
    template_id = data.template_id if data else None
    if not template_id and project.workspace_id:
        workspace = db.query(Workspace).filter(Workspace.id == project.workspace_id).first()
        if workspace:
            template_id = workspace.brief_template_doc_id
    
    if not template_id:
        raise HTTPException(
            status_code=400,
            detail="No template specified and workspace has no brief template configured"
        )
    
    # Get target folder (Brief subfolder)
    target_folder = None
    if project.drive_folder_id:
        try:
            service = get_google_workspace_service(current_user.id)
            brief_folder = await service.find_folder_by_name("Brief", project.drive_folder_id)
            if brief_folder:
                target_folder = brief_folder["id"]
            else:
                target_folder = project.drive_folder_id
        except:
            target_folder = project.drive_folder_id
    
    try:
        service = get_google_workspace_service(current_user.id)
        
        # Default replacements
        replacements = data.replacements if data else {}
        if not replacements:
            replacements = {
                "{{PROJECT_NAME}}": project.name,
                "{{CLIENT_NAME}}": project.client.name if project.client else "",
                "{{DATE}}": datetime.utcnow().strftime("%d/%m/%Y"),
                "{{DEADLINE}}": project.deadline.strftime("%d/%m/%Y") if project.deadline else "À définir",
            }
        
        result = await service.create_brief_from_template(
            template_id=template_id,
            project_name=project.name,
            brief_folder_id=target_folder,
            replacements=replacements,
        )
        
        # Save doc ID to project
        project.brief_doc_id = result["id"]
        db.commit()
        
        return DocResponse(
            id=result["id"],
            url=result["url"],
            name=result.get("name", f"Brief - {project.name}")
        )
        
    except TokenExpiredError:
        raise HTTPException(status_code=401, detail="Google authorization required")
    except GoogleAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get("/projects/{project_id}/brief", response_model=Optional[DocResponse])
async def get_project_brief(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get project brief document info"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project.workspace_id and not _user_has_workspace_access(db, current_user.id, project.workspace_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    if not project.brief_doc_id:
        return None
    
    return DocResponse(
        id=project.brief_doc_id,
        url=f"https://docs.google.com/document/d/{project.brief_doc_id}/edit",
        name=f"Brief - {project.name}"
    )


# ============================================================================
# PROJECT REPORT (Google Sheet)
# ============================================================================

@router.post("/projects/{project_id}/report", response_model=DocResponse)
async def create_project_report(
    project_id: int,
    data: CreateDocRequest = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create report spreadsheet from template for project"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project.workspace_id and not _user_has_workspace_access(db, current_user.id, project.workspace_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Return existing report if exists
    if project.report_sheet_id:
        return DocResponse(
            id=project.report_sheet_id,
            url=f"https://docs.google.com/spreadsheets/d/{project.report_sheet_id}/edit",
            name=f"Report - {project.name}"
        )
    
    # Get template ID
    template_id = data.template_id if data else None
    if not template_id and project.workspace_id:
        workspace = db.query(Workspace).filter(Workspace.id == project.workspace_id).first()
        if workspace:
            template_id = workspace.report_template_sheet_id
    
    if not template_id:
        raise HTTPException(
            status_code=400,
            detail="No template specified and workspace has no report template configured"
        )
    
    # Get target folder (Admin subfolder)
    target_folder = None
    if project.drive_folder_id:
        try:
            service = get_google_workspace_service(current_user.id)
            admin_folder = await service.find_folder_by_name("Admin", project.drive_folder_id)
            if admin_folder:
                target_folder = admin_folder["id"]
            else:
                target_folder = project.drive_folder_id
        except:
            target_folder = project.drive_folder_id
    
    try:
        service = get_google_workspace_service(current_user.id)
        
        result = await service.create_report_from_template(
            template_id=template_id,
            project_name=project.name,
            admin_folder_id=target_folder,
        )
        
        # Save sheet ID to project
        project.report_sheet_id = result["id"]
        db.commit()
        
        return DocResponse(
            id=result["id"],
            url=result["url"],
            name=result.get("name", f"Report - {project.name}")
        )
        
    except TokenExpiredError:
        raise HTTPException(status_code=401, detail="Google authorization required")
    except GoogleAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get("/projects/{project_id}/report", response_model=Optional[DocResponse])
async def get_project_report(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get project report sheet info"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project.workspace_id and not _user_has_workspace_access(db, current_user.id, project.workspace_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    if not project.report_sheet_id:
        return None
    
    return DocResponse(
        id=project.report_sheet_id,
        url=f"https://docs.google.com/spreadsheets/d/{project.report_sheet_id}/edit",
        name=f"Report - {project.name}"
    )


# ============================================================================
# CALENDAR EVENTS
# ============================================================================

@router.post("/projects/{project_id}/deadline-event")
async def create_project_deadline_event(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create calendar event for project deadline"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project.workspace_id and not _user_has_workspace_access(db, current_user.id, project.workspace_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    if not project.deadline:
        raise HTTPException(status_code=400, detail="Project has no deadline")
    
    # Return existing event if exists
    if project.calendar_event_id:
        return {
            "id": project.calendar_event_id,
            "message": "Calendar event already exists"
        }
    
    # Get calendar ID from workspace
    calendar_id = "primary"
    if project.workspace_id:
        workspace = db.query(Workspace).filter(Workspace.id == project.workspace_id).first()
        if workspace and workspace.calendar_id:
            calendar_id = workspace.calendar_id
    
    try:
        service = get_google_workspace_service(current_user.id)
        
        description = f"Deadline projet: {project.name}"
        if project.client:
            description += f"\nClient: {project.client.name}"
        
        result = await service.create_deadline_event(
            title=project.name,
            deadline=project.deadline,
            description=description,
            calendar_id=calendar_id,
        )
        
        # Save event ID to project
        project.calendar_event_id = result["id"]
        db.commit()
        
        return {
            "id": result["id"],
            "url": result["url"],
            "message": "Calendar event created"
        }
        
    except TokenExpiredError:
        raise HTTPException(status_code=401, detail="Google authorization required")
    except GoogleAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/deliverables/{deliverable_id}/deadline-event")
async def create_deliverable_deadline_event(
    deliverable_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create calendar event for deliverable deadline"""
    deliverable = db.query(Deliverable).filter(Deliverable.id == deliverable_id).first()
    if not deliverable:
        raise HTTPException(status_code=404, detail="Deliverable not found")
    
    project = deliverable.project
    if project.workspace_id and not _user_has_workspace_access(db, current_user.id, project.workspace_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    if not deliverable.due_date:
        raise HTTPException(status_code=400, detail="Deliverable has no due date")
    
    # Return existing event if exists
    if deliverable.calendar_event_id:
        return {
            "id": deliverable.calendar_event_id,
            "message": "Calendar event already exists"
        }
    
    # Get calendar ID from workspace
    calendar_id = "primary"
    if project.workspace_id:
        workspace = db.query(Workspace).filter(Workspace.id == project.workspace_id).first()
        if workspace and workspace.calendar_id:
            calendar_id = workspace.calendar_id
    
    try:
        service = get_google_workspace_service(current_user.id)
        
        description = f"Livrable: {deliverable.name}\nProjet: {project.name}"
        if project.client:
            description += f"\nClient: {project.client.name}"
        
        result = await service.create_deadline_event(
            title=f"📦 {deliverable.name}",
            deadline=deliverable.due_date,
            description=description,
            calendar_id=calendar_id,
        )
        
        # Save event ID to deliverable
        deliverable.calendar_event_id = result["id"]
        db.commit()
        
        return {
            "id": result["id"],
            "url": result["url"],
            "message": "Calendar event created"
        }
        
    except TokenExpiredError:
        raise HTTPException(status_code=401, detail="Google authorization required")
    except GoogleAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
