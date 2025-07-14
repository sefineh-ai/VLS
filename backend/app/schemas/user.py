from pydantic import BaseModel, EmailStr
from typing import Optional
from app.models.user import UserRole

class UserBase(BaseModel):
    email: EmailStr
    role: UserRole = UserRole.viewer
    is_active: bool = True
    is_superuser: bool = False

class UserCreate(UserBase):
    password: str

class UserRead(UserBase):
    id: int

    model_config = {"from_attributes": True}

class UserInDB(UserBase):
    id: int
    hashed_password: str

    model_config = {"from_attributes": True} 