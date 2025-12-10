"""
Image API Routes
Endpoints for comic image generation using Gemini
"""

import os
import logging
import base64
from flask import Blueprint, request, jsonify
from services.image_service import ImageService
from services.supabase_service import supabase_service

logger = logging.getLogger("VidyAI_Flask")

image_bp = Blueprint('image', __name__)


def get_image_service():
    """Get or create image service instance with API key"""
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        raise ValueError('GEMINI_API_KEY not found in environment variables')
    return ImageService(api_key)


@image_bp.route('/generate-scene', methods=['POST'])
def generate_scene():
    """
    Generate a single comic scene image
    
    Request JSON:
        {
            "scene_prompt": str,
            "scene_num": int,
            "style_sheet": str (optional),
            "character_sheet": str (optional),
            "negative_concepts": list[str] (optional),
            "aspect_ratio": str (optional, default: "16:9")
        }
    
    Response JSON:
        {
            "success": bool,
            "image": str (base64) or null,
            "error": str (if failed)
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'scene_prompt' not in data or 'scene_num' not in data:
            return jsonify({
                'success': False,
                'error': 'scene_prompt and scene_num are required'
            }), 400
        
        scene_prompt = data['scene_prompt']
        scene_num = data['scene_num']
        style_sheet = data.get('style_sheet', '')
        character_sheet = data.get('character_sheet', '')
        negative_concepts = data.get('negative_concepts', ['text', 'letters', 'watermark', 'logo'])
        aspect_ratio = data.get('aspect_ratio', '16:9')
        
        # Get image service
        image_service = get_image_service()
        
        # Generate image
        image_data = image_service.generate_comic_image(
            scene_prompt, scene_num,
            style_sheet=style_sheet,
            character_sheet=character_sheet,
            negative_concepts=negative_concepts,
            aspect_ratio=aspect_ratio
        )
        
        if not image_data:
            return jsonify({
                'success': False,
                'error': 'Failed to generate image'
            }), 500
        
        # Convert to base64
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        return jsonify({
            'success': True,
            'image': image_base64,
            'scene_num': scene_num
        }), 200
        
    except Exception as e:
        logger.error(f"Error in generate_scene: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@image_bp.route('/generate-all', methods=['POST'])
def generate_all():
    """
    Generate all comic scene images
    
    Request JSON:
        {
            "scene_prompts": list[str],
            "title": str,
            "style_sheet": str (optional),
            "character_sheet": str (optional),
            "negative_concepts": list[str] (optional),
            "aspect_ratio": str (optional, default: "16:9", choices: "16:9", "4:3", "1:1", "9:16", "21:9"),
            "image_quality": str (optional, default: "high", choices: "standard", "high", "ultra"),
            "lighting_style": str (optional, default: "natural", choices: "natural", "dramatic", "soft", "cinematic"),
            "color_temperature": str (optional, default: "neutral", choices: "warm", "cool", "neutral", "vibrant"),
            "upload_to_supabase": bool (optional, default: false),
            "project_name": str (optional, for supabase path)
        }
    
    Response JSON:
        {
            "success": bool,
            "images": list[str] (base64) or null,
            "supabase_urls": list[str] (if uploaded),
            "count": int,
            "error": str (if failed)
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'scene_prompts' not in data or 'title' not in data:
            return jsonify({
                'success': False,
                'error': 'scene_prompts and title are required'
            }), 400
        
        scene_prompts = data['scene_prompts']
        title = data['title']
        style_sheet = data.get('style_sheet', '')
        character_sheet = data.get('character_sheet', '')
        negative_concepts = data.get('negative_concepts', ['text', 'letters', 'watermark', 'logo', 'caption', 'speech bubble', 'ui'])
        aspect_ratio = data.get('aspect_ratio', '16:9')
        image_quality = data.get('image_quality', 'high')
        lighting_style = data.get('lighting_style', 'natural')
        color_temperature = data.get('color_temperature', 'neutral')
        upload_to_supabase = data.get('upload_to_supabase', False)
        project_name = data.get('project_name', title.replace(' ', '_'))
        
        # Get image service
        image_service = get_image_service()
        
        # Generate all images with all customization options
        images = image_service.generate_comic_strip(
            scene_prompts, title,
            style_sheet=style_sheet,
            character_sheet=character_sheet,
            negative_concepts=negative_concepts,
            aspect_ratio=aspect_ratio,
            image_quality=image_quality,
            lighting_style=lighting_style,
            color_temperature=color_temperature
        )
        
        # Filter out None images
        valid_images = [img for img in images if img]
        
        if not valid_images:
            return jsonify({
                'success': False,
                'error': 'Failed to generate any images'
            }), 500
        
        # Convert to base64
        images_base64 = []
        for img in valid_images:
            if img:
                images_base64.append(base64.b64encode(img).decode('utf-8'))
            else:
                images_base64.append(None)
        
        response = {
            'success': True,
            'images': images_base64,
            'count': len(valid_images)
        }
        
        # Upload to Supabase if requested
        if upload_to_supabase:
            supabase_urls = []
            for i, img_data in enumerate(valid_images, 1):
                if img_data:
                    path = f"{project_name}/scene_{i}.jpg"
                    result = supabase_service.upload_file('images', path, img_data, 'image/jpeg')
                    if result['success']:
                        supabase_urls.append(result['public_url'])
                    else:
                        supabase_urls.append(None)
                else:
                    supabase_urls.append(None)
            
            response['supabase_urls'] = supabase_urls
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error in generate_all: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

