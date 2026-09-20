from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.authz import get_current_user
from app.core.demo import get_request_settings
from app.core.enums import AuditEventType
from app.core.security import (
    DUMMY_PASSWORD_HASH,
    create_access_token,
    create_refresh_token,
    hash_refresh_token,
    verify_password,
)
from app.db.session import get_db
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.auth import AuthResponse, LoginRequest
from app.schemas.user import UserResponse
from app.services.audit import record_audit

router = APIRouter(prefix="/auth", tags=["authentication"])


def _verify_origin(request: Request) -> None:
    origin = request.headers.get("origin")
    if origin and origin not in get_request_settings(request).allowed_cors_origins:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Origin is not allowed")


def _set_refresh_cookie(response: Response, request: Request, token: str) -> None:
    settings = get_request_settings(request)
    response.set_cookie(
        settings.refresh_cookie_name,
        token,
        max_age=settings.refresh_token_days * 86400,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite=settings.auth_cookie_samesite,
        path="/auth",
    )


def _auth_response(user: User, request: Request) -> AuthResponse:
    settings = get_request_settings(request)
    return AuthResponse(
        access_token=create_access_token(user.id, settings),
        expires_in=settings.access_token_minutes * 60,
        user=UserResponse.model_validate(user),
    )


@router.post("/login", response_model=AuthResponse)
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> AuthResponse:
    _verify_origin(request)
    user = db.scalar(select(User).where(User.email == payload.email))
    password_valid = verify_password(
        payload.password, user.hashed_password if user is not None else DUMMY_PASSWORD_HASH
    )
    if user is None or not user.is_active or not password_valid:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
    settings = get_request_settings(request)
    raw_refresh = create_refresh_token()
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=hash_refresh_token(raw_refresh),
            expires_at=datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_days),
        )
    )
    user.last_login_at = datetime.now(timezone.utc)
    record_audit(
        db,
        actor_user_id=user.id,
        event_type=AuditEventType.LOGIN_SUCCEEDED,
        entity_type="user",
        entity_id=user.id,
    )
    db.commit()
    db.refresh(user)
    _set_refresh_cookie(response, request, raw_refresh)
    return _auth_response(user, request)


@router.post("/refresh", response_model=AuthResponse)
def refresh(request: Request, response: Response, db: Session = Depends(get_db)) -> AuthResponse:
    _verify_origin(request)
    settings = get_request_settings(request)
    raw_token = request.cookies.get(settings.refresh_cookie_name)
    if not raw_token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid refresh session")
    token = db.scalar(
        select(RefreshToken).where(RefreshToken.token_hash == hash_refresh_token(raw_token))
    )
    now = datetime.now(timezone.utc)
    expires_at = token.expires_at if token is not None else None
    if expires_at is not None and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if token is None or token.revoked_at is not None or expires_at is None or expires_at <= now:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid refresh session")
    user = db.get(User, token.user_id)
    if user is None or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid refresh session")
    replacement_raw = create_refresh_token()
    replacement = RefreshToken(
        user_id=user.id,
        token_hash=hash_refresh_token(replacement_raw),
        expires_at=now + timedelta(days=settings.refresh_token_days),
    )
    db.add(replacement)
    db.flush()
    token.revoked_at = now
    token.replaced_by_id = replacement.id
    db.commit()
    _set_refresh_cookie(response, request, replacement_raw)
    return _auth_response(user, request)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: Request, response: Response, db: Session = Depends(get_db)) -> Response:
    _verify_origin(request)
    settings = get_request_settings(request)
    raw_token = request.cookies.get(settings.refresh_cookie_name)
    if raw_token:
        token = db.scalar(
            select(RefreshToken).where(RefreshToken.token_hash == hash_refresh_token(raw_token))
        )
        if token and token.revoked_at is None:
            token.revoked_at = datetime.now(timezone.utc)
            db.commit()
    response.delete_cookie(settings.refresh_cookie_name, path="/auth")
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(user)
