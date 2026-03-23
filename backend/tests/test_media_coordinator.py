"""Unit tests for MediaCoordinator."""

import asyncio
import base64
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.agents.coordinators.media_coordinator import MediaCoordinator
from app.services.session_time_enforcer import TimeCheckResult


def _make_mc():
    """Create a MediaCoordinator with mocked dependencies."""
    visual = MagicMock(enabled=False)
    style_transfer = MagicMock()
    compositor = MagicMock()
    return MediaCoordinator(visual, style_transfer, compositor)


CHARACTERS = {"child1": {"name": "Ale"}, "child2": {"name": "Sofi"}}


class TestGenerateScene:
    """generate_scene handles disabled visual, compositing, and fallback."""

    @pytest.mark.asyncio
    async def test_returns_none_when_disabled(self):
        mc = _make_mc()
        db = MagicMock()
        db.fetch_all = AsyncMock(return_value=[])
        result = await mc.generate_scene(
            {"text": "story"}, CHARACTERS, "s1", "Ale:Sofi", db,
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_scene_when_enabled(self):
        mc = _make_mc()
        mc.visual.enabled = True
        mc.visual.generate_scene_image = AsyncMock(return_value="base64img")
        db = MagicMock()
        db.fetch_all = AsyncMock(return_value=[])
        result = await mc.generate_scene(
            {"text": "forest story"}, CHARACTERS, "s1", "Ale:Sofi", db,
        )
        assert result == "base64img"

    @pytest.mark.asyncio
    async def test_compositor_failure_returns_base_scene(self):
        mc = _make_mc()
        mc.visual.enabled = True
        scene_b64 = base64.b64encode(b"scene").decode()
        mc.visual.generate_scene_image = AsyncMock(return_value=scene_b64)
        mc._scene_compositor.composite = MagicMock(side_effect=Exception("comp fail"))

        portrait_b64 = base64.b64encode(b"portrait").decode()
        mc._style_transfer.generate_portraits_for_session = AsyncMock(
            return_value={"child1": portrait_b64}
        )

        db = MagicMock()
        db.fetch_all = AsyncMock(return_value=[
            {"mapping_id": "m1", "sibling_pair_id": "Ale:Sofi",
             "character_role": "child1", "face_id": "f1", "created_at": "2024-01-01"},
        ])

        result = await mc.generate_scene(
            {"text": "story"}, CHARACTERS, "s1", "Ale:Sofi", db,
        )
        # Falls back to base scene (not composited)
        assert result == scene_b64


class TestInjectDrawingPrompt:
    """inject_drawing_prompt sends DRAWING_PROMPT with clamped duration."""

    @pytest.mark.asyncio
    async def test_sends_prompt_when_present(self):
        mc = _make_mc()
        session_coord = MagicMock()
        session_coord.ws_manager = MagicMock()
        session_coord.ws_manager.send_story = AsyncMock()
        session_coord.session_time_enforcer = None

        segment = {"text": "story", "drawing_prompt": "Draw a tree!", "drawing_duration": 60}

        with patch("asyncio.create_task", return_value=MagicMock()):
            await mc.inject_drawing_prompt("s1", segment, session_coord)

        calls = [c for c in session_coord.ws_manager.send_story.call_args_list
                 if c[0][1].get("type") == "DRAWING_PROMPT"]
        assert len(calls) == 1
        assert calls[0][0][1]["duration"] == 60

    @pytest.mark.asyncio
    async def test_skips_when_no_prompt(self):
        mc = _make_mc()
        session_coord = MagicMock()
        session_coord.ws_manager = MagicMock()
        session_coord.ws_manager.send_story = AsyncMock()
        await mc.inject_drawing_prompt("s1", {"text": "story"}, session_coord)
        session_coord.ws_manager.send_story.assert_not_called()

    @pytest.mark.asyncio
    async def test_skips_when_ws_none(self):
        mc = _make_mc()
        session_coord = MagicMock()
        session_coord.ws_manager = None
        segment = {"text": "story", "drawing_prompt": "Draw!"}
        await mc.inject_drawing_prompt("s1", segment, session_coord)  # no raise


class TestTextExtraction:
    """extract_setting and extract_key_objects helpers."""

    def test_extract_setting_forest(self):
        mc = _make_mc()
        assert mc.extract_setting("They entered the dark forest") == "magical forest"

    def test_extract_setting_default(self):
        mc = _make_mc()
        assert mc.extract_setting("Something happened") == "magical realm"

    def test_extract_key_objects(self):
        mc = _make_mc()
        result = mc.extract_key_objects("The dragon guarded the crystal portal")
        assert "dragon" in result
        assert "crystal" in result
        assert "portal" in result

    def test_extract_key_objects_default(self):
        mc = _make_mc()
        assert mc.extract_key_objects("Nothing special") == "magical sparkles"
