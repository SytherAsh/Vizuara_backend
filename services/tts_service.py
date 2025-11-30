"""
TTS (Text-to-Speech) Service
Handles audio generation from narration text using Google TTS
"""

import os
import logging
from typing import Dict, Any, Optional
from gtts import gTTS
from io import BytesIO

logger = logging.getLogger("VidyAI_Flask")

# Check for pydub availability
try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    logger.warning("pydub not installed. Audio speed adjustment will not be available.")
    PYDUB_AVAILABLE = False


class TTSService:
    """Service for text-to-speech conversion"""
    
    def __init__(self):
        """Initialize TTS Service"""
        logger.info("TTSService initialized")
    
    def adjust_audio_speed(self, audio_data: bytes, speed: float = 1.25) -> bytes:
        """
        Adjust audio playback speed
        
        Args:
            audio_data: Input audio as bytes
            speed: Speed multiplier (1.25 = 25% faster)
            
        Returns:
            Speed-adjusted audio as bytes
        """
        if not PYDUB_AVAILABLE:
            logger.warning("pydub not available. Returning original audio without speed adjustment.")
            return audio_data
        
        try:
            # Load audio
            audio = AudioSegment.from_mp3(BytesIO(audio_data))
            
            # Calculate new frame rate
            new_frame_rate = int(audio.frame_rate * speed)
            
            # Apply speed adjustment
            adjusted_audio = audio._spawn(audio.raw_data, overrides={
                "frame_rate": new_frame_rate
            })
            
            # Convert back to standard frame rate
            adjusted_audio = adjusted_audio.set_frame_rate(audio.frame_rate)
            
            # Export to bytes
            output = BytesIO()
            adjusted_audio.export(output, format="mp3", bitrate="192k")
            
            logger.info(f"Adjusted audio speed to {speed}x")
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Error adjusting audio speed: {str(e)}")
            return audio_data
    
    def synthesize_to_mp3(
        self,
        text: str,
        lang: str = "en",
        tld: str = "com",
        slow: bool = False,
        speed: float = 1.0
    ) -> bytes:
        """
        Synthesize text to MP3 audio
        
        Args:
            text: Text to convert to speech
            lang: Language code (e.g., 'en', 'hi', 'es')
            tld: Top-level domain for accent ('com'=US, 'co.uk'=UK, 'co.in'=India)
            slow: Whether to use slower speech rate
            speed: Speed multiplier (1.0 = normal, 1.25 = 25% faster)
            
        Returns:
            Audio data as bytes
        """
        try:
            # Generate TTS
            tts = gTTS(text=text, lang=lang, tld=tld, slow=slow)
            
            # Save to BytesIO
            audio_buffer = BytesIO()
            tts.write_to_fp(audio_buffer)
            audio_buffer.seek(0)
            audio_data = audio_buffer.read()
            
            logger.info("Generated TTS audio")
            
            # Apply speed adjustment if needed
            if speed != 1.0 and abs(speed - 1.0) > 0.01:
                audio_data = self.adjust_audio_speed(audio_data, speed)
            
            return audio_data
            
        except Exception as e:
            logger.error(f"Error generating TTS: {str(e)}")
            raise Exception(f"Error generating TTS: {str(e)}")
    
    def estimate_tts_duration_seconds(self, text: str, speed: float = 1.0) -> float:
        """
        Estimate audio duration from text
        
        Args:
            text: Text to estimate duration for
            speed: Speed multiplier
            
        Returns:
            Estimated duration in seconds
        """
        words = [w for w in text.strip().split() if w]
        base_duration = len(words) / 2.5  # ~2.5 words per second
        adjusted_duration = base_duration / speed if speed > 0 else base_duration
        return max(0.0, adjusted_duration)
    
    def generate_scene_audios(
        self,
        narrations: Dict[str, Any],
        lang: str = "en",
        tld: str = "com",
        slow: bool = False,
        speed: float = 1.25
    ) -> Dict[str, bytes]:
        """
        Generate audio for all scenes
        
        Args:
            narrations: Dictionary with narration data
            lang: Language code
            tld: Top-level domain for accent
            slow: Whether to use slower speech
            speed: Speed multiplier
            
        Returns:
            Dictionary mapping scene keys to audio bytes
        """
        logger.info(f"Generating audio for {len(narrations.get('narrations', {}))} scenes at {speed}x speed")
        
        scene_to_audio = {}
        narrs = narrations.get("narrations", {})
        
        for scene_key, scene_data in narrs.items():
            scene_num = scene_data.get("scene_number")
            text = scene_data.get("narration", "").strip()
            
            if not text:
                logger.warning(f"No narration text for scene {scene_num}")
                continue
            
            try:
                audio_data = self.synthesize_to_mp3(text, lang, tld, slow, speed)
                scene_to_audio[scene_key] = audio_data
                
                duration = self.estimate_tts_duration_seconds(text, speed)
                logger.info(f"Generated audio for scene {scene_num} (~{duration:.1f}s at {speed}x speed)")
                
            except Exception as e:
                logger.error(f"✗ Error generating audio for scene {scene_num}: {str(e)}")
                continue
        
        logger.info(f"Successfully generated {len(scene_to_audio)}/{len(narrs)} audio files")
        return scene_to_audio


# Create service instance
tts_service = TTSService()

