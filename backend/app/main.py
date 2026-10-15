import asyncio, secrets, string
from contextlib import asynccontextmanager
from datetime import datetime, timezone, timedelta
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pymongo import ReturnDocument
from bson import ObjectId
import socketio
from .config import settings
from .db import db, init_indexes, ping
from .schemas import RegisterIn, LoginIn, SessionIn, JoinIn
from .auth import hashing, make_token, public_user, get_current, require_role, session_member
from .service import get_session, queue_state, serialize_session, end_turn, now

sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins=settings.origins, logger=False, engineio_logger=False)
connections = {}

@asynccontextmanager
async def lifespan(app):
    try: ping(); init_indexes()
    except Exception as exc: print(f"MongoDB unavailable at startup: {exc}")
    task = asyncio.create_task(turn_watchdog())
    yield
    task.cancel()

app = FastAPI(title="CrowdMic API", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

async def broadcast(session_id):
    session = db.sessions.find_one({"_id": session_id})
    if session: await sio.emit("queue:update", {"queue": queue_state(session_id), "active_speaker": session.get("active_speaker")}, room="session:"+str(session_id))

async def turn_watchdog():
    while True:
        try:
            cutoff = now()
            for s in db.sessions.find({"status":"active", "active_speaker":{"$exists":True}}):
                active=s.get("active_speaker", {})
                if active.get("ends_at") and active["ends_at"] <= cutoff:
                    end_turn(s, "time_limit")
                    await sio.emit("speaker:revoked", {"reason":"time_limit"}, room="session:"+str(s["_id"]))
                    await broadcast(s["_id"])
        except Exception as exc: print(f"Turn watchdog error: {exc}")
        await asyncio.sleep(1)

@app.get("/api/health")
def health():
    try: ping(); return {"status":"ok","database":"connected"}
    except Exception: return JSONResponse(status_code=503, content={"status":"degraded","database":"unavailable"})

@app.post("/api/auth/register")
def register(body:RegisterIn):
    if body.role not in ("student","moderator","receiver"): raise HTTPException(400,"Invalid role")
    doc={"name":body.name.strip(),"email":body.email.lower(),"password_hash":hashing.hash(body.password),"role":body.role,"created_at":now()}
    try: result=db.users.insert_one(doc)
    except Exception: raise HTTPException(409,"An account with this email already exists")
    doc["_id"]=result.inserted_id
    return {"token":make_token(doc),"user":public_user(doc)}

@app.post("/api/auth/login")
def login(body:LoginIn):
    user=db.users.find_one({"email":body.email.lower()})
    if not user or not hashing.verify(body.password,user["password_hash"]): raise HTTPException(401,"Email or password is incorrect")
    return {"token":make_token(user),"user":public_user(user)}

@app.get("/api/auth/me")
def me(user=Depends(get_current)): return public_user(user)

@app.post("/api/sessions")
async def create_session(body:SessionIn,user=Depends(require_role("moderator"))):
    code="".join(secrets.choice(string.ascii_uppercase+string.digits) for _ in range(6))
    doc={"name":body.name,"code":code,"status":"active","speaking_limit":body.speaking_limit,"moderator_id":str(user["_id"]),"members":[],"created_at":now()}
    result=db.sessions.insert_one(doc); doc["_id"]=result.inserted_id
    return serialize_session(doc)

@app.get("/api/sessions")
def list_sessions(user=Depends(get_current)):
    query={"status":"active"}
    if user["role"]=="moderator": query["moderator_id"]=str(user["_id"])
    return [serialize_session(s) for s in db.sessions.find(query).sort("created_at",-1)]

@app.post("/api/sessions/join")
async def join_session(body:JoinIn,user=Depends(require_role("student"))):
    session=get_session(body.code)
    db.sessions.update_one({"_id":session["_id"]},{"$addToSet":{"members":str(user["_id"])}})
    await sio.emit("session:member",{"name":user["name"],"user_id":str(user["_id"]),"connected":True},room="session:"+str(session["_id"]))
    return serialize_session(session)

@app.get("/api/sessions/{code}")
def session_status(code:str,user=Depends(get_current)):
    session=get_session(code); session_member(session,user)
    return {**serialize_session(session),"queue":queue_state(session["_id"])}

@app.post("/api/sessions/{code}/queue")
async def raise_hand(code:str,user=Depends(require_role("student"))):
    session=get_session(code); session_member(session,user)
    uid=str(user["_id"])
    if session.get("active_speaker",{}).get("user_id")==uid: raise HTTPException(409,"You are currently speaking")
    recent=db.queue_entries.find_one({"session_id":session["_id"],"user_id":uid,"status":{"$in":["pending","approved","speaking"]}})
    if recent: raise HTTPException(409,"You are already in the queue")
    # Atomic uniqueness is enforced by checking immediately before insertion and the unique logical state check.
    active_count=db.queue_entries.count_documents({"session_id":session["_id"],"user_id":uid,"status":{"$in":["pending","approved","speaking"]}})
    if active_count: raise HTTPException(429,"Please wait before requesting another turn")
    try: db.queue_entries.insert_one({"session_id":session["_id"],"user_id":uid,"name":user["name"],"status":"pending","active_key":str(session["_id"])+":"+uid,"created_at":now()})
    except Exception: raise HTTPException(409,"You are already in the queue")
    await broadcast(session["_id"]); return {"queue":queue_state(session["_id"])}

@app.delete("/api/sessions/{code}/queue")
async def cancel_queue(code:str,user=Depends(require_role("student"))):
    session=get_session(code); session_member(session,user); uid=str(user["_id"])
    if session.get("active_speaker",{}).get("user_id")==uid: raise HTTPException(409,"A speaking turn must be ended by the moderator")
    db.queue_entries.update_many({"session_id":session["_id"],"user_id":uid,"status":{"$in":["pending","approved"]}},{"$set":{"status":"cancelled","ended_at":now()},"$unset":{"active_key":""}})
    await broadcast(session["_id"]); return {"queue":queue_state(session["_id"])}

async def emit_speaker(session, entry, user):
    return {"user_id":entry["user_id"],"name":entry["name"],"entry_id":str(entry["_id"]),"started_at":now(),"ends_at":now()+timedelta(seconds=session["speaking_limit"])}

@app.post("/api/sessions/{code}/approve/{entry_id}")
async def approve(code:str,entry_id:str,user=Depends(require_role("moderator"))):
    session=get_session(code)
    if session["moderator_id"]!=str(user["_id"]): raise HTTPException(403,"Only the session moderator can approve speakers")
    try: oid=ObjectId(entry_id)
    except Exception: raise HTTPException(404,"Queue entry not found")
    entry=db.queue_entries.find_one({"_id":oid,"session_id":session["_id"],"status":"pending"})
    if not entry: raise HTTPException(404,"Pending queue entry not found")
    active={"user_id":entry["user_id"],"name":entry["name"],"entry_id":str(entry["_id"]),"started_at":now(),"ends_at":now()+timedelta(seconds=session["speaking_limit"])}
    claimed=db.sessions.find_one_and_update({"_id":session["_id"],"status":"active","active_speaker":{"$exists":False}}, {"$set":{"active_speaker":active}}, return_document=ReturnDocument.AFTER)
    if not claimed: raise HTTPException(409,"Another speaker is active. End their turn first.")
    db.queue_entries.update_one({"_id":oid,"status":"pending"},{"$set":{"status":"speaking"},"$unset":{"active_key":""}})
    await sio.emit("speaker:approved",{"speaker":active,"speaking_limit":session["speaking_limit"]},room="session:"+str(session["_id"]))
    await broadcast(session["_id"]); return {"active_speaker":active}

@app.post("/api/sessions/{code}/end-turn")
async def moderator_end(code:str,user=Depends(require_role("moderator"))):
    session=get_session(code)
    if session["moderator_id"]!=str(user["_id"]): raise HTTPException(403,"Only the session moderator can end turns")
    if not session.get("active_speaker"): raise HTTPException(409,"No active speaker")
    end_turn(session)
    await sio.emit("speaker:revoked",{"reason":"moderator"},room="session:"+str(session["_id"]))
    await broadcast(session["_id"]); return {"status":"ended"}

@app.post("/api/sessions/{code}/queue/{entry_id}/skip")
async def skip(code:str,entry_id:str,user=Depends(require_role("moderator"))):
    session=get_session(code)
    if session["moderator_id"]!=str(user["_id"]): raise HTTPException(403,"Only the session moderator can skip queue entries")
    try: oid=ObjectId(entry_id)
    except Exception: raise HTTPException(404,"Queue entry not found")
    result=db.queue_entries.update_one({"_id":oid,"session_id":session["_id"],"status":"pending"},{"$set":{"status":"skipped","ended_at":now()},"$unset":{"active_key":""}})
    if not result.modified_count: raise HTTPException(404,"Pending queue entry not found")
    await broadcast(session["_id"]); return {"queue":queue_state(session["_id"])}

@app.get("/api/sessions/{code}/history")
def history(code:str,user=Depends(require_role("moderator"))):
    session=get_session(code)
    if session["moderator_id"]!=str(user["_id"]): raise HTTPException(403,"Only the session moderator can view history")
    return [{"name":h["name"],"started_at":h["started_at"].isoformat(),"ended_at":h["ended_at"].isoformat(),"reason":h["reason"]} for h in db.speaking_history.find({"session_id":session["_id"]}).sort("started_at",-1).limit(50)]

def decode_token(token):
    from jose import jwt, JWTError
    try:
        data=jwt.decode(token,settings.jwt_secret,algorithms=["HS256"]); user=db.users.find_one({"_id":ObjectId(data["sub"])}); return user
    except Exception: return None

@sio.event
async def connect(sid,environ,auth):
    token=(auth or {}).get("token") if isinstance(auth,dict) else None
    user=decode_token(token) if token else None
    if not user: return False
    connections[sid]=user
    await sio.save_session(sid,{"user_id":str(user["_id"]),"role":user["role"]})
    return True

@sio.event
async def disconnect(sid):
    user=connections.pop(sid,None)
    if user:
        for s in db.sessions.find({"members":str(user["_id"])}):
            await sio.emit("session:member",{"name":user["name"],"user_id":str(user["_id"]),"connected":False},room="session:"+str(s["_id"]))
            if (s.get("active_speaker") or {}).get("user_id")==str(user["_id"]):
                end_turn(s,"speaker_disconnected")
                await sio.emit("speaker:revoked",{"reason":"speaker_disconnected"},room="session:"+str(s["_id"]))
                await broadcast(s["_id"])
        if user["role"]=="receiver":
            for s in db.sessions.find({"receiver_sid":sid}):
                db.sessions.update_one({"_id":s["_id"],"receiver_sid":sid},{"$unset":{"receiver_sid":""}})
                await sio.emit("receiver:status",{"connected":False,"sid":sid},room="session:"+str(s["_id"]))

@sio.on("session:join")
async def socket_join(sid,data):
    user=connections.get(sid)
    if not user: return {"error":"unauthorized"}
    try:
        session=get_session((data or {}).get("code","")); session_member(session,user)
    except HTTPException as exc: return {"error":exc.detail}
    await sio.enter_room(sid,"session:"+str(session["_id"]))
    if user["role"]=="student":
        await sio.emit("session:member",{"name":user["name"],"user_id":str(user["_id"]),"connected":True},room="session:"+str(session["_id"]))
    return {"ok":True,"session":serialize_session(session),"queue":queue_state(session["_id"])}

@sio.on("webrtc:signal")
async def relay_signal(sid,data):
    sender=connections.get(sid)
    if not sender: return {"error":"unauthorized"}
    if not isinstance(data,dict): return {"error":"invalid_payload"}
    to=data.get("to"); payload=data.get("data")
    if not isinstance(to,str) or not isinstance(payload,dict): return {"error":"invalid_payload"}
    receiver=connections.get(to)
    if not receiver:
        match=next(((connected_sid, connected_user) for connected_sid, connected_user in connections.items() if str(connected_user["_id"])==to),None)
        if match: to,receiver=match
    if not receiver: return {"error":"peer_offline"}
    session=None
    sender_id=str(sender["_id"]); receiver_id=str(receiver["_id"])
    for candidate in db.sessions.find({"status":"active"}):
        active=candidate.get("active_speaker") or {}
        receiver_authorized=(receiver["role"]=="receiver" and receiver_id in [candidate.get("receiver_id"),*candidate.get("members",[])])
        if (active.get("user_id")==sender_id and receiver_authorized) or (active.get("user_id")==receiver_id and sender["role"]=="receiver" and sender_id in [candidate.get("receiver_id"),*candidate.get("members",[])]):
            session=candidate; break
    if not session: return {"error":"signaling_not_authorized"}
    await sio.emit("webrtc:signal",{"from":sid,"data":payload},to=to)
    return {"ok":True}

@sio.on("receiver:claim")
async def receiver_claim(sid,data):
    user=connections.get(sid)
    if not user or user["role"]!="receiver": return {"error":"unauthorized"}
    try: session=get_session((data or {}).get("code",""))
    except HTTPException as exc: return {"error":exc.detail}
    claimed=db.sessions.find_one_and_update({"_id":session["_id"],"$or":[{"receiver_id":{"$exists":False}},{"receiver_id":str(user["_id"])}]}, {"$set":{"receiver_id":str(user["_id"]),"receiver_sid":sid}},return_document=ReturnDocument.AFTER)
    if not claimed: return {"error":"receiver_already_claimed"}
    await sio.enter_room(sid,"session:"+str(session["_id"]))
    await sio.emit("receiver:status",{"connected":True,"sid":sid},room="session:"+str(session["_id"]))
    return {"ok":True,"session":serialize_session(claimed),"sid":sid}

@sio.on("receiver:status")
async def receiver_status(sid,data):
    user=connections.get(sid)
    if not user or user["role"]!="receiver": return {"error":"unauthorized"}
    code=(data or {}).get("code","")
    try: session=get_session(code)
    except HTTPException as exc: return {"error":exc.detail}
    if session.get("receiver_id")!=str(user["_id"]): return {"error":"receiver_not_claimed"}
    await sio.emit("receiver:status",{"connected":bool((data or {}).get("connected")),"sid":sid},room="session:"+str(session["_id"]))
    return {"ok":True}

@app.get("/api/webrtc-config")
def webrtc_config(user=Depends(get_current)):
    servers=[{"urls":settings.stun_url}]
    if settings.turn_url: servers.append({"urls":settings.turn_url,"username":settings.turn_username,"credential":settings.turn_credential})
    return {"iceServers":servers}

application=socketio.ASGIApp(sio,other_asgi_app=app)
