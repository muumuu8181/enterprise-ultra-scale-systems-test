from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./inventory.db"
    debug: bool = True
    cors_origins: list[str] = ["*"]

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
