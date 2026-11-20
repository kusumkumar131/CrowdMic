from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class SessionStatus:
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    PAUSED = "paused"
    ENDED = "ended"

class SessionBase(BaseModel):
    companyName: str
    title: str
    sessionCode: str
    speakerTimerDuration: int = 60 # Default 60 seconds
    allowProfMic: bool = True

class SessionCreate(BaseModel):
    companyName: str
    title: str
    speakerTimerDuration: int = 60
    allowProfMic: bool = True

class SessionInDB(SessionBase):
    id: str = Field(alias="_id")
    status: str = SessionStatus.ACTIVE
    createdBy: str
    currentSpeakerId: Optional[str] = None
    currentSpeakerName: Optional[str] = None
    currentSpeakerRole: Optional[str] = None
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    startedAt: Optional[datetime] = None
    endedAt: Optional[datetime] = None

class SessionResponse(SessionBase):
    id: str
    status: str
    createdBy: str
    currentSpeakerId: Optional[str] = None
    currentSpeakerName: Optional[str] = None
    currentSpeakerRole: Optional[str] = None
    createdAt: datetime
    startedAt: Optional[datetime] = None
    endedAt: Optional[datetime] = None

    class Config:
        from_attributes = True
