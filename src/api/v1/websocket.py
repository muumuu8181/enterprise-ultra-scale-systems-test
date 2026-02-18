from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, List, Set
import asyncio
import json

router = APIRouter()

class ConnectionManager:
    """
    WebSocket接続管理クラス
    車両IDベースのグループ管理などを担当
    """
    def __init__(self):
        # 車両IDごとの接続管理
        self.vehicle_connections: Dict[str, WebSocket] = {}
        # ブロードキャスト用サブスクライバー
        self.broadcast_subscribers: Set[WebSocket] = set()
        # DENMアラート用サブスクライバー
        self.alert_subscribers: Set[WebSocket] = set()
        # 交差点ごとのSPATサブスクライバー
        self.spat_subscribers: Dict[str, Set[WebSocket]] = {}

    async def connect_vehicle(self, websocket: WebSocket, vehicle_id: str):
        """車両として接続"""
        await websocket.accept()
        self.vehicle_connections[vehicle_id] = websocket

    async def disconnect_vehicle(self, vehicle_id: str):
        if vehicle_id in self.vehicle_connections:
            del self.vehicle_connections[vehicle_id]

    async def connect_broadcast(self, websocket: WebSocket):
        """ブロードキャストチャネルに接続"""
        await websocket.accept()
        self.broadcast_subscribers.add(websocket)

    async def disconnect_broadcast(self, websocket: WebSocket):
        self.broadcast_subscribers.remove(websocket)

    async def connect_alert(self, websocket: WebSocket):
        """危険情報アラートチャネルに接続"""
        await websocket.accept()
        self.alert_subscribers.add(websocket)

    async def disconnect_alert(self, websocket: WebSocket):
        self.alert_subscribers.remove(websocket)

    async def connect_spat(self, websocket: WebSocket, intersection_id: str):
        """特定の交差点の信号情報ストリームに接続"""
        await websocket.accept()
        if intersection_id not in self.spat_subscribers:
            self.spat_subscribers[intersection_id] = set()
        self.spat_subscribers[intersection_id].add(websocket)

    async def disconnect_spat(self, websocket: WebSocket, intersection_id: str):
        if intersection_id in self.spat_subscribers:
            self.spat_subscribers[intersection_id].discard(websocket)

    async def broadcast_message(self, message: str, sender_socket: WebSocket = None):
        """全接続者にメッセージを配信 (送信者を除く)"""
        for connection in self.broadcast_subscribers:
            if connection == sender_socket:
                continue
            try:
                await connection.send_text(message)
            except:
                pass # 切断時のエラーハンドリングは簡易化

    async def send_alert(self, message: str):
        """アラート配信"""
        for connection in self.alert_subscribers:
            try:
                await connection.send_text(message)
            except:
                pass

    async def send_spat_update(self, intersection_id: str, message: str):
        """信号情報の配信"""
        if intersection_id in self.spat_subscribers:
            for connection in self.spat_subscribers[intersection_id]:
                try:
                    await connection.send_text(message)
                except:
                    pass

manager = ConnectionManager()

@router.websocket("/ws/v2x/broadcast")
async def websocket_broadcast(websocket: WebSocket):
    """
    車両からのCAMメッセージ受信・ブロードキャスト用エンドポイント
    """
    await manager.connect_broadcast(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # 受信したデータを他の全ブロードキャスト購読者に配信
            await manager.broadcast_message(data, sender_socket=websocket)
    except WebSocketDisconnect:
        await manager.disconnect_broadcast(websocket)

@router.websocket("/ws/v2x/denm-alerts")
async def websocket_denm_alerts(websocket: WebSocket):
    """
    DENM危険情報のリアルタイム配信
    サーバー側からPush通知を行うため、クライアントからの送信は基本無視するが、
    Keep-Alive等は受け付ける
    """
    await manager.connect_alert(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect_alert(websocket)

@router.websocket("/ws/v2x/spat/{intersection_id}")
async def websocket_spat(websocket: WebSocket, intersection_id: str):
    """
    信号情報ストリーム (SPAT)
    指定された交差点IDの信号情報を購読する
    """
    await manager.connect_spat(websocket, intersection_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect_spat(websocket, intersection_id)
