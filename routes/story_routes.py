"""
Story API Routes
Endpoints for storyline and scene prompt generation
"""

import os
import logging
from flask import Blueprint, request, jsonify
from services.story_service import StoryService

logger = logging.getLogger("VidyAI_Flask")

story_bp = Blueprint('story', __name__)


def get_story_service():
    """Get or create story service instance with API key"""
    api_key = os.getenv('GROQ_API_KEY')
    if not api_key:
        raise ValueError('GROQ_API_KEY not found in environment variables')
    return StoryService(api_key)


@story_bp.route('/generate-storyline', methods=['POST'])
def generate_storyline():
    """
    Generate comic storyline from Wikipedia content
    
    Request JSON:
        {
            "title": str,
            "content": str,
            "target_length": str (optional, default: "medium", choices: "very short", "short", "medium", "long"),
            "max_chars": int (optional, default: 25000),
            "tone": str (optional, default: "casual", choices: "casual", "formal", "enthusiastic", "professional", "conversational"),
            "target_audience": str (optional, default: "general", choices: "kids", "students", "general", "professionals"),
            "complexity": str (optional, default: "moderate", choices: "simple", "moderate", "detailed"),
            "focus_style": str (optional, default: "comprehensive", choices: "key-points", "comprehensive", "highlights"),
            "scene_count": int (optional),
            "educational_level": str (optional, default: "intermediate", choices: "beginner", "intermediate", "advanced"),
            "visual_style": str (optional, default: "educational", choices: "educational", "entertaining", "documentary", "animated")
        }
    
    Response JSON:
        {
            "success": bool,
            "storyline": str or null,
            "error": str (if failed)
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'title' not in data or 'content' not in data:
            return jsonify({
                'success': False,
                'error': 'Title and content are required'
            }), 400
        
        title = data['title']
        content = data['content']
        target_length = data.get('target_length', 'medium')
        max_chars = data.get('max_chars', 25000)
        
        # Extract customization options
        tone = data.get('tone', 'casual')
        target_audience = data.get('target_audience', 'general')
        complexity = data.get('complexity', 'moderate')
        focus_style = data.get('focus_style', 'comprehensive')
        scene_count = data.get('scene_count')
        educational_level = data.get('educational_level', 'intermediate')
        visual_style = data.get('visual_style', 'educational')
        
        # Get story service
        story_service = get_story_service()
        
        # Generate storyline with all customization options
        storyline = story_service.generate_comic_storyline(
            title=title,
            content=content,
            target_length=target_length,
            max_chars=max_chars,
            tone=tone,
            target_audience=target_audience,
            complexity=complexity,
            focus_style=focus_style,
            scene_count=scene_count,
            educational_level=educational_level,
            visual_style=visual_style
        )
        
        return jsonify({
            'success': True,
            'storyline': storyline
        }), 200
        
    except Exception as e:
        logger.error(f"Error in generate_storyline: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@story_bp.route('/generate-scenes', methods=['POST'])
def generate_scenes():
    """
    Generate scene prompts from storyline
    
    Request JSON:
        {
            "title": str,
            "storyline": str,
            "comic_style": str (default: "western comic"),
            "num_scenes": int (optional, default: 10),
            "age_group": str (optional, default: "general"),
            "education_level": str (optional, default: "intermediate"),
            "visual_detail": str (optional, default: "moderate", choices: "minimal", "moderate", "detailed"),
            "camera_style": str (optional, default: "varied", choices: "dynamic", "cinematic", "traditional", "varied"),
            "color_palette": str (optional, default: "natural", choices: "vibrant", "muted", "monochrome", "natural"),
            "scene_pacing": str (optional, default: "moderate", choices: "fast", "moderate", "slow"),
            "negative_concepts": list[str] (optional),
            "character_sheet": str (optional),
            "style_sheet": str (optional)
        }
    
    Response JSON:
        {
            "success": bool,
            "scene_prompts": list[str] or null,
            "count": int,
            "error": str (if failed)
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'title' not in data or 'storyline' not in data:
            return jsonify({
                'success': False,
                'error': 'Title and storyline are required'
            }), 400
        
        title = data['title']
        storyline = data['storyline']
        comic_style = data.get('comic_style', 'western comic')
        num_scenes = data.get('num_scenes', 10)
        age_group = data.get('age_group', 'general')
        education_level = data.get('education_level', 'intermediate')
        visual_detail = data.get('visual_detail', 'moderate')
        camera_style = data.get('camera_style', 'varied')
        color_palette = data.get('color_palette', 'natural')
        scene_pacing = data.get('scene_pacing', 'moderate')
        negative_concepts = data.get('negative_concepts', ['text', 'letters', 'watermark', 'logo', 'caption', 'speech bubble', 'ui'])
        character_sheet = data.get('character_sheet', '')
        style_sheet = data.get('style_sheet', '')
        
        # Get story service
        story_service = get_story_service()
        
        # Generate scene prompts with all customization options
        scene_prompts = story_service.generate_scene_prompts(
            title=title,
            storyline=storyline,
            comic_style=comic_style,
            num_scenes=num_scenes,
            age_group=age_group,
            education_level=education_level,
            negative_concepts=negative_concepts,
            character_sheet=character_sheet,
            style_sheet=style_sheet,
            visual_detail=visual_detail,
            camera_style=camera_style,
            color_palette=color_palette,
            scene_pacing=scene_pacing
        )
        
        return jsonify({
            'success': True,
            'scene_prompts': scene_prompts,
            'count': len(scene_prompts)
        }), 200
        
    except Exception as e:
        logger.error(f"Error in generate_scenes: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@story_bp.route('/generate-complete', methods=['POST'])
def generate_complete():
    """
    Generate complete story (storyline + scene prompts)
    
    Request JSON:
        {
            "title": str,
            "content": str,
            "target_length": str (optional),
            "max_chars": int (optional),
            "comic_style": str (optional),
            "num_scenes": int (optional),
            "age_group": str (optional),
            "education_level": str (optional),
            "negative_concepts": list[str] (optional),
            "character_sheet": str (optional),
            "style_sheet": str (optional)
        }
    
    Response JSON:
        {
            "success": bool,
            "storyline": str or null,
            "scene_prompts": list[str] or null,
            "error": str (if failed)
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'title' not in data or 'content' not in data:
            return jsonify({
                'success': False,
                'error': 'Title and content are required'
            }), 400
        
        title = data['title']
        content = data['content']
        target_length = data.get('target_length', 'medium')
        max_chars = data.get('max_chars', 25000)
        comic_style = data.get('comic_style', 'western comic')
        num_scenes = data.get('num_scenes', 10)
        age_group = data.get('age_group', 'general')
        education_level = data.get('education_level', 'standard')
        negative_concepts = data.get('negative_concepts', ['text', 'letters', 'watermark', 'logo', 'caption', 'speech bubble', 'ui'])
        character_sheet = data.get('character_sheet', '')
        style_sheet = data.get('style_sheet', '')
        
        # Get story service
        story_service = get_story_service()
        
        # Generate storyline
        storyline = story_service.generate_comic_storyline(
            title, content, target_length, max_chars
        )
        
        # Generate scene prompts
        scene_prompts = story_service.generate_scene_prompts(
            title, storyline, comic_style, num_scenes,
            age_group, education_level, negative_concepts,
            character_sheet, style_sheet
        )
        
        return jsonify({
            'success': True,
            'storyline': storyline,
            'scene_prompts': scene_prompts,
            'num_scenes': len(scene_prompts)
        }), 200
        
    except Exception as e:
        logger.error(f"Error in generate_complete: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

