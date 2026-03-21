"""
Agent Orchestrator
Coordinates all AI agents to create rich multimodal story experiences.

Extended with sibling dynamics pipeline (Layers 1-4) that processes
personality, relationship, skills, and narrative directives in sequence.

Requirements: 2.1, 2.3, 2.4, 2.5, 6.2, 6.5, 8.1, 8.2, 8.3, 9.1, 9.2, 9.3, 9.4, 11.1, 11.4, 11.5
"""

import asyncio
import logging
from typing import Dict, Optional, List
from datetime import datetime

from app.models.multimodal import MultimodalInputEvent, EmotionCategory, EmotionResult
from app.services.content_filter import ContentFilter, ContentRating
from app.services.session_service import SessionService
from app.services.story_archive_service import StoryArchiveService
from app.utils.title_generator import generate_story_title
from app.utils.beat_transformer import transform_beats

logger = logging.getLogger(__name__)

MAX_CONTENT_RETRIES = 3


class AgentOrchestrator:
    """
    Master coordinator for all AI agents, including the 4-layer
    Sibling Dynamics Engine pipeline.
    """
    
    def __init__(self):
        # Import agents here to avoid circular imports
        from .storyteller_agent import storyteller
        from .visual_agent import visual_agent
        from .voice_agent import voice_agent
        from .memory_agent import memory_agent
        
        self.storyteller = storyteller
        self.visual = visual_agent
        self.voice = voice_agent
        self.memory = memory_agent

        # Sibling dynamics services (Layer 1-3)
        from app.services.sibling_db import SiblingDB
        from app.services.personality_engine import PersonalityEngine
        from app.services.relationship_mapper import RelationshipMapper
        from app.services.skills_discoverer import ComplementarySkillsDiscoverer

        from app.db.connection import DatabaseConnection

        self._db_conn = DatabaseConnection()
        self._sibling_db = SiblingDB(self._db_conn)
        self._db_initialized = False
        self.personality_engine = PersonalityEngine(self._sibling_db)
        self.relationship_mapper = RelationshipMapper(self._sibling_db)
        self.skills_discoverer = ComplementarySkillsDiscoverer(self._sibling_db)

        # Track protagonist history for narrative directive alternation
        self._protagonist_history: list[str] = []

        # Content safety filter (Req 8.1, 8.2, 8.3)
        self.content_filter = ContentFilter()

        # Track in-flight asyncio tasks per session for emergency stop (Req 6.2, 6.5)
        self._session_tasks: Dict[str, set[asyncio.Task]] = {}

        # Session time enforcer and WebSocket manager references (set from main.py)
        self.session_time_enforcer = None  # SessionTimeEnforcer instance
        self.ws_manager = None  # ConnectionManager instance for sending WS messages

        # Persistent world state (cross-session)
        from app.services.world_db import WorldDB
        from app.services.world_state_extractor import WorldStateExtractor
        from app.services.world_context_formatter import WorldContextFormatter

        self._world_db = WorldDB(self._db_conn)
        self._world_extractor = WorldStateExtractor()
        self._world_context_formatter = WorldContextFormatter()
        self._world_state_cache: Dict[str, dict] = {}  # keyed by sibling_pair_id

        # Photo pipeline (family photo integration)
        from app.agents.style_transfer_agent import StyleTransferAgent
        from app.services.scene_compositor import SceneCompositor

        self._style_transfer = StyleTransferAgent()
        self._scene_compositor = SceneCompositor()

        # Voice recording playback integration (initialized lazily in _ensure_db_initialized)
        self._playback_integrator = None

        print("🎭 Agent orchestrator initialized")

    async def _generate_safe_story_segment(
        self,
        story_context: Dict,
        user_input: Optional[str],
        allowed_themes: Optional[List[str]] = None,
        custom_blocked_words: Optional[List[str]] = None,
    ) -> Dict:
        """Generate a story segment with content filtering and retry logic.

        Retries up to MAX_CONTENT_RETRIES times when the ContentFilter rates
        the segment as REVIEW or BLOCKED.  Returns a safe fallback after all
        retries are exhausted or if the filter itself raises an exception.

        Requirements: 2.1, 2.3, 2.4, 2.5, 8.1, 8.3
        """
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

            # Run content filter on the generated text
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

            # REVIEW or BLOCKED — discard and retry
            logger.warning(
                "Content rejected: session=%s attempt=%d rating=%s matched=%s",
                session_id, attempt + 1, result.rating.value, result.matched_terms,
            )

        # All retries exhausted (Req 2.5)
        logger.warning(
            "All %d content retries exhausted for session=%s — returning fallback",
            MAX_CONTENT_RETRIES, session_id,
        )
        return self.storyteller._fallback_story(story_context)

    def _filter_text(
        self,
        text: str,
        session_id: str,
        allowed_themes: Optional[List[str]] = None,
        custom_blocked_words: Optional[List[str]] = None,
    ) -> Optional[str]:
        """Filter a piece of text through ContentFilter.

        Returns the original text if SAFE, or None if REVIEW/BLOCKED or on error.
        Requirements: 8.2, 8.3
        """
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

    async def cancel_session(self, session_id: str) -> Dict:
        """Cancel all in-flight tasks for a session and return state summary.

        Requirements: 6.2, 6.5
        """
        # End session time tracking before cancelling tasks
        if self.session_time_enforcer is not None:
            self.session_time_enforcer.end_session(session_id)

        tasks = self._session_tasks.pop(session_id, set())
        cancelled_count = 0
        for task in tasks:
            if not task.done():
                task.cancel()
                cancelled_count += 1

        # Wait briefly for tasks to wrap up
        if tasks:
            await asyncio.wait(tasks, timeout=2.0)

        logger.info(
            "Emergency stop: session=%s cancelled=%d total=%d",
            session_id, cancelled_count, len(tasks),
        )

        return {
            "session_id": session_id,
            "cancelled_tasks": cancelled_count,
            "session_saved": True,
            "status": "stopped",
        }

    async def _drawing_time_watchdog(self, session_id: str, duration: int) -> None:
        """Background task that checks session time during an active drawing.

        Polls ``session_time_enforcer.check_time()`` every 5 seconds for up to
        *duration* seconds.  If the session expires mid-drawing, sends a
        ``DRAWING_END`` message with ``reason: "session_expired"`` and exits.

        Requirements: 9.1, 9.2
        """
        _POLL_INTERVAL = 5  # seconds
        elapsed = 0
        try:
            while elapsed < duration:
                await asyncio.sleep(_POLL_INTERVAL)
                elapsed += _POLL_INTERVAL

                if self.session_time_enforcer is None:
                    break

                time_check = self.session_time_enforcer.check_time(session_id)
                if time_check.is_expired:
                    logger.info(
                        "Drawing watchdog: session %s expired mid-drawing at %ds",
                        session_id, elapsed,
                    )
                    if self.ws_manager is not None:
                        await self.ws_manager.send_story(session_id, {
                            "type": "DRAWING_END",
                            "session_id": session_id,
                            "reason": "session_expired",
                        })
                    return
        except asyncio.CancelledError:
            logger.debug("Drawing watchdog cancelled for session %s", session_id)
        except Exception as e:
            logger.warning("Drawing watchdog error for session %s: %s", session_id, e)

    async def generate_rich_story_moment(self, session_id: str, characters: Dict, user_input: Optional[str] = None, language: str = "en", **kwargs) -> Dict:
        """Generate a complete multimodal story moment with all agents."""
        print(f"\n🎬 Generating rich story moment for session {session_id}")

        # Check session time before generation (Req 1.2, 1.3, 1.4)
        if self.session_time_enforcer is not None:
            time_check = self.session_time_enforcer.check_time(session_id)
            if time_check.is_expired:
                logger.info("Session %s time expired — skipping generation", session_id)
                if self.ws_manager is not None:
                    await self.ws_manager.send_story(session_id, {
                        "type": "SESSION_TIME_EXPIRED",
                        "session_id": session_id,
                    })
                return {
                    "text": "",
                    "image": None,
                    "audio": {"narration": None, "character_voices": []},
                    "interactive": {},
                    "timestamp": None,
                    "memories_used": 0,
                    "voice_recordings": [],
                    "agents_used": {
                        "storyteller": False,
                        "visual": False,
                        "voice": False,
                        "memory": False,
                    },
                    "session_time_expired": True,
                }

        # Signal generation pause start (Req 7.1, 7.7)
        if self.session_time_enforcer is not None:
            self.session_time_enforcer.start_generation_pause(session_id)
        if self.ws_manager is not None:
            await self.ws_manager.send_story(session_id, {
                "type": "GENERATION_STARTED",
                "session_id": session_id,
            })

        try:
            return await self._do_generate_rich_story_moment(
                session_id, characters, user_input, language, **kwargs
            )
        finally:
            # Signal generation pause end (Req 7.2, 7.7)
            if self.session_time_enforcer is not None:
                self.session_time_enforcer.end_generation_pause(session_id)
            if self.ws_manager is not None:
                await self.ws_manager.send_story(session_id, {
                    "type": "GENERATION_COMPLETED",
                    "session_id": session_id,
                })

    async def _do_generate_rich_story_moment(self, session_id: str, characters: Dict, user_input: Optional[str] = None, language: str = "en", **kwargs) -> Dict:
        """Internal implementation of rich story moment generation."""

        # Extract parent preference fields from kwargs
        allowed_themes = kwargs.pop("allowed_themes", None)
        complexity_level = kwargs.pop("complexity_level", None)
        custom_blocked_words = kwargs.pop("custom_blocked_words", None)

        # Extract drawing context injected after a completed drawing (Req 5.1, 5.2, 5.3)
        drawing_context = kwargs.pop("drawing_context", None)

        # STEP 1: Get relevant memories
        memories = []
        if self.memory.enabled:
            try:
                memories = await self.memory.recall_relevant_moments(
                    session_id=session_id,
                    query=user_input or "story beginning"
                )
                print(f"🧠 Retrieved {len(memories)} relevant memories")
            except Exception as e:
                print(f"⚠️  Memory recall skipped: {e}")

        # STEP 1b: Load and inject world context (cross-session persistence)
        world_context_str = ""
        try:
            child1_name = characters.get("child1", {}).get("name", "child1")
            child2_name = characters.get("child2", {}).get("name", "child2")
            sibling_pair_id = ":".join(sorted([child1_name, child2_name]))

            if sibling_pair_id not in self._world_state_cache:
                await self._ensure_db_initialized()
                self._world_state_cache[sibling_pair_id] = await self._world_db.load_world_state(sibling_pair_id)

            world_state = self._world_state_cache.get(sibling_pair_id, {})
            world_context_str = self._world_context_formatter.format_beat_context(
                world_state, user_input or ""
            )
            if world_context_str:
                print(f"🗺️  World context injected ({len(world_state.get('locations', []))} locations, {len(world_state.get('npcs', []))} NPCs, {len(world_state.get('items', []))} items)")
        except Exception as e:
            logger.warning("World context injection failed: %s", e)

        # STEP 2: Generate story with content filtering (Req 2.1, 2.3, 2.4, 2.5, 8.1)
        story_context = {
            "characters": characters,
            "session_id": session_id,
            "language": language,
            "memories": memories,
            **kwargs
        }

        if world_context_str:
            story_context["world_context"] = world_context_str

        if complexity_level is not None:
            story_context["complexity_level"] = complexity_level

        # Inject drawing context so the storyteller references the drawing (Req 5.1, 5.2, 5.3)
        if drawing_context is not None:
            story_context["drawing_context"] = drawing_context

        try:
            story_segment = await self._generate_safe_story_segment(
                story_context=story_context,
                user_input=user_input,
                allowed_themes=allowed_themes,
                custom_blocked_words=custom_blocked_words,
            )
        except Exception as e:
            logger.error(
                "Unhandled error in safe story generation: session=%s error=%s — returning fallback",
                session_id, e,
            )
            story_segment = self.storyteller._fallback_story(story_context)

        print(f"📖 Story text generated: {len(story_segment['text'])} chars")

        # STEP 2a: Drawing prompt injection (Req 5.1, 9.1, 9.2, 9.3)
        # If the storyteller included a drawing_prompt, send it to clients
        drawing_prompt = story_segment.get("drawing_prompt")
        if drawing_prompt and self.ws_manager is not None:
            try:
                from app.services.drawing_sync_service import DrawingSyncService

                # Compute effective duration clamped to remaining session time
                requested_duration = story_segment.get("drawing_duration", 60)
                remaining_seconds: int | None = None
                if self.session_time_enforcer is not None:
                    time_check = self.session_time_enforcer.check_time(session_id)
                    if time_check.is_expired:
                        # Session already expired — skip drawing, send expiry
                        await self.ws_manager.send_story(session_id, {
                            "type": "DRAWING_END",
                            "session_id": session_id,
                            "reason": "session_expired",
                        })
                        logger.info("Session %s expired — skipping drawing prompt", session_id)
                    else:
                        remaining_seconds = int(time_check.remaining_seconds)
                        effective_duration = DrawingSyncService.clamp_duration(
                            requested_duration, remaining_seconds
                        )
                        await self.ws_manager.send_story(session_id, {
                            "type": "DRAWING_PROMPT",
                            "prompt": drawing_prompt,
                            "duration": effective_duration,
                            "session_id": session_id,
                        })
                        logger.info(
                            "Drawing prompt sent: session=%s duration=%d prompt=%s",
                            session_id, effective_duration, drawing_prompt[:80],
                        )
                        # Start background watchdog to expire drawing if session time runs out (Req 9.1, 9.2)
                        asyncio.create_task(
                            self._drawing_time_watchdog(session_id, effective_duration)
                        )
                else:
                    # No time enforcer — send with default clamped duration
                    effective_duration = DrawingSyncService.clamp_duration(requested_duration)
                    await self.ws_manager.send_story(session_id, {
                        "type": "DRAWING_PROMPT",
                        "prompt": drawing_prompt,
                        "duration": effective_duration,
                        "session_id": session_id,
                    })
                    logger.info(
                        "Drawing prompt sent (no time enforcer): session=%s duration=%d",
                        session_id, effective_duration,
                    )
            except Exception as e:
                logger.warning("Drawing prompt injection failed: %s", e)

        # STEP 2b: Filter story choices and perspective text (Req 8.2)
        interactive = story_segment.get("interactive", {})
        if interactive:
            choice_text = interactive.get("text", "")
            if choice_text:
                filtered = self._filter_text(
                    choice_text, session_id, allowed_themes, custom_blocked_words,
                )
                if filtered is None:
                    # Replace with a safe generic prompt
                    interactive["text"] = "What would you like to do next?"

            # Filter individual choices if present
            choices = interactive.get("choices", [])
            if choices:
                safe_choices = []
                for choice in choices:
                    choice_str = choice if isinstance(choice, str) else choice.get("text", "")
                    if choice_str:
                        result = self._filter_text(
                            choice_str, session_id, allowed_themes, custom_blocked_words,
                        )
                        if result is not None:
                            safe_choices.append(choice)
                if safe_choices:
                    interactive["choices"] = safe_choices

            story_segment["interactive"] = interactive

        # STEP 2c: Check for voice recording playback triggers
        voice_recordings = []
        try:
            if self._playback_integrator is not None:
                child1_name = characters.get("child1", {}).get("name", "child1")
                child2_name = characters.get("child2", {}).get("name", "child2")
                sibling_pair_id = ":".join(sorted([child1_name, child2_name]))

                story_text_lower = story_segment.get("text", "").lower()
                user_input_lower = (user_input or "").lower()

                # Check STORY_INTRO on first beat (no user input = session start)
                if not user_input or user_input_lower in ("story_start", "story beginning"):
                    intro_result = await self._playback_integrator.get_story_intro_audio(
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
                    enc_result = await self._playback_integrator.get_encouragement_audio(
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
                    sfx_result = await self._playback_integrator.get_sound_effect(
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

        # STEP 3: Generate scene illustration (if enabled)
        # Load photo pipeline portraits for compositing (if character mappings exist)
        photo_portraits = {}
        try:
            child1_name = characters.get("child1", {}).get("name", "child1")
            child2_name = characters.get("child2", {}).get("name", "child2")
            sibling_pair_id = ":".join(sorted([child1_name, child2_name]))

            await self._ensure_db_initialized()
            mappings = await self._db_conn.fetch_all(
                "SELECT mapping_id, sibling_pair_id, character_role, face_id, "
                "created_at FROM character_mappings WHERE sibling_pair_id = ?",
                (sibling_pair_id,),
            )
            if mappings and any(m["face_id"] for m in mappings):
                from app.models.photo import CharacterMapping as CM
                cm_list = [
                    CM(
                        mapping_id=m["mapping_id"],
                        sibling_pair_id=m["sibling_pair_id"],
                        character_role=m["character_role"],
                        face_id=m["face_id"],
                        family_member_name=None,
                        created_at=m["created_at"],
                    )
                    for m in mappings
                ]
                photo_portraits = await self._style_transfer.generate_portraits_for_session(
                    sibling_pair_id=sibling_pair_id,
                    session_id=session_id,
                    mappings=cm_list,
                    db=self._db_conn,
                )
                if photo_portraits:
                    print(f"📸 Photo portraits ready: {len(photo_portraits)} characters")
        except Exception as e:
            logger.warning("Photo pipeline skipped: %s", e)

        scene_image = None
        if self.visual.enabled:
            try:
                scene_image = await self.visual.generate_scene_image(
                    story_context={
                        "setting": self._extract_setting(story_segment['text']),
                        "mood": "joyful",
                        "key_objects": self._extract_key_objects(story_segment['text'])
                    },
                    child_profiles=characters,
                    scene_description=story_segment['text'][:200]
                )
                print(f"🎨 Scene image: {'✅ Generated' if scene_image else '❌ Failed'}")

                # Composite photo portraits into scene if available
                if scene_image and photo_portraits:
                    try:
                        import base64 as b64
                        scene_bytes = b64.b64decode(scene_image)
                        portrait_bytes = {}
                        for role, portrait_b64 in photo_portraits.items():
                            portrait_bytes[role] = b64.b64decode(portrait_b64)
                        composited = self._scene_compositor.composite(
                            base_scene_bytes=scene_bytes,
                            portraits=portrait_bytes,
                            character_positions={},
                        )
                        scene_image = b64.b64encode(composited).decode("utf-8")
                        print(f"📸 Scene composited with {len(portrait_bytes)} portraits")
                    except Exception as comp_err:
                        logger.warning("Scene compositing failed, using base scene: %s", comp_err)
            except Exception as e:
                print(f"⚠️  Visual generation skipped: {e}")

        # STEP 4: Generate narration audio (if enabled)
        narration_audio = None
        if self.voice.enabled:
            try:
                narration_audio = await self.voice.generate_narration(
                    text=story_segment['text'],
                    language=language
                )
                print(f"🎤 Narration: {'✅ Generated' if narration_audio else '❌ Failed'}")
            except Exception as e:
                print(f"⚠️  Voice generation skipped: {e}")

        # STEP 5: Generate character dialogue voices (optional)
        character_voices = []
        dialogues = self._extract_dialogues(story_segment['text'])

        if dialogues and self.voice.enabled:
            for dialogue in dialogues[:2]:  # Limit to 2 dialogues
                try:
                    spirit_animal = characters.get('child1', {}).get('spirit_animal', 'dragon')
                    voice_type = self.voice.get_character_voice_for_spirit_animal(spirit_animal)

                    audio = await self.voice.generate_dialogue(
                        text=dialogue['text'],
                        character_type=voice_type,
                        emotion=dialogue.get('emotion', 'neutral'),
                        language=language
                    )

                    if audio:
                        character_voices.append({
                            "character": dialogue['character'],
                            "audio": audio,
                            "text": dialogue['text']
                        })
                except Exception as e:
                    print(f"⚠️  Character voice skipped: {e}")

        # STEP 6: Store this moment in memory (if enabled)
        if self.memory.enabled:
            try:
                await self.memory.store_story_moment(
                    session_id=session_id,
                    moment_data={
                        "scene": story_segment['text'][:100],
                        "choice_made": user_input or "story_start",
                        "outcome": story_segment.get('interactive', {}).get('text', ''),
                        "emotion": "joyful",
                        "lesson": self._extract_lesson(story_segment['text'])
                    }
                )
            except Exception as e:
                print(f"⚠️  Memory storage skipped: {e}")

        # STEP 7: Return complete multimodal experience
        result = {
            "text": story_segment['text'],
            "image": scene_image,
            "audio": {
                "narration": narration_audio,
                "character_voices": character_voices
            },
            "interactive": story_segment.get('interactive', {}),
            "timestamp": story_segment.get('timestamp'),
            "memories_used": len(memories),
            "voice_recordings": voice_recordings,
            "agents_used": {
                "storyteller": True,
                "visual": scene_image is not None,
                "voice": narration_audio is not None,
                "memory": len(memories) > 0
            }
        }

        # STEP 7a: Associate drawing image with story beat (Req 4.5, 5.1)
        if drawing_context is not None:
            result["drawing_image_path"] = drawing_context.get("image_path", "")

        return result

    async def process_multimodal_event(
        self,
        event: MultimodalInputEvent,
        characters: Dict,
        language: str = "en",
    ) -> Dict:
        """
        Process a multimodal input event and generate an adapted story moment.

        Extracts transcript and emotion from the event, adapts story context
        based on the child's emotional state, and stores the emotion in memory.

        Args:
            event: Fused multimodal input containing transcript, emotions, face data
            characters: Dict with child1 and child2 data
            language: Story language (en/es/hi)

        Returns:
            Complete multimodal story moment dict
        """
        context = event.to_orchestrator_context()
        user_input = context["user_input"]
        detected_emotion = context["emotion"]

        # Req 9.5: Two-face perspective matching — when multiple emotions are
        # detected, pick the emotion belonging to the child whose name matches
        # the current story perspective character.
        if len(event.emotions) >= 2:
            detected_emotion = self._resolve_perspective_emotion(
                event.emotions, characters
            )

        # Build extra story context for the storyteller
        story_context_extra: Dict = {}

        # Req 9.2: Include emotion in story context when not neutral
        if detected_emotion != EmotionCategory.NEUTRAL.value:
            story_context_extra["child_emotion"] = detected_emotion

        # Req 9.3: When scared, instruct storyteller to reduce intensity
        if detected_emotion == EmotionCategory.SCARED.value:
            story_context_extra["emotion_instruction"] = (
                "The child seems scared. Please reduce the story intensity, "
                "avoid any frightening elements, and introduce comforting, "
                "reassuring story elements."
            )

        # Req 9.1: Pass transcript as user_input via generate_rich_story_moment
        result = await self.generate_rich_story_moment(
            session_id=event.session_id,
            characters=characters,
            user_input=user_input,
            language=language,
            **story_context_extra,
        )

        # Req 9.4: Store detected emotion in memory agent
        if self.memory.enabled:
            try:
                await self.memory.store_story_moment(
                    session_id=event.session_id,
                    moment_data={
                        "scene": result.get("text", "")[:100],
                        "choice_made": user_input or "multimodal_input",
                        "outcome": result.get("interactive", {}).get("text", ""),
                        "emotion": detected_emotion,
                        "lesson": self._extract_lesson(result.get("text", "")),
                    },
                )
            except Exception as e:
                print(f"⚠️  Multimodal memory storage skipped: {e}")

        return result

    # ── Sibling Dynamics Pipeline ─────────────────────────────────

    async def _ensure_db_initialized(self) -> None:
        """Lazily connect to DB and run migrations on first use."""
        if not self._db_initialized:
            import os
            from app.db.migration_runner import MigrationRunner

            await self._db_conn.connect()
            runner = MigrationRunner(self._db_conn)
            await runner.ensure_migration_table()

            if os.getenv("AUTO_MIGRATE", "").lower() == "true":
                applied = await runner.apply_all()
                if applied:
                    logger.info("Auto-applied %d migration(s)", len(applied))
            else:
                pending = await runner.get_pending_migrations()
                if pending:
                    names = [f for _, f in pending]
                    logger.warning("Unapplied migrations: %s", names)
                    # Apply anyway for dev convenience
                    await runner.apply_all()

            # Initialize PlaybackIntegrator for voice recording playback
            try:
                from app.services.playback_integrator import PlaybackIntegrator
                from app.services.voice_recording_service import VoiceRecordingService
                from app.services.audio_normalizer import AudioNormalizer

                audio_normalizer = AudioNormalizer()
                vrs = VoiceRecordingService(
                    db=self._db_conn,
                    audio_normalizer=audio_normalizer,
                )
                self._playback_integrator = PlaybackIntegrator(
                    voice_recording_service=vrs,
                    voice_agent=self.voice,
                    audio_normalizer=audio_normalizer,
                )
                logger.info("PlaybackIntegrator initialized")
            except Exception as e:
                logger.warning("PlaybackIntegrator initialization failed: %s", e)
                self._playback_integrator = None

            self._db_initialized = True

    async def process_sibling_event(
        self,
        event: MultimodalInputEvent,
        child1_id: str,
        child2_id: str,
        characters: Dict,
        language: str = "en",
    ) -> Dict:
        """Extended pipeline: personality → relationship → skills → narrative.

        Calls Layer 1 through Layer 4 in sequence. Each layer is wrapped
        in try/except for resilience — a failure in one layer does not
        block subsequent layers (Req 11.1, 11.5).

        Skips Layers 1-3 when the event has no usable data (empty
        transcript and no emotions) per Requirement 11.4.
        """
        await self._ensure_db_initialized()

        profile1 = None
        profile2 = None
        relationship = None
        skill_map = None
        narrative_dirs = None

        # Determine if the event has usable data (Req 11.4)
        has_usable_data = (
            not event.transcript.is_empty or len(event.emotions) > 0
        )

        if has_usable_data:
            # ── Layer 1: Personality Engine (Req 11.1, 11.2) ──────
            try:
                profile1 = await self.personality_engine.update_from_event(
                    child1_id, event
                )
            except Exception as e:
                logger.error("Layer 1 (personality child1) failed: %s", e)

            try:
                profile2 = await self.personality_engine.update_from_event(
                    child2_id, event
                )
            except Exception as e:
                logger.error("Layer 1 (personality child2) failed: %s", e)

            # ── Layer 2: Relationship Mapper (Req 11.1) ───────────
            try:
                p1 = profile1 or await self.personality_engine.load_profile(child1_id)
                p2 = profile2 or await self.personality_engine.load_profile(child2_id)
                relationship = await self.relationship_mapper.update_from_event(
                    event, (p1, p2)
                )
            except Exception as e:
                logger.error("Layer 2 (relationship) failed: %s", e)

            # ── Layer 3: Complementary Skills Discoverer ──────────
            try:
                p1 = profile1 or await self.personality_engine.load_profile(child1_id)
                p2 = profile2 or await self.personality_engine.load_profile(child2_id)
                interaction_count = p1.total_interactions + p2.total_interactions
                skill_map = await self.skills_discoverer.evaluate(
                    (p1, p2), interaction_count
                )
            except Exception as e:
                logger.error("Layer 3 (skills) failed: %s", e)

        # ── Layer 4: Narrative Directives + Story Generation ──────
        personality_context = None
        relationship_context = None
        skill_map_context = None

        try:
            # Build personality context for storyteller
            p1 = profile1 or await self.personality_engine.load_profile(child1_id)
            p2 = profile2 or await self.personality_engine.load_profile(child2_id)

            personality_context = {}
            for p in (p1, p2):
                traits = p.trait_dict()
                dominant = [
                    name for name, t in traits.items()
                    if t.confidence > 0.5 and t.value > 0.6
                ]
                personality_context[p.child_id] = {
                    "dominant_traits": dominant,
                    "fears": p.fears,
                    "preferred_themes": p.preferred_themes,
                }
        except Exception as e:
            logger.error("Building personality context failed: %s", e)

        try:
            if relationship is None:
                pair_id = ":".join(sorted([child1_id, child2_id]))
                relationship = await self.relationship_mapper.load_model(pair_id)
            relationship_context = {
                "leadership_balance": relationship.leadership_balance,
                "cooperation_score": relationship.cooperation_score,
                "emotional_synchrony": relationship.emotional_synchrony,
                "recent_conflicts": [
                    ce.description for ce in relationship.conflict_events[-3:]
                ],
            }
        except Exception as e:
            logger.error("Building relationship context failed: %s", e)

        try:
            if skill_map is not None and skill_map.has_pairs():
                skill_map_context = {
                    "complementary_pairs": [
                        {
                            "strength_holder": cp.strength_holder_id,
                            "growth_holder": cp.growth_area_holder_id,
                            "trait": cp.trait_dimension,
                            "scenario": cp.suggested_scenario,
                        }
                        for cp in skill_map.complementary_pairs
                    ]
                }
        except Exception as e:
            logger.error("Building skill map context failed: %s", e)

        try:
            from app.services.narrative_directives import build_narrative_directives

            p1 = profile1 or await self.personality_engine.load_profile(child1_id)
            p2 = profile2 or await self.personality_engine.load_profile(child2_id)
            rel = relationship or await self.relationship_mapper.load_model(
                ":".join(sorted([child1_id, child2_id]))
            )

            # Build current emotions map from event
            current_emotions: Dict[str, str] = {}
            if event.emotions:
                for er in event.emotions:
                    if er.face_id == 0:
                        current_emotions[child1_id] = er.emotion.value
                    elif er.face_id == 1:
                        current_emotions[child2_id] = er.emotion.value

            narrative_dirs = build_narrative_directives(
                profiles=(p1, p2),
                relationship=rel,
                skill_map=skill_map,
                current_emotions=current_emotions,
                previous_protagonists=self._protagonist_history,
            )

            # Track protagonist for alternation
            if narrative_dirs and narrative_dirs.get("protagonist_child_id"):
                self._protagonist_history.append(
                    narrative_dirs["protagonist_child_id"]
                )
        except Exception as e:
            logger.error("Layer 4 (narrative directives) failed: %s", e)

        # Generate the story moment via the storyteller
        story_context = {
            "characters": characters,
            "session_id": event.session_id,
            "language": language,
        }

        user_input = (
            event.transcript.text
            if not event.transcript.is_empty
            else None
        )

        result = await self.storyteller.generate_story_segment(
            context=story_context,
            user_input=user_input,
            personality_context=personality_context,
            relationship_context=relationship_context,
            skill_map_context=skill_map_context,
            narrative_directives=narrative_dirs,
        )

        return result

    async def end_session(
        self, session_id: str, sibling_pair_id: str
    ) -> dict:
        """Persist profiles, compute Sibling_Dynamics_Score, generate summary.

        Saves whatever data is available even if score computation fails
        (Req 8.1, 9.1, 9.2, 9.3, 9.4).
        """
        await self._ensure_db_initialized()

        score = 0.0
        summary = ""
        suggestion = None

        # Compute session score (Req 9.1)
        try:
            score = await self.relationship_mapper.compute_session_score(
                sibling_pair_id
            )
        except Exception as e:
            logger.error("end_session: score computation failed: %s", e)

        # Generate plain-language summary (Req 9.2, 9.3, 9.4)
        try:
            summary = await self.relationship_mapper.generate_summary(
                sibling_pair_id
            )
            # Extract suggestion if present (Req 9.4)
            if "Suggestion:" in summary:
                parts = summary.split("Suggestion:", 1)
                summary = parts[0].strip()
                suggestion = "Suggestion:" + parts[1].strip()
        except Exception as e:
            logger.error("end_session: summary generation failed: %s", e)

        # Persist session summary to DB (Req 8.1)
        try:
            await self._sibling_db.save_session_summary(
                session_id=session_id,
                pair_id=sibling_pair_id,
                score=score,
                summary=summary,
                suggestion=suggestion,
            )
        except Exception as e:
            logger.error("end_session: saving summary failed: %s", e)

        # ── Extract and persist world state (Req 2.1-2.5, 4.1, 4.3, 9.1) ──
        try:
            # Retrieve session moments from memory agent
            session_moments: list[dict] = []
            if self.memory.enabled:
                results = self.memory.story_memories.get(
                    where={"session_id": session_id}
                )
                if results and results.get("metadatas"):
                    session_moments = results["metadatas"]

            if session_moments:
                changes = await self._world_extractor.extract(session_moments)

                # Persist new locations
                for loc in changes.get("new_locations", []):
                    await self._world_db.save_location(
                        sibling_pair_id,
                        loc.get("name", "Unknown"),
                        loc.get("description", ""),
                        loc.get("state", "discovered"),
                    )

                # Persist new NPCs
                for npc in changes.get("new_npcs", []):
                    await self._world_db.save_npc(
                        sibling_pair_id,
                        npc.get("name", "Unknown"),
                        npc.get("description", ""),
                        npc.get("relationship_level", 1),
                    )

                # Persist new items
                for item in changes.get("new_items", []):
                    await self._world_db.save_item(
                        sibling_pair_id,
                        item.get("name", "Unknown"),
                        item.get("description", ""),
                        session_id,
                    )

                # Apply location updates
                for upd in changes.get("location_updates", []):
                    loc_name = upd.get("name", "")
                    if loc_name:
                        locs = await self._world_db.load_locations(sibling_pair_id)
                        for loc in locs:
                            if loc["name"] == loc_name:
                                await self._world_db.update_location_state(
                                    loc["id"],
                                    upd.get("new_state", loc["state"]),
                                    upd.get("new_description", loc["description"]),
                                )
                                break

                # Apply NPC relationship updates
                for upd in changes.get("npc_updates", []):
                    npc_name = upd.get("name", "")
                    if npc_name:
                        npcs = await self._world_db.load_npcs(sibling_pair_id)
                        for npc in npcs:
                            if npc["name"] == npc_name:
                                await self._world_db.update_npc_relationship(
                                    npc["id"],
                                    upd.get("relationship_level", npc["relationship_level"]),
                                )
                                break

                # Invalidate cache so next session picks up fresh state
                self._world_state_cache.pop(sibling_pair_id, None)

                logger.info(
                    "end_session: world state persisted for %s — %d locs, %d npcs, %d items, %d loc_upd, %d npc_upd",
                    sibling_pair_id,
                    len(changes.get("new_locations", [])),
                    len(changes.get("new_npcs", [])),
                    len(changes.get("new_items", [])),
                    len(changes.get("location_updates", [])),
                    len(changes.get("npc_updates", [])),
                )
        except Exception as e:
            logger.error("end_session: world state extraction failed: %s", e)

        # ── Archive story to gallery ──────────────────────────────
        storybook_id = None
        try:
            snapshot = await SessionService(self._db_conn).load_snapshot(sibling_pair_id)
            if snapshot is None:
                logger.warning("end_session: no snapshot found for %s — skipping archival", sibling_pair_id)
            elif not snapshot.get("story_history"):
                logger.warning("end_session: empty story_history for %s — skipping archival", sibling_pair_id)
            else:
                story_history = snapshot["story_history"]
                session_metadata = snapshot.get("session_metadata") or {}
                language = session_metadata.get("language", "en")
                duration_seconds = session_metadata.get("session_duration_seconds", 0)

                beats = transform_beats(story_history)
                title = generate_story_title(beats[0].get("narration"))

                record = await StoryArchiveService(self._db_conn).archive_story(
                    sibling_pair_id, title, language, beats, duration_seconds
                )
                if record is not None:
                    storybook_id = record.storybook_id
        except Exception as e:
            logger.error("end_session: story archival failed: %s", e)

        return {
            "session_id": session_id,
            "sibling_pair_id": sibling_pair_id,
            "sibling_dynamics_score": score,
            "summary": summary,
            "suggestion": suggestion,
            "storybook_id": storybook_id,
        }

    def _resolve_perspective_emotion(
        self,
        emotions: list[EmotionResult],
        characters: Dict,
    ) -> str:
        """
        When two faces are detected with different emotions, return the emotion
        of the child whose name matches the current story perspective.

        Falls back to the highest-confidence emotion if no name match is found.
        """
        # Build a mapping of face_id -> character name from the characters dict.
        # Convention: face_id 0 → child1, face_id 1 → child2
        child_names: Dict[int, str] = {}
        for idx, key in enumerate(("child1", "child2")):
            child = characters.get(key, {})
            name = child.get("name", "")
            if name:
                child_names[idx] = name.lower()

        # Determine the current perspective character (defaults to child1)
        perspective_name = (
            characters.get("current_perspective", "")
            or characters.get("child1", {}).get("name", "")
        ).lower()

        # Find the emotion for the perspective child
        for emotion_result in emotions:
            face_name = child_names.get(emotion_result.face_id, "")
            if face_name == perspective_name:
                return emotion_result.emotion.value

        # Fallback: highest confidence
        best = max(emotions, key=lambda e: e.confidence)
        return best.emotion.value

    
    def _extract_setting(self, text: str) -> str:
        """Extract setting from story text"""
        text_lower = text.lower()
        if "forest" in text_lower:
            return "magical forest"
        elif "castle" in text_lower:
            return "enchanted castle"
        elif "mountain" in text_lower:
            return "mystical mountains"
        elif "ocean" in text_lower or "sea" in text_lower:
            return "crystal ocean"
        elif "sky" in text_lower or "cloud" in text_lower:
            return "floating sky islands"
        else:
            return "magical realm"
    
    def _extract_key_objects(self, text: str) -> str:
        """Extract key objects from story"""
        objects = []
        keywords = [
            "portal", "treasure", "sword", "wand", "crystal", 
            "dragon", "owl", "phoenix", "unicorn", "lion",
            "tree", "star", "moon", "sun", "flower"
        ]
        
        text_lower = text.lower()
        for keyword in keywords:
            if keyword in text_lower:
                objects.append(keyword)
        
        return ", ".join(objects[:3]) if objects else "magical sparkles"
    
    def _extract_dialogues(self, text: str) -> List[Dict]:
        """Extract character dialogues from story text"""
        dialogues = []
        
        # Simple quoted text extraction
        if '"' in text:
            parts = text.split('"')
            for i in range(1, len(parts), 2):
                if parts[i].strip():
                    dialogues.append({
                        "character": "character",
                        "text": parts[i].strip(),
                        "emotion": "neutral"
                    })
        
        return dialogues
    
    def _extract_lesson(self, text: str) -> str:
        """Extract moral/lesson from story"""
        themes = {
            "brave": "courage",
            "courage": "courage",
            "kind": "kindness",
            "kindness": "kindness",
            "share": "sharing",
            "sharing": "sharing",
            "help": "helping others",
            "friend": "friendship",
            "friendship": "friendship",
            "honest": "honesty",
            "truth": "honesty",
            "teamwork": "teamwork",
            "together": "teamwork"
        }
        
        text_lower = text.lower()
        for keyword, theme in themes.items():
            if keyword in text_lower:
                return theme
        
        return "adventure"


# Global instance
orchestrator = AgentOrchestrator()