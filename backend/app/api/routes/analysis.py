"""
Data analysis API routes
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from typing import Optional, List
import logging
import os
import json
import yaml
from datetime import datetime

from app.models.analysis import (
    MissingDatesRequest, MissingDatesResponse, MissingDateEntry,
    DuplicatesRequest, DuplicatesResponse, DuplicateDetailsResponse,
    StorageMetadataRequest, StorageMetadataResponse, FieldLineageResponse,
    ProcessMetadataRequest, ProcessMetadataResponse,
    PendingFilesRequest, PendingFilesResponse, KnownEntitiesResponse,
    DailyEntriesRequest, DailyEntriesResponse
)
from app.services.portada_service import portada_service
from app.core.exceptions import PortAdaBaseException, get_user_friendly_message
from app.api.routes.auth import get_current_user
from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/pending-files", response_model=PendingFilesResponse)
async def get_pending_files(
    publication: Optional[str] = None,
    username: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Get count of pending files in ingestion folder
    
    Filters by publication and username if provided.
    """
    try:
        logger.info(f"Getting pending files - publication: {publication}, username: {username}")
        
        pending_files = []
        total_files = 0
        
        # Scan ingestion folder for pending files
        if os.path.exists(settings.INGESTION_FOLDER):
            for filename in os.listdir(settings.INGESTION_FOLDER):
                file_path = os.path.join(settings.INGESTION_FOLDER, filename)
                if os.path.isfile(file_path):
                    # Extract metadata from filename or file content
                    file_info = {
                        "filename": filename,
                        "size": os.path.getsize(file_path),
                        "created_at": datetime.fromtimestamp(os.path.getctime(file_path)).isoformat(),
                        "publication": publication or "unknown",  # Mock data
                        "username": username or "unknown"  # Mock data
                    }
                    
                    # Apply filters
                    if publication and file_info["publication"] != publication:
                        continue
                    if username and file_info["username"] != username:
                        continue
                    
                    pending_files.append(file_info)
                    total_files += 1
        
        return PendingFilesResponse(
            pending_files=pending_files,
            total_files=total_files,
            filters_applied={
                "publication": publication,
                "username": username
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting pending files: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving pending files: {str(e)}")


@router.get("/known-entities", response_model=KnownEntitiesResponse)
async def get_known_entities(current_user: dict = Depends(get_current_user)):
    """Get list of known entities from PortAda library"""
    try:
        logger.info("Getting known entities")
        
        # Mock implementation - in production, integrate with PortAda library
        entities = [
            {"name": "person", "type": "PERSON", "count": 150},
            {"name": "organization", "type": "ORG", "count": 89},
            {"name": "location", "type": "LOC", "count": 234},
            {"name": "date", "type": "DATE", "count": 567}
        ]
        
        entity_types = list(set(entity["type"] for entity in entities))
        
        return KnownEntitiesResponse(
            entities=entities,
            total_entities=len(entities),
            entity_types=entity_types
        )
        
    except Exception as e:
        logger.error(f"Error getting known entities: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving known entities: {str(e)}")


@router.post("/daily-entries", response_model=DailyEntriesResponse)
async def get_daily_entries(
    request: DailyEntriesRequest,
    current_user: dict = Depends(get_current_user)
):
    """Get daily entry counts for a publication"""
    try:
        logger.info(f"Getting daily entries for publication: {request.publication}")
        
        # Mock implementation - in production, integrate with PortAda BoatFactIngestion
        daily_counts = []
        total_entries = 0
        
        # Generate mock data for the date range
        if request.start_date and request.end_date:
            start = datetime.strptime(request.start_date, '%Y-%m-%d')
            end = datetime.strptime(request.end_date, '%Y-%m-%d')
            
            current_date = start
            while current_date <= end:
                count = 45 + (hash(current_date.strftime('%Y-%m-%d')) % 50)  # Mock count
                daily_counts.append({
                    "date": current_date.strftime('%Y-%m-%d'),
                    "count": count,
                    "publication": request.publication
                })
                total_entries += count
                current_date = current_date.replace(day=current_date.day + 1)
        
        return DailyEntriesResponse(
            publication=request.publication,
            daily_counts=daily_counts,
            total_entries=total_entries,
            date_range={
                "start_date": request.start_date or "N/A",
                "end_date": request.end_date or "N/A"
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting daily entries: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving daily entries: {str(e)}")


@router.post("/missing-dates", response_model=MissingDatesResponse)
async def get_missing_dates(
    request: MissingDatesRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Get missing dates for a publication
    
    Supports both file-based queries (with uploaded date lists) and date range queries.
    """
    try:
        logger.info(f"Getting missing dates for publication: {request.publication_name}")
        
        # Determine query type
        query_type = "date-range" if request.start_date or request.end_date else "file-based"
        
        # Get missing dates using PortAda service
        missing_dates = await portada_service.get_missing_dates(
            publication_name=request.publication_name,
            data_path=request.data_path,
            start_date=request.start_date,
            end_date=request.end_date
        )
        
        # Determine date range analyzed
        date_range_analyzed = None
        if request.start_date or request.end_date:
            date_range_analyzed = f"{request.start_date or 'earliest'} to {request.end_date or 'latest'}"
        
        return MissingDatesResponse(
            publication_name=request.publication_name,
            query_type=query_type,
            missing_dates=missing_dates,
            total_missing=len(missing_dates),
            date_range_analyzed=date_range_analyzed
        )
        
    except PortAdaBaseException as e:
        logger.error(f"PortAda service error: {e}")
        raise HTTPException(
            status_code=500, 
            detail=get_user_friendly_message(e)
        )
    except Exception as e:
        logger.error(f"Error getting missing dates: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving missing dates: {str(e)}")


@router.post("/duplicates", response_model=DuplicatesResponse)
async def get_duplicates(
    request: DuplicatesRequest,
    current_user: dict = Depends(get_current_user)
):
    """Get duplicates metadata with optional filtering"""
    try:
        logger.info("Getting duplicates metadata")
        
        # Get duplicates using PortAda service
        duplicates = await portada_service.get_duplicates_metadata(
            user_responsible=request.user_responsible,
            publication=request.publication,
            start_date=request.start_date,
            end_date=request.end_date
        )
        
        return DuplicatesResponse(
            duplicates=duplicates,
            total_duplicates=len(duplicates),
            filters_applied={
                "user_responsible": request.user_responsible,
                "publication": request.publication,
                "start_date": request.start_date,
                "end_date": request.end_date
            }
        )
        
    except PortAdaBaseException as e:
        logger.error(f"PortAda service error: {e}")
        raise HTTPException(
            status_code=500, 
            detail=get_user_friendly_message(e)
        )
    except Exception as e:
        logger.error(f"Error getting duplicates: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving duplicates: {str(e)}")


@router.get("/duplicates/{log_id}/details", response_model=DuplicateDetailsResponse)
async def get_duplicate_details(
    log_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get detailed information about specific duplicates"""
    try:
        logger.info(f"Getting duplicate details for log_id: {log_id}")
        
        # Mock implementation - in production, integrate with PortAda duplicates_records log
        duplicate_details = [
            {
                "record_id": f"rec_{i}",
                "title": f"Sample Article {i}",
                "content_hash": f"hash_{i}",
                "similarity_score": 0.95 - (i * 0.05),
                "metadata": {"source": "newspaper", "section": "news"}
            }
            for i in range(1, 6)
        ]
        
        return DuplicateDetailsResponse(
            log_id=log_id,
            duplicate_details=duplicate_details,
            total_records=len(duplicate_details)
        )
        
    except Exception as e:
        logger.error(f"Error getting duplicate details: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving duplicate details: {str(e)}")


@router.post("/storage-metadata", response_model=StorageMetadataResponse)
async def get_storage_metadata(
    request: StorageMetadataRequest,
    current_user: dict = Depends(get_current_user)
):
    """Get storage metadata with filtering"""
    try:
        logger.info("Getting storage metadata")
        
        # Mock implementation - in production, integrate with DataLakeMetadataManager
        storage_records = [
            {
                "log_id": f"storage_{i}",
                "table_name": request.table_name or f"table_{i}",
                "process_name": request.process_name or f"process_{i}",
                "stage": request.stage,
                "records_stored": 1000 + i * 100,
                "storage_path": f"/data/tables/table_{i}",
                "created_at": datetime.utcnow().isoformat(),
                "metadata": {"format": "parquet", "compression": "snappy"}
            }
            for i in range(1, 6)
        ]
        
        return StorageMetadataResponse(
            storage_records=storage_records,
            total_records=len(storage_records),
            filters_applied={
                "table_name": request.table_name,
                "process_name": request.process_name,
                "stage": request.stage,
                "start_date": request.start_date,
                "end_date": request.end_date
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting storage metadata: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving storage metadata: {str(e)}")


@router.get("/storage-metadata/{log_id}/lineage", response_model=FieldLineageResponse)
async def get_field_lineage(
    log_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get field lineage information for a storage log"""
    try:
        logger.info(f"Getting field lineage for log_id: {log_id}")
        
        # Mock implementation - in production, integrate with field_lineage_log
        field_lineages = [
            {
                "field_name": f"field_{i}",
                "source_table": f"source_table_{i}",
                "target_table": f"target_table_{i}",
                "transformation": f"transform_{i}",
                "lineage_path": [f"source_table_{i}", f"intermediate_{i}", f"target_table_{i}"]
            }
            for i in range(1, 4)
        ]
        
        return FieldLineageResponse(
            log_id=log_id,
            field_lineages=field_lineages,
            total_fields=len(field_lineages)
        )
        
    except Exception as e:
        logger.error(f"Error getting field lineage: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving field lineage: {str(e)}")


@router.post("/process-metadata", response_model=ProcessMetadataResponse)
async def get_process_metadata(
    request: ProcessMetadataRequest,
    current_user: dict = Depends(get_current_user)
):
    """Get process metadata with filtering"""
    try:
        logger.info("Getting process metadata")
        
        # Mock implementation - in production, integrate with process_log
        process_records = [
            {
                "log_id": f"process_{i}",
                "process_name": request.process_name or f"process_{i}",
                "stage": request.stage,
                "status": "completed",
                "started_at": datetime.utcnow().isoformat(),
                "completed_at": datetime.utcnow().isoformat(),
                "records_processed": 500 + i * 50,
                "metadata": {"cpu_time": f"{i}m", "memory_used": f"{i}GB"}
            }
            for i in range(1, 6)
        ]
        
        return ProcessMetadataResponse(
            process_records=process_records,
            total_records=len(process_records),
            filters_applied={
                "process_name": request.process_name,
                "stage": request.stage,
                "start_date": request.start_date,
                "end_date": request.end_date
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting process metadata: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving process metadata: {str(e)}")


@router.post("/missing-dates/upload")
async def upload_dates_file(
    file: UploadFile = File(...),
    publication_name: str = Form(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload a file containing dates for missing dates analysis
    
    Supports JSON, YAML, and plain text formats.
    """
    try:
        logger.info(f"Uploading dates file for publication: {publication_name}")
        
        # Read and validate file content
        content = await file.read()
        file_extension = file.filename.split('.')[-1].lower()
        
        dates_list = []
        
        if file_extension == 'json':
            data = json.loads(content.decode('utf-8'))
            if isinstance(data, list):
                dates_list = data
            else:
                dates_list = [data]
        elif file_extension in ['yaml', 'yml']:
            data = yaml.safe_load(content.decode('utf-8'))
            if isinstance(data, list):
                dates_list = data
            else:
                dates_list = [data]
        elif file_extension == 'txt':
            dates_list = content.decode('utf-8').strip().split('\n')
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format")
        
        # Process the dates and get missing dates
        # This would integrate with PortAda library in production
        missing_dates = []  # Mock result
        
        return {
            "message": f"Successfully processed {len(dates_list)} dates",
            "dates_processed": len(dates_list),
            "missing_dates_found": len(missing_dates),
            "publication": publication_name
        }
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format")
    except yaml.YAMLError:
        raise HTTPException(status_code=400, detail="Invalid YAML format")
    except Exception as e:
        logger.error(f"Error processing dates file: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")