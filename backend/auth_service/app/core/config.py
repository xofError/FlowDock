from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App configuration
    app_name: str = "Auth Service"
    
    # JWT configuration - shared with Media Service
    secret_key: str = "secret"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    
    # Internal Service Authentication - for inter-service communication
    # Used to authenticate requests from other internal services (e.g., Media Service)
    internal_api_key: str = "internal-api-key-change-in-production"
    
    # Database configuration - PostgreSQL
    postgres_user: str = "postgres"
    postgres_password: str = "postgres"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "FlowDock"
    
    @property
    def database_url(self) -> str:
        """Construct database URL from components"""
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )
    
    # OAuth2 / External provider settings (example: Google)
    # Do NOT hard-code secrets here. Configure via environment variables or a .env file.
    google_client_id: str = ""
    google_client_secret: str = ""
    
    # Backend URL for OAuth redirect (used in production/docker)
    backend_url: str = "http://localhost:8000"
    
    # Frontend redirect URL after OAuth
    frontend_url: str = "http://localhost:5173"
    
    # Cookie security settings
    # Set to False for local development (HTTP), True for production (HTTPS)
    cookie_secure: bool = False  # Default to False for development

    class Config:
        env_file = ".env"


settings = Settings()
