from fastapi import FastAPI, APIRouter, WebSocket, WebSocketDisconnect
from typing import List, Dict
from src.services.crdt_service import crdt_service
from src.api.v1.comments import router as comments_router

app = FastAPI()
router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.presence_connections: Dict[str, List[WebSocket]] = {}

    async def connect_doc(self, websocket: WebSocket, doc_id: str):
        await websocket.accept()
        if doc_id not in self.active_connections:
            self.active_connections[doc_id] = []
        self.active_connections[doc_id].append(websocket)

    def disconnect_doc(self, websocket: WebSocket, doc_id: str):
        if doc_id in self.active_connections:
            self.active_connections[doc_id].remove(websocket)
            if not self.active_connections[doc_id]:
                del self.active_connections[doc_id]

    async def broadcast_doc(self, message: str, doc_id: str):
        if doc_id in self.active_connections:
            for connection in self.active_connections[doc_id]:
                await connection.send_text(message)

    async def connect_presence(self, websocket: WebSocket, doc_id: str):
        await websocket.accept()
        if doc_id not in self.presence_connections:
            self.presence_connections[doc_id] = []
        self.presence_connections[doc_id].append(websocket)

    def disconnect_presence(self, websocket: WebSocket, doc_id: str):
        if doc_id in self.presence_connections:
            self.presence_connections[doc_id].remove(websocket)
            if not self.presence_connections[doc_id]:
                del self.presence_connections[doc_id]

    async def broadcast_presence(self, message: str, doc_id: str):
         if doc_id in self.presence_connections:
            for connection in self.presence_connections[doc_id]:
                await connection.send_text(message)

manager = ConnectionManager()

@router.websocket("/ws/documents/{id}")
async def websocket_document_endpoint(websocket: WebSocket, id: str):
    await manager.connect_doc(websocket, id)
    try:
        while True:
            data = await websocket.receive_text()
            # Placeholder for OT/CRDT sync
            # In real world: ops = parse(data); merged = crdt_service.merge(ops); broadcast(merged)
            await manager.broadcast_doc(f"Sync {id}: {data}", id)
    except WebSocketDisconnect:
        manager.disconnect_doc(websocket, id)
        await manager.broadcast_doc(f"User disconnected from {id}", id)

@router.websocket("/ws/presence/{id}")
async def websocket_presence_endpoint(websocket: WebSocket, id: str):
    await manager.connect_presence(websocket, id)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast_presence(f"Presence {id}: {data}", id)
    except WebSocketDisconnect:
        manager.disconnect_presence(websocket, id)

app.include_router(router)
app.include_router(comments_router)
