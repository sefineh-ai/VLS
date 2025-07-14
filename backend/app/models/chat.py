from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, func, UniqueConstraint
from sqlalchemy.orm import relationship
from app.models.user import Base

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    stream_id = Column(Integer, ForeignKey("streams.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(String(1000), nullable=False)
    timestamp = Column(DateTime, server_default=func.now(), nullable=False)
    is_deleted = Column(Boolean, default=False)

    stream = relationship("Stream", backref="chat_messages")
    user = relationship("User")

class ChatBan(Base):
    __tablename__ = "chat_bans"
    id = Column(Integer, primary_key=True, index=True)
    stream_id = Column(Integer, ForeignKey("streams.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_muted = Column(Boolean, default=False)
    is_banned = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (UniqueConstraint('stream_id', 'user_id', name='_stream_user_uc'),)

    stream = relationship("Stream")
    user = relationship("User") 