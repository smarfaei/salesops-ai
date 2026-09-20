from datetime import datetime, timezone
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import asc, desc, func, select
from sqlalchemy.orm import Session

from app.core.authz import Permission, authorize_lead_access, require_permissions
from app.core.demo import block_in_demo_mode
from app.core.enums import AuditEventType, TaskPriority, TaskStatus, UserRole
from app.db.session import get_db
from app.models.lead import Lead
from app.models.task import SalesTask
from app.models.user import User
from app.schemas.task import TaskCreate, TaskListResponse, TaskResponse, TaskUpdate
from app.services.tasks import cancel_task, complete_task, create_task, update_task
from app.services.audit import record_audit

router = APIRouter(tags=["tasks"])


class TaskTiming(str, Enum):
    overdue = "overdue"
    upcoming = "upcoming"


class DueSort(str, Enum):
    asc = "asc"
    desc = "desc"


def _get_task_or_404(
    db: Session, task_id: int, user: User | None = None, *, write: bool = False
) -> SalesTask:
    task = db.get(SalesTask, task_id)
    if task is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Task not found")
    if user is not None:
        lead = db.get(Lead, task.lead_id)
        if lead is not None:
            authorize_lead_access(user, lead, write=write)
    return task


def _list_tasks(
    db: Session,
    *,
    lead_id: int | None,
    task_status: TaskStatus | None,
    priority: TaskPriority | None,
    timing: TaskTiming | None,
    sort_order: DueSort,
    owner_user_id: int | None = None,
) -> TaskListResponse:
    filters = []
    if lead_id is not None:
        filters.append(SalesTask.lead_id == lead_id)
    if task_status is not None:
        filters.append(SalesTask.status == task_status)
    if priority is not None:
        filters.append(SalesTask.priority == priority)
    now = datetime.now(timezone.utc)
    if timing == TaskTiming.overdue:
        filters.extend((SalesTask.status == TaskStatus.PENDING, SalesTask.due_at < now))
    elif timing == TaskTiming.upcoming:
        filters.extend((SalesTask.status == TaskStatus.PENDING, SalesTask.due_at >= now))
    count_query = select(func.count()).select_from(SalesTask)
    task_query = select(SalesTask)
    if owner_user_id is not None:
        count_query = count_query.join(Lead).where(Lead.owner_user_id == owner_user_id)
        task_query = task_query.join(Lead).where(Lead.owner_user_id == owner_user_id)
    total = db.scalar(count_query.where(*filters)) or 0
    ordering = asc(SalesTask.due_at) if sort_order == DueSort.asc else desc(SalesTask.due_at)
    tasks = db.scalars(
        task_query.where(*filters).order_by(ordering, SalesTask.id.asc())
    ).all()
    return TaskListResponse(
        items=[TaskResponse.model_validate(item) for item in tasks], total=total
    )


@router.post(
    "/leads/{lead_id}/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_task(
    lead_id: int,
    payload: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(Permission.TASK_WRITE)),
) -> TaskResponse:
    lead = db.get(Lead, lead_id)
    if lead is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Lead not found")
    authorize_lead_access(current_user, lead, write=True)
    task = create_task(lead_id, payload)
    db.add(task)
    db.flush()
    record_audit(
        db,
        actor_user_id=current_user.id,
        event_type=AuditEventType.TASK_CREATED,
        entity_type="task",
        entity_id=task.id,
        metadata={"lead_id": lead_id},
    )
    db.commit()
    db.refresh(task)
    return TaskResponse.model_validate(task)


@router.get("/leads/{lead_id}/tasks", response_model=TaskListResponse)
def list_lead_tasks(
    lead_id: int,
    task_status: TaskStatus | None = Query(None, alias="status"),
    priority: TaskPriority | None = None,
    timing: TaskTiming | None = None,
    sort_order: DueSort = DueSort.asc,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(Permission.LEAD_READ)),
) -> TaskListResponse:
    lead = db.get(Lead, lead_id)
    if lead is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Lead not found")
    authorize_lead_access(current_user, lead)
    return _list_tasks(
        db,
        lead_id=lead_id,
        task_status=task_status,
        priority=priority,
        timing=timing,
        sort_order=sort_order,
    )


@router.get("/tasks", response_model=TaskListResponse)
def list_all_tasks(
    task_status: TaskStatus | None = Query(None, alias="status"),
    priority: TaskPriority | None = None,
    timing: TaskTiming | None = None,
    sort_order: DueSort = DueSort.asc,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(Permission.LEAD_READ)),
) -> TaskListResponse:
    return _list_tasks(
        db,
        lead_id=None,
        task_status=task_status,
        priority=priority,
        timing=timing,
        sort_order=sort_order,
        owner_user_id=(current_user.id if current_user.role == UserRole.SALES_REP else None),
    )


@router.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(Permission.LEAD_READ)),
) -> TaskResponse:
    return TaskResponse.model_validate(_get_task_or_404(db, task_id, current_user))


@router.patch("/tasks/{task_id}", response_model=TaskResponse)
def patch_task(
    task_id: int,
    payload: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(Permission.TASK_WRITE)),
) -> TaskResponse:
    task = _get_task_or_404(db, task_id, current_user, write=True)
    if not payload.model_fields_set:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No fields provided for update")
    update_task(task, payload)
    db.commit()
    db.refresh(task)
    return TaskResponse.model_validate(task)


@router.post("/tasks/{task_id}/complete", response_model=TaskResponse)
def mark_task_complete(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(Permission.TASK_WRITE)),
) -> TaskResponse:
    task = _get_task_or_404(db, task_id, current_user, write=True)
    complete_task(task)
    record_audit(
        db,
        actor_user_id=current_user.id,
        event_type=AuditEventType.TASK_COMPLETED,
        entity_type="task",
        entity_id=task.id,
    )
    db.commit()
    db.refresh(task)
    return TaskResponse.model_validate(task)


@router.post("/tasks/{task_id}/cancel", response_model=TaskResponse)
def mark_task_cancelled(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(Permission.TASK_WRITE)),
) -> TaskResponse:
    task = _get_task_or_404(db, task_id, current_user, write=True)
    cancel_task(task)
    record_audit(
        db,
        actor_user_id=current_user.id,
        event_type=AuditEventType.TASK_CANCELLED,
        entity_type="task",
        entity_id=task.id,
    )
    db.commit()
    db.refresh(task)
    return TaskResponse.model_validate(task)


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    _demo_guard: None = Depends(block_in_demo_mode),
    current_user: User = Depends(require_permissions(Permission.TASK_WRITE)),
) -> Response:
    task = _get_task_or_404(db, task_id, current_user, write=True)
    db.delete(task)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
