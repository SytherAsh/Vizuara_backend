"""
Video Service
Handles video compilation from images and audio using MoviePy
"""

import os
import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from PIL import Image
from io import BytesIO

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


class VideoService:
    """Service for video generation"""
    
    def __init__(self):
        """Initialize Video Service"""
        if not MOVIEPY_AVAILABLE:
            logger.error("MoviePy is not available. Video generation will not work.")
        else:
            logger.info(f"VideoService initialized with MoviePy {MOVIEPY_VERSION}.x")
    
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
            import tempfile
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
        max_video_duration: Optional[float] = None
    ) -> bytes:
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
            
        Returns:
            Video data as bytes
        """
        if not MOVIEPY_AVAILABLE:
            raise ImportError("❌ MoviePy is required for video generation")
        
        if not images:
            raise ValueError("❌ No images provided")
        
        logger.info("Building video with MoviePy...")
        logger.info(f"   Processing {len(images)} scenes...")
        if max_video_duration:
            logger.info(f"   Maximum video duration: {max_video_duration:.1f}s")
        
        timings = []
        current_start = 0.0
        video_clips = []
        audio_tracks = []
        
        # Create temporary directory for working files (use local data folder)
        import tempfile
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(base_dir, 'data', 'temp')
        os.makedirs(data_dir, exist_ok=True)
        temp_dir = tempfile.mkdtemp(dir=data_dir, prefix='video_')
        logger.info(f"Using temp directory: {temp_dir}")
        
        # First pass: Get actual audio durations and calculate scene durations
        # This ensures we use ALL audio without trimming
        audio_durations = []
        scene_durations = []
        
        # Get actual audio durations (no need to save files, use existing method)
        for idx, img_data in enumerate(images):
            scene_num = idx + 1
            scene_key = f"scene_{scene_num}"
            audio_data = scene_audio.get(scene_key)
            
            if audio_data:
                # Get actual audio duration
                audio_duration = self._get_audio_duration_seconds(audio_data)
                audio_durations.append(audio_duration)
                
                # Scene duration = audio duration + padding
                # This ensures ALL audio fits within the scene
                scene_duration = max(min_scene_seconds, audio_duration + head_pad + tail_pad)
                scene_durations.append(scene_duration)
            else:
                # No audio for this scene
                audio_durations.append(0.0)
                scene_durations.append(min_scene_seconds)
        
        # Calculate total duration (accounting for crossfades)
        total_duration = sum(scene_durations)
        if len(scene_durations) > 1:
            total_duration -= crossfade_sec * (len(scene_durations) - 1)
        
        # If max_video_duration is set, reduce padding instead of scaling durations
        # This preserves ALL audio content
        adjusted_head_pad = head_pad
        adjusted_tail_pad = tail_pad
        
        if max_video_duration and total_duration > max_video_duration:
            # Calculate how much we need to reduce
            excess_duration = total_duration - max_video_duration
            total_padding = (head_pad + tail_pad) * len([a for a in audio_durations if a > 0])
            
            if total_padding > 0:
                # Reduce padding proportionally
                padding_reduction = min(excess_duration / total_padding, 0.8)  # Max 80% reduction
                adjusted_head_pad = head_pad * (1 - padding_reduction)
                adjusted_tail_pad = tail_pad * (1 - padding_reduction)
                
                # Recalculate scene durations with reduced padding
                scene_durations = []
                for audio_dur in audio_durations:
                    if audio_dur > 0:
                        scene_duration = max(min_scene_seconds, audio_dur + adjusted_head_pad + adjusted_tail_pad)
                    else:
                        scene_duration = min_scene_seconds
                    scene_durations.append(scene_duration)
                
                # Recalculate total
                total_duration = sum(scene_durations)
                if len(scene_durations) > 1:
                    total_duration -= crossfade_sec * (len(scene_durations) - 1)
                
                logger.info(f"   Video duration ({total_duration:.1f}s) exceeds max ({max_video_duration:.1f}s)")
                logger.info(f"   Reducing padding from {head_pad + tail_pad:.2f}s to {adjusted_head_pad + adjusted_tail_pad:.2f}s per scene")
                logger.info(f"   Adjusted total duration: {total_duration:.1f}s (preserving ALL audio)")
            else:
                # If padding reduction isn't enough, we'll need to trim (last resort)
                duration_scale = max_video_duration / total_duration
                logger.warning(f"   Video duration ({total_duration:.1f}s) exceeds max ({max_video_duration:.1f}s)")
                logger.warning(f"   Padding reduction not sufficient. Applying scale factor: {duration_scale:.2f}x")
                logger.warning(f"   ⚠️  Some audio may be trimmed to fit within limit")
                scene_durations = [d * duration_scale for d in scene_durations]
                scene_durations = [max(min_scene_seconds, d) for d in scene_durations]
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
                
                if not img_data:
                    logger.warning(f"No image data for scene {scene_num}, skipping")
                    continue
                
                # Use pre-calculated duration (based on actual audio duration + padding)
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
                                
                                # Calculate when next scene starts (accounting for crossfade)
                                next_scene_start = current_start + duration - (crossfade_sec if crossfade_sec > 0 and len(video_clips) > 0 else 0)
                                # Audio should end before next scene starts to prevent overlap
                                audio_max_duration = next_scene_start - current_start
                                
                                # Scene duration is already calculated to fit audio + padding
                                # But double-check: if audio is longer than scene, trim it (shouldn't happen with new logic)
                                if narr.duration > audio_max_duration:
                                    narr = narr.with_duration(audio_max_duration)
                                    logger.warning(f"   ⚠️  Trimmed audio for scene {scene_num} from {original_duration:.2f}s to {audio_max_duration:.2f}s")
                                else:
                                    logger.info(f"   ✅ Audio for scene {scene_num}: {original_duration:.2f}s fits perfectly in scene ({duration:.2f}s)")
                                
                                # Apply fade in/out for smooth transitions using adjusted padding
                                effects = []
                                if adjusted_head_pad > 0 and afx:
                                    effects.append(afx.AudioFadeIn(adjusted_head_pad))
                                if adjusted_tail_pad > 0 and afx:
                                    effects.append(afx.AudioFadeOut(adjusted_tail_pad))
                                
                                if effects:
                                    narr = narr.with_effects(effects)
                                
                                # Set start time at scene start
                                narr = narr.with_start(current_start)
                            else:
                                narr = mpe.AudioFileClip(audio_path)
                                original_duration = narr.duration
                                
                                # Calculate when next scene starts (accounting for crossfade)
                                next_scene_start = current_start + duration - (crossfade_sec if crossfade_sec > 0 and len(video_clips) > 0 else 0)
                                # Audio should end before next scene starts to prevent overlap
                                audio_max_duration = next_scene_start - current_start
                                
                                # Scene duration is already calculated to fit audio + padding
                                # But double-check: if audio is longer than scene, trim it (shouldn't happen with new logic)
                                if narr.duration > audio_max_duration:
                                    narr = narr.subclip(0, audio_max_duration)
                                    logger.warning(f"   ⚠️  Trimmed audio for scene {scene_num} from {original_duration:.2f}s to {audio_max_duration:.2f}s")
                                else:
                                    logger.info(f"   ✅ Audio for scene {scene_num}: {original_duration:.2f}s fits perfectly in scene ({duration:.2f}s)")
                                
                                # Apply fade in/out using adjusted padding
                                narr = narr.audio_fadein(adjusted_head_pad).audio_fadeout(adjusted_tail_pad)
                                # Set start time at scene start
                                narr = narr.set_start(current_start)
                            
                            audio_tracks.append(narr)
                            logger.info(f"   Added audio for scene {scene_num} (duration: {narr.duration:.2f}s, start: {current_start:.2f}s, end: {current_start + narr.duration:.2f}s)")
                        except Exception as e:
                            logger.warning(f"Could not load audio for scene {scene_num}: {e}")
                    
                    timings.append({
                        "scene": scene_num,
                        "start": current_start,
                        "end": current_start + duration,
                        "duration": duration
                    })
                    
                    current_start += duration - (crossfade_sec if crossfade_sec > 0 and len(video_clips) > 1 else 0)
                    
                    logger.info(f"Scene {scene_num} processed ({duration:.1f}s)")
                    
                except Exception as e:
                    logger.error(f"Error processing scene {scene_num}: {e}")
                    continue
            
            if not video_clips:
                raise ValueError("❌ No valid clips were created")
            
            # Combine video clips
            logger.info(f"   Combining {len(video_clips)} video clips...")
            if MOVIEPY_VERSION == 2:
                final_video = CompositeVideoClip(video_clips)
            else:
                final_video = mpe.CompositeVideoClip(video_clips)
            
            logger.info(f"Combined {len(video_clips)} video scenes")
            
            # Combine audio
            if audio_tracks:
                logger.info(f"   Processing {len(audio_tracks)} audio tracks...")
                for i, track in enumerate(audio_tracks, 1):
                    start = track.start if hasattr(track, 'start') else 0
                    dur = track.duration if hasattr(track, 'duration') else 0
                    end = start + dur if dur else 0
                    logger.info(f"   Track {i}: start={start:.2f}s, duration={dur:.2f}s, end={end:.2f}s")
                
                try:
                    if MOVIEPY_VERSION == 2:
                        base_audio = CompositeAudioClip(audio_tracks)
                        logger.info(f"   Combined audio duration: {base_audio.duration}")
                    else:
                        base_audio = mpe.CompositeAudioClip(audio_tracks)
                        logger.info(f"   Combined audio duration: {base_audio.duration}")
                    
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
                            
                            logger.info("Added background music")
                        except Exception as e:
                            logger.warning(f"Could not add background music: {e}")
                            final_audio = base_audio
                    else:
                        final_audio = base_audio
                    
                    # Attach audio to video (matching video_editor.py - no duration adjustment needed)
                    # CompositeAudioClip handles timing automatically based on with_start() calls
                    if MOVIEPY_VERSION == 2:
                        final_video = final_video.with_audio(final_audio)
                    else:
                        final_video = final_video.set_audio(final_audio)
                    
                    logger.info(f"✅ Audio attached to video (audio: {final_audio.duration:.2f}s, video: {final_video.duration:.2f}s)")
                except Exception as e:
                    logger.error(f"Error combining audio: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
                    raise
            else:
                logger.warning("No audio tracks found, creating silent video")
            
            # Write video to bytes
            logger.info(f"Writing final video...")
            safe_title = title.replace('/', '_').replace('\\', '_')
            output_path = os.path.join(temp_dir, f"{safe_title}.mp4")
            
            # Also save to data/videos folder for easy access
            videos_dir = os.path.join(base_dir, 'data', 'videos')
            os.makedirs(videos_dir, exist_ok=True)
            saved_video_path = os.path.join(videos_dir, f"{safe_title}.mp4")
            
            final_video.write_videofile(
                output_path,
                fps=fps,
                codec="libx264",
                audio_codec="aac",
                threads=4,
                preset='medium',
                temp_audiofile=os.path.join(temp_dir, "temp-audio.m4a"),
                remove_temp=False,  # Keep temp files for debugging
                logger='bar'
            )
            
            # Copy to videos folder for easy access
            import shutil
            try:
                shutil.copy2(output_path, saved_video_path)
                logger.info(f"✅ Video saved to: {saved_video_path}")
            except Exception as e:
                logger.warning(f"Could not copy video to videos folder: {e}")
            
            # Read video file
            with open(output_path, 'rb') as f:
                video_data = f.read()
            
            # Cleanup - Close all clips to prevent daemon thread issues
            logger.info("Cleaning up resources...")
            
            # Close final video and audio first (this will close nested clips)
            try:
                if hasattr(final_video, 'close'):
                    final_video.close()
            except Exception as e:
                logger.debug(f"Error closing final video: {e}")
            
            # Close final_audio if it exists separately (before video closes it)
            try:
                if 'final_audio' in locals() and final_audio and hasattr(final_audio, 'close'):
                    final_audio.close()
            except:
                pass
            
            # Close base_audio if it exists separately
            try:
                if 'base_audio' in locals() and base_audio and hasattr(base_audio, 'close'):
                    base_audio.close()
            except:
                pass
            
            # Close all individual audio tracks (after composite is closed)
            for audio_track in audio_tracks:
                try:
                    if hasattr(audio_track, 'close'):
                        audio_track.close()
                except Exception as e:
                    logger.debug(f"Error closing audio track: {e}")
            
            # Close all video clips (after composite is closed)
            for clip in video_clips:
                try:
                    if hasattr(clip, 'close'):
                        clip.close()
                except Exception as e:
                    logger.debug(f"Error closing video clip: {e}")
            
            # Small delay to let threads finish
            import time
            time.sleep(0.1)
            
            # Cleanup temp directory (keep for debugging, but can be removed)
            # import shutil
            # try:
            #     shutil.rmtree(temp_dir)
            # except:
            #     pass
            
            logger.info("Video generation complete")
            return video_data
            
        except Exception as e:
            # Cleanup on error - close all clips
            logger.error(f"Error building video: {e}")
            
            # Close all audio tracks
            for audio_track in audio_tracks:
                try:
                    if hasattr(audio_track, 'close'):
                        audio_track.close()
                except:
                    pass
            
            # Close all video clips
            for clip in video_clips:
                try:
                    if hasattr(clip, 'close'):
                        clip.close()
                except:
                    pass
            
            # Close final video if it exists
            try:
                if 'final_video' in locals() and hasattr(final_video, 'close'):
                    final_video.close()
            except:
                pass
            
            # Cleanup temp directory
            # import shutil
            # try:
            #     shutil.rmtree(temp_dir)
            # except:
            #     pass
            
            raise Exception(f"❌ Failed to build video: {e}")


# Create service instance
video_service = VideoService()

