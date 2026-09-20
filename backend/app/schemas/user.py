import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.enums import UserRole

EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def normalize_email(value: str) -> str:
    normalized = value.strip().lower()
    if len(normalized) > 320 or not EMAIL_PATTERN.fullmatch(normalized):
        raise ValueError("must be a valid email address")
    return normalized


class UserSummary(BaseModel):
    id: int
    email: str
    full_name: str
    role: UserRole
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class UserResponse(UserSummary):
    created_at: datetime
    updated_at: datetime
    last_login_at: datetime | None


class UserCreate(BaseModel):
    email: str
    full_name: str = Field(min_length=2, max_length=120)
    password: str = Field(min_length=10, max_length=200)
    role: UserRole
    is_active: bool = True

    _normalize_email = field_validator("email")(normalize_email)

    @field_validator("full_name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        return value.strip()


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=120)
    role: UserRole | None = None
    is_active: bool | None = None

    @field_validator("full_name")
    @classmethod
    def clean_optional_name(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else None


class UserListResponse(BaseModel):
    items: list[UserResponse]
    total: int
    page: int
    page_size: int
    pages: int
