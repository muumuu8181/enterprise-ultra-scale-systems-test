from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from .config import get_settings

settings = get_settings()

# 非同期エンジンの作成
engine = create_async_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    echo=True,  # SQLログを出力（本番ではFalse推奨）
    future=True
)

# 非同期セッションファクトリの作成
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

class Base(DeclarativeBase):
    """SQLAlchemyモデルの基底クラス"""
    pass

async def get_db():
    """
    FastAPIのDependency Injection用データベースセッションジェネレータ
    非同期セッションを提供し、終了時にクローズします。
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
