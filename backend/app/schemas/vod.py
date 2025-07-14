from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class VODBase(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    is_public: bool = True

class VODCreate(VODBase):
    stream_id: int
    file_path: str
    duration: Optional[int] = None

class VODRead(VODBase):
    id: int
    stream_id: int
    file_path: str
    created_at: datetime
    duration: Optional[int] = None

    model_config = {"from_attributes": True} 