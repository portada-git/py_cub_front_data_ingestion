"""
Database models for file upload storage and session management
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy import Column, String, DateTime, Integer, BigInteger, Text, JSON, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import event
from sqlalchemy.engine import Engine
import sqlite3

# Enable foreign key constraints for SQLite
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

Base = declarative_base()


class Session(Base):
    """
    User session model for tracking upload sessions and maintaining state
    across browser refreshes and multiple uploads.
    """
    __tablename__ = "sessions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_accessed = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    session_metadata = Column(JSON, default=dict)  # Renamed from 'metadata'
    
    # Relationship to processing records
    processing_records = relationship("ProcessingRecord", back_populates="session", cascade="all, delete-orphan")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.expires_at:
            # Default to 30 days from creation
            from ..core.config import settings
            duration_days = settings.database.SESSION_DURATION_DAYS
            self.expires_at = self.created_at + timedelta(days=duration_days)
    
    def is_expired(self) -> bool:
        """Check if the session has expired"""
        return datetime.utcnow() > self.expires_at
    
    def update_last_accessed(self) -> None:
        """Update the last accessed timestamp"""
        self.last_accessed = datetime.utcnow()
    
    def extend_expiration(self, days: Optional[int] = None) -> None:
        """Extend session expiration"""
        if days is None:
            from ..core.config import settings
            days = settings.database.SESSION_DURATION_DAYS
        
        self.expires_at = datetime.utcnow() + timedelta(days=days)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary for API responses"""
        return {
            'id': self.id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_accessed': self.last_accessed.isoformat() if self.last_accessed else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_expired': self.is_expired(),
            'metadata': self.session_metadata or {}
        }
    
    def __repr__(self):
        return f"<Session(id={self.id}, created_at={self.created_at}, expires_at={self.expires_at})>"


class ProcessingRecord(Base):
    """
    Processing record model for tracking file uploads, processing status,
    and maintaining history of user activities.
    """
    __tablename__ = "processing_records"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("sessions.id"), nullable=False)
    
    # File information
    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    file_path = Column(Text, nullable=True)  # Full path to stored file
    
    # Processing information
    upload_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    processing_status = Column(String(50), default='uploaded', nullable=False)
    processing_started_at = Column(DateTime, nullable=True)
    processing_completed_at = Column(DateTime, nullable=True)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    
    # Additional metadata
    record_metadata = Column(JSON, default=dict)  # Renamed from 'metadata'
    
    # Relationship to session
    session = relationship("Session", back_populates="processing_records")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure we have a valid processing status
        valid_statuses = ['uploaded', 'processing', 'completed', 'failed', 'cancelled']
        if self.processing_status not in valid_statuses:
            self.processing_status = 'uploaded'
    
    def update_status(self, status: str, error_message: Optional[str] = None) -> None:
        """Update processing status with timestamp tracking"""
        valid_statuses = ['uploaded', 'processing', 'completed', 'failed', 'cancelled']
        if status not in valid_statuses:
            raise ValueError(f"Invalid status: {status}. Must be one of {valid_statuses}")
        
        old_status = self.processing_status
        self.processing_status = status
        
        # Update timestamps based on status
        if status == 'processing' and old_status == 'uploaded':
            self.processing_started_at = datetime.utcnow()
        elif status in ['completed', 'failed', 'cancelled']:
            if not self.processing_started_at:
                self.processing_started_at = datetime.utcnow()
            self.processing_completed_at = datetime.utcnow()
        
        # Handle error messages
        if error_message:
            self.error_message = error_message
        elif status == 'completed':
            self.error_message = None  # Clear error on success
    
    def increment_retry_count(self) -> None:
        """Increment the retry counter"""
        self.retry_count += 1
    
    def get_processing_duration(self) -> Optional[timedelta]:
        """Get the total processing duration if available"""
        if self.processing_started_at and self.processing_completed_at:
            return self.processing_completed_at - self.processing_started_at
        return None
    
    def is_processing_complete(self) -> bool:
        """Check if processing is in a final state"""
        return self.processing_status in ['completed', 'failed', 'cancelled']
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert processing record to dictionary for API responses"""
        duration = self.get_processing_duration()
        
        return {
            'id': self.id,
            'session_id': self.session_id,
            'original_filename': self.original_filename,
            'stored_filename': self.stored_filename,
            'file_size': self.file_size,
            'file_path': self.file_path,
            'upload_timestamp': self.upload_timestamp.isoformat() if self.upload_timestamp else None,
            'processing_status': self.processing_status,
            'processing_started_at': self.processing_started_at.isoformat() if self.processing_started_at else None,
            'processing_completed_at': self.processing_completed_at.isoformat() if self.processing_completed_at else None,
            'processing_duration_seconds': duration.total_seconds() if duration else None,
            'error_message': self.error_message,
            'retry_count': self.retry_count,
            'metadata': self.record_metadata or {},  # Use renamed field
            'is_complete': self.is_processing_complete()
        }
    
    def __repr__(self):
        return (f"<ProcessingRecord(id={self.id}, filename={self.original_filename}, "
                f"status={self.processing_status}, session_id={self.session_id})>")


class FileMetadata(Base):
    """
    Extended file metadata model for storing additional file information
    and analysis results.
    """
    __tablename__ = "file_metadata"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    processing_record_id = Column(String(36), ForeignKey("processing_records.id"), nullable=False)
    
    # File analysis metadata
    file_type = Column(String(50), nullable=True)  # Detected file type
    encoding = Column(String(50), nullable=True)   # File encoding
    line_count = Column(Integer, nullable=True)    # Number of lines (for text files)
    record_count = Column(Integer, nullable=True)  # Number of records (for structured data)
    
    # Content analysis
    content_hash = Column(String(64), nullable=True)  # SHA-256 hash of content
    content_preview = Column(Text, nullable=True)     # First few lines/records
    
    # Validation results
    is_valid_json = Column(Boolean, nullable=True)
    is_valid_csv = Column(Boolean, nullable=True)
    validation_errors = Column(JSON, default=list)
    
    # Processing metadata
    analysis_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    analysis_duration_ms = Column(Integer, nullable=True)
    
    # Additional metadata
    file_metadata = Column(JSON, default=dict)  # Renamed from 'metadata'
    
    # Relationship to processing record
    processing_record = relationship("ProcessingRecord")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert file metadata to dictionary for API responses"""
        return {
            'id': self.id,
            'processing_record_id': self.processing_record_id,
            'file_type': self.file_type,
            'encoding': self.encoding,
            'line_count': self.line_count,
            'record_count': self.record_count,
            'content_hash': self.content_hash,
            'content_preview': self.content_preview,
            'is_valid_json': self.is_valid_json,
            'is_valid_csv': self.is_valid_csv,
            'validation_errors': self.validation_errors or [],
            'analysis_timestamp': self.analysis_timestamp.isoformat() if self.analysis_timestamp else None,
            'analysis_duration_ms': self.analysis_duration_ms,
            'metadata': self.file_metadata or {}  # Use renamed field
        }
    
    def __repr__(self):
        return (f"<FileMetadata(id={self.id}, processing_record_id={self.processing_record_id}, "
                f"file_type={self.file_type})>")


# Export all models
__all__ = ["Base", "Session", "ProcessingRecord", "FileMetadata"]