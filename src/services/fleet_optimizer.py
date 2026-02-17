from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, asc
from geoalchemy2.functions import ST_Distance
from src.models.fleet_models import Fleet, FleetVehicle, FleetTask, Vehicle
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

class FleetOptimizer:
    """
    フリート管理および最適化ロジックを提供するサービスクラス
    """

    async def assign_nearest_vehicle(self, db: AsyncSession, task_id: int) -> Optional[int]:
        """
        タスクに最も近い利用可能な車両を割り当てる

        Args:
            db (AsyncSession): データベースセッション
            task_id (int): 対象タスクID

        Returns:
            Optional[int]: 割り当てられた FleetVehicle.id (失敗時は None)
        """
        # タスク情報の取得
        stmt = select(FleetTask).where(FleetTask.id == task_id)
        result = await db.execute(stmt)
        task = result.scalar_one_or_none()

        if not task:
            return None

        if task.vehicle_id:
            return task.vehicle_id  # 既に割り当て済み

        # フリート内の利用可能な車両を検索し、タスク目的地への距離でソート
        # FleetVehicle -> Vehicle (location) join
        # 注意: PostGIS関数ST_Distanceを使用
        stmt = (
            select(FleetVehicle)
            .join(Vehicle, FleetVehicle.vehicle_id == Vehicle.id)
            .where(
                FleetVehicle.fleet_id == task.fleet_id,
                FleetVehicle.status == "active",  # 利用可能なステータス
                FleetVehicle.current_driver_id.is_not(None) # ドライバーが必要と仮定
            )
            .order_by(ST_Distance(Vehicle.location, task.destination))
            .limit(1)
        )

        result = await db.execute(stmt)
        nearest_vehicle = result.scalar_one_or_none()

        if nearest_vehicle:
            # タスク割り当て更新
            task.vehicle_id = nearest_vehicle.id
            task.status = "assigned"
            task.assigned_at = datetime.now(timezone.utc)
            await db.commit()
            await db.refresh(task)
            return nearest_vehicle.id

        return None

    async def optimize_routes(self, db: AsyncSession, fleet_id: int) -> List[FleetTask]:
        """
        フリート内のタスクを優先度順に最適化（ソート）して返す
        本来は巡回セールスマン問題(TSP)などのアルゴリズムを適用するが、
        ここでは単純に優先度(priority)と作成日時順でソートする。

        Args:
            db (AsyncSession): データベースセッション
            fleet_id (int): フリートID

        Returns:
            List[FleetTask]: 最適化されたタスクリスト
        """
        stmt = (
            select(FleetTask)
            .where(
                FleetTask.fleet_id == fleet_id,
                FleetTask.status.in_(["pending", "assigned"])
            )
            .order_by(desc(FleetTask.priority), asc(FleetTask.created_at))
        )

        result = await db.execute(stmt)
        tasks = result.scalars().all()
        return list(tasks)

    async def generate_fleet_report(self, db: AsyncSession, fleet_id: int) -> Dict[str, Any]:
        """
        フリートの分析レポートを生成する（総走行距離、燃費、稼働状況など）

        Args:
            db (AsyncSession): データベースセッション
            fleet_id (int): フリートID

        Returns:
            Dict[str, Any]: 分析結果
        """
        # 車両数と総走行距離の集計
        stmt = (
            select(
                func.count(FleetVehicle.id).label("vehicle_count"),
                func.sum(FleetVehicle.odometer).label("total_odometer")
            )
            .where(FleetVehicle.fleet_id == fleet_id)
        )

        result = await db.execute(stmt)
        stats = result.one()

        vehicle_count = stats.vehicle_count or 0
        total_odometer = stats.total_odometer or 0.0

        # 簡易的な燃費計算 (仮定: 平均燃費 10km/L)
        estimated_fuel_consumption = total_odometer / 10.0

        # アイドリング時間の集計 (データがないためダミー値または0を返す)
        # 本来はセンサーデータから集計する
        idling_time_hours = 0.0

        return {
            "fleet_id": fleet_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_vehicles": vehicle_count,
            "total_distance_km": total_odometer,
            "estimated_fuel_consumption_liters": estimated_fuel_consumption,
            "total_idling_hours": idling_time_hours,
            "status": "generated"
        }
