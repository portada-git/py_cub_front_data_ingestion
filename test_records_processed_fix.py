#!/usr/bin/env python3
"""
Test to verify that records_processed is correctly populated in task_info
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / 'backend'))

from app.services.task_service import task_service, TaskType, TaskPriority
from app.services.portada_service import portada_service
from app.models.ingestion import IngestionRequest, IngestionType


async def test_records_processed():
    """Test that records_processed is populated correctly"""
    
    # Use a small test file
    test_file = Path('.data/converted/1914_traversing_converted.json')
    
    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return False
    
    print("=" * 70)
    print("🧪 Testing records_processed Fix")
    print("=" * 70)
    print()
    
    # Create a task
    task_id = task_service.create_task(
        task_type=TaskType.INGESTION,
        title="Test Ingestion",
        description="Testing records_processed field",
        priority=TaskPriority.NORMAL,
        metadata={"test": True},
        user_id="test_user",
        file_name="test_file.json",
        file_size=1000
    )
    
    print(f"✅ Task created: {task_id}")
    
    # Check initial state
    task_info = task_service.get_task_status(task_id)
    print(f"📊 Initial state:")
    print(f"   status: {task_info.status}")
    print(f"   records_processed: {task_info.records_processed}")
    print()
    
    # Define the ingestion function
    async def process_ingestion(task_info, file_path):
        """Simulate ingestion"""
        print(f"🚀 Starting ingestion...")
        
        result = await portada_service.ingest_extraction_data(
            file_path=str(file_path),
            newspaper="DM",
            data_path_delta_lake="ship_entries"
        )
        
        print(f"✅ Ingestion completed")
        print(f"   Result: {result}")
        
        return result
    
    # Execute the task
    await task_service.execute_task(
        task_id,
        process_ingestion,
        test_file
    )
    
    # Check final state
    task_info = task_service.get_task_status(task_id)
    print()
    print(f"📊 Final state:")
    print(f"   status: {task_info.status}")
    print(f"   records_processed: {task_info.records_processed}")
    print(f"   result: {task_info.result}")
    print()
    
    # Verify the fix worked
    if task_info.records_processed and task_info.records_processed > 0:
        print(f"✅ SUCCESS! records_processed is populated: {task_info.records_processed}")
        return True
    else:
        print(f"❌ FAILED! records_processed is still None or 0")
        return False


async def main():
    success = await test_records_processed()
    print()
    print("=" * 70)
    if success:
        print("✅ TEST PASSED - records_processed fix is working!")
    else:
        print("❌ TEST FAILED - records_processed is not being populated")
    print("=" * 70)
    
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
