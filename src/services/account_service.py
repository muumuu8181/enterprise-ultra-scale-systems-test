from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models.account import Account
from ..models.customer import Customer
from ..core.exceptions import AccountNotFound, CustomerNotFound
from .audit_service import AuditService
import uuid
from decimal import Decimal

class AccountService:
    """口座管理サービス"""

    def __init__(self, db: AsyncSession, audit_service: AuditService):
        self.db = db
        self.audit = audit_service

    async def create_account(self, customer_id: uuid.UUID, account_type: str, currency: str = "JPY") -> Account:
        """口座を開設します"""
        # 顧客存在確認
        result = await self.db.execute(select(Customer).filter_by(customer_id=customer_id))
        customer = result.scalar_one_or_none()
        if not customer:
            raise CustomerNotFound(f"Customer {customer_id} not found")

        account = Account(
            customer_id=customer_id,
            account_type=account_type,
            currency=currency,
            balance=Decimal("0"),
            status="ACTIVE"
        )
        self.db.add(account)
        await self.db.flush()  # ID生成のため

        await self.audit.log_action(
            action="CREATE",
            target_table="accounts",
            target_id=str(account.account_id),
            after={"customer_id": str(customer_id), "type": account_type}
        )
        await self.db.commit()
        return account

    async def get_account(self, account_id: uuid.UUID) -> Account:
        """口座情報を取得します"""
        result = await self.db.execute(select(Account).filter_by(account_id=account_id))
        account = result.scalar_one_or_none()
        if not account:
            raise AccountNotFound(f"Account {account_id} not found")

        # 参照ログは負荷が高いので省略するか、要件に応じて記録
        # await self.audit.log_action("VIEW", "accounts", str(account_id))
        return account
