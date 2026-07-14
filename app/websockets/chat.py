"""
WebSocket implementation for real-time chat
"""
import logging
from typing import Dict
from uuid import UUID
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


import asyncio
import json
import redis.asyncio as redis
from app.config import settings

class ConnectionManager:
    """
    Gerencia conexões WebSocket ativas usando Redis Pub/Sub para multi-workers
    """
    def __init__(self):
        # user_id -> list of WebSocket connections (local)
        self.active_connections: Dict[str, list[WebSocket]] = {}
        self.redis_client = None
        self.pubsub = None
        self.listen_task = None
        self.channel_name = "chat:broadcast"
        
    async def connect_redis(self):
        if not self.redis_client:
            self.redis_client = redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
            self.pubsub = self.redis_client.pubsub()
            await self.pubsub.subscribe(self.channel_name)
            self.listen_task = asyncio.create_task(self._listen_redis())
            logger.info("Connected to Redis PubSub for WebSockets")

    async def _listen_redis(self):
        try:
            async for message in self.pubsub.listen():
                if message["type"] == "message":
                    data = json.loads(message["data"])
                    target_user_id = data.get("target_user_id")
                    payload = data.get("payload")
                    
                    if target_user_id and target_user_id in self.active_connections:
                        disconnected = []
                        for connection in self.active_connections[target_user_id]:
                            try:
                                await connection.send_json(payload)
                            except Exception as e:
                                logger.error(f"Error sending message to {target_user_id}: {e}")
                                disconnected.append(connection)
                        
                        # Remove conexões falhas localmente
                        for conn in disconnected:
                            if conn in self.active_connections[target_user_id]:
                                self.active_connections[target_user_id].remove(conn)
                        
                        if not self.active_connections[target_user_id]:
                            del self.active_connections[target_user_id]
        except Exception as e:
            logger.error(f"Redis pubsub error: {e}")
            # Em produção, deve haver lógica de reconexão aqui
    
    async def connect(self, websocket: WebSocket, user_id: UUID):
        """Aceita conexão e adiciona à lista local"""
        await websocket.accept()
        user_id_str = str(user_id)
        
        if user_id_str not in self.active_connections:
            self.active_connections[user_id_str] = []
        
        self.active_connections[user_id_str].append(websocket)
        logger.info(f"User {user_id} connected via WebSocket")
        
        # Conecta no Redis lazy
        await self.connect_redis()
    
    def disconnect(self, websocket: WebSocket, user_id: UUID):
        """Remove conexão da lista local"""
        user_id_str = str(user_id)
        
        if user_id_str in self.active_connections:
            if websocket in self.active_connections[user_id_str]:
                self.active_connections[user_id_str].remove(websocket)
            
            if not self.active_connections[user_id_str]:
                del self.active_connections[user_id_str]
        
        logger.info(f"User {user_id} disconnected from WebSocket")
    
    async def send_personal_message(self, message: dict, user_id: UUID):
        """Publica mensagem no Redis para que o worker correto a entregue"""
        if not self.redis_client:
            await self.connect_redis()
            
        data = {
            "target_user_id": str(user_id),
            "payload": message
        }
        await self.redis_client.publish(self.channel_name, json.dumps(data))
    
    async def broadcast_to_conversation(self, message: dict, user_ids: list[UUID]):
        """Publica mensagem para todos os participantes de uma conversa via Redis"""
        for user_id in user_ids:
            await self.send_personal_message(message, user_id)
    
    def is_user_online(self, user_id: UUID) -> bool:
        """Verifica se usuário está online *neste worker* (para fallback de push)"""
        # Nota: Em um sistema multi-worker perfeito, teríamos que checar um Redis Hash
        # map (user_id -> boolean) para saber se ele está online em *qualquer* worker.
        # Por hora, se não estiver neste, mandamos push. O push é inofensivo se ele estiver online em outro.
        return str(user_id) in self.active_connections


# Singleton instance
manager = ConnectionManager()


async def handle_chat_message(
    message_data: dict, 
    sender_id: UUID, 
    db: AsyncSession
):
    """
    Processa mensagem de chat recebida via WebSocket
    """
    from app.services.chat_service import ChatService
    from app.models.chat import Message
    from app.schemas.chat import MessageCreate
    
    conversation_id = UUID(message_data.get("conversation_id"))
    content = message_data.get("content")
    media_url = message_data.get("media_url")
    
    # Salva mensagem no banco
    chat_service = ChatService(db)
    msg_in = MessageCreate(content=content)
    message = await chat_service.send_message(
        sender_id=sender_id,
        conversation_id=conversation_id,
        msg_in=msg_in
    )
    
    # Busca conversation para pegar participantes
    from sqlalchemy import select
    from app.models.chat import Conversation
    
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    
    if conversation:
        # Busca o sender para enriquecer o payload
        sender_result = await db.execute(
            select(User).where(User.id == sender_id)
        )
        sender = sender_result.scalar_one_or_none()
        
        # Prepara payload para enviar
        message_payload = {
            "type": "new_message",
            "data": {
                "id": str(message.id),
                "conversation_id": str(conversation_id),
                "sender_id": str(sender_id),
                "content": content,
                "media_url": media_url,
                "created_at": message.created_at.isoformat(),
                "is_read": False,
                "sender": {
                    "id": str(sender.id),
                    "full_name": sender.full_name,
                    "avatar_url": sender.avatar_url
                } if sender else None
            }
        }
        
        # Envia para todos os participantes
        participant_ids = [conversation.host_id, conversation.guest_id]
        await manager.broadcast_to_conversation(message_payload, participant_ids)
        
        # Envia notificação push para quem está offline
        from app.services.notification_service import NotificationService
        from app.models.user import User
        
        notification_service = NotificationService(db)
        
        for user_id in participant_ids:
            if user_id != sender_id and not manager.is_user_online(user_id):
                if sender:
                    try:
                        await notification_service.create_notification(
                            user_id=user_id,
                            n_type="NEW_MESSAGE",
                            title=f"Nova mensagem de {sender.full_name}",
                            body=content[:100],
                            data={
                                "conversation_id": str(conversation_id),
                                "message_id": str(message.id)
                            }
                        )
                    except Exception as e:
                        logger.error(f"Error sending notification: {e}")


async def handle_typing_indicator(
    data: dict,
    sender_id: UUID,
    db: AsyncSession
):
    """
    Envia indicador de digitação
    """
    from sqlalchemy import select
    from app.models.chat import Conversation
    
    conversation_id = UUID(data.get("conversation_id"))
    is_typing = data.get("is_typing", False)
    
    # Busca conversation
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    
    if conversation:
        # Identifica o destinatário (o outro participante)
        recipient_id = (
            conversation.guest_id if conversation.host_id == sender_id 
            else conversation.host_id
        )
        
        # Envia indicador
        await manager.send_personal_message(
            {
                "type": "typing",
                "conversation_id": str(conversation_id),
                "user_id": str(sender_id),
                "is_typing": is_typing
            },
            recipient_id
        )


async def handle_message_read(
    data: dict,
    reader_id: UUID,
    db: AsyncSession
):
    """
    Marca mensagens como lidas
    """
    from sqlalchemy import update, select
    from app.models.chat import Message, Conversation
    
    conversation_id = UUID(data.get("conversation_id"))
    
    # Marca todas as mensagens da conversa como lidas
    await db.execute(
        update(Message)
        .where(
            Message.conversation_id == conversation_id,
            Message.sender_id != reader_id,
            Message.is_read == False
        )
        .values(is_read=True)
    )
    await db.commit()
    
    # Busca conversation para notificar o outro participante
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    
    if conversation:
        sender_id = (
            conversation.guest_id if conversation.host_id == reader_id 
            else conversation.host_id
        )
        
        # Notifica que mensagens foram lidas
        await manager.send_personal_message(
            {
                "type": "messages_read",
                "conversation_id": str(conversation_id),
                "read_by": str(reader_id)
            },
            sender_id
        )
