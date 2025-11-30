"""
Utils Package
Utility modules and helper functions
"""

from .helpers import (
    sanitize_filename,
    sanitize_path,
    validate_required_fields,
    get_file_extension,
    get_content_type,
    format_duration,
    truncate_text,
    parse_resolution,
    estimate_words_from_duration,
    estimate_duration_from_words
)

from .validation import (
    validate_language_code,
    validate_tld,
    validate_comic_style,
    validate_target_length,
    validate_narration_style,
    validate_voice_tone,
    validate_age_group,
    validate_education_level,
    validate_bucket_name,
    validate_resolution,
    validate_fps,
    validate_speed,
    validate_num_scenes,
    validate_aspect_ratio,
    validate_positive_float,
    validate_percentage,
    RequestValidator
)

__all__ = [
    # helpers
    'sanitize_filename',
    'sanitize_path',
    'validate_required_fields',
    'get_file_extension',
    'get_content_type',
    'format_duration',
    'truncate_text',
    'parse_resolution',
    'estimate_words_from_duration',
    'estimate_duration_from_words',
    # validation
    'validate_language_code',
    'validate_tld',
    'validate_comic_style',
    'validate_target_length',
    'validate_narration_style',
    'validate_voice_tone',
    'validate_age_group',
    'validate_education_level',
    'validate_bucket_name',
    'validate_resolution',
    'validate_fps',
    'validate_speed',
    'validate_num_scenes',
    'validate_aspect_ratio',
    'validate_positive_float',
    'validate_percentage',
    'RequestValidator'
]

