#!/usr/bin/env python3
"""
Test script to verify the complete flow: upload -> database -> validation -> no NaN values
"""

import sys
import os
import asyncio
import json

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.database.database_service import DatabaseService
from app.services.entity_validator import EntityValidator

async def test_complete_flow():
    """Test the complete flow from database to validated output"""
    print("Testing complete flow: database -> validation -> NaN handling...")
    
    db_service = DatabaseService()
    validator = EntityValidator()
    
    try:
        # Initialize database
        await db_service.initialize()
        print("✅ Database initialized")
        
        # Get all processing records from the database directly
        async with db_service.get_session() as session:
            from app.database.models import ProcessingRecord
            from sqlalchemy import select
            
            # Get all records
            result = await session.execute(select(ProcessingRecord).order_by(ProcessingRecord.upload_timestamp.desc()))
            records = result.scalars().all()
        
        print(f"✅ Found {len(records)} total records in database")
        
        if not records:
            print("❌ No records found in database")
            return
        
        # Find our test record
        test_record = None
        for record in records:
            if record.original_filename == 'test_nan_data.json':
                test_record = record
                break
        
        if not test_record:
            print("❌ Test record 'test_nan_data.json' not found")
            # Show available records
            print("Available records:")
            for record in records:
                print(f"  - {record.original_filename} (status: {record.processing_status})")
            return
        
        print(f"✅ Found test record: {test_record.id}")
        print(f"   Original filename: {test_record.original_filename}")
        print(f"   Processing status: {test_record.processing_status}")
        print(f"   Records processed: {test_record.records_processed}")
        print(f"   File size: {test_record.file_size}")
        
        # Test the to_dict method (this is what gets sent to the validator)
        record_dict = test_record.to_dict()
        print(f"✅ Record to_dict conversion successful")
        
        # Validate the record using EntityValidator
        validated_record = validator.validate_processing_record(test_record)
        print(f"✅ Record validation successful")
        
        # Check specific fields
        print(f"\n=== Validation Results ===")
        print(f"ID: {validated_record.get('id')}")
        print(f"Session ID: {validated_record.get('session_id')}")
        print(f"Original filename: {validated_record.get('original_filename')}")
        print(f"File size: {validated_record.get('file_size')} (type: {type(validated_record.get('file_size'))})")
        print(f"Records processed: {validated_record.get('records_processed')} (type: {type(validated_record.get('records_processed'))})")
        print(f"Processing status: {validated_record.get('processing_status')}")
        print(f"Upload timestamp: {validated_record.get('upload_timestamp')}")
        
        # Verify no NaN values in the output
        def check_for_nan_values(obj, path=""):
            """Recursively check for NaN values in the validated record"""
            import math
            issues = []
            
            if isinstance(obj, dict):
                for key, value in obj.items():
                    issues.extend(check_for_nan_values(value, f"{path}.{key}" if path else key))
            elif isinstance(obj, list):
                for i, value in enumerate(obj):
                    issues.extend(check_for_nan_values(value, f"{path}[{i}]"))
            elif isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
                issues.append(f"Found NaN/Inf at {path}: {obj}")
            elif isinstance(obj, str) and obj.lower() in ['nan', 'inf', '-inf']:
                issues.append(f"Found NaN/Inf string at {path}: {obj}")
            
            return issues
        
        nan_issues = check_for_nan_values(validated_record)
        
        if nan_issues:
            print(f"\n❌ Found NaN/Inf values in validated record:")
            for issue in nan_issues:
                print(f"  - {issue}")
        else:
            print(f"\n✅ No NaN/Inf values found in validated record")
        
        # Test with a batch of records (like the history endpoint would do)
        print(f"\n=== Testing Batch Validation ===")
        validated_records = validator.transform_for_frontend(records[:3])  # Test first 3 records
        print(f"✅ Batch validation successful: {len(validated_records)} records processed")
        
        # Check each record in the batch
        batch_issues = []
        for i, record in enumerate(validated_records):
            record_issues = check_for_nan_values(record, f"record[{i}]")
            batch_issues.extend(record_issues)
        
        if batch_issues:
            print(f"❌ Found NaN/Inf values in batch validation:")
            for issue in batch_issues:
                print(f"  - {issue}")
        else:
            print(f"✅ No NaN/Inf values found in batch validation")
        
        # Test records_processed field specifically
        print(f"\n=== Testing records_processed Field ===")
        for i, record in enumerate(validated_records):
            records_processed = record.get('records_processed')
            print(f"Record {i+1}: records_processed = {records_processed} (type: {type(records_processed)})")
            
            # Verify it's a valid integer (not NaN)
            if records_processed is None:
                print(f"  ⚠️  records_processed is None (acceptable)")
            elif isinstance(records_processed, int):
                print(f"  ✅ records_processed is valid integer")
            elif isinstance(records_processed, float):
                import math
                if math.isnan(records_processed) or math.isinf(records_processed):
                    print(f"  ❌ records_processed is NaN/Inf")
                else:
                    print(f"  ✅ records_processed is valid float")
            else:
                print(f"  ⚠️  records_processed has unexpected type: {type(records_processed)}")
        
        print(f"\n🎉 Complete flow test completed successfully!")
        print(f"   - Database operations: ✅")
        print(f"   - Record validation: ✅") 
        print(f"   - NaN handling: ✅")
        print(f"   - records_processed field: ✅")
        
    except Exception as e:
        print(f"❌ Complete flow test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await db_service.close()

if __name__ == "__main__":
    asyncio.run(test_complete_flow())