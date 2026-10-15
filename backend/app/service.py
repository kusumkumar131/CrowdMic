from datetime import datetime, timezone, timedelta
from fastapi import HTTPException
from bson import ObjectId
from .db import db

def now(): return datetime.now(timezone.utc)
def sid(value):
    try: return ObjectId(value)
    except Exception: raise HTTPException(404, "Session not found")

def get_session(code):
    session = db.sessions.find_one({"code": code.upper(), "status": "active"})
    if not session: raise HTTPException(404, "Active session not found")
    return session

def queue_state(session_id):
    entries = list(db.queue_entries.find({"session_id": session_id, "status": {"$in": ["pending", "approved", "speaking"]}}).sort("created_at", 1))
    return [{"id": str(e["_id"]), "user_id": e["user_id"], "name": e["name"], "status": e["status"], "position": i+1, "created_at": e["created_at"].isoformat()} for i,e in enumerate(entries)]

def serialize_session(s):
    return {"id": str(s["_id"]), "name": s["name"], "code": s["code"], "status": s["status"], "speaking_limit": s["speaking_limit"], "active_speaker": s.get("active_speaker"), "moderator_id": s["moderator_id"], "receiver_id": s.get("receiver_id"), "receiver_sid": s.get("receiver_sid")}

def end_turn(session, reason="ended"):
    active = session.get("active_speaker")
    if not active: return
    ts = now()
    db.queue_entries.update_one({"_id": ObjectId(active["entry_id"])}, {"$set": {"status": "completed", "ended_at": ts}, "$unset": {"active_key": ""}})
    db.speaking_history.insert_one({"session_id": session["_id"], "user_id": active["user_id"], "name": active["name"], "started_at": active["started_at"], "ended_at": ts, "reason": reason})
    db.sessions.update_one({"_id": session["_id"], "active_speaker.user_id": active["user_id"]}, {"$unset": {"active_speaker": ""}})
