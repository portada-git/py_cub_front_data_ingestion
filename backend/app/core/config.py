"""
Configuration settings for the PortAda API
"""

import os
from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings"""
    
    # FastAPI Configuration
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # PortAda Configuration
    PORTADA_BASE_PATH: str = os.getenv("PORTADA_BASE_PATH", "/tmp/portada_data")
    PORTADA_APP_NAME: str = os.getenv("PORTADA_APP_NAME", "PortAdaAPI")
    PORTADA_PROJECT_NAME: str = os.getenv("PORTADA_PROJECT_NAME", "portada_ingestion")
    
    # CORS Configuration
    ALLOWED_ORIGINS: List[str] = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
    
    class Config:
        env_file = ".env"

settings = Settings()