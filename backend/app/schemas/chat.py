from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ChatMessageBase(BaseModel):
    content: str

class ChatMessageCreate(ChatMessageBase):
    pass

class ChatMessageRead(ChatMessageBase):
    id: int
    stream_id: int
    user_id: int
    timestamp: datetime
    is_deleted: bool

    model_config = {"from_attributes": True}

class ChatBanBase(BaseModel):
    is_muted: bool = False
    is_banned: bool = False

class ChatBanCreate(ChatBanBase):
    stream_id: int
    user_id: int

class ChatBanRead(ChatBanBase):
    id: int
    stream_id: int
    user_id: int
    created_at: datetime

    model_config = {"from_attributes": True} 