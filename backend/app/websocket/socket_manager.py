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
# Active speaker tracking per session: session_id/code -> { userId, userName, role }
active_speakers = {}

def get_active_speaker(identifier: str):
    if not identifier:
        return None
    return active_speakers.get(identifier)

def set_active_speaker(session_id: str, speaker_info, session_code: str = None):
    keys = list(set(filter(None, [session_id, session_code])))
    if speaker_info:
        for k in keys:
            active_speakers[k] = speaker_info
    else:
        for k in keys:
            active_speakers.pop(k, None)
        # Also clean up any other key pointing to the same speaker
        for k in list(active_speakers.keys()):
            if k == session_id or (session_code and k == session_code):
                active_speakers.pop(k, None)
