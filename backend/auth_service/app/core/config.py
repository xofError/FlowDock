from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Auth Service"
    secret_key: str = "your-super-secret-key-change-this"
    access_token_expire_minutes: int = 60
    # OAuth2 / External provider settings (example: Google)
    # Do NOT hard-code secrets here. Configure via environment variables or a .env file.
    google_client_id: str = ""
    google_client_secret: str = ""
    
    # Backend URL for OAuth redirect (used in production/docker)
    backend_url: str = "http://localhost:8000"
    
    # Frontend redirect URL after OAuth
    frontend_url: str = "http://localhost:5173"

    class Config:
        env_file = ".env"


settings = Settings()
