from pydantic import BaseModel, ConfigDict
from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime

class AccountType(str, Enum):
    CHECKING = "checking"
    SAVINGS = "savings"
    INVESTMENT = "investment"
    CRYPTO = "crypto"

class TransactionType(str, Enum):
    DEBIT = "debit"
    CREDIT = "credit"

class AccountCreate(BaseModel):
    user_id: int
    account_name: str
    account_type: AccountType
    balance: float = 0.0
    currency: str = "USD"
    institution: Optional[str] = "Manual"

class AccountResponse(BaseModel):
    id: int
    user_id: int
    account_name: str
    account_type: AccountType
    balance: float
    currency: str
    institution: Optional[str]

    model_config = ConfigDict(from_attributes=True)

class ConnectAccountRequest(BaseModel):
    user_id: int
    institution: str
    account_name: str
    account_type: AccountType

class ManualAccountRequest(BaseModel):
    user_id: int
    account_name: str
    account_type: AccountType
    balance: float
    currency: str = "USD"

class CategorizeTransactionRequest(BaseModel):
    transaction_id: int

class TransactionResponse(BaseModel):
    id: int
    account_id: int
    amount: float
    transaction_type: TransactionType
    merchant: Optional[str]
    category: Optional[str]
    date: datetime
    notes: Optional[str]
    tags: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)
