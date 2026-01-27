"""
History API endpoint for processing records and upload history
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Request, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from ..routes.auth import get_current_user
from ...database import DatabaseService
from ...services.entity_validator import EnhancedEntityValidator
from ...core.session_middleware import get_session_id, get_current_session
from ...core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize services
database_service = DatabaseService()
entity_validator = EnhancedEntityValidator()


class HistoryFilters(BaseModel):
    """Filters for history queries"""
    status: Optional[str] = Field(None, description="Filter by processing status")
    filename: Optional[str] = Field(None, description="Filter by filename (partial match)")
    date_from: Optional[str] = Field(None, description="Start date in ISO format")
    date_to: Optional[str] = Field(None, description="End date in ISO format")
    file_type: Optional[str] = Field(None, description="Filter by file type")


class HistoryResponse(BaseModel):
    """Response model for history queries"""
    success: bool
    session_id: str
    records: List[Dict[str, Any]]
    pagination: Dict[str, Any]
    filters_applied: Dict[str, Any]
    summary: Dict[str, Any]
    timestamp: str


@router.get("/history", response_model=HistoryResponse)
async def get_processing_history(
    request: Request,
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(50, ge=1, le=200, description="Number of records per page"),
    status: Optional[str] = Query(None, description="Filter by processing status"),
    filename: Optional[str] = Query(None, description="Filter by filename (partial match)"),
    date_from: Optional[str] = Query(None, description="Start date in ISO format"),
    date_to: Optional[str] = Query(None, description="End date in ISO format"),
    file_type: Optional[str] = Query(None, description="Filter by file type"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get processing history for the current session with filtering and pagination.
    
    Features:
    - Session-scoped data retrieval
    - Comprehensive filtering options
    - Pagination support
    - Entity validation and transformation
    - Summary statistics
    """
    try:
        # Get session ID from middleware
        session_id = get_session_id(request)
        if not session_id:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "Session not found",
                    "error_code": "SESSION_REQUIRED",
                    "message": "A valid session is required to access processing history",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        
        # Initialize database if needed
        if not database_service._initialized:
            await database_service.initialize()
        
        # Build filters
        filters = {}
        if status:
            filters['status'] = status
        if filename:
            filters['filename'] = filename
        if date_from:
            try:
                # Validate date format
                datetime.fromisoformat(date_from.replace('Z', '+00:00'))
                filters['date_from'] = date_from
            except ValueError:
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "error": "Invalid date format",
                        "error_code": "INVALID_DATE_FORMAT",
                        "message": f"date_from must be in ISO format, got: {date_from}",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
        if date_to:
            try:
                # Validate date format
                datetime.fromisoformat(date_to.replace('Z', '+00:00'))
                filters['date_to'] = date_to
            except ValueError:
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "error": "Invalid date format",
                        "error_code": "INVALID_DATE_FORMAT",
                        "message": f"date_to must be in ISO format, got: {date_to}",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
        
        logger.info(f"History request for session {session_id}: page={page}, page_size={page_size}, filters={filters}")
        
        # Get processing history from database
        records, total_count = await database_service.get_processing_history(
            session_id=session_id,
            filters=filters,
            page=page,
            page_size=page_size
        )
        
        # Validate and transform records for frontend
        validated_records = entity_validator.validate_and_transform_batch(
            records, 
            entity_type='processing_record',
            apply_filters=True
        )
        
        # Apply additional filtering if file_type is specified
        if file_type and validated_records:
            validated_records = [
                record for record in validated_records
                if record.get('metadata', {}).get('file_type', '').lower() == file_type.lower()
            ]
        
        # Calculate pagination info
        total_pages = (total_count + page_size - 1) // page_size
        has_next = page < total_pages
        has_prev = page > 1
        
        pagination_info = {
            "current_page": page,
            "page_size": page_size,
            "total_records": total_count,
            "total_pages": total_pages,
            "has_next_page": has_next,
            "has_previous_page": has_prev,
            "next_page": page + 1 if has_next else None,
            "previous_page": page - 1 if has_prev else None
        }
        
        # Generate summary statistics
        summary = _generate_history_summary(validated_records, total_count)
        
        # Prepare response
        response_data = {
            "success": True,
            "session_id": session_id,
            "records": validated_records,
            "pagination": pagination_info,
            "filters_applied": filters,
            "summary": summary,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"History response for session {session_id}: {len(validated_records)} records, {total_count} total")
        return JSONResponse(content=response_data)
        
    except Exception as e:
        logger.error(f"Error getting processing history: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "History retrieval failed",
                "error_code": "HISTORY_ERROR",
                "message": "An error occurred while retrieving processing history",
                "details": {"error": str(e)},
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.get("/history/summary")
async def get_history_summary(
    request: Request,
    days: int = Query(30, ge=1, le=365, description="Number of days to include in summary"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get summary statistics for processing history.
    
    Provides aggregated statistics for the specified time period.
    """
    try:
        # Get session ID from middleware
        session_id = get_session_id(request)
        if not session_id:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "Session not found",
                    "error_code": "SESSION_REQUIRED",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        
        # Initialize database if needed
        if not database_service._initialized:
            await database_service.initialize()
        
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get records for the time period
        filters = {
            'date_from': start_date.isoformat(),
            'date_to': end_date.isoformat()
        }
        
        records, total_count = await database_service.get_processing_history(
            session_id=session_id,
            filters=filters,
            page=1,
            page_size=1000  # Get all records for summary
        )
        
        # Validate records
        validated_records = entity_validator.validate_and_transform_batch(
            records, 
            entity_type='processing_record',
            apply_filters=True
        )
        
        # Generate comprehensive summary
        summary = _generate_comprehensive_summary(validated_records, days)
        
        response_data = {
            "success": True,
            "session_id": session_id,
            "summary": summary,
            "period_days": days,
            "date_range": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return JSONResponse(content=response_data)
        
    except Exception as e:
        logger.error(f"Error getting history summary: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Summary retrieval failed",
                "error_code": "SUMMARY_ERROR",
                "details": {"error": str(e)},
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.get("/history/record/{record_id}")
async def get_processing_record_details(
    record_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """
    Get detailed information about a specific processing record.
    """
    try:
        # Get session ID for security check
        session_id = get_session_id(request)
        if not session_id:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "Session not found",
                    "error_code": "SESSION_REQUIRED",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        
        # Initialize database if needed
        if not database_service._initialized:
            await database_service.initialize()
        
        # Get the processing record
        record = await database_service.get_processing_record_by_id(record_id)
        
        if not record:
            return JSONResponse(
                status_code=404,
                content={
                    "success": False,
                    "error": "Record not found",
                    "error_code": "RECORD_NOT_FOUND",
                    "message": f"Processing record {record_id} not found",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        
        # Security check: ensure record belongs to current session
        if record.session_id != session_id:
            return JSONResponse(
                status_code=403,
                content={
                    "success": False,
                    "error": "Access denied",
                    "error_code": "ACCESS_DENIED",
                    "message": "You can only access records from your current session",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        
        # Validate and transform record
        validated_record = entity_validator.validate_processing_record(record)
        
        # Get associated file metadata if available
        file_metadata = None
        try:
            # This would require a method to get file metadata by processing record ID
            # For now, we'll include it in the record metadata
            pass
        except Exception as e:
            logger.debug(f"No file metadata found for record {record_id}: {e}")
        
        response_data = {
            "success": True,
            "session_id": session_id,
            "record": validated_record,
            "file_metadata": file_metadata,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return JSONResponse(content=response_data)
        
    except Exception as e:
        logger.error(f"Error getting processing record details {record_id}: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Record retrieval failed",
                "error_code": "RECORD_ERROR",
                "details": {"error": str(e)},
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.delete("/history/record/{record_id}")
async def delete_processing_record(
    record_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a specific processing record (soft delete).
    """
    try:
        # Get session ID for security check
        session_id = get_session_id(request)
        if not session_id:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "Session not found",
                    "error_code": "SESSION_REQUIRED",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        
        # Initialize database if needed
        if not database_service._initialized:
            await database_service.initialize()
        
        # Get the processing record first
        record = await database_service.get_processing_record_by_id(record_id)
        
        if not record:
            return JSONResponse(
                status_code=404,
                content={
                    "success": False,
                    "error": "Record not found",
                    "error_code": "RECORD_NOT_FOUND",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        
        # Security check: ensure record belongs to current session
        if record.session_id != session_id:
            return JSONResponse(
                status_code=403,
                content={
                    "success": False,
                    "error": "Access denied",
                    "error_code": "ACCESS_DENIED",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        
        # Mark as cancelled/deleted (soft delete)
        success = await database_service.update_processing_status(
            record_id, 
            "cancelled", 
            "Deleted by user"
        )
        
        if success:
            logger.info(f"Processing record {record_id} deleted by user {current_user['username']}")
            return JSONResponse(content={
                "success": True,
                "message": f"Processing record {record_id} deleted successfully",
                "timestamp": datetime.utcnow().isoformat()
            })
        else:
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": "Delete failed",
                    "error_code": "DELETE_FAILED",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        
    except Exception as e:
        logger.error(f"Error deleting processing record {record_id}: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Delete operation failed",
                "error_code": "DELETE_ERROR",
                "details": {"error": str(e)},
                "timestamp": datetime.utcnow().isoformat()
            }
        )


def _generate_history_summary(records: List[Dict[str, Any]], total_count: int) -> Dict[str, Any]:
    """Generate summary statistics for history records"""
    try:
        if not records:
            return {
                "total_records": total_count,
                "records_in_page": 0,
                "status_counts": {},
                "file_types": {},
                "average_file_size": 0,
                "total_file_size": 0
            }
        
        # Count by status
        status_counts = {}
        file_types = {}
        total_size = 0
        
        for record in records:
            # Status counts
            status = record.get('processing_status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
            
            # File types
            file_type = record.get('metadata', {}).get('file_type', 'unknown')
            file_types[file_type] = file_types.get(file_type, 0) + 1
            
            # File sizes
            file_size = record.get('file_size', 0)
            if isinstance(file_size, (int, float)):
                total_size += file_size
        
        average_size = total_size / len(records) if records else 0
        
        return {
            "total_records": total_count,
            "records_in_page": len(records),
            "status_counts": status_counts,
            "file_types": file_types,
            "average_file_size": round(average_size, 2),
            "total_file_size": total_size
        }
        
    except Exception as e:
        logger.error(f"Error generating history summary: {e}")
        return {
            "total_records": total_count,
            "records_in_page": len(records) if records else 0,
            "error": str(e)
        }


def _generate_comprehensive_summary(records: List[Dict[str, Any]], days: int) -> Dict[str, Any]:
    """Generate comprehensive summary statistics"""
    try:
        if not records:
            return {
                "total_records": 0,
                "period_days": days,
                "daily_average": 0,
                "status_distribution": {},
                "file_type_distribution": {},
                "size_statistics": {},
                "processing_times": {}
            }
        
        # Basic counts
        total_records = len(records)
        daily_average = total_records / days if days > 0 else 0
        
        # Status distribution
        status_counts = {}
        file_types = {}
        file_sizes = []
        processing_times = []
        
        for record in records:
            # Status distribution
            status = record.get('processing_status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
            
            # File type distribution
            file_type = record.get('metadata', {}).get('file_type', 'unknown')
            file_types[file_type] = file_types.get(file_type, 0) + 1
            
            # File sizes
            file_size = record.get('file_size', 0)
            if isinstance(file_size, (int, float)) and file_size > 0:
                file_sizes.append(file_size)
            
            # Processing times
            duration = record.get('processing_duration_seconds')
            if isinstance(duration, (int, float)) and duration > 0:
                processing_times.append(duration)
        
        # Calculate size statistics
        size_stats = {}
        if file_sizes:
            size_stats = {
                "min_size": min(file_sizes),
                "max_size": max(file_sizes),
                "average_size": sum(file_sizes) / len(file_sizes),
                "total_size": sum(file_sizes)
            }
        
        # Calculate processing time statistics
        time_stats = {}
        if processing_times:
            time_stats = {
                "min_time": min(processing_times),
                "max_time": max(processing_times),
                "average_time": sum(processing_times) / len(processing_times)
            }
        
        return {
            "total_records": total_records,
            "period_days": days,
            "daily_average": round(daily_average, 2),
            "status_distribution": status_counts,
            "file_type_distribution": file_types,
            "size_statistics": size_stats,
            "processing_times": time_stats
        }
        
    except Exception as e:
        logger.error(f"Error generating comprehensive summary: {e}")
        return {
            "total_records": len(records) if records else 0,
            "period_days": days,
            "error": str(e)
        }


@router.get("/session/info")
async def get_session_info(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """
    Get detailed information about the current session.
    """
    try:
        # Get session information from middleware
        session_info = get_current_session(request)
        session_id = session_info.get("session_id")
        
        if not session_id:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "Session not found",
                    "error_code": "SESSION_REQUIRED",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        
        # Initialize database if needed
        if not database_service._initialized:
            await database_service.initialize()
        
        # Get session details from database
        session = await database_service.get_session_by_id(session_id)
        
        if not session:
            return JSONResponse(
                status_code=404,
                content={
                    "success": False,
                    "error": "Session not found in database",
                    "error_code": "SESSION_NOT_FOUND",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        
        # Validate and transform session data
        validated_session = entity_validator.validate_session(session)
        
        # Get session statistics
        session_stats = await _get_session_statistics(session_id)
        
        response_data = {
            "success": True,
            "session": validated_session,
            "statistics": session_stats,
            "is_new_session": session_info.get("is_new_session", False),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return JSONResponse(content=response_data)
        
    except Exception as e:
        logger.error(f"Error getting session info: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Session info retrieval failed",
                "error_code": "SESSION_INFO_ERROR",
                "details": {"error": str(e)},
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.post("/session/extend")
async def extend_session(
    request: Request,
    days: int = Query(30, ge=1, le=365, description="Number of days to extend session"),
    current_user: dict = Depends(get_current_user)
):
    """
    Extend the current session expiration time.
    """
    try:
        session_id = get_session_id(request)
        if not session_id:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "Session not found",
                    "error_code": "SESSION_REQUIRED",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        
        # Initialize database if needed
        if not database_service._initialized:
            await database_service.initialize()
        
        # Get session manager (we'll need to initialize it)
        from ...session import SessionManager
        session_manager = SessionManager(database_service)
        
        # Extend session
        success = await session_manager.extend_session(session_id, days)
        
        if success:
            return JSONResponse(content={
                "success": True,
                "message": f"Session extended by {days} days",
                "session_id": session_id,
                "extended_days": days,
                "timestamp": datetime.utcnow().isoformat()
            })
        else:
            return JSONResponse(
                status_code=404,
                content={
                    "success": False,
                    "error": "Session not found",
                    "error_code": "SESSION_NOT_FOUND",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        
    except Exception as e:
        logger.error(f"Error extending session: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Session extension failed",
                "error_code": "SESSION_EXTEND_ERROR",
                "details": {"error": str(e)},
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.delete("/session/clear")
async def clear_session_history(
    request: Request,
    confirm: bool = Query(False, description="Confirmation flag to prevent accidental deletion"),
    current_user: dict = Depends(get_current_user)
):
    """
    Clear all processing history for the current session.
    """
    try:
        if not confirm:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "Confirmation required",
                    "error_code": "CONFIRMATION_REQUIRED",
                    "message": "Add ?confirm=true to confirm deletion of all session history",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        
        session_id = get_session_id(request)
        if not session_id:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "Session not found",
                    "error_code": "SESSION_REQUIRED",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        
        # Initialize database if needed
        if not database_service._initialized:
            await database_service.initialize()
        
        # Get all records for this session first (for logging)
        records, total_count = await database_service.get_processing_history(
            session_id=session_id,
            filters={},
            page=1,
            page_size=1000
        )
        
        # Mark all records as cancelled (soft delete)
        deleted_count = 0
        for record in records:
            success = await database_service.update_processing_status(
                record.id, 
                "cancelled", 
                "Cleared by user"
            )
            if success:
                deleted_count += 1
        
        logger.info(f"Session history cleared for {session_id}: {deleted_count} records marked as cancelled")
        
        return JSONResponse(content={
            "success": True,
            "message": f"Session history cleared successfully",
            "session_id": session_id,
            "records_cleared": deleted_count,
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error clearing session history: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "History clear failed",
                "error_code": "CLEAR_ERROR",
                "details": {"error": str(e)},
                "timestamp": datetime.utcnow().isoformat()
            }
        )


async def _get_session_statistics(session_id: str) -> Dict[str, Any]:
    """Get statistics for a specific session"""
    try:
        # Get all records for this session
        records, total_count = await database_service.get_processing_history(
            session_id=session_id,
            filters={},
            page=1,
            page_size=1000  # Get all records for stats
        )
        
        if not records:
            return {
                "total_uploads": 0,
                "successful_uploads": 0,
                "failed_uploads": 0,
                "pending_uploads": 0,
                "total_file_size": 0,
                "average_file_size": 0,
                "file_types": {},
                "first_upload": None,
                "last_upload": None
            }
        
        # Calculate statistics
        status_counts = {"completed": 0, "failed": 0, "processing": 0, "uploaded": 0, "cancelled": 0}
        file_types = {}
        total_size = 0
        upload_times = []
        
        for record in records:
            # Status counts
            status = record.processing_status
            if status in status_counts:
                status_counts[status] += 1
            
            # File types (from metadata if available)
            file_type = "unknown"
            if hasattr(record, 'record_metadata') and record.record_metadata:
                file_type = record.record_metadata.get('file_type', 'unknown')
            file_types[file_type] = file_types.get(file_type, 0) + 1
            
            # File sizes
            if record.file_size:
                total_size += record.file_size
            
            # Upload times
            if record.upload_timestamp:
                upload_times.append(record.upload_timestamp)
        
        # Calculate averages and ranges
        average_size = total_size / len(records) if records else 0
        first_upload = min(upload_times) if upload_times else None
        last_upload = max(upload_times) if upload_times else None
        
        return {
            "total_uploads": total_count,
            "successful_uploads": status_counts["completed"],
            "failed_uploads": status_counts["failed"],
            "pending_uploads": status_counts["processing"] + status_counts["uploaded"],
            "cancelled_uploads": status_counts["cancelled"],
            "total_file_size": total_size,
            "average_file_size": round(average_size, 2),
            "file_types": file_types,
            "first_upload": first_upload.isoformat() if first_upload else None,
            "last_upload": last_upload.isoformat() if last_upload else None
        }
        
    except Exception as e:
        logger.error(f"Error getting session statistics: {e}")
        return {
            "error": str(e),
            "total_uploads": 0
        }