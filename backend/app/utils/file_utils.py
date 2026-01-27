"""
File handling utilities
"""

import json
import yaml
from typing import Any, Dict, List, Union
import os

def parse_date_edition_file(file_content: str, file_extension: str) -> Dict[str, Any]:
    """
    Parse date and edition file content based on file type
    
    Args:
        file_content: Content of the file as string
        file_extension: File extension (.json, .yaml, .yml, .txt)
        
    Returns:
        Parsed data structure
    """
    try:
        if file_extension.lower() in ['.json']:
            return json.loads(file_content)
        elif file_extension.lower() in ['.yaml', '.yml']:
            return yaml.safe_load(file_content)
        elif file_extension.lower() in ['.txt']:
            # Parse as plain text list (one date per line)
            lines = [line.strip() for line in file_content.split('\n') if line.strip()]
            return {"dates": lines}
        else:
            raise ValueError(f"Unsupported file extension: {file_extension}")
            
    except Exception as e:
        raise ValueError(f"Error parsing file content: {str(e)}")

def validate_file_size(file_size: int, max_size_mb: int = 50) -> bool:
    """
    Validate file size
    
    Args:
        file_size: Size of file in bytes
        max_size_mb: Maximum allowed size in MB
        
    Returns:
        True if file size is valid
    """
    max_size_bytes = max_size_mb * 1024 * 1024
    return file_size <= max_size_bytes

def get_safe_filename(filename: str) -> str:
    """
    Get a safe filename by removing potentially dangerous characters
    
    Args:
        filename: Original filename
        
    Returns:
        Safe filename
    """
    # Remove path separators and other potentially dangerous characters
    safe_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-_"
    safe_filename = "".join(c for c in filename if c in safe_chars)
    
    # Ensure filename is not empty and has reasonable length
    if not safe_filename:
        safe_filename = "uploaded_file"
    
    return safe_filename[:100]  # Limit length