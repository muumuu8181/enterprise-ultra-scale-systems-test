from decimal import Decimal
from typing import Dict, Optional
from src.models import Account, AccountType, Customer, Transaction, TransactionType

class DepositService:
    def __init__(self):
        self.customers: Dict[str, Customer] = {}
        self.accounts: Dict[str, Account] = {}

    def create_customer(self, name: str, address: str, tax_id: str) -> Customer:
        customer = Customer(name, address, tax_id)
        self.customers[customer.customer_id] = customer
        return customer

    def create_account(self, customer_id: str, account_type: AccountType) -> Account:
        if customer_id not in self.customers:
            raise ValueError(f"Customer with ID {customer_id} does not exist.")

        account = Account(customer_id, account_type)
        self.accounts[account.account_id] = account
        self.customers[customer_id].add_account(account)
        return account

    def get_account(self, account_id: str) -> Optional[Account]:
        return self.accounts.get(account_id)

    def deposit(self, account_id: str, amount: Decimal, description: str = "") -> Transaction:
        if amount <= 0:
            raise ValueError("Deposit amount must be positive.")

        account = self.get_account(account_id)
        if not account:
            raise ValueError(f"Account with ID {account_id} does not exist.")

        # In a real system, you would lock the account here
        transaction = Transaction(account_id, amount, TransactionType.DEPOSIT, description)
        account.add_transaction(transaction)
        return transaction

    def withdraw(self, account_id: str, amount: Decimal, description: str = "") -> Transaction:
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive.")

        account = self.get_account(account_id)
        if not account:
            raise ValueError(f"Account with ID {account_id} does not exist.")

        if account.balance < amount:
            raise ValueError("Insufficient funds.")

        transaction = Transaction(account_id, -amount, TransactionType.WITHDRAWAL, description)
        account.add_transaction(transaction)
        return transaction

    def get_balance(self, account_id: str) -> Decimal:
        account = self.get_account(account_id)
        if not account:
            raise ValueError(f"Account with ID {account_id} does not exist.")
        return account.balance
