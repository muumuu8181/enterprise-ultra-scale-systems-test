from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models.account import Account
from ..models.transaction import Transaction, TransactionEntry
from ..core.exceptions import AccountNotFound, InsufficientFunds, TransactionFailed
from .audit_service import AuditService
from .account_service import AccountService
import uuid
from decimal import Decimal

class TransactionService:
    """
    取引サービス (入出金・振込)
    2フェーズコミット（または厳密なACIDトランザクション）により整合性を保証します。
    """

    def __init__(self, db: AsyncSession, audit_service: AuditService, account_service: AccountService):
        self.db = db
        self.audit = audit_service
        self.account_service = account_service

    async def _check_idempotency(self, idempotency_key: str | None) -> Transaction | None:
        if not idempotency_key:
            return None
        q = select(Transaction).filter_by(idempotency_key=idempotency_key)
        result = await self.db.execute(q)
        return result.scalar_one_or_none()

    async def deposit(self, account_id: uuid.UUID, amount: Decimal, description: str = "Deposit", idempotency_key: str | None = None) -> Transaction:
        """入金処理"""
        existing = await self._check_idempotency(idempotency_key)
        if existing:
            return existing

        if amount <= 0:
            raise TransactionFailed("Amount must be positive")

        account = await self.account_service.get_account(account_id)

        # トランザクションヘッダー作成
        tx_header = Transaction(
            type="DEPOSIT",
            status="COMPLETED",
            description=description,
            idempotency_key=idempotency_key
        )
        self.db.add(tx_header)
        await self.db.flush()

        # 口座残高更新 (Locking for update recommended in high concurrency, but skip for now or use with_for_update)
        # PostgreSQLのUPDATEは行ロックを取得するため、単一ステートメントなら安全だが、
        # 読み取ってから書き込む場合は SELECT ... FOR UPDATE が必要。
        # ここでは get_account で取得したオブジェクトを更新する前に再取得してロックするのがベスト。

        # ロック付きで再取得
        q = select(Account).filter_by(account_id=account_id).with_for_update()
        result = await self.db.execute(q)
        locked_account = result.scalar_one()

        locked_account.balance += amount

        # 取引明細 (Credit)
        entry = TransactionEntry(
            transaction_id=tx_header.transaction_id,
            account_id=account_id,
            amount=amount,
            direction="CREDIT" # 入金
        )
        self.db.add(entry)

        await self.audit.log_action(
            action="DEPOSIT",
            target_table="accounts",
            target_id=str(account_id),
            after={"amount": str(amount), "new_balance": str(locked_account.balance)}
        )
        await self.db.commit()

        return tx_header

    async def withdraw(self, account_id: uuid.UUID, amount: Decimal, description: str = "Withdrawal", idempotency_key: str | None = None) -> Transaction:
        """出金処理"""
        existing = await self._check_idempotency(idempotency_key)
        if existing:
            return existing

        if amount <= 0:
            raise TransactionFailed("Amount must be positive")

        # ロック付きで取得
        q = select(Account).filter_by(account_id=account_id).with_for_update()
        result = await self.db.execute(q)
        account = result.scalar_one_or_none()
        if not account:
            raise AccountNotFound(f"Account {account_id} not found")

        if account.balance < amount:
            raise InsufficientFunds("Insufficient funds")

        # トランザクションヘッダー
        tx_header = Transaction(
            type="WITHDRAWAL",
            status="COMPLETED",
            description=description,
            idempotency_key=idempotency_key
        )
        self.db.add(tx_header)
        await self.db.flush()

        account.balance -= amount

        # 取引明細 (Debit)
        entry = TransactionEntry(
            transaction_id=tx_header.transaction_id,
            account_id=account_id,
            amount=amount,
            direction="DEBIT" # 出金
        )
        self.db.add(entry)

        await self.audit.log_action(
            action="WITHDRAWAL",
            target_table="accounts",
            target_id=str(account_id),
            after={"amount": str(amount), "new_balance": str(account.balance)}
        )
        await self.db.commit()

        return tx_header

    async def transfer(self, from_account_id: uuid.UUID, to_account_id: uuid.UUID, amount: Decimal, description: str = "Transfer", idempotency_key: str | None = None) -> Transaction:
        """
        振込処理 (Atomic Transfer)
        2つの口座間の資金移動を単一のACIDトランザクションとして実行します。
        デッドロック防止のため、Account ID順にロックを取得します。
        """
        existing = await self._check_idempotency(idempotency_key)
        if existing:
            return existing

        if amount <= 0:
            raise TransactionFailed("Amount must be positive")
        if from_account_id == to_account_id:
            raise TransactionFailed("Cannot transfer to same account")

        # デッドロック防止：ID順にロック
        first_id, second_id = sorted([from_account_id, to_account_id])

        # 1. ロック取得
        q1 = select(Account).filter_by(account_id=first_id).with_for_update()
        res1 = await self.db.execute(q1)
        acc1 = res1.scalar_one_or_none()

        q2 = select(Account).filter_by(account_id=second_id).with_for_update()
        res2 = await self.db.execute(q2)
        acc2 = res2.scalar_one_or_none()

        if not acc1 or not acc2:
            raise AccountNotFound("One or both accounts not found")

        # 元の変数名にマッピング
        from_acc = acc1 if acc1.account_id == from_account_id else acc2
        to_acc = acc1 if acc1.account_id == to_account_id else acc2

        # 2. 残高チェック
        if from_acc.balance < amount:
            raise InsufficientFunds("Insufficient funds in source account")

        # 3. トランザクションヘッダー作成
        tx_header = Transaction(
            type="TRANSFER",
            status="COMPLETED",
            description=description,
            idempotency_key=idempotency_key
        )
        self.db.add(tx_header)
        await self.db.flush()

        # 4. バランス更新
        from_acc.balance -= amount
        to_acc.balance += amount

        # 5. 明細作成 (Debit From, Credit To)
        entry_from = TransactionEntry(
            transaction_id=tx_header.transaction_id,
            account_id=from_account_id,
            amount=amount,
            direction="DEBIT"
        )
        entry_to = TransactionEntry(
            transaction_id=tx_header.transaction_id,
            account_id=to_account_id,
            amount=amount,
            direction="CREDIT"
        )
        self.db.add(entry_from)
        self.db.add(entry_to)

        # 6. 監査ログ
        await self.audit.log_action("TRANSFER_OUT", "accounts", str(from_account_id), after={"amount": str(amount)})
        await self.audit.log_action("TRANSFER_IN", "accounts", str(to_account_id), after={"amount": str(amount)})
        await self.db.commit()

        return tx_header

    async def get_transactions(self, account_id: uuid.UUID) -> list[TransactionEntry]:
        """口座の取引履歴を取得"""
        # 口座存在確認
        await self.account_service.get_account(account_id)

        # 明細取得
        q = select(TransactionEntry).filter_by(account_id=account_id).order_by(TransactionEntry.created_at.desc())
        result = await self.db.execute(q)
        return result.scalars().all()
