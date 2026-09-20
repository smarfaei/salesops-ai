from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = Field(alias="DATABASE_URL")
    app_env: str = Field(default="development", alias="APP_ENV")
    debug: bool = Field(default=False, alias="DEBUG")
    demo_mode: bool = Field(default=False, alias="DEMO_MODE")
    demo_rate_limit_requests: int = Field(default=60, ge=1, le=1000, alias="DEMO_RATE_LIMIT_REQUESTS")
    demo_rate_limit_window_seconds: int = Field(
        default=60, ge=1, le=3600, alias="DEMO_RATE_LIMIT_WINDOW_SECONDS"
    )
    ai_provider: Literal["local", "openai"] = Field(default="local", alias="AI_PROVIDER")
    ai_allow_fallback: bool = Field(default=True, alias="AI_ALLOW_FALLBACK")
    openai_api_key: SecretStr | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str | None = Field(default=None, alias="OPENAI_MODEL")
    openai_timeout_seconds: float = Field(default=20.0, gt=0, le=120, alias="OPENAI_TIMEOUT_SECONDS")
    cors_origins: str = Field(alias="CORS_ORIGINS")
    jwt_secret: SecretStr = Field(alias="JWT_SECRET", min_length=32)
    access_token_minutes: int = Field(default=15, ge=1, le=120, alias="ACCESS_TOKEN_MINUTES")
    refresh_token_days: int = Field(default=7, ge=1, le=90, alias="REFRESH_TOKEN_DAYS")
    refresh_cookie_name: str = Field(default="salesops_refresh", alias="REFRESH_COOKIE_NAME")
    auth_cookie_secure: bool = Field(default=False, alias="AUTH_COOKIE_SECURE")
    auth_cookie_samesite: Literal["lax", "strict", "none"] = Field(
        default="lax", alias="AUTH_COOKIE_SAMESITE"
    )
    login_rate_limit_requests: int = Field(default=5, ge=1, le=100, alias="LOGIN_RATE_LIMIT_REQUESTS")
    login_rate_limit_window_seconds: int = Field(
        default=60, ge=1, le=3600, alias="LOGIN_RATE_LIMIT_WINDOW_SECONDS"
    )
    demo_account_password: SecretStr | None = Field(default=None, alias="DEMO_ACCOUNT_PASSWORD")

    @model_validator(mode="after")
    def enforce_public_demo_safety(self) -> "Settings":
        if self.demo_mode:
            self.debug = False
            self.ai_provider = "local"
            self.openai_api_key = None
            self.openai_model = None
            if "*" in self.allowed_cors_origins:
                raise ValueError("CORS_ORIGINS cannot use a wildcard in public demo mode")
        if self.app_env.lower() == "production":
            self.debug = False
            self.auth_cookie_secure = True
        if self.auth_cookie_samesite == "none" and not self.auth_cookie_secure:
            raise ValueError("SameSite=None requires AUTH_COOKIE_SECURE=true")
        return self

    @property
    def allowed_cors_origins(self) -> list[str]:
        origins = [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
        if not origins:
            raise ValueError("CORS_ORIGINS must contain at least one explicit origin")
        return origins

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
