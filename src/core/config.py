from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = "postgresql://postgres:postgres@db:5432/game_db"
    redis_url: str = "redis://redis:6379/0"
    celery_broker_url: str = "redis://redis:6379/0"
    gacha_rate_precision: int = 4
    max_gacha_per_request: int = 100
    fcm_server_key: str = "default_key"

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
