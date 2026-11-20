import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional

class MemoryStore:
    def __init__(self):
        self.users: Dict[str, Dict[str, Any]] = {}
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.queue_entries: Dict[str, Dict[str, Any]] = {} # id -> entry
        self.questions: Dict[str, Dict[str, Any]] = {}
        self.speaker_history: List[Dict[str, Any]] = []

memory_store = MemoryStore()
