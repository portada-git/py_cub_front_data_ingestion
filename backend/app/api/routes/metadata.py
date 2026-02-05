"""
Metadata API routes
Provides endpoints for accessing storage, process, and field lineage metadata
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
import logging
from datetime import datetime

from app.api.routes.auth import get_current_user
from app.models.analysis import (
    StorageMetadataRequest, StorageMetadataResponse,
    ProcessMetadataRequest, ProcessMetadataResponse,
    FieldLineageResponse, StorageRecord, FieldLineage
)
from app.services.portada_service import portada_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/storage", response_model=StorageMetadataResponse)
async def get_storage_metadata_get(
    publication: Optional[str] = Query(None, description="Filter by publication"),
    table_name: Optional[str] = Query(None, description="Filter by table name"),
    process_name: Optional[str] = Query(None, description="Filter by process name"),
    stage: int = Query(0, description="Filter by stage (default 0)"),
    start_date: Optional[str] = Query(None, description="Start date filter (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date filter (YYYY-MM-DD)"),
    current_user: dict = Depends(get_current_user)
):
    """Get storage metadata with optional filtering"""
    try:
        logger.info(f"Getting storage metadata - table: {table_name}, stage: {stage}")
        
        # Get real data from PortAda service
        storage_records = await portada_service.get_storage_metadata(
            table_name=table_name,
            process_name=process_name,
            stage=stage
        )
        
        return {
            "storage_records": storage_records,
            "total_records": len(storage_records),
            "filters_applied": {
                "publication": publication,
                "table_name": table_name,
                "process_name": process_name,
                "stage": stage,
                "start_date": start_date,
                "end_date": end_date
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting storage metadata: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving storage metadata: {str(e)}")


@router.get("/process")
async def get_process_metadata_get(
    publication: Optional[str] = Query(None, description="Filter by publication"),
    process_name: Optional[str] = Query(None, description="Filter by process name"),
    status: Optional[str] = Query(None, description="Filter by status"),
    start_date: Optional[str] = Query(None, description="Start date filter (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date filter (ISO format)"),
    current_user: dict = Depends(get_current_user)
):
    """Get process metadata with optional filtering - GET endpoint for compatibility"""
    try:
        logger.info(f"Getting process metadata - publication: {publication}")
        
        # Mock data for now - in production, integrate with process_log
        process_records = [
            {
                "process_log_id": f"process_{i}_{publication or 'all'}",
                "publication_name": publication or f"Publication_{i}",
                "process_name": process_name or f"data_ingestion_{i}",
                "status": status or ("completed" if i % 3 != 0 else "failed"),
                "records_processed": 1000 + i * 150,
                "records_failed": 0 if i % 3 != 0 else 5,
                "started_at": datetime.utcnow().isoformat(),
                "completed_at": datetime.utcnow().isoformat(),
                "duration_seconds": 120 + i * 10,
                "metadata": {
                    "input_files": [f"input_{i}.json"],
                    "output_tables": [f"ship_entries_{i}"],
                    "transformations_applied": ["clean_text", "extract_entities", "validate_dates"]
                }
            }
            for i in range(1, 11)
        ]
        
        return {
            "process_records": process_records,
            "total_records": len(process_records),
            "filters_applied": {
                "publication": publication,
                "process_name": process_name,
                "status": status,
                "start_date": start_date,
                "end_date": end_date
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting process metadata: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving process metadata: {str(e)}")


@router.get("/lineage", response_model=FieldLineageResponse)
async def get_field_lineage_get(
    stored_log_id: str = Query(..., description="Filter by storage log identifier"),
    current_user: dict = Depends(get_current_user)
):
    """Get field lineage metadata for a specific storage record"""
    try:
        logger.info(f"Getting field lineage for log_id: {stored_log_id}")
        
        # Get real data from PortAda service
        field_lineages = await portada_service.get_field_lineage(stored_log_id)
        
        return {
            "log_id": stored_log_id,
            "field_lineages": field_lineages,
            "total_fields": len(field_lineages)
        }
        
    except Exception as e:
        logger.error(f"Error getting field lineage: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving field lineage: {str(e)}")


@router.get("/publications")
async def get_metadata_publications(
    current_user: dict = Depends(get_current_user)
):
    """Get list of publications that have metadata available"""
    try:
        logger.info("Getting publications with metadata")
        
        # In production, this would query the actual metadata tables
        publications = [
            {
                "publication_name": "DM",
                "display_name": "Diario de la Marina",
                "storage_records": 150,
                "process_records": 45,
                "lineage_records": 300,
                "last_updated": datetime.utcnow().isoformat()
            },
            {
                "publication_name": "Semanario Mercantil",
                "display_name": "Semanario Mercantil",
                "storage_records": 89,
                "process_records": 23,
                "lineage_records": 178,
                "last_updated": datetime.utcnow().isoformat()
            },
            {
                "publication_name": "Diario de Barcelona",
                "display_name": "Diario de Barcelona",
                "storage_records": 234,
                "process_records": 67,
                "lineage_records": 468,
                "last_updated": datetime.utcnow().isoformat()
            }
        ]
        
        return {
            "publications": publications,
            "total_publications": len(publications)
        }
        
    except Exception as e:
        logger.error(f"Error getting metadata publications: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving publications: {str(e)}")


@router.get("/summary")
async def get_metadata_summary(
    current_user: dict = Depends(get_current_user)
):
    """Get overall metadata summary statistics"""
    try:
        logger.info("Getting metadata summary")
        
        summary = {
            "total_storage_records": 473,
            "total_process_records": 135,
            "total_lineage_records": 946,
            "publications_count": 3,
            "last_ingestion": datetime.utcnow().isoformat(),
            "storage_size_gb": 2.4,
            "avg_processing_time_minutes": 8.5,
            "success_rate_percentage": 94.2
        }
        
        return summary
        
    except Exception as e:
        logger.error(f"Error getting metadata summary: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving summary: {str(e)}")