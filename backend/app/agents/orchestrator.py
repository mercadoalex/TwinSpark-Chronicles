"""
Agent Orchestrator
Coordinates all AI agents to create rich multimodal story experiences.

Extended with sibling dynamics pipeline (Layers 1-4) that processes
personality, relationship, skills, and narrative directives in sequence.

Requirements: 8.1, 9.1, 9.2, 9.3, 9.4, 11.1, 11.4, 11.5
"""

import logging
from typing import Dict, Optional, List
from datetime import datetime

from app.models.multimodal import MultimodalInputEvent, EmotionCategory, EmotionResult

logger = logging.getLogger(__name__)


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

        self._sibling_db = SiblingDB()
        self._db_initialized = False
        self.personality_engine = PersonalityEngine(self._sibling_db)
        self.relationship_mapper = RelationshipMapper(self._sibling_db)
        self.skills_discoverer = ComplementarySkillsDiscoverer(self._sibling_db)

        # Track protagonist history for narrative directive alternation
        self._protagonist_history: list[str] = []

        print("🎭 Agent orchestrator initialized")
    
    async def generate_rich_story_moment(self, session_id: str, characters: Dict, user_input: Optional[str] = None, language: str = "en", **kwargs) -> Dict:
        """Generate a complete multimodal story moment with all agents."""
        print(f"\n🎬 Generating rich story moment for session {session_id}")
        
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
        
        # STEP 2: Generate story with context
        story_context = {
            "characters": characters,
            "session_id": session_id,
            "language": language,
            "memories": memories,
            **kwargs
        }
        
        story_segment = await self.storyteller.generate_story_segment(
            context=story_context,
            user_input=user_input
        )
        
        print(f"📖 Story text generated: {len(story_segment['text'])} chars")
        
        # STEP 3: Generate scene illustration (if enabled)
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
        return {
            "text": story_segment['text'],
            "image": scene_image,
            "audio": {
                "narration": narration_audio,
                "character_voices": character_voices
            },
            "interactive": story_segment.get('interactive', {}),
            "timestamp": story_segment.get('timestamp'),
            "memories_used": len(memories),
            "agents_used": {
                "storyteller": True,
                "visual": scene_image is not None,
                "voice": narration_audio is not None,
                "memory": len(memories) > 0
            }
        }

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
        """Lazily initialize the SiblingDB on first use."""
        if not self._db_initialized:
            await self._sibling_db.initialize()
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

        return {
            "session_id": session_id,
            "sibling_pair_id": sibling_pair_id,
            "sibling_dynamics_score": score,
            "summary": summary,
            "suggestion": suggestion,
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