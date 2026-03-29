import os

class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/agri_db")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    INFLUXDB_URL: str = os.getenv("INFLUXDB_URL", "http://localhost:8086")
    INFLUXDB_TOKEN: str = os.getenv("INFLUXDB_TOKEN", "my-token")
    INFLUXDB_ORG: str = os.getenv("INFLUXDB_ORG", "my-org")
    INFLUXDB_BUCKET: str = os.getenv("INFLUXDB_BUCKET", "agri_bucket")

settings = Settings()
