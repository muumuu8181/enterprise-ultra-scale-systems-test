import datetime
import uuid
from decimal import Decimal
from enum import Enum
from typing import List

class AccountType(Enum):
    SAVINGS = "SAVINGS"
    CURRENT = "CURRENT"
    TIME_DEPOSIT = "TIME_DEPOSIT"

class TransactionType(Enum):
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"
    TRANSFER_IN = "TRANSFER_IN"
    TRANSFER_OUT = "TRANSFER_OUT"
    INTEREST = "INTEREST"

class Transaction:
    def __init__(self, account_id: str, amount: Decimal, transaction_type: TransactionType, description: str = ""):
        self.transaction_id = str(uuid.uuid4())
        self.account_id = account_id
        self.amount = amount # Signed amount
        self.transaction_type = transaction_type
        self.timestamp = datetime.datetime.now(datetime.timezone.utc)
        self.description = description

    def __repr__(self):
        return f"<Transaction {self.transaction_id} {self.transaction_type.value} {self.amount}>"

class Account:
    def __init__(self, customer_id: str, account_type: AccountType):
        self.account_id = str(uuid.uuid4())
        self.customer_id = customer_id
        self.account_type = account_type
        self.balance = Decimal("0.00")
        self.transactions: List[Transaction] = []
        self.is_active = True

    def add_transaction(self, transaction: Transaction):
        self.transactions.append(transaction)
        self.balance += transaction.amount

    def __repr__(self):
        return f"<Account {self.account_id} {self.account_type.value} Balance: {self.balance}>"

class Customer:
    def __init__(self, name: str, address: str, tax_id: str):
        self.customer_id = str(uuid.uuid4()) # CIF
        self.name = name
        self.address = address
        self.tax_id = tax_id
        self.accounts: List[Account] = []
        self.created_at = datetime.datetime.now(datetime.timezone.utc)

    def add_account(self, account: Account):
        self.accounts.append(account)

    def __repr__(self):
        return f"<Customer {self.customer_id} {self.name}>"
