from uuid import UUID
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.chat import MessageCreate, MessageResponse, ConversationResponse, ConversationCreate
from app.models.user import User
from app.dependencies import get_current_user, get_current_user_ws
from app.services.chat_service import ChatService
from app.services.contact_filter import contains_contact_info
from typing import Dict, List

router = APIRouter(prefix="/chat", tags=["Chat"])

from app.websockets.chat import manager

@router.post("/conversations", response_model=ConversationResponse)
async def start_conversation(
    conv_in: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    chat_service = ChatService(db)
    conv = await chat_service.get_or_create_conversation_by_space(conv_in.space_id, current_user.id)
    
    # Reload conversation via list_conversations to get formatted UI fields
    # Alternatively, we could manually format it here, but list_conversations does it perfectly
    conversations = await chat_service.list_conversations(current_user.id, limit=100)
    for c in conversations:
        if c["id"] == conv.id:
            return c
            
    raise HTTPException(status_code=500, detail="Failed to format conversation")

@router.post("/conversations/booking/{booking_id}/messages", response_model=MessageResponse)
async def send_message_booking(
    booking_id: UUID,
    msg_in: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if contains_contact_info(msg_in.content):
        raise HTTPException(status_code=400, detail="Sua mensagem foi bloqueada pois contém informações de contato não permitidas pelas nossas políticas.")
        
    chat_service = ChatService(db)
    conv = await chat_service.get_or_create_conversation(booking_id)
    msg = await chat_service.send_message(current_user.id, conv.id, msg_in)
    
    # Notifica via WebSocket
    await manager.broadcast_to_conversation(
        {
            "type": "new_message", 
            "data": {
                "id": str(msg.id), 
                "content": msg.content, 
                "sender_id": str(msg.sender_id),
                "created_at": msg.created_at.isoformat(),
                "sender": {
                    "id": str(current_user.id),
                    "full_name": current_user.full_name,
                    "avatar_url": current_user.avatar_url
                }
            }
        },
        [conv.host_id, conv.guest_id]
    )
    return msg

@router.post("/conversations/{conversation_id}/messages", response_model=MessageResponse)
async def send_message(
    conversation_id: UUID,
    msg_in: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if contains_contact_info(msg_in.content):
        raise HTTPException(status_code=400, detail="Sua mensagem foi bloqueada pois contém informações de contato não permitidas pelas nossas políticas.")
        
    chat_service = ChatService(db)
    msg = await chat_service.send_message(current_user.id, conversation_id, msg_in)
    
    from app.models.chat import Conversation
    conv = await chat_service.db.get(Conversation, conversation_id)
    if conv:
        await manager.broadcast_to_conversation(
            {
                "type": "new_message", 
                "data": {
                    "id": str(msg.id), 
                    "content": msg.content, 
                    "sender_id": str(msg.sender_id),
                    "created_at": msg.created_at.isoformat(),
                    "sender": {
                        "id": str(current_user.id),
                        "full_name": current_user.full_name,
                        "avatar_url": current_user.avatar_url
                    }
                }
            },
            [conv.host_id, conv.guest_id]
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

from fastapi_cache.decorator import cache

@router.get("/conversations/unread-total")
@cache(expire=60)
async def get_total_unread(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    chat_service = ChatService(db)
    conversations = await chat_service.list_conversations(current_user.id, limit=100)
    total = sum(c["unread_count"] for c in conversations)
    return {"unread_total": total}

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

    await manager.connect(websocket, current_user.id)
    
    from app.models.chat import Conversation
    conv = await chat_service.db.get(Conversation, conversation_id)
    participant_ids = [conv.host_id, conv.guest_id] if conv else [current_user.id]

    try:
        import json
        while True:
            data = await websocket.receive_text()
            try:
                payload = json.loads(data)
                
                if payload.get("type") == "message":
                    content = payload.get("content")
                    if contains_contact_info(content):
                        await websocket.send_json({
                            "type": "error",
                            "message": "Sua mensagem foi bloqueada pois contém informações de contato não permitidas pelas nossas políticas."
                        })
                        continue

                    # Salva no DB
                    msg_in = MessageCreate(content=content)
                    msg = await chat_service.send_message(current_user.id, conversation_id, msg_in)
                    
                    # Broadcast
                    await manager.broadcast_to_conversation(
                        {
                            "type": "new_message", 
                            "data": {
                                "id": str(msg.id), 
                                "content": msg.content, 
                                "sender_id": str(msg.sender_id),
                                "created_at": msg.created_at.isoformat(),
                                "sender": {
                                    "id": str(current_user.id),
                                    "full_name": current_user.full_name,
                                    "avatar_url": current_user.avatar_url
                                }
                            }
                        },
                        participant_ids
                    )
                
                elif payload.get("type") == "typing":
                    await manager.broadcast_to_conversation(
                        {"type": "user_typing", "user_id": str(current_user.id)},
                        participant_ids
                    )
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        manager.disconnect(websocket, current_user.id)
