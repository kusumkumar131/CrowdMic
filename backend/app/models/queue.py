from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class QueueStatus:
    WAITING = "waiting"
    NEXT = "next"
    SPEAKING = "speaking"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REMOVED = "removed"
    SKIPPED = "skipped"

class QueueEntryBase(BaseModel):
    sessionId: str
    userId: str
    userName: str
    userRole: str = "student"

class QueueEntryInDB(QueueEntryBase):
    id: str = Field(alias="_id")
    position: int
    status: str = QueueStatus.WAITING
    joinedAt: datetime = Field(default_factory=datetime.utcnow)
    startedAt: Optional[datetime] = None
    endedAt: Optional[datetime] = None

class QueueEntryResponse(QueueEntryBase):
    id: str
    position: int
    status: str
    joinedAt: datetime
    startedAt: Optional[datetime] = None
    endedAt: Optional[datetime] = None

    class Config:
        from_attributes = True
