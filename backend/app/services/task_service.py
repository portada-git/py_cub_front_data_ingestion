"""
Asynchronous task processing service for the PortAda application
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable, Awaitable
from enum import Enum
import logging
from dataclasses import dataclass, asdict

from app.core.exceptions import PortAdaBaseException
from app.models.ingestion import IngestionStatus
from app.database.database_service import DatabaseService
from app.database.models import ProcessingRecord

logger = logging.getLogger(__name__)


class TaskType(str, Enum):
    """Types of background tasks"""
    INGESTION = "ingestion"
    ANALYSIS = "analysis"
    CLEANUP = "cleanup"
    EXPORT = "export"


class TaskPriority(str, Enum):
    """Task priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class TaskInfo:
    """Information about a background task"""
    task_id: str
    task_type: TaskType
    status: IngestionStatus
    priority: TaskPriority
    title: str
    description: str
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    progress_percentage: float = 0.0
    current_step: str = ""
    total_steps: int = 1
    completed_steps: int = 0
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None  # Added for database persistence
    file_name: Optional[str] = None  # Added for frontend display
    file_size: Optional[int] = None  # Added for frontend display
    records_processed: Optional[int] = None  # Added for frontend display
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        data = asdict(self)
        # Convert datetime objects to ISO strings
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
        return data
    
    def update_progress(self, percentage: float, step: str = "", completed_steps: int = None, records_processed: int = None):
        """Update task progress"""
        self.progress_percentage = max(0.0, min(100.0, percentage))
        if step:
            self.current_step = step
        if completed_steps is not None:
            self.completed_steps = completed_steps
        if records_processed is not None:
            self.records_processed = records_processed
        self.updated_at = datetime.utcnow()


class TaskService:
    """Service for managing background tasks"""
    
    def __init__(self):
        self.tasks: Dict[str, TaskInfo] = {}
        self.task_queue: List[str] = []
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.max_concurrent_tasks = 3
        self.task_retention_hours = 24
        self._processing_lock = asyncio.Lock()
        self.database_service: Optional[DatabaseService] = None
    
    async def create_task(
        self,
        task_type: TaskType,
        title: str,
        description: str,
        priority: TaskPriority = TaskPriority.NORMAL,
        metadata: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        file_name: Optional[str] = None,
        file_size: Optional[int] = None
    ) -> str:
        """
        Create a new background task
        
        Args:
            task_type: Type of task
            title: Task title
            description: Task description
            priority: Task priority
            metadata: Additional task metadata
            user_id: ID of user who created the task
            session_id: ID of the current session
            file_name: Name of the file being processed (optional)
            file_size: Size of the file being processed (optional)
            
        Returns:
            Task ID
        """
        task_id = str(uuid.uuid4())
        
        task_info = TaskInfo(
            task_id=task_id,
            task_type=task_type,
            status=IngestionStatus.PENDING,
            priority=priority,
            title=title,
            description=description,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            metadata=metadata or {},
            user_id=user_id,
            session_id=session_id,
            file_name=file_name,
            file_size=file_size
        )
        
        self.tasks[task_id] = task_info
        
        # PERSIST TO DATABASE
        if self.database_service and session_id:
            try:
                # Map ingestion status to processing record status
                db_status = 'uploaded'  # Equivalent to PENDING
                
                await self.database_service.create_processing_record(
                    session_id=session_id,
                    file_info={
                        'original_filename': file_name or "unknown",
                        'stored_filename': file_name or "unknown",
                        'file_size': file_size or 0,
                        'status': db_status,
                        'metadata': metadata or {}
                    },
                    record_id=task_id
                )
                logger.info(f"Task {task_id} persisted to database history")
            except Exception as e:
                logger.error(f"Failed to persist task {task_id} to database: {e}")
        
        # Add to queue based on priority
        self._add_to_queue(task_id, priority)
        
        logger.info(f"Task created: {task_id} - {title}")
        return task_id
    
    def _add_to_queue(self, task_id: str, priority: TaskPriority):
        """Add task to queue based on priority"""
        if priority == TaskPriority.URGENT:
            self.task_queue.insert(0, task_id)
        elif priority == TaskPriority.HIGH:
            # Insert after other urgent tasks
            insert_pos = 0
            for i, queued_id in enumerate(self.task_queue):
                if self.tasks[queued_id].priority != TaskPriority.URGENT:
                    insert_pos = i
                    break
            else:
                insert_pos = len(self.task_queue)
            self.task_queue.insert(insert_pos, task_id)
        else:
            # Normal and low priority go to the end
            self.task_queue.append(task_id)
    
    async def _update_db_record(self, task_info: TaskInfo):
        """Update the database record with current task info"""
        if not self.database_service or not task_info.session_id:
            return
            
        try:
            # Map IngestionStatus to ProcessingRecord status
            status_map = {
                IngestionStatus.PENDING: 'uploaded',
                IngestionStatus.PROCESSING: 'processing',
                IngestionStatus.COMPLETED: 'completed',
                IngestionStatus.FAILED: 'failed',
                IngestionStatus.CANCELLED: 'cancelled'
            }
            db_status = status_map.get(task_info.status, 'uploaded')
            
            await self.database_service.update_processing_status(
                record_id=task_info.task_id,
                status=db_status,
                error_message=task_info.error_message,
                records_processed=task_info.records_processed,
                metadata=task_info.metadata
            )
        except Exception as e:
            logger.error(f"Failed to update database record for task {task_info.task_id}: {e}")

    async def execute_task(
        self,
        task_id: str,
        task_function: Callable[..., Awaitable[Any]],
        *args,
        **kwargs
    ) -> None:
        """
        Execute a background task
        
        Args:
            task_id: Task identifier
            task_function: Async function to execute
            *args: Arguments for task function
            **kwargs: Keyword arguments for task function
        """
        task_info = self.tasks.get(task_id)
        if not task_info:
            logger.error(f"Task not found: {task_id}")
            return
        
        try:
            # Update task status
            task_info.status = IngestionStatus.PROCESSING
            task_info.started_at = datetime.utcnow()
            task_info.updated_at = datetime.utcnow()
            
            # Update DB
            await self._update_db_record(task_info)
            
            logger.info(f"Starting task execution: {task_id}")
            
            # Execute the task function
            result = await task_function(task_info, *args, **kwargs)
            
            # Update task with success
            task_info.status = IngestionStatus.COMPLETED
            task_info.completed_at = datetime.utcnow()
            task_info.updated_at = datetime.utcnow()
            task_info.progress_percentage = 100.0
            task_info.result = result
            
            # Update records_processed if available in result
            if result and isinstance(result, dict) and "records_processed" in result:
                task_info.records_processed = result["records_processed"]
            
            # Update DB
            await self._update_db_record(task_info)
            
            logger.info(f"Task completed successfully: {task_id}")
            
        except Exception as e:
            # Update task with error
            task_info.status = IngestionStatus.FAILED
            task_info.completed_at = datetime.utcnow()
            task_info.updated_at = datetime.utcnow()
            task_info.error_message = str(e)
            
            if isinstance(e, PortAdaBaseException):
                task_info.error_message = e.message
                task_info.metadata.update(e.details)
            
            # Update DB
            await self._update_db_record(task_info)
            
            logger.error(f"Task failed: {task_id} - {str(e)}")
        
        finally:
            # Remove from running tasks
            if task_id in self.running_tasks:
                del self.running_tasks[task_id]
            
            # Process next task in queue
            asyncio.create_task(self._process_queue())
    
    async def start_task_processing(self):
        """Start processing tasks from the queue"""
        await self._process_queue()
    
    async def _process_queue(self):
        """Process tasks from the queue"""
        async with self._processing_lock:
            # Check if we can start more tasks
            if len(self.running_tasks) >= self.max_concurrent_tasks:
                return
            
            # Find next task to process
            while self.task_queue and len(self.running_tasks) < self.max_concurrent_tasks:
                task_id = self.task_queue.pop(0)
                task_info = self.tasks.get(task_id)
                
                if not task_info or task_info.status != IngestionStatus.PENDING:
                    continue
                
                # This will be set by the caller when they call execute_task
                # For now, we just mark it as ready to be picked up
                logger.info(f"Task ready for execution: {task_id}")
                break
    
    def get_task_status(self, task_id: str) -> Optional[TaskInfo]:
        """Get task status information"""
        return self.tasks.get(task_id)
    
    def list_tasks(
        self,
        status: Optional[IngestionStatus] = None,
        task_type: Optional[TaskType] = None,
        user_id: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[TaskInfo]:
        """
        List tasks with optional filtering
        
        Args:
            status: Filter by task status
            task_type: Filter by task type
            user_id: Filter by user ID
            limit: Maximum number of tasks to return
            
        Returns:
            List of task information
        """
        tasks = list(self.tasks.values())
        
        # Apply filters
        if status:
            tasks = [t for t in tasks if t.status == status]
        if task_type:
            tasks = [t for t in tasks if t.task_type == task_type]
        if user_id:
            tasks = [t for t in tasks if t.user_id == user_id]
        
        # Sort by creation time (newest first)
        tasks.sort(key=lambda t: t.created_at, reverse=True)
        
        # Apply limit
        if limit:
            tasks = tasks[:limit]
        
        return tasks
    
    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a pending or running task
        
        Args:
            task_id: Task identifier
            
        Returns:
            True if task was cancelled, False otherwise
        """
        task_info = self.tasks.get(task_id)
        if not task_info:
            return False
        
        # Remove from queue if pending
        if task_info.status == IngestionStatus.PENDING and task_id in self.task_queue:
            self.task_queue.remove(task_id)
            task_info.status = IngestionStatus.FAILED
            task_info.error_message = "Task cancelled by user"
            task_info.completed_at = datetime.utcnow()
            task_info.updated_at = datetime.utcnow()
            logger.info(f"Task cancelled: {task_id}")
            return True
        
        # Cancel running task
        if task_info.status == IngestionStatus.PROCESSING and task_id in self.running_tasks:
            running_task = self.running_tasks[task_id]
            running_task.cancel()
            task_info.status = IngestionStatus.FAILED
            task_info.error_message = "Task cancelled by user"
            task_info.completed_at = datetime.utcnow()
            task_info.updated_at = datetime.utcnow()
            logger.info(f"Running task cancelled: {task_id}")
            return True
        
        return False
    
    def cleanup_old_tasks(self, max_age_hours: Optional[int] = None) -> Dict[str, Any]:
        """
        Clean up old completed tasks
        
        Args:
            max_age_hours: Maximum age in hours (default: 24)
            
        Returns:
            Cleanup statistics
        """
        max_age = max_age_hours or self.task_retention_hours
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age)
        
        tasks_to_remove = []
        
        for task_id, task_info in self.tasks.items():
            # Only remove completed or failed tasks
            if task_info.status in [IngestionStatus.COMPLETED, IngestionStatus.FAILED]:
                # Check if task is old enough
                check_time = task_info.completed_at or task_info.created_at
                if check_time < cutoff_time:
                    tasks_to_remove.append(task_id)
        
        # Remove old tasks
        for task_id in tasks_to_remove:
            del self.tasks[task_id]
        
        cleanup_stats = {
            "tasks_removed": len(tasks_to_remove),
            "removed_task_ids": tasks_to_remove,
            "cleanup_time": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Task cleanup completed: {len(tasks_to_remove)} tasks removed")
        return cleanup_stats
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status"""
        return {
            "pending_tasks": len(self.task_queue),
            "running_tasks": len(self.running_tasks),
            "total_tasks": len(self.tasks),
            "max_concurrent": self.max_concurrent_tasks,
            "queue_order": self.task_queue.copy()
        }
    
    def update_task_progress(
        self,
        task_id: str,
        percentage: float,
        step: str = "",
        completed_steps: int = None,
        records_processed: int = None
    ) -> bool:
        """
        Update task progress
        
        Args:
            task_id: Task identifier
            percentage: Progress percentage (0-100)
            step: Current step description
            completed_steps: Number of completed steps
            records_processed: Number of records processed
            
        Returns:
            True if task was updated, False otherwise
        """
        task_info = self.tasks.get(task_id)
        if not task_info:
            return False
        
        task_info.update_progress(percentage, step, completed_steps, records_processed)
        return True


# Global task service instance
task_service = TaskService()