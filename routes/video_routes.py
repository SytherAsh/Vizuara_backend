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
            "project_name": str (optional, for supabase path)
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
        project_name = data.get('project_name', title.replace(' ', '_'))
        
        # Decode background music if provided
        bg_music_data = None
        if 'bg_music' in data and data['bg_music']:
            bg_music_data = base64.b64decode(data['bg_music'])
        
        # Build video with all customization options
        video_data = video_service.build_video(
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
            kb_pan=kb_pan
        )
        
        # Convert to base64
        video_base64 = base64.b64encode(video_data).decode('utf-8')
        
        response = {
            'success': True,
            'video': video_base64
        }
        
        # Upload to Supabase if requested
        if upload_to_supabase:
            path = f"{project_name}/{title.replace(' ', '_')}.mp4"
            result = supabase_service.upload_file('video', path, video_data, 'video/mp4')
            if result['success']:
                response['supabase_url'] = result['public_url']
            
            # Store metadata if provided
            if 'storyline' in data or 'scene_prompts' in data:
                try:
                    metadata = {
                        'title': title,
                        'project_name': project_name,
                        'created_at': datetime.now().isoformat(),
                        'video_path': path,
                        'video_url': result.get('public_url', '') if result.get('success') else '',
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
                    metadata_path = f"{project_name}/metadata.json"
                    metadata_result = supabase_service.upload_file(
                        'metadata', 
                        metadata_path, 
                        metadata_json.encode('utf-8'), 
                        'application/json'
                    )
                    if metadata_result['success']:
                        logger.info(f"Metadata stored for project: {project_name}")
                except Exception as e:
                    logger.warning(f"Failed to store metadata: {e}")
            
            # Store text files (storyline and scene prompts) if provided
            try:
                if 'storyline' in data and data['storyline']:
                    storyline_text = f"# {title} - Comic Storyline\n\n{data['storyline']}"
                    storyline_path = f"{project_name}/storyline.txt"
                    storyline_result = supabase_service.upload_file(
                        'text',
                        storyline_path,
                        storyline_text.encode('utf-8'),
                        'text/plain'
                    )
                    if storyline_result['success']:
                        logger.info(f"Storyline text stored for project: {project_name}")
                
                if 'scene_prompts' in data and data['scene_prompts']:
                    scene_prompts_text = f"# {title} - Scene Prompts\n\n"
                    for i, prompt in enumerate(data['scene_prompts'], 1):
                        scene_prompts_text += f"## Scene {i}\n{prompt}\n\n{'='*50}\n\n"
                    scene_prompts_path = f"{project_name}/scene_prompts.txt"
                    scene_prompts_result = supabase_service.upload_file(
                        'text',
                        scene_prompts_path,
                        scene_prompts_text.encode('utf-8'),
                        'text/plain'
                    )
                    if scene_prompts_result['success']:
                        logger.info(f"Scene prompts text stored for project: {project_name}")
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
        
        # Download images from Supabase
        images = []
        for i in range(1, num_scenes + 1):
            path = f"{project_name}/scene_{i}.jpg"
            img_data = supabase_service.download_file('images', path)
            images.append(img_data)
        
        # Download audio from Supabase
        scene_audio = {}
        for i in range(1, num_scenes + 1):
            scene_key = f"scene_{i}"
            path = f"{project_name}/scene_{i}.mp3"
            audio_data = supabase_service.download_file('audio', path)
            if audio_data:
                scene_audio[scene_key] = audio_data
        
        # Build video with downloaded assets
        fps = data.get('fps', 30)
        resolution = tuple(data.get('resolution', [1920, 1080]))
        
        video_data = video_service.build_video(
            images=images,
            scene_audio=scene_audio,
            title=title,
            fps=fps,
            resolution=resolution
        )
        
        # Upload to Supabase
        path = f"{project_name}/{title.replace(' ', '_')}.mp4"
        result = supabase_service.upload_file('video', path, video_data, 'video/mp4')
        
        response = {
            'success': True,
            'video': base64.b64encode(video_data).decode('utf-8')
        }
        
        if result['success']:
            response['supabase_url'] = result['public_url']
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error in build_from_supabase: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

