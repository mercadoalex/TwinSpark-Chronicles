import logging
import asyncio
from typing import List, Dict, Optional, AsyncGenerator
from dataclasses import dataclass
from enum import Enum
from ai.twin_intelligence import TwinIntelligenceEngine

logger = logging.getLogger(__name__)

# Try to import Google Generative AI
try:
    import google.generativeai as genai
    from google.generativeai.types import GenerationConfig
    GENAI_AVAILABLE = True
except ImportError:
    logger.warning("Google Generative AI not available")
    GENAI_AVAILABLE = False
    genai = None


class MediaType(Enum):
    """Types of media the Creative Director can generate"""
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    INTERACTIVE = "interactive"


@dataclass
class CreativeAsset:
    """A single creative asset in the output stream"""
    media_type: MediaType
    content: str  # Text, URL, or base64 data
    timestamp: float
    metadata: Dict = None
    duration: Optional[float] = None  # For audio/video


class CreativeDirectorAgent:
    """
    An AI agent that thinks like a creative director AND understands sibling dynamics.
    """
    
    def __init__(self, api_key: str, twin_engine: Optional[TwinIntelligenceEngine] = None):
        self.api_key = api_key
        self.model = None
        self.conversation_history = []
        self.twin_engine = twin_engine  # Connection to sibling relationship model
        
        if GENAI_AVAILABLE and api_key:
            try:
                genai.configure(api_key=api_key)
                
                self.model = genai.GenerativeModel(
                    model_name='gemini-2.0-flash-exp',
                    generation_config=GenerationConfig(
                        temperature=0.9,
                        top_p=0.95,
                        top_k=40,
                        max_output_tokens=8192,
                    ),
                    system_instruction="""You are a Creative Director AND Relationship Coach for siblings.

You create stories that:
1. **Require Real Cooperation**: Puzzles they can only solve together
2. **Build Empathy**: Moments where they feel each other's emotions
3. **Teach Teamwork**: Success comes from working as a unit
4. **Balance Challenge**: Not too easy (boring) or too hard (frustrating)

When designing interactions, consider:
- Can they do this alone? If yes, make it require BOTH of them
- Are they emotionally connected right now? Strengthen that bond
- Is one child struggling? Create a moment for the sibling to help
- Have they been cooperative? Reward their teamwork with story progress"""
                )
                
                self.chat = self.model.start_chat(history=[])
                logger.info("✅ Creative Director with Twin Intelligence initialized")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Creative Director: {e}")
                self.model = None
        else:
            logger.warning("⚠️ Creative Director running in MOCK mode")
    
    async def generate_story_beat(
        self,
        child1_name: str,
        child1_personality: str,
        child1_spirit: str,
        child1_toy: str,
        child2_name: str,
        child2_personality: str,
        child2_spirit: str,
        child2_toy: str,
        previous_choice: Optional[str] = None,
        emotional_state: str = "wonder"
    ) -> AsyncGenerator[CreativeAsset, None]:
        """
        Generate a complete story beat as an interleaved stream of media assets.
        
        This method yields CreativeAssets in real-time as they're generated:
        1. Opening narration text
        2. Image prompt for scene visualization
        3. Character-specific perspective text
        4. Audio cue descriptions
        5. Interactive choice prompts
        """
        
        if not self.model:
            # Fallback to mock generation
            async for asset in self._generate_mock_stream(
                child1_name, child1_spirit, child1_toy,
                child2_name, child2_spirit, child2_toy
            ):
                yield asset
            return
        
        # Build the creative brief for Gemini
        prompt = self._build_creative_prompt(
            child1_name, child1_personality, child1_spirit, child1_toy,
            child2_name, child2_personality, child2_spirit, child2_toy,
            previous_choice, emotional_state
        )
        
        try:
            # Generate with streaming for real-time delivery
            response = await asyncio.to_thread(
                self.chat.send_message,
                prompt,
                stream=False  # We'll parse and stream ourselves
            )
            
            # Parse the response and yield structured assets
            async for asset in self._parse_gemini_response(response):
                yield asset
                
        except Exception as e:
            logger.error(f"❌ Creative Director generation failed: {e}", exc_info=True)
            # Fallback to mock
            async for asset in self._generate_mock_stream(
                child1_name, child1_spirit, child1_toy,
                child2_name, child2_spirit, child2_toy
            ):
                yield asset
    
    async def generate_story_beat_with_dynamics(
        self,
        child1_name: str,
        child1_personality: str,
        child1_spirit: str,
        child1_toy: str,
        child1_emotion: str,
        child2_name: str,
        child2_personality: str,
        child2_spirit: str,
        child2_toy: str,
        child2_emotion: str,
        previous_choice: Optional[str] = None,
        story_context: str = "beginning of adventure"
    ) -> AsyncGenerator[CreativeAsset, None]:
        """Generate story beat WITH sibling dynamics analysis."""
        
        logger.info(f"🎬 Generating story beat for {child1_name} & {child2_name}")
        logger.info(f"   Context: {story_context}")
        logger.info(f"   Emotions: {child1_emotion} / {child2_emotion}")
        
        # First, analyze sibling dynamics
        if self.twin_engine:
            logger.info("🧠 Analyzing sibling dynamics...")
            try:
                dynamics = await self.twin_engine.analyze_sibling_dynamics(
                    child1_name=child1_name,
                    child1_action=previous_choice,
                    child1_emotion=child1_emotion,
                    child2_name=child2_name,
                    child2_action=None,
                    child2_emotion=child2_emotion,
                    story_context=story_context
                )
                logger.info(f"✅ Dynamics analyzed: {dynamics.get('cooperation_required')}")
            except Exception as e:
                logger.error(f"❌ Dynamics analysis failed: {e}")
                dynamics = {"cooperation_required": "REQUIRED", "next_challenge_type": "SYNCHRONIZED"}
        else:
            logger.warning("⚠️ No twin engine, using default dynamics")
            dynamics = {"cooperation_required": "REQUIRED", "next_challenge_type": "SYNCHRONIZED"}
        
        # Generate story
        if not self.model:
            logger.info("📝 Using mock stream (no Gemini model)")
            async for asset in self._generate_mock_stream_with_dynamics(
                child1_name, child1_spirit, child1_toy,
                child2_name, child2_spirit, child2_toy,
                dynamics
            ):
                logger.info(f"   → Mock asset: {asset.media_type.value}")
                yield asset
            return
        
        logger.info("🤖 Generating with Gemini AI...")
        
        # Build prompt
        prompt = self._build_dynamics_aware_prompt(
            child1_name, child1_personality, child1_spirit, child1_toy,
            child2_name, child2_personality, child2_spirit, child2_toy,
            previous_choice, dynamics
        )
        
        logger.info(f"📝 Prompt length: {len(prompt)} chars")
        
        try:
            response = await asyncio.to_thread(
                self.chat.send_message,
                prompt
            )
            
            logger.info(f"✅ Gemini response received: {len(response.text)} chars")
            
            async for asset in self._parse_gemini_response(response):
                if asset.metadata:
                    asset.metadata["cooperation_required"] = dynamics.get("cooperation_required")
                    asset.metadata["teachable_moment"] = dynamics.get("teachable_moment")
                logger.info(f"   → Parsed asset: {asset.media_type.value}")
                yield asset
                
        except Exception as e:
            logger.error(f"❌ Gemini generation failed: {e}", exc_info=True)
            logger.info("   Falling back to mock stream")
            async for asset in self._generate_mock_stream_with_dynamics(
                child1_name, child1_spirit, child1_toy,
                child2_name, child2_spirit, child2_toy,
                dynamics
            ):
                logger.info(f"   → Fallback asset: {asset.media_type.value}")
                yield asset
    
    def _build_creative_prompt(
        self,
        child1_name: str,
        child1_personality: str,
        child1_spirit: str,
        child1_toy: str,
        child2_name: str,
        child2_personality: str,
        child2_spirit: str,
        child2_toy: str,
        previous_choice: Optional[str],
        emotional_state: str
    ) -> str:
        """Build a creative brief for the AI to follow"""
        
        return f"""You are a master storyteller and creative director crafting an interactive adventure for two siblings.

**CHARACTER PROFILES:**
- {child1_name}: {child1_personality}, spirit animal is {child1_spirit}, carries {child1_toy}
- {child2_name}: {child2_personality}, spirit animal is {child2_spirit}, carries {child2_toy}

**CREATIVE BRIEF:**
Generate the next story beat with the following structure:

1. **NARRATION** (2-3 sentences): Main story text that sets the scene
   - Use rich, sensory language
   - Target emotion: {emotional_state}
   - {"Continue from their choice: " + previous_choice if previous_choice else "This is the opening scene"}

2. **IMAGE_PROMPT**: A detailed prompt for generating a scene illustration
   - Style: "Pixar-style 3D animation, cinematic lighting, warm colors"
   - Include both children, their spirit animals, and key objects

3. **CHILD1_PERSPECTIVE** (1-2 sentences): What {child1_name} experiences
   - First-person perspective
   - Reference their {child1_spirit} spirit and {child1_toy}

4. **CHILD2_PERSPECTIVE** (1-2 sentences): What {child2_name} experiences
   - First-person perspective  
   - Reference their {child2_spirit} spirit and {child2_toy}

5. **AUDIO_CUES** (list): Background sounds and music
   - Example: ["forest-ambiance", "magical-chimes", "gentle-wind"]

6. **CHOICES** (3 options): What can the children do next?
   - Choice A: Action for {child1_name}
   - Choice B: Action for {child2_name}
   - Choice C: Collaborative action (both children)

Format your response using clear section headers like:
---NARRATION---
---IMAGE_PROMPT---
---CHILD1_PERSPECTIVE---
etc.

Make it magical, age-appropriate (6-8 years), and emphasize cooperation between siblings!"""
    
    def _build_dynamics_aware_prompt(
        self,
        child1_name: str, child1_personality: str, child1_spirit: str, child1_toy: str,
        child2_name: str, child2_personality: str, child2_spirit: str, child2_toy: str,
        previous_choice: Optional[str],
        dynamics: Dict
    ) -> str:
        """Build prompt that incorporates sibling dynamics"""
        
        cooperation_guidance = {
            "REQUIRED": f"Create a challenge that {child1_name} and {child2_name} MUST solve together. Neither can succeed alone.",
            "OPTIONAL": f"Give them a choice: work together for a bonus, or proceed independently.",
            "INDEPENDENT": f"Let each child have their own moment to shine."
        }[dynamics.get("cooperation_required", "REQUIRED")]
        
        challenge_type = dynamics.get("next_challenge_type", "SYNCHRONIZED")
        challenge_guidance = {
            "SYNCHRONIZED": f"They must perform the EXACT SAME ACTION at the same time (e.g., both touch a magic crystal, both say a word together)",
            "COMPLEMENTARY": f"Each has a DIFFERENT role: one holds, one opens; one distracts, one sneaks; one is brave, one is wise",
            "EMOTIONAL_SUPPORT": f"One child is struggling emotionally - the other must comfort or encourage them",
            "INDEPENDENT_THEN_SHARE": f"They explore different paths, then reunite to share what they learned"
        }[challenge_type]
        
        return f"""Create the next story beat for {child1_name} and {child2_name}.

**SIBLING RELATIONSHIP GUIDANCE:**
{cooperation_guidance}
{challenge_guidance}

**TEACHABLE MOMENT:**
{dynamics.get('lesson', 'They need each other to succeed')}

**CHARACTER PROFILES:**
- {child1_name}: {child1_personality}, {child1_spirit} spirit, carries {child1_toy}
- {child2_name}: {child2_personality}, {child2_spirit} spirit, carries {child2_toy}

**STORY CONTINUATION:**
{f"Previous choice: {previous_choice}" if previous_choice else "Opening scene"}

Generate with this structure:
---NARRATION--- (emphasize they need EACH OTHER)
---IMAGE_PROMPT---
---CHILD1_PERSPECTIVE--- (show how they need their sibling)
---CHILD2_PERSPECTIVE--- (show how they need their sibling)
---AUDIO_CUES---
---CHOICES--- (design choices that require cooperation)

Make the cooperation FEEL REAL - they truly cannot succeed without each other!"""
    
    async def _parse_gemini_response(self, response) -> AsyncGenerator[CreativeAsset, None]:
        """Parse Gemini's response and yield structured creative assets"""
        
        text = response.text
        current_time = asyncio.get_event_loop().time()
        
        # Split response into sections
        sections = {}
        current_section = None
        current_content = []
        
        for line in text.split('\n'):
            if line.startswith('---') and line.endswith('---'):
                # Save previous section
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                
                # Start new section
                current_section = line.strip('-')
                current_content = []
            else:
                current_content.append(line)
        
        # Save last section
        if current_section:
            sections[current_section] = '\n'.join(current_content).strip()
        
        # Yield assets in narrative order
        
        # 1. Main narration
        if 'NARRATION' in sections:
            yield CreativeAsset(
                media_type=MediaType.TEXT,
                content=sections['NARRATION'],
                timestamp=current_time,
                metadata={"type": "narration"}
            )
            await asyncio.sleep(0.5)  # Pacing
        
        # 2. Image prompt (will be used to generate visual)
        if 'IMAGE_PROMPT' in sections:
            yield CreativeAsset(
                media_type=MediaType.IMAGE,
                content=sections['IMAGE_PROMPT'],
                timestamp=current_time + 0.5,
                metadata={"type": "scene_image", "prompt": sections['IMAGE_PROMPT']}
            )
            await asyncio.sleep(0.5)
        
        # 3. Child 1's perspective
        if 'CHILD1_PERSPECTIVE' in sections:
            yield CreativeAsset(
                media_type=MediaType.TEXT,
                content=sections['CHILD1_PERSPECTIVE'],
                timestamp=current_time + 1.0,
                metadata={"type": "child1_perspective"}
            )
            await asyncio.sleep(0.5)
        
        # 4. Child 2's perspective
        if 'CHILD2_PERSPECTIVE' in sections:
            yield CreativeAsset(
                media_type=MediaType.TEXT,
                content=sections['CHILD2_PERSPECTIVE'],
                timestamp=current_time + 1.5,
                metadata={"type": "child2_perspective"}
            )
            await asyncio.sleep(0.5)
        
        # 5. Audio cues
        if 'AUDIO_CUES' in sections:
            yield CreativeAsset(
                media_type=MediaType.AUDIO,
                content=sections['AUDIO_CUES'],
                timestamp=current_time + 2.0,
                metadata={"type": "audio_cues"}
            )
        
        # 6. Interactive choices
        if 'CHOICES' in sections:
            yield CreativeAsset(
                media_type=MediaType.INTERACTIVE,
                content=sections['CHOICES'],
                timestamp=current_time + 2.5,
                metadata={"type": "choices"}
            )
    
    async def _generate_mock_stream(
        self,
        child1_name: str,
        child1_spirit: str,
        child1_toy: str,
        child2_name: str,
        child2_spirit: str,
        child2_toy: str
    ) -> AsyncGenerator[CreativeAsset, None]:
        """Fallback mock stream for when API is unavailable"""
        
        current_time = asyncio.get_event_loop().time()
        
        # Narration
        yield CreativeAsset(
            media_type=MediaType.TEXT,
            content=f"Welcome to the magical realm! {child1_name} and {child2_name} stand at the edge of an enchanted forest...",
            timestamp=current_time,
            metadata={"type": "narration"}
        )
        await asyncio.sleep(0.5)
        
        # Image
        yield CreativeAsset(
            media_type=MediaType.IMAGE,
            content=f"Enchanted forest with {child1_name} ({child1_spirit}) and {child2_name} ({child2_spirit}), magical glow, Pixar style",
            timestamp=current_time + 0.5,
            metadata={"type": "scene_image"}
        )
        await asyncio.sleep(0.5)
        
        # Child 1 perspective
        yield CreativeAsset(
            media_type=MediaType.TEXT,
            content=f"Your {child1_spirit} spirit tingles! You grip {child1_toy} tightly...",
            timestamp=current_time + 1.0,
            metadata={"type": "child1_perspective"}
        )
        await asyncio.sleep(0.5)
        
        # Child 2 perspective
        yield CreativeAsset(
            media_type=MediaType.TEXT,
            content=f"Your {child2_spirit} senses alert! {child2_toy} glows in your hands...",
            timestamp=current_time + 1.5,
            metadata={"type": "child2_perspective"}
        )
        await asyncio.sleep(0.5)
        
        # Audio
        yield CreativeAsset(
            media_type=MediaType.AUDIO,
            content='["forest-ambiance", "magical-shimmer"]',
            timestamp=current_time + 2.0,
            metadata={"type": "audio_cues"}
        )
        
        # Choices
        yield CreativeAsset(
            media_type=MediaType.INTERACTIVE,
            content="A: Explore the forest\nB: Study the glow\nC: Hold hands and approach together",
            timestamp=current_time + 2.5,
            metadata={"type": "choices"}
        )
    
    async def _generate_mock_stream_with_dynamics(
        self,
        child1_name: str, child1_spirit: str, child1_toy: str,
        child2_name: str, child2_spirit: str, child2_toy: str,
        dynamics: Dict
    ) -> AsyncGenerator[CreativeAsset, None]:
        """Mock stream that incorporates dynamics"""
        
        current_time = asyncio.get_event_loop().time()
        
        # Narration emphasizing cooperation
        yield CreativeAsset(
            media_type=MediaType.TEXT,
            content=f"""A massive crystal door blocks your path! 
            
{child1_name} notices ancient writing: "Two hearts, one spirit."
{child2_name} sees two glowing handprints on the door.

You realize: you BOTH must place your hands on it AT THE SAME TIME!""",
            timestamp=current_time,
            metadata={"type": "narration", "requires_cooperation": True}
        )
        await asyncio.sleep(0.5)
        
        # Continue with rest of stream...
        yield CreativeAsset(
            media_type=MediaType.IMAGE,
            content=f"Magical crystal door with two handprints, {child1_name} and {child2_name} looking at each other, Pixar style",
            timestamp=current_time + 0.5,
            metadata={"type": "scene_image"}
        )
        await asyncio.sleep(0.5)
        
        yield CreativeAsset(
            media_type=MediaType.TEXT,
            content=f"You look at {child2_name}. Your {child1_spirit} spirit tells you: together, you can do this!",
            timestamp=current_time + 1.0,
            metadata={"type": "child1_perspective"}
        )
        await asyncio.sleep(0.5)
        
        yield CreativeAsset(
            media_type=MediaType.TEXT,
            content=f"You meet {child1_name}'s eyes. Your {child2_spirit} senses say: you need each other!",
            timestamp=current_time + 1.5,
            metadata={"type": "child2_perspective"}
        )
        await asyncio.sleep(0.5)
        
        yield CreativeAsset(
            media_type=MediaType.INTERACTIVE,
            content="SYNCHRONIZED: Both place hands on door\nWAIT: One waits for the other to be ready\nCOMBINE ITEMS: Use both your special items together",
            timestamp=current_time + 2.5,
            metadata={"type": "choices", "requires_synchronization": True}
        )
    
    async def generate_image_from_prompt(self, prompt: str) -> Optional[str]:
        """Use Gemini's imagen generation (if available) to create images"""
        # This would integrate with Google's Imagen API
        # For now, return the prompt for external image generation
        return prompt
    
    def update_emotional_context(self, child_id: str, emotion: str, intensity: float):
        """Update the creative director's understanding of children's emotional state"""
        logger.info(f"📊 Emotional update: {child_id} feeling {emotion} (intensity: {intensity})")
        # This helps the AI adapt the story tone in real-time

    def generate_story_beat(self, scene_description: str, child1_state: dict, child2_state: dict) -> List[CreativeAsset]:
        """Generate a complete story beat with dual perspectives"""
        # ...existing code...
        
        # Generate interactive choices (ASEGÚRATE QUE SEA ARRAY)
        choices_prompt = f"""Based on this scene, provide 3 exciting choices for what the children could do next.
        
Scene: {scene_description}

Return ONLY 3 choices, one per line, WITHOUT numbers or bullets.
Each choice should be:
- Age-appropriate (4-8 years)
- Exciting and magical
- Something both children can do together
- About 6-10 words long

Example format:
Explore the mysterious glowing cave together
Climb the ancient tree to see farther
Follow the sparkling river downstream
"""
        
        try:
            if self.genai_available:
                response = self.model.generate_content(choices_prompt)
                choices_text = response.text.strip()
                
                # Parse into array (split by newlines, filter empty)
                choices = [
                    line.strip() 
                    for line in choices_text.split('\n') 
                    if line.strip() and not line.strip().startswith(('1.', '2.', '3.', '-', '*'))
                ]
                
                # Ensure we have exactly 3 choices
                if len(choices) < 3:
                    choices = [
                        "Explore the magical place together",
                        "Ask their spirit animals for help",
                        "Use their special toys creatively"
                    ]
                choices = choices[:3]  # Take only first 3
                
                logger.info(f"✅ Generated {len(choices)} choices: {choices}")
                
            else:
                choices = [
                    "Explore the magical place together",
                    "Ask their spirit animals for help", 
                    "Use their special toys creatively"
                ]
        except Exception as e:
            logger.error(f"❌ Error generating choices: {e}")
            choices = [
                "Continue the adventure bravely",
                "Look for clues around them",
                "Work together to solve the mystery"
            ]
        
        assets.append(CreativeAsset(
            media_type=MediaType.INTERACTIVE,
            content=choices,  # ← ARRAY, no string
            metadata={"type": "choices", "count": len(choices)}
        ))
        
        return assets