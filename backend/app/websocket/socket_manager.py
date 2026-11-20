import socketio
import logging
from app.config.settings import settings

logger = logging.getLogger("crowdmic.socketio")

sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",
    logger=False,
    engineio_logger=False
)

# Active sockets tracking: sid -> { userId, role, sessionCode, sessionId }
active_sockets = {}
# Active speaker tracking per session: session_id -> { userId, userName, role }
active_speakers = {}

def get_active_speaker(session_id: str):
    return active_speakers.get(session_id)

def set_active_speaker(session_id: str, speaker_info):
    if speaker_info:
        active_speakers[session_id] = speaker_info
    else:
        active_speakers.pop(session_id, None)
