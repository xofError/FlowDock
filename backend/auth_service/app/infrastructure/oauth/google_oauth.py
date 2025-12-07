
import logging
from typing import Optional
from authlib.integrations.starlette_client import OAuth
from app.core.config import settings

logger = logging.getLogger(__name__)

# Lazy-loaded OAuth client (singleton pattern)
_oauth_client: Optional[OAuth] = None


def get_oauth_client() -> OAuth:
    """
    Get or initialize the OAuth client singleton.
    
    Returns:
        Initialized OAuth client with registered providers
        
    Raises:
        RuntimeError: If OAuth initialization fails
    """
    global _oauth_client
    
    if _oauth_client is None:
        try:
            _oauth_client = OAuth()
            
            # Register Google provider
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
            
            logger.info("OAuth client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OAuth client: {e}")
            raise RuntimeError(f"Failed to initialize OAuth client: {e}")
    
    return _oauth_client


def validate_oauth_provider(provider: str) -> None:
    """
    Validate that the requested provider is supported.
    
    Args:
        provider: Provider name to validate
        
    Raises:
        ValueError: If provider is not supported
    """
    supported_providers = ["google"]
    if provider not in supported_providers:
        raise ValueError(f"Unsupported OAuth provider: {provider}. Supported: {supported_providers}")


def validate_oauth_config(provider: str) -> None:
    """
    Validate that OAuth provider is properly configured.
    
    Args:
        provider: Provider name to validate
        
    Raises:
        ValueError: If provider configuration is missing
    """
    if provider == "google":
        if not settings.google_client_id or not settings.google_client_secret:
            raise ValueError("Google OAuth not properly configured (missing credentials)")
