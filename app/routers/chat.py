from uuid import UUID
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.chat import MessageCreate, MessageResponse, ConversationResponse
from app.models.user import User
from app.dependencies import get_current_user, get_current_user_ws
from app.services.chat_service import ChatService
from typing import Dict, List

router = APIRouter(tags=["Chat"])

# Manager super simples em memória para WebSockets. 
# Para escalar, usar Redis Pub/Sub.
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[UUID, List[WebSocket]] = {}

    async def connect(self, conversation_id: UUID, websocket: WebSocket):
        await websocket.accept()
        if conversation_id not in self.active_connections:
            self.active_connections[conversation_id] = []
        self.active_connections[conversation_id].append(websocket)

    def disconnect(self, conversation_id: UUID, websocket: WebSocket):
        if conversation_id in self.active_connections:
            self.active_connections[conversation_id].remove(websocket)
            if not self.active_connections[conversation_id]:
                del self.active_connections[conversation_id]

    async def broadcast_to_conversation(self, conversation_id: UUID, message: dict):
        if conversation_id in self.active_connections:
            for connection in self.active_connections[conversation_id]:
                await connection.send_json(message)

manager = ConnectionManager()

@router.post("/conversations/{booking_id}/messages", response_model=MessageResponse)
async def send_message(
    booking_id: UUID,
    msg_in: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    chat_service = ChatService(db)
    conv = await chat_service.get_or_create_conversation(booking_id)
    msg = await chat_service.send_message(current_user.id, conv.id, msg_in)
    
    # Notifica via WebSocket
    await manager.broadcast_to_conversation(
        conv.id,
        {"event": "new_message", "data": {"id": str(msg.id), "content": msg.content, "sender_id": str(msg.sender_id)}}
    )
    return msg

@router.get("/conversations", response_model=List[ConversationResponse])
async def list_conversations(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    chat_service = ChatService(db)
    return await chat_service.list_conversations(current_user.id, limit=limit, offset=offset)

@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    conversation_id: UUID,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    chat_service = ChatService(db)
    return await chat_service.get_messages(current_user.id, conversation_id, limit=limit, offset=offset)

@router.put("/conversations/{conversation_id}/read", status_code=204)
async def mark_messages_read(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    chat_service = ChatService(db)
    await chat_service.mark_as_read(current_user.id, conversation_id)

@router.websocket("/ws/chat/{conversation_id}")
async def websocket_chat(
    websocket: WebSocket, 
    conversation_id: UUID,
    current_user: User = Depends(get_current_user_ws),
    db: AsyncSession = Depends(get_db)
):
    chat_service = ChatService(db)
    
    # Valida se o usuário tem acesso à conversa
    try:
        await chat_service.get_messages(current_user.id, conversation_id, limit=1)
    except Exception:
        await websocket.close(code=1008)
        return

    await manager.connect(conversation_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Loop mantido aberto, aqui pode receber msgs enviadas via ws
    except WebSocketDisconnect:
        manager.disconnect(conversation_id, websocket)
