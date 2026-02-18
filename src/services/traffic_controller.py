import logging
import json
from src.database import AsyncSessionLocal
from src.models.city_models import TrafficSignal
from sqlalchemy import select, update

logger = logging.getLogger(__name__)

class TrafficController:
    """
    交通制御サービスクラス: 信号機の最適化や渋滞検知を行う
    """
    def __init__(self):
        self.websockets = [] # 接続中のWebSocketクライアント

    def calculate_webster_timing(self, lost_time: float, flow_ratios: list[float]) -> int:
        """
        Webster法を用いて最適なサイクル時間を計算する
        式: C = (1.5 * L + 5) / (1 - Y)
        """
        Y = sum(flow_ratios)
        if Y >= 1.0:
            logger.warning("Flow ratio sum exceeds 1.0, defaulting to max cycle time")
            return 120

        cycle_time = (1.5 * lost_time + 5) / (1 - Y)
        # サイクル時間は30秒から120秒の間に制限するのが一般的
        return int(max(min(cycle_time, 120), 30))

    async def optimize_intersection(self, intersection_id: str, current_flows: dict):
        """
        交差点の信号時間を最適化し、DBを更新する
        """
        # 仮のロストタイム (全現示の損失時間の合計)
        L = 10.0

        # フロー比の計算 (q/s)
        # current_flows = {"signal_group_1": flow_ratio, ...}
        flow_ratios = list(current_flows.values())

        optimal_cycle = self.calculate_webster_timing(L, flow_ratios)

        # 緑時間の配分 (Yに対する比率で配分)
        Y = sum(flow_ratios)
        updates = {}

        async with AsyncSessionLocal() as session:
            for group, ratio in current_flows.items():
                # 有効緑時間 = サイクル時間 - ロストタイム
                effective_green = (ratio / Y) * (optimal_cycle - L)
                green_time = int(max(effective_green, 10)) # 最小緑時間10秒

                updates[group] = green_time

                stmt = (
                    update(TrafficSignal)
                    .where(TrafficSignal.intersection_id == intersection_id)
                    .where(TrafficSignal.signal_group == group)
                    .values(cycle_time=optimal_cycle, green_time=green_time)
                )
                await session.execute(stmt)

            await session.commit()

        await self.broadcast_signal_update(intersection_id, {"cycle": optimal_cycle, "allocations": updates})
        return {"cycle_time": optimal_cycle, "allocations": updates}

    def detect_congestion(self, sensor_value: float, threshold: float = 0.8) -> bool:
        """
        センサー値（占有率など）が閾値を超えた場合に渋滞と判定
        """
        return sensor_value > threshold

    async def broadcast_signal_update(self, intersection_id: str, data: dict):
        """
        WebSocket経由で状態変更を送信 (実装はプレースホルダー)
        """
        message = json.dumps({"intersection_id": intersection_id, "data": data})
        # for ws in self.websockets:
        #     await ws.send_text(message)
        logger.info(f"Broadcast update for {intersection_id}: {message}")
