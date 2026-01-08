"""
Data analysis routes
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List

from app.models.analysis import (
    MissingDatesRequest, MissingDatesResponse,
    DuplicatesRequest, DuplicatesResponse, DuplicateDetail,
    StorageMetadataRequest, StorageMetadataResponse, FieldLineage,
    ProcessMetadataRequest, ProcessMetadataResponse
)
from app.services.portada_service import portada_service

router = APIRouter()

@router.post("/missing-dates", response_model=MissingDatesResponse)
async def get_missing_dates(request: MissingDatesRequest):
    """
    Get missing dates from a newspaper publication
    
    Supports two modes:
    1. File mode: Provide date_and_edition_list (YAML, JSON, or plain text)
    2. Date range mode: Provide start_date and/or end_date
    """
    try:
        missing_dates = await portada_service.get_missing_dates(
            publication_name=request.publication_name,
            start_date=request.start_date,
            end_date=request.end_date,
            date_and_edition_list=request.date_and_edition_list
        )
        
        return MissingDatesResponse(
            success=True,
            publication_name=request.publication_name,
            missing_dates=missing_dates,
            total_missing=len(missing_dates)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting missing dates: {str(e)}"
        )

@router.post("/duplicates", response_model=DuplicatesResponse)
async def get_duplicates(request: DuplicatesRequest):
    """
    Get duplicates metadata with optional filters
    """
    try:
        duplicates_metadata = await portada_service.get_duplicates_metadata(
            user_responsible=request.user_responsible,
            publication=request.publication,
            start_date=request.start_date,
            end_date=request.end_date
        )
        
        return DuplicatesResponse(
            success=True,
            duplicates_metadata=duplicates_metadata,
            total_records=len(duplicates_metadata)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting duplicates: {str(e)}"
        )

@router.get("/duplicates/{log_id}/details", response_model=List[DuplicateDetail])
async def get_duplicate_details(
    log_id: str,
    duplicates_filter: str = Query(..., description="Filter string for duplicates"),
    duplicate_ids: str = Query(..., description="Comma-separated list of duplicate IDs")
):
    """
    Get detailed duplicate records for a specific log entry
    """
    try:
        duplicate_ids_list = [id.strip() for id in duplicate_ids.split(",")]
        
        duplicate_details = await portada_service.get_duplicate_details(
            duplicates_filter=duplicates_filter,
            duplicate_ids=duplicate_ids_list
        )
        
        return duplicate_details
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting duplicate details: {str(e)}"
        )

@router.post("/storage-metadata", response_model=StorageMetadataResponse)
async def get_storage_metadata(request: StorageMetadataRequest):
    """
    Get storage metadata (always filtered by stage = 0)
    """
    try:
        storage_records = await portada_service.get_storage_metadata(
            table_name=request.table_name,
            process=request.process
        )
        
        return StorageMetadataResponse(
            success=True,
            storage_records=storage_records,
            total_records=len(storage_records)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting storage metadata: {str(e)}"
        )

@router.get("/storage-metadata/{log_id}/lineage", response_model=List[FieldLineage])
async def get_field_lineage(log_id: str):
    """
    Get field lineage for a specific storage log
    """
    try:
        field_lineage = await portada_service.get_field_lineage(log_id)
        return field_lineage
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting field lineage: {str(e)}"
        )

@router.post("/process-metadata", response_model=ProcessMetadataResponse)
async def get_process_metadata(request: ProcessMetadataRequest):
    """
    Get process metadata (always filtered by stage = 0)
    """
    try:
        process_records = await portada_service.get_process_metadata(
            process_name=request.process_name
        )
        
        return ProcessMetadataResponse(
            success=True,
            process_records=process_records,
            total_records=len(process_records)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting process metadata: {str(e)}"
        )