from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/broadcast_db"
    REDIS_URL: str = "redis://localhost:6379/0"
    MINIO_URL: str = "http://localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    SECRET_KEY: str = "secret"

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
