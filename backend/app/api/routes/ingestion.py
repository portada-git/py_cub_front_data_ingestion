"""
Data ingestion API routes
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Optional
import logging
import uuid
import os
import json
import yaml
import aiofiles
from datetime import datetime

from app.models.ingestion import (
    IngestionRequest, IngestionResponse, IngestionStatusResponse,
    IngestionType, FileFormat, FileValidation, IngestionStatus,
    ProcessIsolationStatus
)
from app.services.portada_service import portada_service
from app.services.file_service import file_service
from app.services.task_service import task_service, TaskType, TaskPriority, TaskInfo
from app.core.exceptions import PortAdaBaseException, get_user_friendly_message
from app.api.routes.auth import get_current_user
from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

# Task storage is now handled by task_service
# Remove the old in-memory storage
# active_tasks = {}
# task_queue = []


async def validate_file(file: UploadFile, expected_format: FileFormat) -> FileValidation:
    """Validate uploaded file using file service"""
    return await file_service.validate_file(file, expected_format)


async def save_uploaded_file(file: UploadFile, task_id: str) -> str:
    """Save uploaded file using file service"""
    file_path, metadata = await file_service.save_uploaded_file(file, task_id)
    return file_path


async def process_ingestion_task(task_info: TaskInfo, ingestion_request: IngestionRequest, file_path: str):
    """Background task to process ingestion"""
    try:
        logger.info(f"Starting ingestion task {task_info.task_id}")
        
        # Update progress
        task_service.update_task_progress(task_info.task_id, 10.0, "Initializing ingestion")
        
        if ingestion_request.ingestion_type == IngestionType.EXTRACTION_DATA:
            task_service.update_task_progress(task_info.task_id, 30.0, "Processing extraction data")
            result = await portada_service.ingest_extraction_data(
                file_path=file_path,
                newspaper=ingestion_request.publication,
                data_path_delta_lake=ingestion_request.data_path_delta_lake
            )
        else:  # KNOWN_ENTITIES
            task_service.update_task_progress(task_info.task_id, 30.0, "Processing known entities")
            result = await portada_service.ingest_known_entities(
                file_path=file_path,
                entity_name=ingestion_request.entity_name
            )
        
        task_service.update_task_progress(task_info.task_id, 90.0, "Finalizing ingestion")
        
        # Return result for task completion
        return {
            "success": result["success"],
            "records_processed": result["records_processed"],
            "message": result["message"]
        }
        
    except Exception as e:
        logger.error(f"Error in ingestion task {task_info.task_id}: {e}")
        raise e
    
    finally:
        # Clean up temporary file using file service
        file_service.delete_file(file_path)


@router.post("/upload", response_model=IngestionResponse)
async def upload_data(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    ingestion_type: IngestionType = Form(...),
    publication: Optional[str] = Form(None),
    entity_name: Optional[str] = Form("known_entities"),
    data_path_delta_lake: Optional[str] = Form("ship_entries"),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload and ingest data file
    
    Supports both extraction data (JSON) and known entities (YAML) ingestion.
    """
    try:
        # Create ingestion request
        ingestion_request = IngestionRequest(
            ingestion_type=ingestion_type,
            publication=publication,
            entity_name=entity_name,
            data_path_delta_lake=data_path_delta_lake
        )
        
        # Determine expected file format
        if ingestion_type == IngestionType.EXTRACTION_DATA:
            expected_format = FileFormat.JSON
        else:
            expected_format = FileFormat.YAML
        
        # Validate file
        file_validation = await validate_file(file, expected_format)
        
        if not file_validation.is_valid:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "File validation failed",
                    "errors": file_validation.validation_errors
                }
            )
        
        # Save uploaded file
        file_path = await save_uploaded_file(file, str(uuid.uuid4()))
        
        # Create task using task service
        task_title = f"{ingestion_type.value.title()} Ingestion"
        task_description = f"Ingesting {file.filename} as {ingestion_type.value}"
        
        task_id = task_service.create_task(
            task_type=TaskType.INGESTION,
            title=task_title,
            description=task_description,
            priority=TaskPriority.NORMAL,
            metadata={
                "ingestion_type": ingestion_type.value,
                "filename": file.filename,
                "file_size": file_validation.file_size,
                "publication": publication,
                "entity_name": entity_name
            },
            user_id=current_user["username"]
        )
        
        # Start background processing
        background_tasks.add_task(
            task_service.execute_task,
            task_id,
            process_ingestion_task,
            ingestion_request,
            file_path
        )
        
        logger.info(f"Created ingestion task {task_id} for user {current_user['username']}")
        
        return IngestionResponse(
            task_id=task_id,
            status=IngestionStatus.PENDING,
            message="File uploaded successfully, ingestion started",
            records_processed=0,
            started_at=datetime.utcnow(),
            file_validation=file_validation
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in upload endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/status/{task_id}", response_model=IngestionStatusResponse)
async def get_ingestion_status(
    task_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get status of an ingestion task"""
    task_info = task_service.get_task_status(task_id)
    if not task_info:
        raise HTTPException(
            status_code=404,
            detail=f"Task {task_id} not found"
        )
    
    # Get records processed from result if available
    records_processed = 0
    if task_info.result and "records_processed" in task_info.result:
        records_processed = task_info.result["records_processed"]
    
    return IngestionStatusResponse(
        task_id=task_id,
        status=task_info.status,
        message=task_info.error_message or task_info.current_step or task_info.description,
        progress_percentage=task_info.progress_percentage,
        records_processed=records_processed,
        started_at=task_info.started_at or task_info.created_at,
        updated_at=task_info.updated_at or task_info.created_at
    )


@router.get("/process-status", response_model=ProcessIsolationStatus)
async def get_process_status(current_user: dict = Depends(get_current_user)):
    """Get current process isolation status"""
    # Get queue status from task service
    queue_status = task_service.get_queue_status()
    
    # Get processing tasks
    processing_tasks = task_service.list_tasks(status=IngestionStatus.PROCESSING, task_type=TaskType.INGESTION)
    current_task = processing_tasks[0] if processing_tasks else None
    
    return ProcessIsolationStatus(
        is_processing=len(processing_tasks) > 0,
        current_task_id=current_task.task_id if current_task else None,
        current_ingestion_type=current_task.metadata.get("ingestion_type") if current_task else None,
        queue_length=queue_status["pending_tasks"],
        estimated_wait_time=None  # Could implement estimation logic
    )


@router.get("/tasks")
async def list_tasks(
    status: Optional[IngestionStatus] = None,
    current_user: dict = Depends(get_current_user)
):
    """List ingestion tasks (optionally filtered by status)"""
    tasks = task_service.list_tasks(
        status=status,
        task_type=TaskType.INGESTION,
        user_id=current_user["username"]
    )
    
    # Convert to dict format for response
    task_dicts = [task.to_dict() for task in tasks]
    
    return {
        "tasks": task_dicts,
        "total": len(task_dicts)
    }


@router.post("/cleanup")
async def cleanup_files(
    max_age_hours: Optional[int] = 24,
    current_user: dict = Depends(get_current_user)
):
    """Clean up old temporary files (admin only)"""
    try:
        # Check admin permission
        from app.services.auth_service import auth_service
        auth_service.require_permission(current_user, "admin")
        
        # Perform cleanup
        cleanup_stats = file_service.cleanup_old_files(max_age_hours)
        
        logger.info(f"File cleanup performed by {current_user['username']}")
        return cleanup_stats
        
    except Exception as e:
        logger.error(f"Error during file cleanup: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Cleanup failed: {str(e)}"
        )


@router.get("/files")
async def list_upload_files(current_user: dict = Depends(get_current_user)):
    """List files in upload folder (admin only)"""
    try:
        # Check admin permission
        from app.services.auth_service import auth_service
        auth_service.require_permission(current_user, "admin")
        
        files = file_service.list_upload_folder_contents()
        
        return {
            "files": files,
            "total_files": len(files),
            "upload_folder": settings.INGESTION_FOLDER
        }
        
    except Exception as e:
        logger.error(f"Error listing upload files: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error listing files: {str(e)}"
        )


@router.post("/tasks/cleanup")
async def cleanup_tasks(
    max_age_hours: Optional[int] = 24,
    current_user: dict = Depends(get_current_user)
):
    """Clean up old completed tasks (admin only)"""
    try:
        # Check admin permission
        from app.services.auth_service import auth_service
        auth_service.require_permission(current_user, "admin")
        
        # Perform task cleanup
        cleanup_stats = task_service.cleanup_old_tasks(max_age_hours)
        
        logger.info(f"Task cleanup performed by {current_user['username']}")
        return cleanup_stats
        
    except Exception as e:
        logger.error(f"Error during task cleanup: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Task cleanup failed: {str(e)}"
        )


@router.delete("/tasks/{task_id}")
async def cancel_task(
    task_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Cancel a pending or running task"""
    try:
        # Get task info to check ownership
        task_info = task_service.get_task_status(task_id)
        if not task_info:
            raise HTTPException(
                status_code=404,
                detail=f"Task {task_id} not found"
            )
        
        # Check if user owns the task or is admin
        from app.services.auth_service import auth_service
        if (task_info.user_id != current_user["username"] and 
            not auth_service.check_permission(current_user, "admin")):
            raise HTTPException(
                status_code=403,
                detail="You can only cancel your own tasks"
            )
        
        # Cancel the task
        success = task_service.cancel_task(task_id)
        
        if success:
            logger.info(f"Task {task_id} cancelled by {current_user['username']}")
            return {"message": f"Task {task_id} cancelled successfully", "success": True}
        else:
            return {"message": f"Task {task_id} could not be cancelled (may already be completed)", "success": False}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling task {task_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error cancelling task: {str(e)}"
        )


@router.get("/queue-status")
async def get_queue_status(current_user: dict = Depends(get_current_user)):
    """Get detailed queue status (admin only)"""
    try:
        # Check admin permission
        from app.services.auth_service import auth_service
        auth_service.require_permission(current_user, "admin")
        
        queue_status = task_service.get_queue_status()
        
        return queue_status
        
    except Exception as e:
        logger.error(f"Error getting queue status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting queue status: {str(e)}"
        )