from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True)

    DATABASE_URL: str = "sqlite+aiosqlite:///./mlops.db"
    SECRET_KEY: str = "supersecretkey"

settings = Settings()
