from datetime import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base

class UserAuth(Base):
    __tablename__ = "user_auth"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False) # email, google, apple, guest
    provider_id: Mapped[str] = mapped_column(String(255), nullable=False) # email address or oauth sub
    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_login: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class DeviceToken(Base):
    __tablename__ = "device_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    device_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True) # Unique per device
    fcm_token: Mapped[str] = mapped_column(String(255), nullable=False)
    platform: Mapped[str] = mapped_column(String(20), nullable=False) # ios, android
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
