from fastapi import APIRouter, HTTPException, status, Depends, Response, Cookie
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
def login(data: LoginRequest, response: Response):
    """Authenticate user and, if required, verify TOTP in a single call.

    If the user has 2FA enabled, a `totp_code` must be supplied in the
    request. On success, the access token is returned in the JSON body and
    the refresh token is set as an HttpOnly cookie (not returned in JSON).
    """
    user = user_store.get_user_by_email(data.email)
    if not user or not security.verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if user.twofa_enabled:
        # Require provided TOTP code for users with 2FA enabled
        if not data.totp_code:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="TOTP required")
        ok = totp.verify_totp(user.totp_secret, data.totp_code)
        if not ok:
            # Could increment a failure counter / rate limit here
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid TOTP code")

    access = security.create_access_token(user.id)
    plain, hashed, expiry = security.create_refresh_token(user.id)
    token_store.store_refresh_token(hashed, user.email, expiry)

    # Set refresh token as an HttpOnly cookie. In production, set secure=True
    # and adjust SameSite according to your client requirements.
    now = datetime.now(timezone.utc)
    max_age = int((expiry - now).total_seconds())
    response.set_cookie(
        key="refresh_token",
        value=plain,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=max_age,
    )

    return TokenResponse(access_token=access)


@router.post("/refresh", response_model=TokenResponse)
def refresh(response: Response, refresh_token: str = Cookie(None), data: RefreshRequest = None):
    """Rotate refresh token and issue a new access token.

    The refresh token may be supplied either in the request body (for
    backward-compatibility) or as an HttpOnly cookie. The endpoint will
    rotate the refresh token and set the new one as a cookie.
    """
    token = None
    if data and getattr(data, "refresh_token", None):
        token = data.refresh_token
    elif refresh_token:
        token = refresh_token

    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token required")

    hashed = security.hash_refresh_token(token)
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

    # Set new refresh token cookie
    now = datetime.now(timezone.utc)
    max_age = int((new_expiry - now).total_seconds())
    response.set_cookie(
        key="refresh_token",
        value=new_plain,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=max_age,
    )

    return TokenResponse(access_token=access)


@router.post("/logout")
def logout(response: Response, refresh_token: str = Cookie(None), data: LogoutRequest = None):
    """Revoke a refresh token. Accepts token in cookie or body."""
    token = None
    if data and getattr(data, "refresh_token", None):
        token = data.refresh_token
    elif refresh_token:
        token = refresh_token

    if token:
        hashed = security.hash_refresh_token(token)
        token_store.revoke_refresh_token(hashed)

    # clear cookie
    response.delete_cookie("refresh_token")
    return {"detail": "logged out"}


@router.post("/totp/setup")
def totp_setup(data: TotpSetupRequest):
    user = user_store.get_user_by_email(data.email)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    secret = totp.generate_totp_secret()
    # Persist the secret; verification required to enable 2FA
    try:
        user_store.set_totp_secret(user.email, secret)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

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
    # Enable two-factor auth and create one-time recovery codes to show to the user
    try:
        codes = user_store.enable_twofa_and_generate_recovery_codes(user.email)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return {"detail": "TOTP enabled", "recovery_codes": codes}



@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(data: RegisterRequest):
    # create user and send email OTP for verification
    try:
        user = user_store.create_user(data.email, data.full_name, data.password)
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
