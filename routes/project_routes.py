"""
Project Management Routes
API endpoints for project CRUD operations
"""
from flask import Blueprint, request, jsonify
import logging
from services.project_service import project_service

logger = logging.getLogger("VidyAI_Flask")

# Create blueprint
project_bp = Blueprint('projects', __name__, url_prefix='/api/projects')


@project_bp.route('', methods=['GET'])
def list_projects():
    """
    List all projects (videos from video bucket)
    
    GET /api/projects
    
    Returns all video files from the Supabase video bucket as projects.
    
    Response:
        {
            "success": true,
            "projects": [...],
            "count": 6
        }
    """
    try:
        result = project_service.list_projects()
        return jsonify(result), 200 if result.get('success') else 500
    except Exception as e:
        logger.error(f"Error in list_projects: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@project_bp.route('', methods=['POST'])
def create_project():
    """
    Create a new project
    
    POST /api/projects
    Body:
        {
            "title": "Project Title",
            "wikiUrl": "https://...",
            "wikiTitle": "Wiki Title",
            "wikiSummary": "Summary...",
            "language": "en",
            "status": "draft"
        }
    
    Response:
        {
            "success": true,
            "project": {...},
            "message": "Project created successfully"
        }
    """
    try:
        data = request.get_json()
        
        if not data or not data.get('title'):
            return jsonify({
                'success': False,
                'error': 'Title is required'
            }), 400
        
        result = project_service.create_project(data)
        return jsonify(result), 201 if result.get('success') else 500
        
    except Exception as e:
        logger.error(f"Error in create_project: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@project_bp.route('/<project_id>', methods=['GET'])
def get_project(project_id):
    """
    Get project by ID
    
    GET /api/projects/{project_id}
    
    Response:
        {
            "success": true,
            "project": {...}
        }
    """
    try:
        result = project_service.get_project(project_id)
        return jsonify(result), 200 if result.get('success') else 404
        
    except Exception as e:
        logger.error(f"Error in get_project: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@project_bp.route('/<project_id>', methods=['PUT', 'PATCH'])
def update_project(project_id):
    """
    Update project
    
    PUT/PATCH /api/projects/{project_id}
    Body:
        {
            "status": "completed",
            "storyline": "...",
            "scenePrompts": [...]
        }
    
    Response:
        {
            "success": true,
            "project": {...},
            "message": "Project updated successfully"
        }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Update data is required'
            }), 400
        
        result = project_service.update_project(project_id, data)
        return jsonify(result), 200 if result.get('success') else 500
        
    except Exception as e:
        logger.error(f"Error in update_project: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@project_bp.route('/<project_id>', methods=['DELETE'])
def delete_project(project_id):
    """
    Delete project
    
    DELETE /api/projects/{project_id}
    
    Response:
        {
            "success": true,
            "message": "Project deleted successfully"
        }
    """
    try:
        result = project_service.delete_project(project_id)
        return jsonify(result), 200 if result.get('success') else 500
        
    except Exception as e:
        logger.error(f"Error in delete_project: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

