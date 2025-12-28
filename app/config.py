import os
import sys
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    WEBHOOK_SECRET: str
    DATABASE_URL: str = "sqlite:///./data/app.db"
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"

try:
    settings = Settings()
except Exception as e:
    print("FATAL: WEBHOOK_SECRET is not set.")
    sys.exit(1)