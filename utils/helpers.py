"""
Helper Utilities
Common helper functions used across the application
"""

import re
import os
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger("VidyAI_Flask")


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a string to be used as a filename
    
    Args:
        filename: Original filename string
        
    Returns:
        Sanitized filename safe for all operating systems
    """
    # Replace invalid characters with underscores
    sanitized = re.sub(r'[\\/*?:"<>|]', '_', filename)
    # Limit filename length
    return sanitized[:200]


def sanitize_path(path: str) -> str:
    """
    Sanitize a file path
    
    Args:
        path: Original path string
        
    Returns:
        Sanitized path
    """
    # Replace backslashes with forward slashes
    path = path.replace('\\', '/')
    # Remove leading/trailing slashes
    path = path.strip('/')
    # Remove double slashes
    path = re.sub(r'/+', '/', path)
    return path


def validate_required_fields(data: Dict[str, Any], required_fields: list) -> Optional[str]:
    """
    Validate that required fields are present in request data
    
    Args:
        data: Request data dictionary
        required_fields: List of required field names
        
    Returns:
        Error message string if validation fails, None if valid
    """
    if not data:
        return "Request data is required"
    
    missing_fields = []
    for field in required_fields:
        if field not in data:
            missing_fields.append(field)
    
    if missing_fields:
        return f"Missing required fields: {', '.join(missing_fields)}"
    
    return None


def get_file_extension(filename: str) -> str:
    """
    Get file extension from filename
    
    Args:
        filename: Filename string
        
    Returns:
        File extension (without dot)
    """
    return os.path.splitext(filename)[1].lstrip('.').lower()


def get_content_type(filename: str) -> str:
    """
    Get MIME type from filename
    
    Args:
        filename: Filename string
        
    Returns:
        MIME type string
    """
    ext = get_file_extension(filename)
    
    content_types = {
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'gif': 'image/gif',
        'webp': 'image/webp',
        'mp3': 'audio/mpeg',
        'wav': 'audio/wav',
        'mp4': 'video/mp4',
        'avi': 'video/x-msvideo',
        'mov': 'video/quicktime',
        'json': 'application/json',
        'txt': 'text/plain',
        'md': 'text/markdown'
    }
    
    return content_types.get(ext, 'application/octet-stream')


def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to human-readable string
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string (e.g., "1m 30s")
    """
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    
    if minutes > 0:
        return f"{minutes}m {secs}s"
    return f"{secs}s"


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to maximum length
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def parse_resolution(resolution_str: str) -> tuple:
    """
    Parse resolution string to tuple
    
    Args:
        resolution_str: Resolution string (e.g., "1920x1080")
        
    Returns:
        Tuple of (width, height)
    """
    try:
        parts = resolution_str.lower().split('x')
        if len(parts) == 2:
            return (int(parts[0]), int(parts[1]))
    except:
        pass
    
    # Default resolution
    return (1920, 1080)


def estimate_words_from_duration(seconds: float, speed: float = 1.0) -> int:
    """
    Estimate word count from audio duration
    
    Args:
        seconds: Duration in seconds
        speed: Playback speed multiplier
        
    Returns:
        Estimated word count
    """
    # ~2.5 words per second at normal speed
    words = seconds * 2.5 * speed
    return int(words)


def estimate_duration_from_words(words: int, speed: float = 1.0) -> float:
    """
    Estimate audio duration from word count
    
    Args:
        words: Word count
        speed: Playback speed multiplier
        
    Returns:
        Estimated duration in seconds
    """
    # ~2.5 words per second at normal speed
    seconds = words / 2.5 / speed
    return seconds

