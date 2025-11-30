"""
Storage API Routes
Endpoints for Supabase Storage operations
"""

import os
import logging
import base64
from flask import Blueprint, request, jsonify
from services.supabase_service import supabase_service

logger = logging.getLogger("VidyAI_Flask")

storage_bp = Blueprint('storage', __name__)


@storage_bp.route('/upload', methods=['POST'])
def upload_file():
    """
    Upload a file to Supabase Storage
    
    Request JSON:
        {
            "bucket": str (images, audio, video, metadata, text),
            "path": str (file path in bucket),
            "file_data": str (base64 encoded file),
            "content_type": str (optional)
        }
    
    Response JSON:
        {
            "success": bool,
            "bucket": str,
            "path": str,
            "public_url": str or null,
            "error": str (if failed)
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'bucket' not in data or 'path' not in data or 'file_data' not in data:
            return jsonify({
                'success': False,
                'error': 'bucket, path, and file_data are required'
            }), 400
        
        bucket = data['bucket']
        path = data['path']
        file_data_base64 = data['file_data']
        content_type = data.get('content_type')
        
        # Decode file data
        file_data = base64.b64decode(file_data_base64)
        
        # Upload to Supabase
        result = supabase_service.upload_file(bucket, path, file_data, content_type)
        
        return jsonify(result), 200 if result['success'] else 500
        
    except Exception as e:
        logger.error(f"Error in upload_file: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@storage_bp.route('/download', methods=['POST'])
def download_file():
    """
    Download a file from Supabase Storage
    
    Request JSON:
        {
            "bucket": str,
            "path": str
        }
    
    Response JSON:
        {
            "success": bool,
            "file_data": str (base64) or null,
            "error": str (if failed)
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'bucket' not in data or 'path' not in data:
            return jsonify({
                'success': False,
                'error': 'bucket and path are required'
            }), 400
        
        bucket = data['bucket']
        path = data['path']
        
        # Download from Supabase
        result = supabase_service.download_file(bucket, path)
        
        if not result.get('success'):
            return jsonify(result), 404
        
        # Encode to base64
        file_data_base64 = base64.b64encode(result['file_data']).decode('utf-8')
        
        return jsonify({
            'success': True,
            'file_data': file_data_base64
        }), 200
        
    except Exception as e:
        logger.error(f"Error in download_file: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@storage_bp.route('/delete', methods=['POST'])
def delete_file():
    """
    Delete a file from Supabase Storage
    
    Request JSON:
        {
            "bucket": str,
            "path": str
        }
    
    Response JSON:
        {
            "success": bool,
            "bucket": str,
            "path": str,
            "error": str (if failed)
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'bucket' not in data or 'path' not in data:
            return jsonify({
                'success': False,
                'error': 'bucket and path are required'
            }), 400
        
        bucket = data['bucket']
        path = data['path']
        
        # Delete from Supabase
        result = supabase_service.delete_file(bucket, path)
        
        return jsonify(result), 200 if result['success'] else 500
        
    except Exception as e:
        logger.error(f"Error in delete_file: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@storage_bp.route('/list', methods=['POST'])
def list_files():
    """
    List files in a Supabase Storage bucket
    
    Request JSON:
        {
            "bucket": str,
            "path": str (optional, directory path)
        }
    
    Response JSON:
        {
            "success": bool,
            "files": list[dict] or null,
            "count": int,
            "error": str (if failed)
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'bucket' not in data:
            return jsonify({
                'success': False,
                'error': 'bucket is required'
            }), 400
        
        bucket = data['bucket']
        path = data.get('path', '')
        
        # List files from Supabase
        result = supabase_service.list_files(bucket, path)
        
        return jsonify(result), 200 if result.get('success') else 500
        
    except Exception as e:
        logger.error(f"Error in list_files: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@storage_bp.route('/get-url', methods=['POST'])
def get_public_url():
    """
    Get public URL for a file
    
    Request JSON:
        {
            "bucket": str,
            "path": str
        }
    
    Response JSON:
        {
            "success": bool,
            "public_url": str or null,
            "error": str (if failed)
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'bucket' not in data or 'path' not in data:
            return jsonify({
                'success': False,
                'error': 'bucket and path are required'
            }), 400
        
        bucket = data['bucket']
        path = data['path']
        
        # Get public URL
        public_url = supabase_service.get_public_url(bucket, path)
        
        if not public_url:
            return jsonify({
                'success': False,
                'error': 'Failed to get public URL'
            }), 500
        
        return jsonify({
            'success': True,
            'public_url': public_url
        }), 200
        
    except Exception as e:
        logger.error(f"Error in get_public_url: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@storage_bp.route('/list-projects', methods=['GET'])
def list_projects():
    """
    List all projects (folders) in images bucket
    
    Response JSON:
        {
            "success": bool,
            "projects": list[str] or null,
            "count": int,
            "error": str (if failed)
        }
    """
    try:
        # List files in images bucket root
        files = supabase_service.list_files('images', '')
        
        # Extract unique folder names (projects)
        projects = set()
        for file in files:
            name = file.get('name', '')
            if '/' in name:
                project = name.split('/')[0]
                projects.add(project)
        
        projects_list = sorted(list(projects))
        
        return jsonify({
            'success': True,
            'projects': projects_list,
            'count': len(projects_list)
        }), 200
        
    except Exception as e:
        logger.error(f"Error in list_projects: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

