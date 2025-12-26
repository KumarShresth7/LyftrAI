import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    WEBHOOK_SECRET: str = "testsecret"
    DATABASE_URL: str = "sqlite:////data/app.db"
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"

settings = Settings()
