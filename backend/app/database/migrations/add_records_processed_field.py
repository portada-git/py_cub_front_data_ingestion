"""
Migration to add records_processed field to ProcessingRecord model
"""

import logging
from sqlalchemy import text
from ..database_service import DatabaseService

logger = logging.getLogger(__name__)


async def migrate_add_records_processed_field():
    """
    Add records_processed field to processing_records table
    """
    try:
        logger.info("Starting migration: add records_processed field")
        
        # Initialize database service
        db_service = DatabaseService()
        await db_service.initialize()
        
        # Use the engine directly for this migration
        async with db_service.engine.begin() as conn:
            # Check if the column exists using a simpler approach
            try:
                # Try to select the column - if it fails, it doesn't exist
                await conn.execute(text("SELECT records_processed FROM processing_records LIMIT 1"))
                logger.info("Column 'records_processed' already exists, skipping migration")
                return True
            except Exception:
                # Column doesn't exist, proceed with migration
                logger.info("Column 'records_processed' does not exist, adding it")
            
            # Add the column
            logger.info("Adding 'records_processed' column to processing_records table")
            await conn.execute(text("""
                ALTER TABLE processing_records 
                ADD COLUMN records_processed INTEGER DEFAULT 0 NOT NULL
            """))
            
            logger.info("Successfully added 'records_processed' column")
            
            # Update existing records to have records_processed = 0
            logger.info("Updating existing records with default records_processed value")
            result = await conn.execute(text("""
                UPDATE processing_records 
                SET records_processed = 0 
                WHERE records_processed IS NULL OR records_processed = 0
            """))
            
            logger.info("Updated existing records with default records_processed value")
            
        await db_service.close()
        logger.info("Migration completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False


if __name__ == "__main__":
    import asyncio
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Run migration
    success = asyncio.run(migrate_add_records_processed_field())
    
    if success:
        print("✅ Migration completed successfully")
    else:
        print("❌ Migration failed")
        exit(1)