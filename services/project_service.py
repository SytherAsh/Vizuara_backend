"""
Project Service - Handle project CRUD operations with Supabase
"""
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from services.supabase_service import supabase_service

logger = logging.getLogger("VidyAI_Flask")


class ProjectService:
    """Service for managing projects in Supabase"""
    
    def __init__(self):
        """Initialize ProjectService"""
        self.supabase = supabase_service
        logger.info("ProjectService initialized")
    
    def create_project(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new project and save metadata to Supabase
        
        Args:
            project_data: Project information including title, wiki_url, language, etc.
            
        Returns:
            Dict with success status and project info
        """
        try:
            # Generate project ID (timestamp-based)
            project_id = project_data.get('id') or str(int(datetime.now().timestamp() * 1000))
            
            # Prepare project metadata
            metadata = {
                'id': project_id,
                'title': project_data.get('title', ''),
                'wikiUrl': project_data.get('wikiUrl', ''),
                'wikiTitle': project_data.get('wikiTitle', ''),
                'wikiSummary': project_data.get('wikiSummary', ''),
                'language': project_data.get('language', 'en'),
                'status': project_data.get('status', 'draft'),
                'storyline': project_data.get('storyline', ''),
                'scenePrompts': project_data.get('scenePrompts', []),
                'comicStyle': project_data.get('comicStyle', 'western comic'),
                'narrationStyle': project_data.get('narrationStyle', 'educational'),
                'createdAt': project_data.get('createdAt', datetime.now().isoformat()),
                'updatedAt': datetime.now().isoformat(),
            }
            
            # Save metadata to Supabase
            metadata_json = json.dumps(metadata, indent=2)
            metadata_filename = f"project_{project_id}.json"
            
            result = self.supabase.upload_file(
                bucket='metadata',
                path=metadata_filename,
                file_data=metadata_json.encode('utf-8')
            )
            
            if result.get('success'):
                logger.info(f"Project {project_id} created successfully")
                return {
                    'success': True,
                    'project': metadata,
                    'message': 'Project created successfully'
                }
            else:
                raise Exception(result.get('error', 'Failed to save project metadata'))
                
        except Exception as e:
            logger.error(f"Error creating project: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_project(self, project_id: str) -> Dict[str, Any]:
        """
        Get project metadata from Supabase
        
        Args:
            project_id: Project ID
            
        Returns:
            Dict with success status and project data
        """
        try:
            metadata_filename = f"project_{project_id}.json"
            
            result = self.supabase.download_file(
                bucket='metadata',
                path=metadata_filename
            )
            
            if result.get('success') and result.get('file_data'):
                metadata = json.loads(result['file_data'].decode('utf-8'))
                return {
                    'success': True,
                    'project': metadata
                }
            else:
                return {
                    'success': False,
                    'error': 'Project not found'
                }
                
        except Exception as e:
            logger.error(f"Error getting project {project_id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def list_projects(self) -> Dict[str, Any]:
        """
        List all projects from Supabase video bucket
        Returns all video files from the video bucket as projects
        """
        return self._list_projects_from_videos()
    
    def _list_projects_from_videos(self) -> Dict[str, Any]:
        """
        List projects from video bucket
        Recursively searches for all video files in the video bucket
        """
        try:
            projects = []
            bucket_name = self.supabase.buckets.get('video', 'video')
            
            def find_videos_recursive(path=""):
                """Recursively search for videos"""
                try:
                    items = self.supabase.client.storage.from_(bucket_name).list(path=path)
                    
                    if items is None:
                        logger.warning(f"No items found at path: {path}")
                        return
                    
                    for item in items:
                        if item is None:
                            continue
                            
                        name = item.get("name")
                        if not name:
                            continue
                            
                        full_path = f"{path}/{name}" if path else name
                        
                        metadata = item.get("metadata")
                        is_folder = metadata is None  # Supabase folder rule
                        
                        if is_folder:
                            # It's a folder - recurse into it
                            logger.debug(f"Found folder: {full_path}, recursing...")
                            find_videos_recursive(full_path)
                        else:
                            # It's a file - check if it's a video
                            if name and name.lower().endswith(('.mp4', '.avi', '.mov', '.webm', '.mkv')):
                                try:
                                    # Get public URL
                                    public_url = self.supabase.client.storage.from_(bucket_name).get_public_url(full_path)
                                    
                                    # Extract title from folder name or filename
                                    if '/' in full_path:
                                        folder_name = full_path.rsplit('/', 1)[0]
                                        title = folder_name.replace('_', ' ').replace('-', ' ').title()
                                    else:
                                        title = name.rsplit('.', 1)[0].replace('_', ' ').replace('-', ' ').title()
                                    
                                    # Create project object
                                    project = {
                                        'id': item.get("id") or name,
                                        'title': title,
                                        'videoUrl': public_url,
                                        'videoName': name,
                                        'videoPath': full_path,
                                        'hasVideo': True,
                                        'status': 'completed',
                                        'createdAt': item.get("created_at", ''),
                                        'updatedAt': item.get("updated_at", ''),
                                        'size': metadata.get('size', 0) if metadata else 0,
                                        'mime_type': metadata.get('mimetype', 'video/mp4') if metadata else 'video/mp4'
                                    }
                                    projects.append(project)
                                    logger.debug(f"Added video project: {title} ({full_path})")
                                except Exception as e:
                                    logger.warning(f"Failed to process video {full_path}: {e}")
                                    continue
                except Exception as e:
                    logger.error(f"Error listing path {path}: {e}")
                    return
            
            # Start recursive search from root
            logger.info(f"Starting to list videos from bucket: {bucket_name}")
            find_videos_recursive()
            
            # Sort by updated_at (most recent first)
            projects.sort(key=lambda x: x.get('updatedAt', ''), reverse=True)
            
            logger.info(f"Found {len(projects)} video projects from video bucket")
            return {
                'success': True,
                'projects': projects,
                'count': len(projects)
            }
        except Exception as e:
            logger.error(f"Error listing projects from video bucket: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'projects': [],
                'count': 0
            }
    
    def update_project(self, project_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update project metadata in Supabase
        
        Args:
            project_id: Project ID
            updates: Dictionary of fields to update
            
        Returns:
            Dict with success status and updated project
        """
        try:
            # Get existing project
            get_result = self.get_project(project_id)
            
            if not get_result.get('success'):
                return get_result
            
            # Merge updates
            metadata = get_result['project']
            metadata.update(updates)
            metadata['updatedAt'] = datetime.now().isoformat()
            
            # Save updated metadata
            metadata_json = json.dumps(metadata, indent=2)
            metadata_filename = f"project_{project_id}.json"
            
            result = self.supabase.upload_file(
                bucket='metadata',
                path=metadata_filename,
                file_data=metadata_json.encode('utf-8')
            )
            
            if result.get('success'):
                logger.info(f"Project {project_id} updated successfully")
                return {
                    'success': True,
                    'project': metadata,
                    'message': 'Project updated successfully'
                }
            else:
                raise Exception(result.get('error', 'Failed to update project'))
                
        except Exception as e:
            logger.error(f"Error updating project {project_id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def delete_project(self, project_id: str) -> Dict[str, Any]:
        """
        Delete project and all associated assets from Supabase
        
        Args:
            project_id: Project ID
            
        Returns:
            Dict with success status
        """
        try:
            # Delete metadata file
            metadata_filename = f"project_{project_id}.json"
            result = self.supabase.delete_file(
                bucket='metadata',
                path=metadata_filename
            )
            
            if not result.get('success'):
                logger.warning(f"Failed to delete metadata for project {project_id}")
            
            # Delete associated assets (images, audio, video)
            # This is optional - you may want to keep assets
            # For now, we'll just delete the metadata
            
            logger.info(f"Project {project_id} deleted successfully")
            return {
                'success': True,
                'message': 'Project deleted successfully'
            }
            
        except Exception as e:
            logger.error(f"Error deleting project {project_id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }


# Global instance
project_service = ProjectService()

