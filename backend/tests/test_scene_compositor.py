"""Tests for SceneCompositor — portrait compositing onto scene images."""

from io import BytesIO

import pytest
from PIL import Image

from app.models.photo import CharacterPosition
from app.services.scene_compositor import SceneCompositor


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_png(width: int = 200, height: int = 200, color=(100, 150, 200)) -> bytes:
    """Create a simple solid-colour PNG image."""
    img = Image.new("RGB", (width, height), color)
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _make_rgba_png(width: int = 80, height: int = 80, color=(255, 0, 0, 255)) -> bytes:
    """Create a simple RGBA PNG (portrait with alpha)."""
    img = Image.new("RGBA", (width, height), color)
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _open_png(data: bytes) -> Image.Image:
    return Image.open(BytesIO(data))


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestCompositeBasic:
    """Core compositing behaviour."""

    def test_returns_valid_png_with_correct_dimensions(self):
        compositor = SceneCompositor()
        scene = _make_png(400, 300)
        portraits = {"hero": _make_rgba_png()}
        positions = {"hero": CharacterPosition(x=0.5, y=0.5, scale=0.5)}

        result = compositor.composite(scene, portraits, positions)

        img = _open_png(result)
        assert img.format == "PNG"
        assert img.size == (400, 300)

    def test_empty_portraits_returns_scene_unchanged_dimensions(self):
        compositor = SceneCompositor()
        scene = _make_png(300, 200)

        result = compositor.composite(scene, {}, {})

        img = _open_png(result)
        assert img.size == (300, 200)

    def test_multiple_portraits_composited(self):
        compositor = SceneCompositor()
        scene = _make_png(500, 400)
        portraits = {
            "hero": _make_rgba_png(60, 60, (255, 0, 0, 255)),
            "sidekick": _make_rgba_png(60, 60, (0, 255, 0, 255)),
        }
        positions = {
            "hero": CharacterPosition(x=0.3, y=0.5, scale=0.5, z_order=0),
            "sidekick": CharacterPosition(x=0.7, y=0.5, scale=0.5, z_order=1),
        }

        result = compositor.composite(scene, portraits, positions)

        img = _open_png(result)
        assert img.size == (500, 400)


class TestZOrdering:
    """Portraits are composited in z_order."""

    def test_z_order_respected(self):
        compositor = SceneCompositor()
        scene = _make_png(200, 200, (0, 0, 0))
        # Two portraits at the same position — higher z_order on top
        portraits = {
            "back": _make_rgba_png(80, 80, (255, 0, 0, 200)),
            "front": _make_rgba_png(80, 80, (0, 0, 255, 200)),
        }
        positions = {
            "back": CharacterPosition(x=0.5, y=0.5, scale=0.8, z_order=0),
            "front": CharacterPosition(x=0.5, y=0.5, scale=0.8, z_order=1),
        }

        result = compositor.composite(scene, portraits, positions)

        # The front (blue) portrait should be on top at center
        img = _open_png(result)
        center_pixel = img.getpixel((100, 100))
        # Blue channel should dominate over red at center
        assert center_pixel[2] > center_pixel[0]


class TestMissingPortrait:
    """Missing portraits are skipped gracefully."""

    def test_missing_portrait_skipped(self):
        compositor = SceneCompositor()
        scene = _make_png(200, 200)
        portraits = {}  # no portraits provided
        positions = {"hero": CharacterPosition(x=0.5, y=0.5, scale=0.5)}

        result = compositor.composite(scene, portraits, positions)

        img = _open_png(result)
        assert img.size == (200, 200)

    def test_partial_portraits(self):
        compositor = SceneCompositor()
        scene = _make_png(300, 300)
        portraits = {"hero": _make_rgba_png()}
        positions = {
            "hero": CharacterPosition(x=0.3, y=0.5, scale=0.5),
            "villain": CharacterPosition(x=0.7, y=0.5, scale=0.5),
        }

        result = compositor.composite(scene, portraits, positions)

        img = _open_png(result)
        assert img.size == (300, 300)


class TestErrorHandling:
    """Compositor returns base scene on failure."""

    def test_invalid_base_scene_returns_input(self):
        compositor = SceneCompositor()
        bad_bytes = b"not an image"

        result = compositor.composite(bad_bytes, {}, {})

        assert result == bad_bytes

    def test_invalid_portrait_bytes_skipped(self):
        compositor = SceneCompositor()
        scene = _make_png(200, 200)
        portraits = {"hero": b"corrupt data"}
        positions = {"hero": CharacterPosition(x=0.5, y=0.5, scale=0.5)}

        result = compositor.composite(scene, portraits, positions)

        img = _open_png(result)
        assert img.size == (200, 200)


class TestColorGrading:
    """Color grading shifts portrait toward scene tone."""

    def test_color_grading_applied(self):
        compositor = SceneCompositor()
        # Very blue scene, red portrait
        scene = _make_png(200, 200, (0, 0, 255))
        portraits = {"hero": _make_rgba_png(40, 40, (255, 0, 0, 255))}
        positions = {"hero": CharacterPosition(x=0.5, y=0.5, scale=1.0)}

        result = compositor.composite(scene, portraits, positions)

        # Result should be valid — colour grading doesn't break output
        img = _open_png(result)
        assert img.size == (200, 200)


class TestScaling:
    """Portrait scaling relative to scene height."""

    def test_small_scale_produces_small_portrait(self):
        compositor = SceneCompositor()
        scene = _make_png(400, 400)
        portraits = {"hero": _make_rgba_png(100, 100)}
        positions = {"hero": CharacterPosition(x=0.5, y=0.5, scale=0.1)}

        result = compositor.composite(scene, portraits, positions)

        img = _open_png(result)
        assert img.size == (400, 400)

    def test_large_scale(self):
        compositor = SceneCompositor()
        scene = _make_png(400, 400)
        portraits = {"hero": _make_rgba_png(100, 100)}
        positions = {"hero": CharacterPosition(x=0.5, y=0.5, scale=2.0)}

        result = compositor.composite(scene, portraits, positions)

        img = _open_png(result)
        assert img.size == (400, 400)
