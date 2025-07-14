from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from typing import Dict, List
from app.db.session import SessionLocal
from app.services.auth import get_current_user
from app.models import ChatMessage, ChatBan, Stream, User
from app.schemas.chat import ChatMessageRead
from datetime import datetime
import json

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, stream_id: int, websocket: WebSocket):
        await websocket.accept()
        if stream_id not in self.active_connections:
            self.active_connections[stream_id] = []
        self.active_connections[stream_id].append(websocket)

    def disconnect(self, stream_id: int, websocket: WebSocket):
        if stream_id in self.active_connections:
            self.active_connections[stream_id].remove(websocket)
            if not self.active_connections[stream_id]:
                del self.active_connections[stream_id]

    async def broadcast(self, stream_id: int, message: dict):
        if stream_id in self.active_connections:
            for connection in self.active_connections[stream_id]:
                await connection.send_json(message)

manager = ConnectionManager()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.websocket("/ws/streams/{stream_id}/chat")
async def websocket_chat(
    websocket: WebSocket,
    stream_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check if user is banned
    ban = db.query(ChatBan).filter(ChatBan.stream_id == stream_id, ChatBan.user_id == current_user.id).first()
    if ban and ban.is_banned:
        await websocket.close(code=4003)
        return
    await manager.connect(stream_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Check mute/ban again before accepting message
            ban = db.query(ChatBan).filter(ChatBan.stream_id == stream_id, ChatBan.user_id == current_user.id).first()
            if ban and (ban.is_banned or ban.is_muted):
                continue  # Ignore message
            # Persist message
            msg = ChatMessage(
                stream_id=stream_id,
                user_id=current_user.id,
                content=data,
                timestamp=datetime.utcnow(),
                is_deleted=False
            )
            db.add(msg)
            db.commit()
            db.refresh(msg)
            # Broadcast to all
            msg_read = ChatMessageRead.model_validate(msg)
            await manager.broadcast(stream_id, json.loads(msg_read.model_dump_json()))
    except WebSocketDisconnect:
        manager.disconnect(stream_id, websocket) 