"""Authentication: JWT for Web/API, no auth for CLI."""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from gandra_tools.core.config import Settings, get_settings

security = HTTPBearer(auto_error=False)

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


class TokenPayload(BaseModel):
    sub: str
    exp: datetime


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000)
    return f"{salt}${h.hex()}"


def verify_password(plain: str, hashed: str) -> bool:
    try:
        salt, expected = hashed.split("$", 1)
    except ValueError:
        return False
    h = hashlib.pbkdf2_hmac("sha256", plain.encode(), salt.encode(), 100_000)
    return secrets.compare_digest(h.hex(), expected)


def create_access_token(email: str, settings: Settings | None = None) -> str:
    if settings is None:
        settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": email, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_token(token: str, settings: Settings | None = None) -> TokenPayload | None:
    if settings is None:
        settings = get_settings()
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        return TokenPayload(**payload)
    except JWTError:
        return None


async def require_auth(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    settings: Settings = Depends(get_settings),
) -> TokenPayload:
    """Middleware for Web/API — requires valid JWT."""
    if credentials is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    payload = decode_token(credentials.credentials, settings)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return payload


def get_current_user_or_default(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    settings: Settings = Depends(get_settings),
) -> str:
    """For services used from both CLI and API.
    With token → return authenticated user email.
    Without token → return default user from settings.
    """
    if credentials:
        payload = decode_token(credentials.credentials, settings)
        if payload:
            return payload.sub
    return settings.default_user_email
