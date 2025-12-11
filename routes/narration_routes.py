"""
Narration API Routes
Endpoints for scene narration generation
"""

import os
import logging
from flask import Blueprint, request, jsonify
from services.narration_service import NarrationService
from services.supabase_service import supabase_service
from utils.helpers import sanitize_filename

logger = logging.getLogger("VidyAI_Flask")

narration_bp = Blueprint('narration', __name__)


def get_narration_service():
    """Get or create narration service instance with API key"""
    api_key = os.getenv('GROQ_API_KEY')
    if not api_key:
        raise ValueError('GROQ_API_KEY not found in environment variables')
    return NarrationService(api_key)


@narration_bp.route('/generate-scene', methods=['POST'])
def generate_scene():
    """
    Generate narration for a single scene
    
    Request JSON:
        {
            "title": str,
            "scene_prompt": str,
            "scene_number": int,
            "storyline": str (optional),
            "narration_style": str (optional, default: "dramatic"),
            "voice_tone": str (optional, default: "engaging"),
            "target_seconds": int (optional, default: 20),
            "min_words": int (optional, default: 40),
            "max_words": int (optional, default: 70)
        }
    
    Response JSON:
        {
            "success": bool,
            "narration": str or null,
            "scene_number": int,
            "error": str (if failed)
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'title' not in data or 'scene_prompt' not in data or 'scene_number' not in data:
            return jsonify({
                'success': False,
                'error': 'title, scene_prompt, and scene_number are required'
            }), 400
        
        title = data['title']
        scene_prompt = data['scene_prompt']
        scene_number = data['scene_number']
        storyline = data.get('storyline', '')
        narration_style = data.get('narration_style', 'dramatic')
        voice_tone = data.get('voice_tone', 'engaging')
        target_seconds = data.get('target_seconds', 20)
        min_words = data.get('min_words', 40)
        max_words = data.get('max_words', 70)
        upload_to_supabase = data.get('upload_to_supabase', False)
        project_name = sanitize_filename(data.get('project_name', title))
        
        # Get narration service
        narration_service = get_narration_service()
        
        # Generate narration
        narration = narration_service.generate_scene_narration(
            title, scene_prompt, scene_number, storyline,
            narration_style, voice_tone, target_seconds,
            min_words, max_words
        )

        response = {
            'success': True,
            'narration': narration,
            'scene_number': scene_number
        }

        if upload_to_supabase and narration:
            try:
                path = f"{project_name}/scene_{scene_number}_narration.txt"
                upload_result = supabase_service.upload_file(
                    'text',
                    path,
                    narration.encode('utf-8'),
                    'text/plain'
                )
                response['subtitles_path'] = path
                response['subtitles_url'] = upload_result.get('public_url')
            except Exception as e:
                logger.warning(f"Failed to upload narration text for scene {scene_number}: {e}")
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error in generate_scene: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@narration_bp.route('/generate-all', methods=['POST'])
def generate_all():
    """
    Generate narrations for all scenes
    
    Request JSON:
        {
            "title": str,
            "scene_prompts": list[str],
            "storyline": str (optional),
            "narration_style": str (optional, default: "dramatic"),
            "voice_tone": str (optional, default: "engaging"),
            "narration_length": str (optional, default: "medium", choices: "short", "medium", "long"),
            "target_duration": int (optional, default: 20),
            "min_words": int (optional, default: 40),
            "max_words": int (optional, default: 70),
            "emotion_level": str (optional, default: "moderate", choices: "subtle", "moderate", "expressive"),
            "pace_variation": str (optional, default: "varied", choices: "consistent", "varied", "dynamic"),
            "pause_style": str (optional, default: "natural", choices: "minimal", "natural", "dramatic"),
            "pronunciation_style": str (optional, default: "clear", choices: "standard", "clear", "precise")
        }
    
    Response JSON:
        {
            "success": bool,
            "narrations": dict or null,
            "count": int,
            "error": str (if failed)
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'title' not in data or 'scene_prompts' not in data:
            return jsonify({
                'success': False,
                'error': 'title and scene_prompts are required'
            }), 400
        
        title = data['title']
        scene_prompts = data['scene_prompts']
        storyline = data.get('storyline', '')
        narration_style = data.get('narration_style', 'dramatic')
        voice_tone = data.get('voice_tone', 'engaging')
        narration_length = data.get('narration_length', 'medium')
        target_duration = data.get('target_duration', 20)
        min_words = data.get('min_words', 40)
        max_words = data.get('max_words', 70)
        emotion_level = data.get('emotion_level', 'moderate')
        pace_variation = data.get('pace_variation', 'varied')
        pause_style = data.get('pause_style', 'natural')
        pronunciation_style = data.get('pronunciation_style', 'clear')
        upload_to_supabase = data.get('upload_to_supabase', False)
        project_name = sanitize_filename(data.get('project_name', title))
        
        # Get narration service
        narration_service = get_narration_service()
        
        # Generate all narrations with all customization options
        result = narration_service.generate_all_scene_narrations(
            title=title,
            scene_prompts=scene_prompts,
            storyline=storyline,
            narration_style=narration_style,
            voice_tone=voice_tone,
            narration_length=narration_length,
            target_duration=target_duration,
            min_words=min_words,
            max_words=max_words,
            emotion_level=emotion_level,
            pace_variation=pace_variation,
            pause_style=pause_style,
            pronunciation_style=pronunciation_style
        )

        response = {
            'success': True,
            'narrations': result,
            'count': result.get('total_scenes', 0),
            'title_sanitized': project_name
        }

        if upload_to_supabase:
            uploaded_paths = {}
            narrs = result.get('narrations', {})
            for scene_key, scene_data in narrs.items():
                scene_num = scene_data.get('scene_number')
                narration_text = (scene_data.get('narration') or "").strip()
                if not narration_text:
                    continue
                path = f"{project_name}/scene_{scene_num}_narration.txt"
                try:
                    upload_result = supabase_service.upload_file(
                        'text',
                        path,
                        narration_text.encode('utf-8'),
                        'text/plain'
                    )
                    uploaded_paths[scene_key] = {
                        'path': path,
                        'public_url': upload_result.get('public_url')
                    }
                except Exception as e:
                    logger.warning(f"Failed to upload narration text for scene {scene_num}: {e}")
            response['subtitles_paths'] = uploaded_paths
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error in generate_all: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

