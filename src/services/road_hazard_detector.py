import math
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

@dataclass
class CamMessage:
    vehicle_id: str
    timestamp: datetime
    latitude: float
    longitude: float
    speed: float  # m/s
    heading: float  # degrees
    acceleration: float  # m/s^2

@dataclass
class DenmMessage:
    originating_vehicle_id: str
    event_type: str
    event_position: Dict[str, float]
    detection_time: datetime
    validity_duration: int

class RoadHazardDetector:
    """
    道路上の危険を検知するサービスクラス
    """

    def __init__(self):
        pass

    async def analyze_cam_stream(self, messages: List[CamMessage]) -> List[DenmMessage]:
        """
        CAMストリームを解析し、危険な挙動を検知する

        Args:
            messages: CAMメッセージのリスト

        Returns:
            生成されたDENMメッセージのリスト
        """
        generated_denms = []
        for msg in messages:
            # 急ブレーキ検知 (加速度 < -4m/s^2)
            if msg.acceleration < -4.0:
                denm = await self.detect_sudden_stop(msg)
                if denm:
                    generated_denms.append(denm)

            # 逆走検知
            if await self.detect_wrong_way_driver(msg):
                 denm = DenmMessage(
                    originating_vehicle_id=msg.vehicle_id,
                    event_type="WRONG_WAY_DRIVER",
                    event_position={"lat": msg.latitude, "lon": msg.longitude},
                    detection_time=datetime.now(timezone.utc),
                    validity_duration=60
                )
                 generated_denms.append(denm)

        return generated_denms

    async def detect_sudden_stop(self, msg: CamMessage) -> Optional[DenmMessage]:
        """
        急停止を検知し、DENMメッセージを生成する
        """
        if msg.acceleration < -4.0:
            return DenmMessage(
                originating_vehicle_id=msg.vehicle_id,
                event_type="EMERGENCY_BRAKE",
                event_position={"lat": msg.latitude, "lon": msg.longitude},
                detection_time=datetime.now(timezone.utc),
                validity_duration=30 # 30秒間有効
            )
        return None

    async def detect_wrong_way_driver(self, msg: CamMessage) -> bool:
        """
        逆走車を検知する
        headingと道路の進行方向を比較して判定する
        """
        road_direction = await self._get_road_direction(msg.latitude, msg.longitude)
        if road_direction is None:
            return False

        # 車両の進行方向と道路の進行方向の差分を計算
        diff = abs(msg.heading - road_direction)
        if diff > 180:
            diff = 360 - diff

        # 150度以上の差がある場合は逆走とみなす
        return diff > 150

    async def calculate_ttc(self, vehicle1: CamMessage, vehicle2: CamMessage) -> float:
        """
        Time-to-Collision (TTC) を計算する

        Args:
            vehicle1: 車両1のCAMメッセージ
            vehicle2: 車両2のCAMメッセージ

        Returns:
            TTC(秒)。衝突のリスクがない場合は無限大(inf)
        """
        # 緯度経度から距離への簡易変換 (本来はVincenty法やHaversineなどを使用すべき)
        # 1度あたり約111kmと仮定
        dx = (vehicle2.latitude - vehicle1.latitude) * 111000
        dy = (vehicle2.longitude - vehicle1.longitude) * 111000 * math.cos(math.radians(vehicle1.latitude))
        distance = math.sqrt(dx*dx + dy*dy)

        # 相対速度 (vehicle1がvehicle2に近づく速度)
        # 簡易的にスカラー速度差を使用（同一直線上を仮定）
        # 正確には位置ベクトルと速度ベクトルを使用する必要がある
        relative_speed = vehicle1.speed - vehicle2.speed

        if relative_speed <= 0:
            return float('inf') # 接近していない

        ttc = distance / relative_speed
        return ttc

    async def _get_road_direction(self, lat: float, lon: float) -> Optional[float]:
        """
        指定位置の道路進行方向を取得する(モック)
        実際のシステムではHD Mapデータベースへのクエリが必要
        """
        # デモ用に常に北向き(0度)を返す
        return 0.0
