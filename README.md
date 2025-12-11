# VidyAI Flask Backend

A fully working Flask REST API backend for converting Wikipedia articles into engaging educational videos.

## 🎯 Overview

This Flask backend replaces the Streamlit application and provides RESTful API endpoints for a React frontend. It handles:

- Wikipedia search and content extraction
- AI-powered storyline generation
- Comic scene prompt generation
- Image generation using Gemini AI
- Narration generation
- Text-to-speech audio synthesis
- Video compilation with effects
- Supabase Storage integration

## 📁 Project Structure

```
VidyAi_Flask/
├── app.py                          # Main Flask application
├── requirements.txt                # Python dependencies
├── .env_example                    # Environment variables template
│
├── routes/                         # API route blueprints
│   ├── __init__.py
│   ├── wikipedia_routes.py         # Wikipedia endpoints
│   ├── story_routes.py             # Story generation endpoints
│   ├── image_routes.py             # Image generation endpoints
│   ├── narration_routes.py         # Narration endpoints
│   ├── audio_routes.py             # Audio/TTS endpoints
│   ├── video_routes.py             # Video compilation endpoints
│   └── storage_routes.py           # Supabase Storage endpoints
│
├── services/                       # Business logic services
│   ├── __init__.py
│   ├── supabase_service.py         # Supabase operations
│   ├── wikipedia_service.py        # Wikipedia operations
│   ├── story_service.py            # Story generation (Groq)
│   ├── image_service.py            # Image generation (Gemini)
│   ├── narration_service.py        # Narration generation (Groq)
│   ├── tts_service.py              # Text-to-speech (gTTS)
│   └── video_service.py            # Video compilation (MoviePy)
│
└── utils/                          # Helper utilities
    ├── __init__.py
    ├── helpers.py                  # Common helper functions
    └── validation.py               # Request validation
```

## 🚀 Quick Start

### 1. Installation

```bash
cd VidyAi_Flask

# Create virtual environment
python -m venv fenv

# Activate virtual environment
# Windows:
fenv\Scripts\activate
# Linux/Mac:
source fenv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Setup

Copy `.env_example` to `.env` and fill in your API keys:

```bash
cp .env_example .env
```

Edit `.env` with your credentials:

```env
# API Keys (Required)
GROQ_API_KEY=your_groq_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here

# Supabase (Required)
SUPABASE_URL=your_supabase_url_here
SUPABASE_KEY=your_supabase_anon_key

# Flask Server
FLASK_ENV=development
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
SECRET_KEY=your_secret_key_here

# CORS (Your React frontend URL)
CORS_ORIGINS=http://localhost:8080

# Supabase Buckets
BUCKET_IMAGES=images
BUCKET_AUDIO=audio
BUCKET_VIDEO=video
BUCKET_METADATA=metadata
BUCKET_TEXT=text
```

### 3. Run the Server

```bash
python app.py
```

The server will start at `http://localhost:5000`

## 📚 API Documentation

See [API_DOCUMENTATION.md](./API_DOCUMENTATION.md) for complete API reference.

### Quick Examples

#### Search Wikipedia:
```bash
curl -X POST http://localhost:5000/api/wikipedia/search \
  -H "Content-Type: application/json" \
  -d '{"query": "Albert Einstein"}'
```

#### Generate Storyline:
```bash
curl -X POST http://localhost:5000/api/story/generate-complete \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Albert Einstein",
    "content": "Wikipedia content...",
    "num_scenes": 10
  }'
```

#### Build Video with Subtitles:
```bash
curl -X POST http://localhost:5000/api/video/build \
  -H "Content-Type: application/json" \
  -d '{
    "images": ["base64_image1", "base64_image2"],
    "scene_audio": {
      "scene_1": "base64_audio1",
      "scene_2": "base64_audio2"
    },
    "title": "Albert Einstein",
    "narrations": {
      "scene_1": {"narration": "Text for scene 1"},
      "scene_2": {"narration": "Text for scene 2"}
    },
    "generate_subtitles": true,
    "upload_to_supabase": true
  }'
```

**Response includes:**
- `video`: Base64 encoded video file
- `subtitles`: Base64 encoded SRT subtitle file (if generated)
- `subtitles_url`: Public URL to subtitle file (if uploaded to Supabase)
- `timings`: Scene timing information

## 🔧 Technologies Used

- **Flask** - Web framework
- **Flask-CORS** - CORS support
- **Supabase** - Storage backend
- **Groq** - AI story/narration generation (Llama 3.3 70B)
- **Google Gemini** - Image generation (Gemini 2.5 Flash Image)
- **gTTS** - Text-to-speech
- **MoviePy** - Video compilation
- **Wikipedia-API** - Wikipedia content extraction

## 🎨 Key Features

### ✅ Complete RESTful API
- All Streamlit functionality converted to REST endpoints
- JSON request/response format
- Proper error handling and validation

### ✅ Supabase Storage Integration
- File upload/download/delete operations
- Public buckets for images, audio, video, metadata, text
- Direct URL access to files

#### Bucket Map (per project/title_sanitized)
- `images/{title_sanitized}/scene_{i}.jpg` - Generated comic panel images
- `audio/{title_sanitized}/scene_{i}.mp3` - Text-to-speech audio for each scene
- `text/{title_sanitized}/scene_{i}_narration.txt` - Narration text for each scene
- `text/{title_sanitized}/storyline.txt` - Complete storyline text
- `text/{title_sanitized}/scene_prompts.txt` - Scene generation prompts
- `video/{title_sanitized}/{title_sanitized}.mp4` - Final compiled video
- `video/{title_sanitized}/{title_sanitized}.srt` - Subtitle file (SRT format)
- `metadata/{title_sanitized}/metadata.json` - Project metadata

### ✅ AI-Powered Generation
- Groq API for storyline and narration (Llama 3.3 70B)
- Gemini 2.5 Flash Image for comic panel generation
- Student-friendly, simple language output

### ✅ Professional Architecture
- Clean separation: routes/services/utils
- No database required (Supabase Storage only)
- Comprehensive logging
- Request validation

### ✅ Video Processing
- MoviePy integration for video compilation
- Ken Burns effect support
- Audio synchronization
- Crossfade transitions
- Subtitle generation (SRT format)

### ✅ Subtitle Support
- Automatic SRT subtitle generation from narrations
- Accurate timing synchronization with audio
- Text cleaning and formatting (removes markdown)
- Smart text wrapping (max 3 lines per subtitle)
- Styled subtitles (white text, black outline, Arial font)
- External SRT file generation (compatible with VLC, web players)
- Upload to Supabase alongside video files

**Note**: Subtitles are currently generated as external `.srt` files. They are NOT burned into the video file itself. This means:
- ✅ Works with players that support external SRT files (VLC, some web players)
- ⚠️ May not work with basic players or social media platforms
- ✅ Subtitles can be toggled on/off in supporting players

## 🔐 Security Notes

1. **Never commit .env file** - It contains sensitive API keys
2. **Use environment variables** - All secrets in `.env`
3. **CORS configured** - Only allows requests from specified origins
4. **File size limits** - Configurable max upload size (default 100MB)

## 🐛 Debugging

### Check Logs
All logs are written to `vidyai_flask.log`:

```bash
tail -f vidyai_flask.log
```

### Common Issues

**Issue:** `GROQ_API_KEY not found`
- **Solution:** Make sure `.env` file exists and contains the API key

**Issue:** `MoviePy not working`
- **Solution:** Install ffmpeg: `pip install imageio-ffmpeg`

**Issue:** `Supabase connection failed`
- **Solution:** Verify SUPABASE_URL and SUPABASE_KEY in `.env`

**Issue:** `CORS errors from React`
- **Solution:** Add your React URL to CORS_ORIGINS in `.env`

**Issue:** `Subtitles not showing in video player`
- **Solution:** Subtitles are external SRT files. Ensure your player supports external subtitle files. Use VLC or a web player with subtitle support. The SRT file must be in the same directory as the video or loaded separately.

**Issue:** `Subtitles timing is off`
- **Solution:** Check that narrations match the audio content. Subtitle timing is calculated from scene durations which are based on audio length.

## 📊 API Endpoints Summary

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/wikipedia/search` | POST | Search Wikipedia |
| `/api/wikipedia/page` | POST | Get page content |
| `/api/story/generate-storyline` | POST | Generate storyline |
| `/api/story/generate-scenes` | POST | Generate scene prompts |
| `/api/story/generate-complete` | POST | Generate storyline + scenes |
| `/api/images/generate-scene` | POST | Generate single image |
| `/api/images/generate-all` | POST | Generate all images |
| `/api/narration/generate-scene` | POST | Generate scene narration |
| `/api/narration/generate-all` | POST | Generate all narrations |
| `/api/audio/generate-scene` | POST | Generate scene audio |
| `/api/audio/generate-all` | POST | Generate all audio |
| `/api/video/build` | POST | Build final video (with optional subtitles) |
| `/api/video/build-from-supabase` | POST | Build video from Supabase assets |
| `/api/video/subtitles-url` | POST | Get public URL for subtitles SRT file |
| `/api/video/subtitles/download` | POST | Download subtitles SRT file |
| `/api/storage/upload` | POST | Upload file to Supabase |
| `/api/storage/download` | POST | Download file from Supabase |
| `/api/storage/delete` | POST | Delete file from Supabase |
| `/api/storage/list` | POST | List files in bucket |
| `/api/storage/get-url` | POST | Get public URL for file |
| `/api/storage/list-projects` | GET | List all projects |

## 🎯 Complete Workflow

1. **Search Wikipedia** → Get topic ideas
2. **Get Page** → Fetch article content
3. **Generate Story** → Create storyline and scene prompts
4. **Generate Images** → Create comic panels with Gemini
5. **Generate Narrations** → Create narration text for each scene
6. **Generate Audio** → Convert narrations to speech (MP3)
7. **Build Video** → Compile images + audio into final video
   - Optionally generate subtitles (SRT format)
   - Subtitles are created from narration texts with accurate timing
8. **Upload to Supabase** → Store assets in cloud storage
   - Video MP4 file
   - Subtitle SRT file (if generated)
   - All scene images and audio files

## 🔄 Integration with React Frontend

The Flask backend is designed to work seamlessly with the React frontend at `vizuara-flow-studio`.

### Example React Integration:

```javascript
// Search Wikipedia
const searchWikipedia = async (query) => {
  const response = await fetch('http://localhost:5000/api/wikipedia/search', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query })
  });
  return await response.json();
};

// Generate complete story
const generateStory = async (title, content) => {
  const response = await fetch('http://localhost:5000/api/story/generate-complete', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title, content, num_scenes: 10 })
  });
  return await response.json();
};

// Build video with subtitles
const buildVideo = async (images, sceneAudio, narrations, title) => {
  const response = await fetch('http://localhost:5000/api/video/build', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      images: images, // Array of base64 encoded images
      scene_audio: sceneAudio, // Object with scene_1, scene_2, etc.
      title: title,
      narrations: narrations, // Object or array of narration texts
      generate_subtitles: true,
      upload_to_supabase: true
    })
  });
  const data = await response.json();
  
  // Decode video and subtitles
  if (data.success) {
    const videoBlob = base64ToBlob(data.video, 'video/mp4');
    const subtitlesBlob = data.subtitles 
      ? base64ToBlob(data.subtitles, 'text/plain')
      : null;
    
    return {
      video: videoBlob,
      subtitles: subtitlesBlob,
      subtitlesUrl: data.subtitles_url,
      timings: data.timings
    };
  }
};

// Helper function to convert base64 to Blob
const base64ToBlob = (base64, mimeType) => {
  const byteCharacters = atob(base64);
  const byteNumbers = new Array(byteCharacters.length);
  for (let i = 0; i < byteCharacters.length; i++) {
    byteNumbers[i] = byteCharacters.charCodeAt(i);
  }
  const byteArray = new Uint8Array(byteNumbers);
  return new Blob([byteArray], { type: mimeType });
};
```

## 📦 Deployment

### Production Setup

1. Set `FLASK_ENV=production` in `.env`
2. Use a production WSGI server (gunicorn/waitress):

```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Docker Deployment (Optional)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

## 📝 Subtitle Implementation Details

### How Subtitles Work

1. **Generation**: Subtitles are generated from narration texts after video rendering
2. **Format**: SRT (SubRip) format with HTML styling tags
3. **Timing**: Calculated from scene durations which are based on audio length
4. **Text Processing**: 
   - Removes markdown formatting
   - Extracts clean narration text
   - Wraps text to max 3 lines per subtitle
   - Applies styling (white text, black outline)

### Subtitle File Structure

```
1
00:00:00,000 --> 00:00:03,500
<font size='28' face='Arial' color='#FFFFFF' outline='2' outline-color='#000000'>First subtitle line</font>

2
00:00:03,500 --> 00:00:07,200
<font size='28' face='Arial' color='#FFFFFF' outline='2' outline-color='#000000'>Second subtitle line</font>
```

### Using Subtitles in Frontend

**Option 1: HTML5 Video Player**
```html
<video controls>
  <source src="video.mp4" type="video/mp4">
  <track kind="subtitles" src="subtitles.srt" srclang="en" label="English" default>
</video>
```

**Option 2: Download Link**
```javascript
<a href={subtitlesUrl} download="video.srt">
  Download Subtitles
</a>
```

**Option 3: VLC/External Players**
- Place SRT file in same directory as video with same name
- Most players will auto-detect and load subtitles

### Limitations & Future Improvements

**Current Limitations:**
- Subtitles are external files (not burned into video)
- May not work with all video players
- Not visible on social media platforms

**Future Enhancements:**
- Option to burn subtitles directly into video using MoviePy TextClip
- Multiple language subtitle support
- Subtitle customization (position, size, colors)
- Automatic subtitle synchronization improvements

## 🤝 Contributing

This is a complete conversion from Streamlit to Flask. All functionality has been preserved and enhanced with:

- RESTful API design
- Supabase Storage integration
- Better error handling
- Request validation
- Comprehensive logging
- Subtitle generation support

## 📝 License

Same as the original Streamlit application.

## 🆘 Support

For issues or questions:
1. Check `vidyai_flask.log` for errors
2. Review [API_DOCUMENTATION.md](./API_DOCUMENTATION.md)
3. Verify all environment variables are set correctly
4. Check that all API keys are valid and have sufficient quota
5. For subtitle issues, see [SUBTITLE_ANALYSIS.md](./SUBTITLE_ANALYSIS.md)

## 📋 Related Documentation

- [API_DOCUMENTATION.md](./API_DOCUMENTATION.md) - Complete API reference
- [SUBTITLE_ANALYSIS.md](./SUBTITLE_ANALYSIS.md) - Detailed subtitle implementation analysis

---

**Note:** This Flask backend replaces the Streamlit application entirely and provides a production-ready API for your React frontend. Subtitles are generated as external SRT files for maximum compatibility with various video players.

