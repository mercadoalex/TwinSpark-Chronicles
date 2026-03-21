"""Async persistence for collaborative drawings.

Renders stroke data into composite PNG images using Pillow, saves them
to disk, and stores drawing metadata in the ``drawings`` table.  Follows
the same ``DatabaseConnection`` pattern used by ``StoryArchiveService``.

Requirements: 4.1, 4.2, 4.3, 4.4, 4.5
"""

from __future__ import annotations

import io
import logging
import os
import time
import uuid
from datetime import datetime, timezone

from PIL import Image, ImageDraw

from app.db.connection import DatabaseConnection
from app.models.drawing import DrawingRecord

logger = logging.getLogger(__name__)

_CANVAS_BG = (255, 255, 255)  # white
_ERASER_COLOR = "#FFFFFF"


class DrawingPersistenceService:
    """Renders, persists, and retrieves collaborative drawings."""

    def __init__(self, db: DatabaseConnection) -> None:
        self._db = db

    # ── rendering ─────────────────────────────────────────────────

    @staticmethod
    def render_composite(
        strokes: list[dict], width: int, height: int
    ) -> bytes:
        """Render *strokes* onto a white canvas and return PNG bytes.

        Each stroke dict is expected to contain:
        - ``points``: list of ``{"x": float, "y": float}`` in [0.0, 1.0]
        - ``color``: hex colour string (e.g. ``"#FF6B6B"``)
        - ``brush_size``: int pixel width
        - ``tool``: ``"brush"`` | ``"eraser"`` (optional, defaults to brush)
        """
        img = Image.new("RGB", (width, height), _CANVAS_BG)
        draw = ImageDraw.Draw(img)

        for stroke in strokes:
            points = stroke.get("points", [])
            if len(points) < 2:
                continue

            tool = stroke.get("tool", "brush")
            if tool == "eraser":
                color = _ERASER_COLOR
            else:
                color = stroke.get("color", "#000000")

            brush_size = stroke.get("brush_size", 4)

            # Scale normalised [0.0, 1.0] coordinates to pixel dimensions
            scaled = [
                (pt["x"] * width, pt["y"] * height) for pt in points
            ]

            draw.line(scaled, fill=color, width=brush_size)

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    # ── persistence ───────────────────────────────────────────────

    async def save_drawing(
        self,
        session_id: str,
        sibling_pair_id: str,
        strokes: list[dict],
        prompt: str,
        duration_seconds: int,
        beat_index: int,
    ) -> DrawingRecord:
        """Render strokes to PNG, save to disk, and insert DB metadata.

        On render failure the record is still created with
        ``image_path=""``, and a warning is logged (Req 4.4).
        """
        drawing_id = uuid.uuid4().hex
        now = datetime.now(timezone.utc).isoformat()
        image_path = ""

        try:
            png_bytes = self.render_composite(strokes, 800, 600)
            ts = int(time.time())
            rel_path = f"assets/generated_images/drawing_{ts}.png"
            os.makedirs(os.path.dirname(rel_path), exist_ok=True)
            with open(rel_path, "wb") as fh:
                fh.write(png_bytes)
            image_path = rel_path
        except Exception:
            logger.warning(
                "Failed to render composite for session %s — saving record without image",
                session_id,
                exc_info=True,
            )

        await self._db.execute(
            """INSERT INTO drawings
                (drawing_id, session_id, sibling_pair_id, prompt,
                 stroke_count, duration_seconds, image_path,
                 beat_index, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                drawing_id,
                session_id,
                sibling_pair_id,
                prompt,
                len(strokes),
                duration_seconds,
                image_path,
                beat_index,
                now,
            ),
        )

        return DrawingRecord(
            drawing_id=drawing_id,
            session_id=session_id,
            sibling_pair_id=sibling_pair_id,
            prompt=prompt,
            stroke_count=len(strokes),
            duration_seconds=duration_seconds,
            image_path=image_path,
            beat_index=beat_index,
            created_at=now,
        )

    # ── queries ───────────────────────────────────────────────────

    async def get_drawing(self, drawing_id: str) -> DrawingRecord | None:
        """Retrieve a single drawing by its ID."""
        row = await self._db.fetch_one(
            """SELECT drawing_id, session_id, sibling_pair_id, prompt,
                      stroke_count, duration_seconds, image_path,
                      beat_index, created_at
            FROM drawings WHERE drawing_id = ?""",
            (drawing_id,),
        )
        if row is None:
            return None
        return DrawingRecord(**row)

    async def get_drawings_for_session(
        self, session_id: str
    ) -> list[DrawingRecord]:
        """Return all drawings for a story session, oldest first."""
        rows = await self._db.fetch_all(
            """SELECT drawing_id, session_id, sibling_pair_id, prompt,
                      stroke_count, duration_seconds, image_path,
                      beat_index, created_at
            FROM drawings
            WHERE session_id = ?
            ORDER BY created_at ASC""",
            (session_id,),
        )
        return [DrawingRecord(**row) for row in rows]
