import os
import socketio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.config.settings import settings
from app.database.mongodb import connect_to_mongo, close_mongo_connection
from app.routes import auth, sessions, queue, questions, analytics
from app.websocket.socket_manager import sio
import app.websocket.events # Load event handlers

from app.services.auth_service import seed_demo_users

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    await seed_demo_users()
    yield
    await close_mongo_connection()

fastapi_app = FastAPI(
    title="CrowdMic API",
    description="Real-time virtual microphone and Q&A management platform for large events.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register REST Routers
fastapi_app.include_router(auth.router)
fastapi_app.include_router(sessions.router)
fastapi_app.include_router(queue.router)
fastapi_app.include_router(questions.router)
fastapi_app.include_router(analytics.router)

@fastapi_app.get("/")
async def root():
    from app.database.mongodb import get_database, db_instance
    db = get_database()
    return {
        "app": "CrowdMic API",
        "status": "online",
        "database": "connected" if db is not None else "in_memory_fallback",
        "db_error": db_instance.last_error if db is None else None,
        "tagline": "One microphone system for thousands of voices."
    }

# Combine Socket.IO ASGI App with FastAPI
app = socketio.ASGIApp(
    socketio_server=sio,
    other_asgi_app=fastapi_app,
    socketio_path="/socket.io"
)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", settings.PORT or 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False)
