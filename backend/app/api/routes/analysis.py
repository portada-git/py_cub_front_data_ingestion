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
    KnownEntitiesResponse,
    DailyEntriesRequest, DailyEntriesResponse
)
from app.services.portada_service import portada_service
from app.core.exceptions import PortAdaBaseException, get_user_friendly_message
from app.api.routes.auth import get_current_user
from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/publications", response_model=dict)
async def get_publications(current_user: dict = Depends(get_current_user)):
    """Get list of available publications from processed data"""
    try:
        logger.info("Getting available publications")
        
        # Try to get publications from PortAda data
        try:
            # This would query the actual data to get unique publications
            # For now, return the known publications based on the system
            publications = [
                {"code": "db", "name": "Diario de Barcelona", "full_name": "Diario de Barcelona"},
                {"code": "dm", "name": "Diario de la Marina", "full_name": "Diario de la Marina"},
                {"code": "sm", "name": "Le semaphore de Marseille", "full_name": "Le semaphore de Marseille"},
                {"code": "gm", "name": "Gaceta Mercantil", "full_name": "Gaceta Mercantil"},
                {"code": "bp", "name": "British Packet", "full_name": "British Packet"},
                {"code": "en", "name": "El Nacional", "full_name": "El Nacional"},
                {"code": "lp", "name": "La Prensa", "full_name": "La Prensa"}
            ]
            
            return {
                "publications": publications,
                "total": len(publications)
            }
            
        except Exception as e:
            logger.warning(f"Could not get publications from PortAda: {e}")
            # Return default publications
            return {
                "publications": [
                    {"code": "db", "name": "Diario de Barcelona", "full_name": "Diario de Barcelona"},
                    {"code": "dm", "name": "Diario de la Marina", "full_name": "Diario de la Marina"},
                    {"code": "sm", "name": "Semanario Mercantil", "full_name": "Semanario Mercantil"}
                ],
                "total": 3
            }
            
    except Exception as e:
        logger.error(f"Error getting publications: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving publications: {str(e)}")


@router.get("/known-entities", response_model=KnownEntitiesResponse)
async def get_known_entities(current_user: dict = Depends(get_current_user)):
    """Get list of known entities from PortAda library"""
    try:
        logger.info("Getting known entities")
        
        # Try to get real data from PortAda service
        try:
            # Use PortAda service to get real entities data
            layer_entities = portada_service._get_entities_layer()
            
            # This would be the real implementation with PortAda library
            # For now, we'll use enhanced mock data that looks more realistic
            entities = []
            
            # Check if there are any uploaded entity files
            entities_folder = os.path.join(settings.PORTADA_BASE_PATH, "known_entities")
            if os.path.exists(entities_folder):
                for filename in os.listdir(entities_folder):
                    if filename.endswith(('.yaml', '.yml', '.json')):
                        file_path = os.path.join(entities_folder, filename)
                        file_stat = os.stat(file_path)
                        
                        # Extract entity type from filename
                        entity_name = filename.split('.')[0]
                        entity_type = "ENTITY"
                        
                        # Try to determine type from filename
                        if "person" in entity_name.lower():
                            entity_type = "PERSON"
                        elif "org" in entity_name.lower() or "company" in entity_name.lower():
                            entity_type = "ORG"
                        elif "loc" in entity_name.lower() or "place" in entity_name.lower():
                            entity_type = "LOC"
                        elif "date" in entity_name.lower():
                            entity_type = "DATE"
                        
                        # Try to count entities in file
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                if filename.endswith('.json'):
                                    data = json.load(f)
                                    count = len(data) if isinstance(data, list) else len(data.keys()) if isinstance(data, dict) else 1
                                else:
                                    data = yaml.safe_load(f)
                                    count = len(data) if isinstance(data, list) else len(data.keys()) if isinstance(data, dict) else 1
                        except:
                            count = 1
                        
                        entities.append({
                            "name": entity_name,
                            "type": entity_type,
                            "count": count
                        })
            
            # If no real files found, provide some realistic sample data
            if not entities:
                entities = [
                    {"name": "flag", "type": "nacionalidad", "count": 0},
                    {"name": "comodity", "type": "mercancias", "count": 0},
                    {"name": "ship_type", "type": "tipos de barcos", "count": 0},
                    {"name": "unit", "type": "unidades de medida", "count": 0},
                    {"name": "port", "type": "puertos", "count": 0},
                    {"name": "master_role", "type": "roles maestros", "count": 0}
                ]
            
        except Exception as e:
            logger.warning(f"Could not get real entities data: {e}, using fallback data")
            # Fallback to enhanced mock data
            entities = [
                {"name": "flag", "type": "nacionalidad", "count": 0},
                {"name": "comodity", "type": "mercancias", "count": 0},
                {"name": "ship_type", "type": "tipos de barcos", "count": 0},
                {"name": "unit", "type": "unidades de medida", "count": 0}
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
    """Get daily entry counts for a publication from real data"""
    try:
        logger.info(f"Getting daily entries for publication: {request.publication}")
        
        # Get real data from PortAda service
        try:
            layer_news = portada_service._get_news_layer()
            
            # Read real data from ship_entries table
            df = layer_news.read_raw_data("ship_entries")
            
            # Filter by publication (case-insensitive)
            publication_upper = request.publication.upper()
            df_filtered = df.filter(f"UPPER(publication_name) = '{publication_upper}'")
            
            # If dates provided, filter by date range
            if request.start_date and request.end_date:
                df_filtered = df_filtered.filter(
                    f"publication_date >= '{request.start_date}' AND publication_date <= '{request.end_date}'"
                )
                logger.info(f"Filtering by date range: {request.start_date} to {request.end_date}")
            
            # Group by publication_date and count entries
            from pyspark.sql import functions as F
            daily_df = df_filtered.groupBy("publication_date").agg(
                F.count("*").alias("count")
            ).orderBy("publication_date")
            
            # Collect results
            daily_results = daily_df.collect()
            
            daily_counts = []
            total_entries = 0
            
            for row in daily_results:
                date_str = row["publication_date"]
                count = row["count"]
                
                daily_counts.append({
                    "date": date_str,
                    "count": count,
                    "publication": request.publication
                })
                total_entries += count
            
            # Determine actual date range from data
            if daily_counts:
                actual_start_date = daily_counts[0]["date"]
                actual_end_date = daily_counts[-1]["date"]
            else:
                actual_start_date = request.start_date or "N/A"
                actual_end_date = request.end_date or "N/A"
            
            logger.info(f"Found {len(daily_counts)} days with {total_entries} total entries for {request.publication}")
            
        except Exception as e:
            logger.error(f"Error getting real daily entries data: {e}")
            import traceback
            traceback.print_exc()
            raise HTTPException(
                status_code=500,
                detail=f"Error querying daily entries from database: {str(e)}"
            )
        
        return DailyEntriesResponse(
            publication=request.publication,
            daily_counts=daily_counts,
            total_entries=total_entries,
            date_range={
                "start_date": actual_start_date,
                "end_date": actual_end_date
            }
        )
        
    except HTTPException:
        raise
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
            end_date=request.end_date,
            date_and_edition_list=request.date_and_edition_list
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