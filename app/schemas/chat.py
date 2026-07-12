from typing import List, Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel
from app.schemas.common import BaseSchema
from app.schemas.user import UserSummary

class MessageBase(BaseSchema):
    content: str

class MessageCreate(MessageBase):
    pass

class ConversationCreate(BaseSchema):
    space_id: UUID

class MessageResponse(MessageBase):
    id: UUID
    conversation_id: UUID
    sender_id: UUID
    is_read: bool
    created_at: datetime
    sender: Optional[UserSummary] = None

class ConversationResponse(BaseSchema):
    id: UUID
    booking_id: Optional[UUID]
    space_id: UUID
    host_id: UUID
    guest_id: UUID
    last_message_at: datetime
    created_at: datetime
    
    # Detalhes opcionais
    space_title: Optional[str] = None
    space_image: Optional[str] = None
    last_message: Optional[str] = None
    other_user: Optional[UserSummary] = None
    unread_count: int = 0
