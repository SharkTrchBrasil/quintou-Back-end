import uuid
from sqlalchemy import Column, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    booking_id = Column(UUID(as_uuid=True), ForeignKey("bookings.id"), nullable=True)
    space_id = Column(UUID(as_uuid=True), ForeignKey("spaces.id"), nullable=False)
    host_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    guest_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    last_message_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relacionamentos
    host = relationship("User", foreign_keys=[host_id])
    guest = relationship("User", foreign_keys=[guest_id])
    space = relationship("Space")
    booking = relationship("Booking")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")

class Message(Base):
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False)
    sender_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    content = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relacionamentos
    conversation = relationship("Conversation", back_populates="messages")
    sender = relationship("User")
