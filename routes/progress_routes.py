"""
Progress API Routes
Endpoints for tracking progress of long-running operations
"""

import logging
from flask import Blueprint, request, jsonify
from services.progress_service import progress_tracker

logger = logging.getLogger("VidyAI_Flask")

progress_bp = Blueprint('progress', __name__)


@progress_bp.route('/get', methods=['GET'])
def get_progress():
    """
    Get progress for a task
    
    Query Parameters:
        task_id: Task identifier (e.g., "images_Title" or "video_Title")
    
    Response JSON:
        {
            "success": bool,
            "progress": int (0-100),
            "message": str,
            "current": int,
            "total": int,
            "error": str (if failed)
        }
    """
    try:
        task_id = request.args.get('task_id')
        
        if not task_id:
            return jsonify({
                'success': False,
                'error': 'task_id is required'
            }), 400
        
        progress_data = progress_tracker.get_progress(task_id)
        
        if not progress_data:
            return jsonify({
                'success': True,
                'progress': 0,
                'message': 'Task not found',
                'current': 0,
                'total': 0
            }), 200
        
        return jsonify({
            'success': True,
            'progress': progress_data['progress'],
            'message': progress_data['message'],
            'current': progress_data['current'],
            'total': progress_data['total']
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting progress: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@progress_bp.route('/clear', methods=['POST'])
def clear_progress():
    """
    Clear progress for a task
    
    Request JSON:
        {
            "task_id": str
        }
    
    Response JSON:
        {
            "success": bool,
            "error": str (if failed)
        }
    """
    try:
        data = request.get_json()
        task_id = data.get('task_id') if data else None
        
        if not task_id:
            return jsonify({
                'success': False,
                'error': 'task_id is required'
            }), 400
        
        progress_tracker.clear_progress(task_id)
        
        return jsonify({
            'success': True
        }), 200
        
    except Exception as e:
        logger.error(f"Error clearing progress: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

