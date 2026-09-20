from datetime import datetime, timezone

from app.core.enums import TaskStatus
from app.models.task import SalesTask
from app.schemas.task import TaskCreate, TaskUpdate


def create_task(lead_id: int, payload: TaskCreate) -> SalesTask:
    return SalesTask(lead_id=lead_id, **payload.model_dump())


def update_task(task: SalesTask, payload: TaskUpdate) -> bool:
    updates = payload.model_dump(exclude_unset=True)
    changed = False
    for field, value in updates.items():
        if getattr(task, field) != value:
            setattr(task, field, value)
            changed = True
    if "status" in updates:
        task.completed_at = datetime.now(timezone.utc) if task.status == TaskStatus.COMPLETED else None
    return changed


def complete_task(task: SalesTask) -> bool:
    if task.status == TaskStatus.COMPLETED:
        return False
    task.status = TaskStatus.COMPLETED
    task.completed_at = datetime.now(timezone.utc)
    return True


def cancel_task(task: SalesTask) -> bool:
    if task.status == TaskStatus.CANCELLED:
        return False
    task.status = TaskStatus.CANCELLED
    task.completed_at = None
    return True
