from decimal import Decimal
from typing import List
from src.deposit_service import DepositService
from src.models import TransactionType, Transaction

class TransactionManager:
    def __init__(self, deposit_service: DepositService):
        self.deposit_service = deposit_service

    def transfer(self, from_account_id: str, to_account_id: str, amount: Decimal, description: str = "") -> List[Transaction]:
        """
        Executes a transfer between two accounts with basic atomicity.
        If the credit to the receiver fails, the debit from the sender is rolled back.
        """
        if amount <= 0:
            raise ValueError("Transfer amount must be positive.")

        # Verify accounts exist
        if not self.deposit_service.get_account(from_account_id):
            raise ValueError(f"Sender account {from_account_id} does not exist.")
        if not self.deposit_service.get_account(to_account_id):
            raise ValueError(f"Receiver account {to_account_id} does not exist.")

        # In a real system, you would acquire locks on both accounts here to prevent race conditions.
        # e.g., lock(from_account_id), lock(to_account_id)

        debit_transaction = None
        credit_transaction = None

        try:
            # Step 1: Withdraw from sender
            # The service handles balance check and throws ValueError if insufficient funds
            debit_transaction = self.deposit_service.withdraw(
                from_account_id,
                amount,
                f"Transfer to {to_account_id}: {description}"
            )
            # Override type for clarity
            debit_transaction.transaction_type = TransactionType.TRANSFER_OUT

            # Step 2: Deposit to receiver
            credit_transaction = self.deposit_service.deposit(
                to_account_id,
                amount,
                f"Transfer from {from_account_id}: {description}"
            )
            credit_transaction.transaction_type = TransactionType.TRANSFER_IN

            return [debit_transaction, credit_transaction]

        except Exception as e:
            # If step 2 fails (or step 1 fails), we need to rollback step 1 if it succeeded
            if debit_transaction and not credit_transaction:
                # Rollback Step 1: Re-deposit the money to sender
                try:
                    rollback_transaction = self.deposit_service.deposit(
                        from_account_id,
                        amount,
                        f"ROLLBACK: Transfer to {to_account_id} failed"
                    )
                    # Ideally, link this rollback transaction to the original debit transaction for audit
                except Exception as rollback_error:
                    # If rollback fails, we are in a critical inconsistent state (money lost).
                    # In a real system, this would trigger an immediate alert to operations.
                    raise RuntimeError(f"CRITICAL: Rollback failed after transfer error. System state inconsistent. Original error: {e}. Rollback error: {rollback_error}")

            # Re-raise the original exception to inform the caller
            raise e
