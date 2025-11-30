"""
Audio API Routes
Endpoints for text-to-speech audio generation
"""

import os
import logging
import base64
from flask import Blueprint, request, jsonify
from services.tts_service import tts_service
from services.supabase_service import supabase_service

logger = logging.getLogger("VidyAI_Flask")

audio_bp = Blueprint('audio', __name__)


@audio_bp.route('/generate-scene', methods=['POST'])
def generate_scene():
    """
    Generate audio for a single scene
    
    Request JSON:
        {
            "text": str,
            "scene_number": int,
            "lang": str (optional, default: "en"),
            "tld": str (optional, default: "com"),
            "slow": bool (optional, default: false),
            "speed": float (optional, default: 1.25)
        }
    
    Response JSON:
        {
            "success": bool,
            "audio": str (base64) or null,
            "scene_number": int,
            "duration_estimate": float,
            "error": str (if failed)
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'text' not in data or 'scene_number' not in data:
            return jsonify({
                'success': False,
                'error': 'text and scene_number are required'
            }), 400
        
        text = data['text']
        scene_number = data['scene_number']
        lang = data.get('lang', 'en')
        tld = data.get('tld', 'com')
        slow = data.get('slow', False)
        speed = data.get('speed', 1.25)
        
        # Generate audio
        audio_data = tts_service.synthesize_to_mp3(text, lang, tld, slow, speed)
        
        # Estimate duration
        duration = tts_service.estimate_tts_duration_seconds(text, speed)
        
        # Convert to base64
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        
        return jsonify({
            'success': True,
            'audio': audio_base64,
            'scene_number': scene_number,
            'duration_estimate': duration
        }), 200
        
    except Exception as e:
        logger.error(f"Error in generate_scene: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@audio_bp.route('/generate-all', methods=['POST'])
def generate_all():
    """
    Generate audio for all scenes
    
    Request JSON:
        {
            "narrations": dict (from narration service),
            "lang": str (optional, default: "en"),
            "tld": str (optional, default: "com"),
            "slow": bool (optional, default: false),
            "speed": float (optional, default: 1.25),
            "upload_to_supabase": bool (optional, default: false),
            "project_name": str (optional, for supabase path)
        }
    
    Response JSON:
        {
            "success": bool,
            "audio_files": dict (scene_key -> base64) or null,
            "supabase_urls": dict (if uploaded),
            "count": int,
            "error": str (if failed)
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'narrations' not in data:
            return jsonify({
                'success': False,
                'error': 'narrations are required'
            }), 400
        
        narrations = data['narrations']
        lang = data.get('lang', 'en')
        tld = data.get('tld', 'com')
        slow = data.get('slow', False)
        speed = data.get('speed', 1.25)
        upload_to_supabase = data.get('upload_to_supabase', False)
        project_name = data.get('project_name', 'project')
        
        # Generate all audio
        scene_to_audio = tts_service.generate_scene_audios(
            narrations, lang, tld, slow, speed
        )
        
        # Convert to base64
        audio_files = {}
        for scene_key, audio_data in scene_to_audio.items():
            audio_files[scene_key] = base64.b64encode(audio_data).decode('utf-8')
        
        response = {
            'success': True,
            'audio_files': audio_files,
            'count': len(audio_files)
        }
        
        # Upload to Supabase if requested
        if upload_to_supabase:
            supabase_urls = {}
            for scene_key, audio_data in scene_to_audio.items():
                scene_num = scene_key.split('_')[1]
                path = f"{project_name}/scene_{scene_num}.mp3"
                result = supabase_service.upload_file('audio', path, audio_data, 'audio/mpeg')
                if result['success']:
                    supabase_urls[scene_key] = result['public_url']
                else:
                    supabase_urls[scene_key] = None
            
            response['supabase_urls'] = supabase_urls
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error in generate_all: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@audio_bp.route('/estimate-duration', methods=['POST'])
def estimate_duration():
    """
    Estimate audio duration from text
    
    Request JSON:
        {
            "text": str,
            "speed": float (optional, default: 1.0)
        }
    
    Response JSON:
        {
            "success": bool,
            "duration": float,
            "error": str (if failed)
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({
                'success': False,
                'error': 'text is required'
            }), 400
        
        text = data['text']
        speed = data.get('speed', 1.0)
        
        duration = tts_service.estimate_tts_duration_seconds(text, speed)
        
        return jsonify({
            'success': True,
            'duration': duration
        }), 200
        
    except Exception as e:
        logger.error(f"Error in estimate_duration: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

