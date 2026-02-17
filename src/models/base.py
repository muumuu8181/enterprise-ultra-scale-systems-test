from sqlalchemy import Column, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from ..core.database import Base

class TimestampMixin:
    """共通のタイムスタンプカラム（作成日時、更新日時）を提供"""
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
