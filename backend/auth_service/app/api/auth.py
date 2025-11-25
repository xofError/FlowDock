from fastapi import APIRouter, HTTPException, status, Depends
from datetime import datetime, timezone

from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
    RefreshRequest,
    LogoutRequest,
    TotpSetupRequest,
    TotpVerifyRequest,
    RegisterRequest,
    VerifyEmailOTPRequest,
)
from app.services import user_store
from app.services import token_store
from app.services import auth_service as svc_auth
from app.utils import security, totp
from app.utils import email as email_utils

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



@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(data: RegisterRequest):
    # create user and send email OTP for verification
    try:
        user = user_store.create_user(data.email, data.password)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists")

    otp = svc_auth.create_email_otp(user.email)
    # send OTP email (falls back to console if SMTP not configured)
    subject = "Your FlowDock registration code"
    body = f"Your verification code is: {otp}\nIt expires in 15 minutes."
    email_utils.send_email(user.email, subject, body)

    return {"detail": "verification code sent"}


@router.post("/verify-email")
def verify_email(data: VerifyEmailOTPRequest):
    ok = svc_auth.verify_email_otp(data.email, data.token)
    if not ok:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token")
    return {"detail": "email verified"}
