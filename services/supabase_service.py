"""
Supabase Storage Service
Handles all file operations with Supabase Storage buckets
"""

import os
import logging
from typing import Optional, Dict, Any, List
from io import BytesIO
from supabase import create_client, Client

logger = logging.getLogger("VidyAI_Flask")


class SupabaseService:
    """Service for Supabase Storage operations"""
    
    def __init__(self):
        """Initialize Supabase client"""
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")
        
        self.client: Client = create_client(self.supabase_url, self.supabase_key)
        
        # Bucket names from environment or defaults
        self.buckets = {
            'images': os.getenv('BUCKET_IMAGES', 'images'),
            'audio': os.getenv('BUCKET_AUDIO', 'audio'),
            'video': os.getenv('BUCKET_VIDEO', 'video'),
            'metadata': os.getenv('BUCKET_METADATA', 'metadata'),
            'text': os.getenv('BUCKET_TEXT', 'text')
        }
        
        logger.info("SupabaseService initialized successfully")
    
    def upload_file(self, bucket: str, path: str, file_data: bytes, content_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Upload a file to Supabase Storage
        
        Args:
            bucket: Bucket name (images, audio, video, metadata, text)
            path: File path in bucket (e.g., 'project1/scene_1.jpg')
            file_data: File content as bytes
            content_type: MIME type of file (optional)
            
        Returns:
            Dict with upload result including public URL
        """
        try:
            bucket_name = self.buckets.get(bucket, bucket)
            
            # Upload file
            response = self.client.storage.from_(bucket_name).upload(
                path=path,
                file=file_data,
                file_options={"content-type": content_type} if content_type else {}
            )
            
            # Get public URL
            public_url = self.client.storage.from_(bucket_name).get_public_url(path)
            
            logger.info(f"Successfully uploaded file to {bucket_name}/{path}")
            
            return {
                'success': True,
                'bucket': bucket_name,
                'path': path,
                'public_url': public_url
            }
            
        except Exception as e:
            logger.error(f"Failed to upload file to {bucket}/{path}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'bucket': bucket,
                'path': path
            }
    
    def download_file(self, bucket: str, path: str) -> Dict[str, Any]:
        """
        Download a file from Supabase Storage
        
        Args:
            bucket: Bucket name
            path: File path in bucket
            
        Returns:
            Dict with success status and file_data (bytes) or error
        """
        try:
            bucket_name = self.buckets.get(bucket, bucket)
            
            response = self.client.storage.from_(bucket_name).download(path)
            
            logger.info(f"Successfully downloaded file from {bucket_name}/{path}")
            return {
                'success': True,
                'file_data': response,
                'bucket': bucket_name,
                'path': path
            }
            
        except Exception as e:
            logger.error(f"Failed to download file from {bucket}/{path}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'bucket': bucket,
                'path': path
            }
    
    def delete_file(self, bucket: str, path: str) -> Dict[str, Any]:
        """
        Delete a file from Supabase Storage
        
        Args:
            bucket: Bucket name
            path: File path in bucket
            
        Returns:
            Dict with deletion result
        """
        try:
            bucket_name = self.buckets.get(bucket, bucket)
            
            response = self.client.storage.from_(bucket_name).remove([path])
            
            logger.info(f"Successfully deleted file from {bucket_name}/{path}")
            
            return {
                'success': True,
                'bucket': bucket_name,
                'path': path
            }
            
        except Exception as e:
            logger.error(f"Failed to delete file from {bucket}/{path}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'bucket': bucket,
                'path': path
            }
    
    def list_files(self, bucket: str, path: str = '') -> Dict[str, Any]:
        """
        List files in a Supabase Storage bucket
        
        Args:
            bucket: Bucket name
            path: Directory path in bucket (optional)
            
        Returns:
            Dict with success status and list of file metadata dicts
        """
        try:
            bucket_name = self.buckets.get(bucket, bucket)
            
            response = self.client.storage.from_(bucket_name).list(path)
            
            if response is None:
                logger.warning(f"No response from Supabase for bucket {bucket_name}/{path}")
                return {
                    'success': True,
                    'files': [],
                    'count': 0,
                    'bucket': bucket_name,
                    'path': path
                }
            
            logger.info(f"Successfully listed files from {bucket_name}/{path}")
            
            # Format response - using the same pattern as info.py
            files = []
            if isinstance(response, list):
                for item in response:
                    if item is None:
                        continue
                    
                    # Check if it's a file (has metadata) or folder (no metadata)
                    # This matches the logic from info.py
                    metadata = item.get("metadata")
                    is_folder = metadata is None
                    
                    # Skip folders, only process files
                    if is_folder:
                        continue
                    
                    try:
                        # Extract file information (same pattern as info.py)
                        name = item.get("name")
                        if not name:
                            continue
                        
                        files.append({
                            'name': name,
                            'id': item.get("id"),
                            'created_at': item.get("created_at"),
                            'updated_at': item.get("updated_at"),
                            'last_accessed_at': item.get("last_accessed_at"),
                            'size': metadata.get('size') if metadata else None,
                            'mime_type': metadata.get('mimetype') if metadata else None,
                            'metadata': metadata
                        })
                    except Exception as e:
                        logger.warning(f"Error processing file item: {e}, item: {item}")
                        continue
            else:
                logger.warning(f"Unexpected response type from Supabase: {type(response)}")
            
            return {
                'success': True,
                'files': files,
                'count': len(files),
                'bucket': bucket_name,
                'path': path
            }
            
        except Exception as e:
            logger.error(f"Failed to list files from {bucket}/{path}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'files': [],
                'count': 0,
                'bucket': bucket,
                'path': path
            }
    
    def get_public_url(self, bucket: str, path: str) -> Optional[str]:
        """
        Get public URL for a file
        
        Args:
            bucket: Bucket name
            path: File path in bucket
            
        Returns:
            Public URL string or None
        """
        try:
            bucket_name = self.buckets.get(bucket, bucket)
            public_url = self.client.storage.from_(bucket_name).get_public_url(path)
            return public_url
        except Exception as e:
            logger.error(f"Failed to get public URL for {bucket}/{path}: {str(e)}")
            return None
    
    def upload_from_local_file(self, bucket: str, path: str, local_file_path: str) -> Dict[str, Any]:
        """
        Upload a local file to Supabase Storage
        
        Args:
            bucket: Bucket name
            path: Destination path in bucket
            local_file_path: Path to local file
            
        Returns:
            Dict with upload result
        """
        try:
            with open(local_file_path, 'rb') as f:
                file_data = f.read()
            
            # Detect content type from file extension
            content_type = self._get_content_type(local_file_path)
            
            return self.upload_file(bucket, path, file_data, content_type)
            
        except Exception as e:
            logger.error(f"Failed to upload local file {local_file_path}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'local_file': local_file_path
            }
    
    def _get_content_type(self, file_path: str) -> str:
        """Get MIME type from file extension"""
        ext = os.path.splitext(file_path)[1].lower()
        
        content_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
            '.mp3': 'audio/mpeg',
            '.wav': 'audio/wav',
            '.mp4': 'video/mp4',
            '.avi': 'video/x-msvideo',
            '.mov': 'video/quicktime',
            '.json': 'application/json',
            '.txt': 'text/plain',
            '.md': 'text/markdown'
        }
        
        return content_types.get(ext, 'application/octet-stream')


# Create singleton instance
supabase_service = SupabaseService()

