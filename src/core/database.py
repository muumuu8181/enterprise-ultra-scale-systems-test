from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from src.core.config import settings

# 非同期エンジンの作成
engine = create_async_engine(settings.database_url, echo=settings.debug)

# 非同期セッションの作成
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

# ベースモデルの作成
Base = declarative_base()

# 依存関係注入のためのDBセッション取得関数
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
