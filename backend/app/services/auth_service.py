import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from app.database.mongodb import get_database
from app.services.memory_store import memory_store
from app.utils.security import get_password_hash, verify_password, create_access_token

async def register_user(name: str, email: str, password: str, role: str) -> Dict[str, Any]:
    db = get_database()
    email_lower = email.strip().lower()
    
    if db is not None:
        existing = await db.users.find_one({"email": email_lower})
        if existing:
            raise ValueError("Email already registered")
        
        user_doc = {
            "name": name.strip(),
            "email": email_lower,
            "role": role,
            "hashed_password": get_password_hash(password),
            "createdAt": datetime.utcnow().isoformat()
        }
        res = await db.users.insert_one(user_doc)
        user_id = str(res.inserted_id)
        user_doc["_id"] = user_id
        user_doc["id"] = user_id
    else:
        # Memory fallback
        for u in memory_store.users.values():
            if u["email"] == email_lower:
                raise ValueError("Email already registered")
        
        user_id = str(uuid.uuid4())
        user_doc = {
            "_id": user_id,
            "id": user_id,
            "name": name.strip(),
            "email": email_lower,
            "role": role,
            "hashed_password": get_password_hash(password),
            "createdAt": datetime.utcnow().isoformat()
        }
        memory_store.users[user_id] = user_doc

    token = create_access_token({"sub": user_id, "role": role, "name": name, "email": email_lower})
    res_user = dict(user_doc)
    res_user["_id"] = str(res_user["_id"])
    res_user["id"] = str(res_user["_id"])
    res_user.pop("hashed_password", None)
    return {"user": res_user, "token": token}

async def login_user(email: str, password: str) -> Dict[str, Any]:
    db = get_database()
    email_lower = email.strip().lower()
    user_doc = None

    if db is not None:
        user_doc = await db.users.find_one({"email": email_lower})
    else:
        for u in memory_store.users.values():
            if u["email"] == email_lower:
                user_doc = u
                break
    
    # Auto-seed demo accounts if demo email is requested and not found
    if not user_doc and email_lower in [
        "student@crowdmic.com", "moderator@crowdmic.com", "receiver@crowdmic.com", "pro@crowdmic.com"
    ]:
        role_map = {
            "student@crowdmic.com": ("Sample Student", "student"),
            "moderator@crowdmic.com": ("Event Moderator", "moderator"),
            "receiver@crowdmic.com": ("Auditorium Receiver", "receiver"),
            "pro@crowdmic.com": ("Company Professional", "professional"),
        }
        name, role = role_map[email_lower]
        reg_res = await register_user(name, email_lower, password, role)
        return reg_res

    if not user_doc or not verify_password(password, user_doc["hashed_password"]):
        raise ValueError("Invalid email or password")
    
    user_id = str(user_doc.get("_id", user_doc.get("id")))
    token = create_access_token({"sub": user_id, "role": user_doc["role"], "name": user_doc["name"], "email": email_lower})
    
    res_user = dict(user_doc)
    res_user["_id"] = str(res_user["_id"])
    res_user["id"] = str(res_user["_id"])
    res_user.pop("hashed_password", None)
    return {"user": res_user, "token": token}

async def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    db = get_database()
    if db is not None:
        from bson import ObjectId
        try:
            user_doc = await db.users.find_one({"_id": ObjectId(user_id)})
        except Exception:
            user_doc = await db.users.find_one({"_id": user_id})
        if user_doc:
            user_doc["_id"] = str(user_doc["_id"])
            user_doc["id"] = str(user_doc["_id"])
            user_doc.pop("hashed_password", None)
            return user_doc
        return None
    else:
        user_doc = memory_store.users.get(user_id)
        if user_doc:
            res = dict(user_doc)
            res.pop("hashed_password", None)
            return res
        return None

async def seed_demo_users():
    db = get_database()
    demo_accounts = [
        ("Event Moderator", "moderator@crowdmic.com", "password123", "moderator"),
        ("Auditorium Receiver", "receiver@crowdmic.com", "password123", "receiver"),
        ("Sample Student", "student@crowdmic.com", "password123", "student"),
        ("Company Professional", "pro@crowdmic.com", "password123", "professional"),
    ]
    for name, email, pwd, role in demo_accounts:
        email_lower = email.lower()
        hashed = get_password_hash(pwd)
        if db is not None:
            await db.users.update_one(
                {"email": email_lower},
                {"$set": {
                    "name": name,
                    "email": email_lower,
                    "role": role,
                    "hashed_password": hashed,
                    "createdAt": datetime.utcnow().isoformat()
                }},
                upsert=True
            )
        else:
            found = False
            for u in memory_store.users.values():
                if u["email"] == email_lower:
                    u["hashed_password"] = hashed
                    found = True
                    break
            if not found:
                user_id = str(uuid.uuid4())
                memory_store.users[user_id] = {
                    "_id": user_id,
                    "id": user_id,
                    "name": name,
                    "email": email_lower,
                    "role": role,
                    "hashed_password": hashed,
                    "createdAt": datetime.utcnow().isoformat()
                }
