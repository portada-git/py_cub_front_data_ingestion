#!/usr/bin/env python3
"""
Test script to verify EntityValidator handles NaN values correctly
"""

import sys
import os
import math
import json

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.entity_validator import EntityValidator

def test_nan_handling():
    """Test that EntityValidator properly handles NaN values"""
    validator = EntityValidator()
    
    print("Testing EntityValidator NaN handling...")
    
    # Test _validate_integer with various NaN-like values
    test_cases_int = [
        (None, 0, "None"),
        (100, 100, "Valid integer"),
        ("150", 150, "String integer"),
        ("NaN", 0, "String 'NaN'"),
        ("nan", 0, "String 'nan'"),
        ("", 0, "Empty string"),
        ("null", 0, "String 'null'"),
        (float('nan'), 0, "Float NaN"),
        (float('inf'), 0, "Float infinity"),
        (float('-inf'), 0, "Float negative infinity"),
    ]
    
    print("\n=== Testing _validate_integer ===")
    for value, expected, description in test_cases_int:
        try:
            result = validator._validate_integer(value, 0)
            status = "✅ PASS" if result == expected else f"❌ FAIL (got {result})"
            print(f"{status}: {description} -> {result}")
        except Exception as e:
            print(f"❌ ERROR: {description} -> Exception: {e}")
    
    # Test _validate_float with various NaN-like values
    test_cases_float = [
        (None, 0.0, "None"),
        (100.5, 100.5, "Valid float"),
        ("150.75", 150.75, "String float"),
        ("NaN", 0.0, "String 'NaN'"),
        ("nan", 0.0, "String 'nan'"),
        ("inf", 0.0, "String 'inf'"),
        ("-inf", 0.0, "String '-inf'"),
        ("", 0.0, "Empty string"),
        ("null", 0.0, "String 'null'"),
        (float('nan'), 0.0, "Float NaN"),
        (float('inf'), 0.0, "Float infinity"),
        (float('-inf'), 0.0, "Float negative infinity"),
    ]
    
    print("\n=== Testing _validate_float ===")
    for value, expected, description in test_cases_float:
        try:
            result = validator._validate_float(value, 0.0)
            status = "✅ PASS" if result == expected else f"❌ FAIL (got {result})"
            print(f"{status}: {description} -> {result}")
        except Exception as e:
            print(f"❌ ERROR: {description} -> Exception: {e}")
    
    # Test with a mock processing record that has NaN values
    print("\n=== Testing Processing Record with NaN values ===")
    
    class MockProcessingRecord:
        def __init__(self):
            self.id = "test-123"
            self.session_id = "session-456"
            self.original_filename = "test.json"
            self.stored_filename = "stored-test.json"
            self.file_size = float('nan')  # This should be handled
            self.file_path = "/test/path"
            self.upload_timestamp = "2025-01-26T23:00:00Z"
            self.processing_status = "completed"
            self.processing_started_at = "2025-01-26T23:00:00Z"
            self.processing_completed_at = "2025-01-26T23:01:00Z"
            self.processing_duration_seconds = float('nan')  # This should be handled
            self.records_processed = "NaN"  # This should be handled
            self.error_message = None
            self.retry_count = 0
            self.record_metadata = {}
            self.is_complete = True
        
        def to_dict(self):
            return {
                'id': self.id,
                'session_id': self.session_id,
                'original_filename': self.original_filename,
                'stored_filename': self.stored_filename,
                'file_size': self.file_size,
                'file_path': self.file_path,
                'upload_timestamp': self.upload_timestamp,
                'processing_status': self.processing_status,
                'processing_started_at': self.processing_started_at,
                'processing_completed_at': self.processing_completed_at,
                'processing_duration_seconds': self.processing_duration_seconds,
                'records_processed': self.records_processed,
                'error_message': self.error_message,
                'retry_count': self.retry_count,
                'metadata': self.record_metadata,
                'is_complete': self.is_complete
            }
    
    mock_record = MockProcessingRecord()
    
    try:
        validated_record = validator.validate_processing_record(mock_record)
        print("✅ Processing record validation completed")
        
        # Check specific fields that should have been cleaned
        file_size = validated_record.get('file_size')
        duration = validated_record.get('processing_duration_seconds')
        records_processed = validated_record.get('records_processed')
        
        print(f"  file_size: {file_size} (should be 0)")
        print(f"  processing_duration_seconds: {duration} (should be None)")
        print(f"  records_processed: {records_processed} (should be 0)")
        
        # Verify no NaN values in the output
        def check_for_nan(obj, path=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    check_for_nan(value, f"{path}.{key}" if path else key)
            elif isinstance(obj, list):
                for i, value in enumerate(obj):
                    check_for_nan(value, f"{path}[{i}]")
            elif isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
                print(f"❌ Found NaN/Inf at {path}: {obj}")
                return False
            elif isinstance(obj, str) and obj.lower() in ['nan', 'inf', '-inf']:
                print(f"❌ Found NaN/Inf string at {path}: {obj}")
                return False
            return True
        
        if check_for_nan(validated_record):
            print("✅ No NaN values found in validated record")
        else:
            print("❌ NaN values still present in validated record")
        
        # Print the full validated record for inspection
        print(f"\nValidated record: {json.dumps(validated_record, indent=2, default=str)}")
        
    except Exception as e:
        print(f"❌ ERROR validating processing record: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_nan_handling()