# Requirements Document

## Introduction

This document specifies the requirements for the PortAda Data Ingestion and Analysis System, a web-based application that provides a user interface for managing historical newspaper data ingestion and performing various analytical queries on the data stored in a Delta Lake through the py-portada-data-layer library.

The system enables users to upload extraction data and known entities, query for missing dates in newspaper archives, analyze duplicates, review storage metadata, and monitor data processing operations.

## Glossary

- **System**: The PortAda Data Ingestion and Analysis web application
- **User**: A person interacting with the web application
- **PortAda_Library**: The py-portada-data-layer Python library that provides data lake operations
- **Delta_Lake**: The underlying data storage system managed by PortAda_Library
- **Extraction_Data**: JSON files containing newspaper entry data (ship arrivals, etc.)
- **Known_Entities**: YAML files containing reference data for entity recognition
- **Publication**: A newspaper identifier (e.g., "db" for Diario de Barcelona, "dm" for Diario Mercantil, "sm" for Semanario Mercantil)
- **Edition**: A publication edition identifier (e.g., "M" for morning, "T" for afternoon, "U" for unique)
- **Ingestion_Folder**: Temporary storage directory for uploaded files before processing
- **Metadata_Manager**: Component of PortAda_Library that manages data lake metadata logs
- **Duplicates_Log**: Metadata log tracking duplicate records found during ingestion
- **Storage_Log**: Metadata log tracking data storage operations
- **Process_Log**: Metadata log tracking data processing operations
- **Field_Lineage_Log**: Metadata log tracking field-level data transformations
- **Stage**: A processing stage indicator (0 = raw/initial stage)

## Requirements

### Requirement 1: User Authentication and Access Control

**User Story:** As a user, I want to securely access the system, so that only authorized personnel can perform data ingestion and analysis operations.

#### Acceptance Criteria

1. WHEN a user navigates to the system, THE System SHALL display a login interface
2. WHEN a user provides valid credentials, THE System SHALL grant access to the main interface
3. WHEN a user provides invalid credentials, THE System SHALL deny access and display an error message
4. WHEN a user is authenticated, THE System SHALL maintain the session until logout or timeout

### Requirement 2: Data Ingestion - Extraction Data Upload

**User Story:** As a user, I want to upload extraction data files, so that newspaper entry data can be ingested into the Delta Lake.

#### Acceptance Criteria

1. WHEN a user selects the extraction data upload option, THE System SHALL display a file upload interface for JSON files
2. WHEN a user selects a JSON file and a publication identifier, THE System SHALL validate the file format
3. IF the file format is invalid, THEN THE System SHALL display an error message and prevent upload
4. WHEN a valid JSON file is uploaded, THE System SHALL store the file in Ingestion_Folder at path `<ingestion_folder>/<publication>/<user_name>/<temporary_filename>`
5. WHEN the file is stored, THE System SHALL initiate asynchronous processing using PortAda_Library
6. WHEN processing begins, THE System SHALL display a confirmation message to the user
7. WHEN processing completes, THE System SHALL remove the temporary file from Ingestion_Folder
8. WHEN processing fails, THE System SHALL display an error message with details

### Requirement 3: Data Ingestion - Known Entities Upload

**User Story:** As a user, I want to upload known entities files, so that entity reference data can be ingested into the Delta Lake.

#### Acceptance Criteria

1. WHEN a user selects the known entities upload option, THE System SHALL display a file upload interface for YAML files
2. WHEN a user selects a YAML file, THE System SHALL validate the file format
3. IF the file format is invalid, THEN THE System SHALL display an error message and prevent upload
4. WHEN a valid YAML file is uploaded, THE System SHALL store the file in Ingestion_Folder
5. WHEN the file is stored, THE System SHALL initiate asynchronous processing using PortAda_Library
6. WHEN processing begins, THE System SHALL display a confirmation message to the user
7. WHEN processing completes, THE System SHALL remove the temporary file from Ingestion_Folder
8. WHEN processing fails, THE System SHALL display an error message with details

### Requirement 4: Ingestion Process Separation

**User Story:** As a user, I want extraction data and known entities uploads to be separate processes, so that they cannot be uploaded simultaneously and cause conflicts.

#### Acceptance Criteria

1. THE System SHALL provide separate UI controls for extraction data and known entities uploads
2. WHEN a user is uploading extraction data, THE System SHALL disable the known entities upload interface
3. WHEN a user is uploading known entities, THE System SHALL disable the extraction data upload interface
4. WHEN an upload completes, THE System SHALL re-enable both upload interfaces

### Requirement 5: Pending Ingestion Files Query

**User Story:** As a user, I want to query how many ingestion files are pending processing, so that I can monitor the ingestion queue status.

#### Acceptance Criteria

1. WHEN a user accesses the pending files query, THE System SHALL display filter options for publication and username
2. WHEN a user provides no filters, THE System SHALL count all unprocessed files in Ingestion_Folder
3. WHEN a user provides only a publication filter, THE System SHALL count all unprocessed files for that publication
4. WHEN a user provides both publication and username filters, THE System SHALL count unprocessed files for that specific user and publication
5. WHEN the query executes, THE System SHALL display the count of pending files

### Requirement 6: Missing Dates Analysis - File-Based Query

**User Story:** As a user, I want to check for missing dates by uploading a file with dates and editions, so that I can identify gaps in the newspaper archive.

#### Acceptance Criteria

1. WHEN a user selects missing dates analysis, THE System SHALL require selection of a publication
2. WHEN a user selects file-based query mode, THE System SHALL display a file upload interface
3. WHEN a user uploads a file, THE System SHALL accept YAML, JSON, or plain text formats
4. WHEN the file is YAML format, THE System SHALL parse dates in format `YYYY-MM-DD: [edition_list]`
5. WHEN the file is JSON format, THE System SHALL parse dates in format `[{"YYYY-MM-DD":["edition1", "edition2"]}]`
6. WHEN the file is plain text format, THE System SHALL parse one date per line in format `YYYY-MM-DD`
7. WHEN the file is parsed, THE System SHALL call PortAda_Library method `get_missing_dates_from_a_newspaper` with publication_name and date_and_edition_list parameters
8. WHEN the query completes, THE System SHALL display missing dates and editions in a scrollable table

### Requirement 7: Missing Dates Analysis - Date Range Query

**User Story:** As a user, I want to check for missing dates by specifying a date range, so that I can identify gaps in a specific time period.

#### Acceptance Criteria

1. WHEN a user selects date range query mode, THE System SHALL display start date and end date input fields
2. WHEN a user provides start date only, THE System SHALL query from that date to the latest available date
3. WHEN a user provides end date only, THE System SHALL query from the earliest available date to that date
4. WHEN a user provides neither date, THE System SHALL query the entire date range
5. WHEN dates are provided, THE System SHALL validate the format as YYYY-MM-DD
6. IF date format is invalid, THEN THE System SHALL display an error message
7. WHEN the query executes, THE System SHALL call PortAda_Library method `get_missing_dates_from_a_newspaper` with publication_name, start_date, and end_date parameters
8. WHEN the query completes, THE System SHALL display missing dates and editions in a scrollable table

### Requirement 8: Duplicates Analysis - Metadata Query

**User Story:** As a user, I want to query duplicate records metadata, so that I can identify and review duplicate entries in the data.

#### Acceptance Criteria

1. WHEN a user accesses duplicates analysis, THE System SHALL display filter options for user responsible, publication, start date, and end date
2. WHEN filters are provided, THE System SHALL call Metadata_Manager method `read_log("duplicates_log")`
3. WHEN publication filter is provided, THE System SHALL filter results where publication equals the specified value
4. WHEN user responsible filter is provided, THE System SHALL filter results where uploaded_by equals the specified value
5. WHEN date range filters are provided, THE System SHALL filter results where date is between start_date and end_date
6. WHEN the query completes, THE System SHALL display a master table with columns: date, edition, publication, uploaded_by, duplicate_count
7. WHEN a user selects a row in the master table, THE System SHALL display detailed duplicate records for that date and edition

### Requirement 9: Duplicates Analysis - Detail View

**User Story:** As a user, I want to view detailed duplicate records for a specific date and edition, so that I can examine the actual duplicate entries.

#### Acceptance Criteria

1. WHEN a user selects a row from the duplicates master table, THE System SHALL extract duplicates_filter and duplicate_ids from that row
2. WHEN detail view is requested, THE System SHALL call Metadata_Manager method `read_log("duplicates_records")`
3. WHEN the records are retrieved, THE System SHALL apply the duplicates_filter to the results
4. WHEN the filter is applied, THE System SHALL further filter where entry_id is in duplicate_ids list
5. WHEN the query completes, THE System SHALL display the detailed duplicate records in a detail table

### Requirement 10: Daily Entry Count Analysis

**User Story:** As a user, I want to count daily entries by publication, so that I can analyze data volume over time.

#### Acceptance Criteria

1. WHEN a user accesses daily entry count analysis, THE System SHALL display filter options for publication, start date, and end date
2. WHEN a publication is selected, THE System SHALL instantiate PortAda_Library BoatFactIngestion object
3. WHEN the query executes, THE System SHALL call `read_raw_data(newspaper)` method
4. WHEN data is retrieved, THE System SHALL group by publication_date and publication_edition
5. WHEN grouping is complete, THE System SHALL count entries for each date and edition combination
6. WHEN date range filters are provided, THE System SHALL filter results to the specified range
7. WHEN the query completes, THE System SHALL display results showing date, edition, and entry count

### Requirement 11: Known Entities Query

**User Story:** As a user, I want to view all uploaded known entities, so that I can review the reference data available in the system.

#### Acceptance Criteria

1. WHEN a user accesses known entities query, THE System SHALL retrieve all known entity names from Delta_Lake
2. WHEN entities are retrieved, THE System SHALL display them in a list or table format
3. THE System SHALL display all entities without requiring filter parameters

### Requirement 12: Storage Metadata Query - Master View

**User Story:** As a user, I want to query storage metadata, so that I can review data storage operations and their details.

#### Acceptance Criteria

1. WHEN a user accesses storage metadata query, THE System SHALL display filter options for table_name and process
2. WHEN the query executes, THE System SHALL call Metadata_Manager method `read_log("storage_log")`
3. WHEN the log is retrieved, THE System SHALL filter where stage equals 0
4. WHEN table_name filter is provided, THE System SHALL filter where table_name equals the specified value
5. WHEN process filter is provided, THE System SHALL filter where process equals the specified value
6. WHEN the query completes, THE System SHALL display a master table with storage metadata records
7. WHEN a user selects a row in the master table, THE System SHALL display field lineage details for that storage operation

### Requirement 13: Storage Metadata Query - Field Lineage Detail

**User Story:** As a user, I want to view field lineage for a storage operation, so that I can track data transformations applied to each field.

#### Acceptance Criteria

1. WHEN a user selects a row from the storage metadata master table, THE System SHALL extract log_id from that row
2. WHEN detail view is requested, THE System SHALL call Metadata_Manager method `read_log("field_lineage_log")`
3. WHEN the lineage log is retrieved, THE System SHALL filter where stored_log_id equals the extracted log_id
4. WHEN the query completes, THE System SHALL display field lineage records showing field transformations

### Requirement 14: Process Metadata Query

**User Story:** As a user, I want to query process execution metadata, so that I can monitor data processing operations and their status.

#### Acceptance Criteria

1. WHEN a user accesses process metadata query, THE System SHALL display a filter option for process name
2. WHEN no process filter is provided, THE System SHALL default to filtering where stage equals 0
3. WHEN a process name filter is provided, THE System SHALL filter where process equals the specified value
4. WHEN the query executes, THE System SHALL call Metadata_Manager method `read_log("process_log")`
5. WHEN the query completes, THE System SHALL display process execution records in a table

### Requirement 15: Responsive User Interface

**User Story:** As a user, I want a responsive and intuitive interface, so that I can efficiently perform ingestion and analysis tasks.

#### Acceptance Criteria

1. THE System SHALL provide a navigation menu for accessing different functional areas
2. THE System SHALL organize functions into logical groups: Ingestion, Analysis
3. WHEN displaying large result sets, THE System SHALL provide scrollable tables or pagination
4. WHEN processing long-running operations, THE System SHALL display progress indicators or status messages
5. WHEN errors occur, THE System SHALL display clear error messages with actionable information

### Requirement 16: File Format Validation

**User Story:** As a system, I want to validate uploaded file formats, so that only correctly formatted files are processed.

#### Acceptance Criteria

1. WHEN a JSON file is uploaded for extraction data, THE System SHALL validate it contains valid JSON syntax
2. WHEN a YAML file is uploaded for known entities, THE System SHALL validate it contains valid YAML syntax
3. WHEN a date list file is uploaded, THE System SHALL validate it matches one of the supported formats (YAML, JSON, or plain text)
4. IF validation fails, THEN THE System SHALL display a specific error message indicating the format issue
5. IF validation succeeds, THEN THE System SHALL proceed with file processing

### Requirement 17: Asynchronous Processing

**User Story:** As a system, I want to process ingestion operations asynchronously, so that the user interface remains responsive during long-running operations.

#### Acceptance Criteria

1. WHEN a file is uploaded for ingestion, THE System SHALL return an immediate confirmation response
2. WHEN ingestion processing begins, THE System SHALL execute it in a background task
3. WHEN processing is ongoing, THE System SHALL allow users to continue using other system features
4. WHEN processing completes, THE System SHALL update the status visible to the user
5. IF processing fails, THEN THE System SHALL log the error and make it available to the user

### Requirement 18: Data Persistence and Cleanup

**User Story:** As a system, I want to manage temporary files properly, so that storage is used efficiently and processed files are cleaned up.

#### Acceptance Criteria

1. WHEN a file is uploaded, THE System SHALL store it in Ingestion_Folder with a unique filename
2. WHEN PortAda_Library successfully processes a file, THE System SHALL delete the temporary file from Ingestion_Folder
3. IF processing fails, THEN THE System SHALL retain the file for troubleshooting
4. WHEN querying pending files, THE System SHALL only count files that have not been processed

### Requirement 19: Integration with PortAda Library

**User Story:** As a system, I want to integrate seamlessly with py-portada-data-layer, so that all data operations are performed correctly through the library.

#### Acceptance Criteria

1. THE System SHALL use PortadaBuilder to initialize data layer connections
2. WHEN ingesting extraction data, THE System SHALL call the appropriate PortAda_Library ingestion methods
3. WHEN ingesting known entities, THE System SHALL call the appropriate PortAda_Library entity methods
4. WHEN querying metadata, THE System SHALL use DataLakeMetadataManager from PortAda_Library
5. WHEN querying missing dates, THE System SHALL call PortAda_Library analysis methods
6. THE System SHALL handle all PortAda_Library exceptions and convert them to user-friendly error messages

### Requirement 20: Configuration Management

**User Story:** As a system administrator, I want to configure system parameters, so that the application can be deployed in different environments.

#### Acceptance Criteria

1. THE System SHALL read configuration from environment variables or configuration files
2. THE System SHALL support configuration of Ingestion_Folder path
3. THE System SHALL support configuration of PortAda_Library base path
4. THE System SHALL support configuration of application name and project name for PortAda_Library
5. THE System SHALL validate required configuration parameters at startup
6. IF required configuration is missing, THEN THE System SHALL display an error and prevent startup
