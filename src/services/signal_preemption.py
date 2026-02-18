import uuid
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.models.v2x_models import PreemptionRequest, EmergencyVehicle, Intersection
from src.services.v2x_message_handler import V2XMessageHandler

class SignalPreemptionService:
    """
    緊急車両優先システムサービス
    """
    def __init__(self, message_handler: V2XMessageHandler):
        self.message_handler = message_handler

    async def receive_preemption_request(
        self,
        vehicle_id: str,
        route: dict,
        eta: float,
        db: AsyncSession
    ) -> str:
        """
        優先制御要求を受け付ける。

        Args:
            vehicle_id (str): 緊急車両ID
            route (dict): 経路情報
            eta (float): 到着予定時刻 (または所要時間)
            db (AsyncSession): DBセッション

        Returns:
            str: リクエストID
        """
        # 緊急車両として登録されているか確認
        if db:
            stmt = select(EmergencyVehicle).where(EmergencyVehicle.vehicle_id == vehicle_id)
            result = await db.execute(stmt)
            vehicle = result.scalar_one_or_none()
            if not vehicle:
                # 登録されていない場合はエラーログを出力しつつ、緊急対応のため処理は継続する運用もあり得る
                # ここでは簡易的に続行
                pass

        request_id = str(uuid.uuid4())

        # リクエストを保存
        if db:
            request = PreemptionRequest(
                vehicle_id=vehicle_id,
                request_id=request_id,
                route=route,
                status="pending",
                created_at=datetime.now(timezone.utc)
            )
            db.add(request)
            await db.commit()

        # 青波制御の計算
        adjustments = self.calculate_green_wave(route, eta)

        # 交差点制御 (モック)
        await self.coordinate_intersections(adjustments)

        # 周辺車両への通知
        await self.notify_nearby_vehicles(route)

        # ステータス更新
        if db:
            # requestオブジェクトはセッションに紐付いているため再取得不要だが、
            # commit後なのでrefreshが必要な場合がある。
            # ここでは単純に再度セットしてcommit
            request.status = "granted"
            await db.commit()

        return request_id

    def calculate_green_wave(self, route: dict, eta: float) -> dict:
        """
        青波制御のための信号タイミング調整を計算する。

        Args:
            route (dict): 経路情報 (交差点IDのリストなどを想定)
            eta (float): 全体の所要時間または到着時刻

        Returns:
            dict: 各交差点の調整プラン
        """
        # route = {"waypoints": [{"lat": ..., "lon": ...}, ...], "intersection_ids": [1, 2, 3]}
        # 簡易実装: ルート上の交差点をすべて青にするプランを作成

        adjustments = {}
        intersection_ids = route.get("intersection_ids", [])

        # ETAに基づいて各交差点の通過時刻を推測するロジックが必要
        # ここでは単純に「即時青」を要求するプランとする
        for i_id in intersection_ids:
            adjustments[str(i_id)] = {
                "action": "force_green",
                "duration": 60, # 60秒間青を維持
                "priority": "emergency"
            }

        return adjustments

    async def coordinate_intersections(self, adjustments: dict):
        """
        各交差点コントローラーに指令を送る (モック)。
        """
        # 実際にはMQTTや専用プロトコルで信号機に指令を送る
        for i_id, plan in adjustments.items():
            # 本来はここで通信処理
            pass

    async def notify_nearby_vehicles(self, route: dict):
        """
        ルート周辺の車両に退避命令をブロードキャストする。
        """
        # ルートの各ポイント周辺にメッセージを送信
        # route["waypoints"] があると仮定
        waypoints = route.get("waypoints", [])

        # 重複送信を防ぐため、ある程度間引いて送信するロジックなどが本来は必要
        for wp in waypoints:
            lat = wp.get("lat")
            lon = wp.get("lon")
            if lat is not None and lon is not None:
                message = {
                    "type": "EMERGENCY_VEHICLE_APPROACHING",
                    "location": {"lat": lat, "lon": lon},
                    "action": "YIELD"
                }
                # 半径500mに通知
                await self.message_handler.broadcast_to_nearby_vehicles(message, lat, lon, radius_m=500.0)
