from fastapi import APIRouter, HTTPException, status, Depends
from datetime import datetime, timezone

from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
    RefreshRequest,
    LogoutRequest,
    TotpSetupRequest,
    TotpVerifyRequest,
)
from app.services import user_store
from app.services import token_store
from app.utils import security, totp

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest):
    user = user_store.get_user_by_email(data.email)
    if not user or not security.verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if user.twofa_enabled:
        # For simplicity, require TOTP before issuing tokens
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="TOTP required")

    access = security.create_access_token(user.id)
    plain, hashed, expiry = security.create_refresh_token(user.id)
    token_store.store_refresh_token(hashed, user.email, expiry)

    return TokenResponse(access_token=access, refresh_token=plain)


@router.post("/refresh", response_model=TokenResponse)
def refresh(data: RefreshRequest):
    # Verify provided refresh token
    hashed = security.hash_refresh_token(data.refresh_token)
    record = token_store.get_refresh_token(hashed)
    if not record:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    if record["expiry"] < datetime.now(timezone.utc):
        token_store.revoke_refresh_token(hashed)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired")

    # OK: issue new access token and rotate refresh token
    user = user_store.get_user_by_email(record["user_email"])
    access = security.create_access_token(user.id)
    new_plain, new_hashed, new_expiry = security.create_refresh_token(user.id)
    token_store.revoke_refresh_token(hashed)
    token_store.store_refresh_token(new_hashed, user.email, new_expiry)

    return TokenResponse(access_token=access, refresh_token=new_plain)


@router.post("/logout")
def logout(data: LogoutRequest):
    hashed = security.hash_refresh_token(data.refresh_token)
    token_store.revoke_refresh_token(hashed)
    return {"detail": "logged out"}


@router.post("/totp/setup")
def totp_setup(data: TotpSetupRequest):
    user = user_store.get_user_by_email(data.email)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    secret = totp.generate_totp_secret()
    # store secret temporarily; require verification to enable
    user.totp_secret = secret
    uri = totp.get_totp_qr_uri(user.email, secret, app_name="FlowDock")
    return {"totp_uri": uri}


@router.post("/totp/verify")
def totp_verify(data: TotpVerifyRequest):
    user = user_store.get_user_by_email(data.email)
    if not user or not user.totp_secret:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User or TOTP setup not found")

    ok = totp.verify_totp(user.totp_secret, data.code)
    if not ok:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid TOTP code")

    user.twofa_enabled = True
    return {"detail": "TOTP enabled"}
