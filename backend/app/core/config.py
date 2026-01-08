"""
Configuration settings for the PortAda API
"""

from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings"""
    
    # FastAPI Configuration
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # PortAda Configuration
    PORTADA_BASE_PATH: str = "/tmp/portada_data"
    PORTADA_APP_NAME: str = "PortAdaAPI"
    PORTADA_PROJECT_NAME: str = "portada_ingestion"
    
    # CORS Configuration
    ALLOWED_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    
    class Config:
        env_file = ".env"

settings = Settings()