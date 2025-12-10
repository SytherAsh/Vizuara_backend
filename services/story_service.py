"""
Story Service
Handles comic storyline and scene prompt generation using Groq
"""

import re
import logging
from typing import List, Dict, Any
from groq import Groq

logger = logging.getLogger("VidyAI_Flask")


class StoryService:
    """Service for story generation using Groq"""
    
    def __init__(self, api_key: str):
        """
        Initialize Story Service
        
        Args:
            api_key: Groq API key
        """
        self.client = Groq(api_key=api_key)
        logger.info("StoryService initialized with Groq client")
    
    def sanitize_filename(self, filename: str) -> str:
        """Sanitize string for filename use"""
        sanitized = re.sub(r'[\\/*?:"<>|]', '_', filename)
        return sanitized[:200]
    
    def generate_comic_storyline(
        self, 
        title: str, 
        content: str, 
        target_length: str = "medium", 
        max_chars: int = 25000,
        tone: str = "casual",
        target_audience: str = "general",
        complexity: str = "moderate",
        focus_style: str = "comprehensive",
        scene_count: int = None,
        educational_level: str = "intermediate",
        visual_style: str = "educational"
    ) -> str:
        """
        Generate a comic storyline from Wikipedia content
        
        Args:
            title: Title of the Wikipedia article
            content: Content of the Wikipedia article
            target_length: Desired length (very short, short, medium, long)
            max_chars: Maximum characters to process
            tone: Story tone (casual, formal, enthusiastic, professional, conversational)
            target_audience: Target audience (kids, students, general, professionals)
            complexity: Content complexity (simple, moderate, detailed)
            focus_style: Focus style (key-points, comprehensive, highlights)
            scene_count: Preferred number of scenes (optional)
            educational_level: Educational level (beginner, intermediate, advanced)
            visual_style: Visual style (educational, entertaining, documentary, animated)
            
        Returns:
            Generated comic storyline
        """
        logger.info(f"Generating comic storyline for: {title} with target length: {target_length}, tone: {tone}, audience: {target_audience}")
        
        # Map target length to word count
        length_map = {
            "very short": 300,
            "short": 500,
            "medium": 1000,
            "long": 2000
        }
        
        word_count = length_map.get(target_length, 1000)
        
        # Map tone to writing style guidance
        tone_guidance = {
            "casual": "Use friendly, conversational language. Write like you're talking to a friend. Use contractions and everyday expressions.",
            "formal": "Use professional, academic language. Maintain a scholarly tone with precise vocabulary and structured sentences.",
            "enthusiastic": "Use energetic, exciting language. Include exclamations and vivid descriptions. Make it feel dynamic and engaging.",
            "professional": "Use polished, business-appropriate language. Balance clarity with sophistication. Maintain credibility and authority.",
            "conversational": "Use natural, flowing language. Write as if speaking directly to the reader. Include rhetorical questions and engaging transitions."
        }
        
        # Map target audience to language complexity
        audience_guidance = {
            "kids": "Use VERY SIMPLE words that children ages 5-12 can understand. Short sentences (5-10 words). Use examples from their world. Avoid abstract concepts.",
            "students": "Use clear, accessible language for ages 13-18. Moderate sentence length. Include relatable examples. Balance simplicity with educational value.",
            "general": "Use accessible language for broad audiences. Clear explanations without being condescending. Balance simplicity with depth.",
            "professionals": "Use sophisticated vocabulary appropriate for educated adults. Can include technical terms with context. More nuanced and detailed."
        }
        
        # Map complexity to detail level
        complexity_guidance = {
            "simple": "Focus on core concepts only. Use straightforward explanations. Avoid technical details or complex relationships. Keep it easy to follow.",
            "moderate": "Include balanced detail. Explain key concepts with some depth. Include important context but avoid overwhelming detail.",
            "detailed": "Include comprehensive information. Provide thorough explanations, context, and relationships. Cover nuances and important details."
        }
        
        # Map focus style to content approach
        focus_guidance = {
            "key-points": "Focus ONLY on the most important points and main events. Skip less critical details. Create a streamlined narrative highlighting essentials.",
            "comprehensive": "Cover the complete story with thorough detail. Include all important aspects, context, and relationships. Provide full narrative coverage.",
            "highlights": "Focus on the most exciting and memorable moments. Emphasize dramatic events and key turning points. Create an engaging highlight reel."
        }
        
        # Map educational level to depth
        education_guidance = {
            "beginner": "Use foundational concepts and basic explanations. Build from the ground up. Assume no prior knowledge. Use analogies and simple examples.",
            "intermediate": "Use moderate depth with some assumed background knowledge. Include important context. Balance accessibility with educational value.",
            "advanced": "Use sophisticated concepts and deeper analysis. Can assume some background knowledge. Include nuanced details and complex relationships."
        }
        
        # Map visual style to narrative approach
        visual_style_guidance = {
            "educational": "Emphasize clarity and learning. Focus on informative content. Use clear explanations and educational structure. Prioritize understanding.",
            "entertaining": "Emphasize engagement and fun. Use exciting language and dramatic moments. Make it enjoyable while still informative. Prioritize engagement.",
            "documentary": "Emphasize factual accuracy and real-world context. Use objective, informative tone. Include historical/social context. Prioritize authenticity.",
            "animated": "Emphasize visual appeal and dynamic storytelling. Use vivid descriptions and energetic language. Make it visually exciting. Prioritize visual impact."
        }
        
        # Truncate content if necessary
        if len(content) > max_chars:
            logger.info(f"Content too long ({len(content)} chars), truncating to {max_chars} chars")
            truncated = content[:max_chars]
            last_paragraph = truncated.rfind('\n\n')
            if last_paragraph > max_chars * 0.8:
                content = content[:last_paragraph] + "\n\n[Content truncated to fit token limits]"
            else:
                content = truncated + "...[Content truncated to fit token limits]"
            logger.info(f"Truncated content to {len(content)} chars")
        
        # Build customization guidance text
        scene_count_note = f" (Target: {scene_count} scenes)" if scene_count else ""
        
        # Create prompt for LLM
        prompt = f"""
        You are creating a detailed, engaging comic book storyline for "{title}" strictly from the provided Wikipedia content.
        
        CUSTOMIZATION PARAMETERS (FOLLOW THESE EXACTLY):
        - Target Audience: {target_audience.upper()} - {audience_guidance.get(target_audience, "Use appropriate language for the target audience.")}
        - Tone: {tone.upper()} - {tone_guidance.get(tone, "Use appropriate tone for the story.")}
        - Complexity Level: {complexity.upper()} - {complexity_guidance.get(complexity, "Use appropriate complexity level.")}
        - Focus Style: {focus_style.upper()} - {focus_guidance.get(focus_style, "Use appropriate focus approach.")}
        - Educational Level: {educational_level.upper()} - {education_guidance.get(educational_level, "Use appropriate educational depth.")}
        - Visual Style: {visual_style.upper()} - {visual_style_guidance.get(visual_style, "Use appropriate visual narrative approach.")}
        - Target Length: ~{word_count} words (±100 words){scene_count_note} - prioritize completeness over strict word count
        
        HARD REQUIREMENTS:
        - 5 acts with clear narrative progression and smooth transitions
        - Chronologically accurate with clear timeline markers
        - Historically/factually accurate; no invented facts or fabricated details
        - Use ONLY details present in the provided source content
        - If any detail is uncertain or missing in the source, omit it rather than inventing
        - Cover the COMPLETE story arc from beginning to end with no gaps
        - Follow the TONE, AUDIENCE, COMPLEXITY, FOCUS, EDUCATION LEVEL, and VISUAL STYLE parameters above
        - BE ENGAGING - make it exciting, use active voice, keep readers interested
        
        FORMAT (FOLLOW EXACTLY):
        # {title}: Comprehensive Comic Storyline
        
        ## Story Overview
        [3-4 sentences providing a compelling summary of the complete narrative arc, including the beginning, major turning points, climax, and resolution. Make it engaging and informative.]
        
        ## Historical/Contextual Background
        [2-3 sentences establishing the time period, setting, and broader context. Help readers understand the world this story takes place in and why it matters.]
        
        ## Main Characters & Key Figures
        [4-8 character entries with 2-3 sentences each. Include:
        - Character name and primary role
        - Key personality traits and motivations
        - Their significance to the overall story
        Make characters feel real and three-dimensional.]
        
        ## Act 1: The Beginning - [Specific Descriptive Title]
        [~{word_count // 5} words covering:
        - Initial situation and setting
        - Introduction of main characters
        - The world before the main events
        - Early signs of change or conflict
        - The inciting incident that sets everything in motion
        Include specific details, dates, locations, and circumstances.]
        
        ## Act 2: Rising Action - [Specific Descriptive Title]
        [~{word_count // 5} words covering:
        - How characters respond to the initial challenge
        - Escalating tensions and growing stakes
        - Early victories or setbacks
        - Character development and relationship dynamics
        - New complications that raise the stakes
        Show clear progression and build momentum.]
        
        ## Act 3: Turning Point - [Specific Descriptive Title]
        [~{word_count // 5} words covering:
        - The critical moment where everything changes
        - Major conflicts reaching their peak
        - Difficult choices and their consequences
        - Shifts in power, understanding, or circumstances
        - The point of no return
        This is the heart of the story - make it powerful.]
        
        ## Act 4: Climax & Resolution - [Specific Descriptive Title]
        [~{word_count // 5} words covering:
        - The final confrontation or ultimate challenge
        - How conflicts are resolved
        - Victories, defeats, sacrifices, or transformations
        - The immediate aftermath of major events
        - Direct consequences of the climax
        Show the emotional and factual resolution.]
        
        ## Act 5: Lasting Impact & Legacy - [Specific Descriptive Title]
        [~{word_count // 5} words covering:
        - Long-term effects and changes
        - How the world/society was transformed
        - The ultimate legacy of events and characters
        - Final reflections on significance
        - Connection to broader history or future events
        Give proper closure while highlighting enduring importance.]
        
        ## Key Themes & Messages
        [3-5 bullet points identifying the major themes, lessons, or important ideas that run through this story. What should audiences take away?]
        
        ## Critical Moments for Visualization
        [8-10 bullet points describing the most visually powerful, emotionally significant, or narratively crucial moments that would make excellent comic scenes. Include:
        - Specific event description
        - Why this moment matters
        - Visual/emotional impact potential
        These will guide scene selection.]
        
        ## Timeline & Chronology
        [Create a clear chronological sequence of 8-12 major events with approximate dates/time periods where available. This ensures the story flows in proper order.]
        
        WRITING GUIDELINES (FOLLOW CUSTOMIZATION PARAMETERS):
        - TONE: {tone_guidance.get(tone, "Use appropriate tone")}
        - AUDIENCE: {audience_guidance.get(target_audience, "Use appropriate language")}
        - COMPLEXITY: {complexity_guidance.get(complexity, "Use appropriate detail level")}
        - FOCUS: {focus_guidance.get(focus_style, "Use appropriate focus approach")}
        - EDUCATION: {education_guidance.get(educational_level, "Use appropriate educational depth")}
        - VISUAL STYLE: {visual_style_guidance.get(visual_style, "Use appropriate visual narrative")}
        - Use specific names, dates, locations, and facts from the source
        - Build clear cause-and-effect relationships between events
        - Show character growth and change over time
        - Create emotional connection while maintaining accuracy
        - Ensure smooth transitions between acts with connecting phrases
        - Make the chronology crystal clear - use time markers like "First...", "Then...", "After that..."
        - Leave no important story elements uncovered (unless focus_style is "key-points" or "highlights")
        - Balance engaging storytelling with factual accuracy
        - Adapt language complexity based on target_audience and educational_level
        
        SOURCE MATERIAL (your only source - use all relevant details):
        {content}
        
        Create a storyline that is comprehensive, engaging, and provides everything needed for detailed scene generation and narration. Cover the entire story from beginning to end with depth and detail.
        """
        
        try:
            # Create dynamic system message based on customization
            system_message = f"""You are an expert storyteller who creates engaging comic book storylines. 
            You adapt your writing style based on customization parameters:
            - Target Audience: {target_audience} - {audience_guidance.get(target_audience, "Use appropriate language")}
            - Tone: {tone} - {tone_guidance.get(tone, "Use appropriate tone")}
            - Complexity: {complexity} - {complexity_guidance.get(complexity, "Use appropriate detail")}
            - Educational Level: {educational_level} - {education_guidance.get(educational_level, "Use appropriate depth")}
            - Visual Style: {visual_style} - {visual_style_guidance.get(visual_style, "Use appropriate approach")}
            
            Your storylines are historically accurate but written in an engaging way that matches the specified parameters. 
            You always follow the customization settings provided and adapt your language, depth, and style accordingly."""
            
            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                model="llama-3.3-70b-versatile",
                temperature=0.4,
                max_tokens=12000,
                top_p=0.9
            )
            
            storyline = response.choices[0].message.content
            logger.info(f"Successfully generated comic storyline for: {title}")
            return storyline
            
        except Exception as e:
            logger.error(f"Failed to generate storyline: {str(e)}")
            raise Exception(f"Error generating storyline: {str(e)}")
    
    def generate_scene_prompts(
        self,
        title: str,
        storyline: str,
        comic_style: str,
        num_scenes: int = 10,
        age_group: str = "general",
        education_level: str = "intermediate",
        negative_concepts: List[str] = None,
        character_sheet: str = "",
        style_sheet: str = "",
        visual_detail: str = "moderate",
        camera_style: str = "varied",
        color_palette: str = "natural",
        scene_pacing: str = "moderate"
    ) -> List[str]:
        """
        Generate scene prompts for comic panels
        
        Args:
            title: Title of the article
            storyline: Generated comic storyline
            comic_style: Selected comic art style
            num_scenes: Number of scene prompts
            age_group: Target age group
            education_level: Education level
            negative_concepts: Concepts to avoid
            character_sheet: Character consistency guide
            style_sheet: Style consistency guide
            
        Returns:
            List of scene prompts
        """
        logger.info(f"Generating {num_scenes} scene prompts for comic in {comic_style} style")
        
        # Style guidance
        style_guidance = {
            "manga": "Use manga-specific visual elements like speed lines, expressive emotions, and distinctive panel layouts. Character eyes should be larger, with detailed hair and simplified facial features. Use black and white with screen tones for shading.",
            "superhero": "Use bold colors, dynamic poses with exaggerated anatomy, dramatic lighting, and action-oriented compositions. Include detailed musculature and costumes with strong outlines and saturated colors.",
            "cartoon": "Use simplified, exaggerated character features with bold outlines. Employ bright colors, expressive faces, and playful physics. Include visual effects like motion lines and impact stars.",
            "noir": "Use high-contrast black and white or muted colors with dramatic shadows. Feature low-key lighting, rain effects, and urban settings. Characters should have realistic proportions with hardboiled expressions.",
            "european": "Use detailed backgrounds with architectural precision and clear line work. Character designs should be semi-realistic with consistent proportions. Panel layouts should be regular and methodical.",
            "indie": "Use unconventional art styles with personal flair. Panel layouts can be experimental and fluid. Line work may be sketchy or deliberately unpolished. Colors can be watercolor-like or limited palette.",
            "retro": "Use halftone dots for shading, slightly faded colors, and classic panel compositions. Character designs should reflect the comics of the 50s-70s with simplified but distinctive features.",
        }.get(comic_style.lower(), f"Incorporate distinctive visual elements of {comic_style} style consistently in all panels.")
        
        # Age guidance
        age_guidance = {
            "kids": "Use simple, clear vocabulary and straightforward concepts. Avoid complex themes, frightening imagery, or adult situations. Characters should be expressive and appealing. Educational content should be presented in an engaging, accessible way.",
            "teens": "Use relatable language and themes important to adolescents. Include more nuanced emotional content and moderate complexity. Educational aspects can challenge readers while remaining accessible.",
            "general": "Balance accessibility with depth. Include some complexity in both themes and visuals while remaining broadly appropriate. Educational content should be informative without being overly technical.",
            "adult": "Include sophisticated themes, complex characterizations, and nuanced storytelling. Educational content can be presented with full complexity and technical detail where appropriate."
        }.get(age_group.lower(), "Create content appropriate for a general audience with balanced accessibility and depth.")
        
        # Education guidance
        education_guidance = {
            "beginner": "Use simple vocabulary, clear explanations, and focus on foundational concepts. Break down complex ideas into easily digestible components with examples.",
            "intermediate": "Use moderate vocabulary and present concepts with appropriate depth for general understanding. Balance educational content with narrative engagement.",
            "advanced": "Use field-specific terminology where appropriate and explore concepts in depth. Present nuanced details and sophisticated analysis of the subject matter."
        }.get(education_level.lower(), "Present educational content with balanced complexity suitable for interested general readers.")
        
        # Visual detail guidance
        visual_detail_guidance = {
            "minimal": "Use simple, clean visual descriptions. Focus on essential elements only. Avoid excessive detail. Keep descriptions concise and straightforward.",
            "moderate": "Use balanced visual descriptions with appropriate detail. Include important elements and context without overwhelming. Maintain clarity while providing sufficient information.",
            "detailed": "Use rich, comprehensive visual descriptions. Include extensive detail about settings, characters, lighting, composition, and atmosphere. Paint a vivid, complete picture."
        }.get(visual_detail.lower(), "Use balanced visual descriptions with appropriate detail.")
        
        # Camera style guidance
        camera_style_guidance = {
            "dynamic": "Use dynamic camera angles: low angles for power, high angles for vulnerability, Dutch angles for tension, close-ups for emotion, wide shots for context. Emphasize action and movement.",
            "cinematic": "Use cinematic camera work: dramatic framing, depth of field, rule of thirds, leading lines. Create movie-like compositions with professional cinematography techniques.",
            "traditional": "Use classic comic panel compositions: straightforward angles, clear staging, traditional layouts. Focus on clarity and readability with standard comic conventions.",
            "varied": "Mix camera angles and compositions throughout scenes. Vary between close-ups, medium shots, wide shots, and different angles to create visual interest and narrative flow."
        }.get(camera_style.lower(), "Use varied camera angles and compositions.")
        
        # Color palette guidance
        color_palette_guidance = {
            "vibrant": "Use bold, saturated colors with high contrast. Employ bright primaries and vivid hues. Create energetic, eye-catching visuals with strong color impact.",
            "muted": "Use soft, desaturated colors with subtle contrast. Employ pastels and earth tones. Create gentle, calming visuals with refined color harmony.",
            "monochrome": "Use black and white or grayscale only. Focus on contrast, shadows, and lighting. Create dramatic, timeless visuals with strong value relationships.",
            "natural": "Use realistic, natural colors matching real-world appearances. Employ authentic color palettes based on actual settings and lighting conditions."
        }.get(color_palette.lower(), "Use natural, realistic colors.")
        
        # Scene pacing guidance
        scene_pacing_guidance = {
            "fast": "Create quick, energetic scene transitions. Focus on key moments and action. Use shorter, more dynamic scene descriptions. Emphasize movement and progression.",
            "moderate": "Create balanced scene pacing with appropriate transitions. Balance action with moments of reflection. Use varied scene lengths and pacing.",
            "slow": "Create deliberate, detailed scene pacing. Allow time for important moments to breathe. Use longer, more contemplative scene descriptions. Emphasize atmosphere and detail."
        }.get(scene_pacing.lower(), "Create balanced scene pacing.")
        
        # Prepare negative concepts text
        negatives_text = ""
        if negative_concepts:
            negatives_text = "\nGLOBAL BANS (strictly avoid): " + ", ".join(negative_concepts)
        
        # Prepare sheets text
        sheets_text = ""
        if style_sheet:
            sheets_text += f"\nSTYLE SHEET (follow consistently): {style_sheet}"
        if character_sheet:
            sheets_text += f"\nCHARACTER SHEET (identities, outfits, colors): {character_sheet}"
        
        prompt = f"""
        Based on the storyline for "{title}", create EXACTLY {num_scenes} exciting scene descriptions for comic panels. Tell the story in order, making each scene flow naturally into the next. Make it ENGAGING and VISUAL!

        CORE REQUIREMENTS FOR EVERY SCENE:
        1. Tell the story in ORDER - each scene follows the previous one naturally
        2. Visual description ONLY (NO text, captions, speech bubbles, or words on images)
        3. Word count: {"40-60 words" if visual_detail == "minimal" else "80-120 words" if visual_detail == "moderate" else "120-180 words"} describing: what we see, who is there, what they're doing, how they look, the mood, lighting, colors, composition
        4. Keep characters and places looking the same across all scenes
        5. Follow the {comic_style} comic style with {visual_detail} visual detail
        6. Only use facts from the storyline - don't make up new things
        7. Absolutely NO text, letters, logos, watermarks, or words in images
        8. Each scene must move the story forward and connect to the next scene with {scene_pacing} pacing
        9. Use SIMPLE words students can understand - avoid complex vocabulary
        10. Apply {color_palette} color palette and {camera_style} camera style consistently

        SCENE DISTRIBUTION STRATEGY ({scene_pacing.upper()} PACING):
        - Follow {scene_pacing_guidance} for scene transitions and pacing
        - Scenes 1-2: Opening/Setup (introduce setting, main characters, initial situation)
        - Scenes 3-4: Early Development (first challenges, rising action begins)
        - Scenes 5-6: Mid-Story Turning Points (escalating conflict, crucial developments)
        - Scenes 7-8: Climax & Resolution (peak drama, major events, decisive moments)
        - Scenes 9-{num_scenes}: Aftermath & Legacy (resolution, lasting impact, conclusion)
        
        Ensure complete story coverage from first moment to final impact with {scene_pacing} pacing.

        HOW TO MAKE SCENES ENGAGING ({visual_detail.upper()} DETAIL, {camera_style.upper()} CAMERA, {color_palette.upper()} COLORS):
        - Visual Detail: {visual_detail_guidance}
        - Camera Work: {camera_style_guidance}
        - Color Approach: {color_palette_guidance}
        - Make each scene unique and exciting - something memorable
        - Use camera angles to show emotion: close-ups for feelings, wide shots to show the big picture
        - Show what characters are feeling through their faces and body language
        - Include details that show where and when this is happening
        - Make sure scenes connect smoothly - if someone is running in one scene, show where they're going in the next
        - Focus on the most exciting or important moments
        - Use light and shadows to create mood (bright for happy, dark for scary/serious)
        - Apply {color_palette} color palette consistently throughout all scenes

        STYLE PARAMETERS (FOLLOW THESE EXACTLY):
        - Comic Style: {comic_style} — {style_guidance}
        - Age Group: {age_group} — {age_guidance}
        - Education Level: {education_level} — {education_guidance}
        - Visual Detail: {visual_detail.upper()} — {visual_detail_guidance}
        - Camera Style: {camera_style.upper()} — {camera_style_guidance}
        - Color Palette: {color_palette.upper()} — {color_palette_guidance}
        - Scene Pacing: {scene_pacing.upper()} — {scene_pacing_guidance}
        {negatives_text}
        {sheets_text}

        COMPLETE STORYLINE (your authoritative source for all scene content):
        {storyline}

        OUTPUT FORMAT (FOLLOW EXACTLY):
        Scene [number]: [Specific, descriptive scene title that indicates chronological position]
        Narrative Context: [1-2 sentences explaining where this fits in the story flow and what narrative purpose it serves]
        Visual Description: [80-120 words of detailed, visual-only description including:
        - Setting and environment details
        - Character positioning, actions, and expressions
        - Camera angle and composition choices
        - Lighting, atmosphere, and mood
        - Key visual elements that convey the story moment
        - Color palette suggestions if appropriate
        - Emotional tone through visual elements]
        Style Notes: {comic_style} with [specific stylistic elements to emphasize for this particular scene]
        Continuity: [Brief note on how this connects to previous/next scene]

        CRITICAL GUIDELINES:
        - Cover the ENTIRE story arc across all {num_scenes} scenes with no gaps
        - Maintain perfect chronological sequence - never jump backward in time without reason
        - Ensure smooth visual transitions between consecutive scenes
        - Balance establishing shots, action scenes, and emotional moments
        - Make key story moments visually powerful and clear
        - Every scene must feel essential to telling the complete story
        - Create strong visual variety while maintaining consistency

        Produce EXACTLY {num_scenes} scenes that tell the complete story of "{title}" from beginning to end with perfect narrative flow and visual storytelling excellence.
        """
        
        try:
            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are an expert comic artist who creates exciting, easy-to-understand scene descriptions for STUDENTS. You use SIMPLE, CLEAR words that anyone can understand. You describe what people see in each panel using everyday language, making sure the story is exciting and easy to follow. You never use complex vocabulary - you explain things like you're talking to a friend. Your scenes flow naturally from one to the next, and you always make sure NO text appears in the images."},
                    {"role": "user", "content": prompt}
                ],
                model="llama-3.3-70b-versatile",
                temperature=0.4,
                max_tokens=12000,
                top_p=0.9
            )
            
            scenes_text = response.choices[0].message.content
            
            # Process text to extract scene prompts
            scene_prompts = []
            scene_pattern = re.compile(r'Scene \d+:.*?(?=Scene \d+:|$)', re.DOTALL)
            matches = scene_pattern.findall(scenes_text)
            
            for match in matches:
                # Remove dialog lines
                cleaned = re.sub(r'^\s*Dialog\s*:\s*.*$', '', match, flags=re.IGNORECASE | re.MULTILINE)
                cleaned = re.sub(r'^\s*(Narrator|Caption|Voiceover|Voice-over|Announcer)\s*:\s*.*$', '', cleaned, flags=re.IGNORECASE | re.MULTILINE)
                scene_prompts.append(cleaned.strip())
            
            # Pad if needed
            while len(scene_prompts) < num_scenes:
                scene_num = len(scene_prompts) + 1
                scene_prompts.append(f"""Scene {scene_num}: Additional scene from {title}
                Visual: A character from the story stands in a relevant setting from {title}, looking thoughtful. No on-screen text, no captions, no speech.
                Style: {comic_style} style with appropriate elements for {age_group} audience.""")
            
            # Truncate if too many
            scene_prompts = scene_prompts[:num_scenes]
            
            # Validate prompts
            validated_prompts = []
            for i, prompt in enumerate(scene_prompts):
                # Strip dialog
                prompt = re.sub(r'^\s*Dialog\s*:\s*.*$', '', prompt, flags=re.IGNORECASE | re.MULTILINE)
                prompt = re.sub(r'^\s*(Narrator|Caption|Voiceover|Voice-over|Announcer)\s*:\s*.*$', '', prompt, flags=re.IGNORECASE | re.MULTILINE)
                prompt = re.sub(r'^\s*"[^"]+"\s*$', '', prompt, flags=re.MULTILINE)
                validated_prompts.append(prompt)
            
            logger.info(f"Successfully generated {len(validated_prompts)} scene prompts")
            return validated_prompts
            
        except Exception as e:
            logger.error(f"Failed to generate scene prompts: {str(e)}")
            raise Exception(f"Error generating scene prompts: {str(e)}")

