import unittest
from decimal import Decimal
from unittest.mock import MagicMock, patch

from src.models import AccountType, TransactionType
from src.deposit_service import DepositService
from src.transaction_manager import TransactionManager

class TestBankingSystem(unittest.TestCase):
    def setUp(self):
        self.service = DepositService()
        self.manager = TransactionManager(self.service)

        # Setup basic data
        self.customer_a = self.service.create_customer("Alice", "NYC", "123")
        self.account_a = self.service.create_account(self.customer_a.customer_id, AccountType.SAVINGS)

        self.customer_b = self.service.create_customer("Bob", "SF", "456")
        self.account_b = self.service.create_account(self.customer_b.customer_id, AccountType.CURRENT)

    def test_deposit(self):
        self.service.deposit(self.account_a.account_id, Decimal("100.00"))
        self.assertEqual(self.service.get_balance(self.account_a.account_id), Decimal("100.00"))

    def test_withdraw_success(self):
        self.service.deposit(self.account_a.account_id, Decimal("100.00"))
        self.service.withdraw(self.account_a.account_id, Decimal("40.00"))
        self.assertEqual(self.service.get_balance(self.account_a.account_id), Decimal("60.00"))

    def test_withdraw_insufficient_funds(self):
        self.service.deposit(self.account_a.account_id, Decimal("50.00"))
        with self.assertRaises(ValueError):
            self.service.withdraw(self.account_a.account_id, Decimal("100.00"))

    def test_transfer_success(self):
        self.service.deposit(self.account_a.account_id, Decimal("100.00"))
        self.manager.transfer(self.account_a.account_id, self.account_b.account_id, Decimal("30.00"))

        self.assertEqual(self.service.get_balance(self.account_a.account_id), Decimal("70.00"))
        self.assertEqual(self.service.get_balance(self.account_b.account_id), Decimal("30.00"))

    def test_transfer_fail_rollback(self):
        # Setup: Account A has 100
        self.service.deposit(self.account_a.account_id, Decimal("100.00"))

        # We want to fail ONLY when depositing to account_b with a specific description
        # We need to wrap the original deposit method to call it normally unless it's the target call
        original_deposit = self.service.deposit

        def side_effect(account_id, amount, description=""):
            # Check if this is the deposit step of the transfer
            if account_id == self.account_b.account_id and "Transfer from" in description:
                raise Exception("Simulated Deposit Failure")
            return original_deposit(account_id, amount, description)

        with patch.object(self.service, 'deposit', side_effect=side_effect):
            with self.assertRaisesRegex(Exception, "Simulated Deposit Failure"):
                self.manager.transfer(self.account_a.account_id, self.account_b.account_id, Decimal("30.00"), "Fail test")

        # Verify rollback: Account A should still have 100 (100 - 30 + 30), Account B should have 0
        self.assertEqual(self.service.get_balance(self.account_a.account_id), Decimal("100.00"))
        self.assertEqual(self.service.get_balance(self.account_b.account_id), Decimal("0.00"))

if __name__ == '__main__':
    unittest.main()
