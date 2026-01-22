"""
Configuration settings for the PortAda application
"""

import os
from typing import List, Optional
from pydantic import validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # PortAda Configuration
    PORTADA_BASE_PATH: str = "/tmp/portada_data"
    PORTADA_APP_NAME: str = "PortAdaAPI"
    PORTADA_PROJECT_NAME: str = "portada_ingestion"
    INGESTION_FOLDER: str = "/tmp/portada_ingestion"
    
    # FastAPI Configuration
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # CORS Configuration
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://127.0.0.1:3001,http://localhost:5173,http://127.0.0.1:5173"
    
    @property
    def cors_origins(self) -> List[str]:
        """Parse CORS origins from string"""
        if isinstance(self.ALLOWED_ORIGINS, str):
            # Handle comma-separated string format
            if self.ALLOWED_ORIGINS.startswith('[') and self.ALLOWED_ORIGINS.endswith(']'):
                # Handle JSON array format (legacy)
                import json
                try:
                    return json.loads(self.ALLOWED_ORIGINS)
                except json.JSONDecodeError:
                    # If JSON parsing fails, treat as comma-separated
                    return [origin.strip() for origin in self.ALLOWED_ORIGINS.strip('[]').replace('"', '').split(',') if origin.strip()]
            else:
                # Handle comma-separated format
                return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(',') if origin.strip()]
        return [self.ALLOWED_ORIGINS]
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    def validate_config(self) -> None:
        """Validate required configuration parameters"""
        required_fields = [
            'PORTADA_BASE_PATH',
            'PORTADA_APP_NAME', 
            'PORTADA_PROJECT_NAME',
            'INGESTION_FOLDER',
            'SECRET_KEY'
        ]
        
        missing_fields = []
        for field in required_fields:
            value = getattr(self, field, None)
            if not value or (isinstance(value, str) and not value.strip()):
                missing_fields.append(field)
        
        if missing_fields:
            raise ValueError(f"Missing required configuration: {', '.join(missing_fields)}")
        
        # Validate paths exist or can be created
        for path_field in ['PORTADA_BASE_PATH', 'INGESTION_FOLDER']:
            path = getattr(self, path_field)
            try:
                os.makedirs(path, exist_ok=True)
            except Exception as e:
                raise ValueError(f"Cannot create directory {path_field}={path}: {e}")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()