"""
Service layer for PortAda library integration
Enhanced version with improved error handling and logging
"""

import os
import json
import yaml
from typing import Optional, List, Dict, Any
from datetime import datetime
import asyncio
import aiofiles
import logging
from concurrent.futures import ThreadPoolExecutor
import functools

# PortAda library imports
try:
    from portada_data_layer import PortadaBuilder, DataLakeMetadataManager
    from portada_data_layer.layer_boat_news.boat_news_layer import BOAT_NEWS_TYPE
    from pyspark.sql import functions as F
except ImportError as e:
    logging.warning(f"PortAda library not available: {e}")
    # Mock classes for development
    BOAT_NEWS_TYPE = "boat_news"
    class PortadaBuilder:
        NEWS_TYPE = "news"
        BOAT_NEWS_TYPE = "boat_news"
        KNOWN_ENTITIES_TYPE = "known_entities"
        
        def __init__(self, config=None):
            pass
            
        def protocol(self, protocol: str): return self
        def base_path(self, path: str): return self
        def app_name(self, name: str): return self
        def project_name(self, name: str): return self
        def config(self, key: str, value: str): return self
        def build(self, layer_type: str): return MockLayer()
    
    class DataLakeMetadataManager:
        def __init__(self, config): pass
        def read_log(self, log_type: str): return MockDataFrame()
    
    class MockLayer:
        def start_session(self): pass
        def get_configuration(self): return {}
        def ingest(self, dest_path: str, local_path: str, **kwargs): pass
        def copy_ingested_entities(self, entity: str, local_path: str): return {}, ""
        def save_raw_entities(self, entity: str, data: dict): pass
        def get_missing_dates_from_a_newspaper(self, data_path: str, **kwargs): return []
        def read_raw_data(self, newspaper: str): return MockDataFrame()
    
    class MockDataFrame:
        def filter(self, condition): return self
        def collect(self): return []
        def groupBy(self, *cols): return self
        def count(self): return self
        def orderBy(self, *cols, **kwargs): return self
        def limit(self, n): return self
        def agg(self, *funcs): return self
        def select(self, *cols): return self
        def withColumn(self, *args): return self
        def alias(self, *args): return self
    
    class F:
        def to_date(self, *args): return self
        def year(self, *args): return self
        def month(self, *args): return self
        def dayofmonth(self, *args): return self
        def count(self, *args): return self
        def alias(self, *args): return self

from app.core.config import settings
from app.core.exceptions import (
    PortAdaBaseException, PortAdaConnectionError, PortAdaConfigurationError,
    PortAdaIngestionError, PortAdaQueryError, PortAdaValidationError,
    PortAdaFileError, wrap_portada_error
)
from app.models.ingestion import IngestionType
from app.models.analysis import (
    MissingDateEntry, DuplicateRecord, DuplicateDetail,
    StorageRecord, FieldLineage, ProcessRecord
)


# Keep backward compatibility
class PortAdaServiceError(PortAdaBaseException):
    """Legacy exception for backward compatibility"""
    pass


class PortAdaService:
    """Enhanced service for interacting with PortAda library"""
    
    # Layer type constants from PortadaBuilder
    NEWS_TYPE = "news"
    KNOWN_ENTITIES_TYPE = "known_entities"
    
    def __init__(self):
        self.base_path = settings.PORTADA_BASE_PATH
        self.app_name = settings.PORTADA_APP_NAME
        self.project_name = settings.PORTADA_PROJECT_NAME
        self._builder = None
        self._layer_news = None
        self._layer_boat_news = None
        self._layer_entities = None
        self._metadata_manager = None
        self.logger = logging.getLogger(__name__)
        
        # Log library availability status
        if 'MockLayer' in globals():
            self.logger.warning("🔸 PortAda service is running in MOCK mode (library not found)")
        else:
            self.logger.info("🚀 PortAda service initialized with REAL py-portada-data-layer")
        
        # Thread pool for CPU-intensive operations
        self._thread_pool = ThreadPoolExecutor(
            max_workers=4,  # Increased from 2 to 4 for better concurrency
            thread_name_prefix="portada"
        )
    
    def _get_builder(self) -> PortadaBuilder:
        """Get or create PortAda builder instance with configuration"""
        if self._builder is None:
            try:
                # Load configuration from JSON file
                with open(settings.PORTADA_CONFIG_PATH) as f:
                    config = json.load(f)
                
                self._builder = (
                    PortadaBuilder(config)  # ✅ Pass config dictionary
                    .protocol("file://")
                    .base_path(self.base_path)
                    .app_name(self.app_name)
                    .project_name(self.project_name)
                    .config("spark.sql.shuffle.partitions", "4")  # ✅ Configure Spark
                )
                self.logger.info("PortAda builder initialized successfully with configuration")
            except FileNotFoundError:
                self.logger.error(f"Configuration file not found: {settings.PORTADA_CONFIG_PATH}")
                raise PortAdaConfigurationError(
                    f"Configuration file not found: {settings.PORTADA_CONFIG_PATH}",
                    details={"config_path": settings.PORTADA_CONFIG_PATH}
                )
            except json.JSONDecodeError as e:
                self.logger.error(f"Invalid JSON in configuration file: {e}")
                raise PortAdaConfigurationError(
                    f"Invalid JSON in configuration file: {e}",
                    details={"config_path": settings.PORTADA_CONFIG_PATH}
                )
            except Exception as e:
                self.logger.error(f"Failed to initialize PortAda builder: {e}")
                raise wrap_portada_error(e, "builder initialization")
        return self._builder
    
    def _get_news_layer(self):
        """Get or create news layer instance"""
        if self._layer_news is None:
            try:
                builder = self._get_builder()
                self._layer_news = builder.build(builder.NEWS_TYPE)
                self._layer_news.start_session()
                self.logger.info("News layer initialized successfully")
            except Exception as e:
                self.logger.error(f"Failed to initialize news layer: {e}")
                raise wrap_portada_error(e, "news layer initialization")
        return self._layer_news

    def _get_boat_news_layer(self):
        """Get or create boat news layer instance"""
        if self._layer_boat_news is None:
            try:
                builder = self._get_builder()
                self._layer_boat_news = builder.build(builder.BOAT_NEWS_TYPE)
                self._layer_boat_news.start_session()
                self.logger.info("Boat News layer initialized successfully")
            except Exception as e:
                self.logger.error(f"Failed to initialize boat news layer: {e}")
                raise wrap_portada_error(e, "boat news layer initialization")
        return self._layer_boat_news
    
    def _get_entities_layer(self):
        """Get or create entities layer instance"""
        if self._layer_entities is None:
            try:
                builder = self._get_builder()
                self._layer_entities = builder.build(builder.KNOWN_ENTITIES_TYPE)
                self._layer_entities.start_session()
                self.logger.info("Entities layer initialized successfully")
            except Exception as e:
                self.logger.error(f"Failed to initialize entities layer: {e}")
                raise wrap_portada_error(e, "entities layer initialization")
        return self._layer_entities
    
    def _get_metadata_manager(self) -> DataLakeMetadataManager:
        """Get or create metadata manager instance"""
        if self._metadata_manager is None:
            try:
                layer_news = self._get_news_layer()
                self._metadata_manager = DataLakeMetadataManager(layer_news.get_configuration())
                self.logger.info("Metadata manager initialized successfully")
            except Exception as e:
                self.logger.error(f"Failed to initialize metadata manager: {e}")
                raise wrap_portada_error(e, "metadata manager initialization")
        return self._metadata_manager

    def _run_in_thread(self, func, *args, **kwargs):
        """Run a potentially blocking function in a thread pool"""
        loop = asyncio.get_event_loop()
        return loop.run_in_executor(
            self._thread_pool,
            functools.partial(func, *args, **kwargs)
        )
    
    def _handle_ingestion_error(self, e: Exception, operation: str) -> Dict[str, Any]:
        """
        Handle ingestion errors and return standardized error response
        
        Args:
            e: The exception that occurred
            operation: Description of the operation that failed
            
        Returns:
            Standardized error response dictionary
        """
        if isinstance(e, PortAdaBaseException):
            error_msg = e.message
        else:
            wrapped_error = wrap_portada_error(e, operation)
            error_msg = wrapped_error.message
        
        return {
            "success": False,
            "records_processed": 0,
            "message": error_msg
        }

    def _perform_ingestion_sync(self, data_path: str, temp_file_path: str, user: str) -> None:
        """
        Synchronous ingestion operation to run in thread pool
        
        Args:
            data_path: Path in the data lake (e.g., "ship_entries")
            temp_file_path: Local path to the file to ingest
            user: User responsible for the ingestion
        """
        layer_news = self._get_news_layer()
        layer_news.ingest(data_path, user=user, local_path=temp_file_path)
    
    async def ingest_extraction_data(self, file_path: str, newspaper: Optional[str] = None, data_path_delta_lake: str = "ship_entries") -> Dict[str, Any]:
        """
        Ingest extraction data from JSON file
        
        The PortAda library expects JSON files to contain a flat array of entry objects.
        This method handles both formats:
        1. Flat array: [{"publication_date": "...", ...}, ...]
        2. Nested format: {"entries": [{"publication_date": "...", ...}], ...}
        
        Args:
            file_path: Path to the JSON file
            newspaper: Optional newspaper identifier for organization
            data_path_delta_lake: Destination path in delta lake
            
        Returns:
            Dictionary with ingestion results
        """
        try:
            self.logger.info(f"Starting extraction data ingestion: {file_path}")
            layer_news = self._get_news_layer()
            
            # Read and process JSON data
            async with aiofiles.open(file_path, 'r') as f:
                content = await f.read()
                data = json.loads(content)
            
            # Convert to flat array format if needed
            if isinstance(data, list):
                # Already in flat array format
                entries = data
                record_count = len(entries)
                self.logger.info(f"JSON is already in flat array format with {record_count} entries")
            elif isinstance(data, dict):
                # Nested format - extract entries and add metadata to each entry
                if 'entries' in data and isinstance(data['entries'], list):
                    entries = []
                    base_metadata = {
                        'publication_date': data.get('publication_date'),
                        'publication_name': data.get('publication_name'),
                        'publication_edition': data.get('publication_edition')
                    }
                    
                    # Add metadata to each entry if not already present
                    for entry in data['entries']:
                        enhanced_entry = entry.copy()
                        for key, value in base_metadata.items():
                            if key not in enhanced_entry and value is not None:
                                enhanced_entry[key] = value
                        entries.append(enhanced_entry)
                    
                    record_count = len(entries)
                    self.logger.info(f"Converted nested format to flat array with {record_count} entries")
                else:
                    # Single entry object
                    entries = [data]
                    record_count = 1
                    self.logger.info("Converted single object to flat array with 1 entry")
            else:
                raise ValueError(f"Unsupported JSON format: expected array or object, got {type(data)}")
            
            # Create temporary file with flat array format (no indentation for speed)
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
                json.dump(entries, temp_file)  # No indent for faster I/O
                temp_file_path = temp_file.name
            
            try:
                # Use the data_path_delta_lake directly - the library handles publication organization
                destination_path = data_path_delta_lake
                
                # Perform ingestion using PortAda library in thread pool to avoid blocking
                # The library will automatically organize by publication_name, date, and edition
                # Note: ingest signature is (data_path: str, user: str, local_path: str)
                await self._run_in_thread(self._perform_ingestion_sync, destination_path, temp_file_path, "api_user")
                
                self.logger.info(f"Successfully ingested {record_count} records to {destination_path}")
                return {
                    "success": True,
                    "records_processed": record_count,
                    "message": f"Successfully ingested {record_count} records. Data organized automatically by publication and date."
                }
            finally:
                # Clean up temporary file
                import os
                try:
                    os.unlink(temp_file_path)
                except Exception as e:
                    self.logger.warning(f"Could not delete temporary file {temp_file_path}: {e}")
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON format in file {file_path}: {e}")
            return self._handle_ingestion_error(e, "JSON validation")
        except Exception as e:
            self.logger.error(f"Error during extraction data ingestion: {e}")
            return self._handle_ingestion_error(e, "extraction data ingestion")
    
    def _perform_entity_ingestion_sync(self, entity_name: str, file_path: str) -> tuple:
        """Synchronous entity ingestion operation to run in thread pool"""
        layer_entities = self._get_entities_layer()
        data, dest = layer_entities.copy_ingested_entities(entity=entity_name, local_path=file_path)
        odata = {"source_path": dest, "data": data}
        layer_entities.save_raw_entities(entity=entity_name, data=odata)
        return data, dest
    
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
            self.logger.info(f"Starting known entities ingestion: {file_path}")
            layer_entities = self._get_entities_layer()
            
            # Count entities before ingestion
            async with aiofiles.open(file_path, 'r') as f:
                content = await f.read()
                data = yaml.safe_load(content)
                entity_count = len(data) if isinstance(data, (list, dict)) else 1
            
            # Perform entity ingestion using PortAda library in thread pool
            data, dest = await self._run_in_thread(self._perform_entity_ingestion_sync, entity_name, file_path)
            
            self.logger.info(f"Successfully ingested {entity_count} entities as {entity_name}")
            return {
                "success": True,
                "records_processed": entity_count,
                "message": f"Successfully ingested {entity_count} entities as {entity_name}"
            }
            
        except yaml.YAMLError as e:
            self.logger.error(f"Invalid YAML format in file {file_path}: {e}")
            return self._handle_ingestion_error(e, "YAML validation")
        except Exception as e:
            self.logger.error(f"Error during known entities ingestion: {e}")
            return self._handle_ingestion_error(e, "known entities ingestion")
    
    def _get_missing_dates_sync(
        self, 
        data_path: str, 
        publication_name: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        date_and_edition_list: Optional[str] = None
    ) -> list:
        """Synchronous missing dates operation to run in thread pool"""
        try:
            layer_boat_news = self._get_boat_news_layer()
            
            # Build kwargs with required parameters according to library specs
            # The library expects news_type=BOAT_NEWS_TYPE
            kwargs = {
                "publication_name": publication_name,
                "news_type": BOAT_NEWS_TYPE
            }
            
            if start_date:
                kwargs["start_date"] = start_date
            if end_date:
                kwargs["end_date"] = end_date
            if date_and_edition_list:
                kwargs["date_and_edition_list"] = date_and_edition_list
            
            # Call the library method with data_path as required by the library (see main.py)
            return layer_boat_news.get_missing_dates_from_a_newspaper(data_path, **kwargs)
        except Exception as e:
            # If any error occurs (including missing data), log it and return empty list
            if "PATH_NOT_FOUND" in str(e) or "does not exist" in str(e):
                self.logger.info(f"Data not found for publication {publication_name} - no data has been processed yet")
            else:
                self.logger.warning(f"Error getting missing dates for {publication_name}: {str(e)}")
            return []
    
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
            self.logger.info(f"Getting missing dates for publication: {publication_name}")
            
            # Get missing dates using PortAda library in thread pool
            # Pass optional start_date and end_date parameters
            missing_dates_result = await self._run_in_thread(
                self._get_missing_dates_sync, 
                data_path, 
                publication_name,
                start_date,
                end_date,
                date_and_edition_list
            )
            
            # Convert results to our model format
            missing_dates = []
            if missing_dates_result:
                for item in missing_dates_result:
                    # Handle different return formats from PortAda
                    if isinstance(item, (list, tuple)) and len(item) >= 2:
                        # Tuple format: (date, edition)
                        missing_dates.append(MissingDateEntry(
                            date=str(item[0]),
                            edition=str(item[1]),
                            gap_duration=''
                        ))
                    elif isinstance(item, dict):
                        # Dictionary format
                        missing_dates.append(MissingDateEntry(
                            date=str(item.get('date', '')),
                            edition=str(item.get('edition', 'U')),
                            gap_duration=str(item.get('gap_duration', ''))
                        ))
                    elif isinstance(item, str):
                        # String format - assume it's a date
                        missing_dates.append(MissingDateEntry(
                            date=item,
                            edition='U',
                            gap_duration=''
                        ))
                    else:
                        # Other formats - try to convert to string
                        missing_dates.append(MissingDateEntry(
                            date=str(item),
                            edition='U',
                            gap_duration=''
                        ))
            
            self.logger.info(f"Found {len(missing_dates)} missing dates for {publication_name}")
            return missing_dates
            
        except Exception as e:
            error_msg = f"Error getting missing dates for {publication_name}: {str(e)}"
            self.logger.error(error_msg)
            # Return empty list instead of raising error for graceful degradation
            self.logger.info(f"Returning empty missing dates list for {publication_name} due to error")
            return []

    def _get_duplicates_metadata_sync(self, publication: Optional[str], start_date: Optional[str], end_date: Optional[str]) -> list:
        """Synchronous duplicates metadata operation to run in thread pool"""
        try:
            metadata = self._get_metadata_manager()
            
            # Check if duplicates log exists before trying to read it
            try:
                # Read duplicates log from PortAda
                self.logger.info("Attempting to read duplicates_log...")
                df_dup = metadata.read_log("duplicates_log")
                self.logger.info(f"Successfully read duplicates_log, type: {type(df_dup)}")
            except Exception as e:
                # Log the full error for debugging
                self.logger.error(f"Error reading duplicates_log: {type(e).__name__}: {str(e)}")
                import traceback
                self.logger.error(f"Traceback: {traceback.format_exc()}")
                
                # If the log doesn't exist, return empty list
                if "PATH_NOT_FOUND" in str(e) or "does not exist" in str(e) or "path" in str(e).lower():
                    self.logger.info("Duplicates log not found - no data has been processed yet")
                    return []
                else:
                    # Re-raise other errors
                    raise e
            
            # Apply filters
            if publication:
                df_dup = df_dup.filter(f"lower(publication)='{publication.lower()}'")
            if start_date:
                df_dup = df_dup.filter(f"date >= '{start_date}'")
            if end_date:
                df_dup = df_dup.filter(f"date <= '{end_date}'")
            
            # Collect results
            return df_dup.collect()
            
        except Exception as e:
            # If any error occurs, log it and return empty list for graceful degradation
            self.logger.error(f"Error in _get_duplicates_metadata_sync: {type(e).__name__}: {str(e)}")
            import traceback
            self.logger.error(f"Full traceback: {traceback.format_exc()}")
            return []
    
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
            self.logger.info("Getting duplicates metadata")
            
            # Get duplicates metadata in thread pool
            results = await self._run_in_thread(
                self._get_duplicates_metadata_sync, publication, start_date, end_date
            )
            
            # Convert to our model format
            duplicates = []
            for row in results:
                # PySpark Row objects use attribute access, not dict.get()
                # Convert Row to dict first for easier access
                try:
                    row_dict = row.asDict() if hasattr(row, 'asDict') else dict(row)
                except Exception as e:
                    self.logger.warning(f"Could not convert row to dict: {e}, using attribute access")
                    row_dict = {field: getattr(row, field, None) for field in row.__fields__}
                
                duplicates.append(DuplicateRecord(
                    log_id=str(row_dict.get('log_id', '')),
                    date=str(row_dict.get('date', '')),
                    edition=str(row_dict.get('edition', '')),
                    publication=str(row_dict.get('publication', '')),
                    uploaded_by=str(row_dict.get('uploaded_by', user_responsible or '')),
                    duplicate_count=int(row_dict.get('duplicate_count', 0)),
                    duplicates_filter=str(row_dict.get('duplicates_filter', '')),
                    duplicate_ids=row_dict.get('duplicate_ids', [])
                ))
            
            self.logger.info(f"Found {len(duplicates)} duplicate records")
            return duplicates
            
        except Exception as e:
            error_msg = f"Error getting duplicates metadata: {str(e)}"
            self.logger.error(error_msg)
            import traceback
            self.logger.error(f"Full traceback: {traceback.format_exc()}")
            raise wrap_portada_error(e, "duplicates metadata query")

    def _get_storage_metadata_sync(self, table_name: Optional[str] = None, process_name: Optional[str] = None, stage: int = 0) -> list:
        """Synchronous storage metadata operation to run in thread pool"""
        try:
            metadata = self._get_metadata_manager()
            df_sto = metadata.read_log("storage_log")
            
            # Apply filters
            # Ensure stage is handled correctly
            df_sto = df_sto.filter(f"stage={stage}")
            
            if table_name:
                df_sto = df_sto.filter(f"table_name='{table_name}'")
            
            if process_name:
                try:
                    df_sto = df_sto.filter(f"process_name='{process_name}'")
                except:
                    df_sto = df_sto.filter(f"process='{process_name}'")
            
            return df_sto.collect()
        except Exception as e:
            self.logger.error(f"Error in _get_storage_metadata_sync: {e}")
            return []

    async def get_storage_metadata(
        self, 
        table_name: Optional[str] = None, 
        process_name: Optional[str] = None, 
        stage: int = 0
    ) -> List[StorageRecord]:
        """
        Get storage metadata records
        """
        try:
            results = await self._run_in_thread(
                self._get_storage_metadata_sync, table_name, process_name, stage
            )
            
            records = []
            for row in results:
                try:
                    row_dict = row.asDict() if hasattr(row, 'asDict') else dict(row)
                except:
                    row_dict = {field: getattr(row, field, None) for field in getattr(row, '__fields__', [])}
                
                records.append(StorageRecord(
                    log_id=str(row_dict.get('log_id', row_dict.get('stored_log_id', ''))),
                    table_name=str(row_dict.get('table_name', '')),
                    process_name=str(row_dict.get('process_name', row_dict.get('process', ''))),
                    stage=int(row_dict.get('stage', 0)),
                    records_stored=int(row_dict.get('records_count', row_dict.get('records_stored', 0))),
                    storage_path=str(row_dict.get('file_path', row_dict.get('storage_path', ''))),
                    created_at=row_dict.get('stored_at', row_dict.get('created_at', datetime.utcnow())),
                    metadata=row_dict.get('metadata', {})
                ))
            
            return records
        except Exception as e:
            self.logger.error(f"Error getting storage metadata: {e}")
            raise wrap_portada_error(e, "storage metadata query")

    def _get_field_lineage_sync(self, log_id: str) -> list:
        """Synchronous field lineage operation to run in thread pool"""
        try:
            metadata = self._get_metadata_manager()
            df_fl = metadata.read_log("field_lineage_log")
            
            # Filter by stored_log_id as requested
            df_fl = df_fl.filter(f"stored_log_id='{log_id}'")
            
            return df_fl.collect()
        except Exception as e:
            self.logger.error(f"Error in _get_field_lineage_sync: {e}")
            return []

    async def get_field_lineage(self, log_id: str) -> List[FieldLineage]:
        """
        Get field lineage for a specific storage record
        """
        try:
            results = await self._run_in_thread(self._get_field_lineage_sync, log_id)
            
            lineages = []
            for row in results:
                try:
                    row_dict = row.asDict() if hasattr(row, 'asDict') else dict(row)
                except:
                    row_dict = {field: getattr(row, field, None) for field in getattr(row, '__fields__', [])}
                
                lineages.append(FieldLineage(
                    field_name=str(row_dict.get('field_name', '')),
                    source_table=str(row_dict.get('source_table', '')),
                    target_table=str(row_dict.get('target_table', '')),
                    transformation=row_dict.get('transformation'),
                    lineage_path=row_dict.get('lineage_path', [])
                ))
            
            return lineages
        except Exception as e:
            self.logger.error(f"Error getting field lineage: {e}")
            raise wrap_portada_error(e, "field lineage query")

    def _get_daily_ingestion_summary_sync(self, newspaper: str, start_date: Optional[str], end_date: Optional[str]) -> List[Dict[str, Any]]:
        """Synchronous daily ingestion summary operation to run in thread pool"""
        try:
            layer_news = self._get_news_layer()
            df = layer_news.read_raw_data(newspaper)

            # Filter by date range if provided
            if start_date:
                df = df.filter(F.col("publication_date") >= start_date)
            if end_date:
                df = df.filter(F.col("publication_date") <= end_date)

            # 1.- separar la fecha en columnas para el año, el mes y el dia
            df = df.withColumn("data_dt", F.to_date("publication_date", "yyyy-MM-dd")) \
                .withColumn("y", F.year("data_dt")) \
                .withColumn("m", F.month("data_dt")) \
                .withColumn("d", F.dayofmonth("data_dt"))

            # 2.- Calculator totales y subtotales
            dfr = df.rollup("y", "m", "d", "publication_edition") \
                .agg(F.count("*").alias("t")).orderBy("y", "m", "d", "publication_edition")

            # 3 gestionar resultados
            results = []
            for row in dfr.collect():
                row_dict = row.asDict()
                label = ""
                if row_dict['y'] is None:
                    label = "TOTAL"
                elif row_dict['m'] is None:
                    label = f"Total año {row_dict['y']}"
                elif row_dict['d'] is None:
                    label = f"Total año {row_dict['y']} y mes {row_dict['m']}"
                elif row_dict['publication_edition'] is None:
                    label = f"Total año {row_dict['y']}, mes {row_dict['m']} y dia {row_dict['d']}"
                else:
                    label = f"Total año {row_dict['y']}, mes {row_dict['m']}, dia {row_dict['d']} y edition {row_dict['publication_edition']}"
                
                results.append({
                    "label": label,
                    "count": row_dict['t'],
                    "year": row_dict.get('y'),
                    "month": row_dict.get('m'),
                    "day": row_dict.get('d'),
                    "edition": row_dict.get('publication_edition')
                })
            return results
        except Exception as e:
            self.logger.error(f"Error in _get_daily_ingestion_summary_sync: {e}")
            return []

    async def get_daily_ingestion_summary(
        self,
        newspaper: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get daily ingestion summary
        """
        try:
            self.logger.info(f"Getting daily ingestion summary for newspaper: {newspaper}")
            
            results = await self._run_in_thread(
                self._get_daily_ingestion_summary_sync, newspaper, start_date, end_date
            )
            
            return results
        except Exception as e:
            error_msg = f"Error getting daily ingestion summary for {newspaper}: {str(e)}"
            self.logger.error(error_msg)
            raise wrap_portada_error(e, "daily ingestion summary query")


# Global service instance
portada_service = PortAdaService()
