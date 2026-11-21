import logging
from app.websocket.socket_manager import sio, active_sockets, active_speakers, get_active_speaker, set_active_speaker
from app.services.session_service import get_session_by_code_or_id
from app.services.queue_service import (
    add_to_queue, get_session_queue, update_queue_entry_status, cancel_user_hand, recalculate_queue_positions
)

logger = logging.getLogger("crowdmic.events")

@sio.event
async def connect(sid, environ):
    logger.info(f"Socket connected: {sid}")

@sio.event
async def disconnect(sid):
    info = active_sockets.pop(sid, None)
    if info:
        session_id = info.get("sessionId")
        user_id = info.get("userId")
        logger.info(f"Socket disconnected: {sid} (user: {user_id})")
        if session_id:
            await broadcast_queue_update(session_id)

@sio.event
async def join_session(sid, data):
    """
    Data: { sessionCode, userId, name, role }
    """
    session_code = data.get("sessionCode", "").upper()
    user_id = data.get("userId")
    name = data.get("name", "Guest")
    role = data.get("role", "student")

    session = await get_session_by_code_or_id(session_code)
    if not session:
        await sio.emit("error", {"message": "Invalid session code"}, to=sid)
        return

    session_id = session["id"]
    room_name = f"session_{session_id}"
    await sio.enter_room(sid, room_name)

    active_sockets[sid] = {
        "userId": user_id,
        "name": name,
        "role": role,
        "sessionCode": session_code,
        "sessionId": session_id
    }

    queue = await get_session_queue(session_id)

    # Emit joined confirmation to client with current queue
    await sio.emit("joined_session", {
        "sessionId": session_id,
        "session": session,
        "queue": queue,
        "activeSpeaker": get_active_speaker(session_id)
    }, to=sid)

    # Emit updated queue state
    await broadcast_queue_update(session_id)

@sio.event
async def leave_session(sid, data):
    info = active_sockets.get(sid)
    if info:
        session_id = info.get("sessionId")
        await sio.leave_room(sid, f"session_{session_id}")
        active_sockets.pop(sid, None)
        if session_id:
            await broadcast_queue_update(session_id)

@sio.event
async def raise_hand(sid, data):
    info = active_sockets.get(sid)
    if not info:
        return
    session_id = info["sessionId"]
    user_id = info["userId"]
    name = info["name"]
    role = info["role"]

    try:
        entry = await add_to_queue(session_id, user_id, name, role)
        await sio.emit("notification", {"type": "info", "message": f"Your hand has been raised. Position #{entry['position']}"}, to=sid)
    except ValueError as e:
        await sio.emit("notification", {"type": "warning", "message": str(e)}, to=sid)
    
    await broadcast_queue_update(session_id)

@sio.event
async def cancel_hand(sid, data):
    info = active_sockets.get(sid)
    if not info:
        return
    session_id = info["sessionId"]
    user_id = info["userId"]

    await cancel_user_hand(session_id, user_id)
    await sio.emit("notification", {"type": "info", "message": "Hand request cancelled"}, to=sid)
    await broadcast_queue_update(session_id)

@sio.event
async def allow_speaker(sid, data):
    """
    Moderator action: { entryId, userId, userName }
    """
    info = active_sockets.get(sid)
    if not info or info.get("role") not in ["moderator", "admin"]:
        await sio.emit("error", {"message": "Permission denied"}, to=sid)
        return

    session_id = info["sessionId"]
    session_code = info.get("sessionCode")
    target_entry_id = data.get("entryId")
    target_user_id = data.get("userId")
    target_user_name = data.get("userName")

    # Update current speaker state
    await update_queue_entry_status(session_id, target_entry_id, "speaking")
    speaker_info = {
        "userId": target_user_id,
        "name": target_user_name,
        "role": "student",
        "startedAt": str(data.get("startedAt", ""))
    }
    set_active_speaker(session_id, speaker_info, session_code)

    # Notify session room
    room = f"session_{session_id}"
    await sio.emit("speaker_allowed", {
        "sessionId": session_id,
        "speaker": speaker_info
    }, room=room)

    # Send direct permission to student socket
    for s_id, s_info in active_sockets.items():
        if s_info.get("sessionId") == session_id and s_info.get("userId") == target_user_id:
            await sio.emit("notification", {"type": "success", "message": "You are now live! Your microphone is authorized."}, to=s_id)
            await sio.emit("mic_permission_granted", {"sessionId": session_id}, to=s_id)

    await broadcast_queue_update(session_id)

@sio.event
async def end_speaker(sid, data):
    """
    Moderator or Speaker action to end current turn.
    """
    info = active_sockets.get(sid)
    if not info:
        return

    session_id = info["sessionId"]
    session_code = info.get("sessionCode")
    current_speaker = get_active_speaker(session_id) or (session_code and get_active_speaker(session_code))
    
    set_active_speaker(session_id, None, session_code)

    # Find speaking entry and mark completed
    queue = await get_session_queue(session_id)
    for entry in queue:
        if entry["status"] == "speaking":
            await update_queue_entry_status(session_id, entry["id"], "completed")

    await recalculate_queue_positions(session_id)

    room = f"session_{session_id}"
    await sio.emit("speaker_ended", {"sessionId": session_id}, room=room)
    await broadcast_queue_update(session_id)

@sio.event
async def mute_speaker(sid, data):
    info = active_sockets.get(sid)
    if not info or info.get("role") not in ["moderator", "admin"]:
        return
    session_id = info["sessionId"]
    room = f"session_{session_id}"
    await sio.emit("speaker_muted", {"sessionId": session_id}, room=room)

@sio.event
async def allow_professional_mic(sid, data):
    """
    Moderator action to grant professional mic access.
    """
    info = active_sockets.get(sid)
    if not info or info.get("role") not in ["moderator", "admin"]:
        return
    session_id = info["sessionId"]
    session_code = info.get("sessionCode")
    target_user_id = data.get("userId")
    target_user_name = data.get("userName")

    speaker_info = {
        "userId": target_user_id,
        "name": target_user_name,
        "role": "professional"
    }
    set_active_speaker(session_id, speaker_info, session_code)

    room = f"session_{session_id}"
    await sio.emit("speaker_allowed", {
        "sessionId": session_id,
        "speaker": speaker_info
    }, room=room)

# WebRTC Signaling Handlers with Server-Side Authorization Check
@sio.event
async def webrtc_offer(sid, data):
    """
    Data: { sdp, targetRole, sessionId }
    Sender must be authorized active speaker!
    """
    info = active_sockets.get(sid)
    if not info:
        logger.warning(f"webrtc_offer: sid {sid} not found in active_sockets")
        return
    session_id = info["sessionId"]
    session_code = info.get("sessionCode")
    user_id = info["userId"]
    user_role = info["role"]

    current_speaker = get_active_speaker(session_id) or (session_code and get_active_speaker(session_code))
    if not current_speaker and user_role != "professional":
        logger.warning(f"Unauthorized WebRTC offer attempt by {user_id}")
        return

    logger.info(f"Forwarding WebRTC offer from {info.get('name')} (role {user_role}) for session {session_id}")
    receivers_found = 0
    # Forward offer to receiver/admin/moderator sockets in the session
    for s_id, s_info in active_sockets.items():
        is_same_session = (
            s_info.get("sessionId") == session_id or
            (session_code and s_info.get("sessionCode") == session_code)
        )
        if is_same_session and s_info.get("role") in ["receiver", "admin", "moderator"]:
            await sio.emit("webrtc_offer", {
                "sdp": data.get("sdp"),
                "senderUserId": user_id,
                "senderName": info.get("name"),
                "senderRole": user_role
            }, to=s_id)
            receivers_found += 1
    logger.info(f"WebRTC offer forwarded to {receivers_found} receiver(s)")

@sio.event
async def webrtc_answer(sid, data):
    """
    Receiver sends answer back to active speaker.
    Data: { sdp, targetUserId, sessionId }
    """
    info = active_sockets.get(sid)
    if not info:
        return
    session_id = info["sessionId"]
    session_code = info.get("sessionCode")
    target_user_id = data.get("targetUserId")
    logger.info(f"Forwarding WebRTC answer from receiver {sid} to target user {target_user_id}")

    answers_sent = 0
    for s_id, s_info in active_sockets.items():
        is_same_session = (
            s_info.get("sessionId") == session_id or
            (session_code and s_info.get("sessionCode") == session_code)
        )
        if is_same_session and str(s_info.get("userId")) == str(target_user_id):
            await sio.emit("webrtc_answer", {
                "sdp": data.get("sdp")
            }, to=s_id)
            answers_sent += 1
    logger.info(f"WebRTC answer forwarded to {answers_sent} speaker socket(s)")

@sio.event
async def webrtc_ice_candidate(sid, data):
    """
    Data: { candidate, targetUserId, sessionId }
    """
    info = active_sockets.get(sid)
    if not info:
        return
    session_id = info["sessionId"]
    session_code = info.get("sessionCode")
    user_role = info["role"]
    target_user_id = data.get("targetUserId")

    if user_role in ["receiver", "admin", "moderator"] and target_user_id:
        for s_id, s_info in active_sockets.items():
            is_same_session = (
                s_info.get("sessionId") == session_id or
                (session_code and s_info.get("sessionCode") == session_code)
            )
            if is_same_session and str(s_info.get("userId")) == str(target_user_id):
                await sio.emit("webrtc_ice_candidate", {"candidate": data.get("candidate")}, to=s_id)
    else:
        # Forward candidate from speaker to receiver sockets
        for s_id, s_info in active_sockets.items():
            is_same_session = (
                s_info.get("sessionId") == session_id or
                (session_code and s_info.get("sessionCode") == session_code)
            )
            if is_same_session and s_info.get("role") in ["receiver", "admin", "moderator"]:
                await sio.emit("webrtc_ice_candidate", {
                    "candidate": data.get("candidate"),
                    "senderUserId": info.get("userId")
                }, to=s_id)

async def broadcast_queue_update(session_id: str):
    queue = await get_session_queue(session_id)
    room = f"session_{session_id}"

    # Notify next speaker if position #1
    if queue and queue[0]["status"] == "next":
        next_user_id = queue[0]["userId"]
        for s_id, s_info in active_sockets.items():
            if s_info.get("sessionId") == session_id and s_info.get("userId") == next_user_id:
                await sio.emit("notification", {"type": "warning", "message": "You are next in queue! Get ready to speak."}, to=s_id)

    payload = {
        "sessionId": session_id,
        "queue": queue,
        "activeSpeaker": get_active_speaker(session_id)
    }
    await sio.emit("queue_updated", payload, room=room)
    # Also emit directly to individual sockets in session to guarantee delivery
    for s_id, s_info in active_sockets.items():
        if s_info.get("sessionId") == session_id:
            await sio.emit("queue_updated", payload, to=s_id)
