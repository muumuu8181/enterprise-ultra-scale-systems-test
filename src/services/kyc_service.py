from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from src.models.kyc_models import KYCApplication, KYCStatus

class KYCService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def check_aml_list(self, name: str) -> bool:
        """
        AML (マネーロンダリング防止) リストのチェックを行う (スタブ実装)

        Args:
            name (str): チェック対象の名前

        Returns:
            bool: ブラックリストに含まれる場合はTrue, それ以外はFalse
        """
        # 単純なスタブ実装: 特定の名前が含まれる場合にTrueを返す
        blacklisted_names = ["Terrorist", "Criminal", "Launderer"]
        if any(b_name in name for b_name in blacklisted_names):
            return True
        return False

    async def submit_kyc(self, customer_id: str, name: str, dob: str, address: str, id_number: str) -> KYCApplication:
        """
        KYC申請を提出する

        Args:
            customer_id (str): 顧客ID
            name (str): 名前
            dob (str): 生年月日
            address (str): 住所
            id_number (str): ID番号

        Returns:
            KYCApplication: 作成されたKYC申請オブジェクト
        """
        # AMLチェック
        is_blacklisted = await self.check_aml_list(name)

        # 既存の申請があるか確認 (オプション: 重複申請を防ぐ場合)
        # 今回は単純化のため省略、常に新規作成

        documents = {
            "name": name,
            "dob": dob,
            "address": address,
            "id_number": id_number,
            "aml_check": "FAILED" if is_blacklisted else "PASSED"
        }

        # AMLチェックに失敗した場合、自動的に拒否するロジックを入れることも可能だが、
        # ここではステータスをPENDINGにし、管理者が判断できるようにする、または自動REJECTにする。
        # 要件に従い、単純に申請を作成する。

        kyc_app = KYCApplication(
            customer_id=customer_id,
            status=KYCStatus.PENDING,
            documents=documents
        )

        if is_blacklisted:
             # 自動拒否ロジック (オプション)
             kyc_app.status = KYCStatus.REJECTED
             kyc_app.rejection_reason = "AML Check Failed"
             kyc_app.verified_at = datetime.now(timezone.utc)

        self.db.add(kyc_app)
        await self.db.commit()
        await self.db.refresh(kyc_app)
        return kyc_app

    async def get_kyc_status(self, customer_id: str) -> Optional[KYCApplication]:
        """
        顧客IDからKYCステータスを取得する

        Args:
            customer_id (str): 顧客ID

        Returns:
            Optional[KYCApplication]: KYC申請オブジェクト
        """
        query = select(KYCApplication).where(KYCApplication.customer_id == customer_id).order_by(KYCApplication.submitted_at.desc())
        result = await self.db.execute(query)
        # 最新の申請を返す
        return result.scalars().first()

    async def verify_kyc(self, customer_id: str) -> Optional[KYCApplication]:
        """
        KYC申請を承認する (管理者用)

        Args:
            customer_id (str): 顧客ID

        Returns:
            Optional[KYCApplication]: 更新されたKYC申請オブジェクト
        """
        kyc_app = await self.get_kyc_status(customer_id)
        if not kyc_app:
            return None

        if kyc_app.status != KYCStatus.PENDING:
            # 既に処理済みの場合は何もしないか、エラーを返す
            # ここでは現在の状態を返す
            return kyc_app

        kyc_app.status = KYCStatus.VERIFIED
        kyc_app.verified_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(kyc_app)
        return kyc_app

    async def reject_kyc(self, customer_id: str, reason: str) -> Optional[KYCApplication]:
        """
        KYC申請を拒否する (管理者用)

        Args:
            customer_id (str): 顧客ID
            reason (str): 拒否理由

        Returns:
            Optional[KYCApplication]: 更新されたKYC申請オブジェクト
        """
        kyc_app = await self.get_kyc_status(customer_id)
        if not kyc_app:
            return None

        if kyc_app.status != KYCStatus.PENDING:
            return kyc_app

        kyc_app.status = KYCStatus.REJECTED
        kyc_app.rejection_reason = reason
        kyc_app.verified_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(kyc_app)
        return kyc_app

    async def get_pending_applications(self, skip: int = 0, limit: int = 10) -> List[KYCApplication]:
        """
        保留中のKYC申請一覧を取得する (管理者用)

        Args:
            skip (int): ページネーションのスキップ数
            limit (int): 取得件数

        Returns:
            List[KYCApplication]: KYC申請のリスト
        """
        query = select(KYCApplication).where(KYCApplication.status == KYCStatus.PENDING).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()
