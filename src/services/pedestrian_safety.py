import math
from datetime import datetime, timezone
from typing import List, Dict, Any, Tuple
from sqlalchemy import select, func, cast
from sqlalchemy.ext.asyncio import AsyncSession
from geoalchemy2 import Geography
from geoalchemy2.elements import WKTElement

from src.models.v2x_models import Vehicle
from src.models.pedestrian_models import SafetyAlert

class PedestrianSafety:
    """
    歩行者保護サービス
    車両と歩行者の接近検知および警告生成を行う
    """

    def __init__(self, warning_threshold_seconds: float = 3.0):
        self.warning_threshold_seconds = warning_threshold_seconds
        self.earth_radius = 6371000.0  # meters

    async def detect_conflict(
        self,
        pedestrian_id: str,
        lat: float,
        lon: float,
        speed: float,
        heading: float,
        db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """
        車両との接近を検知する (TTC < 3秒)

        Args:
            pedestrian_id (str): 歩行者ID
            lat (float): 緯度
            lon (float): 経度
            speed (float): 歩行者速度 (m/s)
            heading (float): 歩行者進行方向 (度)
            db (AsyncSession): DBセッション

        Returns:
            List[Dict]: 検知された危険情報のリスト
        """
        if not db:
            return []

        # 1. 近傍の車両を検索 (例えば半径100m)
        # PostGISのST_DWithinを使用したいが、テスト容易性と依存関係最小化のため
        # 全車両を取得して距離フィルタする（ただし座標取得のためにST_X/Yを使用）

        # 検索範囲 (m)
        search_radius = 100.0

        point = WKTElement(f"POINT({lon} {lat})", srid=4326)

        # ST_X = Longitude, ST_Y = Latitude
        # Use ST_DWithin for filtering (Performance optimization)
        # Cast to Geography to use meters
        stmt = select(
            Vehicle,
            func.ST_X(Vehicle.location).label("lon"),
            func.ST_Y(Vehicle.location).label("lat")
        ).where(
            func.ST_DWithin(
                cast(Vehicle.location, Geography),
                cast(point, Geography),
                search_radius
            )
        )
        result = await db.execute(stmt)
        rows = result.all()

        conflicts = []

        for row in rows:
            vehicle = row[0]
            v_lon = row[1]
            v_lat = row[2]

            # 座標が取得できない場合はスキップ
            if v_lon is None or v_lat is None:
                continue

            dist = self._haversine_distance(lat, lon, v_lat, v_lon)

            if dist > search_radius:
                continue

            # 相対速度とTTC計算
            # ベクトル計算
            # 歩行者ベクトル
            p_vx, p_vy = self._get_velocity_vector(speed, heading)
            # 車両ベクトル
            v_vx, v_vy = self._get_velocity_vector(vehicle.speed, vehicle.heading)

            # 相対速度ベクトル (車両 - 歩行者)
            rel_vx = v_vx - p_vx
            rel_vy = v_vy - p_vy

            # 相対速度の大きさ
            rel_speed = math.sqrt(rel_vx**2 + rel_vy**2)

            # 相対位置ベクトル (車両 - 歩行者)
            # 緯度経度差分をメートルに変換 (簡易計算)
            # x: 東西方向 (経度), y: 南北方向 (緯度)
            # 経度差分は緯度によって距離が変わる
            dx = (v_lon - lon) * (self.earth_radius * math.cos(math.radians(lat)) * math.pi / 180)
            dy = (v_lat - lat) * (self.earth_radius * math.pi / 180)

            # 接近判定: 位置ベクトルと相対速度ベクトルの内積
            # 位置ベクトルD = P_car - P_ped
            # 相対速度V_rel = V_car - V_ped
            # 接近しているなら、DとV_relのなす角は鈍角 (内積 < 0)
            dot_product = dx * rel_vx + dy * rel_vy

            if dot_product < 0 and rel_speed > 0.1:
                # 接近速度 (D方向への射影)
                # closing_speed = - (D . V_rel) / |D|
                closing_speed = -dot_product / dist

                if closing_speed > 0:
                    ttc = dist / closing_speed

                    if ttc < self.warning_threshold_seconds:
                        # 警告生成
                        alert_data = self.generate_warning(vehicle.vehicle_id, pedestrian_id, ttc)
                        alert_data["distance_m"] = dist
                        conflicts.append(alert_data)

                        # アラートをDBに保存
                        alert = SafetyAlert(
                            vehicle_id=vehicle.vehicle_id,
                            pedestrian_id=pedestrian_id,
                            ttc_seconds=ttc,
                            distance_m=dist,
                            created_at=datetime.now(timezone.utc)
                        )
                        db.add(alert)

        if conflicts:
            await db.commit()

        return conflicts

    def generate_warning(self, vehicle_id: str, pedestrian_id: str, ttc: float) -> Dict[str, Any]:
        """
        警告メッセージを生成する
        """
        return {
            "type": "collision_warning",
            "level": "critical" if ttc < 1.5 else "warning",
            "vehicle_id": vehicle_id,
            "pedestrian_id": pedestrian_id,
            "ttc": ttc,
            "message": f"Vehicle {vehicle_id} approaching! TTC: {ttc:.1f}s"
        }

    def predict_trajectory(self, lat: float, lon: float, speed: float, heading: float, seconds: float = 1.0) -> Tuple[float, float]:
        """
        歩行者の将来位置を予測する (線形外挿)

        Args:
            lat, lon: 現在位置
            speed: 速度 (m/s)
            heading: 進行方向 (度)
            seconds: 予測時間 (秒)

        Returns:
            (lat, lon): 予測位置
        """
        dist = speed * seconds

        # ラジアン変換
        head_rad = math.radians(heading)

        # 移動量 (m)
        dy = dist * math.cos(head_rad)
        dx = dist * math.sin(head_rad)

        # 緯度経度への変換
        # 緯度1度あたりの距離 (約111km)
        lat_diff = (dy / self.earth_radius) * (180 / math.pi)
        # 経度1度あたりの距離 (緯度によって変わる)
        lon_diff = (dx / (self.earth_radius * math.cos(math.radians(lat)))) * (180 / math.pi)

        return lat + lat_diff, lon + lon_diff

    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """2点間の距離(m)を計算"""
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        a = math.sin(delta_phi / 2)**2 + \
            math.cos(phi1) * math.cos(phi2) * \
            math.sin(delta_lambda / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return self.earth_radius * c

    def _get_velocity_vector(self, speed: float, heading: float) -> Tuple[float, float]:
        """速度と方位から速度ベクトル(vx, vy)を計算"""
        # heading: 0=North(y+), 90=East(x+)
        rad = math.radians(heading)
        # 数学的な座標系では0度はEastだが、地理座標系(Heading)では0度はNorth
        # North(y+) -> sin(0)=0, cos(0)=1 -> y成分
        # East(x+) -> sin(90)=1, cos(90)=0 -> x成分
        # つまり、vx = sin(heading), vy = cos(heading)
        vy = speed * math.cos(rad)
        vx = speed * math.sin(rad)
        return vx, vy
