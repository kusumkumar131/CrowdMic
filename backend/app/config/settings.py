import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    MONGODB_URI: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "crowdmic"
    JWT_SECRET: str = "crowdmic_super_secret_jwt_key_2026_change_in_production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    FRONTEND_URL: str = "http://localhost:5173"
    PORT: int = 8000
    STUN_SERVER: str = "stun:stun.l.google.com:19302"
    TURN_SERVER: str = "turn:openrelay.metered.ca:80"
    TURN_USERNAME: str = "openrelayproject"
    TURN_PASSWORD: str = "openrelayproject"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
