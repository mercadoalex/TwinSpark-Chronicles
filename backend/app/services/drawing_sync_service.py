"""Service for validating, serializing, and broadcasting drawing strokes.

Handles real-time stroke synchronization between siblings during
collaborative drawing sessions, including validation, JSON
serialization/deserialization, duration clamping, and default color
assignment.
"""

from __future__ import annotations

import json
import re

from app.models.drawing import REQUIRED_FIELDS, StrokeMessage

# 8 child-friendly colors that meet >= 3:1 contrast ratio against #FFFFFF.
PALETTE_COLORS: list[str] = [
    "#E53935",  # red          – 4.0:1
    "#D81B60",  # pink         – 4.5:1
    "#8E24AA",  # purple       – 5.3:1
    "#1E88E5",  # blue         – 3.6:1
    "#00897B",  # teal         – 3.2:1
    "#43A047",  # green        – 3.1:1
    "#F4511E",  # deep orange  – 3.5:1
    "#6D4C41",  # brown        – 5.1:1
]

_HEX_COLOR_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")
_VALID_SIBLING_IDS = {"child1", "child2"}

_MIN_DURATION = 30
_MAX_DURATION = 120

_DEFAULT_COLORS: dict[str, str] = {
    "child1": "#E53935",  # red
    "child2": "#1E88E5",  # blue
}


class DrawingSyncService:
    """Validates, serializes, and manages drawing stroke data."""

    def validate_stroke(self, data: dict) -> StrokeMessage | None:
        """Validate incoming stroke dict.

        Returns a parsed ``StrokeMessage`` when *data* is well-formed,
        or ``None`` on any validation failure — never raises.
        """
        try:
            # All required fields must be present
            if not REQUIRED_FIELDS.issubset(data):
                return None

            # sibling_id must be child1 or child2
            if data["sibling_id"] not in _VALID_SIBLING_IDS:
                return None

            # points must be a non-empty list of {x, y} dicts
            points = data["points"]
            if not isinstance(points, list) or len(points) == 0:
                return None
            for pt in points:
                if not isinstance(pt, dict) or "x" not in pt or "y" not in pt:
                    return None

            # color must be a valid hex string
            color = data["color"]
            if not isinstance(color, str) or not _HEX_COLOR_RE.match(color):
                return None

            # brush_size must be a positive integer
            brush_size = data["brush_size"]
            if not isinstance(brush_size, int) or brush_size <= 0:
                return None

            return StrokeMessage(
                session_id=data["session_id"],
                sibling_id=data["sibling_id"],
                points=points,
                color=color,
                brush_size=brush_size,
                timestamp=data["timestamp"],
                tool=data.get("tool", "brush"),
                stamp_shape=data.get("stamp_shape"),
            )
        except Exception:
            return None

    def serialize_stroke(self, stroke: StrokeMessage) -> str:
        """Convert a ``StrokeMessage`` to a JSON string."""
        payload: dict = {
            "session_id": stroke.session_id,
            "sibling_id": stroke.sibling_id,
            "points": stroke.points,
            "color": stroke.color,
            "brush_size": stroke.brush_size,
            "timestamp": stroke.timestamp,
            "tool": stroke.tool,
            "stamp_shape": stroke.stamp_shape,
        }
        return json.dumps(payload, separators=(",", ":"), sort_keys=True)

    def deserialize_stroke(self, json_str: str) -> StrokeMessage | None:
        """Parse a JSON string into a ``StrokeMessage``.

        Returns ``None`` when the string is not valid JSON or fails
        stroke validation.
        """
        try:
            data = json.loads(json_str)
        except (json.JSONDecodeError, TypeError):
            return None
        if not isinstance(data, dict):
            return None
        return self.validate_stroke(data)

    @staticmethod
    def clamp_duration(
        requested: int,
        remaining_session_time: int | None = None,
    ) -> int:
        """Clamp *requested* duration to [30, 120], then to remaining time."""
        clamped = max(_MIN_DURATION, min(_MAX_DURATION, requested))
        if remaining_session_time is not None:
            clamped = min(clamped, remaining_session_time)
        return clamped

    @staticmethod
    def get_default_color(sibling_id: str) -> str:
        """Return the default drawing color for *sibling_id*."""
        return _DEFAULT_COLORS.get(sibling_id, PALETTE_COLORS[0])
