from sqlalchemy import Column, Integer, String, Text, Enum, DateTime, Boolean, ForeignKey, func
from sqlalchemy.orm import relationship
from app.models.user import Base
import enum

class StreamStatus(str, enum.Enum):
    scheduled = "scheduled"
    live = "live"
    ended = "ended"

class Stream(Base):
    __tablename__ = "streams"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(StreamStatus), default=StreamStatus.scheduled, nullable=False)
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    stream_key = Column(String(64), unique=True, nullable=False, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_public = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    owner = relationship("User", backref="streams") 