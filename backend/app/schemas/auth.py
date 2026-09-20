from pydantic import BaseModel, Field, field_validator

from app.schemas.user import UserResponse, normalize_email


class LoginRequest(BaseModel):
    email: str
    password: str = Field(min_length=1, max_length=200)

    _normalize_email = field_validator("email")(normalize_email)


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse
