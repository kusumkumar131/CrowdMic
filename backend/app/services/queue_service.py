import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from app.database.mongodb import get_database
from app.services.memory_store import memory_store

async def _resolve_session_identifiers(session_id: str):
    """
    Returns (list_of_equivalent_ids, canonical_id).
    Handles both sessionCode (e.g. 'UBX549') and MongoDB ObjectId string.
    """
    from app.services.session_service import get_session_by_code_or_id
    try:
        session = await get_session_by_code_or_id(session_id)
        if session:
            canonical_id = session.get("id") or str(session.get("_id"))
            session_code = session.get("sessionCode")
            all_ids = list(set(filter(None, [session_id, canonical_id, session_code])))
            return all_ids, canonical_id
    except Exception:
        pass
    return [session_id], session_id

async def add_to_queue(session_id: str, user_id: str, user_name: str, user_role: str = "student") -> Dict[str, Any]:
    db = get_database()
    session_ids, canonical_id = await _resolve_session_identifiers(session_id)
    uid_str = str(user_id) if user_id is not None else ""
    
    if db is not None:
        # 1. If user is already active in queue, reject duplicate
        existing_active = await db.queue_entries.find_one({
            "sessionId": {"$in": session_ids},
            "userId": uid_str,
            "status": {"$in": ["waiting", "next", "speaking"]}
        })
        if existing_active:
            raise ValueError("Student is already in the queue")

        # 2. Determine new position
        waiting_count = await db.queue_entries.count_documents({
            "sessionId": {"$in": session_ids},
            "status": {"$in": ["waiting", "next"]}
        })
        position = waiting_count + 1

        # 3. Check if an inactive entry exists (completed/cancelled) to reuse it
        existing_inactive = await db.queue_entries.find_one({
            "sessionId": {"$in": session_ids},
            "userId": uid_str
        })

        if existing_inactive:
            update_data = {
                "sessionId": canonical_id,
                "userName": user_name,
                "userRole": user_role,
                "position": position,
                "status": "next" if position == 1 else "waiting",
                "joinedAt": datetime.utcnow().isoformat(),
                "startedAt": None,
                "endedAt": None
            }
            await db.queue_entries.update_one({"_id": existing_inactive["_id"]}, {"$set": update_data})
            entry = dict(existing_inactive)
            entry.update(update_data)
            entry["_id"] = str(entry["_id"])
            entry["id"] = str(entry["_id"])
            return entry
        else:
            entry = {
                "sessionId": canonical_id,
                "userId": uid_str,
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
        # Memory store fallback
        for q in memory_store.queue_entries.values():
            if q["sessionId"] in session_ids and str(q.get("userId")) == uid_str and q["status"] in ["waiting", "next", "speaking"]:
                raise ValueError("Student is already in the queue")
        
        waiting_items = [q for q in memory_store.queue_entries.values() if q["sessionId"] in session_ids and q["status"] in ["waiting", "next"]]
        position = len(waiting_items) + 1
        entry_id = str(uuid.uuid4())
        entry = {
            "_id": entry_id,
            "id": entry_id,
            "sessionId": canonical_id,
            "userId": uid_str,
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
    session_ids, _ = await _resolve_session_identifiers(session_id)

    if db is not None:
        cursor = db.queue_entries.find({
            "sessionId": {"$in": session_ids},
            "status": {"$in": ["waiting", "next", "speaking"]}
        }).sort("position", 1)
        entries = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            doc["id"] = str(doc["_id"])
            entries.append(doc)
        return entries
    else:
        entries = [q for q in memory_store.queue_entries.values() if q["sessionId"] in session_ids and q["status"] in ["waiting", "next", "speaking"]]
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
    session_ids, _ = await _resolve_session_identifiers(session_id)
    uid_str = str(user_id) if user_id is not None else ""

    if db is not None:
        entry = await db.queue_entries.find_one({
            "sessionId": {"$in": session_ids},
            "userId": uid_str,
            "status": {"$in": ["waiting", "next"]}
        })
        if entry:
            await db.queue_entries.update_one({"_id": entry["_id"]}, {"$set": {"status": "cancelled", "endedAt": datetime.utcnow().isoformat()}})
            await recalculate_queue_positions(session_id)
            return True
        return False
    else:
        for q in list(memory_store.queue_entries.values()):
            if q["sessionId"] in session_ids and str(q.get("userId")) == uid_str and q["status"] in ["waiting", "next"]:
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
    session_ids, canonical_id = await _resolve_session_identifiers(session_id)

    if db is not None:
        cursor = db.queue_entries.find({
            "sessionId": {"$in": session_ids},
            "status": {"$in": ["waiting", "next"]}
        }).sort("joinedAt", 1)
        
        idx = 1
        async for doc in cursor:
            new_status = "next" if idx == 1 else "waiting"
            await db.queue_entries.update_one(
                {"_id": doc["_id"]},
                {"$set": {"position": idx, "status": new_status, "sessionId": canonical_id}}
            )
            idx += 1
    else:
        waiting_items = [q for q in memory_store.queue_entries.values() if q["sessionId"] in session_ids and q["status"] in ["waiting", "next"]]
        sorted_items = sorted(waiting_items, key=lambda x: x.get("joinedAt", datetime.utcnow()))
        for idx, item in enumerate(sorted_items, start=1):
            item["position"] = idx
            item["status"] = "next" if idx == 1 else "waiting"
            item["sessionId"] = canonical_id
