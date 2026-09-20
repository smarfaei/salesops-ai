from typing import Any

from sqlalchemy.orm import Session

from app.core.enums import AuditEventType
from app.models.audit import AuditLog

SENSITIVE_KEY_MARKERS = {
    "password",
    "hashed_password",
    "access_token",
    "refresh_token",
    "authorization",
    "api_key",
    "openai_api_key",
    "jwt_secret",
}


def _safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _safe(item)
            for key, item in value.items()
            if not any(marker in key.lower() for marker in SENSITIVE_KEY_MARKERS)
        }
    if isinstance(value, (list, tuple)):
        return [_safe(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def record_audit(
    db: Session,
    *,
    actor_user_id: int | None,
    event_type: AuditEventType,
    entity_type: str,
    entity_id: int | str | None,
    metadata: dict[str, Any] | None = None,
) -> AuditLog:
    event = AuditLog(
        actor_user_id=actor_user_id,
        event_type=event_type,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id is not None else None,
        audit_metadata=_safe(metadata) if metadata else None,
    )
    db.add(event)
    return event
