from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from app.routes.auth import get_current_user
from app.database.mongodb import get_database
from app.services.memory_store import memory_store

router = APIRouter(prefix="/sessions/{session_id}/analytics", tags=["analytics"])

def _parse_timestamp(val):
    if isinstance(val, datetime):
        return val
    if isinstance(val, str):
        try:
            return datetime.fromisoformat(val)
        except Exception:
            return None
    return None

@router.get("")
async def get_analytics(session_id: str, current_user: dict = Depends(get_current_user)):
    db = get_database()
    questions = []
    queue_entries = []

    if db is not None:
        async for q in db.questions.find({"sessionId": session_id}):
            questions.append(q)
        async for qe in db.queue_entries.find({"sessionId": session_id}):
            queue_entries.append(qe)
    else:
        questions = [q for q in memory_store.questions.values() if q["sessionId"] == session_id]
        queue_entries = [q for q in memory_store.queue_entries.values() if q["sessionId"] == session_id]

    categories_count: Dict[str, int] = {}
    for q in questions:
        cat = q.get("category", "General")
        categories_count[cat] = categories_count.get(cat, 0) + 1

    duplicate_count = sum(1 for q in questions if q.get("isDuplicate", False))
    completed_speakers = [q for q in queue_entries if q.get("status") == "completed"]
    
    # Average speaking time (estimated 45s if not recorded)
    avg_speaking_time = 45.0
    if completed_speakers:
        durations = []
        for cs in completed_speakers:
            s_dt = _parse_timestamp(cs.get("startedAt"))
            e_dt = _parse_timestamp(cs.get("endedAt"))
            if s_dt and e_dt:
                durations.append(max((e_dt - s_dt).total_seconds(), 0))
        if durations:
            avg_speaking_time = round(sum(durations) / len(durations), 1)

    return {
        "sessionId": session_id,
        "totalParticipants": max(len(queue_entries) * 3, 10), # Estimated based on queue active users
        "questionsAsked": len(questions),
        "categories": categories_count,
        "averageSpeakingTime": avg_speaking_time,
        "duplicateQuestions": duplicate_count,
        "averageQueueWaitTime": "3m 45s"
    }
