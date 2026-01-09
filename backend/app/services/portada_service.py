"""
Service layer for PortAda library integration
"""

import os
import json
import yaml
from typing import Optional, List, Dict, Any
from datetime import datetime
import asyncio
import aiofiles

# PortAda library imports
from portada_data_layer import PortadaBuilder, DataLakeMetadataManager

from app.core.config import settings
from app.models.ingestion import IngestionType
from app.models.analysis import (
    MissingDateEntry, DuplicateRecord, DuplicateDetail,
    StorageRecord, FieldLineage, ProcessRecord
)


class PortAdaService:
    """Service for interacting with PortAda library"""
    
    # Layer type constants from PortadaBuilder
    NEWS_TYPE = "news"
    KNOWN_ENTITIES_TYPE = "known_entities"
    
    def __init__(self):
        self.base_path = settings.PORTADA_BASE_PATH
        self.app_name = settings.PORTADA_APP_NAME
        self.project_name = settings.PORTADA_PROJECT_NAME
        self._builder = None
        self._layer_news = None
        self._layer_entities = None
        self._metadata_manager = None
    
    def _get_builder(self) -> PortadaBuilder:
        """Get or create PortAda builder instance"""
        if self._builder is None:
            self._builder = (
                PortadaBuilder()
                .protocol("file://")
                .base_path(self.base_path)
                .app_name(self.app_name)
                .project_name(self.project_name)
            )
        return self._builder
    
    def _get_news_layer(self):
        """Get or create news layer instance"""
        if self._layer_news is None:
            builder = self._get_builder()
            self._layer_news = builder.build(builder.NEWS_TYPE)
            self._layer_news.start_session()
        return self._layer_news
    
    def _get_entities_layer(self):
        """Get or create entities layer instance"""
        if self._layer_entities is None:
            builder = self._get_builder()
            self._layer_entities = builder.build(builder.KNOWN_ENTITIES_TYPE)
            self._layer_entities.start_session()
        return self._layer_entities
    
    def _get_metadata_manager(self) -> DataLakeMetadataManager:
        """Get or create metadata manager instance"""
        if self._metadata_manager is None:
            layer_news = self._get_news_layer()
            self._metadata_manager = DataLakeMetadataManager(layer_news.get_configuration())
        return self._metadata_manager

    async def ingest_extraction_data(self, file_path: str, data_path_delta_lake: str = "ship_entries") -> Dict[str, Any]:
        """
        Ingest extraction data from JSON file
        
        Args:
            file_path: Path to the JSON file
            data_path_delta_lake: Destination path in delta lake
            
        Returns:
            Dictionary with ingestion results
        """
        try:
            layer_news = self._get_news_layer()
            
            # Count records before ingestion
            async with aiofiles.open(file_path, 'r') as f:
                content = await f.read()
                data = json.loads(content)
                record_count = len(data) if isinstance(data, list) else 1
            
            # Perform ingestion using PortAda library
            # Note: This operation may delete the source file
            layer_news.ingest(data_path_delta_lake, local_path=file_path)
            
            return {
                "success": True,
                "records_processed": record_count,
                "message": f"Successfully ingested {record_count} records to {data_path_delta_lake}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "records_processed": 0,
                "message": f"Error during ingestion: {str(e)}"
            }
    
    async def ingest_known_entities(self, file_path: str, entity_name: str = "known_entities") -> Dict[str, Any]:
        """
        Ingest known entities from YAML file
        
        Args:
            file_path: Path to the YAML file
            entity_name: Name for the entity in delta lake
            
        Returns:
            Dictionary with ingestion results
        """
        try:
            layer_entities = self._get_entities_layer()
            
            # Count entities before ingestion
            async with aiofiles.open(file_path, 'r') as f:
                content = await f.read()
                data = yaml.safe_load(content)
                entity_count = len(data) if isinstance(data, (list, dict)) else 1
            
            # Perform entity ingestion using PortAda library
            data, dest = layer_entities.copy_ingested_entities(entity=entity_name, local_path=file_path)
            odata = {"source_path": dest, "data": data}
            layer_entities.save_raw_entities(entity=entity_name, data=odata)
            
            return {
                "success": True,
                "records_processed": entity_count,
                "message": f"Successfully ingested {entity_count} entities as {entity_name}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "records_processed": 0,
                "message": f"Error during entity ingestion: {str(e)}"
            }
    
    async def get_missing_dates(
        self, 
        publication_name: str,
        data_path: str = "ship_entries",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        date_and_edition_list: Optional[str] = None
    ) -> List[MissingDateEntry]:
        """
        Get missing dates from a newspaper
        
        Args:
            publication_name: Name of the publication (e.g., "db", "dm", "sm")
            data_path: Path to the data in delta lake
            start_date: Start date in YYYY-MM-DD format (optional)
            end_date: End date in YYYY-MM-DD format (optional)
            date_and_edition_list: List of dates and editions to check (optional)
            
        Returns:
            List of missing date entries
        """
        try:
            layer_news = self._get_news_layer()
            
            # Get missing dates using PortAda library
            missing_dates_result = layer_news.get_missing_dates_from_a_newspaper(
                data_path,
                publication_name=publication_name
            )
            
            # Convert results to our model format
            missing_dates = []
            if missing_dates_result:
                for item in missing_dates_result:
                    missing_dates.append(MissingDateEntry(
                        date=str(item.get('date', '')),
                        edition=str(item.get('edition', 'U')),
                        gap_duration=str(item.get('gap_duration', ''))
                    ))
            
            return missing_dates
            
        except Exception as e:
            raise Exception(f"Error getting missing dates: {str(e)}")

    async def get_duplicates_metadata(
        self,
        user_responsible: Optional[str] = None,
        publication: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[DuplicateRecord]:
        """
        Get duplicates metadata
        
        Returns:
            List of duplicate records with metadata
        """
        try:
            metadata = self._get_metadata_manager()
            
            # Read duplicates log from PortAda
            df_dup = metadata.read_log("duplicates_log")
            
            # Apply filters
            if publication:
                df_dup = df_dup.filter(f"lower(publication)='{publication.lower()}'")
            if start_date:
                df_dup = df_dup.filter(f"date >= '{start_date}'")
            if end_date:
                df_dup = df_dup.filter(f"date <= '{end_date}'")
            
            # Collect results
            results = df_dup.collect()
            
            # Convert to our model format
            duplicates = []
            for row in results:
                duplicates.append(DuplicateRecord(
                    log_id=str(row.get('log_id', '')),
                    date=str(row.get('date', '')),
                    edition=str(row.get('edition', '')),
                    publication=str(row.get('publication', '')),
                    uploaded_by=str(row.get('uploaded_by', user_responsible or '')),
                    duplicate_count=int(row.get('duplicate_count', 0)),
                    duplicates_filter=str(row.get('duplicates_filter', '')),
                    duplicate_ids=row.get('duplicate_ids', [])
                ))
            
            return duplicates
            
        except Exception as e:
            raise Exception(f"Error getting duplicates metadata: {str(e)}")
    
    async def get_duplicate_details(self, duplicates_filter: str, duplicate_ids: List[str]) -> List[DuplicateDetail]:
        """
        Get detailed duplicate records
        
        Args:
            duplicates_filter: Filter string for duplicates
            duplicate_ids: List of duplicate entry IDs
            
        Returns:
            List of detailed duplicate records
        """
        try:
            metadata = self._get_metadata_manager()
            
            # Read duplicate records from PortAda
            df_duplicates = metadata.read_log("duplicates_records")
            
            # Apply filters
            filtered_df = df_duplicates.filter(duplicates_filter)
            if duplicate_ids:
                filtered_df = filtered_df.filter(filtered_df.entry_id.isin(duplicate_ids))
            
            # Collect results
            results = filtered_df.collect()
            
            # Convert to our model format
            details = []
            for row in results:
                details.append(DuplicateDetail(
                    entry_id=str(row.get('entry_id', '')),
                    content=str(row.get('content', '')),
                    similarity_score=float(row.get('similarity_score', 0.0))
                ))
            
            return details
            
        except Exception as e:
            raise Exception(f"Error getting duplicate details: {str(e)}")
    
    async def get_storage_metadata(
        self,
        table_name: Optional[str] = None,
        process: Optional[str] = None
    ) -> List[StorageRecord]:
        """
        Get storage metadata (always filtered by stage = 0)
        
        Returns:
            List of storage records
        """
        try:
            metadata = self._get_metadata_manager()
            
            # Read storage log from PortAda
            df_storage = metadata.read_log("storage_log")
            
            # Always filter by stage = 0
            df_storage = df_storage.filter("stage == 0")
            
            # Apply additional filters
            if table_name:
                df_storage = df_storage.filter(f"table_name = '{table_name}'")
            if process:
                df_storage = df_storage.filter(f"process = '{process}'")
            
            # Collect results
            results = df_storage.collect()
            
            # Convert to our model format
            storage_records = []
            for row in results:
                storage_records.append(StorageRecord(
                    log_id=str(row.get('log_id', '')),
                    table_name=str(row.get('table_name', '')),
                    process=str(row.get('process', '')),
                    timestamp=row.get('timestamp', datetime.now()),
                    record_count=int(row.get('record_count', 0)),
                    stage=int(row.get('stage', 0))
                ))
            
            return storage_records
            
        except Exception as e:
            raise Exception(f"Error getting storage metadata: {str(e)}")

    async def get_field_lineage(self, stored_log_id: str) -> List[FieldLineage]:
        """
        Get field lineage for a specific storage log
        
        Args:
            stored_log_id: The log ID from storage metadata
            
        Returns:
            List of field lineage records
        """
        try:
            metadata = self._get_metadata_manager()
            
            # Read field lineage log from PortAda
            df_lineage = metadata.read_log("field_lineage_log")
            
            # Filter by stored_log_id
            df_lineage = df_lineage.filter(df_lineage.stored_log_id == stored_log_id)
            
            # Collect results
            results = df_lineage.collect()
            
            # Convert to our model format
            lineage_records = []
            for row in results:
                lineage_records.append(FieldLineage(
                    field_name=str(row.get('field_name', '')),
                    operation=str(row.get('operation', '')),
                    old_value=str(row.get('old_value', '')),
                    new_value=str(row.get('new_value', '')),
                    timestamp=row.get('timestamp', datetime.now())
                ))
            
            return lineage_records
            
        except Exception as e:
            raise Exception(f"Error getting field lineage: {str(e)}")
    
    async def get_process_metadata(self, process_name: Optional[str] = None) -> List[ProcessRecord]:
        """
        Get process metadata (filtered by process = 'ingest.save_raw_data' by default)
        
        Returns:
            List of process records
        """
        try:
            metadata = self._get_metadata_manager()
            
            # Read process log from PortAda
            df_process = metadata.read_log("process_log")
            
            # Apply process filter
            if process_name:
                df_process = df_process.filter(f"process = '{process_name}'")
            else:
                # Default filter as per documentation
                df_process = df_process.filter("process = 'ingest.save_raw_data'")
            
            # Collect results
            results = df_process.collect()
            
            # Convert to our model format
            process_records = []
            for row in results:
                process_records.append(ProcessRecord(
                    log_id=str(row.get('log_id', '')),
                    process=str(row.get('process', '')),
                    timestamp=row.get('timestamp', datetime.now()),
                    duration=float(row.get('duration', 0.0)),
                    status=str(row.get('status', '')),
                    records_processed=int(row.get('records_processed', 0)),
                    stage=int(row.get('stage', 0)),
                    error_message=row.get('error_message')
                ))
            
            return process_records
            
        except Exception as e:
            raise Exception(f"Error getting process metadata: {str(e)}")


# Global service instance
portada_service = PortAdaService()
