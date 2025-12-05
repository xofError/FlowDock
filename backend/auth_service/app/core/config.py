from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Auth Service"
    secret_key: str = "your-super-secret-key-change-this"
    access_token_expire_minutes: int = 60
    # OAuth2 / External provider settings (example: Google)
    # Do NOT hard-code secrets here. Configure via environment variables or a .env file.
    google_client_id: str = ""
    google_client_secret: str = ""
    
    # RabbitMQ
    RABBITMQ_URL: str = "amqp://guest:guest@rabbitmq:5672/"

    class Config:
        env_file = ".env"


settings = Settings()
