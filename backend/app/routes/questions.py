import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import List, Dict, Any
from app.routes.auth import get_current_user
from app.database.mongodb import get_database
from app.services.memory_store import memory_store
from app.services.ai_service import detect_duplicates_and_prioritize
from app.services.queue_service import _resolve_session_identifiers

router = APIRouter(prefix="/sessions/{session_id}/questions", tags=["questions"])

class CreateQuestionRequest(BaseModel):
    text: str

@router.get("")
async def get_questions(session_id: str, current_user: dict = Depends(get_current_user)):
    db = get_database()
    session_ids, _ = await _resolve_session_identifiers(session_id)
    if db is not None:
        cursor = db.questions.find({"sessionId": {"$in": session_ids}}).sort("priorityScore", -1)
        questions = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            doc["id"] = str(doc["_id"])
            questions.append(doc)
        return questions
    else:
        q_list = [q for q in memory_store.questions.values() if q["sessionId"] in session_ids]
        return sorted(q_list, key=lambda x: x.get("priorityScore", 1.0), reverse=True)

@router.post("")
async def post_question(session_id: str, req: CreateQuestionRequest, current_user: dict = Depends(get_current_user)):
    db = get_database()
    session_ids, canonical_id = await _resolve_session_identifiers(session_id)
    
    # Get existing questions for similarity check
    existing_questions = []
    if db is not None:
        cursor = db.questions.find({"sessionId": {"$in": session_ids}})
        async for doc in cursor:
            existing_questions.append(doc)
    else:
        existing_questions = [q for q in memory_store.questions.values() if q["sessionId"] in session_ids]

    is_dup, sim_score, priority_score, category = detect_duplicates_and_prioritize(req.text, existing_questions)

    question_doc = {
        "sessionId": canonical_id,
        "userId": current_user.get("id"),
        "userName": current_user.get("name"),
        "text": req.text.strip(),
        "category": category,
        "status": "active",
        "isDuplicate": is_dup,
        "similarityScore": sim_score,
        "priorityScore": priority_score,
        "createdAt": datetime.utcnow().isoformat()
    }

    if db is not None:
        res = await db.questions.insert_one(question_doc)
        question_doc["_id"] = str(res.inserted_id)
        question_doc["id"] = str(res.inserted_id)
    else:
        q_id = str(uuid.uuid4())
        question_doc["_id"] = q_id
        question_doc["id"] = q_id
        memory_store.questions[q_id] = question_doc

    return question_doc

@router.post("/{question_id}/flag")
async def flag_question(session_id: str, question_id: str, current_user: dict = Depends(get_current_user)):
    if current_user.get("role") not in ["moderator", "admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")
    
    db = get_database()
    if db is not None:
        from bson import ObjectId
        try:
            qid = ObjectId(question_id)
        except Exception:
            qid = question_id
        await db.questions.update_one({"_id": qid}, {"$set": {"status": "flagged"}})
    else:
        q = memory_store.questions.get(question_id)
        if q:
            q["status"] = "flagged"

    return {"message": "Question flagged"}
