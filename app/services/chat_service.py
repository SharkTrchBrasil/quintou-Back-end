from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException
from app.models.chat import Conversation, Message
from app.models.booking import Booking
from app.models.space import Space
from app.models.user import User
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

    async def get_or_create_conversation_by_space(self, space_id: UUID, guest_id: UUID) -> Conversation:
        space = await self.db.get(Space, space_id)
        if not space:
            raise HTTPException(status_code=404, detail="Space not found.")
            
        if space.host_id == guest_id:
            raise HTTPException(status_code=400, detail="Cannot start a conversation with yourself.")
            
        query = select(Conversation).where(
            Conversation.space_id == space_id,
            Conversation.guest_id == guest_id
        )
        conv = (await self.db.execute(query)).scalars().first()
        
        if not conv:
            conv = Conversation(
                space_id=space_id,
                host_id=space.host_id,
                guest_id=guest_id
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
        conv.last_message_preview = msg_in.content[:100]
        
        if sender_id == conv.host_id:
            conv.guest_unread_count = (conv.guest_unread_count or 0) + 1
        else:
            conv.host_unread_count = (conv.host_unread_count or 0) + 1
        
        await self.db.commit()
        await self.db.refresh(message)
        
        # Load sender details for the response
        await self.db.refresh(message, ["sender"])
        return message

    async def list_conversations(self, user_id: UUID, limit: int = 20, offset: int = 0) -> list[dict]:
        query = select(Conversation).options(
            selectinload(Conversation.space).selectinload(Space.images),
            selectinload(Conversation.host),
            selectinload(Conversation.guest)
        ).where(
            or_(Conversation.host_id == user_id, Conversation.guest_id == user_id)
        ).order_by(Conversation.last_message_at.desc().nullslast()).limit(limit).offset(offset)
        
        result = await self.db.execute(query)
        conversations = result.scalars().all()
        
        response = []
        for conv in conversations:
            is_host = conv.host_id == user_id
            other_user = conv.guest if is_host else conv.host
            unread_count = conv.host_unread_count if is_host else conv.guest_unread_count
            
            space_image = conv.space.images[0].url if conv.space.images else None
            
            response.append({
                "id": conv.id,
                "booking_id": conv.booking_id,
                "space_id": conv.space_id,
                "host_id": conv.host_id,
                "guest_id": conv.guest_id,
                "last_message_at": conv.last_message_at or conv.created_at,
                "created_at": conv.created_at,
                "space_title": conv.space.title,
                "space_image": space_image,
                "last_message": conv.last_message_preview,
                "other_user": other_user,
                "unread_count": unread_count or 0
            })
            
        return response

    async def get_messages(self, user_id: UUID, conversation_id: UUID, limit: int = 50, offset: int = 0) -> list[Message]:
        conv = await self.db.get(Conversation, conversation_id)
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found.")
            
        if user_id not in [conv.host_id, conv.guest_id]:
            raise HTTPException(status_code=403, detail="Unauthorized to view this conversation.")
            
        query = select(Message).options(
            selectinload(Message.sender)
        ).where(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at.desc()).limit(limit).offset(offset)
        result = await self.db.execute(query)
        return list(result.scalars().all())

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
            
        if user_id == conv.host_id:
            conv.host_unread_count = 0
        else:
            conv.guest_unread_count = 0
            
        await self.db.commit()
