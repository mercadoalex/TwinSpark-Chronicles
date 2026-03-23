"""StoryCoordinator — story generation pipeline with content filtering."""

import logging
from typing import Dict, Optional, List

from app.services.content_filter import ContentFilter, ContentRating

logger = logging.getLogger(__name__)

MAX_CONTENT_RETRIES = 3


class StoryCoordinator:
    """Owns story generation, content filtering, voice playback triggers, memory, narration."""

    def __init__(
        self,
        storyteller,
        content_filter: ContentFilter,
        memory_agent,
        voice_agent,
        playback_integrator=None,
    ) -> None:
        self.storyteller = storyteller
        self.content_filter = content_filter
        self.memory = memory_agent
        self.voice = voice_agent
        self.playback_integrator = playback_integrator

    async def generate_safe_story_segment(
        self,
        story_context: Dict,
        user_input: Optional[str],
        allowed_themes: Optional[List[str]] = None,
        custom_blocked_words: Optional[List[str]] = None,
    ) -> Dict:
        """Generate a story segment with content filtering and retry logic."""
        session_id = story_context.get("session_id", "")

        for attempt in range(MAX_CONTENT_RETRIES):
            try:
                segment = await self.storyteller.generate_story_segment(
                    context=story_context,
                    user_input=user_input,
                )
            except Exception as e:
                logger.error(
                    "Story generation failed: session=%s attempt=%d error=%s",
                    session_id, attempt + 1, e,
                )
                continue

            try:
                result = self.content_filter.scan(
                    text=segment["text"],
                    allowed_themes=allowed_themes,
                    custom_blocked_words=custom_blocked_words,
                    session_id=session_id,
                )
            except Exception as e:
                logger.error(
                    "ContentFilter error: session=%s attempt=%d error=%s — returning fallback",
                    session_id, attempt + 1, e,
                )
                return self.storyteller._fallback_story(story_context)

            logger.info(
                "Content filter: session=%s attempt=%d rating=%s reason=%s",
                session_id, attempt + 1, result.rating, result.reason,
            )

            if result.rating == ContentRating.SAFE:
                return segment

            logger.warning(
                "Content rejected: session=%s attempt=%d rating=%s matched=%s",
                session_id, attempt + 1, result.rating.value, result.matched_terms,
            )

        logger.warning(
            "All %d content retries exhausted for session=%s — returning fallback",
            MAX_CONTENT_RETRIES, session_id,
        )
        return self.storyteller._fallback_story(story_context)

    def filter_text(
        self,
        text: str,
        session_id: str,
        allowed_themes: Optional[List[str]] = None,
        custom_blocked_words: Optional[List[str]] = None,
    ) -> Optional[str]:
        """Filter text through ContentFilter. Returns text if SAFE, None otherwise."""
        try:
            result = self.content_filter.scan(
                text=text,
                allowed_themes=allowed_themes,
                custom_blocked_words=custom_blocked_words,
                session_id=session_id,
            )
            if result.rating == ContentRating.SAFE:
                return text
            logger.warning(
                "Text filtered out: session=%s rating=%s reason=%s",
                session_id, result.rating.value, result.reason,
            )
            return None
        except Exception as e:
            logger.error("ContentFilter error during text filter: %s", e)
            return None

    def filter_choices(
        self,
        story_segment: Dict,
        session_id: str,
        allowed_themes: Optional[List[str]] = None,
        custom_blocked_words: Optional[List[str]] = None,
    ) -> Dict:
        """Filter story choices and perspective text through content filter."""
        interactive = story_segment.get("interactive", {})
        if not interactive:
            return story_segment

        choice_text = interactive.get("text", "")
        if choice_text:
            filtered = self.filter_text(
                choice_text, session_id, allowed_themes, custom_blocked_words,
            )
            if filtered is None:
                interactive["text"] = "What would you like to do next?"

        choices = interactive.get("choices", [])
        if choices:
            safe_choices = []
            for choice in choices:
                choice_str = choice if isinstance(choice, str) else choice.get("text", "")
                if choice_str:
                    result = self.filter_text(
                        choice_str, session_id, allowed_themes, custom_blocked_words,
                    )
                    if result is not None:
                        safe_choices.append(choice)
            if safe_choices:
                interactive["choices"] = safe_choices

        story_segment["interactive"] = interactive
        return story_segment

    async def check_voice_playback(
        self,
        story_segment: Dict,
        characters: Dict,
        user_input: Optional[str],
        language: str,
    ) -> List[Dict]:
        """Check for voice recording playback triggers and return matches."""
        voice_recordings = []
        try:
            if self.playback_integrator is None:
                return voice_recordings

            child1_name = characters.get("child1", {}).get("name", "child1")
            child2_name = characters.get("child2", {}).get("name", "child2")
            sibling_pair_id = ":".join(sorted([child1_name, child2_name]))

            story_text_lower = story_segment.get("text", "").lower()
            user_input_lower = (user_input or "").lower()

            # Check STORY_INTRO on first beat
            if not user_input or user_input_lower in ("story_start", "story beginning"):
                intro_result = await self.playback_integrator.get_story_intro_audio(
                    sibling_pair_id, language
                )
                if intro_result:
                    voice_recordings.append({
                        "type": "story_intro",
                        "audio_base64": intro_result.audio_base64,
                        "source": intro_result.source,
                        "recorder_name": intro_result.recorder_name,
                        "recording_id": intro_result.recording_id,
                    })

            # Check ENCOURAGEMENT on brave decisions
            brave_keywords = ["brave", "courage", "hero", "valiente", "coraje"]
            if any(kw in story_text_lower for kw in brave_keywords) or any(
                kw in user_input_lower for kw in brave_keywords
            ):
                enc_result = await self.playback_integrator.get_encouragement_audio(
                    sibling_pair_id, language
                )
                if enc_result:
                    voice_recordings.append({
                        "type": "encouragement",
                        "audio_base64": enc_result.audio_base64,
                        "source": enc_result.source,
                        "recorder_name": enc_result.recorder_name,
                        "recording_id": enc_result.recording_id,
                    })

            # Check SOUND_EFFECT on playful moments
            playful_keywords = ["silly", "funny", "laugh", "giggle", "play", "divertido", "risa"]
            if any(kw in story_text_lower for kw in playful_keywords):
                sfx_result = await self.playback_integrator.get_sound_effect(
                    sibling_pair_id, language
                )
                if sfx_result:
                    voice_recordings.append({
                        "type": "sound_effect",
                        "audio_base64": sfx_result.audio_base64,
                        "source": sfx_result.source,
                        "recorder_name": sfx_result.recorder_name,
                        "recording_id": sfx_result.recording_id,
                    })
        except Exception as e:
            logger.warning("Voice recording playback check failed: %s", e)

        return voice_recordings

    async def recall_memories(self, session_id: str, query: str) -> List:
        """Recall relevant memories for the session."""
        if not self.memory.enabled:
            return []
        try:
            memories = await self.memory.recall_relevant_moments(
                session_id=session_id, query=query,
            )
            return memories
        except Exception as e:
            logger.warning("Memory recall skipped: %s", e)
            return []

    async def store_memory(
        self, session_id: str, story_text: str, user_input: Optional[str]
    ) -> None:
        """Store a story moment in memory."""
        if not self.memory.enabled:
            return
        try:
            await self.memory.store_story_moment(
                session_id=session_id,
                moment_data={
                    "scene": story_text[:100],
                    "choice_made": user_input or "story_start",
                    "outcome": "",
                    "emotion": "joyful",
                    "lesson": self.extract_lesson(story_text),
                },
            )
        except Exception as e:
            logger.warning("Memory storage skipped: %s", e)

    async def generate_narration(self, text: str, language: str) -> Optional[str]:
        """Generate narration audio if voice agent is enabled."""
        if not self.voice.enabled:
            return None
        try:
            return await self.voice.generate_narration(text=text, language=language)
        except Exception as e:
            logger.warning("Voice generation skipped: %s", e)
            return None

    async def generate_character_voices(
        self, text: str, characters: Dict, language: str
    ) -> List[Dict]:
        """Generate character dialogue voices."""
        if not self.voice.enabled:
            return []
        dialogues = self.extract_dialogues(text)
        character_voices = []
        for dialogue in dialogues[:2]:
            try:
                spirit_animal = characters.get("child1", {}).get("spirit_animal", "dragon")
                voice_type = self.voice.get_character_voice_for_spirit_animal(spirit_animal)
                audio = await self.voice.generate_dialogue(
                    text=dialogue["text"],
                    character_type=voice_type,
                    emotion=dialogue.get("emotion", "neutral"),
                    language=language,
                )
                if audio:
                    character_voices.append({
                        "character": dialogue["character"],
                        "audio": audio,
                        "text": dialogue["text"],
                    })
            except Exception as e:
                logger.warning("Character voice skipped: %s", e)
        return character_voices

    def extract_dialogues(self, text: str) -> List[Dict]:
        """Extract character dialogues from story text."""
        dialogues = []
        if '"' in text:
            parts = text.split('"')
            for i in range(1, len(parts), 2):
                if parts[i].strip():
                    dialogues.append({
                        "character": "character",
                        "text": parts[i].strip(),
                        "emotion": "neutral",
                    })
        return dialogues

    def extract_lesson(self, text: str) -> str:
        """Extract moral/lesson from story text."""
        themes = {
            "brave": "courage", "courage": "courage",
            "kind": "kindness", "kindness": "kindness",
            "share": "sharing", "sharing": "sharing",
            "help": "helping others",
            "friend": "friendship", "friendship": "friendship",
            "honest": "honesty", "truth": "honesty",
            "teamwork": "teamwork", "together": "teamwork",
        }
        text_lower = text.lower()
        for keyword, theme in themes.items():
            if keyword in text_lower:
                return theme
        return "adventure"
