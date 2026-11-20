import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from app.database.mongodb import get_database
from app.services.memory_store import memory_store

async def add_to_queue(session_id: str, user_id: str, user_name: str, user_role: str = "student") -> Dict[str, Any]:
    db = get_database()
    
    if db is not None:
        # Check duplicate waiting/speaking entry
        existing = await db.queue_entries.find_one({
            "sessionId": session_id,
            "userId": user_id,
            "status": {"$in": ["waiting", "next", "speaking"]}
        })
        if existing:
            raise ValueError("Student is already in the queue")

        # Get count to determine position
        waiting_count = await db.queue_entries.count_documents({
            "sessionId": session_id,
            "status": {"$in": ["waiting", "next"]}
        })
        position = waiting_count + 1

        entry = {
            "sessionId": session_id,
            "userId": user_id,
            "userName": user_name,
            "userRole": user_role,
            "position": position,
            "status": "next" if position == 1 else "waiting",
            "joinedAt": datetime.utcnow().isoformat(),
            "startedAt": None,
            "endedAt": None
        }
        res = await db.queue_entries.insert_one(entry)
        entry["_id"] = str(res.inserted_id)
        entry["id"] = str(res.inserted_id)
        return entry
    else:
        # Memory store
        for q in memory_store.queue_entries.values():
            if q["sessionId"] == session_id and q["userId"] == user_id and q["status"] in ["waiting", "next", "speaking"]:
                raise ValueError("Student is already in the queue")
        
        waiting_items = [q for q in memory_store.queue_entries.values() if q["sessionId"] == session_id and q["status"] in ["waiting", "next"]]
        position = len(waiting_items) + 1
        entry_id = str(uuid.uuid4())
        entry = {
            "_id": entry_id,
            "id": entry_id,
            "sessionId": session_id,
            "userId": user_id,
            "userName": user_name,
            "userRole": user_role,
            "position": position,
            "status": "next" if position == 1 else "waiting",
            "joinedAt": datetime.utcnow().isoformat(),
            "startedAt": None,
            "endedAt": None
        }
        memory_store.queue_entries[entry_id] = entry
        return entry

async def get_session_queue(session_id: str) -> List[Dict[str, Any]]:
    db = get_database()
    if db is not None:
        cursor = db.queue_entries.find({
            "sessionId": session_id,
            "status": {"$in": ["waiting", "next", "speaking"]}
        }).sort("position", 1)
        entries = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            doc["id"] = str(doc["_id"])
            entries.append(doc)
        return entries
    else:
        entries = [q for q in memory_store.queue_entries.values() if q["sessionId"] == session_id and q["status"] in ["waiting", "next", "speaking"]]
        return sorted(entries, key=lambda x: x["position"])

async def update_queue_entry_status(session_id: str, entry_id: str, new_status: str) -> Optional[Dict[str, Any]]:
    db = get_database()
    if db is not None:
        from bson import ObjectId
        try:
            target_id = ObjectId(entry_id)
        except Exception:
            target_id = entry_id

        update_fields = {"status": new_status}
        if new_status == "speaking":
            update_fields["startedAt"] = datetime.utcnow().isoformat()
        elif new_status in ["completed", "cancelled", "removed", "skipped"]:
            update_fields["endedAt"] = datetime.utcnow().isoformat()

        await db.queue_entries.update_one({"_id": target_id}, {"$set": update_fields})
        await recalculate_queue_positions(session_id)
        entry = await db.queue_entries.find_one({"_id": target_id})
        if entry:
            entry["_id"] = str(entry["_id"])
            entry["id"] = str(entry["_id"])
        return entry
    else:
        entry = memory_store.queue_entries.get(entry_id)
        if entry:
            entry["status"] = new_status
            if new_status == "speaking":
                entry["startedAt"] = datetime.utcnow().isoformat()
            elif new_status in ["completed", "cancelled", "removed", "skipped"]:
                entry["endedAt"] = datetime.utcnow().isoformat()
            await recalculate_queue_positions(session_id)
            return entry
        return None

async def cancel_user_hand(session_id: str, user_id: str) -> bool:
    db = get_database()
    if db is not None:
        entry = await db.queue_entries.find_one({
            "sessionId": session_id,
            "userId": user_id,
            "status": {"$in": ["waiting", "next"]}
        })
        if entry:
            await db.queue_entries.update_one({"_id": entry["_id"]}, {"$set": {"status": "cancelled", "endedAt": datetime.utcnow().isoformat()}})
            await recalculate_queue_positions(session_id)
            return True
        return False
    else:
        for q in list(memory_store.queue_entries.values()):
            if q["sessionId"] == session_id and q["userId"] == user_id and q["status"] in ["waiting", "next"]:
                q["status"] = "cancelled"
                q["endedAt"] = datetime.utcnow().isoformat()
                await recalculate_queue_positions(session_id)
                return True
        return False

async def recalculate_queue_positions(session_id: str):
    """
    Reorders active waiting and next students 1..N.
    Sets position #1 status to 'next' if status was 'waiting'.
    """
    db = get_database()
    if db is not None:
        cursor = db.queue_entries.find({
            "sessionId": session_id,
            "status": {"$in": ["waiting", "next"]}
        }).sort("joinedAt", 1)
        
        idx = 1
        async for doc in cursor:
            new_status = "next" if idx == 1 else "waiting"
            await db.queue_entries.update_one(
                {"_id": doc["_id"]},
                {"$set": {"position": idx, "status": new_status}}
            )
            idx += 1
    else:
        waiting_items = [q for q in memory_store.queue_entries.values() if q["sessionId"] == session_id and q["status"] in ["waiting", "next"]]
        sorted_items = sorted(waiting_items, key=lambda x: x.get("joinedAt", datetime.utcnow()))
        for idx, item in enumerate(sorted_items, start=1):
            item["position"] = idx
            item["status"] = "next" if idx == 1 else "waiting"
