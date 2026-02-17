from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Marine Vessel Tracking"
    DATABASE_URL: str = "sqlite+aiosqlite:///./test.db"

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
