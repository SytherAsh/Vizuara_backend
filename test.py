"""
Test script for video generation pipeline
Tests all steps: image loading -> narration generation -> audio generation -> video building

This script is designed to help debug audio merging issues in video generation.
It will:
1. Load images from the data folder (scene_1.jpg, scene_2.jpg, etc.)
2. Generate narration text for each scene (uses Groq API if available, otherwise mock data)
3. Generate audio files from narrations using TTS (gTTS)
4. Build final video by merging images with audio tracks

Usage:
    python test.py

To control video duration:
    Edit MAX_VIDEO_DURATION in this file (line ~60)
    - Set to None for no limit
    - Set to a number (e.g., 60.0) to limit video to that many seconds
    - The script will automatically trim scenes proportionally to fit

Requirements:
    - Images in VidyAi_Flask/data/ folder (scene_1.jpg, scene_2.jpg, etc.)
    - GROQ_API_KEY in .env file (optional - will use mock narrations if not set)
    - MoviePy installed (for video generation)
    - gTTS installed (for audio generation)

Output:
    - Audio files: data/test_output/scene_1.mp3, scene_2.mp3, etc.
    - Video file: data/test_output/Test Video.mp4
"""

import os
import sys
import logging
from typing import Dict, List, Any
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_video_generation")

# Import services
from services.narration_service import NarrationService
from services.tts_service import TTSService
from services.video_service import VideoService
from services.supabase_service import supabase_service
from utils.helpers import sanitize_filename

# Test configuration
TEST_TITLE = "Chhatrapati Shivaji Maharaj"
PROJECT_NAME = sanitize_filename(os.getenv("TEST_PROJECT_NAME", TEST_TITLE))
TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), "data/Test")

# Video duration control (set to None for no limit, or specify max seconds)
MAX_VIDEO_DURATION = 30  # target ~30 second video
# Toggle whether to upload generated assets to Supabase instead of writing locally
UPLOAD_TO_SUPABASE = True
# Toggle to pull source images from Supabase (images bucket) instead of local data folder
USE_SUPABASE_IMAGES = True

# Mock storyline and scene prompts (you can replace these with real data)
MOCK_STORYLINE = """
This is a test story about an epic adventure. The hero embarks on a journey to save the kingdom.
Along the way, they face challenges, meet allies, and overcome obstacles to achieve their goal.
"""

MOCK_SCENE_PROMPTS = [
    "Scene 1: Young Shivaji surveys the Sahyadri hill forts at dawn, Maratha warriors by his side as saffron flags flutter.",
    "Scene 2: Shivaji rides into a bustling fort courtyard, greeted by soldiers and citizens, the royal seal being presented."
]


def _load_images_from_supabase(project_name: str) -> List[bytes]:
    """Load scene images from Supabase images bucket."""
    bucket = 'images'
    # List files under project prefix
    list_result = supabase_service.list_files(bucket, project_name)
    if not list_result.get("success"):
        raise FileNotFoundError(f"Unable to list images in Supabase for {project_name}: {list_result.get('error')}")
    files = list_result.get("files", [])
    scene_files = sorted([f["name"] for f in files if f and f.get("name", "").startswith(f"{project_name}/scene_")])
    if not scene_files:
        raise FileNotFoundError(f"No scene images found in Supabase under {project_name}")
    images: List[bytes] = []
    for path in scene_files:
        dl = supabase_service.download_file(bucket, path)
        if not dl.get("success") or not dl.get("file_data"):
            raise FileNotFoundError(f"Failed to download {path} from Supabase")
        images.append(dl["file_data"])
        logger.info(f"  ✓ Loaded {path} ({len(dl['file_data'])} bytes)")
    logger.info(f"✅ Loaded {len(images)} images from Supabase")
    return images


def _load_images_from_local() -> List[bytes]:
    """Load images from local data folder (fallback)."""
    image_files = sorted([f for f in os.listdir(TEST_DATA_DIR) if f.startswith("scene_") and f.endswith(".jpg")])
    if not image_files:
        raise FileNotFoundError(f"No scene images found in {TEST_DATA_DIR}")
    images: List[bytes] = []
    for img_file in image_files:
        img_path = os.path.join(TEST_DATA_DIR, img_file)
        with open(img_path, 'rb') as f:
            data = f.read()
            images.append(data)
            logger.info(f"  ✓ Loaded {img_file} ({len(data)} bytes)")
    logger.info(f"✅ Loaded {len(images)} images from local folder")
    return images


def load_images() -> List[bytes]:
    """Load images from Supabase (preferred) or local fallback."""
    logger.info("=" * 60)
    logger.info("STEP 1: Loading Images")
    logger.info("=" * 60)
    if USE_SUPABASE_IMAGES:
        try:
            return _load_images_from_supabase(PROJECT_NAME)
        except Exception as e:
            logger.warning(f"Supabase image load failed ({e}); falling back to local data folder")
    return _load_images_from_local()


def generate_narrations(images: List[bytes], use_mock: bool = False) -> Dict[str, Any]:
    """Generate narrations for all scenes"""
    logger.info("=" * 60)
    logger.info("STEP 2: Generating Narrations")
    logger.info("=" * 60)
    
    groq_api_key = os.getenv("GROQ_API_KEY")
    num_scenes = len(images)
    
    if not groq_api_key and not use_mock:
        logger.warning("⚠️  GROQ_API_KEY not found in environment")
        logger.warning("   Using mock narrations. Set GROQ_API_KEY to generate real narrations.")
        use_mock = True
    
    narrations = {}
    
    if use_mock:
        # Use mock narrations
        logger.info("Using mock narrations...")
        mock_narration_texts = [
            "The hero stands in a grand palace, ready for an epic adventure. The kingdom awaits their journey.",
            "Our hero begins their quest, walking through a beautiful forest. The path ahead is full of possibilities.",
            "A great challenge appears before the hero. They must overcome this obstacle to continue their journey.",
            "An ally joins the hero, offering help and friendship. Together they are stronger than alone.",
            "The hero reaches their destination, victorious and triumphant. The kingdom is saved!"
        ]
        
        # Extend mock narrations if we have more scenes
        while len(mock_narration_texts) < num_scenes:
            mock_narration_texts.append(f"Scene {len(mock_narration_texts) + 1} continues the epic journey.")
        
        for i in range(1, num_scenes + 1):
            narration_text = mock_narration_texts[i-1] if i <= len(mock_narration_texts) else f"Scene {i} narration."
            scene_key = f"scene_{i}"
            narrations[scene_key] = {
                "scene_number": i,
                "narration": narration_text,
                "scene_prompt": MOCK_SCENE_PROMPTS[i-1] if i <= len(MOCK_SCENE_PROMPTS) else f"Scene {i} description."
            }
            logger.info(f"  ✓ Generated mock narration for scene {i}: {narration_text[:50]}...")
    else:
        # Generate real narrations using Groq
        logger.info("Generating narrations using Groq API...")
        narration_service = NarrationService(groq_api_key)
        
        # Use available scene prompts or generate generic ones
        scene_prompts = MOCK_SCENE_PROMPTS[:num_scenes]
        while len(scene_prompts) < num_scenes:
            scene_prompts.append(f"Scene {len(scene_prompts) + 1} of the story.")
        
        for i, scene_prompt in enumerate(scene_prompts, 1):
            try:
                narration_text = narration_service.generate_scene_narration(
                    title=TEST_TITLE,
                    scene_prompt=scene_prompt,
                    scene_number=i,
                    storyline=MOCK_STORYLINE,
                    narration_style="dramatic",
                    voice_tone="engaging"
                )
                
                scene_key = f"scene_{i}"
                narrations[scene_key] = {
                    "scene_number": i,
                    "narration": narration_text,
                    "scene_prompt": scene_prompt
                }
                logger.info(f"  ✓ Generated narration for scene {i}: {narration_text[:50]}...")
            except Exception as e:
                logger.error(f"  ✗ Error generating narration for scene {i}: {e}")
                # Fallback to mock
                narrations[f"scene_{i}"] = {
                    "scene_number": i,
                    "narration": f"Scene {i} narration text.",
                    "scene_prompt": scene_prompt
                }
    
    logger.info(f"✅ Successfully generated {len(narrations)} narrations")
    return {"narrations": narrations, "title": TEST_TITLE}


def generate_audio(narrations: Dict[str, Any]) -> Dict[str, bytes]:
    """Generate audio files from narrations"""
    logger.info("=" * 60)
    logger.info("STEP 3: Generating Audio (TTS)")
    logger.info("=" * 60)
    
    tts_service = TTSService()
    scene_audio: Dict[str, bytes] = {}
    
    narrs = narrations.get("narrations", {})
    
    for scene_key, scene_data in narrs.items():
        scene_num = scene_data.get("scene_number")
        narration_text = scene_data.get("narration", "").strip()
        
        if not narration_text:
            logger.warning(f"No narration text for {scene_key}, skipping")
            continue
        
        try:
            logger.info(f"  Generating audio for scene {scene_num}...")
            audio_data = tts_service.synthesize_to_mp3(
                text=narration_text,
                lang="en",
                tld="com",
                slow=False,
                speed=1.25  # 25% faster
            )
            
            scene_audio[scene_key] = audio_data
            
            duration = tts_service.estimate_tts_duration_seconds(narration_text, speed=1.25)
            logger.info(f"  ✓ Generated audio for scene {scene_num} (~{duration:.1f}s, {len(audio_data)} bytes)")
            
        except Exception as e:
            logger.error(f"  ✗ Error generating audio for scene {scene_num}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    logger.info(f"✅ Successfully generated {len(scene_audio)} audio files")
    return scene_audio


def build_video(images: List[bytes], scene_audio: Dict[str, bytes]) -> bytes:
    """Build final video from images and audio"""
    logger.info("=" * 60)
    logger.info("STEP 4: Building Video")
    logger.info("=" * 60)
    
    video_service = VideoService()
    
    try:
        logger.info(f"Building video with {len(images)} scenes and {len(scene_audio)} audio tracks...")
        
        video_result = video_service.build_video(
            images=images,
            scene_audio=scene_audio,
            title=TEST_TITLE,
            fps=30,
            resolution=(1920, 1080),
            crossfade_sec=0.3,
            min_scene_seconds=2.0,
            head_pad=0.15,
            tail_pad=0.15,
            bg_music_data=None,  # Optional: add background music
            bg_music_volume=0.08,
            ken_burns=True,
            kb_zoom_start=1.05,
            kb_zoom_end=1.15,
            kb_pan="auto",
            max_video_duration=MAX_VIDEO_DURATION,
            title_sanitized=PROJECT_NAME,
            generate_subtitles=True,
            return_subtitles=True,
            subtitle_narrations=[scene_audio.get(f"scene_{i}", b"") and "" for i in range(1, len(images) + 1)]
        )

        if isinstance(video_result, dict):
            video_data = video_result.get("video_data")
            subtitles_bytes = video_result.get("subtitles_bytes")
            timings = video_result.get("timings")
        else:
            video_data = video_result
            subtitles_bytes = None
            timings = None

        if not video_data:
            raise RuntimeError("Video generation returned empty data")

        logger.info(f"✅ Video generated successfully! Size: {len(video_data) / (1024*1024):.2f} MB")

        upload_info = {}
        if UPLOAD_TO_SUPABASE:
            video_path = f"{PROJECT_NAME}/{PROJECT_NAME}.mp4"
            up_video = supabase_service.upload_file('video', video_path, video_data, 'video/mp4')
            upload_info["video_path"] = video_path
            upload_info["video_url"] = up_video.get("public_url")
            logger.info(f"Uploaded video to Supabase: {upload_info['video_url']}")

            if subtitles_bytes:
                sub_path = f"{PROJECT_NAME}/{PROJECT_NAME}.srt"
                up_sub = supabase_service.upload_file('video', sub_path, subtitles_bytes, 'text/plain')
                upload_info["subtitles_path"] = sub_path
                upload_info["subtitles_url"] = up_sub.get("public_url")
                logger.info(f"Uploaded subtitles to Supabase: {upload_info.get('subtitles_url')}")

            if timings is not None:
                import json
                timings_bytes = json.dumps(timings, indent=2).encode("utf-8")
                time_path = f"{PROJECT_NAME}/{PROJECT_NAME}_timings.json"
                up_time = supabase_service.upload_file('metadata', time_path, timings_bytes, 'application/json')
                upload_info["timings_path"] = time_path
                upload_info["timings_url"] = up_time.get("public_url")

        return video_data
        
    except Exception as e:
        logger.error(f"✗ Error building video: {e}")
        import traceback
        traceback.print_exc()
        raise


def main():
    """Main test function"""
    logger.info("=" * 60)
    logger.info("VIDEO GENERATION PIPELINE TEST")
    logger.info("=" * 60)
    logger.info(f"Title: {TEST_TITLE}")
    logger.info(f"Project name (Supabase prefix): {PROJECT_NAME}")
    logger.info(f"Source images: {'Supabase' if USE_SUPABASE_IMAGES else 'local data folder'}")
    logger.info(f"Upload outputs to Supabase: {UPLOAD_TO_SUPABASE}")
    if MAX_VIDEO_DURATION:
        logger.info(f"Maximum video duration: {MAX_VIDEO_DURATION:.1f} seconds")
    else:
        logger.info("Maximum video duration: No limit")
    logger.info("")
    
    try:
        images = load_images()
        logger.info("")
        
        narrations = generate_narrations(images, use_mock=False)
        logger.info("")
        
        scene_audio = generate_audio(narrations)
        logger.info("")
        
        if len(scene_audio) < len(images):
            logger.warning(f"⚠️  Warning: Only {len(scene_audio)} audio files generated for {len(images)} images")
            logger.warning("   Video will be created with available audio only")
        
        video_data = build_video(images, scene_audio)
        logger.info("")
        
        logger.info("=" * 60)
        logger.info("✅ ALL STEPS COMPLETED SUCCESSFULLY!")
        logger.info("=" * 60)
        logger.info(f"Images processed: {len(images)}")
        logger.info(f"Narrations generated: {len(narrations.get('narrations', {}))}")
        logger.info(f"Audio files generated: {len(scene_audio)}")
        logger.info(f"Video size: {len(video_data) / (1024*1024):.2f} MB")
        
    except Exception as e:
        logger.error("=" * 60)
        logger.error("❌ TEST FAILED")
        logger.error("=" * 60)
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

