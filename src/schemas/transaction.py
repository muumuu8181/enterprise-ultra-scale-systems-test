from pydantic import BaseModel, ConfigDict
from decimal import Decimal
from typing import Optional
import uuid
from datetime import datetime

class TransactionBase(BaseModel):
    amount: Decimal
    description: Optional[str] = None

class DepositRequest(TransactionBase):
    pass

class WithdrawRequest(TransactionBase):
    pass

class TransferRequest(TransactionBase):
    from_account_id: uuid.UUID
    to_account_id: uuid.UUID

class TransactionResponse(BaseModel):
    transaction_id: uuid.UUID
    type: str
    status: str
    description: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class TransactionEntryResponse(BaseModel):
    entry_id: uuid.UUID
    transaction_id: uuid.UUID
    account_id: uuid.UUID
    amount: Decimal
    direction: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
