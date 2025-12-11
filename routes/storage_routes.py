"""
Storage API Routes
Endpoints for Supabase Storage operations
"""

import os
import logging
import base64
from flask import Blueprint, request, jsonify
from services.supabase_service import supabase_service
from services.project_service import project_service

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
        result = supabase_service.list_files('images', '')
        if not result.get('success'):
            return jsonify({
                'success': False,
                'error': result.get('error', 'Failed to list projects'),
                'projects': [],
                'count': 0
            }), 500

        files = result.get('files', [])
        projects = {
            name.split('/')[0]
            for name in [f.get('name', '') for f in files]
            if name and '/' in name
        }

        projects_list = sorted(projects)

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


@storage_bp.route('/get-video-count', methods=['GET'])
def get_video_count():
    """
    Get count of video folders (projects) in the video bucket
    Simple logic: use project service count (each video = one folder/project)
    
    Response JSON:
        {
            "success": bool,
            "count": int,
            "error": str (if failed)
        }
    """
    try:
        # Use project service which already successfully lists videos from video bucket
        # Each video project corresponds to one folder in the video bucket
        result = project_service.list_projects()
        
        if result.get('success'):
            video_count = result.get('count', 0)
            logger.info(f"Video count from project service: {video_count}")
            return jsonify({
                'success': True,
                'count': video_count
            }), 200
        else:
            logger.error(f"Project service returned error: {result.get('error')}")
            return jsonify({
                'success': False,
                'error': result.get('error', 'Failed to get video count'),
                'count': 0
            }), 500
        
    except Exception as e:
        logger.error(f"Error getting video count: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e),
            'count': 0
        }), 500


@storage_bp.route('/get-all-thumbnails', methods=['GET'])
def get_all_thumbnails():
    """
    Get thumbnails for all projects in images bucket in a single optimized call
    
    Response JSON:
        {
            "success": bool,
            "thumbnails": {
                "project_folder_name": "public_url",
                ...
            },
            "count": int,
            "error": str (if failed)
        }
    """
    try:
        bucket_name = supabase_service.buckets.get('images', 'images')
        
        # List all files in images bucket recursively
        def list_all_files_recursive(path=""):
            """Recursively list all files in the bucket"""
            all_files = []
            try:
                items = supabase_service.client.storage.from_(bucket_name).list(path=path)
                
                if items is None:
                    return all_files
                
                for item in items:
                    if item is None:
                        continue
                    
                    name = item.get("name")
                    if not name:
                        continue
                    
                    full_path = f"{path}/{name}" if path else name
                    
                    metadata = item.get("metadata")
                    is_folder = metadata is None
                    
                    if is_folder:
                        # It's a folder - recurse into it
                        all_files.extend(list_all_files_recursive(full_path))
                    else:
                        # It's a file - add it
                        all_files.append({
                            'name': name,
                            'path': full_path,
                            'mime_type': metadata.get('mimetype') if metadata else None
                        })
            except Exception as e:
                logger.warning(f"Error listing files at {path}: {e}")
            
            return all_files
        
        # Get all files
        all_files = list_all_files_recursive()
        logger.info(f"Found {len(all_files)} total files in images bucket")
        
        # Group files by project folder and find first image for each
        thumbnails = {}
        project_files = {}
        
        for file_info in all_files:
            path = file_info['path']
            if '/' in path:
                project_folder = path.split('/')[0]
                file_name = path.split('/', 1)[1]
                
                # Check if it's an image file
                mime_type = file_info.get('mime_type', '').lower()
                name_lower = file_name.lower()
                
                is_image = (
                    mime_type.startswith('image/') or
                    name_lower.endswith(('.jpg', '.jpeg', '.png', '.webp', '.gif'))
                )
                
                if is_image:
                    if project_folder not in project_files:
                        project_files[project_folder] = []
                    project_files[project_folder].append(path)
        
        logger.info(f"Found {len(project_files)} project folders with images: {list(project_files.keys())}")
        
        # Get public URL for first image of each project
        for project_folder, file_paths in project_files.items():
            if file_paths:
                # Sort to get consistent first image (scene_1.jpg typically)
                file_paths.sort()
                first_image_path = file_paths[0]
                
                try:
                    public_url = supabase_service.client.storage.from_(bucket_name).get_public_url(first_image_path)
                    thumbnails[project_folder] = public_url
                    logger.info(f"Added thumbnail for project folder: {project_folder}")
                except Exception as e:
                    logger.warning(f"Failed to get public URL for {first_image_path}: {e}")
        
        logger.info(f"Returning {len(thumbnails)} thumbnails: {list(thumbnails.keys())}")
        
        return jsonify({
            'success': True,
            'thumbnails': thumbnails,
            'count': len(thumbnails),
            'debug': {
                'total_files': len(all_files),
                'project_folders': list(project_files.keys()),
                'thumbnail_keys': list(thumbnails.keys())
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error in get_all_thumbnails: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'thumbnails': {},
            'count': 0
        }), 500