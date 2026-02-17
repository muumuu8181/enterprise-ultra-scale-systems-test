from datetime import datetime, timezone
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncAttrs

class Base(AsyncAttrs, DeclarativeBase):
    """
    SQLAlchemy 2.0のベースクラス
    AsyncAttrsを使用して非同期操作をサポート
    """
    pass

def utcnow():
    return datetime.now(timezone.utc)
