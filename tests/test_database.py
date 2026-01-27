#!/usr/bin/env python3
"""
Test script to verify database operations work correctly
"""

import sys
import os
import asyncio

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.database.database_service import DatabaseService

async def test_database():
    """Test database operations"""
    print("Testing database operations...")
    
    db_service = DatabaseService()
    
    try:
        # Initialize database
        print("Initializing database...")
        await db_service.initialize()
        print("✅ Database initialized")
        
        # Create a test session
        print("Creating test session...")
        session = await db_service.create_session()
        print(f"✅ Session created: {session.id}")
        
        # Create a test processing record
        print("Creating test processing record...")
        file_info = {
            'original_filename': 'test.json',
            'stored_filename': 'stored-test.json',
            'file_size': 1024,
            'file_path': '/test/path/stored-test.json',
            'metadata': {
                'test': True,
                'records_count': 5
            }
        }
        
        record = await db_service.create_processing_record(session.id, file_info)
        print(f"✅ Processing record created: {record.id}")
        print(f"   records_processed: {record.records_processed}")
        
        # Update the records_processed field
        print("Updating processing status...")
        success = await db_service.update_processing_status(record.id, "completed")
        print(f"✅ Updated processing status: {success}")
        
        # Update records_processed by modifying the record directly and committing
        print("Updating records_processed...")
        from app.database.models import ProcessingRecord
        async with db_service.get_session() as db_session:
            # Get the record again
            updated_record = await db_session.get(ProcessingRecord, record.id)
            if updated_record:
                updated_record.records_processed = 5
                await db_session.commit()
                print(f"✅ Updated records_processed to: {updated_record.records_processed}")
            else:
                print("❌ Could not find record to update")
        
        # Get processing history
        print("Getting processing history...")
        records, total_count = await db_service.get_processing_history(
            session_id=session.id,  # This is the Session model object we created
            filters={},
            page=1,
            page_size=10
        )
        print(f"✅ Found {total_count} records in history")
        
        if records:
            first_record = records[0]
            print(f"   First record ID: {first_record.id}")
            print(f"   Records processed: {first_record.records_processed}")
            print(f"   Status: {first_record.processing_status}")
        
        # Test the to_dict method
        if records:
            record_dict = first_record.to_dict()
            print(f"✅ Record to_dict works")
            print(f"   records_processed in dict: {record_dict.get('records_processed')}")
        
        print("✅ All database tests passed!")
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await db_service.close()

if __name__ == "__main__":
    asyncio.run(test_database())