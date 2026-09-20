from enum import Enum

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.demo import get_request_settings
from app.core.enums import UserRole
from app.core.security import InvalidToken, decode_access_token
from app.db.session import get_db
from app.models.lead import Lead
from app.models.user import User


class Permission(str, Enum):
    LEAD_READ = "lead:read"
    LEAD_CREATE = "lead:create"
    LEAD_EDIT = "lead:edit"
    LEAD_DELETE = "lead:delete"
    LEAD_ASSIGN = "lead:assign"
    PIPELINE_WRITE = "pipeline:write"
    ACTIVITY_WRITE = "activity:write"
    TASK_WRITE = "task:write"
    INTELLIGENCE_WRITE = "intelligence:write"
    ANALYTICS_READ = "analytics:read"
    USER_MANAGE = "user:manage"
    AUDIT_READ = "audit:read"


ROLE_PERMISSIONS: dict[UserRole, frozenset[Permission]] = {
    UserRole.ADMIN: frozenset(Permission),
    UserRole.SALES_MANAGER: frozenset(
        {
            Permission.LEAD_READ,
            Permission.LEAD_CREATE,
            Permission.LEAD_EDIT,
            Permission.LEAD_DELETE,
            Permission.LEAD_ASSIGN,
            Permission.PIPELINE_WRITE,
            Permission.ACTIVITY_WRITE,
            Permission.TASK_WRITE,
            Permission.INTELLIGENCE_WRITE,
            Permission.ANALYTICS_READ,
            Permission.AUDIT_READ,
        }
    ),
    UserRole.SALES_REP: frozenset(
        {
            Permission.LEAD_READ,
            Permission.LEAD_EDIT,
            Permission.PIPELINE_WRITE,
            Permission.ACTIVITY_WRITE,
            Permission.TASK_WRITE,
            Permission.INTELLIGENCE_WRITE,
            Permission.ANALYTICS_READ,
        }
    ),
    UserRole.VIEWER: frozenset({Permission.LEAD_READ, Permission.ANALYTICS_READ}),
}

bearer = HTTPBearer(auto_error=False)


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    unauthorized = HTTPException(
        status.HTTP_401_UNAUTHORIZED,
        "Authentication required",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise unauthorized
    try:
        payload = decode_access_token(credentials.credentials, get_request_settings(request))
        user_id = int(payload["sub"])
    except (InvalidToken, ValueError, KeyError) as exc:
        raise unauthorized from exc
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise unauthorized
    return user


def require_permissions(*required: Permission):
    def dependency(user: User = Depends(get_current_user)) -> User:
        if not set(required).issubset(ROLE_PERMISSIONS[user.role]):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient permissions")
        return user

    return dependency


def authorize_lead_access(user: User, lead: Lead, *, write: bool = False) -> None:
    if write and Permission.LEAD_EDIT not in ROLE_PERMISSIONS[user.role]:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient permissions")
    if user.role == UserRole.SALES_REP and lead.owner_user_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Lead is not assigned to this user")
