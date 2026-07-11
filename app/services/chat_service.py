from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException
from app.models.chat import Conversation, Message
from app.models.booking import Booking
from app.models.space import Space
from app.schemas.chat import MessageCreate
from sqlalchemy import or_

class ChatService:
    def __init__(self, db: AsyncSession):
        self.db = db
        
    async def get_or_create_conversation(self, booking_id: UUID) -> Conversation:
        booking = await self.db.get(Booking, booking_id)
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found.")
            
        # Fetch the associated space to determine host
        space = await self.db.get(Space, booking.space_id)
        
        query = select(Conversation).where(Conversation.booking_id == booking_id)
        conv = (await self.db.execute(query)).scalars().first()
        
        if not conv:
            conv = Conversation(
                booking_id=booking_id,
                space_id=space.id,
                host_id=space.host_id,
                guest_id=booking.guest_id
            )
            self.db.add(conv)
            await self.db.commit()
            await self.db.refresh(conv)
            
        return conv

    async def send_message(self, sender_id: UUID, conversation_id: UUID, msg_in: MessageCreate) -> Message:
        conv = await self.db.get(Conversation, conversation_id)
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found.")
            
        if sender_id not in [conv.host_id, conv.guest_id]:
            raise HTTPException(status_code=403, detail="Unauthorized to send in this conversation.")
            
        message = Message(
            conversation_id=conversation_id,
            sender_id=sender_id,
            content=msg_in.content
        )
        self.db.add(message)
        
        from sqlalchemy.sql import func
        conv.last_message_at = func.now()
        
        await self.db.commit()
        await self.db.refresh(message)
        return message

    async def list_conversations(self, user_id: UUID, limit: int = 20, offset: int = 0) -> list[Conversation]:
        query = select(Conversation).where(
            or_(Conversation.host_id == user_id, Conversation.guest_id == user_id)
        ).order_by(Conversation.last_message_at.desc().nullslast()).limit(limit).offset(offset)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_messages(self, user_id: UUID, conversation_id: UUID, limit: int = 50, offset: int = 0) -> list[Message]:
        conv = await self.db.get(Conversation, conversation_id)
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found.")
            
        if user_id not in [conv.host_id, conv.guest_id]:
            raise HTTPException(status_code=403, detail="Unauthorized to view this conversation.")
            
        query = select(Message).where(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at.desc()).limit(limit).offset(offset)
        result = await self.db.execute(query)
        # Retorna na ordem cronológica
        return list(reversed(result.scalars().all()))

    async def mark_as_read(self, user_id: UUID, conversation_id: UUID):
        conv = await self.db.get(Conversation, conversation_id)
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found.")
            
        if user_id not in [conv.host_id, conv.guest_id]:
            raise HTTPException(status_code=403, detail="Unauthorized to access this conversation.")
            
        query = select(Message).where(
            Message.conversation_id == conversation_id,
            Message.sender_id != user_id,
            Message.is_read == False
        )
        result = await self.db.execute(query)
        messages = result.scalars().all()
        
        for msg in messages:
            msg.is_read = True
            
        await self.db.commit()
