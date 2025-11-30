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
from pathlib import Path
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

# Test configuration
TEST_TITLE = "Test Video"
TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
TEST_OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "data", "test_output")
os.makedirs(TEST_OUTPUT_DIR, exist_ok=True)

# Video duration control (set to None for no limit, or specify max seconds)
# Example: MAX_VIDEO_DURATION = 60.0  # 60 seconds max
MAX_VIDEO_DURATION = 60  # Change this to limit video duration (e.g., 60.0 for 60 seconds)

# Mock storyline and scene prompts (you can replace these with real data)
MOCK_STORYLINE = """
This is a test story about an epic adventure. The hero embarks on a journey to save the kingdom.
Along the way, they face challenges, meet allies, and overcome obstacles to achieve their goal.
"""

MOCK_SCENE_PROMPTS = [
    "Scene 1: The hero stands in a grand palace, looking determined. The setting is majestic with golden decorations.",
    "Scene 2: The hero begins their journey, walking through a beautiful forest with sunlight filtering through trees.",
    "Scene 3: The hero encounters a challenge - a large obstacle blocking their path. They look determined to overcome it.",
    "Scene 4: The hero meets an ally who offers help. They shake hands in a friendly forest clearing.",
    "Scene 5: The hero reaches their destination - a beautiful kingdom. They stand victorious with arms raised."
]


def load_images() -> List[bytes]:
    """Load images from data folder"""
    logger.info("=" * 60)
    logger.info("STEP 1: Loading Images")
    logger.info("=" * 60)
    
    images = []
    image_files = sorted([f for f in os.listdir(TEST_DATA_DIR) if f.startswith("scene_") and f.endswith(".jpg")])
    
    if not image_files:
        raise FileNotFoundError(f"No scene images found in {TEST_DATA_DIR}")
    
    logger.info(f"Found {len(image_files)} image files")
    
    for img_file in image_files:
        img_path = os.path.join(TEST_DATA_DIR, img_file)
        with open(img_path, 'rb') as f:
            img_data = f.read()
            images.append(img_data)
            logger.info(f"  ✓ Loaded {img_file} ({len(img_data)} bytes)")
    
    logger.info(f"✅ Successfully loaded {len(images)} images")
    return images


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
    scene_audio = {}
    
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
            
            # Save audio file for debugging
            audio_path = os.path.join(TEST_OUTPUT_DIR, f"{scene_key}.mp3")
            with open(audio_path, 'wb') as f:
                f.write(audio_data)
            
            duration = tts_service.estimate_tts_duration_seconds(narration_text, speed=1.25)
            logger.info(f"  ✓ Generated audio for scene {scene_num} (~{duration:.1f}s, {len(audio_data)} bytes)")
            logger.info(f"    Saved to: {audio_path}")
            
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
        
        video_data = video_service.build_video(
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
            max_video_duration=MAX_VIDEO_DURATION  # Limit video duration if set
        )
        
        # Save video file
        video_path = os.path.join(TEST_OUTPUT_DIR, f"{TEST_TITLE}.mp4")
        with open(video_path, 'wb') as f:
            f.write(video_data)
        
        logger.info(f"✅ Video generated successfully!")
        logger.info(f"   Output: {video_path}")
        logger.info(f"   Size: {len(video_data) / (1024*1024):.2f} MB")
        
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
    logger.info(f"Data directory: {TEST_DATA_DIR}")
    logger.info(f"Output directory: {TEST_OUTPUT_DIR}")
    if MAX_VIDEO_DURATION:
        logger.info(f"Maximum video duration: {MAX_VIDEO_DURATION:.1f} seconds")
    else:
        logger.info("Maximum video duration: No limit")
    logger.info("")
    
    try:
        # Step 1: Load images
        images = load_images()
        logger.info("")
        
        # Step 2: Generate narrations
        narrations = generate_narrations(images, use_mock=False)
        logger.info("")
        
        # Step 3: Generate audio
        scene_audio = generate_audio(narrations)
        logger.info("")
        
        # Validate that we have audio for all scenes
        if len(scene_audio) < len(images):
            logger.warning(f"⚠️  Warning: Only {len(scene_audio)} audio files generated for {len(images)} images")
            logger.warning("   Video will be created with available audio only")
        
        # Step 4: Build video
        video_data = build_video(images, scene_audio)
        logger.info("")
        
        # Summary
        logger.info("=" * 60)
        logger.info("✅ ALL STEPS COMPLETED SUCCESSFULLY!")
        logger.info("=" * 60)
        logger.info(f"Images processed: {len(images)}")
        logger.info(f"Narrations generated: {len(narrations.get('narrations', {}))}")
        logger.info(f"Audio files generated: {len(scene_audio)}")
        logger.info(f"Video size: {len(video_data) / (1024*1024):.2f} MB")
        logger.info(f"Output directory: {TEST_OUTPUT_DIR}")
        logger.info("")
        logger.info("Check the output directory for:")
        logger.info("  - Individual audio files (scene_1.mp3, scene_2.mp3, etc.)")
        logger.info("  - Final video file (Test Video.mp4)")
        
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

