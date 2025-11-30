# Video Bucket Project Listing

## Overview

The `GET /api/projects` endpoint now lists all projects directly from the **video bucket** in Supabase Storage.

## How It Works

1. **Recursively searches** the video bucket for all video files
2. **Finds all video files** with extensions: `.mp4`, `.avi`, `.mov`, `.webm`, `.mkv`
3. **Extracts project information** from folder structure and file metadata
4. **Returns formatted project list** with video URLs

## Route

**Endpoint:** `GET /api/projects`

**Response:**
```json
{
  "success": true,
  "projects": [
    {
      "id": "file-id-or-name",
      "title": "Project Title",
      "videoUrl": "https://...",
      "videoName": "video.mp4",
      "videoPath": "project_name/video.mp4",
      "hasVideo": true,
      "status": "completed",
      "createdAt": "2024-01-01T00:00:00",
      "updatedAt": "2024-01-01T00:00:00",
      "size": 12345678,
      "mime_type": "video/mp4"
    }
  ],
  "count": 1
}
```

## Implementation

### Backend (`project_service.py`)

```python
def list_projects(self) -> Dict[str, Any]:
    """
    List all projects from Supabase video bucket
    Returns all video files from the video bucket as projects
    """
    return self._list_projects_from_videos()
```

The method:
- Recursively searches the video bucket
- Handles nested folder structures
- Extracts titles from folder names or filenames
- Gets public URLs for all videos
- Sorts by `updatedAt` (most recent first)

## Folder Structure

The video bucket can have videos in different structures:

```
video/
├── project_name/
│   └── video.mp4          → Title: "Project Name"
├── another_project.mp4     → Title: "Another Project"
└── nested/
    └── deep/
        └── video.mp4      → Title: "Deep"
```

## Frontend Usage

```typescript
const response = await apiClient.getAllProjects();
// response.projects contains all videos from video bucket
```

## Error Handling

- Returns empty list if bucket is empty
- Logs errors but doesn't crash
- Returns error message in response if something fails

## Notes

- Only completed videos (in video bucket) are listed
- Projects in draft/in-progress state won't appear (they're in metadata bucket)
- Video URLs are public URLs from Supabase Storage
- Projects are sorted by most recently updated first

