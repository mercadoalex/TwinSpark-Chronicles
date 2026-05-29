"""Freeform input handler for the voice-first story loop.

Interprets any child input (voice transcript or card selection) and
produces a valid StoryBeatResponse. Uses a "yes-and" approach: the AI
never rejects or invalidates creative input, always weaving it into
the narrative.

Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6
"""

import json
import logging
import os
import uuid
from typing import Optional

from app.models.story_beat import StoryBeatResponse, SuggestionData

logger = logging.getLogger(__name__)


class FreeformInputHandler:
    """Ensures any child input produces a valid story beat.

    Uses Google Gemini 2.0 Flash to interpret freeform voice input or
    card selections and generate the next narrative beat with contextual
    suggestions. Never returns an error or rejection for creative input.
    """

    def __init__(self):
        self._model = None
        self._init_model()

    def _init_model(self) -> None:
        """Initialize the Gemini model if an API key is available."""
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            logger.warning(
                "GOOGLE_API_KEY not set — FreeformInputHandler will use fallback responses"
            )
            return

        try:
            import google.generativeai as genai

            genai.configure(api_key=api_key)
            self._model = genai.GenerativeModel(
                model_name="gemini-2.0-flash-exp",
                generation_config={
                    "temperature": 0.9,
                    "top_p": 0.95,
                    "top_k": 40,
                    "max_output_tokens": 1024,
                    "response_mime_type": "application/json",
                },
                safety_settings=[
                    {
                        "category": "HARM_CATEGORY_HARASSMENT",
                        "threshold": "BLOCK_LOW_AND_ABOVE",
                    },
                    {
                        "category": "HARM_CATEGORY_HATE_SPEECH",
                        "threshold": "BLOCK_LOW_AND_ABOVE",
                    },
                    {
                        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                        "threshold": "BLOCK_LOW_AND_ABOVE",
                    },
                    {
                        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                        "threshold": "BLOCK_LOW_AND_ABOVE",
                    },
                ],
            )
            logger.info("FreeformInputHandler: Gemini model initialized")
        except Exception as e:
            logger.error("Failed to initialize Gemini model: %s", e)
            self._model = None

    def build_storyteller_prompt(
        self,
        input_text: str,
        active_twin: str,
        story_context: dict,
    ) -> str:
        """Build the storyteller prompt with yes-and instruction.

        The prompt instructs the AI to:
        - Accept any input and weave it creatively into the narrative
        - Generate 2-3 contextual suggestions for the next turn
        - Limit narration to 3 sentences max
        - Never reject or invalidate the child's input
        """
        theme = story_context.get("theme", "a magical adventure")
        previous_narration = story_context.get("previous_narration", "")
        twin_names = story_context.get("twin_names", {})
        active_name = twin_names.get(active_twin, active_twin)

        context_section = ""
        if previous_narration:
            context_section = f"\nPrevious story beat: {previous_narration}\n"

        return f"""You are a magical storyteller for young children (ages 6-8).
You are telling a story about twins on {theme}.

CRITICAL RULES — "YES-AND" STORYTELLING:
1. ACCEPT any input from the child — no matter how fantastical, silly, off-topic, or grammatically incorrect.
2. NEVER say "I don't understand", "that doesn't make sense", or reject the input in any way.
3. Creatively weave the child's input into the ongoing narrative. If they say "make it rain candy", then it rains candy. If they say random words, interpret them as magical incantations or sound effects.
4. If the child mentions the other twin by name, incorporate that twin into the action.
5. Keep the story child-safe, fun, and full of wonder.

NARRATION RULES:
- Maximum 3 sentences for the narration. Keep it concise and vivid.
- Write for text-to-speech: use simple words, short sentences, natural rhythm.
- The narration should advance the story based on what {active_name} said.

SUGGESTION RULES:
- Generate exactly 2 or 3 suggestions for what could happen next.
- Each suggestion label must be 4 words or fewer.
- Suggestions should be contextually relevant to the current story moment.
- Make suggestions varied: one adventurous, one silly/fun, one gentle/cozy.
{context_section}
The active child ({active_name}) says: "{input_text}"

Respond with a JSON object matching this exact schema:
{{
  "narration": "string (max 3 sentences, the next story beat)",
  "illustration_prompt": "string (a vivid scene description for image generation)",
  "suggestions": [
    {{
      "id": "string (unique id like spark_1)",
      "label": "string (max 4 words)",
      "illustration_prompt": "string (scene for this suggestion's card)",
      "story_direction": "string (full text of what happens if chosen)"
    }}
  ],
  "perspective": "string (the active twin's name or id)",
  "is_milestone": false
}}"""

    async def interpret_input(
        self,
        input_text: str,
        session_id: str,
        active_twin: str,
        story_context: dict,
    ) -> StoryBeatResponse:
        """Interpret freeform input and produce a valid story beat.

        NEVER returns an error or rejection for creative input.
        Always produces a valid StoryBeatResponse.

        Args:
            input_text: The child's voice transcript or card story_direction.
            session_id: Current session identifier.
            active_twin: Which twin is providing input ('twin1' or 'twin2').
            story_context: Dict with theme, previous_narration, twin_names, etc.

        Returns:
            A validated StoryBeatResponse with narration, suggestions, etc.
        """
        if self._model is None:
            return self._fallback_response(input_text, active_twin, story_context)

        prompt = self.build_storyteller_prompt(input_text, active_twin, story_context)

        try:
            response = await self._generate_with_gemini(prompt)
            return self._parse_response(response, active_twin, story_context)
        except Exception as e:
            logger.error(
                "Gemini generation failed for session %s: %s — using fallback",
                session_id,
                e,
            )
            return self._fallback_response(input_text, active_twin, story_context)

    async def _generate_with_gemini(self, prompt: str) -> str:
        """Call Gemini and return the raw response text."""
        response = await self._model.generate_content_async(prompt)
        return response.text

    def _parse_response(
        self,
        response_text: str,
        active_twin: str,
        story_context: dict,
    ) -> StoryBeatResponse:
        """Parse Gemini JSON response into a validated StoryBeatResponse."""
        try:
            data = json.loads(response_text)
        except json.JSONDecodeError:
            logger.warning("Failed to parse Gemini response as JSON, using fallback")
            return self._fallback_response("", active_twin, story_context)

        # Build suggestions from response
        suggestions_data = data.get("suggestions", [])
        suggestions = []
        for i, s in enumerate(suggestions_data):
            suggestions.append(
                SuggestionData(
                    id=s.get("id", f"spark_{i + 1}"),
                    label=self._truncate_label(s.get("label", "Keep going")),
                    illustration_prompt=s.get(
                        "illustration_prompt", "A magical scene"
                    ),
                    illustration_url=None,
                    story_direction=s.get(
                        "story_direction", "The adventure continues"
                    ),
                )
            )

        # Ensure we have 2-3 suggestions
        if len(suggestions) < 2:
            suggestions = self._default_suggestions()
        elif len(suggestions) > 3:
            suggestions = suggestions[:3]

        # Build the response
        narration = data.get("narration", "The adventure continues with wonder!")
        perspective = data.get("perspective", active_twin)
        is_milestone = data.get("is_milestone", False)
        illustration_prompt = data.get(
            "illustration_prompt", "A magical adventure scene"
        )

        return StoryBeatResponse(
            narration=narration,
            illustration_prompt=illustration_prompt,
            illustration_url=None,
            suggestions=suggestions,
            perspective=perspective,
            is_milestone=is_milestone,
        )

    def _fallback_response(
        self,
        input_text: str,
        active_twin: str,
        story_context: dict,
    ) -> StoryBeatResponse:
        """Generate a valid fallback response when Gemini is unavailable.

        Always produces a valid beat — never returns an error to the child.
        """
        twin_names = story_context.get("twin_names", {})
        active_name = twin_names.get(active_twin, "our hero")

        if input_text:
            narration = (
                f"And just like that, {active_name} imagined something amazing! "
                f"The world around them shimmered and changed. "
                f"A new path appeared, glowing with possibility."
            )
        else:
            narration = (
                f"{active_name} looked around with wonder. "
                f"The magical world was full of surprises. "
                f"What would happen next?"
            )

        return StoryBeatResponse(
            narration=narration,
            illustration_prompt=f"A magical adventure scene with a child named {active_name} discovering something wonderful",
            illustration_url=None,
            suggestions=self._default_suggestions(),
            perspective=active_twin,
            is_milestone=False,
        )

    def _default_suggestions(self) -> list[SuggestionData]:
        """Return default suggestions when parsing fails or as fallback."""
        return [
            SuggestionData(
                id=f"spark_{uuid.uuid4().hex[:6]}",
                label="Explore the cave",
                illustration_prompt="A glowing mysterious cave entrance",
                illustration_url=None,
                story_direction="They decide to explore a mysterious glowing cave nearby",
            ),
            SuggestionData(
                id=f"spark_{uuid.uuid4().hex[:6]}",
                label="Find a friend",
                illustration_prompt="A friendly magical creature appearing",
                illustration_url=None,
                story_direction="A friendly magical creature appears and wants to play",
            ),
            SuggestionData(
                id=f"spark_{uuid.uuid4().hex[:6]}",
                label="Fly up high",
                illustration_prompt="Children soaring through colorful clouds",
                illustration_url=None,
                story_direction="They discover they can fly and soar up into the colorful clouds",
            ),
        ]

    @staticmethod
    def _truncate_label(label: str) -> str:
        """Ensure label is at most 4 words."""
        words = label.split()
        if len(words) > 4:
            return " ".join(words[:4])
        return label
