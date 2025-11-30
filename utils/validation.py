"""
Validation Utilities
Request validation and data validation functions
"""

import logging
from typing import Any, Dict, Optional, List

logger = logging.getLogger("VidyAI_Flask")


def validate_language_code(lang: str) -> bool:
    """Validate language code"""
    valid_languages = ["en", "hi", "es", "fr", "de", "it", "pt", "ru", "ja", "zh-CN", "zh"]
    return lang in valid_languages


def validate_tld(tld: str) -> bool:
    """Validate top-level domain"""
    valid_tlds = ["com", "co.uk", "co.in", "com.au", "ca", "co.za"]
    return tld in valid_tlds


def validate_comic_style(style: str) -> bool:
    """Validate comic style"""
    valid_styles = [
        "western comic", "manga", "comic book", "noir comic", 
        "superhero comic", "indie comic", "cartoon", "graphic novel",
        "golden age comic", "modern comic", "manhwa", "european", "retro"
    ]
    return style.lower() in [s.lower() for s in valid_styles]


def validate_target_length(length: str) -> bool:
    """Validate story target length"""
    valid_lengths = ["short", "medium", "long"]
    return length.lower() in valid_lengths


def validate_narration_style(style: str) -> bool:
    """Validate narration style"""
    valid_styles = ["dramatic", "educational", "storytelling", "documentary"]
    return style.lower() in valid_styles


def validate_voice_tone(tone: str) -> bool:
    """Validate voice tone"""
    valid_tones = ["engaging", "serious", "playful", "informative"]
    return tone.lower() in valid_tones


def validate_age_group(age_group: str) -> bool:
    """Validate age group"""
    valid_groups = ["kids", "teens", "general", "adult"]
    return age_group.lower() in valid_groups


def validate_education_level(level: str) -> bool:
    """Validate education level"""
    valid_levels = ["basic", "standard", "advanced"]
    return level.lower() in valid_levels


def validate_bucket_name(bucket: str) -> bool:
    """Validate Supabase bucket name"""
    valid_buckets = ["images", "audio", "video", "metadata", "text"]
    return bucket in valid_buckets


def validate_resolution(resolution: List[int]) -> bool:
    """Validate video resolution"""
    if not isinstance(resolution, list) or len(resolution) != 2:
        return False
    
    width, height = resolution
    
    # Check if reasonable values
    if not (320 <= width <= 7680 and 240 <= height <= 4320):
        return False
    
    return True


def validate_fps(fps: int) -> bool:
    """Validate frames per second"""
    valid_fps = [24, 25, 30, 50, 60]
    return fps in valid_fps


def validate_speed(speed: float) -> bool:
    """Validate audio speed multiplier"""
    return 0.5 <= speed <= 2.0


def validate_num_scenes(num_scenes: int) -> bool:
    """Validate number of scenes"""
    return 3 <= num_scenes <= 20


def validate_aspect_ratio(aspect_ratio: str) -> bool:
    """Validate aspect ratio"""
    valid_ratios = ["16:9", "4:3", "1:1", "21:9"]
    return aspect_ratio in valid_ratios


def validate_positive_float(value: float) -> bool:
    """Validate positive float value"""
    return isinstance(value, (int, float)) and value > 0


def validate_percentage(value: float) -> bool:
    """Validate percentage value (0-1)"""
    return isinstance(value, (int, float)) and 0 <= value <= 1


class RequestValidator:
    """Request validation helper class"""
    
    @staticmethod
    def validate_wikipedia_search(data: Dict[str, Any]) -> Optional[str]:
        """Validate Wikipedia search request"""
        if not data or 'query' not in data:
            return "Query is required"
        
        if not data['query'] or not data['query'].strip():
            return "Query cannot be empty"
        
        if 'language' in data and not validate_language_code(data['language']):
            return f"Invalid language code: {data['language']}"
        
        if 'results_limit' in data:
            limit = data['results_limit']
            if not isinstance(limit, int) or limit < 1 or limit > 50:
                return "results_limit must be between 1 and 50"
        
        return None
    
    @staticmethod
    def validate_story_generation(data: Dict[str, Any]) -> Optional[str]:
        """Validate story generation request"""
        if not data:
            return "Request data is required"
        
        if 'title' not in data or not data['title']:
            return "Title is required"
        
        if 'content' not in data or not data['content']:
            return "Content is required"
        
        if 'target_length' in data and not validate_target_length(data['target_length']):
            return f"Invalid target_length: {data['target_length']}"
        
        if 'comic_style' in data and not validate_comic_style(data['comic_style']):
            return f"Invalid comic_style: {data['comic_style']}"
        
        if 'num_scenes' in data and not validate_num_scenes(data['num_scenes']):
            return "num_scenes must be between 3 and 20"
        
        if 'age_group' in data and not validate_age_group(data['age_group']):
            return f"Invalid age_group: {data['age_group']}"
        
        if 'education_level' in data and not validate_education_level(data['education_level']):
            return f"Invalid education_level: {data['education_level']}"
        
        return None
    
    @staticmethod
    def validate_narration_generation(data: Dict[str, Any]) -> Optional[str]:
        """Validate narration generation request"""
        if not data:
            return "Request data is required"
        
        if 'title' not in data or not data['title']:
            return "Title is required"
        
        if 'scene_prompts' in data:
            if not isinstance(data['scene_prompts'], list) or not data['scene_prompts']:
                return "scene_prompts must be a non-empty list"
        
        if 'narration_style' in data and not validate_narration_style(data['narration_style']):
            return f"Invalid narration_style: {data['narration_style']}"
        
        if 'voice_tone' in data and not validate_voice_tone(data['voice_tone']):
            return f"Invalid voice_tone: {data['voice_tone']}"
        
        return None
    
    @staticmethod
    def validate_audio_generation(data: Dict[str, Any]) -> Optional[str]:
        """Validate audio generation request"""
        if not data:
            return "Request data is required"
        
        if 'text' in data and (not data['text'] or not data['text'].strip()):
            return "text cannot be empty"
        
        if 'lang' in data and not validate_language_code(data['lang']):
            return f"Invalid language code: {data['lang']}"
        
        if 'tld' in data and not validate_tld(data['tld']):
            return f"Invalid TLD: {data['tld']}"
        
        if 'speed' in data and not validate_speed(data['speed']):
            return "speed must be between 0.5 and 2.0"
        
        return None
    
    @staticmethod
    def validate_video_generation(data: Dict[str, Any]) -> Optional[str]:
        """Validate video generation request"""
        if not data:
            return "Request data is required"
        
        if 'images' not in data or not isinstance(data['images'], list) or not data['images']:
            return "images must be a non-empty list"
        
        if 'scene_audio' not in data or not isinstance(data['scene_audio'], dict):
            return "scene_audio must be a dictionary"
        
        if 'title' not in data or not data['title']:
            return "title is required"
        
        if 'fps' in data and not validate_fps(data['fps']):
            return "fps must be one of: 24, 25, 30, 50, 60"
        
        if 'resolution' in data and not validate_resolution(data['resolution']):
            return "Invalid resolution"
        
        if 'crossfade_sec' in data and not validate_positive_float(data['crossfade_sec']):
            return "crossfade_sec must be positive"
        
        if 'bg_music_volume' in data and not validate_percentage(data['bg_music_volume']):
            return "bg_music_volume must be between 0 and 1"
        
        return None
    
    @staticmethod
    def validate_storage_operation(data: Dict[str, Any], operation: str) -> Optional[str]:
        """Validate storage operation request"""
        if not data:
            return "Request data is required"
        
        if 'bucket' not in data or not data['bucket']:
            return "bucket is required"
        
        if not validate_bucket_name(data['bucket']):
            return f"Invalid bucket name: {data['bucket']}"
        
        if operation in ['upload', 'download', 'delete', 'get-url']:
            if 'path' not in data or not data['path']:
                return "path is required"
        
        if operation == 'upload':
            if 'file_data' not in data or not data['file_data']:
                return "file_data is required"
        
        return None

