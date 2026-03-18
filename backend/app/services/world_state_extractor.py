"""Extracts world state changes from session story moments using Gemini.

Parses narrative text to identify new locations, NPCs, items, and updates
to existing world entities. Uses structured JSON output from Gemini 2.0 Flash.

Requirements: 2.1, 2.2, 2.3, 2.4
"""

import json
import logging
import os

import google.generativeai as genai

logger = logging.getLogger(__name__)

EXTRACTION_PROMPT_TEMPLATE = """You are analyzing a children's story session to extract world state changes.

Given the following story moments from a session, identify:
1. NEW LOCATIONS the children discovered (places they visited for the first time)
2. NEW NPCs (characters they met and befriended)
3. NEW ITEMS (objects/artifacts they collected or received)
4. LOCATION UPDATES (existing places that changed state, e.g. "dark forest" became "enchanted grove")
5. NPC UPDATES (existing characters whose relationship deepened)

Story moments:
{moments_text}

Respond with ONLY valid JSON in this exact format (no markdown, no explanation):
{{
  "new_locations": [
    {{"name": "Crystal Cave", "description": "A shimmering cave filled with glowing crystals", "state": "discovered"}}
  ],
  "new_npcs": [
    {{"name": "Luna the Fox", "description": "A friendly silver fox who guards the forest path", "relationship_level": 1}}
  ],
  "new_items": [
    {{"name": "Star Compass", "description": "A compass that points toward hidden treasures"}}
  ],
  "location_updates": [
    {{"name": "Dark Forest", "new_state": "enchanted", "new_description": "The once-dark forest now glows with fireflies"}}
  ],
  "npc_updates": [
    {{"name": "Old Owl", "relationship_level": 3}}
  ]
}}

If nothing was discovered, return empty arrays. Only include genuinely new or changed entities."""

_EMPTY_RESULT = {
    "new_locations": [],
    "new_npcs": [],
    "new_items": [],
    "location_updates": [],
    "npc_updates": [],
}


class WorldStateExtractor:
    """Extracts world state changes from session story moments using Gemini."""

    def __init__(self) -> None:
        self._model = None
        self._init_model()

    def _init_model(self) -> None:
        """Initialize Gemini model for extraction."""
        try:
            api_key = os.getenv("GOOGLE_API_KEY")
            if api_key:
                genai.configure(api_key=api_key)
                self._model = genai.GenerativeModel(
                    model_name="gemini-2.0-flash-exp",
                    generation_config={
                        "temperature": 0.2,
                        "max_output_tokens": 2048,
                    },
                )
                logger.info("WorldStateExtractor: Gemini model initialized")
            else:
                logger.warning("WorldStateExtractor: No GOOGLE_API_KEY, extraction disabled")
        except Exception as e:
            logger.warning("WorldStateExtractor: model init failed: %s", e)

    def build_extraction_prompt(self, moments: list[dict]) -> str:
        """Build the Gemini prompt for world state extraction."""
        lines = []
        for i, m in enumerate(moments, 1):
            scene = m.get("scene", "")
            choice = m.get("choice_made", "")
            outcome = m.get("outcome", "")
            lines.append(f"Moment {i}: {scene} | Choice: {choice} | Outcome: {outcome}")
        moments_text = "\n".join(lines) if lines else "No story moments recorded."
        return EXTRACTION_PROMPT_TEMPLATE.format(moments_text=moments_text)

    def parse_extraction_response(self, response_text: str) -> dict:
        """Parse Gemini's JSON response into structured world changes."""
        try:
            # Strip markdown code fences if present
            text = response_text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1] if "\n" in text else text[3:]
                if text.endswith("```"):
                    text = text[:-3]
                text = text.strip()
            data = json.loads(text)
            # Validate expected keys
            result = {}
            for key in ("new_locations", "new_npcs", "new_items", "location_updates", "npc_updates"):
                val = data.get(key, [])
                result[key] = val if isinstance(val, list) else []
            return result
        except (json.JSONDecodeError, TypeError, KeyError) as e:
            logger.error("WorldStateExtractor: failed to parse response: %s", e)
            return dict(_EMPTY_RESULT)

    async def extract(self, session_moments: list[dict]) -> dict:
        """Parse story moments and return structured world changes."""
        if not session_moments:
            return dict(_EMPTY_RESULT)

        if self._model is None:
            logger.warning("WorldStateExtractor: model not available, returning empty")
            return dict(_EMPTY_RESULT)

        prompt = self.build_extraction_prompt(session_moments)
        try:
            response = await self._model.generate_content_async(prompt)
            return self.parse_extraction_response(response.text)
        except Exception as e:
            logger.error("WorldStateExtractor: Gemini call failed: %s", e)
            return dict(_EMPTY_RESULT)
