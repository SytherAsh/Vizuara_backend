"""
Video API Routes
Endpoints for video compilation from images and audio
"""

import os
import logging
import base64
import json
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file
from io import BytesIO
from services.video_service import video_service
from services.supabase_service import supabase_service
from utils.helpers import sanitize_filename

logger = logging.getLogger("VidyAI_Flask")

video_bp = Blueprint('video', __name__)


@video_bp.route('/build', methods=['POST'])
def build_video():
    """
    Build video from images and audio
    
    Request JSON:
        {
            "images": list[str] (base64 encoded),
            "scene_audio": dict (scene_key -> base64 audio),
            "title": str,
            "narrations": dict or list (optional, for subtitle generation),
            "fps": int (optional, default: 30),
            "resolution": list[int, int] (optional, default: [1920, 1080]),
            "crossfade_sec": float (optional, default: 0.3),
            "min_scene_seconds": float (optional, default: 2.0),
            "head_pad": float (optional, default: 0.15),
            "tail_pad": float (optional, default: 0.15),
            "bg_music": str (optional, base64),
            "bg_music_volume": float (optional, default: 0.08),
            "ken_burns": bool (optional, default: true),
            "kb_zoom_start": float (optional, default: 1.05),
            "kb_zoom_end": float (optional, default: 1.15),
            "kb_pan": str (optional, default: "auto", choices: "auto", "left", "right", "up", "down", "none"),
            "upload_to_supabase": bool (optional, default: false),
            "project_name": str (optional, for supabase path),
            "generate_subtitles": bool (optional, default: same as upload_to_supabase)
        }
    
    Response JSON:
        {
            "success": bool,
            "video": str (base64) or null,
            "supabase_url": str (if uploaded),
            "error": str (if failed)
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'images' not in data or 'scene_audio' not in data or 'title' not in data:
            return jsonify({
                'success': False,
                'error': 'images, scene_audio, and title are required'
            }), 400
        
        # Decode images from base64
        images_base64 = data['images']
        images = []
        for img_b64 in images_base64:
            if img_b64:
                images.append(base64.b64decode(img_b64))
            else:
                images.append(None)
        
        # Decode audio from base64
        scene_audio_base64 = data['scene_audio']
        scene_audio = {}
        for scene_key, audio_b64 in scene_audio_base64.items():
            if audio_b64:
                scene_audio[scene_key] = base64.b64decode(audio_b64)
            else:
                scene_audio[scene_key] = None
        
        title = data['title']
        fps = data.get('fps', 30)
        resolution = tuple(data.get('resolution', [1920, 1080]))
        crossfade_sec = data.get('crossfade_sec', 0.3)
        min_scene_seconds = data.get('min_scene_seconds', 2.0)
        head_pad = data.get('head_pad', 0.15)
        tail_pad = data.get('tail_pad', 0.15)
        bg_music_volume = data.get('bg_music_volume', 0.08)
        ken_burns = data.get('ken_burns', True)
        kb_zoom_start = data.get('kb_zoom_start', 1.05)
        kb_zoom_end = data.get('kb_zoom_end', 1.15)
        kb_pan = data.get('kb_pan', 'auto')
        upload_to_supabase = data.get('upload_to_supabase', False)
        title_sanitized = sanitize_filename(data.get('project_name', title))
        generate_subtitles = data.get('generate_subtitles', upload_to_supabase)
        
        # Decode background music if provided
        bg_music_data = None
        if 'bg_music' in data and data['bg_music']:
            bg_music_data = base64.b64decode(data['bg_music'])
        
        # Extract narrations for subtitle generation
        # Narrations can come in different formats:
        # 1. Dict with scene keys: {"scene_1": {"narration": "text"}, ...}
        # 2. List of narration texts: ["text1", "text2", ...]
        # 3. Dict with narrations nested: {"narrations": {"scene_1": {...}}}
        subtitle_narrations_list = None
        if generate_subtitles and 'narrations' in data:
            narrations_data = data['narrations']
            subtitle_narrations_list = []
            
            # Handle dict format with scene keys
            if isinstance(narrations_data, dict):
                # Check if it's nested format: {"narrations": {"scene_1": {...}}}
                if 'narrations' in narrations_data:
                    narrations_data = narrations_data['narrations']
                
                # Extract narration texts in order (scene_1, scene_2, ...)
                num_scenes = len(images)
                for i in range(1, num_scenes + 1):
                    scene_key = f"scene_{i}"
                    if scene_key in narrations_data:
                        scene_data = narrations_data[scene_key]
                        # Handle both {"narration": "text"} and direct text
                        if isinstance(scene_data, dict):
                            narration_text = scene_data.get('narration', '')
                        else:
                            narration_text = str(scene_data)
                        subtitle_narrations_list.append(narration_text)
                    else:
                        subtitle_narrations_list.append('')
            
            # Handle list format
            elif isinstance(narrations_data, list):
                subtitle_narrations_list = [str(n) for n in narrations_data]
                # Pad or truncate to match number of images
                num_scenes = len(images)
                while len(subtitle_narrations_list) < num_scenes:
                    subtitle_narrations_list.append('')
                subtitle_narrations_list = subtitle_narrations_list[:num_scenes]
        
        # Build video with all customization options and optional subtitles
        video_result = video_service.build_video(
            images=images,
            scene_audio=scene_audio,
            title=title,
            fps=fps,
            resolution=resolution,
            crossfade_sec=crossfade_sec,
            min_scene_seconds=min_scene_seconds,
            head_pad=head_pad,
            tail_pad=tail_pad,
            bg_music_data=bg_music_data,
            bg_music_volume=bg_music_volume,
            ken_burns=ken_burns,
            kb_zoom_start=kb_zoom_start,
            kb_zoom_end=kb_zoom_end,
            kb_pan=kb_pan,
            title_sanitized=title_sanitized,
            generate_subtitles=generate_subtitles,
            return_subtitles=True,
            subtitle_narrations=subtitle_narrations_list
        )

        if isinstance(video_result, dict):
            video_data = video_result.get('video_data')
            subtitles_bytes = video_result.get('subtitles_bytes')
            timings = video_result.get('timings')
        else:
            video_data = video_result
            subtitles_bytes = None
            timings = None

        # Convert to base64
        video_base64 = base64.b64encode(video_data).decode('utf-8') if video_data else None
        subtitles_base64 = base64.b64encode(subtitles_bytes).decode('utf-8') if subtitles_bytes else None
        
        response = {
            'success': True,
            'video': video_base64,
            'title_sanitized': title_sanitized,
            'timings': timings
        }
        if subtitles_base64:
            response['subtitles'] = subtitles_base64
        
        # Upload to Supabase if requested
        if upload_to_supabase and video_data:
            video_path = f"{title_sanitized}/{title_sanitized}.mp4"
            result = supabase_service.upload_file('video', video_path, video_data, 'video/mp4')
            if result['success']:
                response['video_path'] = video_path
                response['supabase_url'] = result['public_url']

            # Upload subtitles to video bucket alongside MP4
            subtitles_url = None
            subtitles_path = None
            if subtitles_bytes:
                subtitles_path = f"{title_sanitized}/{title_sanitized}.srt"
                sub_result = supabase_service.upload_file(
                    'video',
                    subtitles_path,
                    subtitles_bytes,
                    'text/plain'
                )
                if sub_result.get('success'):
                    subtitles_url = sub_result.get('public_url')
                response['subtitles_path'] = subtitles_path
                response['subtitles_url'] = subtitles_url

            # Store metadata if provided
            if 'storyline' in data or 'scene_prompts' in data:
                try:
                    metadata = {
                        'title': title,
                        'project_name': title_sanitized,
                        'created_at': datetime.now().isoformat(),
                        'video_path': video_path,
                        'video_url': result.get('public_url', '') if result.get('success') else '',
                        'subtitles_path': subtitles_path,
                        'subtitles_url': subtitles_url,
                        'fps': fps,
                        'resolution': list(resolution),
                        'num_scenes': len(images)
                    }
                    
                    if 'storyline' in data:
                        metadata['storyline'] = data['storyline']
                    if 'scene_prompts' in data:
                        metadata['scene_prompts'] = data['scene_prompts']
                    if 'wikiUrl' in data:
                        metadata['wikiUrl'] = data['wikiUrl']
                    if 'wikiTitle' in data:
                        metadata['wikiTitle'] = data['wikiTitle']
                    
                    metadata_json = json.dumps(metadata, indent=2)
                    metadata_path = f"{title_sanitized}/metadata.json"
                    metadata_result = supabase_service.upload_file(
                        'metadata', 
                        metadata_path, 
                        metadata_json.encode('utf-8'), 
                        'application/json'
                    )
                    if metadata_result['success']:
                        logger.info(f"Metadata stored for project: {title_sanitized}")
                except Exception as e:
                    logger.warning(f"Failed to store metadata: {e}")
            
            # Store text files (storyline and scene prompts) if provided
            try:
                if 'storyline' in data and data['storyline']:
                    storyline_text = f"# {title} - Comic Storyline\n\n{data['storyline']}"
                    storyline_path = f"{title_sanitized}/storyline.txt"
                    storyline_result = supabase_service.upload_file(
                        'text',
                        storyline_path,
                        storyline_text.encode('utf-8'),
                        'text/plain'
                    )
                    if storyline_result['success']:
                        logger.info(f"Storyline text stored for project: {title_sanitized}")
                
                if 'scene_prompts' in data and data['scene_prompts']:
                    scene_prompts_text = f"# {title} - Scene Prompts\n\n"
                    for i, prompt in enumerate(data['scene_prompts'], 1):
                        scene_prompts_text += f"## Scene {i}\n{prompt}\n\n{'='*50}\n\n"
                    scene_prompts_path = f"{title_sanitized}/scene_prompts.txt"
                    scene_prompts_result = supabase_service.upload_file(
                        'text',
                        scene_prompts_path,
                        scene_prompts_text.encode('utf-8'),
                        'text/plain'
                    )
                    if scene_prompts_result['success']:
                        logger.info(f"Scene prompts text stored for project: {title_sanitized}")
            except Exception as e:
                logger.warning(f"Failed to store text files: {e}")
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error in build_video: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@video_bp.route('/build-from-supabase', methods=['POST'])
def build_from_supabase():
    """
    Build video from assets stored in Supabase
    
    Request JSON:
        {
            "project_name": str,
            "title": str,
            "num_scenes": int,
            "fps": int (optional),
            "resolution": list[int, int] (optional),
            "other_video_params": ... (same as /build)
        }
    
    Response JSON:
        {
            "success": bool,
            "video": str (base64) or null,
            "supabase_url": str (if uploaded),
            "error": str (if failed)
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'project_name' not in data or 'title' not in data or 'num_scenes' not in data:
            return jsonify({
                'success': False,
                'error': 'project_name, title, and num_scenes are required'
            }), 400
        
        project_name = data['project_name']
        title = data['title']
        num_scenes = data['num_scenes']
        title_sanitized = sanitize_filename(project_name or title)
        
        # Download images from Supabase
        images = []
        for i in range(1, num_scenes + 1):
            path = f"{title_sanitized}/scene_{i}.jpg"
            img_result = supabase_service.download_file('images', path)
            images.append(img_result.get('file_data') if img_result.get('success') else None)
        
        # Download audio from Supabase
        scene_audio = {}
        for i in range(1, num_scenes + 1):
            scene_key = f"scene_{i}"
            path = f"{title_sanitized}/scene_{i}.mp3"
            audio_result = supabase_service.download_file('audio', path)
            if audio_result.get('success') and audio_result.get('file_data'):
                scene_audio[scene_key] = audio_result['file_data']
        
        # Build video with downloaded assets
        fps = data.get('fps', 30)
        resolution = tuple(data.get('resolution', [1920, 1080]))
        video_result = video_service.build_video(
            images=images,
            scene_audio=scene_audio,
            title=title,
            fps=fps,
            resolution=resolution,
            title_sanitized=title_sanitized,
            generate_subtitles=True,
            return_subtitles=True
        )

        if isinstance(video_result, dict):
            video_data = video_result.get('video_data')
            subtitles_bytes = video_result.get('subtitles_bytes')
            timings = video_result.get('timings')
        else:
            video_data = video_result
            subtitles_bytes = None
            timings = None
        
        # Upload to Supabase
        video_path = f"{title_sanitized}/{title_sanitized}.mp4"
        result = supabase_service.upload_file('video', video_path, video_data, 'video/mp4')

        subtitles_url = None
        subtitles_path = None
        if subtitles_bytes:
            subtitles_path = f"{title_sanitized}/{title_sanitized}.srt"
            sub_result = supabase_service.upload_file(
                'video',
                subtitles_path,
                subtitles_bytes,
                'text/plain'
            )
            if sub_result.get('success'):
                subtitles_url = sub_result.get('public_url')
        
        response = {
            'success': True,
            'video': base64.b64encode(video_data).decode('utf-8') if video_data else None,
            'supabase_url': result.get('public_url') if result.get('success') else None,
            'video_path': video_path,
            'subtitles_path': subtitles_path,
            'subtitles_url': subtitles_url,
            'timings': timings
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error in build_from_supabase: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@video_bp.route('/subtitles-url', methods=['POST'])
def get_subtitles_url():
    """
    Get public URL for subtitles SRT stored alongside the video.
    Request JSON:
        {
            "title": str,
            "project_name": str (optional, defaults to title)
        }
    """
    try:
        data = request.get_json()
        if not data or 'title' not in data:
            return jsonify({
                'success': False,
                'error': 'title is required'
            }), 400

        title = data['title']
        title_sanitized = sanitize_filename(data.get('project_name', title))
        subtitles_path = f"{title_sanitized}/{title_sanitized}.srt"
        subtitles_url = supabase_service.get_public_url('video', subtitles_path)

        if not subtitles_url:
            return jsonify({
                'success': False,
                'error': 'Subtitles not found',
                'subtitles_path': subtitles_path
            }), 404

        return jsonify({
            'success': True,
            'subtitles_url': subtitles_url,
            'subtitles_path': subtitles_path
        }), 200
    except Exception as e:
        logger.error(f"Error fetching subtitles URL: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@video_bp.route('/subtitles/download', methods=['POST'])
def download_subtitles():
    """
    Download subtitles SRT file and stream it to the client.
    Request JSON:
        {
            "title": str,
            "project_name": str (optional)
        }
    """
    try:
        data = request.get_json()
        if not data or 'title' not in data:
            return jsonify({
                'success': False,
                'error': 'title is required'
            }), 400

        title = data['title']
        title_sanitized = sanitize_filename(data.get('project_name', title))
        subtitles_path = f"{title_sanitized}/{title_sanitized}.srt"

        result = supabase_service.download_file('video', subtitles_path)
        if not result.get('success') or not result.get('file_data'):
            return jsonify({
                'success': False,
                'error': 'Subtitles not found',
                'subtitles_path': subtitles_path
            }), 404

        return send_file(
            BytesIO(result['file_data']),
            mimetype='text/plain; charset=utf-8',
            as_attachment=True,
            download_name=f"{title_sanitized}.srt"
        )
    except Exception as e:
        logger.error(f"Error downloading subtitles: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

