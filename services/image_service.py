"""
Image Service
Handles comic image generation using Google Gemini 2.5 Flash Image
"""

import os
import re
import time
import logging
from typing import List, Optional
from google import genai
from PIL import Image
from io import BytesIO
import numpy as np

logger = logging.getLogger("VidyAI_Flask")


class ImageService:
    """Service for comic image generation using Gemini"""
    
    def __init__(self, api_key: str):
        """
        Initialize Image Service
        
        Args:
            api_key: Google Gemini API key
        """
        self.api_key = api_key
        self.client = None
        logger.info("ImageService initializing...")
        self._initialize_client()
    
    def _initialize_client(self) -> bool:
        """Initialize Gemini client"""
        try:
            if not self.api_key:
                logger.error("No Gemini API key provided")
                return False
            
            self.client = genai.Client(api_key=self.api_key)
            logger.info("Gemini client initialized successfully")
            
            try:
                _ = self.client.models.generate_content(
                    model="gemini-2.5-flash-image",
                    contents="test"
                )
                logger.info("Gemini API key validated successfully")
                return True
            except Exception as test_error:
                logger.warning(f"API key test failed: {test_error}")
                logger.warning("Proceeding anyway (model may still work)")
                return True
                
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
            return False
    
    def _clean_scene_prompt(self, scene_prompt: str) -> tuple:
        """Extract visual description from scene prompt"""
        cleaned = re.sub(
            r"^\s*(Narrator|Caption|Voiceover|Voice-over|Announcer)\s*:\s*.*$",
            "",
            scene_prompt,
            flags=re.IGNORECASE | re.MULTILINE,
        )
        cleaned = re.sub(r"^\s*Dialog\s*:\s*.*$", "", cleaned, flags=re.IGNORECASE | re.MULTILINE)
        
        visual_match = re.search(
            r'Visual[:\s]+(.+?)(?=\n(?:Dialog|Style|Narrative|Continuity):|$)',
            cleaned,
            re.DOTALL | re.IGNORECASE
        )
        visual_description = (
            visual_match.group(1).strip() if visual_match else cleaned.strip()
        )
        
        style_match = re.search(
            r'Style[:\s]+(.+?)(?=\n|$)',
            scene_prompt,
            re.DOTALL | re.IGNORECASE
        )
        style_info = style_match.group(1).strip() if style_match else ""
        
        visual_description = re.sub(
            r'^(Scene \d+:|Visual:|Description:)',
            '',
            visual_description,
            flags=re.IGNORECASE
        ).strip()
        
        return visual_description, style_info
    
    def _enhance_prompt_for_gemini(
        self,
        scene_prompt: str,
        style_sheet: str = "",
        character_sheet: str = "",
        negative_concepts: Optional[List[str]] = None,
        aspect_ratio: str = "16:9"
    ) -> str:
        """Enhance prompt for Gemini"""
        visual_description, style_info = self._clean_scene_prompt(scene_prompt)
        
        parts = [
            f"Create a single comic book panel with this exact visual content:\n{visual_description}"
        ]
        
        if style_info:
            parts.append(f"\nArt style: {style_info}")
        if style_sheet:
            parts.append(f"\nStyle consistency requirements: {style_sheet}")
        if character_sheet:
            parts.append(f"\nCharacter appearance consistency: {character_sheet}")
        
        parts.append(f"""
Technical requirements:
- Aspect ratio: {aspect_ratio} (landscape)
- High quality comic book art
- Cinematic lighting, balanced framing
- Vibrant but not oversaturated colors
- NO text, captions, or speech bubbles
- NO watermarks, logos, or UI elements
- Character consistency across panels
        """)
        
        if negative_concepts:
            parts.append(f"\nAvoid: {', '.join(negative_concepts)}")
        
        parts.append("""
Quality standards:
- Professional comic book art
- Clear expressions and clean background
- Consistent art style
- Absolutely NO text or writing
        """)
        
        return "\n".join(parts)
    
    def generate_comic_image(
        self,
        scene_prompt: str,
        scene_num: int,
        attempt: int = 1,
        max_retries: int = 3,
        style_sheet: str = "",
        character_sheet: str = "",
        negative_concepts: Optional[List[str]] = None,
        aspect_ratio: str = "16:9"
    ) -> Optional[bytes]:
        """
        Generate a single comic panel
        
        Args:
            scene_prompt: Scene description
            scene_num: Scene number
            attempt: Current attempt number
            max_retries: Maximum retry attempts
            style_sheet: Style consistency guide
            character_sheet: Character consistency guide
            negative_concepts: Concepts to avoid
            aspect_ratio: Image aspect ratio
            
        Returns:
            Image data as bytes or None
        """
        if not self.client:
            logger.error(f"Gemini client not initialized for scene {scene_num}")
            return None
        
        try:
            prompt = self._enhance_prompt_for_gemini(
                scene_prompt,
                style_sheet,
                character_sheet,
                negative_concepts,
                aspect_ratio
            )
            
            logger.info(f"Generating image for scene {scene_num} (Attempt {attempt})")
            response = self.client.models.generate_content(
                model="gemini-2.5-flash-image",
                contents=prompt
            )
            
            image_found = False
            image_data = None
            
            for candidate in getattr(response, "candidates", []):
                content = getattr(candidate, "content", None)
                if not content:
                    continue
                for part in getattr(content, "parts", []):
                    inline_data = getattr(part, "inline_data", None)
                    if inline_data and inline_data.mime_type.startswith("image/"):
                        try:
                            img_data = BytesIO(inline_data.data)
                            image = Image.open(img_data)
                            
                            # Convert to RGB if needed
                            if image.mode in ("RGBA", "LA", "P"):
                                rgb = Image.new("RGB", image.size, (255, 255, 255))
                                if image.mode == "P":
                                    image = image.convert("RGBA")
                                rgb.paste(image, mask=image.split()[-1] if image.mode in ("RGBA", "LA") else None)
                                image = rgb
                            
                            # Convert to bytes
                            output = BytesIO()
                            image.save(output, "JPEG", quality=95)
                            image_data = output.getvalue()
                            
                            logger.info(f"Generated image for scene {scene_num}")
                            image_found = True
                            break
                        except Exception as err:
                            logger.error(f"Error processing image scene {scene_num}: {err}")
                if image_found:
                    break
            
            if not image_found:
                logger.warning(f"No image data for scene {scene_num}")
                if attempt < max_retries:
                    wait_time = 2 ** attempt
                    logger.info(f"Retrying in {wait_time}s (Attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    return self.generate_comic_image(
                        scene_prompt, scene_num,
                        attempt + 1, max_retries,
                        style_sheet, character_sheet, negative_concepts, aspect_ratio
                    )
                return None
            
            return image_data
            
        except Exception as e:
            msg = str(e)
            logger.error(f"Error generating image scene {scene_num}: {msg}")
            
            if "RESOURCE_EXHAUSTED" in msg or "QUOTA" in msg:
                return None
            
            if attempt < max_retries:
                wait_time = 2 ** attempt
                logger.info(f"Retrying in {wait_time}s (Attempt {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
                return self.generate_comic_image(
                    scene_prompt, scene_num,
                    attempt + 1, max_retries,
                    style_sheet, character_sheet, negative_concepts, aspect_ratio
                )
            
            return None
    
    def generate_comic_strip(
        self,
        scene_prompts: List[str],
        comic_title: str,
        style_sheet: str = "",
        character_sheet: str = "",
        negative_concepts: Optional[List[str]] = None,
        aspect_ratio: str = "16:9"
    ) -> List[Optional[bytes]]:
        """
        Generate all comic panels
        
        Args:
            scene_prompts: List of scene descriptions
            comic_title: Title of the comic
            style_sheet: Style consistency guide
            character_sheet: Character consistency guide
            negative_concepts: Concepts to avoid
            aspect_ratio: Image aspect ratio
            
        Returns:
            List of image data (bytes) for each scene
        """
        logger.info(f"Generating {len(scene_prompts)} scenes for {comic_title}")
        
        if not self.client:
            logger.error("Gemini client not initialized.")
            return []
        
        images = []
        for i, prompt in enumerate(scene_prompts):
            scene_num = i + 1
            
            logger.info(f"Processing scene {scene_num}/{len(scene_prompts)}")
            image_data = self.generate_comic_image(
                scene_prompt=prompt,
                scene_num=scene_num,
                style_sheet=style_sheet,
                character_sheet=character_sheet,
                negative_concepts=negative_concepts,
                aspect_ratio=aspect_ratio
            )
            
            images.append(image_data)
            
            if scene_num < len(scene_prompts):
                time.sleep(1)
        
        logger.info(f"Comic strip done: {len([img for img in images if img])} images generated.")
        return images

