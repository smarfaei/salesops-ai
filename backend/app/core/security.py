import base64
import binascii
import hashlib
import hmac
import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from app.core.config import Settings


class InvalidToken(Exception):
    pass


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _b64decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def hash_password(password: str) -> str:
    if len(password) < 10:
        raise ValueError("Password must contain at least 10 characters")
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1, dklen=32)
    return f"scrypt$16384$8$1${_b64encode(salt)}${_b64encode(digest)}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, n, r, p, salt, expected = encoded.split("$", 5)
        if algorithm != "scrypt" or (int(n), int(r), int(p)) != (2**14, 8, 1):
            return False
        actual = hashlib.scrypt(
            password.encode(),
            salt=_b64decode(salt),
            n=int(n),
            r=int(r),
            p=int(p),
            dklen=32,
        )
        return hmac.compare_digest(actual, _b64decode(expected))
    except (TypeError, ValueError, binascii.Error):
        return False


# A process-local decoy makes unknown-user and wrong-password checks perform the
# same expensive password operation without embedding a reusable credential.
DUMMY_PASSWORD_HASH = hash_password(secrets.token_urlsafe(32))


def create_access_token(user_id: int, settings: Settings, *, now: datetime | None = None) -> str:
    issued = now or datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "type": "access",
        "iat": int(issued.timestamp()),
        "exp": int((issued + timedelta(minutes=settings.access_token_minutes)).timestamp()),
        "jti": secrets.token_hex(12),
    }
    header = {"alg": "HS256", "typ": "JWT"}
    signing_input = ".".join(
        _b64encode(json.dumps(part, separators=(",", ":"), sort_keys=True).encode())
        for part in (header, payload)
    )
    signature = hmac.new(
        settings.jwt_secret.get_secret_value().encode(), signing_input.encode(), hashlib.sha256
    ).digest()
    return f"{signing_input}.{_b64encode(signature)}"


def decode_access_token(token: str, settings: Settings, *, now: datetime | None = None) -> dict[str, Any]:
    try:
        if len(token) > 4096:
            raise InvalidToken
        encoded_header, encoded_payload, encoded_signature = token.split(".")
        signing_input = f"{encoded_header}.{encoded_payload}"
        expected = hmac.new(
            settings.jwt_secret.get_secret_value().encode(), signing_input.encode(), hashlib.sha256
        ).digest()
        if not hmac.compare_digest(expected, _b64decode(encoded_signature)):
            raise InvalidToken
        header = json.loads(_b64decode(encoded_header))
        payload = json.loads(_b64decode(encoded_payload))
        current = int((now or datetime.now(timezone.utc)).timestamp())
        if header != {"alg": "HS256", "typ": "JWT"}:
            raise InvalidToken
        if payload.get("type") != "access":
            raise InvalidToken
        expires_at = int(payload["exp"])
        issued_at = int(payload["iat"])
        user_id = int(payload["sub"])
        if expires_at <= current or issued_at > current + 60 or user_id < 1:
            raise InvalidToken
        return payload
    except (
        ValueError,
        TypeError,
        KeyError,
        UnicodeDecodeError,
        binascii.Error,
        json.JSONDecodeError,
    ) as exc:
        raise InvalidToken from exc


def create_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
