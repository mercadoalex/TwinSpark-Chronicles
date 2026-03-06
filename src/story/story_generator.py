"""
TwinSpark Chronicles - Story Generation Engine

Uses Google's Gemini API to generate dynamic, adaptive stories
based on the Twin Intelligence Engine's directives.
"""

import logging
import json
import random
import sys
import os
from typing import Dict, List, Optional

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings
from models import StoryTheme, ChildProfile, StoryBeat, Choice

logger = logging.getLogger(__name__)

# Try to import Google Generative AI
try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    logger.warning("Google Generative AI not available - using mock mode only")
    GENAI_AVAILABLE = False
    genai = None


class StoryGenerator:
    """
    Generates dynamic story content using Google's Gemini API.
    Falls back to rich mock stories if API is unavailable.
    """

    def __init__(self):
        self.model = None
        
        # Only configure if API is available and key exists
        if GENAI_AVAILABLE and settings.google_api_key:
            try:
                genai.configure(api_key=settings.google_api_key)
                self.model = genai.GenerativeModel('gemini-pro')
                logger.info("✅ Google Gemini AI initialized")
            except Exception as e:
                logger.warning(f"⚠️ Could not initialize Gemini: {e}")
                self.model = None
        else:
            logger.info("⚡ Running in MOCK STORY mode (instant generation)")

    async def generate_opening(self, child1: ChildProfile, child2: ChildProfile) -> StoryBeat:
        """Generate opening story beat using AI or mock."""
        
        # Always use mock for instant stories
        if not self.model or not GENAI_AVAILABLE:
            return self._generate_mock_story(child1, child2)
        
        # If we want to use real AI in the future, implement here
        try:
            # Real Gemini API call would go here
            pass
        except Exception as e:
            logger.error(f"AI generation failed: {e}")
            return self._generate_mock_story(child1, child2)

    def _generate_mock_story(self, child1: ChildProfile, child2: ChildProfile) -> StoryBeat:
        """Generate instant rich mock story with full personalization (Bruno, Dragon, etc.)"""
        
        # Rich personalized opening with spirit animals and favorite items
        narration = f"""Welcome to the magical realm of TwinSpark! 

{child1.name}, guided by the spirit of the {child1.spirit_animal}, holds {child1.favorite_toy_name} close. 
{child2.name}, blessed by the {child2.spirit_animal}, carries {child2.favorite_toy_name} for protection.

Together, you stand at the edge of the Enchanted Forest. A mysterious glow appears in the distance."""
        
        # Child 1's perspective
        c1_perspective = f"""{child1.name}, your {child1.spirit_animal} spirit tingles with excitement! 
You clutch {child1.favorite_toy_name} tightly as the magical glow beckons you forward.
The forest whispers secrets only you can hear..."""
        
        # Child 2's perspective
        c2_perspective = f"""{child2.name}, your {child2.spirit_animal} senses alert you to ancient magic nearby!
{child2.favorite_toy_name} glows faintly in your hands, responding to the mysterious light.
You feel drawn toward the unknown..."""
        
        return StoryBeat(
            beat_number=1,
            narration=narration,
            child1_perspective=c1_perspective,
            child2_perspective=c2_perspective,
            choices=[
                Choice(
                    id="explore",
                    text=f"Follow the glow into the forest",
                    child_id=child1.id,
                    consequence_hint="Adventure awaits the brave..."
                ),
                Choice(
                    id="investigate",
                    text=f"Study the light from a safe distance",
                    child_id=child2.id,
                    consequence_hint="Knowledge comes to the patient..."
                ),
                Choice(
                    id="together",
                    text=f"Approach together, holding hands",
                    child_id="both",
                    consequence_hint="Strength lies in unity..."
                )
            ],
            emotion_target="wonder",
            image_prompt=f"{child1.name} and {child2.name} at the edge of an enchanted forest, magical glow, {child1.spirit_animal} and {child2.spirit_animal} spirits visible",
            audio_cues=["forest-ambiance", "magical-shimmer"]
        )

    async def generate_next_beat(
        self,
        previous_beats: List[StoryBeat],
        child_choice: Choice,
        child1: ChildProfile,
        child2: ChildProfile
    ) -> StoryBeat:
        """Generate the next story beat based on player choice."""
        
        # For now, use mock
        return self._generate_mock_story(child1, child2)
