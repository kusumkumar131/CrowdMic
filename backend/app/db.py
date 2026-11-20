from pymongo import MongoClient, ASCENDING, DESCENDING
from .config import settings

client = MongoClient(settings.mongodb_uri, serverSelectionTimeoutMS=3000)
db = client[settings.database_name]

def init_indexes():
    db.users.create_index([("email", ASCENDING)], unique=True)
    # Ignore pre-existing/incomplete documents without a valid code while keeping
    # session codes unique for all new, valid session records.
    db.sessions.create_index([("code", ASCENDING)], unique=True, partialFilterExpression={"code": {"$type": "string"}})
    db.queue_entries.create_index([("session_id", ASCENDING), ("status", ASCENDING), ("created_at", ASCENDING)])
    db.queue_entries.create_index([("session_id", ASCENDING), ("user_id", ASCENDING), ("status", ASCENDING)])
    db.queue_entries.create_index([("active_key", ASCENDING)], unique=True, sparse=True)
    db.speaking_history.create_index([("session_id", ASCENDING), ("started_at", DESCENDING)])

def ping():
    client.admin.command("ping")
