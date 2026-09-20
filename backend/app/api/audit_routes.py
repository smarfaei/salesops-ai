import math

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.authz import Permission, require_permissions
from app.core.enums import AuditEventType
from app.db.session import get_db
from app.models.audit import AuditLog
from app.models.user import User
from app.schemas.audit import AuditLogListResponse, AuditLogResponse

router = APIRouter(prefix="/audit-logs", tags=["audit"])


@router.get("", response_model=AuditLogListResponse)
def list_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    event_type: AuditEventType | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_permissions(Permission.AUDIT_READ)),
) -> AuditLogListResponse:
    filters = [AuditLog.event_type == event_type] if event_type else []
    total = db.scalar(select(func.count()).select_from(AuditLog).where(*filters)) or 0
    logs = db.scalars(
        select(AuditLog)
        .options(selectinload(AuditLog.actor))
        .where(*filters)
        .order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return AuditLogListResponse(
        items=[AuditLogResponse.model_validate(item) for item in logs],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total else 0,
    )
