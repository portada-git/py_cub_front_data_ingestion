"""
Database Service for managing database operations, schema initialization,
and data persistence for the file upload storage system.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload
from sqlalchemy import select, delete, update, func, and_, or_
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from .models import Base, Session, ProcessingRecord, FileMetadata
from ..core.config import settings

logger = logging.getLogger(__name__)


class DatabaseService:
    """
    Handles all database operations including schema management, session management,
    processing record persistence, and cleanup operations.
    """
    
    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize the DatabaseService with database connection.
        
        Args:
            database_url: Database URL (defaults to settings.database.DATABASE_URL)
        """
        self.database_url = database_url or settings.database.DATABASE_URL
        self.engine = None
        self.async_session_maker = None
        self._initialized = False
        
        logger.info(f"DatabaseService initialized with URL: {self._mask_db_url(self.database_url)}")
    
    async def initialize(self) -> None:
        """
        Initialize database engine, session maker, and create schema if needed.
        """
        try:
            # Create async engine with simplified configuration for portability
            engine_kwargs = {
                'echo': settings.database.DATABASE_ECHO,
                'pool_pre_ping': True,  # Verify connections before use
            }
            
            # Add SQLite-specific optimizations
            if 'sqlite' in self.database_url.lower():
                engine_kwargs.update({
                    'pool_size': 1,  # SQLite doesn't benefit from connection pooling
                    'max_overflow': 0,
                    'poolclass': None  # Use default for SQLite
                })
            else:
                # For other databases, use basic pooling
                engine_kwargs.update({
                    'pool_size': 5,
                    'max_overflow': 10,
                    'pool_recycle': 3600
                })
            
            self.engine = create_async_engine(self.database_url, **engine_kwargs)
            
            # Create session maker
            self.async_session_maker = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # Create schema
            await self.create_schema()
            
            self._initialized = True
            logger.info("Database service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database service: {e}")
            raise
    
    async def create_schema(self) -> None:
        """
        Create database schema (tables, indexes, constraints).
        """
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            
            logger.info("Database schema created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create database schema: {e}")
            raise
    
    async def close(self) -> None:
        """
        Close database connections and clean up resources.
        """
        if self.engine:
            await self.engine.dispose()
            logger.info("Database service closed")
    
    @asynccontextmanager
    async def get_session(self):
        """
        Get an async database session with automatic cleanup.
        
        Yields:
            AsyncSession: Database session
        """
        if not self._initialized:
            await self.initialize()
        
        async with self.async_session_maker() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    # Session Management Methods
    
    async def create_session(self, metadata: Optional[Dict[str, Any]] = None) -> Session:
        """
        Create a new user session.
        
        Args:
            metadata: Optional session metadata
            
        Returns:
            Session: Created session object
        """
        try:
            session_obj = Session(metadata=metadata or {})
            
            async with self.get_session() as db_session:
                db_session.add(session_obj)
                await db_session.commit()
                await db_session.refresh(session_obj)
            
            logger.info(f"Created new session: {session_obj.id}")
            return session_obj
            
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            raise
    
    async def get_session_by_id(self, session_id: str) -> Optional[Session]:
        """
        Get session by ID.
        
        Args:
            session_id: Session ID to retrieve
            
        Returns:
            Session or None if not found
        """
        try:
            async with self.get_session() as db_session:
                result = await db_session.execute(
                    select(Session).where(Session.id == session_id)
                )
                session_obj = result.scalar_one_or_none()
                
                if session_obj:
                    # Update last accessed time
                    session_obj.update_last_accessed()
                    await db_session.commit()
                
                return session_obj
                
        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {e}")
            return None
    
    async def update_session_access(self, session_id: str) -> bool:
        """
        Update session last accessed timestamp.
        
        Args:
            session_id: Session ID to update
            
        Returns:
            bool: True if updated successfully, False otherwise
        """
        try:
            async with self.get_session() as db_session:
                result = await db_session.execute(
                    update(Session)
                    .where(Session.id == session_id)
                    .values(last_accessed=datetime.utcnow())
                )
                
                await db_session.commit()
                return result.rowcount > 0
                
        except Exception as e:
            logger.error(f"Failed to update session access {session_id}: {e}")
            return False
    
    async def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions and their associated data.
        
        Returns:
            int: Number of sessions cleaned up
        """
        try:
            current_time = datetime.utcnow()
            
            async with self.get_session() as db_session:
                # Get expired sessions
                result = await db_session.execute(
                    select(Session).where(Session.expires_at < current_time)
                )
                expired_sessions = result.scalars().all()
                
                if not expired_sessions:
                    return 0
                
                # Delete expired sessions (cascade will handle processing records)
                await db_session.execute(
                    delete(Session).where(Session.expires_at < current_time)
                )
                
                await db_session.commit()
                
                count = len(expired_sessions)
                logger.info(f"Cleaned up {count} expired sessions")
                return count
                
        except Exception as e:
            logger.error(f"Failed to cleanup expired sessions: {e}")
            return 0
    
    # Processing Record Methods
    
    async def create_processing_record(self, session_id: str, file_info: Dict[str, Any]) -> ProcessingRecord:
        """
        Create a new processing record.
        
        Args:
            session_id: Session ID for the record
            file_info: File information dictionary
            
        Returns:
            ProcessingRecord: Created processing record
        """
        try:
            record = ProcessingRecord(
                session_id=session_id,
                original_filename=file_info.get('original_filename'),
                stored_filename=file_info.get('stored_filename'),
                file_size=file_info.get('file_size', 0),
                file_path=file_info.get('file_path'),
                metadata=file_info.get('metadata', {})
            )
            
            async with self.get_session() as db_session:
                db_session.add(record)
                await db_session.commit()
                await db_session.refresh(record)
            
            logger.info(f"Created processing record: {record.id} for file: {record.original_filename}")
            return record
            
        except Exception as e:
            logger.error(f"Failed to create processing record: {e}")
            raise
    
    async def update_processing_status(self, record_id: str, status: str, 
                                     error_message: Optional[str] = None) -> bool:
        """
        Update processing record status.
        
        Args:
            record_id: Processing record ID
            status: New status
            error_message: Optional error message
            
        Returns:
            bool: True if updated successfully, False otherwise
        """
        try:
            async with self.get_session() as db_session:
                result = await db_session.execute(
                    select(ProcessingRecord).where(ProcessingRecord.id == record_id)
                )
                record = result.scalar_one_or_none()
                
                if not record:
                    logger.warning(f"Processing record not found: {record_id}")
                    return False
                
                record.update_status(status, error_message)
                await db_session.commit()
                
                logger.info(f"Updated processing record {record_id} status to: {status}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to update processing status {record_id}: {e}")
            return False
    
    async def get_processing_history(self, session_id: str, 
                                   filters: Optional[Dict[str, Any]] = None,
                                   page: int = 1, page_size: int = 50) -> Tuple[List[ProcessingRecord], int]:
        """
        Get processing history for a session with optional filtering and pagination.
        
        Args:
            session_id: Session ID to get history for
            filters: Optional filters (status, filename, date_range)
            page: Page number (1-based)
            page_size: Number of records per page
            
        Returns:
            Tuple of (records, total_count)
        """
        try:
            filters = filters or {}
            
            async with self.get_session() as db_session:
                # Build query
                query = select(ProcessingRecord).where(ProcessingRecord.session_id == session_id)
                
                # Apply filters
                if 'status' in filters and filters['status']:
                    query = query.where(ProcessingRecord.processing_status == filters['status'])
                
                if 'filename' in filters and filters['filename']:
                    query = query.where(
                        ProcessingRecord.original_filename.ilike(f"%{filters['filename']}%")
                    )
                
                if 'date_from' in filters and filters['date_from']:
                    query = query.where(ProcessingRecord.upload_timestamp >= filters['date_from'])
                
                if 'date_to' in filters and filters['date_to']:
                    query = query.where(ProcessingRecord.upload_timestamp <= filters['date_to'])
                
                # Get total count
                count_query = select(func.count()).select_from(query.subquery())
                total_count = await db_session.scalar(count_query)
                
                # Apply pagination and ordering
                query = (query
                        .order_by(ProcessingRecord.upload_timestamp.desc())
                        .offset((page - 1) * page_size)
                        .limit(page_size))
                
                result = await db_session.execute(query)
                records = result.scalars().all()
                
                logger.debug(f"Retrieved {len(records)} processing records for session {session_id}")
                return records, total_count or 0
                
        except Exception as e:
            logger.error(f"Failed to get processing history for session {session_id}: {e}")
            return [], 0
    
    async def get_processing_record_by_id(self, record_id: str) -> Optional[ProcessingRecord]:
        """
        Get processing record by ID.
        
        Args:
            record_id: Processing record ID
            
        Returns:
            ProcessingRecord or None if not found
        """
        try:
            async with self.get_session() as db_session:
                result = await db_session.execute(
                    select(ProcessingRecord).where(ProcessingRecord.id == record_id)
                )
                return result.scalar_one_or_none()
                
        except Exception as e:
            logger.error(f"Failed to get processing record {record_id}: {e}")
            return None
    
    # File Metadata Methods
    
    async def create_file_metadata(self, processing_record_id: str, 
                                 metadata_info: Dict[str, Any]) -> FileMetadata:
        """
        Create file metadata record.
        
        Args:
            processing_record_id: Associated processing record ID
            metadata_info: Metadata information dictionary
            
        Returns:
            FileMetadata: Created metadata record
        """
        try:
            metadata = FileMetadata(
                processing_record_id=processing_record_id,
                **metadata_info
            )
            
            async with self.get_session() as db_session:
                db_session.add(metadata)
                await db_session.commit()
                await db_session.refresh(metadata)
            
            logger.info(f"Created file metadata: {metadata.id} for record: {processing_record_id}")
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to create file metadata: {e}")
            raise
    
    # Statistics and Monitoring Methods
    
    async def get_database_stats(self) -> Dict[str, Any]:
        """
        Get database statistics for monitoring.
        
        Returns:
            dict: Database statistics
        """
        try:
            async with self.get_session() as db_session:
                # Count sessions
                session_count = await db_session.scalar(select(func.count(Session.id)))
                
                # Count processing records by status
                status_counts = {}
                result = await db_session.execute(
                    select(ProcessingRecord.processing_status, func.count())
                    .group_by(ProcessingRecord.processing_status)
                )
                
                for status, count in result.all():
                    status_counts[status] = count
                
                # Count expired sessions
                expired_count = await db_session.scalar(
                    select(func.count(Session.id))
                    .where(Session.expires_at < datetime.utcnow())
                )
                
                # Get recent activity (last 24 hours)
                recent_uploads = await db_session.scalar(
                    select(func.count(ProcessingRecord.id))
                    .where(ProcessingRecord.upload_timestamp >= datetime.utcnow() - timedelta(hours=24))
                )
                
                return {
                    'total_sessions': session_count or 0,
                    'expired_sessions': expired_count or 0,
                    'processing_status_counts': status_counts,
                    'recent_uploads_24h': recent_uploads or 0,
                    'database_url': self._mask_db_url(self.database_url),
                    'last_updated': datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {
                'error': str(e),
                'last_updated': datetime.utcnow().isoformat()
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform database health check.
        
        Returns:
            dict: Health check results
        """
        try:
            start_time = datetime.utcnow()
            
            async with self.get_session() as db_session:
                # Simple query to test connectivity
                await db_session.execute(select(1))
            
            end_time = datetime.utcnow()
            response_time_ms = (end_time - start_time).total_seconds() * 1000
            
            return {
                'status': 'healthy',
                'response_time_ms': round(response_time_ms, 2),
                'database_url': self._mask_db_url(self.database_url),
                'timestamp': end_time.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def _mask_db_url(self, url: str) -> str:
        """
        Mask sensitive information in database URL for logging.
        
        Args:
            url: Database URL
            
        Returns:
            str: Masked URL
        """
        if '://' in url:
            scheme, rest = url.split('://', 1)
            if '@' in rest:
                credentials, host_part = rest.split('@', 1)
                return f"{scheme}://***:***@{host_part}"
        return url