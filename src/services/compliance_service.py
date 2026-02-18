from sqlalchemy.ext.asyncio import AsyncSession
from src.models.compliance_models import SanctionsCheck, SAR
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
import random

class ComplianceService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def check_sanctions_list(self, customer_id: str) -> SanctionsCheck:
        """
        OFAC/国連制裁リストと照合を行う (モック実装)
        """
        # モックロジック: 特定のIDを制裁対象とする
        sanctioned_ids = ["bad_guy", "sanctioned_entity_001"]
        status = "MATCHED" if customer_id in sanctioned_ids else "CLEAR"
        matched_list = "OFAC" if status == "MATCHED" else None

        check_record = SanctionsCheck(
            customer_id=customer_id,
            status=status,
            matched_list=matched_list,
            checked_at=datetime.now(timezone.utc)
        )
        self.db.add(check_record)
        await self.db.commit()
        await self.db.refresh(check_record)
        return check_record

    async def generate_sar(self, customer_id: str, transaction_ids: Optional[List[str]] = None) -> SAR:
        """
        疑わしい取引報告書 (SAR) を自動生成する
        """
        # モックデータ生成
        # 実際には transaction_ids に基づいてDBから取引を取得する
        transactions: Dict[str, Any] = {
            "tx_1": {"amount": 1000000, "currency": "USD", "destination": "Unknown"},
            "tx_2": {"amount": 5000, "currency": "JPY", "destination": "Known"}
        }
        risk_indicators = ["High Value Transaction", "Rapid Movement of Funds"]

        sar_record = SAR(
            customer_id=customer_id,
            transactions=transactions,
            risk_indicators=risk_indicators,
            submitted_at=datetime.now(timezone.utc)
        )
        self.db.add(sar_record)
        await self.db.commit()
        await self.db.refresh(sar_record)
        return sar_record

    async def check_fatf_requirements(self, customer_id: str) -> bool:
        """
        FATF勧告に基づくチェックを行う
        """
        # 単純なモック: 常にTrue (準拠) とする
        return True

    async def calculate_aml_score(self, customer_id: str) -> Dict[str, Any]:
        """
        AMLリスクスコアを算出する (取引パターン分析)
        """
        # モックロジック
        if customer_id == "high_risk_user":
            score = 85.0
            level = "HIGH"
        else:
            score = 15.0
            level = "LOW"

        return {
            "customer_id": customer_id,
            "risk_score": score,
            "risk_level": level,
            "analyzed_at": datetime.now(timezone.utc)
        }
