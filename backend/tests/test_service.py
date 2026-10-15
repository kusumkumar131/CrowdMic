from datetime import datetime, timezone
from app.service import queue_state

class FakeCursor(list):
    def sort(self, key, direction):
        return FakeCursor(sorted(self, key=lambda x: x[key], reverse=direction < 0))

class FakeCollection:
    def __init__(self, entries): self.entries = entries
    def find(self, query):
        return FakeCursor([x for x in self.entries if x["session_id"]==query["session_id"] and x["status"] in query["status"]["$in"]])

def test_queue_filters_terminal_entries_and_assigns_positions(monkeypatch):
    from app import service
    sid="session-a"; created=datetime.now(timezone.utc)
    entries=[{"_id":"1","session_id":sid,"user_id":"u1","name":"A","status":"pending","created_at":created},{"_id":"2","session_id":sid,"user_id":"u2","name":"B","status":"skipped","created_at":created},{"_id":"3","session_id":sid,"user_id":"u3","name":"C","status":"speaking","created_at":created}]
    class DB: queue_entries=FakeCollection(entries)
    monkeypatch.setattr(service,"db",DB())
    result=queue_state(sid)
    assert [(x["name"],x["position"]) for x in result]==[("A",1),("C",2)]

