import uuid
import random
import string
from datetime import datetime
from typing import List, Dict, Any, Optional
from app.database.mongodb import get_database
from app.services.memory_store import memory_store

def generate_session_code() -> str:
    letters = ''.join(random.choices(string.ascii_uppercase, k=3))
    digits = ''.join(random.choices(string.digits, k=3))
    return f"{letters}{digits}"

async def create_session(company_name: str, title: str, created_by: str, duration: int = 60, allow_prof_mic: bool = True) -> Dict[str, Any]:
    db = get_database()
    session_code = generate_session_code()
    
    session_doc = {
        "companyName": company_name.strip(),
        "title": title.strip(),
        "sessionCode": session_code,
        "status": "active",
        "createdBy": created_by,
        "speakerTimerDuration": duration,
        "allowProfMic": allow_prof_mic,
        "currentSpeakerId": None,
        "currentSpeakerName": None,
        "currentSpeakerRole": None,
        "createdAt": datetime.utcnow().isoformat(),
        "startedAt": datetime.utcnow().isoformat(),
        "endedAt": None
    }

    if db is not None:
        res = await db.sessions.insert_one(session_doc)
        session_id = str(res.inserted_id)
        session_doc["_id"] = session_id
        session_doc["id"] = session_id
    else:
        session_id = str(uuid.uuid4())
        session_doc["_id"] = session_id
        session_doc["id"] = session_id
        memory_store.sessions[session_id] = session_doc

    return session_doc

async def get_session_by_code_or_id(identifier: str) -> Optional[Dict[str, Any]]:
    db = get_database()
    if db is not None:
        from bson import ObjectId
        # Try finding by sessionCode or _id
        session = await db.sessions.find_one({"sessionCode": identifier.upper()})
        if not session:
            try:
                session = await db.sessions.find_one({"_id": ObjectId(identifier)})
            except Exception:
                session = await db.sessions.find_one({"_id": identifier})
        if session:
            session["_id"] = str(session["_id"])
            session["id"] = str(session["_id"])
            return session
        return None
    else:
        # Memory fallback
        for s in memory_store.sessions.values():
            if s["sessionCode"] == identifier.upper() or s["id"] == identifier:
                return s
        return None

async def list_active_sessions() -> List[Dict[str, Any]]:
    db = get_database()
    if db is not None:
        cursor = db.sessions.find({"status": {"$ne": "ended"}})
        sessions = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            doc["id"] = str(doc["_id"])
            sessions.append(doc)
        return sessions
    else:
        return [s for s in memory_store.sessions.values() if s.get("status") != "ended"]

async def update_session_status(session_id: str, status: str) -> Optional[Dict[str, Any]]:
    db = get_database()
    if db is not None:
        from bson import ObjectId
        try:
            target_id = ObjectId(session_id)
        except Exception:
            target_id = session_id
        
        update_data = {"status": status}
        if status == "ended":
            update_data["endedAt"] = datetime.utcnow().isoformat()
            update_data["currentSpeakerId"] = None
            update_data["currentSpeakerName"] = None
            update_data["currentSpeakerRole"] = None

        await db.sessions.update_one({"_id": target_id}, {"$set": update_data})
        return await get_session_by_code_or_id(session_id)
    else:
        s = memory_store.sessions.get(session_id)
        if s:
            s["status"] = status
            if status == "ended":
                s["endedAt"] = datetime.utcnow().isoformat()
                s["currentSpeakerId"] = None
                s["currentSpeakerName"] = None
                s["currentSpeakerRole"] = None
            return s
        return None
