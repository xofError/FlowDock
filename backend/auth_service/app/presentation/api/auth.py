"""
Presentation Layer: API Routes

These routes use dependency injection to access the clean application services.
They handle HTTP concerns (request/response, status codes, cookies) and delegate
business logic to the application layer.
"""

import os
import logging
from fastapi import APIRouter, HTTPException, status, Depends, Response, Cookie, Request
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from starlette.responses import RedirectResponse
from app.core.config import settings

from app.application.dtos import (
    LoginRequestDTO,
    TokenResponseDTO,
    RefreshRequestDTO,
    LogoutRequestDTO,
    TotpSetupRequestDTO,
    TotpVerifyRequestDTO,
    RegisterRequestDTO,
    VerifyEmailOTPRequestDTO,
    ForgotPasswordRequestDTO,
    ResetPasswordRequestDTO,
    GeneratePasscodeRequestDTO,
    VerifyPasscodeRequestDTO,
)
from app.application.services import AuthService
from app.application.twofa_service import TwoFAService
from app.application.oauth_service import OAuthService
from app.presentation.dependencies import (
    get_auth_service,
    get_db,
    get_twofa_service,
    get_token_generator,
    get_refresh_token_store,
    get_email_service,
    get_oauth_service,
)
from app.infrastructure.security.security import JWTTokenGenerator
from app.infrastructure.security.token_store import RefreshTokenStore
from app.infrastructure.email.email import IEmailService
from app.infrastructure.oauth import get_oauth_client, validate_oauth_provider, validate_oauth_config

logger = logging.getLogger(__name__)
router = APIRouter()


# ============ Registration & Email Verification ============


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(
    data: RegisterRequestDTO,
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
    data: VerifyEmailOTPRequestDTO,
    service: AuthService = Depends(get_auth_service),
):
    """Verify email using OTP."""
    try:
        service.verify_email_otp(data.email, data.token)
        return {"detail": "email verified"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ============ Authentication (Login/Logout) ============


@router.post("/login", response_model=TokenResponseDTO)
def login(
    data: LoginRequestDTO,
    request: Request,
    response: Response,
    service: AuthService = Depends(get_auth_service),
    twofa_service: TwoFAService = Depends(get_twofa_service),
    token_store: RefreshTokenStore = Depends(get_refresh_token_store),
    token_gen: JWTTokenGenerator = Depends(get_token_generator),
    db: Session = Depends(get_db),
):
    """Authenticate user and issue tokens."""
    try:
        # Extract client IP
        client_ip = request.client.host if request.client else None
        
        # Authenticate user and set login metadata
        user = service.authenticate_user(data.email, data.password, client_ip)

        # Check if email is verified
        if not user.verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Email not verified",
            )

        # Handle TOTP if enabled
        if user.twofa_enabled:
            if not data.totp_code:
                # Return response indicating TOTP is required (don't generate tokens yet)
                return TokenResponseDTO(
                    access_token="",
                    user_id=str(user.id),
                    totp_required=True,
                )
            # Verify TOTP code
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

        # Update user with login information in database
        from app.infrastructure.database.repositories import PostgresUserRepository
        user_repo = PostgresUserRepository(db)
        user_repo.update(user)

        # Set refresh token as HttpOnly cookie
        # [SECURITY FIX: Insecure Cookies]
        # Use environment variable to determine cookie security settings
        from app.core.config import settings
        
        now = datetime.now(timezone.utc)
        max_age = int((expiry - now).total_seconds())
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=True,  # [FIX] Set to True for HTTPS - prevents plain text transmission
            samesite="Strict",  # [FIX] Strict instead of lax for CSRF protection
            max_age=max_age,
        )

        return TokenResponseDTO(
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
    data: LogoutRequestDTO = None,
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


@router.post("/refresh", response_model=TokenResponseDTO)
def refresh(
    response: Response,
    refresh_token: str = Cookie(None),
    data: RefreshRequestDTO = None,
    token_store: RefreshTokenStore = Depends(get_refresh_token_store),
    token_gen: JWTTokenGenerator = Depends(get_token_generator),
    db=Depends(get_db),
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
    # [SECURITY FIX: Insecure Cookies]
    now = datetime.now(timezone.utc)
    max_age = int((new_expiry - now).total_seconds())
    response.set_cookie(
        key="refresh_token",
        value=new_refresh,
        httponly=True,
        secure=True,  # [FIX] Set to True for HTTPS
        samesite="Strict",  # [FIX] Strict for CSRF protection
        max_age=max_age,
    )

    return TokenResponseDTO(
        access_token=access_token,
        user_id=str(user.id),
        totp_required=False,
    )


# ============ TOTP / 2FA Setup ============


@router.post("/totp/setup")
def totp_setup(
    data: TotpSetupRequestDTO,
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
    data: TotpVerifyRequestDTO,
    twofa_service: TwoFAService = Depends(get_twofa_service),
):
    """Verify TOTP code.
    
    Supports two flows:
    1. Setup verification: When enabling 2FA, verifies code against provided secret and generates recovery codes
    2. Login verification: When logging in with 2FA enabled, verifies code against stored secret
    """
    try:
        # Setup verification: totp_secret is provided
        if data.totp_secret:
            recovery_codes = twofa_service.verify_totp_and_enable_2fa(
                email=data.email,
                totp_secret=data.totp_secret,
                totp_code=data.code,
            )

            logger.info(f"2FA enabled for user: {data.email}")

            return {
                "detail": "2FA enabled successfully",
                "recovery_codes": recovery_codes,
            }
        
        # Login verification: retrieve secret from database
        else:
            is_valid = twofa_service.verify_totp_code(data.email, data.code)
            if not is_valid:
                raise ValueError("Invalid TOTP code")
            
            logger.info(f"TOTP code verified for user: {data.email}")
            
            return {
                "detail": "TOTP verified successfully",
            }
    
    except ValueError as e:
        logger.warning(f"TOTP verification failed for {data.email}: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ============ OAuth2 / External Providers ============


@router.get("/oauth/{provider}/login")
async def oauth_login(provider: str, request: Request):
    """Begin OAuth login for a provider. Currently only 'google' is supported."""
    try:
        validate_oauth_provider(provider)
        validate_oauth_config(provider)
    except ValueError as e:
        logger.warning(f"OAuth validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    try:
        oauth = get_oauth_client()
    except RuntimeError as e:
        logger.error(f"OAuth client initialization failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OAuth provider unavailable",
        )

    # Build redirect URI using configured backend URL
    redirect_uri = f"{settings.backend_url}/auth/oauth/{provider}/callback"
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/oauth/{provider}/callback", name="oauth_callback")
async def oauth_callback(
    provider: str,
    request: Request,
    response: Response,
    oauth_service: OAuthService = Depends(get_oauth_service),
    token_gen: JWTTokenGenerator = Depends(get_token_generator),
    token_store: RefreshTokenStore = Depends(get_refresh_token_store),
    db=Depends(get_db),
):
    """Handle OAuth provider callback and authenticate user."""
    try:
        validate_oauth_provider(provider)
    except ValueError as e:
        logger.warning(f"Invalid OAuth provider in callback: {e}")
        return RedirectResponse(
            url=f"{settings.frontend_url}/#/login?error=invalid_provider",
            status_code=302,
        )

    # Exchange authorization code for access token
    try:
        oauth = get_oauth_client()
        oauth_token = await oauth.google.authorize_access_token(request)
    except Exception as e:
        logger.error(f"OAuth token exchange failed: {e}")
        return RedirectResponse(
            url=f"{settings.frontend_url}/#/login?error=authentication_failed",
            status_code=302,
        )

    # Get user info from OAuth provider
    try:
        userinfo = oauth_token.get("userinfo")
        if not userinfo:
            # Fallback: fetch user info if not in token
            userinfo = await oauth_service.get_google_userinfo(oauth_token["access_token"])
        
        if not userinfo:
            raise ValueError("Unable to retrieve user information from OAuth provider")

        email = userinfo.get("email")
        name = userinfo.get("name", "")
        sub = oauth_token.get("sub", "")

        # Get or create user (domain entity)
        user = oauth_service.get_or_create_user_from_oauth(
            email=email,
            name=name,
            oauth_provider=provider,
            oauth_sub=sub,
        )

        # Persist new user if it doesn't have an ID (it's new)
        if user.id is None:
            user = oauth_service.save_user(user)

        logger.info(f"OAuth authentication successful for user: {user.email}")

    except Exception as e:
        logger.error(f"OAuth user processing failed: {e}")
        error_msg = "User authentication failed"
        return RedirectResponse(
            url=f"{settings.frontend_url}/#/login?error={error_msg}",
            status_code=302,
        )

    # Generate JWT tokens
    try:
        access_token = token_gen.create_access_token(user.id)
        refresh_token_plain, refresh_token_hash, expiry = token_gen.create_refresh_token(user.id)
        
        # Store refresh token hash with user email and expiry
        token_store.store(refresh_token_hash, user.email, expiry)

        # Create redirect response to OAuthCallback component first
        # (not directly to dashboard) so tokens can be properly processed
        redirect_response = RedirectResponse(
            url=f"{settings.frontend_url}/#/auth/callback?access_token={access_token}&user_id={user.id}",
            status_code=302,
        )
        
        # Set refresh token as HttpOnly cookie
        # [SECURITY FIX: Insecure Cookies]
        redirect_response.set_cookie(
            "refresh_token",
            refresh_token_plain,
            httponly=True,
            secure=True,  # [FIX] Set to True for HTTPS - prevents plain text transmission
            samesite="Strict",  # [FIX] Strict for CSRF protection
            max_age=30 * 24 * 60 * 60,  # 30 days
        )
        
        return redirect_response

    except Exception as e:
        logger.error(f"Token generation failed: {e}")
        return RedirectResponse(
            url=f"{settings.frontend_url}/#/login?error=token_generation_failed",
            status_code=302,
        )



# ============ Password Recovery ============


@router.post("/forgot-password")
async def forgot_password(
    data: ForgotPasswordRequestDTO,
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
    data: ResetPasswordRequestDTO,
    service: AuthService = Depends(get_auth_service),
):
    """Confirm password reset."""
    try:
        service.confirm_password_reset(data.email, data.token, data.new_password)
        return {"detail": "password updated"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ============ Passcode Sign-In (Magic Link) ============


@router.post("/generate-passcode")
def generate_passcode(
    data: GeneratePasscodeRequestDTO,
    service: AuthService = Depends(get_auth_service),
    email_service: IEmailService = Depends(get_email_service),
):
    """Generate a 6-digit passcode and send it to user's email.
    
    Rate limited: max 3 requests per 5 minutes per email.
    """
    try:
        # Generate passcode
        passcode = service.generate_passcode(data.email)

        # Send via email
        subject = "Your FlowDock Sign-In Code"
        body = f"Your sign-in code is: {passcode}\n\nIt expires in 15 minutes."
        email_service.send(data.email, subject, body)

        return {"detail": "passcode sent to email"}
    except ValueError as e:
        # Prevent email enumeration - return success anyway
        return {"detail": "passcode sent to email"}


@router.post("/verify-passcode", response_model=TokenResponseDTO)
def verify_passcode(
    data: VerifyPasscodeRequestDTO,
    request: Request,
    response: Response,
    service: AuthService = Depends(get_auth_service),
    token_store: RefreshTokenStore = Depends(get_refresh_token_store),
    token_gen: JWTTokenGenerator = Depends(get_token_generator),
    db: Session = Depends(get_db),
):
    """Verify a 6-digit passcode and authenticate the user.
    
    Returns access token and sets refresh token cookie.
    """
    try:
        # Verify passcode
        user = service.verify_passcode(data.email, data.code)

        # Update login metadata
        ip_address = request.client.host if request.client else None
        user.last_login_ip = ip_address
        user.last_login_at = datetime.now(timezone.utc)

        # Revoke all previous tokens for this user (single-session enforcement)
        token_store.revoke_all_by_user(user.email)

        # Create tokens
        access_token = token_gen.create_access_token(user.id)
        refresh_token, refresh_hash, expiry = token_gen.create_refresh_token(user.id)

        # Store refresh token in Redis
        token_store.store(refresh_hash, user.email, expiry)

        # Update user with login information in database
        from app.infrastructure.database.repositories import PostgresUserRepository
        user_repo = PostgresUserRepository(db)
        user_repo.update(user)

        # Set refresh token cookie
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=True,
            samesite="Strict",
            max_age=int(expiry.timestamp() - datetime.now(timezone.utc).timestamp()),
        )

        return TokenResponseDTO(
            access_token=access_token,
            token_type="bearer",
            user_id=str(user.id),
            totp_required=False,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
