"""MediaCoordinator — visual/media pipeline: scenes, compositing, drawing prompts."""

import asyncio
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class MediaCoordinator:
    """Owns scene generation, photo compositing, and drawing prompt injection."""

    def __init__(self, visual_agent, style_transfer, scene_compositor) -> None:
        self.visual = visual_agent
        self._style_transfer = style_transfer
        self._scene_compositor = scene_compositor

    async def generate_scene(
        self,
        story_segment: Dict,
        characters: Dict,
        session_id: str,
        sibling_pair_id: str,
        db_conn,
    ) -> Optional[str]:
        """Generate scene image with optional photo portrait compositing."""
        # Load photo portraits for compositing
        photo_portraits = {}
        try:
            mappings = await db_conn.fetch_all(
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
                    db=db_conn,
                )
                if photo_portraits:
                    print(f"📸 Photo portraits ready: {len(photo_portraits)} characters")
        except Exception as e:
            logger.warning("Photo pipeline skipped: %s", e)

        scene_image = None
        if not self.visual.enabled:
            return None

        try:
            scene_image = await self.visual.generate_scene_image(
                story_context={
                    "setting": self.extract_setting(story_segment["text"]),
                    "mood": "joyful",
                    "key_objects": self.extract_key_objects(story_segment["text"]),
                },
                child_profiles=characters,
                scene_description=story_segment["text"][:200],
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
            logger.warning("Visual generation skipped: %s", e)

        return scene_image

    async def inject_drawing_prompt(
        self,
        session_id: str,
        story_segment: Dict,
        session_coordinator,
    ) -> None:
        """Send DRAWING_PROMPT to clients if story segment includes one."""
        drawing_prompt = story_segment.get("drawing_prompt")
        if not drawing_prompt or session_coordinator.ws_manager is None:
            return

        try:
            from app.services.drawing_sync_service import DrawingSyncService

            requested_duration = story_segment.get("drawing_duration", 60)
            remaining_seconds = None

            if session_coordinator.session_time_enforcer is not None:
                time_check = session_coordinator.session_time_enforcer.check_time(session_id)
                if time_check.is_expired:
                    await session_coordinator.ws_manager.send_story(session_id, {
                        "type": "DRAWING_END",
                        "session_id": session_id,
                        "reason": "session_expired",
                    })
                    logger.info("Session %s expired — skipping drawing prompt", session_id)
                    return

                remaining_seconds = int(time_check.remaining_seconds)
                effective_duration = DrawingSyncService.clamp_duration(
                    requested_duration, remaining_seconds,
                )
            else:
                effective_duration = DrawingSyncService.clamp_duration(requested_duration)

            await session_coordinator.ws_manager.send_story(session_id, {
                "type": "DRAWING_PROMPT",
                "prompt": drawing_prompt,
                "duration": effective_duration,
                "session_id": session_id,
            })
            logger.info(
                "Drawing prompt sent: session=%s duration=%d prompt=%s",
                session_id, effective_duration, drawing_prompt[:80],
            )

            # Start background watchdog
            asyncio.create_task(
                self.drawing_time_watchdog(session_id, effective_duration, session_coordinator)
            )
        except Exception as e:
            logger.warning("Drawing prompt injection failed: %s", e)

    async def drawing_time_watchdog(
        self, session_id: str, duration: int, session_coordinator,
    ) -> None:
        """Background task that checks session time during an active drawing."""
        _POLL_INTERVAL = 5
        elapsed = 0
        try:
            while elapsed < duration:
                await asyncio.sleep(_POLL_INTERVAL)
                elapsed += _POLL_INTERVAL

                if session_coordinator.session_time_enforcer is None:
                    break

                time_check = session_coordinator.session_time_enforcer.check_time(session_id)
                if time_check.is_expired:
                    logger.info(
                        "Drawing watchdog: session %s expired mid-drawing at %ds",
                        session_id, elapsed,
                    )
                    if session_coordinator.ws_manager is not None:
                        await session_coordinator.ws_manager.send_story(session_id, {
                            "type": "DRAWING_END",
                            "session_id": session_id,
                            "reason": "session_expired",
                        })
                    return
        except asyncio.CancelledError:
            logger.debug("Drawing watchdog cancelled for session %s", session_id)
        except Exception as e:
            logger.warning("Drawing watchdog error for session %s: %s", session_id, e)

    def extract_setting(self, text: str) -> str:
        """Extract setting from story text."""
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

    def extract_key_objects(self, text: str) -> str:
        """Extract key objects from story text."""
        objects = []
        keywords = [
            "portal", "treasure", "sword", "wand", "crystal",
            "dragon", "owl", "phoenix", "unicorn", "lion",
            "tree", "star", "moon", "sun", "flower",
        ]
        text_lower = text.lower()
        for keyword in keywords:
            if keyword in text_lower:
                objects.append(keyword)
        return ", ".join(objects[:3]) if objects else "magical sparkles"
