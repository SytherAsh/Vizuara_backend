"""
Video Service
Handles video compilation from images and audio using MoviePy
"""

import os
import re
import time
import logging
import tempfile
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from PIL import Image
from io import BytesIO
from services.supabase_service import supabase_service
from utils.helpers import sanitize_filename

logger = logging.getLogger("VidyAI_Flask")

# MoviePy setup
MOVIEPY_AVAILABLE = False
MOVIEPY_VERSION = 0

try:
    from moviepy import ImageClip, AudioFileClip, CompositeAudioClip, CompositeVideoClip, VideoClip, vfx
    try:
        from moviepy import AudioClip
        from moviepy.audio.fx import AudioFadeIn, AudioFadeOut
        import moviepy.audio.fx as afx
    except ImportError:
        AudioClip = None
        try:
            from moviepy.audio.fx import AudioFadeIn, AudioFadeOut
            import moviepy.audio.fx as afx
        except ImportError:
            afx = None
    MOVIEPY_AVAILABLE = True
    MOVIEPY_VERSION = 2
    logger.info("MoviePy 2.x detected and loaded")
except ImportError:
    try:
        import moviepy.editor as mpe
        MOVIEPY_AVAILABLE = True
        MOVIEPY_VERSION = 1
        logger.info("MoviePy 1.x detected and loaded")
    except ImportError as e:
        logger.warning(f"MoviePy not available: {e}")

# Configure imageio-ffmpeg
try:
    import imageio_ffmpeg
    os.environ["IMAGEIO_FFMPEG_EXE"] = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:
    pass


class MoviePyProgressLogger:
    """
    Custom logger that intercepts MoviePy's progress output and updates
    internal progress tracker without requiring backend requests.
    This eliminates the need for repeated polling during video rendering.
    """
    def __init__(self, progress_tracker, task_id, start_percent=80, end_percent=95):
        """
        Args:
            progress_tracker: ProgressTracker instance
            task_id: Task ID for progress tracking
            start_percent: Starting progress percentage (when rendering begins)
            end_percent: Ending progress percentage (when rendering completes)
        """
        self.progress_tracker = progress_tracker
        self.task_id = task_id
        self.start_percent = start_percent
        self.end_percent = end_percent
        self.progress_range = end_percent - start_percent
        self.last_update_percent = start_percent
        self.last_update_time = time.time()
        self.min_update_interval = 2.0  # Update at most once every 2 seconds
        self.min_progress_delta = 2  # Only update if progress changed by at least 2%
        
        # Pattern to match MoviePy progress bar output
        # Example: "frame_index:  20%|████| 328/1631 [01:54<08:06, 2.68it/s]"
        self.re_pattern = re.compile(
            r'frame_index:\s*(\d+)%\|.*?\|.*?(\d+)/(\d+).*?\[(.*?)\]',
            re.IGNORECASE
        )
    
    def __call__(self, message):
        """Called by MoviePy with progress messages"""
        if not message:
            return
        
        message_str = str(message)
        
        # Parse MoviePy progress bar output
        match = self.re_pattern.search(message_str)
        if match:
            try:
                percent_str = match.group(1)
                current_frame = int(match.group(2))
                total_frames = int(match.group(3))
                time_info = match.group(4)
                
                # Calculate rendering progress (0.0 to 1.0)
                if total_frames > 0:
                    rendering_progress = current_frame / total_frames
                else:
                    rendering_progress = float(percent_str) / 100.0
                
                # Map to overall progress (80% to 95%)
                overall_progress = int(self.start_percent + (rendering_progress * self.progress_range))
                
                # Throttle updates: only update if enough time passed AND progress changed significantly
                current_time = time.time()
                progress_delta = abs(overall_progress - self.last_update_percent)
                time_delta = current_time - self.last_update_time
                
                if (progress_delta >= self.min_progress_delta and 
                    time_delta >= self.min_update_interval):
                    
                    # Parse time remaining from MoviePy output
                    time_remaining = None
                    if '<' in time_info:
                        try:
                            time_parts = time_info.split('<')[1].split(',')[0].strip()
                            # Parse MM:SS format
                            if ':' in time_parts:
                                mins, secs = map(int, time_parts.split(':'))
                                time_remaining = mins * 60 + secs
                        except:
                            pass
                    
                    message_text = f"Rendering video... {percent_str}%"
                    if time_remaining:
                        message_text += f" (~{time_remaining}s remaining)"
                    
                    # Update progress tracker (in-memory, no backend request)
                    self.progress_tracker.set_progress(
                        self.task_id,
                        overall_progress,
                        message_text,
                        current_frame,
                        total_frames
                    )
                    
                    self.last_update_percent = overall_progress
                    self.last_update_time = current_time
                    
            except Exception as e:
                # Silently ignore parsing errors to avoid disrupting video generation
                logger.debug(f"Progress parsing error: {e}")


class VideoService:
    """Service for video generation"""
    
    def __init__(self):
        """Initialize Video Service"""
        if not MOVIEPY_AVAILABLE:
            logger.error("MoviePy is not available. Video generation will not work.")
        else:
            logger.info(f"VideoService initialized with MoviePy {MOVIEPY_VERSION}.x")

    # ------------------------------------------------------------------
    # Subtitle helpers
    # ------------------------------------------------------------------
    def _clean_narration_for_subtitles(self, raw: str) -> str:
        """
        Strip headings/markdown so subtitles contain only spoken text.
        """
        if not raw:
            return ""

        text = raw.replace("\r\n", "\n")

        # Prefer "Narration Text" section if present
        match = re.search(
            r"##\s*Narration\s*Text\s*(.*?)(?:^=+|^##\s*Original Scene Prompt|^##\s*Narrative Context|\Z)",
            text,
            flags=re.IGNORECASE | re.DOTALL | re.MULTILINE,
        )
        if match:
            text = match.group(1).strip()
        else:
            lines = []
            for line in text.split("\n"):
                stripped = line.strip()
                if not stripped:
                    continue
                if stripped.startswith("#"):
                    continue
                if stripped.lower().startswith(("original scene prompt", "narrative context")):
                    continue
                if set(stripped) <= {"=", "-"} and len(stripped) >= 3:
                    continue
                lines.append(stripped)
            text = "\n".join(lines).strip()

        text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
        text = re.sub(r"\*(.*?)\*", r"\1", text)
        text = re.sub(r"\n{2,}", "\n", text)
        return text.strip()

    def _format_srt_time(self, seconds: float) -> str:
        if seconds < 0:
            seconds = 0
        total_ms = int(round(seconds * 1000))
        ms = total_ms % 1000
        total_seconds = total_ms // 1000
        s = total_seconds % 60
        total_minutes = total_seconds // 60
        m = total_minutes % 60
        h = total_minutes // 60
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    def _split_into_lines(self, text: str, max_len: int = 42) -> List[str]:
        words = text.strip().split()
        if not words:
            return []

        lines = []
        current = []
        for word in words:
            candidate = (" ".join(current + [word])).strip()
            if len(candidate) <= max_len:
                current.append(word)
            else:
                if current:
                    lines.append(" ".join(current))
                current = [word]
        if current:
            lines.append(" ".join(current))
        return lines

    def _load_scene_narrations(self, title_sanitized: str, num_scenes: int) -> Optional[List[str]]:
        """
        Load per-scene narration text from Supabase text bucket.
        Path: text/{title_sanitized}/scene_{i}_narration.txt
        """
        narrations: List[str] = []
        if not title_sanitized:
            return None

        for i in range(1, num_scenes + 1):
            path = f"{title_sanitized}/scene_{i}_narration.txt"
            try:
                result = supabase_service.download_file('text', path)
                if result.get('success') and result.get('file_data'):
                    raw = result['file_data'].decode('utf-8', errors='ignore')
                    narrations.append(self._clean_narration_for_subtitles(raw))
                else:
                    narrations.append("")
            except Exception as e:
                logger.debug(f"Could not load narration for scene {i} at {path}: {e}")
                narrations.append("")

        if all(not n for n in narrations):
            return None
        return narrations

    def _generate_subtitles_text(self, timings: List[Dict[str, Any]], narrations: List[str]) -> Optional[str]:
        if not timings or not narrations:
            return None

        timings_sorted = sorted(timings, key=lambda t: t.get("start", 0.0))
        lines: List[str] = []
        block_index = 1

        for t in timings_sorted:
            scene_num = t.get("scene")
            if not isinstance(scene_num, int):
                continue

            if scene_num < 1 or scene_num > len(narrations):
                text = ""
            else:
                text = (narrations[scene_num - 1] or "").strip()

            if not text:
                continue

            start = float(t.get("start", 0.0))
            end = float(t.get("end", start))

            start_str = self._format_srt_time(start)
            end_str = self._format_srt_time(end)

            best_lines = None
            for width in [90, 110, 120]:
                test_lines = self._split_into_lines(text, max_len=width)
                if len(test_lines) <= 3:
                    best_lines = test_lines
                    break
            if best_lines is None:
                best_lines = self._split_into_lines(text, max_len=120)[:3]

            styled_lines = [
                f"<font size='28' face='Arial' color='#FFFFFF' outline='2' outline-color='#000000'>{line}</font>"
                for line in best_lines
            ]

            block = [
                str(block_index),
                f"{start_str} --> {end_str}",
                *styled_lines,
                "",
            ]
            lines.extend(block)
            block_index += 1

        if block_index == 1:
            return None

        return "\n".join(lines)
    
    def _get_audio_duration_seconds(self, audio_data: bytes) -> float:
        """Get audio duration from bytes"""
        # Try pydub first
        try:
            from pydub import AudioSegment
            seg = AudioSegment.from_file(BytesIO(audio_data))
            duration = seg.duration_seconds
            if duration > 0:
                return duration
        except Exception as e:
            logger.debug(f"Pydub failed to get audio duration: {e}")
        
        # Fallback: Try MoviePy (requires saving to temp file)
        try:
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
                tmp.write(audio_data)
                tmp_path = tmp.name
            
            try:
                if MOVIEPY_VERSION == 2:
                    with AudioFileClip(tmp_path) as audio:
                        duration = audio.duration
                else:
                    audio = mpe.AudioFileClip(tmp_path)
                    duration = audio.duration
                    audio.close()
                
                # Cleanup
                try:
                    os.unlink(tmp_path)
                except:
                    pass
                
                if duration and duration > 0:
                    return duration
            except Exception as e:
                logger.debug(f"MoviePy failed to get audio duration: {e}")
                try:
                    os.unlink(tmp_path)
                except:
                    pass
        except Exception:
            pass
        
        return 0.0
    
    def _estimate_scene_duration(
        self,
        audio_data: Optional[bytes],
        min_seconds: float,
        head_pad: float,
        tail_pad: float
    ) -> float:
        """Estimate scene duration based on audio (matching video_editor.py logic)"""
        duration = min_seconds
        if audio_data:
            d = self._get_audio_duration_seconds(audio_data)
            if d > 0:
                # Scene duration = audio duration + padding (matching video_editor.py)
                duration = max(min_seconds, d + head_pad + tail_pad)
        return duration
    
    def _apply_ken_burns_v2(
        self,
        clip,
        duration: float,
        scene_num: int,
        kb_zoom_start: float,
        kb_zoom_end: float,
        kb_pan: str,
        resolution: Tuple[int, int]
    ):
        """Apply Ken Burns effect for MoviePy 2.x"""
        w, h = resolution
        base_frame = clip.get_frame(0)
        base_img = Image.fromarray(base_frame.astype(np.uint8))
        
        def make_frame(t):
            progress = min(1.0, max(0.0, t / duration)) if duration > 0 else 0
            zoom = kb_zoom_start + (kb_zoom_end - kb_zoom_start) * progress
            
            pan_strength = 0.06
            dx, dy = 0, 0
            if kb_pan == "left" or (kb_pan == "auto" and scene_num % 4 == 1):
                dx = -pan_strength * progress
            elif kb_pan == "right" or (kb_pan == "auto" and scene_num % 4 == 2):
                dx = pan_strength * progress
            elif kb_pan == "up" or (kb_pan == "auto" and scene_num % 4 == 3):
                dy = -pan_strength * progress
            elif kb_pan == "down" or (kb_pan == "auto" and scene_num % 4 == 0):
                dy = pan_strength * progress
            
            zoomed_w = max(w, int(base_img.width * zoom))
            zoomed_h = max(h, int(base_img.height * zoom))
            img_zoomed = base_img.resize((zoomed_w, zoomed_h), Image.LANCZOS)
            zoomed = np.array(img_zoomed, dtype=np.uint8)
            
            center_x = zoomed_w // 2 + int(w * dx)
            center_y = zoomed_h // 2 + int(h * dy)
            
            x1 = max(0, min(center_x - w // 2, zoomed_w - w))
            y1 = max(0, min(center_y - h // 2, zoomed_h - h))
            x2 = min(zoomed_w, x1 + w)
            y2 = min(zoomed_h, y1 + h)
            
            cropped = zoomed[y1:y2, x1:x2]
            
            if cropped.shape[0] != h or cropped.shape[1] != w:
                output = np.zeros((h, w, 3), dtype=np.uint8)
                h_crop = min(cropped.shape[0], h)
                w_crop = min(cropped.shape[1], w)
                output[:h_crop, :w_crop] = cropped[:h_crop, :w_crop]
                return output
            
            return cropped
        
        return VideoClip(make_frame, duration=duration)
    
    def build_video(
        self,
        images: List[bytes],
        scene_audio: Dict[str, bytes],
        title: str,
        fps: int = 30,
        resolution: Tuple[int, int] = (1920, 1080),
        crossfade_sec: float = 0.3,
        min_scene_seconds: float = 2.0,
        head_pad: float = 0.15,
        tail_pad: float = 0.15,
        bg_music_data: Optional[bytes] = None,
        bg_music_volume: float = 0.08,
        ken_burns: bool = True,
        kb_zoom_start: float = 1.05,
        kb_zoom_end: float = 1.15,
        kb_pan: str = "auto",
        max_video_duration: Optional[float] = None,
        title_sanitized: Optional[str] = None,
        generate_subtitles: bool = False,
        return_subtitles: bool = False,
        subtitle_narrations: Optional[List[str]] = None
    ) -> Any:
        """
        Build video from images and audio
        
        Args:
            images: List of image data (bytes)
            scene_audio: Dict mapping scene keys to audio bytes
            title: Video title
            fps: Frame rate
            resolution: Video resolution
            crossfade_sec: Crossfade duration
            min_scene_seconds: Minimum scene duration
            head_pad: Audio head padding
            tail_pad: Audio tail padding
            bg_music_data: Background music bytes
            bg_music_volume: Background music volume
            ken_burns: Enable Ken Burns effect
            kb_zoom_start: Ken Burns start zoom
            kb_zoom_end: Ken Burns end zoom
            kb_pan: Ken Burns pan direction
            max_video_duration: Maximum video duration in seconds (None = no limit)
            title_sanitized: Folder-safe title for Supabase paths
            generate_subtitles: Generate SRT subtitles using narrations
            return_subtitles: Return subtitles bytes/timings instead of just video bytes
            subtitle_narrations: Optional narrations list to bypass loader
            
        Returns:
            Video data as bytes, or dict when return_subtitles=True
        """
        if not MOVIEPY_AVAILABLE:
            raise ImportError("❌ MoviePy is required for video generation")
        
        if not images:
            raise ValueError("❌ No images provided")
        
        logger.info(f"Building video: {len(images)} scenes, max_duration={max_video_duration:.1f}s" if max_video_duration else f"Building video: {len(images)} scenes")

        title_sanitized = title_sanitized or sanitize_filename(title)
        subtitles_bytes: Optional[bytes] = None
        subtitles_local_path: Optional[str] = None
        
        timings = []
        current_start = 0.0
        video_clips = []
        audio_tracks = []
        
        # Import progress tracker
        from services.progress_service import progress_tracker
        task_id = f"video_{title.replace(' ', '_')}"
        total_scenes = len(images)
        
        # Initialize progress
        progress_tracker.set_progress(task_id, 5, "Initializing video build...", 0, total_scenes)
        
        # Ephemeral temp workspace; cleaned automatically
        with tempfile.TemporaryDirectory(prefix='vidyai_video_') as temp_dir:
            logger.debug(f"Using temp directory: {temp_dir}")
            
            # First pass: Get actual audio durations and calculate scene durations
            # Parallelize audio duration calculation for better performance
            audio_durations = []
            scene_durations = []
            
            # Use ThreadPoolExecutor for I/O-bound audio duration calculations
            from concurrent.futures import ThreadPoolExecutor, as_completed
            
            def calculate_duration(idx):
                scene_num = idx + 1
                scene_key = f"scene_{scene_num}"
                audio_data = scene_audio.get(scene_key)
                if audio_data:
                    duration = self._get_audio_duration_seconds(audio_data)
                    return idx, duration
                return idx, 0.0
            
            # Process audio durations in parallel (I/O-bound operation)
            with ThreadPoolExecutor(max_workers=min(4, len(images))) as executor:
                future_to_idx = {executor.submit(calculate_duration, idx): idx for idx in range(len(images))}
                results = {}
                for future in as_completed(future_to_idx):
                    try:
                        idx, duration = future.result()
                        results[idx] = duration
                    except Exception as e:
                        idx = future_to_idx[future]
                        logger.warning(f"Failed to calculate duration for scene {idx + 1}: {e}")
                        results[idx] = 0.0
            
            # Build durations list in order
            for idx in range(len(images)):
                audio_duration = results.get(idx, 0.0)
                audio_durations.append(audio_duration)
                scene_durations.append(max(min_scene_seconds, audio_duration + head_pad + tail_pad))
            
            # Calculate total duration (accounting for crossfades)
            total_duration = sum(scene_durations)
            if len(scene_durations) > 1:
                total_duration -= crossfade_sec * (len(scene_durations) - 1)
            
            # If max_video_duration is set, reduce padding instead of scaling durations
            adjusted_head_pad = head_pad
            adjusted_tail_pad = tail_pad
            
            if max_video_duration and total_duration > max_video_duration:
                excess_duration = total_duration - max_video_duration
                total_padding = (head_pad + tail_pad) * len([a for a in audio_durations if a > 0])
                
                if total_padding > 0:
                    padding_reduction = min(excess_duration / total_padding, 0.8)  # Max 80% reduction
                    adjusted_head_pad = head_pad * (1 - padding_reduction)
                    adjusted_tail_pad = tail_pad * (1 - padding_reduction)
                    
                    scene_durations = []
                    for audio_dur in audio_durations:
                        if audio_dur > 0:
                            scene_duration = max(min_scene_seconds, audio_dur + adjusted_head_pad + adjusted_tail_pad)
                        else:
                            scene_duration = min_scene_seconds
                        scene_durations.append(scene_duration)
                    
                    total_duration = sum(scene_durations)
                    if len(scene_durations) > 1:
                        total_duration -= crossfade_sec * (len(scene_durations) - 1)
                    
                    logger.info(f"   Video duration ({total_duration:.1f}s) exceeds max ({max_video_duration:.1f}s)")
                    logger.info(f"   Reducing padding from {head_pad + tail_pad:.2f}s to {adjusted_head_pad + adjusted_tail_pad:.2f}s per scene")
                    logger.info(f"   Adjusted total duration: {total_duration:.1f}s (preserving ALL audio)")
                else:
                    duration_scale = max_video_duration / total_duration
                    logger.warning(f"   Video duration ({total_duration:.1f}s) exceeds max ({max_video_duration:.1f}s)")
                    logger.warning(f"   Padding reduction not sufficient. Applying scale factor: {duration_scale:.2f}x")
                    logger.warning(f"   ⚠️  Some audio may be trimmed to fit within limit")
                    scene_durations = [max(min_scene_seconds, d * duration_scale) for d in scene_durations]
                    total_duration = sum(scene_durations)
                    if len(scene_durations) > 1:
                        total_duration -= crossfade_sec * (len(scene_durations) - 1)
                    logger.info(f"   Adjusted total duration: {total_duration:.1f}s")
            
            try:
                # Process each scene
                for idx, img_data in enumerate(images):
                    scene_num = idx + 1
                    scene_key = f"scene_{scene_num}"
                    audio_data = scene_audio.get(scene_key)
                    
                    # Update progress: 5-60% for scene processing
                    progress_percent = 5 + int((idx / total_scenes) * 55)
                    progress_tracker.set_progress(
                        task_id,
                        progress_percent,
                        f"Processing scene {scene_num} of {total_scenes}",
                        scene_num,
                        total_scenes
                    )
                    
                    if not img_data:
                        logger.warning(f"No image data for scene {scene_num}, skipping")
                        continue
                    
                    duration = scene_durations[idx]
                    actual_audio_duration = audio_durations[idx] if idx < len(audio_durations) else 0.0
                    
                    try:
                        # Save image temporarily
                        img_path = os.path.join(temp_dir, f"scene_{scene_num}.jpg")
                        with open(img_path, 'wb') as f:
                            f.write(img_data)
                        
                        # Create image clip
                        if MOVIEPY_VERSION == 2:
                            img_clip = ImageClip(img_path, duration=duration)
                            img_clip = img_clip.resized(resolution)
                            
                            if ken_burns:
                                img_clip = self._apply_ken_burns_v2(
                                    img_clip, duration, scene_num,
                                    kb_zoom_start, kb_zoom_end, kb_pan, resolution
                                )
                            
                            img_clip = img_clip.with_start(current_start)
                            
                            if crossfade_sec > 0 and len(video_clips) > 0:
                                img_clip = img_clip.with_effects([vfx.CrossFadeIn(crossfade_sec)])
                        else:
                            img_clip = mpe.ImageClip(img_path).set_duration(duration)
                            img_clip = img_clip.resize(resolution)
                            img_clip = img_clip.set_start(current_start)
                            
                            if crossfade_sec > 0 and len(video_clips) > 0:
                                img_clip = img_clip.crossfadein(crossfade_sec)
                        
                        video_clips.append(img_clip)
                        
                        # Add audio - trim to scene duration to prevent overlapping
                        if audio_data:
                            try:
                                audio_path = os.path.join(temp_dir, f"scene_{scene_num}.mp3")
                                with open(audio_path, 'wb') as f:
                                    f.write(audio_data)
                                
                                if MOVIEPY_VERSION == 2:
                                    narr = AudioFileClip(audio_path)
                                    original_duration = narr.duration
                                    
                                    next_scene_start = current_start + duration - (crossfade_sec if crossfade_sec > 0 and len(video_clips) > 0 else 0)
                                    audio_max_duration = next_scene_start - current_start
                                    
                                    if narr.duration > audio_max_duration:
                                        narr = narr.with_duration(audio_max_duration)
                                        logger.warning(f"   ⚠️  Trimmed audio for scene {scene_num} from {original_duration:.2f}s to {audio_max_duration:.2f}s")
                                    else:
                                        logger.debug(f"Audio scene {scene_num}: {original_duration:.2f}s fits in {duration:.2f}s")
                                    
                                    effects = []
                                    if adjusted_head_pad > 0 and afx:
                                        effects.append(afx.AudioFadeIn(adjusted_head_pad))
                                    if adjusted_tail_pad > 0 and afx:
                                        effects.append(afx.AudioFadeOut(adjusted_tail_pad))
                                    
                                    if effects:
                                        narr = narr.with_effects(effects)
                                    
                                    narr = narr.with_start(current_start)
                                else:
                                    narr = mpe.AudioFileClip(audio_path)
                                    original_duration = narr.duration
                                    
                                    next_scene_start = current_start + duration - (crossfade_sec if crossfade_sec > 0 and len(video_clips) > 0 else 0)
                                    audio_max_duration = next_scene_start - current_start
                                    
                                    if narr.duration > audio_max_duration:
                                        narr = narr.subclip(0, audio_max_duration)
                                        logger.warning(f"   ⚠️  Trimmed audio for scene {scene_num} from {original_duration:.2f}s to {audio_max_duration:.2f}s")
                                    else:
                                        logger.debug(f"Audio scene {scene_num}: {original_duration:.2f}s fits in {duration:.2f}s")
                                    
                                    narr = narr.audio_fadein(adjusted_head_pad).audio_fadeout(adjusted_tail_pad)
                                    narr = narr.set_start(current_start)
                                
                                audio_tracks.append(narr)
                                logger.debug(f"Added audio scene {scene_num}: {narr.duration:.2f}s")
                            except Exception as e:
                                logger.warning(f"Could not load audio for scene {scene_num}: {e}")
                        
                        timings.append({
                            "scene": scene_num,
                            "start": current_start,
                            "end": current_start + duration,
                            "duration": duration
                        })
                        
                        current_start += duration - (crossfade_sec if crossfade_sec > 0 and len(video_clips) > 1 else 0)
                        
                        # Update progress after scene completion
                        progress_percent = 5 + int(((idx + 1) / total_scenes) * 55)
                        progress_tracker.set_progress(
                            task_id,
                            progress_percent,
                            f"Completed scene {scene_num} of {total_scenes}",
                            scene_num,
                            total_scenes
                        )
                        
                        logger.debug(f"Scene {scene_num} processed ({duration:.1f}s)")
                        
                    except Exception as e:
                        logger.error(f"Error processing scene {scene_num}: {e}")
                        continue
                
                if not video_clips:
                    raise ValueError("❌ No valid clips were created")
                
                # Update progress: 60% - combining clips
                progress_tracker.set_progress(task_id, 60, "Combining video clips...", total_scenes, total_scenes)
                
                # Combine video clips
                logger.debug(f"Combining {len(video_clips)} video clips...")
                if MOVIEPY_VERSION == 2:
                    final_video = CompositeVideoClip(video_clips)
                else:
                    final_video = mpe.CompositeVideoClip(video_clips)
                
                logger.debug(f"Combined {len(video_clips)} video scenes")
                
                # Update progress: 70% - combining audio
                progress_tracker.set_progress(task_id, 70, "Combining audio tracks...", total_scenes, total_scenes)
                
                # Combine audio
                if audio_tracks:
                    logger.debug(f"Processing {len(audio_tracks)} audio tracks...")
                    try:
                        if MOVIEPY_VERSION == 2:
                            base_audio = CompositeAudioClip(audio_tracks)
                            logger.debug(f"Combined audio duration: {base_audio.duration:.2f}s")
                        else:
                            base_audio = mpe.CompositeAudioClip(audio_tracks)
                            logger.debug(f"Combined audio duration: {base_audio.duration:.2f}s")
                        
                        # Add background music if provided
                        if bg_music_data:
                            try:
                                music_path = os.path.join(temp_dir, "bg_music.mp3")
                                with open(music_path, 'wb') as f:
                                    f.write(bg_music_data)
                                
                                if MOVIEPY_VERSION == 2:
                                    music = AudioFileClip(music_path)
                                    music = music.with_volume_scaled(bg_music_volume)
                                    music = music.with_duration(final_video.duration)
                                    final_audio = CompositeAudioClip([base_audio, music])
                                else:
                                    music = mpe.AudioFileClip(music_path).volumex(bg_music_volume)
                                    music = music.set_duration(final_video.duration)
                                    final_audio = mpe.CompositeAudioClip([base_audio, music])
                                
                                logger.debug("Added background music")
                            except Exception as e:
                                logger.warning(f"Could not add background music: {e}")
                                final_audio = base_audio
                        else:
                            final_audio = base_audio
                        
                        # Attach audio to video
                        if MOVIEPY_VERSION == 2:
                            final_video = final_video.with_audio(final_audio)
                        else:
                            final_video = final_video.set_audio(final_audio)
                        
                        logger.debug(f"Audio attached: {final_audio.duration:.2f}s audio, {final_video.duration:.2f}s video")
                    except Exception as e:
                        logger.error(f"Error combining audio: {e}")
                        import traceback
                        logger.error(traceback.format_exc())
                        raise
                else:
                    logger.warning("No audio tracks found, creating silent video")
                
                # Update progress: 80% - rendering video
                progress_tracker.set_progress(task_id, 80, "Rendering final video...", total_scenes, total_scenes)
                
                logger.info("Rendering final video...")
                safe_title = title_sanitized or sanitize_filename(title)
                output_path = os.path.join(temp_dir, f"{safe_title}.mp4")
                
                # Use custom logger that intercepts MoviePy progress internally
                # This avoids repeated backend requests during video rendering
                custom_logger = MoviePyProgressLogger(progress_tracker, task_id, start_percent=80, end_percent=95)
                
                final_video.write_videofile(
                    output_path,
                    fps=fps,
                    codec="libx264",
                    audio_codec="aac",
                    threads=4,
                    preset='medium',
                    temp_audiofile=os.path.join(temp_dir, "temp-audio.m4a"),
                    remove_temp=False,
                    logger=custom_logger  # Use custom logger instead of 'bar'
                )
                
                # Update progress: 95% - finalizing
                progress_tracker.set_progress(task_id, 95, "Finalizing video...", total_scenes, total_scenes)
                
                # Read video file
                with open(output_path, 'rb') as f:
                    video_data = f.read()
                
                # Generate subtitles if requested (best-effort, non-blocking on failure)
                if generate_subtitles:
                    try:
                        # Use provided narrations or try to load from Supabase
                        narrations = subtitle_narrations
                        if not narrations:
                            narrations = self._load_scene_narrations(title_sanitized, len(images))
                        
                        # If narrations is a list, clean each narration text
                        if narrations and isinstance(narrations, list):
                            narrations = [self._clean_narration_for_subtitles(str(n)) for n in narrations]
                        
                        subtitles_text = self._generate_subtitles_text(timings, narrations) if narrations else None
                        if subtitles_text:
                            subtitles_bytes = subtitles_text.encode('utf-8')
                            subtitles_local_path = os.path.join(temp_dir, f"{safe_title}.srt")
                            with open(subtitles_local_path, "w", encoding="utf-8") as srt_file:
                                srt_file.write(subtitles_text)
                            logger.info(f"Generated subtitles for {safe_title}")
                        else:
                            logger.debug("No subtitles generated (missing narrations or timings)")
                    except Exception as e:
                        logger.warning(f"Failed to generate subtitles: {e}")
                        import traceback
                        logger.debug(traceback.format_exc())
                
                # Mark as complete
                progress_tracker.set_progress(task_id, 100, "Video generation complete!", total_scenes, total_scenes)
                
                # Cleanup - Close all clips to prevent daemon thread issues
                logger.info("Cleaning up resources...")
                
                try:
                    if hasattr(final_video, 'close'):
                        final_video.close()
                except Exception as e:
                    logger.debug(f"Error closing final video: {e}")
                
                try:
                    if 'final_audio' in locals() and final_audio and hasattr(final_audio, 'close'):
                        final_audio.close()
                except:
                    pass
                
                try:
                    if 'base_audio' in locals() and base_audio and hasattr(base_audio, 'close'):
                        base_audio.close()
                except:
                    pass
                
                for audio_track in audio_tracks:
                    try:
                        if hasattr(audio_track, 'close'):
                            audio_track.close()
                    except Exception as e:
                        logger.debug(f"Error closing audio track: {e}")
                
                for clip in video_clips:
                    try:
                        if hasattr(clip, 'close'):
                            clip.close()
                    except Exception as e:
                        logger.debug(f"Error closing video clip: {e}")
                
                import time
                time.sleep(0.1)
                
                logger.info(f"Video generation complete: {len(video_data) / (1024*1024):.1f}MB")
                if return_subtitles:
                    return {
                        "video_data": video_data,
                        "timings": timings,
                        "subtitles_bytes": subtitles_bytes,
                        "title_sanitized": safe_title
                    }
                return video_data
                
            except Exception as e:
                # Cleanup on error - close all clips
                logger.error(f"Error building video: {e}")
                
                for audio_track in audio_tracks:
                    try:
                        if hasattr(audio_track, 'close'):
                            audio_track.close()
                    except:
                        pass
                
                for clip in video_clips:
                    try:
                        if hasattr(clip, 'close'):
                            clip.close()
                    except:
                        pass
                
                try:
                    if 'final_video' in locals() and hasattr(final_video, 'close'):
                        final_video.close()
                except:
                    pass
                
                raise Exception(f"❌ Failed to build video: {e}")


# Create service instance
video_service = VideoService()

