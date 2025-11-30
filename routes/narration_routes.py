"""
Narration API Routes
Endpoints for scene narration generation
"""

import os
import logging
from flask import Blueprint, request, jsonify
from services.narration_service import NarrationService

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
        
        # Get narration service
        narration_service = get_narration_service()
        
        # Generate narration
        narration = narration_service.generate_scene_narration(
            title, scene_prompt, scene_number, storyline,
            narration_style, voice_tone, target_seconds,
            min_words, max_words
        )
        
        return jsonify({
            'success': True,
            'narration': narration,
            'scene_number': scene_number
        }), 200
        
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
            "voice_tone": str (optional, default: "engaging")
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
        
        # Get narration service
        narration_service = get_narration_service()
        
        # Generate all narrations
        result = narration_service.generate_all_scene_narrations(
            title, scene_prompts, storyline,
            narration_style, voice_tone
        )
        
        return jsonify({
            'success': True,
            'narrations': result,
            'count': result.get('total_scenes', 0)
        }), 200
        
    except Exception as e:
        logger.error(f"Error in generate_all: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

