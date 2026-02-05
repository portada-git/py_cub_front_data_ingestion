"""
Configuration settings for the PortAda application
"""

import os
from typing import List, Optional
from pathlib import Path
from pydantic import validator
from pydantic_settings import BaseSettings

# Calculate project root directory - use environment variable or calculate
PROJECT_ROOT = Path(os.environ.get('PROJECT_ROOT', Path(__file__).parent.parent.parent.parent))
STORAGE_DIR = PROJECT_ROOT / ".storage"

# Ensure we use absolute paths to avoid working directory issues
STORAGE_DIR = STORAGE_DIR.resolve()


class DatabaseSettings(BaseSettings):
    """Database configuration settings"""
    
    # Database Configuration - Simple SQLite by default
    DATABASE_URL: str = f"sqlite+aiosqlite:///{STORAGE_DIR}/portada.db"
    DATABASE_ECHO: bool = False  # Set to True for SQL query logging
    
    # Session Configuration
    SESSION_DURATION_DAYS: int = 30
    SESSION_CLEANUP_INTERVAL_HOURS: int = 24
    
    class Config:
        env_prefix = "DB_"
        env_file = ".env"
        extra = "ignore"  # Ignore extra fields


class StorageSettings(BaseSettings):
    """Storage configuration settings"""
    
    # Storage Configuration
    STORAGE_BASE_PATH: str = str(STORAGE_DIR)
    INGESTION_STORAGE_PATH: str = str(STORAGE_DIR / "ingestion")
    MAX_FILE_SIZE_MB: int = 100
    ALLOWED_FILE_EXTENSIONS: List[str] = [".json", ".csv", ".txt"]
    STORAGE_PERMISSIONS: int = 0o755
    
    # Disk space management
    MIN_FREE_SPACE_MB: int = 100
    CLEANUP_TEMP_FILES_HOURS: int = 24
    
    class Config:
        env_prefix = "STORAGE_"
        env_file = ".env"
        extra = "ignore"  # Ignore extra fields


class Settings(BaseSettings):
    """Application settings"""
    
    # PortAda Configuration - Using project-relative paths
    PORTADA_BASE_PATH: str = str(STORAGE_DIR / "portada_data")
    PORTADA_APP_NAME: str = "PortAdaAPI"
    PORTADA_PROJECT_NAME: str = "portada_ingestion"
    INGESTION_FOLDER: str = str(STORAGE_DIR / "ingestion")
    
    # PortAda Configuration Files - CRITICAL for portada_data_layer
    PORTADA_CONFIG_PATH: str = str(STORAGE_DIR / "config" / "delta_data_layer_config.json")
    PORTADA_SCHEMA_PATH: str = str(STORAGE_DIR / "config" / "schema.json")
    PORTADA_MAPPING_PATH: str = str(STORAGE_DIR / "config" / "mapping_to_clean_chars.json")
    
    # FastAPI Configuration
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Java Configuration
    JAVA_HOME: Optional[str] = "/usr/lib/jvm/java-17-openjdk-amd64"
    
    # CORS Configuration
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"
    
    # Sub-configurations
    database: DatabaseSettings = DatabaseSettings()
    storage: StorageSettings = StorageSettings()
    
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
    
    @validator('JAVA_HOME', pre=True)
    def set_java_home_env(cls, v):
        """Set JAVA_HOME environment variable if provided"""
        if v:
            os.environ['JAVA_HOME'] = v
        return v
    
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
        
        # Validate Java configuration
        if self.JAVA_HOME:
            java_executable = os.path.join(self.JAVA_HOME, 'bin', 'java')
            if not os.path.exists(java_executable):
                raise ValueError(f"Java executable not found at {java_executable}. Please check JAVA_HOME configuration.")
        
        # Validate paths exist or can be created - using absolute paths
        for path_field in ['PORTADA_BASE_PATH', 'INGESTION_FOLDER']:
            path = getattr(self, path_field)
            abs_path = Path(path).resolve()  # Convert to absolute path
            try:
                abs_path.mkdir(parents=True, exist_ok=True)
                print(f"✅ Storage directory ready: {abs_path}")
            except Exception as e:
                raise ValueError(f"Cannot create directory {path_field}={abs_path}: {e}")
        
        # Validate storage configuration
        self._validate_storage_config()
        
        # Validate database configuration
        self._validate_database_config()
        
        # Validate Portada configuration files
        self._validate_portada_config_files()
    
    def _validate_storage_config(self) -> None:
        """Validate storage configuration"""
        storage_path = Path(self.storage.STORAGE_BASE_PATH).resolve()
        ingestion_path = Path(self.storage.INGESTION_STORAGE_PATH).resolve()
        
        # Create directories if they don't exist
        try:
            storage_path.mkdir(parents=True, exist_ok=True)
            ingestion_path.mkdir(parents=True, exist_ok=True)
            print(f"✅ Storage directories ready: {storage_path}, {ingestion_path}")
        except Exception as e:
            raise ValueError(f"Cannot create storage directories: {e}")
        
        # Validate file size limits
        if self.storage.MAX_FILE_SIZE_MB <= 0:
            raise ValueError("MAX_FILE_SIZE_MB must be positive")
        
        if self.storage.MIN_FREE_SPACE_MB <= 0:
            raise ValueError("MIN_FREE_SPACE_MB must be positive")
    
    def _validate_database_config(self) -> None:
        """Validate database configuration"""
        if not self.database.DATABASE_URL:
            raise ValueError("DATABASE_URL is required")
        
        if self.database.SESSION_DURATION_DAYS <= 0:
            raise ValueError("SESSION_DURATION_DAYS must be positive")
        
        if self.database.SESSION_CLEANUP_INTERVAL_HOURS <= 0:
            raise ValueError("SESSION_CLEANUP_INTERVAL_HOURS must be positive")
    
    def _validate_portada_config_files(self) -> None:
        """Validate that Portada configuration files exist"""
        config_files = {
            'PORTADA_CONFIG_PATH': 'delta_data_layer_config.json',
            'PORTADA_SCHEMA_PATH': 'schema.json',
            'PORTADA_MAPPING_PATH': 'mapping_to_clean_chars.json'
        }
        
        missing_files = []
        for config_key, file_name in config_files.items():
            file_path = Path(getattr(self, config_key))
            if not file_path.exists():
                missing_files.append(f"{file_name} (expected at: {file_path})")
        
        if missing_files:
            error_msg = (
                f"❌ Portada configuration files missing:\n"
                f"  - {chr(10).join(missing_files)}\n\n"
                f"These files are REQUIRED for portada_data_layer to function.\n"
                f"Please create these files or copy them from the configuration repository."
            )
            raise ValueError(error_msg)
        
        print(f"✅ Portada configuration files validated successfully")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()