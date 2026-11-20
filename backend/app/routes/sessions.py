from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import Optional, List
from app.routes.auth import get_current_user
from app.services.session_service import (
    create_session, get_session_by_code_or_id, list_active_sessions, update_session_status
)

router = APIRouter(prefix="/sessions", tags=["sessions"])

class CreateSessionRequest(BaseModel):
    companyName: str
    title: str
    speakerTimerDuration: int = 60
    allowProfMic: bool = True

class StatusUpdateRequest(BaseModel):
    status: str # active, paused, ended

@router.post("")
async def create_new_session(req: CreateSessionRequest, current_user: dict = Depends(get_current_user)):
    if current_user.get("role") not in ["moderator", "admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only moderators or admins can create sessions")
    
    session = await create_session(
        company_name=req.companyName,
        title=req.title,
        created_by=current_user.get("id"),
        duration=req.speakerTimerDuration,
        allow_prof_mic=req.allowProfMic
    )
    return session

@router.get("")
async def get_all_sessions(current_user: dict = Depends(get_current_user)):
    sessions = await list_active_sessions()
    return sessions

@router.get("/{identifier}")
async def get_session(identifier: str, current_user: dict = Depends(get_current_user)):
    session = await get_session_by_code_or_id(identifier)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return session

@router.patch("/{session_id}/status")
async def update_status(session_id: str, req: StatusUpdateRequest, current_user: dict = Depends(get_current_user)):
    if current_user.get("role") not in ["moderator", "admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")
    
    session = await update_session_status(session_id, req.status)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return session
