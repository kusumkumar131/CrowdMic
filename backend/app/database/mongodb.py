import logging
from motor.motor_asyncio import AsyncIOMotorClient
from app.config.settings import settings

logger = logging.getLogger("crowdmic.database")

class Database:
    client: AsyncIOMotorClient = None
    db = None
    last_error: str = None

db_instance = Database()

async def connect_to_mongo():
    try:
        logger.info(f"Connecting to MongoDB at {settings.MONGODB_URI}...")
        db_instance.client = AsyncIOMotorClient(settings.MONGODB_URI, serverSelectionTimeoutMS=5000)
        # Verify connection
        await db_instance.client.admin.command('ping')
        
        # Ensure database name is never empty
        db_name = (settings.DATABASE_NAME or "").strip()
        if not db_name:
            db_name = "crowdmic"

        db_instance.db = db_instance.client[db_name]
        db_instance.last_error = None
        logger.info(f"Connected to MongoDB database: {db_name}")

        # Create indexes
        try:
            await db_instance.db.users.create_index("email", unique=True)
            await db_instance.db.sessions.create_index("sessionCode", unique=True)
            await db_instance.db.queue_entries.create_index([("sessionId", 1), ("userId", 1)], unique=True)
        except Exception as idx_err:
            logger.warning(f"Index creation note: {idx_err}")
    except Exception as e:
        logger.warning(f"MongoDB connection failed: {e}. Falling back to in-memory store mode for development.")
        db_instance.db = None
        db_instance.last_error = str(e)

async def close_mongo_connection():
    if db_instance.client:
        db_instance.client.close()
        logger.info("MongoDB connection closed.")

def get_database():
    return db_instance.db
