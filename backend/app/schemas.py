from pydantic import BaseModel, EmailStr, Field

class RegisterIn(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: str = "student"

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class SessionIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    speaking_limit: int = Field(default=60, ge=10, le=600)

class JoinIn(BaseModel):
    code: str = Field(min_length=4, max_length=12)

class SignalIn(BaseModel):
    to: str
    data: dict
