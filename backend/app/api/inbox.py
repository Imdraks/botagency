"""
Inbox API - Quick capture and triage
"""
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.db.session import get_db
from app.db.models.user import User
from app.db.models.workspace import Workspace, WorkspaceMember, InboxItem, InboxStatus, InboxType
from app.db.models.agency import Client, Deal, Project, Deliverable, AgencyTask, DealStatus, ProjectStatus, DeliverableStatus, TaskStatus, TaskPriority
from app.api.deps import get_current_user
from app.api.workspace import _user_has_workspace_access
from app.schemas.inbox import (
    InboxItemCreate, InboxItemUpdate, InboxItemResponse, InboxListResponse,
    TriageRequest, TriageResponse, TriageTarget,
    ParsedQuickCapture, QuickCaptureTestRequest, QuickCaptureTestResponse,
)

router = APIRouter(prefix="/inbox", tags=["inbox"])


# ============================================================================
# INBOX CRUD
# ============================================================================

@router.get("", response_model=InboxListResponse)
async def list_inbox_items(
    workspace_id: int,
    status_filter: Optional[InboxStatus] = None,
    type_filter: Optional[InboxType] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List inbox items for a workspace"""
    if not _user_has_workspace_access(db, current_user.id, workspace_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    query = db.query(InboxItem).filter(InboxItem.workspace_id == workspace_id)
    
    if status_filter:
        query = query.filter(InboxItem.status == status_filter)
    
    if type_filter:
        query = query.filter(InboxItem.type == type_filter)
    
    # Order: inbox first, then by created_at desc
    query = query.order_by(
        InboxItem.status != InboxStatus.INBOX,  # inbox items first (False sorts before True)
        InboxItem.created_at.desc()
    )
    
    total = query.count()
    items = query.offset(offset).limit(limit).all()
    
    # Get counts
    inbox_count = db.query(func.count(InboxItem.id)).filter(
        InboxItem.workspace_id == workspace_id,
        InboxItem.status == InboxStatus.INBOX
    ).scalar() or 0
    
    triaged_count = db.query(func.count(InboxItem.id)).filter(
        InboxItem.workspace_id == workspace_id,
        InboxItem.status == InboxStatus.TRIAGED
    ).scalar() or 0
    
    done_count = db.query(func.count(InboxItem.id)).filter(
        InboxItem.workspace_id == workspace_id,
        InboxItem.status == InboxStatus.DONE
    ).scalar() or 0
    
    now = datetime.utcnow()
    
    return InboxListResponse(
        items=[
            InboxItemResponse(
                id=item.id,
                workspace_id=item.workspace_id,
                created_by=item.created_by,
                creator_name=item.creator.full_name if item.creator else None,
                text=item.text,
                link=item.link,
                type=item.type,
                tags=item.tags or [],
                status=item.status,
                due_date=item.due_date,
                mentioned_client=item.mentioned_client,
                mentioned_project=item.mentioned_project,
                triaged_to_type=item.triaged_to_type,
                triaged_to_id=item.triaged_to_id,
                triaged_at=item.triaged_at,
                created_at=item.created_at,
                updated_at=item.updated_at,
                is_overdue=item.due_date and item.due_date < now.date() if item.due_date else False,
                age_hours=int((now - item.created_at).total_seconds() / 3600) if item.created_at else None,
            )
            for item in items
        ],
        total=total,
        inbox_count=inbox_count,
        triaged_count=triaged_count,
        done_count=done_count,
    )


@router.post("", response_model=InboxItemResponse, status_code=status.HTTP_201_CREATED)
async def create_inbox_item(
    workspace_id: int,
    data: InboxItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create inbox item with quick capture.
    Format: "Text @client #project due:YYYY-MM-DD type:idea"
    Target: < 5 seconds to capture an idea.
    """
    if not _user_has_workspace_access(db, current_user.id, workspace_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Parse text for tags, mentions, due dates
    parsed = InboxItem.parse_text(data.text)
    
    item = InboxItem(
        workspace_id=workspace_id,
        created_by=current_user.id,
        text=data.text,  # Keep original text
        link=data.link,
        type=data.type or parsed["type"],
        tags=data.tags or parsed["tags"],
        due_date=data.due_date or parsed["due_date"],
        mentioned_client=parsed["mentioned_client"],
        mentioned_project=parsed["mentioned_project"],
        status=InboxStatus.INBOX,
    )
    
    db.add(item)
    db.commit()
    db.refresh(item)
    
    return InboxItemResponse(
        id=item.id,
        workspace_id=item.workspace_id,
        created_by=item.created_by,
        creator_name=current_user.full_name,
        text=item.text,
        link=item.link,
        type=item.type,
        tags=item.tags or [],
        status=item.status,
        due_date=item.due_date,
        mentioned_client=item.mentioned_client,
        mentioned_project=item.mentioned_project,
        created_at=item.created_at,
        updated_at=item.updated_at,
        is_overdue=False,
        age_hours=0,
    )


@router.get("/{item_id}", response_model=InboxItemResponse)
async def get_inbox_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific inbox item"""
    item = db.query(InboxItem).filter(InboxItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    if not _user_has_workspace_access(db, current_user.id, item.workspace_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    now = datetime.utcnow()
    
    return InboxItemResponse(
        id=item.id,
        workspace_id=item.workspace_id,
        created_by=item.created_by,
        creator_name=item.creator.full_name if item.creator else None,
        text=item.text,
        link=item.link,
        type=item.type,
        tags=item.tags or [],
        status=item.status,
        due_date=item.due_date,
        mentioned_client=item.mentioned_client,
        mentioned_project=item.mentioned_project,
        triaged_to_type=item.triaged_to_type,
        triaged_to_id=item.triaged_to_id,
        triaged_at=item.triaged_at,
        created_at=item.created_at,
        updated_at=item.updated_at,
        is_overdue=item.due_date and item.due_date < now.date() if item.due_date else False,
        age_hours=int((now - item.created_at).total_seconds() / 3600) if item.created_at else None,
    )


@router.patch("/{item_id}", response_model=InboxItemResponse)
async def update_inbox_item(
    item_id: int,
    data: InboxItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update an inbox item"""
    item = db.query(InboxItem).filter(InboxItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    if not _user_has_workspace_access(db, current_user.id, item.workspace_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(item, field, value)
    
    db.commit()
    db.refresh(item)
    
    now = datetime.utcnow()
    
    return InboxItemResponse(
        id=item.id,
        workspace_id=item.workspace_id,
        created_by=item.created_by,
        creator_name=item.creator.full_name if item.creator else None,
        text=item.text,
        link=item.link,
        type=item.type,
        tags=item.tags or [],
        status=item.status,
        due_date=item.due_date,
        mentioned_client=item.mentioned_client,
        mentioned_project=item.mentioned_project,
        triaged_to_type=item.triaged_to_type,
        triaged_to_id=item.triaged_to_id,
        triaged_at=item.triaged_at,
        created_at=item.created_at,
        updated_at=item.updated_at,
        is_overdue=item.due_date and item.due_date < now.date() if item.due_date else False,
        age_hours=int((now - item.created_at).total_seconds() / 3600) if item.created_at else None,
    )


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_inbox_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete an inbox item"""
    item = db.query(InboxItem).filter(InboxItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    if not _user_has_workspace_access(db, current_user.id, item.workspace_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    db.delete(item)
    db.commit()


# ============================================================================
# TRIAGE
# ============================================================================

@router.post("/{item_id}/triage", response_model=TriageResponse)
async def triage_inbox_item(
    item_id: int,
    data: TriageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Triage inbox item to Task, Deal, Project, or Deliverable.
    One-click conversion from inbox to actionable item.
    """
    item = db.query(InboxItem).filter(InboxItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    if not _user_has_workspace_access(db, current_user.id, item.workspace_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    if item.status == InboxStatus.TRIAGED:
        raise HTTPException(status_code=400, detail="Item already triaged")
    
    created_id = None
    message = ""
    
    if data.target == TriageTarget.TASK:
        # Create Task
        task = AgencyTask(
            project_id=data.task_project_id,
            title=data.task_title or item.text[:200],
            description=item.text if len(item.text) > 200 else None,
            status=TaskStatus.TODO,
            priority=TaskPriority[data.task_priority.upper()] if data.task_priority else TaskPriority.MEDIUM,
            due_date=data.task_due_date or item.due_date,
            assignee_id=data.task_assignee_id,
        )
        db.add(task)
        db.flush()
        created_id = task.id
        message = f"Tâche créée: {task.title}"
    
    elif data.target == TriageTarget.DEAL:
        # Need client_id
        if not data.deal_client_id:
            raise HTTPException(status_code=400, detail="client_id required for deal")
        
        deal = Deal(
            client_id=data.deal_client_id,
            title=data.deal_title or item.text[:200],
            status=DealStatus.NEW,
            value=data.deal_value,
            owner_id=current_user.id,
            notes=item.text,
        )
        db.add(deal)
        db.flush()
        created_id = deal.id
        message = f"Deal créé: {deal.title}"
    
    elif data.target == TriageTarget.PROJECT:
        # Need client_id
        if not data.project_client_id:
            raise HTTPException(status_code=400, detail="client_id required for project")
        
        project = Project(
            client_id=data.project_client_id,
            name=data.project_name or item.text[:200],
            status=ProjectStatus.ACTIVE,
            deadline=data.project_deadline,
            owner_id=current_user.id,
            description=item.text,
        )
        db.add(project)
        db.flush()
        created_id = project.id
        message = f"Projet créé: {project.name}"
    
    elif data.target == TriageTarget.DELIVERABLE:
        # Need project_id
        if not data.deliverable_project_id:
            raise HTTPException(status_code=400, detail="project_id required for deliverable")
        
        deliverable = Deliverable(
            project_id=data.deliverable_project_id,
            name=data.deliverable_name or item.text[:200],
            type=data.deliverable_type or "other",
            status=DeliverableStatus.DRAFT,
            due_date=data.deliverable_due_date or item.due_date,
            notes=item.text,
        )
        db.add(deliverable)
        db.flush()
        created_id = deliverable.id
        message = f"Livrable créé: {deliverable.name}"
    
    # Mark item as triaged
    item.status = InboxStatus.TRIAGED
    item.triaged_to_type = data.target.value
    item.triaged_to_id = created_id
    item.triaged_at = datetime.utcnow()
    item.triaged_by = current_user.id
    
    db.commit()
    
    return TriageResponse(
        success=True,
        inbox_item_id=item.id,
        triaged_to_type=data.target.value,
        triaged_to_id=created_id,
        message=message,
    )


@router.post("/{item_id}/done", response_model=InboxItemResponse)
async def mark_inbox_done(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark inbox item as done without triaging"""
    item = db.query(InboxItem).filter(InboxItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    if not _user_has_workspace_access(db, current_user.id, item.workspace_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    item.status = InboxStatus.DONE
    db.commit()
    db.refresh(item)
    
    now = datetime.utcnow()
    
    return InboxItemResponse(
        id=item.id,
        workspace_id=item.workspace_id,
        created_by=item.created_by,
        creator_name=item.creator.full_name if item.creator else None,
        text=item.text,
        link=item.link,
        type=item.type,
        tags=item.tags or [],
        status=item.status,
        due_date=item.due_date,
        mentioned_client=item.mentioned_client,
        mentioned_project=item.mentioned_project,
        triaged_to_type=item.triaged_to_type,
        triaged_to_id=item.triaged_to_id,
        triaged_at=item.triaged_at,
        created_at=item.created_at,
        updated_at=item.updated_at,
        is_overdue=False,
        age_hours=int((now - item.created_at).total_seconds() / 3600) if item.created_at else None,
    )


@router.post("/{item_id}/archive", response_model=InboxItemResponse)
async def archive_inbox_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Archive inbox item"""
    item = db.query(InboxItem).filter(InboxItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    if not _user_has_workspace_access(db, current_user.id, item.workspace_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    item.status = InboxStatus.ARCHIVED
    db.commit()
    db.refresh(item)
    
    now = datetime.utcnow()
    
    return InboxItemResponse(
        id=item.id,
        workspace_id=item.workspace_id,
        created_by=item.created_by,
        creator_name=item.creator.full_name if item.creator else None,
        text=item.text,
        link=item.link,
        type=item.type,
        tags=item.tags or [],
        status=item.status,
        due_date=item.due_date,
        mentioned_client=item.mentioned_client,
        mentioned_project=item.mentioned_project,
        triaged_to_type=item.triaged_to_type,
        triaged_to_id=item.triaged_to_id,
        triaged_at=item.triaged_at,
        created_at=item.created_at,
        updated_at=item.updated_at,
        is_overdue=False,
        age_hours=int((now - item.created_at).total_seconds() / 3600) if item.created_at else None,
    )


# ============================================================================
# QUICK CAPTURE PARSING
# ============================================================================

@router.post("/parse", response_model=QuickCaptureTestResponse)
async def test_parse_quick_capture(
    data: QuickCaptureTestRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Test parsing of quick capture text.
    Useful for preview before submitting.
    """
    parsed = InboxItem.parse_text(data.text)
    
    suggested_actions = []
    if parsed["mentioned_client"]:
        suggested_actions.append(f"Link to client: {parsed['mentioned_client']}")
    if parsed["mentioned_project"]:
        suggested_actions.append(f"Link to project: {parsed['mentioned_project']}")
    if parsed["due_date"]:
        suggested_actions.append(f"Due: {parsed['due_date']}")
    if parsed["type"] != InboxType.OTHER:
        suggested_actions.append(f"Type: {parsed['type'].value}")
    
    return QuickCaptureTestResponse(
        parsed=ParsedQuickCapture(
            original_text=data.text,
            clean_text=parsed["clean_text"],
            mentioned_client=parsed["mentioned_client"],
            mentioned_project=parsed["mentioned_project"],
            tags=parsed["tags"],
            due_date=parsed["due_date"],
            type=parsed["type"],
            suggested_actions=suggested_actions,
        )
    )
