import math

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.authz import Permission, require_permissions
from app.core.enums import AuditEventType, UserRole
from app.core.security import hash_password
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserListResponse, UserResponse, UserSummary, UserUpdate
from app.services.audit import record_audit

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/assignable", response_model=list[UserSummary])
def list_assignable_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_permissions(Permission.LEAD_ASSIGN)),
) -> list[UserSummary]:
    users = db.scalars(
        select(User).where(User.role == UserRole.SALES_REP, User.is_active.is_(True)).order_by(User.full_name)
    ).all()
    return [UserSummary.model_validate(user) for user in users]


@router.get("", response_model=UserListResponse)
def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(require_permissions(Permission.USER_MANAGE)),
) -> UserListResponse:
    total = db.scalar(select(func.count()).select_from(User)) or 0
    users = db.scalars(
        select(User).order_by(User.created_at.desc(), User.id.desc()).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return UserListResponse(
        items=[UserResponse.model_validate(user) for user in users],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total else 0,
    )


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permissions(Permission.USER_MANAGE)),
) -> UserResponse:
    user = User(
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
        role=payload.role,
        is_active=payload.is_active,
    )
    db.add(user)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Email is already registered") from exc
    record_audit(
        db,
        actor_user_id=actor.id,
        event_type=AuditEventType.USER_CREATED,
        entity_type="user",
        entity_id=user.id,
        metadata={"role": user.role.value},
    )
    db.commit()
    db.refresh(user)
    return UserResponse.model_validate(user)


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permissions(Permission.USER_MANAGE)),
) -> UserResponse:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    if not payload.model_fields_set:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No fields provided for update")
    if user.id == actor.id and payload.is_active is False:
        raise HTTPException(status.HTTP_409_CONFLICT, "You cannot deactivate your own account")
    previous_role = user.role
    previous_active = user.is_active
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    if previous_role != user.role:
        record_audit(
            db,
            actor_user_id=actor.id,
            event_type=AuditEventType.ROLE_CHANGED,
            entity_type="user",
            entity_id=user.id,
            metadata={"from": previous_role.value, "to": user.role.value},
        )
    if previous_active != user.is_active:
        record_audit(
            db,
            actor_user_id=actor.id,
            event_type=(
                AuditEventType.USER_ACTIVATED if user.is_active else AuditEventType.USER_DEACTIVATED
            ),
            entity_type="user",
            entity_id=user.id,
        )
    db.commit()
    db.refresh(user)
    return UserResponse.model_validate(user)
