from datetime import datetime
from typing import List, Optional
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column
from pydantic import BaseModel

# SQLAlchemy Base
class Base(DeclarativeBase):
    pass

# --- SQLAlchemy Models ---

class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    jan_code: Mapped[str] = mapped_column(String, unique=True, index=True)
    name: Mapped[str] = mapped_column(String)
    price: Mapped[int] = mapped_column(Integer) # JPY usually integer
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    store_id: Mapped[str] = mapped_column(String, index=True) # "store_001"
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    total_amount: Mapped[int] = mapped_column(Integer)
    payment_method: Mapped[str] = mapped_column(String) # "cash", "credit"
    synced: Mapped[bool] = mapped_column(Boolean, default=False) # For Edge -> HQ sync

    items: Mapped[List["TransactionItem"]] = relationship(back_populates="transaction", cascade="all, delete-orphan")

class TransactionItem(Base):
    __tablename__ = "transaction_items"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    transaction_id: Mapped[int] = mapped_column(ForeignKey("transactions.id"))
    product_id: Mapped[int] = mapped_column(Integer) # Store the ID at time of sale
    product_name: Mapped[str] = mapped_column(String) # Snapshot name
    quantity: Mapped[int] = mapped_column(Integer)
    unit_price: Mapped[int] = mapped_column(Integer) # Snapshot price

    transaction: Mapped["Transaction"] = relationship(back_populates="items")


# --- Pydantic Schemas ---

class ProductBase(BaseModel):
    jan_code: str
    name: str
    price: int

class ProductCreate(ProductBase):
    pass

class ProductRead(ProductBase):
    id: int
    updated_at: datetime

    class Config:
        from_attributes = True

class TransactionItemCreate(BaseModel):
    product_id: int
    quantity: int

class TransactionCreate(BaseModel):
    store_id: str
    payment_method: str
    items: List[TransactionItemCreate]

class TransactionItemRead(BaseModel):
    product_name: str
    quantity: int
    unit_price: int

class TransactionRead(BaseModel):
    id: int
    store_id: str
    timestamp: datetime
    total_amount: int
    payment_method: str
    synced: bool
    items: List[TransactionItemRead]

    class Config:
        from_attributes = True

class TransactionSync(BaseModel):
    store_id: str
    timestamp: datetime
    total_amount: int
    payment_method: str
    items: List[TransactionItemRead]
