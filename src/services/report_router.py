from sqlalchemy import select
from typing import Any
from datetime import datetime, timedelta
from src.models.citizen_models import CitizenReport
from src.database import AsyncSessionLocal
import logging

logger = logging.getLogger(__name__)

async def auto_assign_department(category: str, location: Any = None) -> str:
    """
    通報カテゴリと位置情報に基づいて担当部署を自動割り当てします。
    """
    category_map = {
        "road_damage": "Road Maintenance Dept",
        "traffic_signal": "Traffic Control Center",
        "illegal_parking": "Public Safety Dept",
        "park_issue": "Parks & Recreation Dept",
        "garbage": "Sanitation Dept"
    }

    # 将来的にはlocationを使用して管轄区域判定を行うロジックを追加可能
    return category_map.get(category, "General Affairs Dept")

async def notify_citizen(report_id: int, message: str):
    """
    市民に通報のステータス変更などを通知します（モック実装）。
    """
    # 実際にはEmailやPush通知サービスと連携
    logger.info(f"Notification to Citizen (Report ID: {report_id}): {message}")
    print(f"[NOTIFICATION] Report {report_id}: {message}")

async def escalate_overdue():
    """
    対応期限切れの通報を検出し、エスカレーションします。
    """
    async with AsyncSessionLocal() as session:
        # 例えば24時間以上経過してPendingのものを抽出
        threshold = datetime.utcnow() - timedelta(hours=24)
        stmt = select(CitizenReport).where(
            CitizenReport.status == "Pending",
            CitizenReport.created_at < threshold
        )
        result = await session.execute(stmt)
        overdue_reports = result.scalars().all()

        for report in overdue_reports:
            logger.warning(f"Escalating overdue report {report.id}")
            report.assigned_dept = "Emergency Response Unit" # エスカレーション先
            # ステータスを変更するかは要件次第だが、ここでは部署変更のみとする
            await notify_citizen(report.id, "Your report has been escalated due to delay.")
            session.add(report)

        await session.commit()
