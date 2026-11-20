from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from pwdlib import PasswordHash
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from bson import ObjectId
from .config import settings
from .db import db

hashing = PasswordHash.recommended()
bearer = HTTPBearer(auto_error=False)

def public_user(user):
    return {"id": str(user["_id"]), "name": user["name"], "email": user["email"], "role": user["role"]}

def make_token(user):
    return jwt.encode({"sub": str(user["_id"]), "role": user["role"], "exp": datetime.now(timezone.utc)+timedelta(minutes=settings.jwt_expire_minutes)}, settings.jwt_secret, algorithm="HS256")

def get_current(credentials: HTTPAuthorizationCredentials = Depends(bearer)):
    if not credentials:
        raise HTTPException(401, "Sign in to continue")
    try:
        payload = jwt.decode(credentials.credentials, settings.jwt_secret, algorithms=["HS256"])
        user = db.users.find_one({"_id": ObjectId(payload["sub"])})
    except (JWTError, KeyError, Exception):
        raise HTTPException(401, "Invalid or expired session")
    if not user:
        raise HTTPException(401, "User no longer exists")
    return user

def require_role(*roles):
    def check(user=Depends(get_current)):
        if user["role"] not in roles:
            raise HTTPException(403, "This action is not allowed for your role")
        return user
    return check

def session_member(session, user):
    if user["role"] == "moderator" and session["moderator_id"] == str(user["_id"]): return
    if user["role"] == "receiver" and session.get("receiver_id") == str(user["_id"]): return
    if str(user["_id"]) in session.get("members", []): return
    raise HTTPException(403, "Join this session before accessing it")
