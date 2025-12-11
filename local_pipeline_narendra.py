"""
End-to-end local pipeline for "Narendra Modi" using existing images in
`data/Test` and generating everything else (storyline, prompts,
narrations, TTS audio, video, subtitles). No image generation is done.
"""

import os
import json
from typing import List, Dict

import requests
from dotenv import load_dotenv

# Load env before importing services (Supabase client initializes on import)
load_dotenv()

from services.story_service import StoryService
from services.narration_service import NarrationService
from services.tts_service import tts_service
from services.video_service import video_service
from utils.helpers import sanitize_filename

TITLE = "Narendra Modi"
TITLE_SANITIZED = sanitize_filename(TITLE)
IMAGES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "Test")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "test_narendra")
# Aim for a ~30 second final video; scenes derive their pacing from this.
TARGET_VIDEO_SECONDS = 30


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def load_images() -> List[bytes]:
    files = [f for f in os.listdir(IMAGES_DIR) if f.lower().endswith((".jpg", ".jpeg", ".png"))]
    files.sort()  # scene_1, scene_2, ...
    if not files:
        raise RuntimeError(f"No images found in {IMAGES_DIR}")
    images = []
    for fname in files:
        with open(os.path.join(IMAGES_DIR, fname), "rb") as f:
            images.append(f.read())
    print(f"Loaded {len(images)} images from {IMAGES_DIR}")
    return images


def fetch_wikipedia_content(title: str) -> str:
    """Fetch a compact page summary to seed storyline generation."""
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{title.replace(' ', '%20')}"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            parts = [data.get("title", ""), data.get("description", ""), data.get("extract", "")]
            return "\n\n".join(p for p in parts if p)
    except Exception as e:
        print(f"Warning: failed to fetch Wikipedia summary: {e}")
    return f"{title} biography and career highlights."


def generate_story_and_prompts(num_scenes: int) -> Dict[str, any]:
    groq_key = os.getenv("GROQ_API_KEY")
    if not groq_key:
        raise RuntimeError("GROQ_API_KEY is required")
    story_service = StoryService(groq_key)

    content = fetch_wikipedia_content(TITLE)
    storyline = story_service.generate_comic_storyline(
        title=TITLE,
        content=content,
        target_length="medium",
        max_chars=20000,
        tone="enthusiastic",
        target_audience="general",
        complexity="moderate",
        focus_style="highlights",
        scene_count=num_scenes,
        educational_level="intermediate",
        visual_style="documentary",
    )

    scene_prompts = story_service.generate_scene_prompts(
        title=TITLE,
        storyline=storyline,
        comic_style="western comic",
        num_scenes=num_scenes,
        age_group="general",
        education_level="intermediate",
        visual_detail="moderate",
        camera_style="varied",
        color_palette="natural",
        scene_pacing="moderate",
    )

    return {"storyline": storyline, "scene_prompts": scene_prompts}


def generate_narrations(scene_prompts: List[str], target_scene_seconds: float) -> Dict[str, str]:
    groq_key = os.getenv("GROQ_API_KEY")
    if not groq_key:
        raise RuntimeError("GROQ_API_KEY is required")
    narration_service = NarrationService(groq_key)

    narrations: Dict[str, str] = {}
    for i, prompt in enumerate(scene_prompts, 1):
        narration = narration_service.generate_scene_narration(
            title=TITLE,
            scene_prompt=prompt,
            scene_number=i,
            storyline="",
            narration_style="documentary",
            voice_tone="engaging",
            target_seconds=target_scene_seconds,
            min_words=20,
            max_words=50,
        )
        narrations[f"scene_{i}"] = narration
    return narrations


def synthesize_audio(narrations: Dict[str, str]) -> Dict[str, bytes]:
    scene_audio: Dict[str, bytes] = {}
    for scene_key, text in narrations.items():
        if not text:
            continue
        audio_data = tts_service.synthesize_to_mp3(text, lang="en", tld="com", slow=False, speed=1.25)
        scene_audio[scene_key] = audio_data
    return scene_audio


def build_video(images: List[bytes], scene_audio: Dict[str, bytes], narrations_list: List[str]):
    result = video_service.build_video(
        images=images,
        scene_audio=scene_audio,
        title=TITLE,
        title_sanitized=TITLE_SANITIZED,
        generate_subtitles=True,
        return_subtitles=True,
        subtitle_narrations=narrations_list,
        fps=30,
        resolution=(1920, 1080),
        crossfade_sec=0.3,
        min_scene_seconds=1.5,
    )
    if not isinstance(result, dict):
        raise RuntimeError("Expected dict with subtitles; got bytes")
    return result


def save_outputs(result: Dict[str, any]):
    _ensure_dir(OUTPUT_DIR)
    video_path = os.path.join(OUTPUT_DIR, f"{TITLE_SANITIZED}.mp4")
    srt_path = os.path.join(OUTPUT_DIR, f"{TITLE_SANITIZED}.srt")
    timings_path = os.path.join(OUTPUT_DIR, f"{TITLE_SANITIZED}_timings.json")

    with open(video_path, "wb") as f:
        f.write(result["video_data"])
    if result.get("subtitles_bytes"):
        with open(srt_path, "wb") as f:
            f.write(result["subtitles_bytes"])
    with open(timings_path, "w", encoding="utf-8") as f:
        json.dump(result.get("timings"), f, indent=2)

    print(f"Saved video: {video_path}")
    if result.get("subtitles_bytes"):
        print(f"Saved subtitles: {srt_path}")
    print(f"Saved timings: {timings_path}")


def main():
    images = load_images()
    num_scenes = len(images)
    target_scene_seconds = max(4.0, TARGET_VIDEO_SECONDS / max(1, num_scenes))

    print("Generating storyline and scene prompts...")
    story_data = generate_story_and_prompts(num_scenes)

    print("Generating narrations...")
    narrations_dict = generate_narrations(story_data["scene_prompts"], target_scene_seconds)
    narrations_list = [narrations_dict.get(f"scene_{i}", "") for i in range(1, num_scenes + 1)]

    print("Synthesizing audio...")
    scene_audio = synthesize_audio(narrations_dict)

    print("Building video with subtitles...")
    result = build_video(images, scene_audio, narrations_list)

    print("Saving outputs...")
    save_outputs(result)

    print("Done. Check the MP4+SRT in:", OUTPUT_DIR)


if __name__ == "__main__":
    main()

