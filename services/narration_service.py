"""
Narration Service
Handles scene narration generation using Groq
"""

import logging
from typing import Dict, Any
from groq import Groq

logger = logging.getLogger("VidyAI_Flask")


class NarrationService:
    """Service for narration generation using Groq"""
    
    def __init__(self, api_key: str):
        """
        Initialize Narration Service
        
        Args:
            api_key: Groq API key
        """
        self.client = Groq(api_key=api_key)
        logger.info("NarrationService initialized with Groq client")
    
    def generate_scene_narration(
        self,
        title: str,
        scene_prompt: str,
        scene_number: int,
        storyline: str = "",
        narration_style: str = "dramatic",
        voice_tone: str = "engaging",
        target_seconds: int = 20,
        min_words: int = 40,
        max_words: int = 70,
        narration_length: str = "medium",
        emotion_level: str = "moderate",
        pace_variation: str = "varied",
        pause_style: str = "natural",
        pronunciation_style: str = "clear"
    ) -> str:
        """
        Generate narration for a specific scene
        
        Args:
            title: Story title
            scene_prompt: Scene description
            scene_number: Scene number
            storyline: Complete storyline for context
            narration_style: Style (dramatic, educational, storytelling, documentary)
            voice_tone: Tone (engaging, serious, playful, informative)
            target_seconds: Target duration in seconds
            min_words: Minimum word count
            max_words: Maximum word count
            
        Returns:
            Generated narration text
        """
        logger.info(f"Generating narration for scene {scene_number} of '{title}'")
        
        # Style guidance
        style_guidance = {
            "dramatic": "Tell the story in an exciting way that makes students feel like they're watching a movie. Use simple but powerful words that create emotion. Make them feel what's happening - the tension, the excitement, the joy or sadness.",
            "educational": "Explain what's happening in a clear, easy way that helps students learn. Use simple words to explain why things matter and what they mean. Make learning fun and interesting, not boring.",
            "storytelling": "Tell it like you're sharing an exciting story with friends. Use simple words, short sentences, and make students care about what happens to the characters. Keep them wanting to know 'what happens next?'",
            "documentary": "Explain the facts clearly using simple language. Help students understand what really happened and why it's important. Be informative but not boring - make history come alive with clear, interesting explanations.",
            "casual": "Use a friendly, conversational tone. Write like you're talking to a friend. Keep it relaxed and approachable.",
            "formal": "Use professional, polished language while remaining clear. Maintain a scholarly but accessible tone.",
            "inspiring": "Use uplifting, motivational language. Create a sense of hope and possibility. Make it feel empowering."
        }.get(narration_style.lower(), "Use simple, clear, and engaging language to describe what's happening.")
        
        # Voice tone guidance
        tone_guidance = {
            "engaging": "Sound excited and energetic! Make students want to listen. Use a friendly, enthusiastic voice like you're telling them something really cool. Keep the energy up!",
            "serious": "Use a calm, respectful voice that shows this is important. Don't be boring, but show that what you're saying matters. Be thoughtful and clear.",
            "playful": "Keep it light and fun! Use a friendly, warm voice that makes learning enjoyable. Smile while you talk - students should feel like learning is fun, not a chore.",
            "informative": "Be clear and helpful, like a good teacher. Explain things simply so everyone understands. Be friendly but focused on helping students learn.",
            "calm": "Use a peaceful, soothing voice. Create a sense of tranquility and ease.",
            "enthusiastic": "Be passionate and animated! Show genuine excitement and energy.",
            "professional": "Use a polished, authoritative voice. Sound credible and knowledgeable."
        }.get(voice_tone.lower(), "Use a clear, friendly tone that students will enjoy listening to.")
        
        # Narration length guidance
        length_guidance = {
            "short": "Keep it very concise - 15-25 words. Get straight to the point. Use only essential information.",
            "medium": "Use balanced length - 40-70 words. Include key details while staying focused.",
            "long": "Provide comprehensive detail - 80-120 words. Include context, explanations, and rich descriptions."
        }.get(narration_length.lower(), "Use balanced length with appropriate detail.")
        
        # Emotion level guidance
        emotion_guidance = {
            "subtle": "Express emotions gently and subtly. Use restrained emotional language. Keep feelings understated.",
            "moderate": "Express emotions in a balanced way. Show feelings clearly but not overly dramatic.",
            "expressive": "Express emotions strongly and vividly. Use powerful emotional language. Make feelings come alive."
        }.get(emotion_level.lower(), "Express emotions in a balanced way.")
        
        # Pace variation guidance
        pace_guidance = {
            "consistent": "Maintain a steady, consistent pace throughout. Keep rhythm uniform.",
            "varied": "Vary the pace naturally - speed up for action, slow down for important moments. Create natural rhythm.",
            "dynamic": "Use dramatic pace changes - fast for excitement, slow for emphasis. Create strong contrast."
        }.get(pace_variation.lower(), "Vary the pace naturally.")
        
        # Pause style guidance
        pause_guidance = {
            "minimal": "Use minimal pauses. Keep transitions quick and smooth. Maintain momentum.",
            "natural": "Use natural pauses at appropriate moments. Allow for breathing and emphasis. Create natural flow.",
            "dramatic": "Use strategic, dramatic pauses for emphasis. Create tension and anticipation. Make pauses meaningful."
        }.get(pause_style.lower(), "Use natural pauses at appropriate moments.")
        
        # Pronunciation style guidance
        pronunciation_guidance = {
            "standard": "Use natural, standard pronunciation. Speak normally and naturally.",
            "clear": "Enunciate clearly and distinctly. Make sure every word is easily understood. Speak with clarity.",
            "precise": "Use very precise, formal pronunciation. Enunciate every syllable carefully. Speak with precision."
        }.get(pronunciation_style.lower(), "Enunciate clearly and distinctly.")
        
        # Calculate word range based on narration_length if not explicitly set
        if narration_length == "short":
            lo = min(min_words, 15)
            hi = max(max_words, 25)
        elif narration_length == "long":
            lo = max(min_words, 80)
            hi = max(max_words, 120)
        else:  # medium
            if target_seconds and target_seconds > 0:
                actual_audio_seconds = target_seconds / 1.25
                approx_words = int(actual_audio_seconds * 2.5)
                lo = max(min_words, approx_words - 10)
                hi = max(max_words, approx_words + 10)
            else:
                lo = min_words
                hi = max_words
        
        prompt = f"""
        You are creating an engaging, easy-to-understand voice-over narration for scene {scene_number} of "{title}". This will be heard by STUDENTS, so use SIMPLE, CLEAR language that everyone can understand. Make it exciting but brief!
        
        CORE REQUIREMENTS:
        - Length: {lo}–{hi} words (short but powerful for {target_seconds} seconds at 1.25x speed)
        - Structure: 2-4 SHORT, SIMPLE sentences that flow naturally
        - Use SIMPLE WORDS - avoid complex vocabulary (e.g., say "brave" not "valiant", "happy" not "jubilant")
        - Content: Explain what's happening, why it matters, and how people feel
        - Pacing: Mix short and medium sentences to keep it interesting
        - Use ONLY facts from the storyline and scene - don't make things up
        - If you're not sure about something, leave it out
        - Think: "Would a 12-year-old understand every word?" If not, simplify it!
        
        NARRATION STYLE GUIDANCE:
        Style: {narration_style.upper()}
        {style_guidance}
        
        VOICE TONE GUIDANCE:
        Tone: {voice_tone.upper()}
        {tone_guidance}
        
        NARRATION LENGTH: {narration_length.upper()}
        {length_guidance}
        
        EMOTION LEVEL: {emotion_level.upper()}
        {emotion_guidance}
        
        PACE VARIATION: {pace_variation.upper()}
        {pace_guidance}
        
        PAUSE STYLE: {pause_style.upper()}
        {pause_guidance}
        
        PRONUNCIATION STYLE: {pronunciation_style.upper()}
        {pronunciation_guidance}
        
        WHAT TO INCLUDE (in simple language):
        - Where & When: Where is this happening? What time is it? What's the mood?
        - What's Happening: What are people doing? What do they look like? How do they feel?
        - Why It Matters: Why is this moment important? What does it mean for the story?
        - The Stakes: What could go wrong? What are people trying to achieve?
        - The Flow: How does this connect to what happened before and what comes next?
        - Make It Real: Help students imagine they're there - what would they see and feel?
        
        COMPLETE STORYLINE (your authoritative source - use this for context and accuracy):
        {storyline}
        
        CURRENT SCENE DETAILS (visual context for this specific moment):
        {scene_prompt}
        
        IMPORTANT GUIDELINES FOR STUDENTS:
        - Write like you're telling an exciting story to a friend - keep it natural and engaging
        - Use SIMPLE WORDS that students understand - no fancy vocabulary
        - Use SHORT SENTENCES that are easy to follow
        - Make every word count - be clear and interesting, not wordy
        - Help students feel connected to the story and care about what happens
        - Use present tense to make it feel like it's happening now (e.g., "Rama fights" not "Rama fought")
        - Don't just describe what students can see - explain WHY it matters
        - Connect smoothly to help the story flow from scene to scene
        - Build excitement that makes students want to see what happens next
        
        Generate an engaging narration of {lo}–{hi} words using SIMPLE, STUDENT-FRIENDLY language that brings this scene to life. Output ONLY the narration text with no extra words, labels, or formatting.
        """
        
        try:
            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are an expert storyteller who creates engaging narrations for STUDENTS using SIMPLE, CLEAR language. You avoid complex words and write like you're explaining something exciting to a friend. You use short sentences, everyday vocabulary, and make sure everything is easy to understand. You make facts interesting and help students care about the story. You always think: 'Would a student understand every single word I'm using?' If not, you choose a simpler word. Your narrations are accurate, engaging, and perfect for young learners."},
                    {"role": "user", "content": prompt}
                ],
                model="llama-3.3-70b-versatile",
                temperature=0.4,
                max_tokens=2000,
                top_p=0.9
            )
            
            narration = response.choices[0].message.content.strip()
            logger.info(f"Successfully generated narration for scene {scene_number}")
            return narration
            
        except Exception as e:
            logger.error(f"Failed to generate narration for scene {scene_number}: {str(e)}")
            raise Exception(f"Error generating narration: {str(e)}")
    
    def generate_all_scene_narrations(
        self,
        title: str,
        scene_prompts: list,
        storyline: str = "",
        narration_style: str = "dramatic",
        voice_tone: str = "engaging",
        narration_length: str = "medium",
        target_duration: int = 20,
        min_words: int = 40,
        max_words: int = 70,
        emotion_level: str = "moderate",
        pace_variation: str = "varied",
        pause_style: str = "natural",
        pronunciation_style: str = "clear"
    ) -> Dict[str, Any]:
        """
        Generate narrations for all scenes
        
        Args:
            title: Story title
            scene_prompts: List of scene descriptions
            storyline: Complete storyline
            narration_style: Narration style
            voice_tone: Voice tone
            narration_length: Overall length preference (short, medium, long)
            target_duration: Target duration in seconds
            min_words: Minimum word count
            max_words: Maximum word count
            emotion_level: Emotion expression level (subtle, moderate, expressive)
            pace_variation: Pace variation style (consistent, varied, dynamic)
            pause_style: Pause style (minimal, natural, dramatic)
            pronunciation_style: Pronunciation clarity (standard, clear, precise)
            
        Returns:
            Dictionary with all narrations
        """
        logger.info(f"Generating narrations for all {len(scene_prompts)} scenes of '{title}' with style={narration_style}, tone={voice_tone}, length={narration_length}")
        
        narrations = {}
        for i, scene_prompt in enumerate(scene_prompts, 1):
            narration = self.generate_scene_narration(
                title=title,
                scene_prompt=scene_prompt,
                scene_number=i,
                storyline=storyline,
                narration_style=narration_style,
                voice_tone=voice_tone,
                target_seconds=target_duration,
                min_words=min_words,
                max_words=max_words,
                narration_length=narration_length,
                emotion_level=emotion_level,
                pace_variation=pace_variation,
                pause_style=pause_style,
                pronunciation_style=pronunciation_style
            )
            narrations[f"scene_{i}"] = {
                "scene_number": i,
                "narration": narration,
                "scene_prompt": scene_prompt
            }
        
        result = {
            "title": title,
            "narration_style": narration_style,
            "voice_tone": voice_tone,
            "total_scenes": len(scene_prompts),
            "narrations": narrations
        }
        
        logger.info(f"Successfully generated {len(scene_prompts)} narrations for '{title}'")
        return result

