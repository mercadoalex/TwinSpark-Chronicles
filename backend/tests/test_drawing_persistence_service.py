"""Unit tests for DrawingPersistenceService.

Requirements: 4.1, 4.2, 4.4
"""

from __future__ import annotations

import os
import re

import pytest
import pytest_asyncio

from app.db.connection import DatabaseConnection
from app.services.drawing_persistence_service import DrawingPersistenceService

_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"

_MIGRATION_SQL = """\
CREATE TABLE IF NOT EXISTS drawings (
    drawing_id       TEXT PRIMARY KEY,
    session_id       TEXT NOT NULL,
    sibling_pair_id  TEXT NOT NULL,
    prompt           TEXT NOT NULL,
    stroke_count     INTEGER NOT NULL DEFAULT 0,
    duration_seconds INTEGER NOT NULL DEFAULT 0,
    image_path       TEXT NOT NULL,
    beat_index       INTEGER NOT NULL DEFAULT 0,
    created_at       TEXT NOT NULL
);
"""


@pytest_asyncio.fixture
async def db():
    """In-memory SQLite database with the drawings table."""
    conn = DatabaseConnection("sqlite:///:memory:")
    await conn.connect()
    await conn.execute_script(_MIGRATION_SQL)
    yield conn
    await conn.close()


@pytest_asyncio.fixture
async def service(db):
    return DrawingPersistenceService(db)


def _make_strokes(n: int = 2) -> list[dict]:
    """Return *n* simple brush strokes with normalised coordinates."""
    return [
        {
            "points": [{"x": 0.1 * i, "y": 0.1 * i}, {"x": 0.2 * i, "y": 0.2 * i}],
            "color": "#E53935",
            "brush_size": 4,
            "tool": "brush",
        }
        for i in range(1, n + 1)
    ]


# ── render_composite ──────────────────────────────────────────────


class TestRenderComposite:
    def test_zero_strokes_returns_valid_png(self):
        """Rendering with no strokes still produces a valid PNG (white canvas)."""
        data = DrawingPersistenceService.render_composite([], 100, 100)
        assert data[:8] == _PNG_MAGIC

    def test_brush_strokes_produce_valid_png(self):
        data = DrawingPersistenceService.render_composite(_make_strokes(3), 800, 600)
        assert data[:8] == _PNG_MAGIC

    def test_eraser_strokes_produce_valid_png(self):
        strokes = [
            {
                "points": [{"x": 0.0, "y": 0.0}, {"x": 1.0, "y": 1.0}],
                "color": "#000000",
                "brush_size": 8,
                "tool": "eraser",
            }
        ]
        data = DrawingPersistenceService.render_composite(strokes, 200, 200)
        assert data[:8] == _PNG_MAGIC


# ── save_drawing ──────────────────────────────────────────────────


class TestSaveDrawing:
    @pytest.mark.asyncio
    async def test_saves_file_to_correct_path_pattern(self, service):
        record = await service.save_drawing(
            session_id="sess-1",
            sibling_pair_id="pair-1",
            strokes=_make_strokes(),
            prompt="Draw a dragon",
            duration_seconds=60,
            beat_index=2,
        )
        assert re.match(r"assets/generated_images/drawing_\d+\.png", record.image_path)
        # Clean up written file
        if os.path.exists(record.image_path):
            os.remove(record.image_path)

    @pytest.mark.asyncio
    async def test_inserts_correct_metadata_into_db(self, service, db):
        record = await service.save_drawing(
            session_id="sess-2",
            sibling_pair_id="pair-2",
            strokes=_make_strokes(5),
            prompt="Draw a castle",
            duration_seconds=90,
            beat_index=1,
        )
        row = await db.fetch_one(
            "SELECT * FROM drawings WHERE drawing_id = ?",
            (record.drawing_id,),
        )
        assert row is not None
        assert row["session_id"] == "sess-2"
        assert row["sibling_pair_id"] == "pair-2"
        assert row["prompt"] == "Draw a castle"
        assert row["stroke_count"] == 5
        assert row["duration_seconds"] == 90
        assert row["beat_index"] == 1
        # Clean up
        if os.path.exists(record.image_path):
            os.remove(record.image_path)

    @pytest.mark.asyncio
    async def test_render_failure_logs_warning_and_empty_path(self, service, monkeypatch):
        """When render_composite raises, save_drawing still succeeds with image_path=''."""
        monkeypatch.setattr(
            DrawingPersistenceService,
            "render_composite",
            staticmethod(lambda *_a, **_kw: (_ for _ in ()).throw(RuntimeError("boom"))),
        )
        record = await service.save_drawing(
            session_id="sess-3",
            sibling_pair_id="pair-3",
            strokes=_make_strokes(),
            prompt="Draw a tree",
            duration_seconds=45,
            beat_index=0,
        )
        assert record.image_path == ""


# ── get_drawing / get_drawings_for_session ────────────────────────


class TestQueries:
    @pytest.mark.asyncio
    async def test_get_drawing_returns_record(self, service):
        saved = await service.save_drawing(
            session_id="sess-q1",
            sibling_pair_id="pair-q1",
            strokes=_make_strokes(),
            prompt="Draw a sun",
            duration_seconds=30,
            beat_index=0,
        )
        fetched = await service.get_drawing(saved.drawing_id)
        assert fetched is not None
        assert fetched.drawing_id == saved.drawing_id
        assert fetched.prompt == "Draw a sun"
        if os.path.exists(saved.image_path):
            os.remove(saved.image_path)

    @pytest.mark.asyncio
    async def test_get_drawing_returns_none_for_missing(self, service):
        assert await service.get_drawing("nonexistent") is None

    @pytest.mark.asyncio
    async def test_get_drawings_for_session(self, service):
        for i in range(3):
            await service.save_drawing(
                session_id="sess-list",
                sibling_pair_id="pair-list",
                strokes=_make_strokes(),
                prompt=f"Prompt {i}",
                duration_seconds=60,
                beat_index=i,
            )
        results = await service.get_drawings_for_session("sess-list")
        assert len(results) == 3
        assert [r.beat_index for r in results] == [0, 1, 2]
        # Clean up
        for r in results:
            if r.image_path and os.path.exists(r.image_path):
                os.remove(r.image_path)
