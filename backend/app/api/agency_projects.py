"""
Agency Cockpit V2 API - Projects, Deliverables, Production
"""
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.session import get_db
from app.db.models.agency import (
    Client, Deal, Project, Deliverable, Approval, 
    ProjectStatus, DeliverableStatus, ApprovalStatus, DealStatus
)
from app.db.models.user import User
from app.api.deps import get_current_user
from app.schemas.agency import (
    # Project
    ProjectCreate, ProjectUpdate, ProjectResponse, ProjectListResponse,
    ProjectStatus as ProjectStatusEnum,
    # Deliverable
    DeliverableCreate, DeliverableUpdate, DeliverableResponse,
    DeliverableStatus as DeliverableStatusEnum,
    # Approval
    ApprovalCreate, ApprovalUpdate, ApprovalResponse,
    ApprovalStatus as ApprovalStatusEnum,
    # Production
    ProductionResponse, ProductionColumn, ProductionItem
)
from app.services.google_workspace import (
    get_google_workspace_service, 
    GoogleAPIError, 
    TokenExpiredError
)
from app.core.cache import cache_get

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agency", tags=["agency-projects"])


# ============================================================================
# PROJECTS
# ============================================================================

@router.get("/projects", response_model=List[ProjectListResponse])
async def list_projects(
    status: Optional[str] = Query(None),
    client_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Liste des projets"""
    query = db.query(Project).join(Client)
    
    if status:
        # Convert string to enum (case-insensitive)
        try:
            status_enum = ProjectStatus(status.lower())
            query = query.filter(Project.status == status_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    if client_id:
        query = query.filter(Project.client_id == client_id)
    
    projects = query.offset(skip).limit(limit).all()
    now = datetime.utcnow()
    
    result = []
    for project in projects:
        # Count deliverables
        total_deliverables = db.query(func.count(Deliverable.id)).filter(
            Deliverable.project_id == project.id
        ).scalar() or 0
        
        approved_deliverables = db.query(func.count(Deliverable.id)).filter(
            Deliverable.project_id == project.id,
            Deliverable.status.in_([DeliverableStatus.APPROVED, DeliverableStatus.DELIVERED])
        ).scalar() or 0
        
        progress = int((approved_deliverables / total_deliverables * 100)) if total_deliverables > 0 else 0
        
        days_until = None
        is_urgent = False
        if project.deadline:
            days_until = (project.deadline - now).days
            is_urgent = days_until <= 3 and days_until >= 0
        
        result.append(ProjectListResponse(
            id=project.id,
            name=project.name,
            status=ProjectStatusEnum(project.status.value),
            client_id=project.client_id,
            client_name=project.client.name if project.client else None,
            deadline=project.deadline,
            days_until_deadline=days_until,
            is_urgent=is_urgent,
            progress_percent=progress,
            deliverables_count=total_deliverables,
            deliverables_approved=approved_deliverables
        ))
    
    return result


# ============================================================================
# BACKGROUND TASK: CREATE DRIVE STRUCTURE
# ============================================================================

async def create_project_drive_structure_task(
    project_id: int,
    project_name: str,
    user_id: int,
    db_url: str,
):
    """
    Background task to create Google Drive folder structure for a project.
    Called automatically after project creation.
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    try:
        # Check if user has Google Workspace connected
        tokens = cache_get(f"google_workspace_tokens:{user_id}")
        if not tokens:
            logger.info(f"User {user_id} has no Google Workspace connected, skipping Drive creation")
            return
        
        # Get Google Workspace service
        service = get_google_workspace_service(user_id)
        
        # TODO: Get template IDs from workspace settings
        # brief_template_id = workspace.brief_template_id
        # report_template_id = workspace.report_template_id
        brief_template_id = None
        report_template_id = None
        
        # Create the Drive structure
        result = await service.create_project_drive_structure(
            project_name=project_name,
            brief_template_id=brief_template_id,
            report_template_id=report_template_id,
        )
        
        if result["success"] or result["drive_folder_id"]:
            # Update project with Drive folder ID
            engine = create_engine(db_url)
            SessionLocal = sessionmaker(bind=engine)
            db = SessionLocal()
            
            try:
                project = db.query(Project).filter(Project.id == project_id).first()
                if project:
                    project.drive_folder_id = result["drive_folder_id"]
                    if result.get("brief_doc_id"):
                        project.brief_doc_id = result["brief_doc_id"]
                    if result.get("report_sheet_id"):
                        project.report_sheet_id = result["report_sheet_id"]
                    db.commit()
                    logger.info(f"Updated project {project_id} with Drive folder: {result['drive_folder_id']}")
            finally:
                db.close()
        
        if result["errors"]:
            logger.warning(f"Drive structure created with errors: {result['errors']}")
            
    except TokenExpiredError:
        logger.warning(f"Google token expired for user {user_id}, Drive structure not created")
    except Exception as e:
        logger.error(f"Failed to create Drive structure for project {project_id}: {e}")


@router.post("/projects", response_model=ProjectResponse)
async def create_project(
    project_in: ProjectCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Créer un nouveau projet avec création automatique du dossier Drive"""
    client = None
    # Vérifier client si fourni
    if project_in.client_id:
        client = db.query(Client).filter(Client.id == project_in.client_id).first()
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
    
    # Vérifier deal si fourni
    if project_in.deal_id:
        deal = db.query(Deal).filter(Deal.id == project_in.deal_id).first()
        if not deal:
            raise HTTPException(status_code=404, detail="Deal not found")
    
    project = Project(
        client_id=project_in.client_id,
        deal_id=project_in.deal_id,
        name=project_in.name,
        status=project_in.status.value if project_in.status else ProjectStatus.ACTIVE,
        deadline=project_in.deadline,
        budget=project_in.budget,
        description=project_in.description,
        owner_id=current_user.id
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    
    # Trigger background task to create Drive folder structure
    from app.core.config import settings
    background_tasks.add_task(
        create_project_drive_structure_task,
        project_id=project.id,
        project_name=project.name,
        user_id=current_user.id,
        db_url=settings.database_url,
    )
    logger.info(f"Project {project.id} created, Drive structure creation scheduled")
    
    return ProjectResponse(
        id=project.id,
        client_id=project.client_id,
        deal_id=project.deal_id,
        name=project.name,
        status=ProjectStatusEnum(project.status.value),
        deadline=project.deadline,
        budget=project.budget,
        description=project.description,
        owner_id=project.owner_id,
        created_at=project.created_at,
        updated_at=project.updated_at,
        client_name=client.name if client else None
    )


@router.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Détails d'un projet"""
    project = db.query(Project).join(Client).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    now = datetime.utcnow()
    
    total_deliverables = db.query(func.count(Deliverable.id)).filter(
        Deliverable.project_id == project.id
    ).scalar() or 0
    
    approved_deliverables = db.query(func.count(Deliverable.id)).filter(
        Deliverable.project_id == project.id,
        Deliverable.status.in_([DeliverableStatus.APPROVED, DeliverableStatus.DELIVERED])
    ).scalar() or 0
    
    progress = int((approved_deliverables / total_deliverables * 100)) if total_deliverables > 0 else 0
    
    days_until = None
    is_urgent = False
    if project.deadline:
        days_until = (project.deadline - now).days
        is_urgent = days_until <= 3 and days_until >= 0
    
    # Build Drive URLs from IDs
    drive_folder_url = f"https://drive.google.com/drive/folders/{project.drive_folder_id}" if project.drive_folder_id else None
    brief_doc_url = f"https://docs.google.com/document/d/{project.brief_doc_id}/edit" if project.brief_doc_id else None
    report_sheet_url = f"https://docs.google.com/spreadsheets/d/{project.report_sheet_id}/edit" if project.report_sheet_id else None
    
    return ProjectResponse(
        id=project.id,
        client_id=project.client_id,
        deal_id=project.deal_id,
        name=project.name,
        status=ProjectStatusEnum(project.status.value),
        deadline=project.deadline,
        budget=project.budget,
        description=project.description,
        owner_id=project.owner_id,
        created_at=project.created_at,
        updated_at=project.updated_at,
        # Drive integration
        drive_folder_id=project.drive_folder_id,
        drive_folder_url=drive_folder_url,
        brief_doc_id=project.brief_doc_id,
        brief_doc_url=brief_doc_url,
        report_sheet_id=project.report_sheet_id,
        report_sheet_url=report_sheet_url,
        # Computed
        client_name=project.client.name if project.client else None,
        owner_name=project.owner.email if project.owner else None,
        deliverables_count=total_deliverables,
        deliverables_approved=approved_deliverables,
        progress_percent=progress,
        days_until_deadline=days_until,
        is_urgent=is_urgent
    )


@router.put("/projects/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    project_in: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mettre à jour un projet"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project_in.client_id is not None:
        project.client_id = project_in.client_id
    if project_in.deal_id is not None:
        project.deal_id = project_in.deal_id
    if project_in.name is not None:
        project.name = project_in.name
    if project_in.status is not None:
        project.status = project_in.status.value
    if project_in.deadline is not None:
        project.deadline = project_in.deadline
    if project_in.budget is not None:
        project.budget = project_in.budget
    if project_in.description is not None:
        project.description = project_in.description
    
    db.commit()
    db.refresh(project)
    
    return await get_project(project_id, db, current_user)


@router.put("/projects/{project_id}/status")
async def update_project_status(
    project_id: int,
    status: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Quick status update"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project.status = status
    db.commit()
    
    return {"status": "updated", "new_status": status}


@router.delete("/projects/{project_id}")
async def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Supprimer un projet"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    db.delete(project)
    db.commit()
    return {"status": "deleted"}


# ============================================================================
# DELIVERABLES
# ============================================================================

@router.get("/deliverables", response_model=List[DeliverableResponse])
async def list_deliverables(
    project_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Liste des livrables"""
    query = db.query(Deliverable).join(Project).join(Client)
    
    if project_id:
        query = query.filter(Deliverable.project_id == project_id)
    if status:
        # Convert string to enum (case-insensitive)
        try:
            status_enum = DeliverableStatus(status.lower())
            query = query.filter(Deliverable.status == status_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    
    deliverables = query.offset(skip).limit(limit).all()
    now = datetime.utcnow()
    
    result = []
    for d in deliverables:
        has_pending = db.query(func.count(Approval.id)).filter(
            Approval.deliverable_id == d.id,
            Approval.status == ApprovalStatus.PENDING
        ).scalar() > 0
        
        days_until = None
        if d.due_date:
            days_until = (d.due_date - now).days
        
        result.append(DeliverableResponse(
            id=d.id,
            project_id=d.project_id,
            name=d.name,
            type=d.type,
            status=DeliverableStatusEnum(d.status.value),
            due_date=d.due_date,
            link=d.link,
            notes=d.notes,
            created_at=d.created_at,
            updated_at=d.updated_at,
            project_name=d.project.name if d.project else None,
            client_name=d.project.client.name if d.project and d.project.client else None,
            has_pending_approval=has_pending,
            days_until_due=days_until
        ))
    
    return result


@router.post("/deliverables", response_model=DeliverableResponse)
async def create_deliverable(
    deliverable_in: DeliverableCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Créer un nouveau livrable"""
    project = db.query(Project).filter(Project.id == deliverable_in.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    deliverable = Deliverable(
        project_id=deliverable_in.project_id,
        name=deliverable_in.name,
        type=deliverable_in.type,
        status=deliverable_in.status.value if deliverable_in.status else DeliverableStatus.DRAFT,
        due_date=deliverable_in.due_date,
        link=deliverable_in.link,
        notes=deliverable_in.notes
    )
    db.add(deliverable)
    db.commit()
    db.refresh(deliverable)
    
    return DeliverableResponse(
        id=deliverable.id,
        project_id=deliverable.project_id,
        name=deliverable.name,
        type=deliverable.type,
        status=DeliverableStatusEnum(deliverable.status.value),
        due_date=deliverable.due_date,
        link=deliverable.link,
        notes=deliverable.notes,
        created_at=deliverable.created_at,
        updated_at=deliverable.updated_at,
        project_name=project.name,
        client_name=project.client.name if project.client else None
    )


@router.get("/deliverables/{deliverable_id}", response_model=DeliverableResponse)
async def get_deliverable(
    deliverable_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Détails d'un livrable"""
    d = db.query(Deliverable).join(Project).join(Client).filter(
        Deliverable.id == deliverable_id
    ).first()
    if not d:
        raise HTTPException(status_code=404, detail="Deliverable not found")
    
    now = datetime.utcnow()
    has_pending = db.query(func.count(Approval.id)).filter(
        Approval.deliverable_id == d.id,
        Approval.status == ApprovalStatus.PENDING
    ).scalar() > 0
    
    days_until = None
    if d.due_date:
        days_until = (d.due_date - now).days
    
    return DeliverableResponse(
        id=d.id,
        project_id=d.project_id,
        name=d.name,
        type=d.type,
        status=DeliverableStatusEnum(d.status.value),
        due_date=d.due_date,
        link=d.link,
        notes=d.notes,
        created_at=d.created_at,
        updated_at=d.updated_at,
        project_name=d.project.name if d.project else None,
        client_name=d.project.client.name if d.project and d.project.client else None,
        has_pending_approval=has_pending,
        days_until_due=days_until
    )


@router.put("/deliverables/{deliverable_id}", response_model=DeliverableResponse)
async def update_deliverable(
    deliverable_id: int,
    deliverable_in: DeliverableUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mettre à jour un livrable"""
    d = db.query(Deliverable).filter(Deliverable.id == deliverable_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Deliverable not found")
    
    if deliverable_in.name is not None:
        d.name = deliverable_in.name
    if deliverable_in.type is not None:
        d.type = deliverable_in.type
    if deliverable_in.status is not None:
        d.status = deliverable_in.status.value
    if deliverable_in.due_date is not None:
        d.due_date = deliverable_in.due_date
    if deliverable_in.link is not None:
        d.link = deliverable_in.link
    if deliverable_in.notes is not None:
        d.notes = deliverable_in.notes
    
    db.commit()
    db.refresh(d)
    
    return await get_deliverable(deliverable_id, db, current_user)


@router.put("/deliverables/{deliverable_id}/status")
async def update_deliverable_status(
    deliverable_id: int,
    status: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Quick status update (for kanban)"""
    d = db.query(Deliverable).filter(Deliverable.id == deliverable_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Deliverable not found")
    
    d.status = status
    db.commit()
    
    return {"status": "updated", "new_status": status}


@router.delete("/deliverables/{deliverable_id}")
async def delete_deliverable(
    deliverable_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Supprimer un livrable"""
    d = db.query(Deliverable).filter(Deliverable.id == deliverable_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Deliverable not found")
    
    db.delete(d)
    db.commit()
    return {"status": "deleted"}


# ============================================================================
# PRODUCTION KANBAN
# ============================================================================

@router.get("/production", response_model=ProductionResponse)
async def get_production(
    project_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Production Kanban - tous les livrables par statut"""
    columns = []
    total_items = 0
    now = datetime.utcnow()
    
    status_labels = {
        DeliverableStatus.DRAFT: "Brouillon",
        DeliverableStatus.TO_REVIEW: "À valider",
        DeliverableStatus.CHANGES_REQUESTED: "Corrections",
        DeliverableStatus.APPROVED: "Validé",
        DeliverableStatus.DELIVERED: "Livré"
    }
    
    for status in DeliverableStatus:
        query = db.query(Deliverable).join(Project).join(Client).filter(
            Deliverable.status == status
        )
        
        if project_id:
            query = query.filter(Deliverable.project_id == project_id)
        
        deliverables = query.all()
        
        items = []
        for d in deliverables:
            days_until = None
            is_urgent = False
            if d.due_date:
                days_until = (d.due_date - now).days
                is_urgent = days_until <= 3 and days_until >= 0
            
            has_pending = db.query(func.count(Approval.id)).filter(
                Approval.deliverable_id == d.id,
                Approval.status == ApprovalStatus.PENDING
            ).scalar() > 0
            
            items.append(ProductionItem(
                id=d.id,
                name=d.name,
                type=d.type,
                status=DeliverableStatusEnum(d.status.value),
                due_date=d.due_date,
                days_until_due=days_until,
                is_urgent=is_urgent,
                project_id=d.project_id,
                project_name=d.project.name if d.project else "",
                client_name=d.project.client.name if d.project and d.project.client else "",
                has_pending_approval=has_pending,
                link=d.link
            ))
        
        columns.append(ProductionColumn(
            status=DeliverableStatusEnum(status.value),
            label=status_labels.get(status, status.value),
            items=items,
            count=len(items)
        ))
        
        total_items += len(items)
    
    return ProductionResponse(
        columns=columns,
        total_items=total_items
    )


# ============================================================================
# APPROVALS
# ============================================================================

@router.get("/approvals", response_model=List[ApprovalResponse])
async def list_approvals(
    status: Optional[str] = Query(None),
    deliverable_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Liste des demandes de validation"""
    query = db.query(Approval).join(Deliverable).join(Project).join(Client)
    
    if status:
        # Convert string to enum (case-insensitive)
        try:
            status_enum = ApprovalStatus(status.lower())
            query = query.filter(Approval.status == status_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    if deliverable_id:
        query = query.filter(Approval.deliverable_id == deliverable_id)
    
    approvals = query.offset(skip).limit(limit).all()
    
    result = []
    for a in approvals:
        result.append(ApprovalResponse(
            id=a.id,
            deliverable_id=a.deliverable_id,
            status=ApprovalStatusEnum(a.status.value),
            feedback=a.feedback,
            requested_at=a.requested_at,
            decided_at=a.decided_at,
            decided_by=a.decided_by,
            deliverable_name=a.deliverable.name if a.deliverable else None,
            project_name=a.deliverable.project.name if a.deliverable and a.deliverable.project else None,
            client_name=a.deliverable.project.client.name if a.deliverable and a.deliverable.project and a.deliverable.project.client else None
        ))
    
    return result


@router.post("/approvals", response_model=ApprovalResponse)
async def create_approval(
    approval_in: ApprovalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Demander une validation"""
    deliverable = db.query(Deliverable).filter(
        Deliverable.id == approval_in.deliverable_id
    ).first()
    if not deliverable:
        raise HTTPException(status_code=404, detail="Deliverable not found")
    
    # Change deliverable status to "to_review"
    deliverable.status = DeliverableStatus.TO_REVIEW
    
    approval = Approval(
        deliverable_id=approval_in.deliverable_id,
        status=ApprovalStatus.PENDING,
        feedback=approval_in.feedback
    )
    db.add(approval)
    db.commit()
    db.refresh(approval)
    
    return ApprovalResponse(
        id=approval.id,
        deliverable_id=approval.deliverable_id,
        status=ApprovalStatusEnum(approval.status.value),
        feedback=approval.feedback,
        requested_at=approval.requested_at,
        deliverable_name=deliverable.name,
        project_name=deliverable.project.name if deliverable.project else None,
        client_name=deliverable.project.client.name if deliverable.project and deliverable.project.client else None
    )


@router.put("/approvals/{approval_id}/decide")
async def decide_approval(
    approval_id: int,
    status: str,  # "approved" or "changes"
    feedback: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Décider d'une validation"""
    approval = db.query(Approval).filter(Approval.id == approval_id).first()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    
    approval.status = status
    approval.feedback = feedback
    approval.decided_at = datetime.utcnow()
    approval.decided_by = current_user.id
    
    # Update deliverable status
    deliverable = db.query(Deliverable).filter(
        Deliverable.id == approval.deliverable_id
    ).first()
    if deliverable:
        if status == "approved":
            deliverable.status = DeliverableStatus.APPROVED
        elif status == "changes":
            deliverable.status = DeliverableStatus.CHANGES_REQUESTED
    
    db.commit()
    
    return {"status": "decided", "decision": status}
