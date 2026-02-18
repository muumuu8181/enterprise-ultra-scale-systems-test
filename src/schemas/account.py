from pydantic import BaseModel, ConfigDict
from decimal import Decimal
from typing import Optional
import uuid
from datetime import datetime

class AccountBase(BaseModel):
    account_type: str
    currency: str = "JPY"

class AccountCreate(AccountBase):
    customer_id: uuid.UUID

class AccountResponse(AccountBase):
    account_id: uuid.UUID
    customer_id: uuid.UUID
    balance: Decimal
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
