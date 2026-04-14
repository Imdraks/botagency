"""
Agency Cockpit V2 API - Tasks, Assets, Calendar
"""
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.db.session import get_db
from app.db.models.agency import (
    Client, Deal, Project, Asset, AgencyTask, CalendarEvent,
    AssetKind, TaskStatus, TaskPriority, CalendarEventType,
    DealStatus, DeliverableStatus, Deliverable
)
from app.db.models.user import User
from app.db.models.workspace import WorkspaceMember
from app.api.deps import get_current_user, require_workspace_member
from app.schemas.agency import (
    # Task
    TaskCreate, TaskUpdate, TaskResponse,
    TaskStatus as TaskStatusEnum,
    TaskPriority as TaskPriorityEnum,
    # Asset
    AssetCreate, AssetUpdate, AssetResponse,
    AssetKind as AssetKindEnum,
    # Calendar
    CalendarEventCreate, CalendarEventUpdate, CalendarEventResponse,
    CalendarEventType as CalendarEventTypeEnum
)

router = APIRouter(prefix="/agency", tags=["agency-tasks-assets"])


def _get_ws_id(current_user: User, db: Session) -> int:
    """Get workspace_id from current user"""
    ws_id = getattr(current_user, 'workspace_id', None)
    if not ws_id:
        member = db.query(WorkspaceMember).filter(WorkspaceMember.user_id == current_user.id).first()
        ws_id = member.workspace_id if member else None
    return ws_id


# ============================================================================
# TASKS
# ============================================================================

@router.get("/tasks", response_model=List[TaskResponse])
async def list_tasks(
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    project_id: Optional[int] = Query(None),
    deal_id: Optional[int] = Query(None),
    assignee_id: Optional[int] = Query(None),
    include_done: bool = Query(False),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_workspace_member)
):
    """Liste des tâches du workspace"""
    ws_id = _get_ws_id(current_user, db)
    
    # Filter tasks by workspace: tasks linked to projects/deals belonging to workspace clients
    query = db.query(AgencyTask).outerjoin(
        Project, AgencyTask.project_id == Project.id
    ).outerjoin(
        Deal, AgencyTask.deal_id == Deal.id
    ).outerjoin(
        Client, (Project.client_id == Client.id) | (Deal.client_id == Client.id)
    ).filter(Client.workspace_id == ws_id)
    
    if status:
        # Convert string to enum (case-insensitive)
        try:
            status_enum = TaskStatus(status.lower())
            query = query.filter(AgencyTask.status == status_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    elif not include_done:
        query = query.filter(AgencyTask.status != TaskStatus.DONE)
    
    if priority:
        # Convert string to enum (case-insensitive)
        try:
            priority_enum = TaskPriority(priority.lower())
            query = query.filter(AgencyTask.priority == priority_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid priority: {priority}")
    if project_id:
        query = query.filter(AgencyTask.project_id == project_id)
    if deal_id:
        query = query.filter(AgencyTask.deal_id == deal_id)
    if assignee_id:
        query = query.filter(AgencyTask.assignee_id == assignee_id)
    
    tasks = query.order_by(
        AgencyTask.priority.desc(),
        AgencyTask.due_date.asc().nullslast()
    ).offset(skip).limit(limit).all()
    
    now = datetime.utcnow()
    
    result = []
    for task in tasks:
        is_overdue = False
        if task.due_date and task.due_date < now and task.status != TaskStatus.DONE:
            is_overdue = True
        
        result.append(TaskResponse(
            id=task.id,
            project_id=task.project_id,
            deal_id=task.deal_id,
            title=task.title,
            description=task.description,
            status=TaskStatusEnum(task.status.value),
            priority=TaskPriorityEnum(task.priority.value) if task.priority else TaskPriorityEnum.MEDIUM,
            due_date=task.due_date,
            assignee_id=task.assignee_id,
            is_auto_generated=task.is_auto_generated or False,
            auto_type=task.auto_type,
            created_at=task.created_at,
            updated_at=task.updated_at,
            project_name=task.project.name if task.project else None,
            deal_title=task.deal.title if task.deal else None,
            client_name=task.project.client.name if task.project and task.project.client else (
                task.deal.client.name if task.deal and task.deal.client else None
            ),
            assignee_name=task.assignee.email if task.assignee else None,
            is_overdue=is_overdue
        ))
    
    return result


@router.post("/tasks", response_model=TaskResponse)
async def create_task(
    task_in: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_workspace_member)
):
    """Créer une nouvelle tâche"""
    ws_id = _get_ws_id(current_user, db)
    
    # Validate project belongs to workspace
    if task_in.project_id:
        project = db.query(Project).join(Client).filter(
            Project.id == task_in.project_id,
            Client.workspace_id == ws_id
        ).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
    
    # Validate deal belongs to workspace
    if task_in.deal_id:
        deal = db.query(Deal).join(Client).filter(
            Deal.id == task_in.deal_id,
            Client.workspace_id == ws_id
        ).first()
        if not deal:
            raise HTTPException(status_code=404, detail="Deal not found")
    
    task = AgencyTask(
        project_id=task_in.project_id,
        deal_id=task_in.deal_id,
        title=task_in.title,
        description=task_in.description,
        status=task_in.status.value if task_in.status else TaskStatus.TODO,
        priority=task_in.priority.value if task_in.priority else TaskPriority.MEDIUM,
        due_date=task_in.due_date,
        assignee_id=task_in.assignee_id or current_user.id,
        is_auto_generated=False
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    
    return TaskResponse(
        id=task.id,
        project_id=task.project_id,
        deal_id=task.deal_id,
        title=task.title,
        description=task.description,
        status=TaskStatusEnum(task.status.value),
        priority=TaskPriorityEnum(task.priority.value) if task.priority else TaskPriorityEnum.MEDIUM,
        due_date=task.due_date,
        assignee_id=task.assignee_id,
        is_auto_generated=task.is_auto_generated or False,
        auto_type=task.auto_type,
        created_at=task.created_at,
        updated_at=task.updated_at
    )


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_workspace_member)
):
    """Détails d'une tâche"""
    ws_id = _get_ws_id(current_user, db)
    task = db.query(AgencyTask).outerjoin(
        Project, AgencyTask.project_id == Project.id
    ).outerjoin(
        Deal, AgencyTask.deal_id == Deal.id
    ).outerjoin(
        Client, (Project.client_id == Client.id) | (Deal.client_id == Client.id)
    ).filter(AgencyTask.id == task_id, Client.workspace_id == ws_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    now = datetime.utcnow()
    is_overdue = False
    if task.due_date and task.due_date < now and task.status != TaskStatus.DONE:
        is_overdue = True
    
    return TaskResponse(
        id=task.id,
        project_id=task.project_id,
        deal_id=task.deal_id,
        title=task.title,
        description=task.description,
        status=TaskStatusEnum(task.status.value),
        priority=TaskPriorityEnum(task.priority.value) if task.priority else TaskPriorityEnum.MEDIUM,
        due_date=task.due_date,
        assignee_id=task.assignee_id,
        is_auto_generated=task.is_auto_generated or False,
        auto_type=task.auto_type,
        created_at=task.created_at,
        updated_at=task.updated_at,
        project_name=task.project.name if task.project else None,
        deal_title=task.deal.title if task.deal else None,
        client_name=task.project.client.name if task.project and task.project.client else (
            task.deal.client.name if task.deal and task.deal.client else None
        ),
        assignee_name=task.assignee.email if task.assignee else None,
        is_overdue=is_overdue
    )


@router.put("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_in: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_workspace_member)
):
    """Mettre à jour une tâche"""
    ws_id = _get_ws_id(current_user, db)
    task = db.query(AgencyTask).outerjoin(
        Project, AgencyTask.project_id == Project.id
    ).outerjoin(
        Deal, AgencyTask.deal_id == Deal.id
    ).outerjoin(
        Client, (Project.client_id == Client.id) | (Deal.client_id == Client.id)
    ).filter(AgencyTask.id == task_id, Client.workspace_id == ws_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task_in.project_id is not None:
        task.project_id = task_in.project_id
    if task_in.deal_id is not None:
        task.deal_id = task_in.deal_id
    if task_in.title is not None:
        task.title = task_in.title
    if task_in.description is not None:
        task.description = task_in.description
    if task_in.status is not None:
        task.status = task_in.status.value
    if task_in.priority is not None:
        task.priority = task_in.priority.value
    if task_in.due_date is not None:
        task.due_date = task_in.due_date
    if task_in.assignee_id is not None:
        task.assignee_id = task_in.assignee_id
    
    db.commit()
    db.refresh(task)
    
    return await get_task(task_id, db, current_user)


@router.put("/tasks/{task_id}/status")
async def update_task_status(
    task_id: int,
    status: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_workspace_member)
):
    """Quick status update"""
    ws_id = _get_ws_id(current_user, db)
    task = db.query(AgencyTask).outerjoin(
        Project, AgencyTask.project_id == Project.id
    ).outerjoin(
        Deal, AgencyTask.deal_id == Deal.id
    ).outerjoin(
        Client, (Project.client_id == Client.id) | (Deal.client_id == Client.id)
    ).filter(AgencyTask.id == task_id, Client.workspace_id == ws_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task.status = status
    db.commit()
    
    return {"status": "updated", "new_status": status}


@router.delete("/tasks/{task_id}")
async def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_workspace_member)
):
    """Supprimer une tâche"""
    ws_id = _get_ws_id(current_user, db)
    task = db.query(AgencyTask).outerjoin(
        Project, AgencyTask.project_id == Project.id
    ).outerjoin(
        Deal, AgencyTask.deal_id == Deal.id
    ).outerjoin(
        Client, (Project.client_id == Client.id) | (Deal.client_id == Client.id)
    ).filter(AgencyTask.id == task_id, Client.workspace_id == ws_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    db.delete(task)
    db.commit()
    return {"status": "deleted"}


# ============================================================================
# AUTOMATIONS - Generate follow-up tasks
# ============================================================================

@router.post("/tasks/generate-followups")
async def generate_followup_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_workspace_member)
):
    """
    Génère automatiquement des tâches de relance:
    - Deals avec quote_sent depuis 3+ jours sans réponse
    - Livrables avec deadline < 72h pas encore approved
    """
    ws_id = _get_ws_id(current_user, db)
    now = datetime.utcnow()
    three_days_ago = now - timedelta(days=3)
    urgency_threshold = now + timedelta(hours=72)
    
    tasks_created = 0
    
    # 1. Deals quote_sent sans réponse depuis 3 jours (filtered by workspace)
    stale_quotes = db.query(Deal).join(Client).filter(
        Client.workspace_id == ws_id,
        Deal.status == DealStatus.QUOTE_SENT,
        Deal.last_contact_at <= three_days_ago
    ).all()
    
    for deal in stale_quotes:
        # Check if followup task already exists
        existing = db.query(AgencyTask).filter(
            AgencyTask.deal_id == deal.id,
            AgencyTask.auto_type == "quote_followup",
            AgencyTask.status != TaskStatus.DONE
        ).first()
        
        if not existing:
            task = AgencyTask(
                deal_id=deal.id,
                title=f"Relancer devis: {deal.title}",
                description=f"Devis envoyé il y a {(now - deal.last_contact_at).days} jours sans réponse",
                status=TaskStatus.TODO,
                priority=TaskPriority.HIGH,
                due_date=now,
                is_auto_generated=True,
                auto_type="quote_followup"
            )
            db.add(task)
            tasks_created += 1
    
    # 2. Livrables avec deadline urgente (filtered by workspace)
    urgent_deliverables = db.query(Deliverable).join(Project).join(Client).filter(
        Client.workspace_id == ws_id,
        Deliverable.due_date <= urgency_threshold,
        Deliverable.due_date >= now,
        Deliverable.status.notin_([DeliverableStatus.APPROVED, DeliverableStatus.DELIVERED])
    ).all()
    
    for deliverable in urgent_deliverables:
        existing = db.query(AgencyTask).filter(
            AgencyTask.project_id == deliverable.project_id,
            AgencyTask.auto_type == "deadline_alert",
            AgencyTask.title.like(f"%{deliverable.name}%"),
            AgencyTask.status != TaskStatus.DONE
        ).first()
        
        if not existing:
            days_left = (deliverable.due_date - now).days
            task = AgencyTask(
                project_id=deliverable.project_id,
                title=f"Urgent: {deliverable.name} - {days_left}j restants",
                description=f"Livrable dû le {deliverable.due_date.strftime('%d/%m/%Y')}",
                status=TaskStatus.TODO,
                priority=TaskPriority.HIGH,
                due_date=now,
                is_auto_generated=True,
                auto_type="deadline_alert"
            )
            db.add(task)
            tasks_created += 1
    
    db.commit()
    
    return {
        "status": "ok",
        "tasks_created": tasks_created
    }


# ============================================================================
# ASSETS
# ============================================================================

@router.get("/assets", response_model=List[AssetResponse])
async def list_assets(
    project_id: Optional[int] = Query(None),
    kind: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_workspace_member)
):
    """Liste des assets du workspace"""
    ws_id = _get_ws_id(current_user, db)
    query = db.query(Asset).join(Project).join(Client).filter(Client.workspace_id == ws_id)
    
    if project_id:
        query = query.filter(Asset.project_id == project_id)
    if kind:
        query = query.filter(Asset.kind == kind)
    
    assets = query.order_by(Asset.created_at.desc()).offset(skip).limit(limit).all()
    
    result = []
    for asset in assets:
        result.append(AssetResponse(
            id=asset.id,
            project_id=asset.project_id,
            kind=AssetKindEnum(asset.kind.value) if asset.kind else AssetKindEnum.LINK,
            name=asset.name,
            url=asset.url,
            version=asset.version,
            created_at=asset.created_at,
            created_by=asset.created_by,
            project_name=asset.project.name if asset.project else None,
            client_name=asset.project.client.name if asset.project and asset.project.client else None
        ))
    
    return result


@router.post("/assets", response_model=AssetResponse)
async def create_asset(
    asset_in: AssetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_workspace_member)
):
    """Créer un nouvel asset"""
    ws_id = _get_ws_id(current_user, db)
    project = db.query(Project).join(Client).filter(
        Project.id == asset_in.project_id,
        Client.workspace_id == ws_id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    asset = Asset(
        project_id=asset_in.project_id,
        workspace_id=project.workspace_id,  # Inherit from project
        kind=asset_in.kind.value if asset_in.kind else AssetKind.LINK,
        name=asset_in.name,
        url=asset_in.url,
        version=asset_in.version,
        created_by=current_user.id
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    
    return AssetResponse(
        id=asset.id,
        project_id=asset.project_id,
        kind=AssetKindEnum(asset.kind.value) if asset.kind else AssetKindEnum.LINK,
        name=asset.name,
        url=asset.url,
        version=asset.version,
        created_at=asset.created_at,
        created_by=asset.created_by,
        project_name=project.name,
        client_name=project.client.name if project.client else None
    )


@router.get("/assets/{asset_id}", response_model=AssetResponse)
async def get_asset(
    asset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_workspace_member)
):
    """Détails d'un asset"""
    ws_id = _get_ws_id(current_user, db)
    asset = db.query(Asset).join(Project).join(Client).filter(
        Asset.id == asset_id,
        Client.workspace_id == ws_id
    ).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    return AssetResponse(
        id=asset.id,
        project_id=asset.project_id,
        kind=AssetKindEnum(asset.kind.value) if asset.kind else AssetKindEnum.LINK,
        name=asset.name,
        url=asset.url,
        version=asset.version,
        created_at=asset.created_at,
        created_by=asset.created_by,
        project_name=asset.project.name if asset.project else None,
        client_name=asset.project.client.name if asset.project and asset.project.client else None
    )


@router.put("/assets/{asset_id}", response_model=AssetResponse)
async def update_asset(
    asset_id: int,
    asset_in: AssetUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_workspace_member)
):
    """Mettre à jour un asset"""
    ws_id = _get_ws_id(current_user, db)
    asset = db.query(Asset).join(Project).join(Client).filter(
        Asset.id == asset_id,
        Client.workspace_id == ws_id
    ).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    if asset_in.kind is not None:
        asset.kind = asset_in.kind.value
    if asset_in.name is not None:
        asset.name = asset_in.name
    if asset_in.url is not None:
        asset.url = asset_in.url
    if asset_in.version is not None:
        asset.version = asset_in.version
    
    db.commit()
    db.refresh(asset)
    
    return await get_asset(asset_id, db, current_user)


@router.delete("/assets/{asset_id}")
async def delete_asset(
    asset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_workspace_member)
):
    """Supprimer un asset"""
    ws_id = _get_ws_id(current_user, db)
    asset = db.query(Asset).join(Project).join(Client).filter(
        Asset.id == asset_id,
        Client.workspace_id == ws_id
    ).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    db.delete(asset)
    db.commit()
    return {"status": "deleted"}


# ============================================================================
# CALENDAR
# ============================================================================

@router.get("/calendar", response_model=List[CalendarEventResponse])
async def list_calendar_events(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    project_id: Optional[int] = Query(None),
    event_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_workspace_member)
):
    """Liste des événements du calendrier du workspace"""
    ws_id = _get_ws_id(current_user, db)
    query = db.query(CalendarEvent).join(Project).join(Client).filter(Client.workspace_id == ws_id)
    
    if start_date:
        query = query.filter(CalendarEvent.start >= start_date)
    if end_date:
        query = query.filter(CalendarEvent.start <= end_date)
    if project_id:
        query = query.filter(CalendarEvent.project_id == project_id)
    if event_type:
        query = query.filter(CalendarEvent.type == event_type)
    
    events = query.order_by(CalendarEvent.start.asc()).all()
    
    result = []
    for event in events:
        result.append(CalendarEventResponse(
            id=event.id,
            project_id=event.project_id,
            title=event.title,
            type=CalendarEventTypeEnum(event.type.value) if event.type else CalendarEventTypeEnum.OTHER,
            start=event.start,
            end=event.end,
            all_day=event.all_day or False,
            location=event.location,
            notes=event.notes,
            created_at=event.created_at,
            updated_at=event.updated_at,
            project_name=event.project.name if event.project else None,
            client_name=event.project.client.name if event.project and event.project.client else None
        ))
    
    return result


@router.post("/calendar", response_model=CalendarEventResponse)
async def create_calendar_event(
    event_in: CalendarEventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_workspace_member)
):
    """Créer un événement"""
    ws_id = _get_ws_id(current_user, db)
    if event_in.project_id:
        project = db.query(Project).join(Client).filter(
            Project.id == event_in.project_id,
            Client.workspace_id == ws_id
        ).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
    
    event = CalendarEvent(
        project_id=event_in.project_id,
        title=event_in.title,
        type=event_in.type.value if event_in.type else CalendarEventType.OTHER,
        start=event_in.start,
        end=event_in.end,
        all_day=event_in.all_day or False,
        location=event_in.location,
        notes=event_in.notes
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    
    return CalendarEventResponse(
        id=event.id,
        project_id=event.project_id,
        title=event.title,
        type=CalendarEventTypeEnum(event.type.value) if event.type else CalendarEventTypeEnum.OTHER,
        start=event.start,
        end=event.end,
        all_day=event.all_day or False,
        location=event.location,
        notes=event.notes,
        created_at=event.created_at,
        updated_at=event.updated_at,
        project_name=event.project.name if event.project else None,
        client_name=event.project.client.name if event.project and event.project.client else None
    )


@router.get("/calendar/{event_id}", response_model=CalendarEventResponse)
async def get_calendar_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_workspace_member)
):
    """Détails d'un événement"""
    ws_id = _get_ws_id(current_user, db)
    event = db.query(CalendarEvent).join(Project).join(Client).filter(
        CalendarEvent.id == event_id,
        Client.workspace_id == ws_id
    ).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    return CalendarEventResponse(
        id=event.id,
        project_id=event.project_id,
        title=event.title,
        type=CalendarEventTypeEnum(event.type.value) if event.type else CalendarEventTypeEnum.OTHER,
        start=event.start,
        end=event.end,
        all_day=event.all_day or False,
        location=event.location,
        notes=event.notes,
        created_at=event.created_at,
        updated_at=event.updated_at,
        project_name=event.project.name if event.project else None,
        client_name=event.project.client.name if event.project and event.project.client else None
    )


@router.put("/calendar/{event_id}", response_model=CalendarEventResponse)
async def update_calendar_event(
    event_id: int,
    event_in: CalendarEventUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_workspace_member)
):
    """Mettre à jour un événement"""
    ws_id = _get_ws_id(current_user, db)
    event = db.query(CalendarEvent).join(Project).join(Client).filter(
        CalendarEvent.id == event_id,
        Client.workspace_id == ws_id
    ).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    if event_in.project_id is not None:
        event.project_id = event_in.project_id
    if event_in.title is not None:
        event.title = event_in.title
    if event_in.type is not None:
        event.type = event_in.type.value
    if event_in.start is not None:
        event.start = event_in.start
    if event_in.end is not None:
        event.end = event_in.end
    if event_in.all_day is not None:
        event.all_day = event_in.all_day
    if event_in.location is not None:
        event.location = event_in.location
    if event_in.notes is not None:
        event.notes = event_in.notes
    
    db.commit()
    db.refresh(event)
    
    return await get_calendar_event(event_id, db, current_user)


@router.delete("/calendar/{event_id}")
async def delete_calendar_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_workspace_member)
):
    """Supprimer un événement"""
    ws_id = _get_ws_id(current_user, db)
    event = db.query(CalendarEvent).join(Project).join(Client).filter(
        CalendarEvent.id == event_id,
        Client.workspace_id == ws_id
    ).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    db.delete(event)
    db.commit()
    return {"status": "deleted"}
