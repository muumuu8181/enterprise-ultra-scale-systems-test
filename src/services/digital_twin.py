"""
デジタルツインサービス
都市のインフラ状態を管理・分析・可視化するサービス層
"""
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from ..models import Sensor, SensorReading, Alert, TrafficSignal, EmergencyIncident
from geoalchemy2.shape import to_shape
import shapely.geometry
import json
import numpy as np
import datetime

class DigitalTwin:
    """
    都市のデジタルツインを管理するクラス
    """
    def __init__(self, db: AsyncSession, timescale_db: AsyncSession):
        """
        初期化
        :param db: PostGISデータベースセッション (メタデータ、GIS)
        :param timescale_db: TimescaleDBセッション (時系列データ)
        """
        self.db = db
        self.timescale_db = timescale_db

    async def sync_sensor_state(self, sensor_id: int, value: float, metadata: Dict[str, Any] = None) -> SensorReading:
        """
        センサー状態をリアルタイム同期し、データベースに保存します。

        :param sensor_id: センサーID
        :param value: センサー値
        :param metadata: 追加メタデータ
        :return: 保存されたセンサー読み取り値
        """
        # センサーの存在確認と最終更新日時の更新 (PostGIS DB)
        result = await self.db.execute(select(Sensor).where(Sensor.id == sensor_id))
        sensor = result.scalar_one_or_none()

        if sensor:
            sensor.last_updated = datetime.datetime.utcnow()
            self.db.add(sensor)
            # PostGIS側コミット (必須ではないが状態同期のため)
            await self.db.commit()

        # 読み取り値の保存 (TimescaleDB hypertable)
        reading = SensorReading(
            time=datetime.datetime.utcnow(),
            sensor_id=sensor_id,
            value=value,
            metadata_=metadata
        )
        self.timescale_db.add(reading)
        await self.timescale_db.commit()
        await self.timescale_db.refresh(reading)
        return reading

    async def calculate_city_metrics(self) -> Dict[str, float]:
        """
        都市全体メトリクス計算 (平均AQI, 渋滞率, エネルギー消費)
        PostGISとTimescaleDBをまたぐため、アプリケーション側で結合ロジックを実装します。

        :return: メトリクスの辞書
        """
        metrics = {}

        # Helper function to calculate average/sum for specific sensor type
        async def get_metric(sensor_type, agg_func):
            # 1. Get sensor IDs from PostGIS DB
            sensors_res = await self.db.execute(select(Sensor.id).where(Sensor.type == sensor_type))
            sensor_ids = sensors_res.scalars().all()

            if not sensor_ids:
                return 0.0

            # 2. Calculate metric from TimescaleDB
            query = select(agg_func(SensorReading.value)).where(SensorReading.sensor_id.in_(sensor_ids))
            result = await self.timescale_db.execute(query)
            return result.scalar() or 0.0

        # 平均AQI (Air Quality Index)
        metrics['average_aqi'] = await get_metric('air_quality', func.avg)

        # 渋滞率 (trafficセンサーの平均値と仮定, 0-100%)
        metrics['congestion_rate'] = await get_metric('traffic_flow', func.avg)

        # エネルギー消費 (energyセンサーの合計値)
        metrics['total_energy_consumption'] = await get_metric('energy_consumption', func.sum)

        return metrics

    async def predict_anomaly(self) -> List[Dict[str, Any]]:
        """
        異常予測 (統計的外れ値検知: z-score > 3)
        過去のデータから統計的異常を検知します。

        :return: 異常が検知されたセンサーとその詳細のリスト
        """
        anomalies = []

        # アクティブなセンサーIDを取得 (PostGIS DB)
        sensors_result = await self.db.execute(select(Sensor.id).where(Sensor.status == 'active'))
        sensor_ids = sensors_result.scalars().all()

        for sensor_id in sensor_ids:
            # 直近100件のデータを取得 (TimescaleDB)
            query = select(SensorReading.value).where(
                SensorReading.sensor_id == sensor_id
            ).order_by(desc(SensorReading.time)).limit(100)

            result = await self.timescale_db.execute(query)
            values = result.scalars().all()

            if len(values) > 10: # 十分なデータがある場合のみ計算
                data = np.array(values)
                mean = np.mean(data)
                std = np.std(data)

                if std > 0:
                    latest_value = values[0]
                    z_score = (latest_value - mean) / std

                    if abs(z_score) > 3:
                        anomalies.append({
                            "sensor_id": sensor_id,
                            "value": latest_value,
                            "z_score": float(z_score),
                            "timestamp": datetime.datetime.utcnow().isoformat(),
                            "message": "z-score > 3: 統計的外れ値を検知しました"
                        })

        return anomalies

    async def visualize_state(self) -> Dict[str, Any]:
        """
        GeoJSON形式で現在状態出力
        都市内の全エンティティ（センサー、信号機、インシデント）の位置情報をGeoJSON FeatureCollectionとして返します。
        これはPostGIS DBの情報のみを使用します。

        :return: GeoJSON FeatureCollection
        """
        features = []

        # センサー
        sensors_result = await self.db.execute(select(Sensor))
        for sensor in sensors_result.scalars():
            point = to_shape(sensor.location)
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [point.x, point.y]
                },
                "properties": {
                    "id": sensor.id,
                    "type": "sensor",
                    "sensor_type": sensor.type,
                    "status": sensor.status,
                    "name": sensor.name
                }
            })

        # 信号機
        signals_result = await self.db.execute(select(TrafficSignal))
        for signal in signals_result.scalars():
            point = to_shape(signal.location)
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [point.x, point.y]
                },
                "properties": {
                    "id": signal.id,
                    "type": "traffic_signal",
                    "status": signal.status
                }
            })

        # 緊急インシデント
        incidents_result = await self.db.execute(select(EmergencyIncident))
        for incident in incidents_result.scalars():
            point = to_shape(incident.location)
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [point.x, point.y]
                },
                "properties": {
                    "id": incident.id,
                    "type": "emergency_incident",
                    "incident_type": incident.type,
                    "status": incident.status,
                    "reported_at": incident.reported_at.isoformat()
                }
            })

        return {
            "type": "FeatureCollection",
            "features": features
        }
