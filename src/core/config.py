from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    """
    アプリケーション設定クラス
    環境変数から設定を読み込みます。
    """
    PROJECT_NAME: str = "Banking Core System"
    API_V1_STR: str = "/api/v1"

    # データベース設定
    POSTGRES_USER: str = "user"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: str = "5432"
    POSTGRES_DB: str = "banking_core"

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        """SQLAlchemy用の非同期接続URIを生成します"""
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    class Config:
        case_sensitive = True

@lru_cache()
def get_settings():
    """設定インスタンスを取得します（キャッシュ付き）"""
    return Settings()
