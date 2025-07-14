from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, func
from sqlalchemy.orm import relationship
from app.models.user import Base

class VOD(Base):
    __tablename__ = "vods"

    id = Column(Integer, primary_key=True, index=True)
    stream_id = Column(Integer, ForeignKey("streams.id"), nullable=False)
    file_path = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    duration = Column(Integer, nullable=True)  # seconds
    title = Column(String(255), nullable=True)
    description = Column(String, nullable=True)
    is_public = Column(Boolean, default=True)

    stream = relationship("Stream", backref="vods") 