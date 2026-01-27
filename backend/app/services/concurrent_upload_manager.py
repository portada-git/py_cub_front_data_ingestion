"""
Concurrent Upload Manager for handling multiple simultaneous file uploads safely
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, field
from contextlib import asynccontextmanager
from fastapi import UploadFile

from .enhanced_file_handler import EnhancedFileHandler, ProcessingResult
from ..core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class UploadTask:
    """Represents an upload task in the queue"""
    task_id: str
    session_id: str
    file: UploadFile
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[ProcessingResult] = None
    error: Optional[str] = None
    
    @property
    def is_completed(self) -> bool:
        """Check if task is completed"""
        return self.completed_at is not None
    
    @property
    def is_started(self) -> bool:
        """Check if task has started"""
        return self.started_at is not None
    
    @property
    def duration_seconds(self) -> Optional[float]:
        """Get task duration in seconds"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


class ConcurrentUploadManager:
    """
    Manages concurrent file uploads with rate limiting, queue management,
    and thread-safe operations to prevent race conditions.
    """
    
    def __init__(self, file_handler: EnhancedFileHandler, 
                 max_concurrent_uploads: int = 5,
                 max_queue_size: int = 100,
                 upload_timeout_seconds: int = 300):
        """
        Initialize the ConcurrentUploadManager.
        
        Args:
            file_handler: EnhancedFileHandler instance
            max_concurrent_uploads: Maximum number of concurrent uploads
            max_queue_size: Maximum size of upload queue
            upload_timeout_seconds: Timeout for individual uploads
        """
        self.file_handler = file_handler
        self.max_concurrent_uploads = max_concurrent_uploads
        self.max_queue_size = max_queue_size
        self.upload_timeout_seconds = upload_timeout_seconds
        
        # Thread-safe data structures
        self._upload_queue: asyncio.Queue = asyncio.Queue(maxsize=max_queue_size)
        self._active_uploads: Dict[str, UploadTask] = {}
        self._completed_uploads: Dict[str, UploadTask] = {}
        self._upload_lock = asyncio.Lock()
        self._session_locks: Dict[str, asyncio.Lock] = {}
        
        # Worker management
        self._workers: List[asyncio.Task] = []
        self._is_running = False
        self._shutdown_event = asyncio.Event()
        
        # Statistics
        self._stats = {
            'total_uploads': 0,
            'successful_uploads': 0,
            'failed_uploads': 0,
            'queue_full_rejections': 0,
            'timeout_failures': 0,
            'concurrent_peak': 0,
            'average_upload_time': 0.0,
            'last_reset': datetime.utcnow()
        }
        
        logger.info(f"ConcurrentUploadManager initialized: max_concurrent={max_concurrent_uploads}, "
                   f"max_queue={max_queue_size}, timeout={upload_timeout_seconds}s")
    
    async def start(self) -> None:
        """Start the upload manager and worker tasks"""
        if self._is_running:
            logger.warning("Upload manager is already running")
            return
        
        self._is_running = True
        self._shutdown_event.clear()
        
        # Start worker tasks
        for i in range(self.max_concurrent_uploads):
            worker = asyncio.create_task(self._upload_worker(f"worker-{i}"))
            self._workers.append(worker)
        
        logger.info(f"Started {len(self._workers)} upload workers")
    
    async def stop(self) -> None:
        """Stop the upload manager and wait for workers to finish"""
        if not self._is_running:
            return
        
        logger.info("Stopping upload manager...")
        self._is_running = False
        self._shutdown_event.set()
        
        # Cancel all workers
        for worker in self._workers:
            worker.cancel()
        
        # Wait for workers to finish
        if self._workers:
            await asyncio.gather(*self._workers, return_exceptions=True)
        
        self._workers.clear()
        logger.info("Upload manager stopped")
    
    async def submit_upload(self, task_id: str, session_id: str, file: UploadFile,
                          metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Submit an upload task to the queue.
        
        Args:
            task_id: Unique task identifier
            session_id: Session ID for the upload
            file: File to upload
            metadata: Optional metadata
            
        Returns:
            bool: True if task was queued successfully, False if queue is full
        """
        try:
            # Check if queue is full
            if self._upload_queue.full():
                self._stats['queue_full_rejections'] += 1
                logger.warning(f"Upload queue is full, rejecting task: {task_id}")
                return False
            
            # Create upload task
            upload_task = UploadTask(
                task_id=task_id,
                session_id=session_id,
                file=file,
                metadata=metadata or {}
            )
            
            # Add to queue
            await self._upload_queue.put(upload_task)
            
            async with self._upload_lock:
                self._stats['total_uploads'] += 1
            
            logger.info(f"Queued upload task: {task_id} for session: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error submitting upload task {task_id}: {e}")
            return False
    
    async def get_upload_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status of an upload task.
        
        Args:
            task_id: Task ID to check
            
        Returns:
            dict: Task status information or None if not found
        """
        try:
            # Check active uploads
            async with self._upload_lock:
                if task_id in self._active_uploads:
                    task = self._active_uploads[task_id]
                    return {
                        'task_id': task.task_id,
                        'session_id': task.session_id,
                        'status': 'processing',
                        'created_at': task.created_at.isoformat(),
                        'started_at': task.started_at.isoformat() if task.started_at else None,
                        'duration_seconds': task.duration_seconds,
                        'filename': task.file.filename
                    }
                
                # Check completed uploads
                if task_id in self._completed_uploads:
                    task = self._completed_uploads[task_id]
                    return {
                        'task_id': task.task_id,
                        'session_id': task.session_id,
                        'status': 'completed' if task.result and task.result.success else 'failed',
                        'created_at': task.created_at.isoformat(),
                        'started_at': task.started_at.isoformat() if task.started_at else None,
                        'completed_at': task.completed_at.isoformat() if task.completed_at else None,
                        'duration_seconds': task.duration_seconds,
                        'filename': task.file.filename,
                        'result': task.result.to_dict() if task.result else None,
                        'error': task.error
                    }
            
            # Check if task is in queue
            queue_size = self._upload_queue.qsize()
            if queue_size > 0:
                return {
                    'task_id': task_id,
                    'status': 'queued',
                    'queue_position': 'unknown',  # Can't determine position without iterating
                    'queue_size': queue_size
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting upload status for {task_id}: {e}")
            return None
    
    async def get_session_uploads(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get all uploads for a specific session.
        
        Args:
            session_id: Session ID to filter by
            
        Returns:
            list: List of upload status dictionaries
        """
        try:
            uploads = []
            
            async with self._upload_lock:
                # Active uploads
                for task in self._active_uploads.values():
                    if task.session_id == session_id:
                        uploads.append({
                            'task_id': task.task_id,
                            'status': 'processing',
                            'created_at': task.created_at.isoformat(),
                            'started_at': task.started_at.isoformat() if task.started_at else None,
                            'filename': task.file.filename
                        })
                
                # Completed uploads
                for task in self._completed_uploads.values():
                    if task.session_id == session_id:
                        uploads.append({
                            'task_id': task.task_id,
                            'status': 'completed' if task.result and task.result.success else 'failed',
                            'created_at': task.created_at.isoformat(),
                            'started_at': task.started_at.isoformat() if task.started_at else None,
                            'completed_at': task.completed_at.isoformat() if task.completed_at else None,
                            'duration_seconds': task.duration_seconds,
                            'filename': task.file.filename,
                            'result': task.result.to_dict() if task.result else None,
                            'error': task.error
                        })
            
            return sorted(uploads, key=lambda x: x['created_at'], reverse=True)
            
        except Exception as e:
            logger.error(f"Error getting session uploads for {session_id}: {e}")
            return []
    
    async def get_manager_stats(self) -> Dict[str, Any]:
        """
        Get upload manager statistics.
        
        Returns:
            dict: Manager statistics
        """
        try:
            async with self._upload_lock:
                current_active = len(self._active_uploads)
                current_completed = len(self._completed_uploads)
                queue_size = self._upload_queue.qsize()
                
                # Update peak concurrent uploads
                if current_active > self._stats['concurrent_peak']:
                    self._stats['concurrent_peak'] = current_active
                
                return {
                    'is_running': self._is_running,
                    'current_active_uploads': current_active,
                    'current_queue_size': queue_size,
                    'completed_uploads_cached': current_completed,
                    'max_concurrent_uploads': self.max_concurrent_uploads,
                    'max_queue_size': self.max_queue_size,
                    'upload_timeout_seconds': self.upload_timeout_seconds,
                    'worker_count': len(self._workers),
                    'statistics': self._stats.copy(),
                    'last_updated': datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error getting manager stats: {e}")
            return {
                'error': str(e),
                'last_updated': datetime.utcnow().isoformat()
            }
    
    async def cleanup_completed_uploads(self, max_age_hours: int = 24) -> int:
        """
        Clean up old completed upload records from memory.
        
        Args:
            max_age_hours: Maximum age for completed uploads to keep in memory
            
        Returns:
            int: Number of records cleaned up
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
            cleaned_count = 0
            
            async with self._upload_lock:
                to_remove = []
                for task_id, task in self._completed_uploads.items():
                    if task.completed_at and task.completed_at < cutoff_time:
                        to_remove.append(task_id)
                
                for task_id in to_remove:
                    del self._completed_uploads[task_id]
                    cleaned_count += 1
            
            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} old completed upload records")
            
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Error cleaning up completed uploads: {e}")
            return 0
    
    async def _upload_worker(self, worker_name: str) -> None:
        """
        Worker task that processes uploads from the queue.
        
        Args:
            worker_name: Name of the worker for logging
        """
        logger.info(f"Upload worker {worker_name} started")
        
        while self._is_running:
            try:
                # Wait for task or shutdown
                try:
                    task = await asyncio.wait_for(
                        self._upload_queue.get(),
                        timeout=1.0  # Check shutdown every second
                    )
                except asyncio.TimeoutError:
                    continue
                
                if not self._is_running:
                    break
                
                # Process the upload
                await self._process_upload_task(task, worker_name)
                
            except asyncio.CancelledError:
                logger.info(f"Upload worker {worker_name} cancelled")
                break
            except Exception as e:
                logger.error(f"Error in upload worker {worker_name}: {e}")
                await asyncio.sleep(1)  # Brief pause before continuing
        
        logger.info(f"Upload worker {worker_name} stopped")
    
    async def _process_upload_task(self, task: UploadTask, worker_name: str) -> None:
        """
        Process a single upload task.
        
        Args:
            task: Upload task to process
            worker_name: Name of the worker processing the task
        """
        task.started_at = datetime.utcnow()
        
        try:
            # Add to active uploads
            async with self._upload_lock:
                self._active_uploads[task.task_id] = task
            
            logger.info(f"Worker {worker_name} processing upload: {task.task_id}")
            
            # Get session lock to prevent concurrent uploads for same session
            session_lock = await self._get_session_lock(task.session_id)
            
            async with session_lock:
                # Process upload with timeout
                try:
                    task.result = await asyncio.wait_for(
                        self.file_handler.process_upload(
                            task.file, task.session_id, task.metadata
                        ),
                        timeout=self.upload_timeout_seconds
                    )
                except asyncio.TimeoutError:
                    task.error = f"Upload timeout after {self.upload_timeout_seconds} seconds"
                    task.result = ProcessingResult(
                        success=False,
                        error_message=task.error
                    )
                    async with self._upload_lock:
                        self._stats['timeout_failures'] += 1
            
            task.completed_at = datetime.utcnow()
            
            # Update statistics
            async with self._upload_lock:
                if task.result and task.result.success:
                    self._stats['successful_uploads'] += 1
                else:
                    self._stats['failed_uploads'] += 1
                
                # Update average upload time
                if task.duration_seconds:
                    current_avg = self._stats['average_upload_time']
                    total_completed = self._stats['successful_uploads'] + self._stats['failed_uploads']
                    self._stats['average_upload_time'] = (
                        (current_avg * (total_completed - 1) + task.duration_seconds) / total_completed
                    )
                
                # Move from active to completed
                if task.task_id in self._active_uploads:
                    del self._active_uploads[task.task_id]
                self._completed_uploads[task.task_id] = task
            
            status = "success" if task.result and task.result.success else "failed"
            logger.info(f"Worker {worker_name} completed upload: {task.task_id} ({status}) "
                       f"in {task.duration_seconds:.2f}s")
            
        except Exception as e:
            task.completed_at = datetime.utcnow()
            task.error = f"Processing error: {str(e)}"
            task.result = ProcessingResult(success=False, error_message=task.error)
            
            async with self._upload_lock:
                self._stats['failed_uploads'] += 1
                if task.task_id in self._active_uploads:
                    del self._active_uploads[task.task_id]
                self._completed_uploads[task.task_id] = task
            
            logger.error(f"Worker {worker_name} failed to process upload {task.task_id}: {e}")
    
    async def _get_session_lock(self, session_id: str) -> asyncio.Lock:
        """
        Get or create a lock for a specific session.
        
        Args:
            session_id: Session ID
            
        Returns:
            asyncio.Lock: Lock for the session
        """
        if session_id not in self._session_locks:
            self._session_locks[session_id] = asyncio.Lock()
        return self._session_locks[session_id]
    
    @asynccontextmanager
    async def upload_manager_context(self):
        """Context manager for upload manager lifecycle"""
        await self.start()
        try:
            yield self
        finally:
            await self.stop()