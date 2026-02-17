from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/banking"
    redis_url: str = "redis://localhost:6379/0"
    secret_key: str = "supersecretkey"
    log_level: str = "INFO"
    debug: bool = False
    cors_origins: List[str] = ["*"]
    fraud_detection_enabled: bool = True
    fraud_threshold: float = 10000.0

    class Config:
        env_file = ".env"

settings = Settings()
