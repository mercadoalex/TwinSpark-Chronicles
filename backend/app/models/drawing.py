"""Dataclass models for the Collaborative Drawing feature.

Defines structured models for real-time stroke synchronization and
drawing persistence: stroke validation, serialization, composite
image rendering, and database storage.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class StrokeMessage:
    """A single drawing stroke transmitted between siblings via WebSocket.

    Coordinates in `points` are normalized to [0.0, 1.0] range
    (fraction of canvas dimensions) for cross-device consistency.
    """

    session_id: str
    sibling_id: str  # "child1" or "child2"
    points: list[dict]  # [{"x": float, "y": float}, ...]
    color: str  # hex color string, e.g. "#FF6B6B"
    brush_size: int  # pixel width
    timestamp: str  # ISO 8601
    tool: str = "brush"  # "brush", "eraser", "stamp"
    stamp_shape: str | None = None


REQUIRED_FIELDS = {"session_id", "sibling_id", "points", "color", "brush_size", "timestamp"}


@dataclass
class DrawingRecord:
    """Persisted drawing metadata stored in the drawings database table."""

    drawing_id: str
    session_id: str
    sibling_pair_id: str
    prompt: str
    stroke_count: int
    duration_seconds: int
    image_path: str  # e.g. "assets/generated_images/drawing_1737000000.png"
    beat_index: int
    created_at: str  # ISO 8601
