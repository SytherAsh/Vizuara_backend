"""
Progress Tracking Service
Simple in-memory progress tracker for long-running operations
"""

from typing import Dict, Optional
import time
import threading

class ProgressTracker:
    """Thread-safe progress tracker for operations"""
    
    def __init__(self):
        self._progress: Dict[str, Dict] = {}
        self._lock = threading.Lock()
    
    def set_progress(self, task_id: str, progress: int, message: str = "", current: int = 0, total: int = 0):
        """Set progress for a task
        
        Args:
            task_id: Unique task identifier
            progress: Progress percentage (0-100)
            message: Status message
            current: Current item number
            total: Total items
        """
        with self._lock:
            self._progress[task_id] = {
                "progress": max(0, min(100, progress)),
                "message": message,
                "current": current,
                "total": total,
                "timestamp": time.time()
            }
    
    def get_progress(self, task_id: str) -> Optional[Dict]:
        """Get current progress for a task"""
        with self._lock:
            return self._progress.get(task_id)
    
    def clear_progress(self, task_id: str):
        """Clear progress for a task"""
        with self._lock:
            if task_id in self._progress:
                del self._progress[task_id]
    
    def cleanup_old(self, max_age_seconds: int = 3600):
        """Remove old progress entries (older than max_age_seconds)"""
        current_time = time.time()
        with self._lock:
            to_remove = [
                task_id for task_id, data in self._progress.items()
                if current_time - data["timestamp"] > max_age_seconds
            ]
            for task_id in to_remove:
                del self._progress[task_id]

# Global progress tracker instance
progress_tracker = ProgressTracker()

