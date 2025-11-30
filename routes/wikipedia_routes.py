"""
Wikipedia API Routes
Endpoints for Wikipedia search and content extraction
"""

import os
import logging
from flask import Blueprint, request, jsonify
from services.wikipedia_service import wikipedia_service

logger = logging.getLogger("VidyAI_Flask")

wikipedia_bp = Blueprint('wikipedia', __name__)


@wikipedia_bp.route('/search', methods=['POST'])
def search_wikipedia():
    """
    Search Wikipedia
    
    Request JSON:
        {
            "query": str,
            "language": str (optional, default: "en"),
            "results_limit": int (optional, default: 15)
        }
    
    Response JSON:
        {
            "success": bool,
            "results": list[str] or null,
            "error": str (if failed)
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'query' not in data:
            return jsonify({
                'success': False,
                'error': 'Query is required'
            }), 400
        
        query = data['query']
        language = data.get('language', 'en')
        results_limit = data.get('results_limit', 15)
        
        # Set language if different
        if language != wikipedia_service.language:
            wikipedia_service.set_language(language)
        
        # Search Wikipedia
        results = wikipedia_service.search_wikipedia(query, results_limit)
        
        # Check if results is an error dict
        if isinstance(results, dict) and 'error' in results:
            return jsonify({
                'success': False,
                'error': results['error']
            }), 200
        
        return jsonify({
            'success': True,
            'results': results,
            'count': len(results)
        }), 200
        
    except Exception as e:
        logger.error(f"Error in search_wikipedia: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@wikipedia_bp.route('/page', methods=['POST'])
def get_page():
    """
    Get Wikipedia page information
    
    Request JSON:
        {
            "title": str,
            "language": str (optional, default: "en")
        }
    
    Response JSON:
        {
            "success": bool,
            "page_info": dict or null,
            "error": str (if failed),
            "options": list[str] (if disambiguation)
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'title' not in data:
            return jsonify({
                'success': False,
                'error': 'Title is required'
            }), 400
        
        title = data['title']
        language = data.get('language', 'en')
        
        # Set language if different
        if language != wikipedia_service.language:
            wikipedia_service.set_language(language)
        
        # Get page info
        page_info = wikipedia_service.get_page_info(title)
        
        # Check for errors
        if 'error' in page_info:
            response = {
                'success': False,
                'error': page_info.get('message', page_info['error'])
            }
            
            # Include options if disambiguation error
            if 'options' in page_info:
                response['options'] = page_info['options']
            
            return jsonify(response), 200
        
        return jsonify({
            'success': True,
            'page_info': page_info
        }), 200
        
    except Exception as e:
        logger.error(f"Error in get_page: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@wikipedia_bp.route('/set-language', methods=['POST'])
def set_language():
    """
    Set Wikipedia language
    
    Request JSON:
        {
            "language": str
        }
    
    Response JSON:
        {
            "success": bool,
            "language": str,
            "error": str (if failed)
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'language' not in data:
            return jsonify({
                'success': False,
                'error': 'Language is required'
            }), 400
        
        language = data['language']
        wikipedia_service.set_language(language)
        
        return jsonify({
            'success': True,
            'language': language
        }), 200
        
    except Exception as e:
        logger.error(f"Error in set_language: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

