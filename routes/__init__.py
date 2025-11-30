"""
Routes Package
API route blueprints
"""

from .wikipedia_routes import wikipedia_bp
from .story_routes import story_bp
from .image_routes import image_bp
from .narration_routes import narration_bp
from .audio_routes import audio_bp
from .video_routes import video_bp
from .storage_routes import storage_bp
from .project_routes import project_bp

__all__ = [
    'wikipedia_bp',
    'story_bp',
    'image_bp',
    'narration_bp',
    'audio_bp',
    'video_bp',
    'storage_bp',
    'project_bp'
]

