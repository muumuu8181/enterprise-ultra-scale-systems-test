from sqlalchemy import String, Boolean, Column
from src.database import Base

class Customer(Base):
    __tablename__ = "customers"

    id = Column(String, primary_key=True, index=True)
    pin_hash = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
