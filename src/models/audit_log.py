from sqlalchemy import String, Text, UUID, JSON
from sqlalchemy.orm import Mapped, mapped_column
from .base import TimestampMixin
from ..core.database import Base
import uuid

class AuditLog(Base, TimestampMixin):
    """
    監査ログモデル
    docs/STEP2_DATABASE.md の audit_logs テーブルに対応
    """
    __tablename__ = "audit_logs"

    log_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    action: Mapped[str] = mapped_column(String(50))  # UPDATE, DELETE, VIEW
    target_table: Mapped[str] = mapped_column(String(50))
    target_id: Mapped[str] = mapped_column(String(50))
    before_data: Mapped[dict | None] = mapped_column(JSON)
    after_data: Mapped[dict | None] = mapped_column(JSON)
    ip_address: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(Text)
