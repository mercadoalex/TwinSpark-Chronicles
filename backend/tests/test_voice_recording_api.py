"""API integration tests for voice recording endpoints.

Tests the FastAPI endpoints for upload, list, detail, delete, bulk delete,
stats, and commands — including parent PIN auth and error handling.
"""

import io
import os
import shutil

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from pydub.generators import Sine

from app.db.connection import DatabaseConnection
from app.db.migration_runner import MigrationRunner
from app.services.audio_normalizer import AudioNormalizer
from app.services.voice_recording_service import VoiceRecordingService

# We need to patch the lazy service before importing the app
import app.main as main_module
from app.main import app

TEST_STORAGE = "test_voice_api_storage"
PARENT_PIN = "1234"


def _make_wav_bytes(duration_ms: int = 3000, freq: int = 440) -> bytes:
    """Generate a sine tone as WAV bytes."""
    tone = Sine(freq, sample_rate=16000).to_audio_segment(duration=duration_ms)
    tone = tone.set_sample_width(2).set_channels(1)
    buf = io.BytesIO()
    tone.export(buf, format="wav")
    return buf.getvalue()


@pytest_asyncio.fixture
async def db():
    conn = DatabaseConnection("sqlite:///:memory:")
    await conn.connect()
    runner = MigrationRunner(conn)
    await runner.apply_all()
    yield conn
    await conn.close()


@pytest_asyncio.fixture
async def patched_service(db):
    """Create a VoiceRecordingService and patch it into main module."""
    normalizer = AudioNormalizer()
    svc = VoiceRecordingService(db, normalizer, storage_root=TEST_STORAGE)
    # Patch the module-level singleton so endpoints use our test service
    original = main_module._voice_recording_service
    main_module._voice_recording_service = svc
    yield svc
    main_module._voice_recording_service = original
    if os.path.exists(TEST_STORAGE):
        shutil.rmtree(TEST_STORAGE)


@pytest_asyncio.fixture
async def client(patched_service):
    """AsyncClient wired to the FastAPI app with patched service."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ---------------------------------------------------------------------------
# Helper to upload a recording via the API
# ---------------------------------------------------------------------------

async def _upload(client, sibling_pair_id="pair1", **overrides):
    """Upload a voice recording and return the response."""
    audio = _make_wav_bytes(overrides.pop("duration_ms", 3000))
    form = {
        "sibling_pair_id": sibling_pair_id,
        "recorder_name": "Abuela María",
        "relationship": "grandparent",
        "message_type": "story_intro",
        "language": "en",
    }
    form.update(overrides)
    return await client.post(
        "/api/voice-recordings/upload",
        data=form,
        files={"file": ("recording.wav", audio, "audio/wav")},
    )


# ---------------------------------------------------------------------------
# Upload flow
# ---------------------------------------------------------------------------

class TestUploadFlow:
    @pytest.mark.asyncio
    async def test_upload_returns_201(self, client):
        resp = await _upload(client)
        assert resp.status_code == 201
        body = resp.json()
        assert "recording_id" in body
        assert body["message_type"] == "story_intro"
        assert body["duration_seconds"] > 0

    @pytest.mark.asyncio
    async def test_upload_then_detail(self, client):
        resp = await _upload(client)
        recording_id = resp.json()["recording_id"]

        detail = await client.get(f"/api/voice-recordings/detail/{recording_id}")
        assert detail.status_code == 200
        assert detail.json()["recording_id"] == recording_id
        assert detail.json()["recorder_name"] == "Abuela María"

    @pytest.mark.asyncio
    async def test_upload_invalid_message_type(self, client):
        audio = _make_wav_bytes()
        resp = await client.post(
            "/api/voice-recordings/upload",
            data={
                "sibling_pair_id": "pair1",
                "recorder_name": "Test",
                "relationship": "parent",
                "message_type": "invalid_type",
                "language": "en",
            },
            files={"file": ("rec.wav", audio, "audio/wav")},
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_upload_empty_recorder_name(self, client):
        resp = await _upload(client, recorder_name="   ")
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# List with filters
# ---------------------------------------------------------------------------

class TestListWithFilters:
    @pytest.mark.asyncio
    async def test_list_empty(self, client):
        resp = await client.get("/api/voice-recordings/pair1")
        assert resp.status_code == 200
        assert resp.json() == []

    @pytest.mark.asyncio
    async def test_list_returns_uploaded(self, client):
        await _upload(client, sibling_pair_id="pair1")
        await _upload(client, sibling_pair_id="pair1", message_type="encouragement")

        resp = await client.get("/api/voice-recordings/pair1")
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    @pytest.mark.asyncio
    async def test_list_filter_by_message_type(self, client):
        await _upload(client, sibling_pair_id="pair1", message_type="story_intro")
        await _upload(client, sibling_pair_id="pair1", message_type="encouragement")

        resp = await client.get(
            "/api/voice-recordings/pair1",
            params={"message_type": "story_intro"},
        )
        assert resp.status_code == 200
        results = resp.json()
        assert len(results) == 1
        assert results[0]["message_type"] == "story_intro"

    @pytest.mark.asyncio
    async def test_list_filter_by_recorder_name(self, client):
        await _upload(client, sibling_pair_id="pair1", recorder_name="Abuela")
        await _upload(client, sibling_pair_id="pair1", recorder_name="Papá")

        resp = await client.get(
            "/api/voice-recordings/pair1",
            params={"recorder_name": "Papá"},
        )
        assert resp.status_code == 200
        results = resp.json()
        assert len(results) == 1
        assert results[0]["recorder_name"] == "Papá"


# ---------------------------------------------------------------------------
# Delete cascade
# ---------------------------------------------------------------------------

class TestDeleteCascade:
    @pytest.mark.asyncio
    async def test_delete_single(self, client):
        resp = await _upload(client)
        recording_id = resp.json()["recording_id"]

        del_resp = await client.delete(
            f"/api/voice-recordings/{recording_id}",
            headers={"x-parent-pin": PARENT_PIN},
        )
        assert del_resp.status_code == 200
        assert del_resp.json()["deleted_recording_id"] == recording_id

        # Verify gone
        detail = await client.get(f"/api/voice-recordings/detail/{recording_id}")
        assert detail.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_all(self, client):
        await _upload(client, sibling_pair_id="pair1")
        await _upload(client, sibling_pair_id="pair1")

        del_resp = await client.delete(
            "/api/voice-recordings/all/pair1",
            headers={"x-parent-pin": PARENT_PIN},
        )
        assert del_resp.status_code == 200
        assert del_resp.json()["deleted_count"] == 2

        # Verify empty
        resp = await client.get("/api/voice-recordings/pair1")
        assert resp.json() == []

    @pytest.mark.asyncio
    async def test_delete_updates_stats(self, client):
        await _upload(client, sibling_pair_id="pair1")
        resp = await _upload(client, sibling_pair_id="pair1")
        recording_id = resp.json()["recording_id"]

        stats = await client.get("/api/voice-recordings/stats/pair1")
        assert stats.json()["recording_count"] == 2

        await client.delete(
            f"/api/voice-recordings/{recording_id}",
            headers={"x-parent-pin": PARENT_PIN},
        )

        stats = await client.get("/api/voice-recordings/stats/pair1")
        assert stats.json()["recording_count"] == 1


# ---------------------------------------------------------------------------
# Capacity rejection
# ---------------------------------------------------------------------------

class TestCapacityRejection:
    @pytest.mark.asyncio
    async def test_capacity_limit_409(self, client, patched_service):
        """Uploading beyond 50 recordings returns 409."""
        # Pre-fill 50 recordings directly via the service
        audio = _make_wav_bytes()
        from app.models.voice_recording import RecordingMetadata, MessageType

        for i in range(50):
            meta = RecordingMetadata(
                recorder_name=f"Recorder{i}",
                relationship="parent",
                message_type=MessageType.STORY_INTRO,
                language="en",
                sibling_pair_id="full_pair",
            )
            await patched_service.upload_recording("full_pair", audio, meta)

        # 51st via API should be rejected
        resp = await _upload(client, sibling_pair_id="full_pair")
        assert resp.status_code == 409
        assert "50" in resp.json()["detail"]


# ---------------------------------------------------------------------------
# 404 on missing recording
# ---------------------------------------------------------------------------

class TestNotFound:
    @pytest.mark.asyncio
    async def test_detail_404(self, client):
        resp = await client.get("/api/voice-recordings/detail/nonexistent-id")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_404(self, client):
        resp = await client.delete(
            "/api/voice-recordings/nonexistent-id",
            headers={"x-parent-pin": PARENT_PIN},
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Parent PIN auth
# ---------------------------------------------------------------------------

class TestParentPinAuth:
    @pytest.mark.asyncio
    async def test_delete_without_pin_returns_401(self, client):
        resp = await _upload(client)
        recording_id = resp.json()["recording_id"]

        del_resp = await client.delete(f"/api/voice-recordings/{recording_id}")
        assert del_resp.status_code == 401

    @pytest.mark.asyncio
    async def test_delete_with_wrong_pin_returns_401(self, client):
        resp = await _upload(client)
        recording_id = resp.json()["recording_id"]

        del_resp = await client.delete(
            f"/api/voice-recordings/{recording_id}",
            headers={"x-parent-pin": "0000"},
        )
        assert del_resp.status_code == 401

    @pytest.mark.asyncio
    async def test_bulk_delete_without_pin_returns_401(self, client):
        resp = await client.delete("/api/voice-recordings/all/pair1")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_bulk_delete_with_correct_pin(self, client):
        await _upload(client, sibling_pair_id="pair1")
        resp = await client.delete(
            "/api/voice-recordings/all/pair1",
            headers={"x-parent-pin": PARENT_PIN},
        )
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Stats and commands endpoints
# ---------------------------------------------------------------------------

class TestStatsAndCommands:
    @pytest.mark.asyncio
    async def test_stats_empty(self, client):
        resp = await client.get("/api/voice-recordings/stats/empty_pair")
        assert resp.status_code == 200
        body = resp.json()
        assert body["recording_count"] == 0
        assert body["max_recordings"] == 50
        assert body["remaining"] == 50

    @pytest.mark.asyncio
    async def test_stats_after_upload(self, client):
        await _upload(client, sibling_pair_id="pair1")
        resp = await client.get("/api/voice-recordings/stats/pair1")
        body = resp.json()
        assert body["recording_count"] == 1
        assert body["remaining"] == 49

    @pytest.mark.asyncio
    async def test_commands_empty(self, client):
        resp = await client.get("/api/voice-recordings/commands/pair1")
        assert resp.status_code == 200
        assert resp.json() == []

    @pytest.mark.asyncio
    async def test_commands_after_voice_command_upload(self, client):
        resp = await _upload(
            client,
            sibling_pair_id="pair1",
            message_type="voice_command",
            command_phrase="aventura mágica",
            command_action="start_adventure",
        )
        assert resp.status_code == 201

        cmds = await client.get("/api/voice-recordings/commands/pair1")
        assert cmds.status_code == 200
        results = cmds.json()
        assert len(results) == 1
        assert results[0]["command_phrase"] == "aventura mágica"
        assert results[0]["command_action"] == "start_adventure"
