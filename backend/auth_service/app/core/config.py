from pydantic import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Auth Service"
    secret_key: str = "CHANGE_ME"
    access_token_expire_minutes: int = 60

    class Config:
        env_file = ".env"


settings = Settings()
