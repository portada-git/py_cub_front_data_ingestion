"""
Enhanced upload endpoint with improved error handling and database integration
"""

import uuid
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, Request, Response
from fastapi.responses import JSONResponse

from ..routes.auth import get_current_user
from ...storage import StorageService
from ...database import DatabaseService
from ...session import SessionManager, SessionCleanupService
from ...services.enhanced_file_handler import EnhancedFileHandler
from ...services.concurrent_upload_manager import ConcurrentUploadManager
from ...services.entity_validator import EnhancedEntityValidator
from ...core.config import settings
from ...core.exceptions import PortAdaBaseException
from ...core.session_middleware import get_session_id, get_current_session

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize services (these would typically be dependency injected)
storage_service = StorageService()
database_service = DatabaseService()
session_manager = SessionManager(database_service)
session_cleanup_service = SessionCleanupService(database_service, session_manager)
enhanced_file_handler = EnhancedFileHandler(storage_service, database_service)
concurrent_upload_manager = ConcurrentUploadManager(enhanced_file_handler)
entity_validator = EnhancedEntityValidator()


async def get_or_create_session(request: Request, response: Response) -> str:
    """Get session ID from middleware or create fallback"""
    try:
        # Try to get session ID from middleware
        session_id = get_session_id(request)
        if session_id:
            return session_id
        
        # Fallback: create session using session manager
        session = await session_manager.create_or_get_session(request, response)
        return session.id
    except Exception as e:
        logger.error(f"Error managing session: {e}")
        # Final fallback: generate UUID
        return str(uuid.uuid4())


@router.post("/enhanced-upload")
async def enhanced_upload(
    request: Request,
    response: Response,
    file: UploadFile = File(...),
    ingestion_type: Optional[str] = Form("extraction_data"),
    publication: Optional[str] = Form(None),
    entity_name: Optional[str] = Form("known_entities"),
    data_path_delta_lake: Optional[str] = Form("ship_entries"),
    current_user: dict = Depends(get_current_user)
):
    """
    Enhanced upload endpoint with comprehensive error handling and database integration.
    
    Features:
    - Automatic directory creation
    - Database persistence
    - Session management
    - Concurrent upload handling
    - Comprehensive error handling
    - Entity validation
    """
    upload_start_time = datetime.utcnow()
    
    try:
        # Get or create session
        session_id = await get_or_create_session(request, response)
        
        # Validate basic requirements
        if not file or not file.filename:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "File is required",
                    "error_code": "FILE_REQUIRED",
                    "details": {"message": "Please select a file to upload"},
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        
        # Log upload attempt
        logger.info(f"Enhanced upload request from user {current_user['username']}: "
                   f"{ingestion_type} ingestion for file {file.filename} "
                   f"(size: {file.size} bytes, session: {session_id})")
        
        # Create task ID for tracking
        task_id = str(uuid.uuid4())
        
        # Prepare metadata
        upload_metadata = {
            "user_id": current_user["username"],
            "ingestion_type": ingestion_type,
            "publication": publication,
            "entity_name": entity_name,
            "data_path_delta_lake": data_path_delta_lake,
            "upload_start_time": upload_start_time.isoformat(),
            "client_ip": _get_client_ip(request),
            "user_agent": request.headers.get("user-agent")
        }
        
        # Submit to concurrent upload manager
        queued = await concurrent_upload_manager.submit_upload(
            task_id=task_id,
            session_id=session_id,
            file=file,
            metadata=upload_metadata
        )
        
        if not queued:
            return JSONResponse(
                status_code=503,
                content={
                    "success": False,
                    "error": "Upload queue is full",
                    "error_code": "QUEUE_FULL",
                    "details": {
                        "message": "The upload queue is currently full. Please try again in a few moments.",
                        "retry_after_seconds": 30
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        
        # Return immediate response with task tracking
        response_data = {
            "success": True,
            "task_id": task_id,
            "session_id": session_id,
            "status": "queued",
            "message": f"File '{file.filename}' queued for processing",
            "file_info": {
                "filename": file.filename,
                "size": file.size,
                "content_type": file.content_type
            },
            "processing_info": {
                "ingestion_type": ingestion_type,
                "publication": publication,
                "entity_name": entity_name
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Upload queued successfully: task_id={task_id}, session_id={session_id}")
        return JSONResponse(content=response_data)
        
    except PortAdaBaseException as e:
        logger.error(f"PortAda error in enhanced upload: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Processing error",
                "error_code": e.error_code,
                "details": e.details,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    except Exception as e:
        logger.error(f"Unexpected error in enhanced upload: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Internal server error",
                "error_code": "INTERNAL_ERROR",
                "details": {
                    "message": "An unexpected error occurred while processing your upload",
                    "error": str(e)
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.get("/upload/status/{task_id}")
async def get_upload_status(
    task_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get status of an upload task"""
    try:
        status = await concurrent_upload_manager.get_upload_status(task_id)
        
        if not status:
            return JSONResponse(
                status_code=404,
                content={
                    "success": False,
                    "error": "Task not found",
                    "error_code": "TASK_NOT_FOUND",
                    "details": {"task_id": task_id},
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        
        # Validate and transform the status using entity validator
        validated_status = entity_validator.sanitize_entity(status)
        
        return JSONResponse(content={
            "success": True,
            "task_status": validated_status,
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting upload status for task {task_id}: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Status retrieval failed",
                "error_code": "STATUS_ERROR",
                "details": {"error": str(e)},
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.get("/upload/session/{session_id}")
async def get_session_uploads(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get all uploads for a specific session"""
    try:
        uploads = await concurrent_upload_manager.get_session_uploads(session_id)
        
        # Validate and transform uploads using entity validator
        validated_uploads = entity_validator.transform_for_frontend(uploads) if uploads else []
        
        return JSONResponse(content={
            "success": True,
            "session_id": session_id,
            "uploads": validated_uploads,
            "total_uploads": len(validated_uploads),
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting session uploads for {session_id}: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Session uploads retrieval failed",
                "error_code": "SESSION_ERROR",
                "details": {"error": str(e)},
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.get("/upload/manager/stats")
async def get_upload_manager_stats(
    current_user: dict = Depends(get_current_user)
):
    """Get upload manager statistics (admin only)"""
    try:
        # Check admin permission (simplified check)
        if not current_user.get("is_admin", False):
            return JSONResponse(
                status_code=403,
                content={
                    "success": False,
                    "error": "Admin access required",
                    "error_code": "INSUFFICIENT_PERMISSIONS",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        
        stats = await concurrent_upload_manager.get_manager_stats()
        
        # Validate and sanitize stats
        validated_stats = entity_validator.sanitize_entity(stats)
        
        return JSONResponse(content={
            "success": True,
            "manager_stats": validated_stats,
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting upload manager stats: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Stats retrieval failed",
                "error_code": "STATS_ERROR",
                "details": {"error": str(e)},
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.post("/upload/cleanup")
async def cleanup_uploads(
    max_age_hours: Optional[int] = 24,
    current_user: dict = Depends(get_current_user)
):
    """Clean up old upload records and files (admin only)"""
    try:
        # Check admin permission
        if not current_user.get("is_admin", False):
            return JSONResponse(
                status_code=403,
                content={
                    "success": False,
                    "error": "Admin access required",
                    "error_code": "INSUFFICIENT_PERMISSIONS",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        
        # Cleanup completed uploads from memory
        memory_cleaned = await concurrent_upload_manager.cleanup_completed_uploads(max_age_hours)
        
        # Cleanup failed uploads and orphaned files
        file_cleanup = await enhanced_file_handler.cleanup_failed_uploads(max_age_hours)
        
        # Cleanup expired sessions
        sessions_cleaned = await session_cleanup_service.run_cleanup()
        
        cleanup_summary = {
            "memory_records_cleaned": memory_cleaned,
            "file_cleanup_stats": file_cleanup,
            "session_cleanup_stats": sessions_cleaned,
            "max_age_hours": max_age_hours,
            "cleanup_timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Upload cleanup performed by {current_user['username']}: {cleanup_summary}")
        
        return JSONResponse(content={
            "success": True,
            "cleanup_summary": cleanup_summary,
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error during upload cleanup: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Cleanup failed",
                "error_code": "CLEANUP_ERROR",
                "details": {"error": str(e)},
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.get("/health")
async def health_check():
    """Health check endpoint for the enhanced upload system"""
    try:
        # Check database health
        db_health = await database_service.health_check()
        
        # Check storage health
        storage_info = storage_service.get_storage_info()
        
        # Check upload manager health
        manager_stats = await concurrent_upload_manager.get_manager_stats()
        
        health_status = {
            "status": "healthy" if db_health["status"] == "healthy" and storage_info["exists"] else "unhealthy",
            "database": db_health,
            "storage": {
                "exists": storage_info["exists"],
                "writable": storage_info["writable"],
                "free_space_mb": storage_info["free_space_mb"]
            },
            "upload_manager": {
                "is_running": manager_stats["is_running"],
                "active_uploads": manager_stats["current_active_uploads"],
                "queue_size": manager_stats["current_queue_size"]
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        status_code = 200 if health_status["status"] == "healthy" else 503
        
        return JSONResponse(
            status_code=status_code,
            content=health_status
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )


def _get_client_ip(request: Request) -> Optional[str]:
    """Get client IP address from request"""
    try:
        # Check for forwarded headers (proxy/load balancer)
        forwarded_for = request.headers.get('x-forwarded-for')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        # Check for real IP header
        real_ip = request.headers.get('x-real-ip')
        if real_ip:
            return real_ip
        
        # Fall back to direct connection
        if hasattr(request, 'client') and request.client:
            return request.client.host
        
        return None
        
    except Exception:
        return None


# Startup and shutdown events for the upload manager
@router.on_event("startup")
async def startup_upload_services():
    """Initialize upload services on startup"""
    try:
        # Initialize database
        await database_service.initialize()
        
        # Start upload manager
        await concurrent_upload_manager.start()
        
        # Start session cleanup service
        await session_cleanup_service.start_cleanup_scheduler()
        
        logger.info("Enhanced upload services started successfully")
        
    except Exception as e:
        logger.error(f"Failed to start upload services: {e}")
        raise


@router.on_event("shutdown")
async def shutdown_upload_services():
    """Cleanup upload services on shutdown"""
    try:
        # Stop session cleanup service
        await session_cleanup_service.stop_cleanup_scheduler()
        
        # Stop upload manager
        await concurrent_upload_manager.stop()
        
        # Close database connections
        await database_service.close()
        
        logger.info("Enhanced upload services stopped successfully")
        
    except Exception as e:
        logger.error(f"Error stopping upload services: {e}")