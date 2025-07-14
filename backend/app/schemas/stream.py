from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.stream import StreamStatus

class StreamBase(BaseModel):
    title: str
    description: Optional[str] = None
    is_public: bool = True

class StreamCreate(StreamBase):
    pass

class StreamUpdate(StreamBase):
    status: Optional[StreamStatus] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

class StreamRead(StreamBase):
    id: int
    status: StreamStatus
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    stream_key: str
    owner_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True} 