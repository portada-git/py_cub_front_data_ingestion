"""
Data ingestion routes
"""

import os
import uuid
import tempfile
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from typing import Optional
import aiofiles

from app.models.ingestion import (
    IngestionType, IngestionRequest, IngestionResponse, IngestionStatus
)
from app.services.portada_service import portada_service

router = APIRouter()

# In-memory task storage (use Redis or database in production)
ingestion_tasks = {}

async def process_ingestion_task(task_id: str, file_path: str, ingestion_type: IngestionType, newspaper: Optional[str] = None):
    """Background task for processing ingestion"""
    try:
        ingestion_tasks[task_id]["status"] = "processing"
        ingestion_tasks[task_id]["progress"] = 10
        
        if ingestion_type == IngestionType.EXTRACTION:
            result = await portada_service.ingest_extraction_data(file_path, newspaper=newspaper)
        else:  # KNOWN_ENTITIES
            result = await portada_service.ingest_known_entities(file_path)
        
        if result["success"]:
            ingestion_tasks[task_id]["status"] = "completed"
            ingestion_tasks[task_id]["progress"] = 100
            ingestion_tasks[task_id]["records_processed"] = result["records_processed"]
            ingestion_tasks[task_id]["message"] = result["message"]
        else:
            ingestion_tasks[task_id]["status"] = "failed"
            ingestion_tasks[task_id]["error_details"] = result["message"]
            
    except Exception as e:
        ingestion_tasks[task_id]["status"] = "failed"
        ingestion_tasks[task_id]["error_details"] = str(e)
    
    finally:
        # Clean up temporary file
        if os.path.exists(file_path):
            os.remove(file_path)

@router.post("/upload", response_model=IngestionResponse)
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    ingestion_type: IngestionType = Form(...),
    newspaper: Optional[str] = Form(None)
):
    """
    Upload and process a file for ingestion
    
    Args:
        file: The file to upload (JSON/YAML)
        ingestion_type: Type of ingestion (extraction or known_entities)
        newspaper: Newspaper identifier (required for extraction type)
    """
    # Validate file type
    allowed_extensions = {".json", ".yml", ".yaml"}
    file_extension = os.path.splitext(file.filename)[1].lower()
    
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Validate newspaper parameter for extraction type
    if ingestion_type == IngestionType.EXTRACTION and not newspaper:
        raise HTTPException(
            status_code=400,
            detail="Newspaper parameter is required for extraction type ingestion"
        )
    
    # Create temporary file
    task_id = str(uuid.uuid4())
    temp_dir = tempfile.gettempdir()
    temp_file_path = os.path.join(temp_dir, f"{task_id}_{file.filename}")
    
    try:
        # Save uploaded file
        async with aiofiles.open(temp_file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        # Initialize task status
        ingestion_tasks[task_id] = {
            "status": "pending",
            "progress": 0,
            "message": "File uploaded successfully, processing started",
            "records_processed": 0,
            "error_details": None
        }
        
        # Start background processing
        background_tasks.add_task(
            process_ingestion_task, 
            task_id, 
            temp_file_path, 
            ingestion_type,
            newspaper
        )
        
        return IngestionResponse(
            success=True,
            message="File uploaded successfully. Processing started in background.",
            task_id=task_id
        )
        
    except Exception as e:
        # Clean up on error
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        
        raise HTTPException(
            status_code=500,
            detail=f"Error processing file: {str(e)}"
        )

@router.get("/status/{task_id}", response_model=IngestionStatus)
async def get_ingestion_status(task_id: str):
    """
    Get the status of an ingestion task
    """
    if task_id not in ingestion_tasks:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )
    
    task_data = ingestion_tasks[task_id]
    
    return IngestionStatus(
        task_id=task_id,
        status=task_data["status"],
        progress=task_data["progress"],
        message=task_data["message"],
        records_processed=task_data["records_processed"],
        error_details=task_data["error_details"]
    )