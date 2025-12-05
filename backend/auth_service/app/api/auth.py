import os
from fastapi import APIRouter, HTTPException, status, Depends, Response, Cookie, Request
from datetime import datetime, timezone
import secrets

from starlette.responses import RedirectResponse

from app.core.config import settings

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
from app.schemas.recovery import RequestPasswordReset, ResetPasswordRequest
from app.services import user_store
from app.services import token_store
from app.services import auth_service as svc_auth
from app.utils import security, totp
from app.utils import email as email_utils
from app.services import auth_service
from authlib.integrations.starlette_client import OAuth

router = APIRouter()

# OAuth client (initialized once at module load, reused for all requests)
_oauth_client = None

def get_oauth_client():
    """Lazy-load and cache the OAuth client."""
    global _oauth_client
    if _oauth_client is None:
        try:

            _oauth_client = OAuth()
            _oauth_client.register(
                name="google",
                client_id=settings.google_client_id,
                client_secret=settings.google_client_secret,
                server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
                authorize_url="https://accounts.google.com/o/oauth2/v2/auth",
                access_token_url="https://oauth2.googleapis.com/token",
                userinfo_url="https://www.googleapis.com/oauth2/v1/userinfo",
                client_kwargs={"scope": "email profile"},
            )
        except Exception as e:
            raise RuntimeError(f"Failed to initialize OAuth client: {e}")
    return _oauth_client

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(data: RegisterRequest):
    # Check rate limit for OTP requests
    if not svc_auth.check_otp_request_rate_limit(data.email):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many registration attempts. Try again later."
        )
    
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


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, response: Response):
    """Authenticate user and, if required, verify TOTP in a single call.

    If the user has 2FA enabled, a `totp_code` must be supplied in the
    request. On success, the access token is returned in the JSON body and
    the refresh token is set as an HttpOnly cookie (not returned in JSON).
    """
    # Check rate limit
    if not svc_auth.check_login_rate_limit(data.email):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Try again later."
        )
    
    user = user_store.get_user_by_email(data.email)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    # Ensure email is verified before allowing login
    if not getattr(user, "verified", False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Email not verified")

    if not security.verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if user.twofa_enabled:
        # Require provided TOTP code for users with 2FA enabled
        if not data.totp_code:
            # Return a response indicating TOTP is required (instead of throwing error)
            return TokenResponse(
                access_token="",
                user_id=str(user.id),
                totp_required=True
            )
        ok = totp.verify_totp(user.totp_secret, data.totp_code)
        if not ok:
            # Could increment a failure counter / rate limit here
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid TOTP code")

    # Revoke all previous refresh tokens for this user (enforce single-session)
    token_store.revoke_all_refresh_tokens_for_user(user.email)

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

    return TokenResponse(
        access_token=access,
        user_id=str(user.id),
        totp_required=False
    )


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

    return TokenResponse(
        access_token=access,
        user_id=str(user.id),
        totp_required=False
    )


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






# --- OAuth2 / External provider support (example: Google) -----------------


@router.get("/oauth/{provider}/login")
async def oauth_login(provider: str, request: Request):
    """Begin OAuth login for a provider. Currently only 'google' is supported.

    This returns a redirect to the provider's authorization page.
    """
    if provider != "google":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported provider")

    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="OAuth provider not configured")

    try:
        oauth = get_oauth_client()
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="OAuth dependency unavailable")

    redirect_uri = request.url_for("oauth_callback", provider=provider)
    return await oauth.google.authorize_redirect(request, str(redirect_uri))


@router.get("/oauth/{provider}/callback", name="oauth_callback")
async def oauth_callback(provider: str, request: Request, response: Response):
    """Handle OAuth provider callback. Exchanges code, obtains user info,
    maps/creates a local user, and issues the same JWT + refresh cookie used
    by the password login flow.
    """
    if provider != "google":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported provider")

    try:
        oauth = get_oauth_client()
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="OAuth dependency unavailable")

    try:
        token = await oauth.google.authorize_access_token(request)
    except Exception as e:
        print(f"DEBUG: authorize_access_token failed: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to exchange code: {str(e)}")
    
    # Fetch user info using the access token directly via httpx
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://www.googleapis.com/oauth2/v1/userinfo",
                headers={"Authorization": f"Bearer {token['access_token']}"}
            )
            resp.raise_for_status()
            user_info = resp.json()
    except Exception as e:
        print(f"DEBUG: userinfo fetch failed: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to get user info: {str(e)}")

    email = user_info.get("email")
    if not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email not provided by provider")

    user = user_store.get_user_by_email(email)
    created = False
    if not user:
        # create local user with a random password and mark verified (provider confirmed email)
        pwd = secrets.token_urlsafe(16)
        user = user_store.create_user(email, user_info.get("name", ""), pwd)
        user_store.mark_user_verified(email)
        created = True

    # Revoke all previous refresh tokens for this user (enforce single-session)
    token_store.revoke_all_refresh_tokens_for_user(email)

    # Issue local tokens (same as password login)
    access = security.create_access_token(user.id)
    plain, hashed, expiry = security.create_refresh_token(user.id)
    token_store.store_refresh_token(hashed, user.email, expiry)

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

    return TokenResponse(
        access_token=access,
        user_id=str(user.id),
        totp_required=False
    )


@router.post("/forgot-password")
async def forgot_password(data: RequestPasswordReset):
    # request_password_reset is async; await it so exceptions are handled here
    ok = await auth_service.request_password_reset(data.email)
    if not ok:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to request password reset")
    return {"detail": "password reset email sent"}


@router.get("/verify-reset-token")
def verify_reset_token(token: str, email: str):
    """Verify that a reset token is valid. Returns frontend URL to redirect to."""
    ok = auth_service.check_recovery_token(email, token)
    if not ok:
        # Token invalid or expired - redirect to password recovery page
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
        return RedirectResponse(url=f"{frontend_url}/#/pass-recovery?error=invalid_or_expired_token", status_code=302)
    
    # Token is valid - redirect to reset password page with token and email
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
    return RedirectResponse(url=f"{frontend_url}/#/reset-password?token={token}&email={email}", status_code=302)


@router.post("/reset-password")
def reset_password(data: ResetPasswordRequest):
    """Confirm a password reset: verify token and update password."""
    ok = auth_service.confirm_password_reset(data.email, data.token, data.new_password)
    if not ok:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token or email")
    return {"detail": "password updated"}