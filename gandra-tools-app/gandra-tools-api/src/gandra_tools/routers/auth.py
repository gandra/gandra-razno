"""Auth endpoints — login, change password."""

from fastapi import APIRouter, Depends, HTTPException

from gandra_tools.core.auth import (
    ChangePasswordRequest,
    LoginRequest,
    TokenPayload,
    TokenResponse,
    create_access_token,
    hash_password,
    require_auth,
    verify_password,
)
from gandra_tools.core.config import Settings, get_settings

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

# In-memory password store for Phase 1 (will move to DB)
_password_store: dict[str, str] = {}


def _get_hashed_password(email: str, settings: Settings) -> str:
    if email in _password_store:
        return _password_store[email]
    # Default user — hash on first access
    if email == settings.default_user_email:
        hashed = hash_password(settings.default_user_password)
        _password_store[email] = hashed
        return hashed
    raise HTTPException(status_code=401, detail="User not found")


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, settings: Settings = Depends(get_settings)):
    try:
        hashed = _get_hashed_password(body.email, settings)
    except HTTPException:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not verify_password(body.password, hashed):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(body.email, settings)
    return TokenResponse(access_token=token)


@router.post("/change-password")
async def change_password(
    body: ChangePasswordRequest,
    auth: TokenPayload = Depends(require_auth),
    settings: Settings = Depends(get_settings),
):
    hashed = _get_hashed_password(auth.sub, settings)
    if not verify_password(body.current_password, hashed):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    _password_store[auth.sub] = hash_password(body.new_password)
    return {"message": "Password changed successfully"}
