"""
Session cleanup and maintenance tasks for automated session management
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager

from ..database.database_service import DatabaseService
from .session_manager import SessionManager
from ..core.config import settings

logger = logging.getLogger(__name__)


class SessionCleanupService:
    """
    Handles automated session cleanup and maintenance tasks.
    
    Provides scheduled cleanup of expired sessions, monitoring of session
    health, and maintenance operations to keep the session system running
    efficiently.
    """
    
    def __init__(self, database_service: DatabaseService, session_manager: SessionManager):
        """
        Initialize the SessionCleanupService.
        
        Args:
            database_service: DatabaseService instance
            session_manager: SessionManager instance
        """
        self.database_service = database_service
        self.session_manager = session_manager
        self.cleanup_interval_hours = settings.database.SESSION_CLEANUP_INTERVAL_HOURS
        self.is_running = False
        self.cleanup_task = None
        
        logger.info(f"SessionCleanupService initialized with {self.cleanup_interval_hours}h cleanup interval")
    
    async def start_cleanup_scheduler(self) -> None:
        """
        Start the automated cleanup scheduler.
        """
        if self.is_running:
            logger.warning("Cleanup scheduler is already running")
            return
        
        self.is_running = True
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("Session cleanup scheduler started")
    
    async def stop_cleanup_scheduler(self) -> None:
        """
        Stop the automated cleanup scheduler.
        """
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Session cleanup scheduler stopped")
    
    async def run_cleanup(self) -> Dict[str, Any]:
        """
        Run a single cleanup operation and return statistics.
        
        Returns:
            dict: Cleanup statistics and results
        """
        start_time = datetime.utcnow()
        
        try:
            logger.info("Starting session cleanup operation")
            
            # Get stats before cleanup
            stats_before = await self.session_manager.get_session_stats()
            
            # Cleanup expired sessions
            expired_count = await self.session_manager.cleanup_expired_sessions()
            
            # Cleanup orphaned processing records (if any)
            orphaned_count = await self._cleanup_orphaned_records()
            
            # Get stats after cleanup
            stats_after = await self.session_manager.get_session_stats()
            
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            result = {
                'success': True,
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'duration_seconds': round(duration, 2),
                'expired_sessions_cleaned': expired_count,
                'orphaned_records_cleaned': orphaned_count,
                'sessions_before': stats_before.get('total_sessions', 0),
                'sessions_after': stats_after.get('total_sessions', 0),
                'expired_sessions_before': stats_before.get('expired_sessions', 0),
                'expired_sessions_after': stats_after.get('expired_sessions', 0)
            }
            
            logger.info(f"Cleanup completed: {expired_count} sessions, {orphaned_count} orphaned records, "
                       f"duration: {duration:.2f}s")
            
            return result
            
        except Exception as e:
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            logger.error(f"Cleanup operation failed: {e}")
            
            return {
                'success': False,
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'duration_seconds': round(duration, 2),
                'error': str(e),
                'expired_sessions_cleaned': 0,
                'orphaned_records_cleaned': 0
            }
    
    async def get_cleanup_status(self) -> Dict[str, Any]:
        """
        Get current cleanup service status.
        
        Returns:
            dict: Cleanup service status information
        """
        try:
            session_stats = await self.session_manager.get_session_stats()
            db_stats = await self.database_service.get_database_stats()
            
            return {
                'is_running': self.is_running,
                'cleanup_interval_hours': self.cleanup_interval_hours,
                'next_cleanup_estimate': self._get_next_cleanup_estimate(),
                'session_stats': session_stats,
                'database_stats': {
                    'total_sessions': db_stats.get('total_sessions', 0),
                    'expired_sessions': db_stats.get('expired_sessions', 0),
                    'processing_status_counts': db_stats.get('processing_status_counts', {}),
                    'recent_uploads_24h': db_stats.get('recent_uploads_24h', 0)
                },
                'last_updated': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting cleanup status: {e}")
            return {
                'is_running': self.is_running,
                'error': str(e),
                'last_updated': datetime.utcnow().isoformat()
            }
    
    async def force_cleanup_session(self, session_id: str) -> bool:
        """
        Force cleanup of a specific session.
        
        Args:
            session_id: Session ID to cleanup
            
        Returns:
            bool: True if cleaned up successfully, False otherwise
        """
        try:
            # Invalidate the session
            success = await self.session_manager.invalidate_session(session_id)
            
            if success:
                # Run cleanup to remove it from database
                await self.session_manager.cleanup_expired_sessions()
                logger.info(f"Force cleaned up session: {session_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to force cleanup session {session_id}: {e}")
            return False
    
    async def optimize_database(self) -> Dict[str, Any]:
        """
        Run database optimization operations.
        
        Returns:
            dict: Optimization results
        """
        start_time = datetime.utcnow()
        
        try:
            logger.info("Starting database optimization")
            
            # For SQLite, run VACUUM and ANALYZE
            if 'sqlite' in self.database_service.database_url.lower():
                await self._optimize_sqlite()
            
            # For PostgreSQL, run VACUUM ANALYZE
            elif 'postgresql' in self.database_service.database_url.lower():
                await self._optimize_postgresql()
            
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            result = {
                'success': True,
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'duration_seconds': round(duration, 2),
                'database_type': self._get_database_type()
            }
            
            logger.info(f"Database optimization completed in {duration:.2f}s")
            return result
            
        except Exception as e:
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            logger.error(f"Database optimization failed: {e}")
            
            return {
                'success': False,
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'duration_seconds': round(duration, 2),
                'error': str(e),
                'database_type': self._get_database_type()
            }
    
    async def _cleanup_loop(self) -> None:
        """
        Main cleanup loop that runs periodically.
        """
        logger.info("Starting cleanup loop")
        
        while self.is_running:
            try:
                # Wait for the cleanup interval
                await asyncio.sleep(self.cleanup_interval_hours * 3600)
                
                if not self.is_running:
                    break
                
                # Run cleanup
                await self.run_cleanup()
                
            except asyncio.CancelledError:
                logger.info("Cleanup loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
                # Continue running even if cleanup fails
                await asyncio.sleep(300)  # Wait 5 minutes before retrying
    
    async def _cleanup_orphaned_records(self) -> int:
        """
        Clean up orphaned processing records that don't have valid sessions.
        
        Returns:
            int: Number of orphaned records cleaned up
        """
        try:
            # This would be implemented based on specific business logic
            # For now, we rely on foreign key cascades to handle this
            logger.debug("Checking for orphaned processing records")
            return 0
            
        except Exception as e:
            logger.error(f"Error cleaning up orphaned records: {e}")
            return 0
    
    async def _optimize_sqlite(self) -> None:
        """
        Run SQLite-specific optimization commands.
        """
        try:
            async with self.database_service.get_session() as session:
                # Run VACUUM to reclaim space
                await session.execute("VACUUM")
                
                # Run ANALYZE to update statistics
                await session.execute("ANALYZE")
                
                await session.commit()
            
            logger.info("SQLite optimization completed")
            
        except Exception as e:
            logger.error(f"SQLite optimization failed: {e}")
            raise
    
    async def _optimize_postgresql(self) -> None:
        """
        Run PostgreSQL-specific optimization commands.
        """
        try:
            async with self.database_service.get_session() as session:
                # Run VACUUM ANALYZE on main tables
                tables = ['sessions', 'processing_records', 'file_metadata']
                
                for table in tables:
                    await session.execute(f"VACUUM ANALYZE {table}")
                
                await session.commit()
            
            logger.info("PostgreSQL optimization completed")
            
        except Exception as e:
            logger.error(f"PostgreSQL optimization failed: {e}")
            raise
    
    def _get_database_type(self) -> str:
        """
        Get the database type from the connection URL.
        
        Returns:
            str: Database type (sqlite, postgresql, etc.)
        """
        url = self.database_service.database_url.lower()
        
        if 'sqlite' in url:
            return 'sqlite'
        elif 'postgresql' in url:
            return 'postgresql'
        elif 'mysql' in url:
            return 'mysql'
        else:
            return 'unknown'
    
    def _get_next_cleanup_estimate(self) -> Optional[str]:
        """
        Estimate when the next cleanup will run.
        
        Returns:
            str or None: ISO timestamp of estimated next cleanup
        """
        if not self.is_running:
            return None
        
        next_cleanup = datetime.utcnow() + timedelta(hours=self.cleanup_interval_hours)
        return next_cleanup.isoformat()
    
    @asynccontextmanager
    async def cleanup_context(self):
        """
        Context manager for cleanup operations with proper startup/shutdown.
        """
        await self.start_cleanup_scheduler()
        try:
            yield self
        finally:
            await self.stop_cleanup_scheduler()