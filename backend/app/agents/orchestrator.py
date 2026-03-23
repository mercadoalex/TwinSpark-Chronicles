"""
Agent Orchestrator (Facade)
Thin facade that delegates to focused coordinators while preserving
the existing public API for main.py, WebSocket handlers, and all tests.

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

from app.agents.coordinators import (
    SessionCoordinator,
    StoryCoordinator,
    WorldCoordinator,
    MediaCoordinator,
)
from app.data.costume_catalog import get_costume_prompt

logger = logging.getLogger(__name__)

MAX_CONTENT_RETRIES = 3


class AgentOrchestrator:
    """
    Thin facade coordinating four focused coordinators, plus the
    cross-cutting Sibling Dynamics Engine pipeline (Layers 1-4).
    """

    def __init__(self):
        # Import agents here to avoid circular imports
        from .storyteller_agent import storyteller
        from .visual_agent import visual_agent
        from .voice_agent import voice_agent
        from .memory_agent import memory_agent

        # Sibling dynamics services (Layer 1-3) — remain on facade (cross-cutting)
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

        # ── Initialize coordinators ──────────────────────────────

        # Session coordinator
        self.session = SessionCoordinator()

        # Story coordinator
        self.story = StoryCoordinator(
            storyteller=storyteller,
            content_filter=ContentFilter(),
            memory_agent=memory_agent,
            voice_agent=voice_agent,
            playback_integrator=None,
        )

        # World coordinator
        from app.services.world_db import WorldDB
        from app.services.world_state_extractor import WorldStateExtractor
        from app.services.world_context_formatter import WorldContextFormatter
        from app.db.world_repository import WorldRepository

        world_repo = WorldRepository(self._db_conn)
        self.world = WorldCoordinator(
            world_db=WorldDB(self._db_conn, world_repo=world_repo),
            world_extractor=WorldStateExtractor(),
            world_context_formatter=WorldContextFormatter(),
        )

        # Media coordinator
        from app.agents.style_transfer_agent import StyleTransferAgent
        from app.services.scene_compositor import SceneCompositor

        self.media = MediaCoordinator(
            visual_agent=visual_agent,
            style_transfer=StyleTransferAgent(),
            scene_compositor=SceneCompositor(),
        )

        print("🎭 Agent orchestrator initialized")

    # ── Backward-compatible property accessors ────────────────────

    @property
    def storyteller(self):
        if hasattr(self, 'story'):
            return self.story.storyteller
        return self.__dict__.get('_storyteller')

    @storyteller.setter
    def storyteller(self, value):
        if hasattr(self, 'story'):
            self.story.storyteller = value
        self.__dict__['_storyteller'] = value

    @property
    def visual(self):
        if hasattr(self, 'media'):
            return self.media.visual
        return self.__dict__.get('_visual')

    @visual.setter
    def visual(self, value):
        if hasattr(self, 'media'):
            self.media.visual = value
        self.__dict__['_visual'] = value

    @property
    def voice(self):
        if hasattr(self, 'story'):
            return self.story.voice
        return self.__dict__.get('_voice')

    @voice.setter
    def voice(self, value):
        if hasattr(self, 'story'):
            self.story.voice = value
        self.__dict__['_voice'] = value

    @property
    def memory(self):
        if hasattr(self, 'story'):
            return self.story.memory
        return self.__dict__.get('_memory')

    @memory.setter
    def memory(self, value):
        if hasattr(self, 'story'):
            self.story.memory = value
        self.__dict__['_memory'] = value

    @property
    def session_time_enforcer(self):
        if hasattr(self, 'session'):
            return self.session.session_time_enforcer
        return self.__dict__.get('_session_time_enforcer')

    @session_time_enforcer.setter
    def session_time_enforcer(self, value):
        if hasattr(self, 'session'):
            self.session.session_time_enforcer = value
        self.__dict__['_session_time_enforcer'] = value

    @property
    def ws_manager(self):
        if hasattr(self, 'session'):
            return self.session.ws_manager
        return self.__dict__.get('_ws_manager')

    @ws_manager.setter
    def ws_manager(self, value):
        if hasattr(self, 'session'):
            self.session.ws_manager = value
        self.__dict__['_ws_manager'] = value

    @property
    def _session_tasks(self):
        if hasattr(self, 'session'):
            return self.session._session_tasks
        return self.__dict__.get('__session_tasks', {})

    @property
    def _world_db(self):
        if hasattr(self, 'world'):
            return self.world.world_db
        return self.__dict__.get('__world_db')

    @_world_db.setter
    def _world_db(self, value):
        if hasattr(self, 'world'):
            self.world._world_db = value
        self.__dict__['__world_db'] = value

    @property
    def _world_state_cache(self):
        if hasattr(self, 'world'):
            return self.world._world_state_cache
        return self.__dict__.get('__world_state_cache', {})

    @_world_state_cache.setter
    def _world_state_cache(self, value):
        if hasattr(self, 'world'):
            self.world._world_state_cache = value
        self.__dict__['__world_state_cache'] = value

    @property
    def _world_extractor(self):
        if hasattr(self, 'world'):
            return self.world._world_extractor
        return self.__dict__.get('__world_extractor')

    @_world_extractor.setter
    def _world_extractor(self, value):
        if hasattr(self, 'world'):
            self.world._world_extractor = value
        self.__dict__['__world_extractor'] = value

    @property
    def content_filter(self):
        if hasattr(self, 'story'):
            return self.story.content_filter
        return self.__dict__.get('_content_filter')

    @content_filter.setter
    def content_filter(self, value):
        if hasattr(self, 'story'):
            self.story.content_filter = value
        self.__dict__['_content_filter'] = value

    @property
    def _playback_integrator(self):
        if hasattr(self, 'story'):
            return self.story.playback_integrator
        return self.__dict__.get('__playback_integrator')

    @_playback_integrator.setter
    def _playback_integrator(self, value):
        if hasattr(self, 'story'):
            self.story.playback_integrator = value
        self.__dict__['__playback_integrator'] = value

    # ── Delegated public methods ──────────────────────────────────

    async def cancel_session(self, session_id: str) -> Dict:
        """Cancel all in-flight tasks for a session. Delegates to SessionCoordinator."""
        return await self.session.cancel_session(session_id)

    def _generate_safe_story_segment(self, *args, **kwargs):
        """Delegate to StoryCoordinator."""
        return self.story.generate_safe_story_segment(*args, **kwargs)

    def _filter_text(self, *args, **kwargs):
        """Delegate to StoryCoordinator."""
        return self.story.filter_text(*args, **kwargs)

    def _extract_setting(self, text: str) -> str:
        """Delegate to MediaCoordinator."""
        return self.media.extract_setting(text)

    def _extract_key_objects(self, text: str) -> str:
        """Delegate to MediaCoordinator."""
        return self.media.extract_key_objects(text)

    def _extract_dialogues(self, text: str) -> List[Dict]:
        """Delegate to StoryCoordinator."""
        return self.story.extract_dialogues(text)

    def _extract_lesson(self, text: str) -> str:
        """Delegate to StoryCoordinator."""
        return self.story.extract_lesson(text)

    async def _drawing_time_watchdog(self, session_id: str, duration: int) -> None:
        """Delegate to MediaCoordinator."""
        await self.media.drawing_time_watchdog(session_id, duration, self.session)

    # ── Main story generation (delegates to coordinators) ─────────

    async def generate_rich_story_moment(self, session_id: str, characters: Dict, user_input: Optional[str] = None, language: str = "en", **kwargs) -> Dict:
        """Generate a complete multimodal story moment with all agents."""
        print(f"\n🎬 Generating rich story moment for session {session_id}")

        # Check session time before generation
        if self.session.session_time_enforcer is not None:
            time_check = self.session.session_time_enforcer.check_time(session_id)
            if time_check.is_expired:
                logger.info("Session %s time expired — skipping generation", session_id)
                await self.session.notify_session_expired(session_id)
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

        # Signal generation pause start
        self.session.start_generation_pause(session_id)
        await self.session.notify_generation_started(session_id)

        # Enrich characters with costume_prompt from catalog
        for child_key in ("child1", "child2"):
            child = characters.get(child_key, {})
            if "costume_prompt" not in child:
                child["costume_prompt"] = get_costume_prompt(child.get("costume"))
            characters[child_key] = child

        try:
            return await self._do_generate_rich_story_moment(
                session_id, characters, user_input, language, **kwargs
            )
        finally:
            self.session.end_generation_pause(session_id)
            await self.session.notify_generation_completed(session_id)

    async def _do_generate_rich_story_moment(self, session_id: str, characters: Dict, user_input: Optional[str] = None, language: str = "en", **kwargs) -> Dict:
        """Internal implementation of rich story moment generation."""

        allowed_themes = kwargs.pop("allowed_themes", None)
        complexity_level = kwargs.pop("complexity_level", None)
        custom_blocked_words = kwargs.pop("custom_blocked_words", None)
        drawing_context = kwargs.pop("drawing_context", None)

        # STEP 1: Get relevant memories (StoryCoordinator)
        memories = await self.story.recall_memories(session_id, user_input or "story beginning")
        if memories:
            print(f"🧠 Retrieved {len(memories)} relevant memories")

        # STEP 1b: Load and inject world context (WorldCoordinator)
        child1_name = characters.get("child1", {}).get("name", "child1")
        child2_name = characters.get("child2", {}).get("name", "child2")
        sibling_pair_id = ":".join(sorted([child1_name, child2_name]))

        world_context_str = await self.world.get_world_context(
            sibling_pair_id, user_input or "", self._ensure_db_initialized,
        )

        # STEP 2: Generate story with content filtering (StoryCoordinator)
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
        if drawing_context is not None:
            story_context["drawing_context"] = drawing_context

        try:
            story_segment = await self.story.generate_safe_story_segment(
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

        # STEP 2a: Drawing prompt injection (MediaCoordinator)
        await self.media.inject_drawing_prompt(session_id, story_segment, self.session)

        # STEP 2b: Filter story choices (StoryCoordinator)
        story_segment = self.story.filter_choices(
            story_segment, session_id, allowed_themes, custom_blocked_words,
        )

        # STEP 2c: Voice playback triggers (StoryCoordinator)
        voice_recordings = await self.story.check_voice_playback(
            story_segment, characters, user_input, language,
        )

        # STEP 3: Generate scene illustration (MediaCoordinator)
        await self._ensure_db_initialized()
        scene_image = await self.media.generate_scene(
            story_segment, characters, session_id, sibling_pair_id, self._db_conn,
        )

        # STEP 4: Generate narration audio (StoryCoordinator)
        narration_audio = await self.story.generate_narration(story_segment["text"], language)
        if narration_audio:
            print(f"🎤 Narration: ✅ Generated")

        # STEP 5: Generate character dialogue voices (StoryCoordinator)
        character_voices = await self.story.generate_character_voices(
            story_segment["text"], characters, language,
        )

        # STEP 6: Store this moment in memory (StoryCoordinator)
        await self.story.store_memory(session_id, story_segment["text"], user_input)

        # STEP 7: Return complete multimodal experience
        result = {
            "text": story_segment["text"],
            "image": scene_image,
            "audio": {
                "narration": narration_audio,
                "character_voices": character_voices,
            },
            "interactive": story_segment.get("interactive", {}),
            "timestamp": story_segment.get("timestamp"),
            "memories_used": len(memories),
            "voice_recordings": voice_recordings,
            "agents_used": {
                "storyteller": True,
                "visual": scene_image is not None,
                "voice": narration_audio is not None,
                "memory": len(memories) > 0,
            },
        }

        if drawing_context is not None:
            result["drawing_image_path"] = drawing_context.get("image_path", "")

        return result

    async def process_multimodal_event(
        self,
        event: MultimodalInputEvent,
        characters: Dict,
        language: str = "en",
    ) -> Dict:
        """Process a multimodal input event and generate an adapted story moment."""
        context = event.to_orchestrator_context()
        user_input = context["user_input"]
        detected_emotion = context["emotion"]

        if len(event.emotions) >= 2:
            detected_emotion = self._resolve_perspective_emotion(
                event.emotions, characters
            )

        story_context_extra: Dict = {}
        if detected_emotion != EmotionCategory.NEUTRAL.value:
            story_context_extra["child_emotion"] = detected_emotion
        if detected_emotion == EmotionCategory.SCARED.value:
            story_context_extra["emotion_instruction"] = (
                "The child seems scared. Please reduce the story intensity, "
                "avoid any frightening elements, and introduce comforting, "
                "reassuring story elements."
            )

        result = await self.generate_rich_story_moment(
            session_id=event.session_id,
            characters=characters,
            user_input=user_input,
            language=language,
            **story_context_extra,
        )

        if self.memory.enabled:
            try:
                await self.memory.store_story_moment(
                    session_id=event.session_id,
                    moment_data={
                        "scene": result.get("text", "")[:100],
                        "choice_made": user_input or "multimodal_input",
                        "outcome": result.get("interactive", {}).get("text", ""),
                        "emotion": detected_emotion,
                        "lesson": self.story.extract_lesson(result.get("text", "")),
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
        in try/except for resilience (Req 11.1, 11.5).
        """
        await self._ensure_db_initialized()

        profile1 = None
        profile2 = None
        relationship = None
        skill_map = None
        narrative_dirs = None

        has_usable_data = (
            not event.transcript.is_empty or len(event.emotions) > 0
        )

        if has_usable_data:
            # Layer 1: Personality Engine
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

            # Layer 2: Relationship Mapper
            try:
                p1 = profile1 or await self.personality_engine.load_profile(child1_id)
                p2 = profile2 or await self.personality_engine.load_profile(child2_id)
                relationship = await self.relationship_mapper.update_from_event(
                    event, (p1, p2)
                )
            except Exception as e:
                logger.error("Layer 2 (relationship) failed: %s", e)

            # Layer 3: Complementary Skills Discoverer
            try:
                p1 = profile1 or await self.personality_engine.load_profile(child1_id)
                p2 = profile2 or await self.personality_engine.load_profile(child2_id)
                interaction_count = p1.total_interactions + p2.total_interactions
                skill_map = await self.skills_discoverer.evaluate(
                    (p1, p2), interaction_count
                )
            except Exception as e:
                logger.error("Layer 3 (skills) failed: %s", e)

        # Layer 4: Narrative Directives + Story Generation
        personality_context = None
        relationship_context = None
        skill_map_context = None

        try:
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

            if narrative_dirs and narrative_dirs.get("protagonist_child_id"):
                self._protagonist_history.append(
                    narrative_dirs["protagonist_child_id"]
                )
        except Exception as e:
            logger.error("Layer 4 (narrative directives) failed: %s", e)

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
        """Persist profiles, compute Sibling_Dynamics_Score, generate summary."""
        await self._ensure_db_initialized()

        score = 0.0
        summary = ""
        suggestion = None

        try:
            score = await self.relationship_mapper.compute_session_score(
                sibling_pair_id
            )
        except Exception as e:
            logger.error("end_session: score computation failed: %s", e)

        try:
            summary = await self.relationship_mapper.generate_summary(
                sibling_pair_id
            )
            if "Suggestion:" in summary:
                parts = summary.split("Suggestion:", 1)
                summary = parts[0].strip()
                suggestion = "Suggestion:" + parts[1].strip()
        except Exception as e:
            logger.error("end_session: summary generation failed: %s", e)

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

        # Extract and persist world state (WorldCoordinator)
        try:
            await self.world.extract_and_persist_world_state(
                session_id, sibling_pair_id, self.memory,
            )
        except Exception as e:
            logger.error("end_session: world state extraction failed: %s", e)

        # Archive story to gallery
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
        """When two faces are detected, return the emotion of the perspective child."""
        child_names: Dict[int, str] = {}
        for idx, key in enumerate(("child1", "child2")):
            child = characters.get(key, {})
            name = child.get("name", "")
            if name:
                child_names[idx] = name.lower()

        perspective_name = (
            characters.get("current_perspective", "")
            or characters.get("child1", {}).get("name", "")
        ).lower()

        for emotion_result in emotions:
            face_name = child_names.get(emotion_result.face_id, "")
            if face_name == perspective_name:
                return emotion_result.emotion.value

        best = max(emotions, key=lambda e: e.confidence)
        return best.emotion.value


# Global instance
orchestrator = AgentOrchestrator()
