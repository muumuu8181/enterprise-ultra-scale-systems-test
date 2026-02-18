import json
import math
from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from src.services.pki_manager import PKIManager

class V2XMessageHandler:
    """
    V2Xメッセージハンドラー
    CAM/DENMのデコード、署名検証、ブロードキャスト制御を行う。
    """

    def __init__(self, pki_manager: PKIManager):
        self.pki_manager = pki_manager

    def decode_cam(self, raw_data: bytes) -> dict:
        """
        ETSI ITS CAMメッセージをデコードする (簡易実装)。
        本来はASN.1 UPERデコードを行うが、ここではJSONまたは簡易バイナリとして扱う。

        Args:
            raw_data (bytes): 受信した生データ

        Returns:
            dict: デコードされたデータ
        """
        try:
            # テスト用にJSON文字列としてデコードを試みる
            decoded_str = raw_data.decode('utf-8')
            data = json.loads(decoded_str)
            return data
        except Exception:
            # バイナリの場合はモックデータを返す (本来はここでasn1tools等を使用)
            # print("Failed to decode JSON, assuming binary format")
            return {
                "station_id": 12345,
                "station_type": 5, # passengerCar
                "latitude": 35.6895,
                "longitude": 139.6917,
                "speed": 10.5,
                "heading": 90.0
            }

    def decode_denm(self, raw_data: bytes) -> dict:
        """
        ETSI ITS DENMメッセージをデコードする (簡易実装)。

        Args:
            raw_data (bytes): 受信した生データ

        Returns:
            dict: デコードされたデータ
        """
        try:
            decoded_str = raw_data.decode('utf-8')
            data = json.loads(decoded_str)
            return data
        except Exception:
            return {
                "origin_station_id": 999,
                "cause_code": 1, # Traffic Jam
                "sub_cause_code": 0,
                "latitude": 35.6900,
                "longitude": 139.7000,
                "validity_duration": 600
            }

    def validate_message_signature(self, message: bytes, signature: bytes, cert_pem: bytes) -> bool:
        """
        メッセージのPKI署名を検証する。

        Args:
            message (bytes): メッセージ本体
            signature (bytes): 署名
            cert_pem (bytes): 証明書

        Returns:
            bool: 検証成功ならTrue
        """
        return self.pki_manager.verify_certificate(cert_pem, signature, message)

    async def broadcast_to_nearby_vehicles(
        self,
        message: dict,
        sender_lat: float,
        sender_lon: float,
        radius_m: float = 500.0
    ):
        """
        周辺車両へのブロードキャストを行う (WebSocket等を想定)。
        ここではログ出力と、対象範囲の計算ロジックのみ実装。

        Args:
            message (dict): 送信メッセージ
            sender_lat (float): 送信元緯度
            sender_lon (float): 送信元経度
            radius_m (float): 半径 (m)
        """
        # 本来はRedis GeoやPostGISで周辺ユーザーを検索し、WebSocketでPushする
        # print(f"Broadcasting message {message} to vehicles within {radius_m}m of ({sender_lat}, {sender_lon})")
        pass

    def filter_by_relevance(
        self,
        message_lat: float,
        message_lon: float,
        vehicle_lat: float,
        vehicle_lon: float,
        max_distance: float = 1000.0
    ) -> bool:
        """
        メッセージの関連性フィルタリング (距離ベース)。

        Args:
            message_lat (float): メッセージ発生位置緯度
            message_lon (float): メッセージ発生位置経度
            vehicle_lat (float): 車両緯度
            vehicle_lon (float): 車両経度
            max_distance (float): 最大有効距離 (m)

        Returns:
            bool: 関連性があればTrue
        """
        dist = self._haversine_distance(message_lat, message_lon, vehicle_lat, vehicle_lon)
        return dist <= max_distance

    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        2点間の距離を計算 (Haversine formula)。

        Returns:
            float: 距離 (m)
        """
        R = 6371000  # 地球の半径 (m)
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        a = math.sin(delta_phi / 2)**2 + \
            math.cos(phi1) * math.cos(phi2) * \
            math.sin(delta_lambda / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c
