from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime

class UserRole:
    STUDENT = "student"
    PROFESSIONAL = "professional"
    MODERATOR = "moderator"
    RECEIVER = "receiver"
    ADMIN = "admin"

class UserBase(BaseModel):
    name: str
    email: str
    role: str = UserRole.STUDENT

class UserCreate(UserBase):
    password: str

class UserInDB(UserBase):
    id: str = Field(alias="_id")
    hashed_password: str
    createdAt: datetime = Field(default_factory=datetime.utcnow)

class UserResponse(UserBase):
    id: str
    createdAt: datetime

    class Config:
        from_attributes = True
