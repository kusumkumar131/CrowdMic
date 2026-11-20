from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class QuestionCategory:
    TECHNICAL = "Technical"
    HR = "HR"
    INTERNSHIP = "Internship"
    CAREER = "Career"
    COMPANY = "Company"
    SALARY = "Salary"
    WORK_CULTURE = "Work Culture"
    GENERAL = "General"

class QuestionBase(BaseModel):
    sessionId: str
    userId: str
    userName: str
    text: str

class QuestionCreate(BaseModel):
    text: str

class QuestionInDB(QuestionBase):
    id: str = Field(alias="_id")
    category: str = QuestionCategory.GENERAL
    status: str = "active" # active, answered, flagged
    isDuplicate: bool = False
    duplicateGroupId: Optional[str] = None
    similarityScore: float = 0.0
    priorityScore: float = 1.0
    createdAt: datetime = Field(default_factory=datetime.utcnow)

class QuestionResponse(QuestionBase):
    id: str
    category: str
    status: str
    isDuplicate: bool = False
    duplicateGroupId: Optional[str] = None
    similarityScore: float = 0.0
    priorityScore: float = 1.0
    createdAt: datetime

    class Config:
        from_attributes = True
