"""
Presentation Layer: API Routes

These routes use dependency injection to access the clean application services.
They handle HTTP concerns (request/response, status codes, cookies) and delegate
business logic to the application layer.
"""

import os
from fastapi import APIRouter, HTTPException, status, Depends, Response, Cookie, Request
from datetime import datetime, timezone

from starlette.responses import RedirectResponse
import httpx
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
from app.application.services import AuthService
from app.application.twofa_service import TwoFAService
from app.presentation.dependencies import (
    get_auth_service,
    get_db,
    get_twofa_service,
    get_token_generator,
    get_refresh_token_store,
    get_email_service,
)
from app.infrastructure.security.security import JWTTokenGenerator
from app.infrastructure.security.token_store import RefreshTokenStore
from app.infrastructure.email.email import IEmailService
from authlib.integrations.starlette_client import OAuth
from sqlalchemy.orm import Session

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


# ============ Registration & Email Verification ============


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(
    data: RegisterRequest,
    service: AuthService = Depends(get_auth_service),
    email_service: IEmailService = Depends(get_email_service),
):
    """Register a new user and send email OTP."""
    try:
        # Register user
        user = service.register_user(data)

        # Generate and send OTP
        otp = service.generate_email_otp(user.email)
        subject = "Your FlowDock registration code"
        body = f"Your verification code is: {otp}\nIt expires in 15 minutes."
        email_service.send(user.email, subject, body)

        return {"detail": "verification code sent"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/verify-email")
def verify_email(
    data: VerifyEmailOTPRequest,
    service: AuthService = Depends(get_auth_service),
):
    """Verify email using OTP."""
    try:
        service.verify_email_otp(data.email, data.token)
        return {"detail": "email verified"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ============ Authentication (Login/Logout) ============


@router.post("/login", response_model=TokenResponse)
def login(
    data: LoginRequest,
    response: Response,
    service: AuthService = Depends(get_auth_service),
    twofa_service: TwoFAService = Depends(get_twofa_service),
    token_store: RefreshTokenStore = Depends(get_refresh_token_store),
    token_gen: JWTTokenGenerator = Depends(get_token_generator),
):
    """Authenticate user and issue tokens."""
    try:
        # Authenticate user
        user = service.authenticate_user(data.email, data.password)

        # Check if email is verified
        if not user.verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Email not verified",
            )

        # Handle TOTP if enabled
        if user.twofa_enabled:
            if not data.totp_code:
                return TokenResponse(
                    access_token="",
                    user_id=str(user.id),
                    totp_required=True,
                )
            # Verify TOTP
            if not twofa_service.verify_totp_code(data.email, data.totp_code):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid TOTP code",
                )

        # Revoke all previous tokens for this user (single-session enforcement)
        token_store.revoke_all_by_user(user.email)

        # Create tokens
        access_token = token_gen.create_access_token(user.id)
        refresh_token, refresh_hash, expiry = token_gen.create_refresh_token(user.id)

        # Store refresh token in Redis
        token_store.store(refresh_hash, user.email, expiry)

        # Set refresh token as HttpOnly cookie
        now = datetime.now(timezone.utc)
        max_age = int((expiry - now).total_seconds())
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=max_age,
        )

        return TokenResponse(
            access_token=access_token,
            user_id=str(user.id),
            totp_required=False,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/logout")
def logout(
    response: Response,
    refresh_token: str = Cookie(None),
    data: LogoutRequest = None,
    token_store: RefreshTokenStore = Depends(get_refresh_token_store),
    token_gen: JWTTokenGenerator = Depends(get_token_generator),
):
    """Logout and revoke refresh token."""
    token = None
    if data and getattr(data, "refresh_token", None):
        token = data.refresh_token
    elif refresh_token:
        token = refresh_token

    if token:
        hashed = token_gen._hash_token(token)
        token_store.revoke(hashed)

    response.delete_cookie("refresh_token")
    return {"detail": "logged out"}


# ============ Token Refresh ============


@router.post("/refresh", response_model=TokenResponse)
def refresh(
    response: Response,
    refresh_token: str = Cookie(None),
    data: RefreshRequest = None,
    token_store: RefreshTokenStore = Depends(get_refresh_token_store),
    token_gen: JWTTokenGenerator = Depends(get_token_generator),
    db: Session = Depends(get_db),
):
    """Refresh access token and rotate refresh token."""
    from app.infrastructure.database.repositories import PostgresUserRepository
    
    user_repo = PostgresUserRepository(db)
    
    token = None
    if data and getattr(data, "refresh_token", None):
        token = data.refresh_token
    elif refresh_token:
        token = refresh_token

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token required",
        )

    # Verify token hasn't been blacklisted
    hashed = token_gen._hash_token(token)
    if token_store.is_blacklisted(hashed):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token revoked",
        )

    # Get token from store
    record = token_store.get(hashed)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    # Check expiry
    if record["expiry"] < datetime.now(timezone.utc):
        token_store.revoke(hashed)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired",
        )

    # Issue new tokens
    user = user_repo.get_by_email(record["user_email"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    access_token = token_gen.create_access_token(user.id)
    new_refresh, new_hash, new_expiry = token_gen.create_refresh_token(user.id)

    # Revoke old token and store new one
    token_store.revoke(hashed)
    token_store.store(new_hash, user.email, new_expiry)

    # Set new refresh token cookie
    now = datetime.now(timezone.utc)
    max_age = int((new_expiry - now).total_seconds())
    response.set_cookie(
        key="refresh_token",
        value=new_refresh,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=max_age,
    )

    return TokenResponse(
        access_token=access_token,
        user_id=str(user.id),
        totp_required=False,
    )


# ============ TOTP / 2FA Setup ============


@router.post("/totp/setup")
def totp_setup(
    data: TotpSetupRequest,
    twofa_service: TwoFAService = Depends(get_twofa_service),
):
    """Initiate TOTP setup for a user."""
    try:
        secret, uri = twofa_service.initiate_totp_setup(data.email)
        return {"totp_secret": secret, "totp_uri": uri}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/totp/verify")
def totp_verify(
    data: TotpVerifyRequest,
    twofa_service: TwoFAService = Depends(get_twofa_service),
):
    """Verify TOTP code and enable 2FA."""
    try:
        # This endpoint requires the TOTP secret to be provided by the client
        # In a real scenario, the client would have generated the secret from /totp/setup
        # and we'd retrieve it from user session or request. For now, raising error.
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="TOTP verification requires frontend integration",
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ============ OAuth2 / External Providers ============


@router.get("/oauth/{provider}/login")
async def oauth_login(provider: str, request: Request):
    """Begin OAuth login for a provider. Currently only 'google' is supported."""
    if provider != "google":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported provider",
        )

    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OAuth provider not configured",
        )

    try:
        oauth = get_oauth_client()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OAuth dependency unavailable",
        )

    redirect_uri = request.url_for("oauth_callback", provider=provider)
    return await oauth.google.authorize_redirect(request, str(redirect_uri))


@router.get("/oauth/{provider}/callback", name="oauth_callback")
async def oauth_callback(
    provider: str,
    request: Request,
    response: Response,
    service: AuthService = Depends(get_auth_service),
):
    """Handle OAuth provider callback."""
    # TODO: Implement OAuth callback
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="OAuth callback needs implementation",
    )


# ============ Password Recovery ============


@router.post("/forgot-password")
async def forgot_password(
    data: RequestPasswordReset,
    service: AuthService = Depends(get_auth_service),
    email_service: IEmailService = Depends(get_email_service),
):
    """Request password reset."""
    try:
        token_entity = service.request_password_reset(data.email)

        # Build reset link
        backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")
        reset_link = (
            f"{backend_url}/auth/verify-reset-token?token={token_entity.token}&email={data.email}"
        )

        subject = "Reset your FlowDock password"
        body = f"Click the link to reset your password:\n\n{reset_link}\n\nThis link expires in 15 minutes."

        email_service.send(data.email, subject, body)
        return {"detail": "password reset email sent"}
    except ValueError:
        # Prevent email enumeration - return success anyway
        return {"detail": "password reset email sent"}


@router.get("/verify-reset-token")
def verify_reset_token(
    token: str,
    email: str,
    service: AuthService = Depends(get_auth_service),
):
    """Verify reset token and redirect to reset page."""
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")

    if not service.verify_password_reset_token(email, token):
        return RedirectResponse(
            url=f"{frontend_url}/#/pass-recovery?error=invalid_or_expired_token",
            status_code=302,
        )

    return RedirectResponse(
        url=f"{frontend_url}/#/reset-password?token={token}&email={email}",
        status_code=302,
    )


@router.post("/reset-password")
def reset_password(
    data: ResetPasswordRequest,
    service: AuthService = Depends(get_auth_service),
):
    """Confirm password reset."""
    try:
        service.confirm_password_reset(data.email, data.token, data.new_password)
        return {"detail": "password updated"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
