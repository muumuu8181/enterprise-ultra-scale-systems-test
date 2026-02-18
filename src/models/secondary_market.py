from sqlalchemy import String, Integer, Float, Enum as SQLEnum, DateTime, Boolean, DECIMAL
from sqlalchemy.orm import Mapped, mapped_column
from src.core.database import Base
import enum
from datetime import datetime, timezone

class ListingStatus(str, enum.Enum):
    LISTED = "listed"
    SOLD = "sold"
    CANCELLED = "cancelled"

class TransferType(str, enum.Enum):
    RESALE = "resale"
    GIFT = "gift"

class SecondaryListing(Base):
    __tablename__ = "secondary_listings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ticket_id: Mapped[str] = mapped_column(String, index=True)
    seller_id: Mapped[str] = mapped_column(String, index=True)
    asking_price: Mapped[float] = mapped_column(Float) # Using Float for simplicity, DECIMAL is better for money but requires more setup
    platform_fee_pct: Mapped[float] = mapped_column(Float)
    status: Mapped[ListingStatus] = mapped_column(SQLEnum(ListingStatus), default=ListingStatus.LISTED)

class TransferRecord(Base):
    __tablename__ = "transfer_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ticket_id: Mapped[str] = mapped_column(String, index=True)
    from_user: Mapped[str] = mapped_column(String)
    to_user: Mapped[str] = mapped_column(String)
    transfer_type: Mapped[TransferType] = mapped_column(SQLEnum(TransferType))
    transfer_price: Mapped[float] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class Waitlist(Base):
    __tablename__ = "waitlists"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    event_id: Mapped[str] = mapped_column(String, index=True)
    user_id: Mapped[str] = mapped_column(String)
    tier_preference: Mapped[str] = mapped_column(String)
    max_price: Mapped[float] = mapped_column(Float)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    notified: Mapped[bool] = mapped_column(Boolean, default=False)
