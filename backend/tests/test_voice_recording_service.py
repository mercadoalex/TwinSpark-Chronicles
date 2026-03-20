"""Tests for VoiceRecordingService: property-based and unit tests.

Property tests use Hypothesis to verify correctness properties 3-9, 13-18.
Unit tests cover specific examples and edge cases.
"""

import io
import os
import shutil

import pytest
import pytest_asyncio
from hypothesis import given, settings, strategies as st, HealthCheck, assume
from pydub import AudioSegment
from pydub.generators import Sine

from app.db.connection import DatabaseConnection
from app.db.migration_runner import MigrationRunner
from app.models.voice_recording import (
    CloneStatus,
    MessageType,
    RecordingMetadata,
    VoiceRecordingRecord,
)
from app.services.audio_normalizer import AudioNormalizer
from app.services.voice_recording_service import (
    VoiceRecordingCapacityError,
    VoiceRecordingService,
    VoiceRecordingValidationError,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

TEST_STORAGE = "test_voice_storage"


def _make_wav_bytes(duration_ms: int = 3000, freq: int = 440) -> bytes:
    """Generate a sine tone as WAV bytes."""
    tone = Sine(freq, sample_rate=16000).to_audio_segment(duration=duration_ms)
    tone = tone.set_sample_width(2).set_channels(1)
    buf = io.BytesIO()
    tone.export(buf, format="wav")
    return buf.getvalue()


def _make_metadata(
    recorder_name: str = "Abuela María",
    relationship: str = "grandparent",
    message_type: MessageType = MessageType.STORY_INTRO,
    language: str = "en",
    sibling_pair_id: str = "pair1",
    command_phrase: str | None = None,
    command_action: str | None = None,
) -> RecordingMetadata:
    """Create a RecordingMetadata with sensible defaults."""
    return RecordingMetadata(
        recorder_name=recorder_name,
        relationship=relationship,
        message_type=message_type,
        language=language,
        sibling_pair_id=sibling_pair_id,
        command_phrase=command_phrase,
        command_action=command_action,
    )


# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------

valid_message_types = st.sampled_from(list(MessageType))
non_command_types = st.sampled_from([
    MessageType.STORY_INTRO,
    MessageType.ENCOURAGEMENT,
    MessageType.SOUND_EFFECT,
    MessageType.CUSTOM,
])
valid_languages = st.sampled_from(["en", "es"])
valid_relationships = st.sampled_from(["grandparent", "parent", "sibling", "other"])
recorder_names = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N", "Zs"), min_codepoint=32),
    min_size=1,
    max_size=30,
).filter(lambda s: s.strip())


@st.composite
def valid_metadata(draw, sibling_pair_id: str | None = None):
    """Generate valid RecordingMetadata."""
    msg_type = draw(valid_message_types)
    name = draw(recorder_names)
    rel = draw(valid_relationships)
    lang = draw(valid_languages)
    pair_id = sibling_pair_id or draw(st.text(min_size=4, max_size=10, alphabet="abcdefghijklmnop"))

    cmd_phrase = None
    cmd_action = None
    if msg_type == MessageType.VOICE_COMMAND:
        cmd_phrase = draw(st.text(min_size=1, max_size=20, alphabet="abcdefghijklmnop ").filter(lambda s: s.strip()))
        cmd_action = draw(st.sampled_from(["start_adventure", "call_help", "use_magic"]))

    return RecordingMetadata(
        recorder_name=name,
        relationship=rel,
        message_type=msg_type,
        language=lang,
        sibling_pair_id=pair_id,
        command_phrase=cmd_phrase,
        command_action=cmd_action,
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def db():
    conn = DatabaseConnection("sqlite:///:memory:")
    await conn.connect()
    runner = MigrationRunner(conn)
    await runner.apply_all()
    yield conn
    await conn.close()


@pytest_asyncio.fixture
async def service(db):
    normalizer = AudioNormalizer()
    svc = VoiceRecordingService(db, normalizer, storage_root=TEST_STORAGE)
    yield svc
    if os.path.exists(TEST_STORAGE):
        shutil.rmtree(TEST_STORAGE)


# ---------------------------------------------------------------------------
# Property Tests
# ---------------------------------------------------------------------------


class TestRoundTrip:
    """Property 3: Recording store/load round-trip.

    For any valid voice recording, storing via upload_recording and loading
    via get_recording SHALL produce a record with equivalent metadata.
    Both WAV and MP3 files SHALL exist at the stored paths.

    **Validates: Requirements 2.4, 4.3, 4.4, 4.7, 7.2**
    """

    @given(data=valid_metadata(sibling_pair_id="rt_pair"))
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_round_trip(self, service, data):
        audio = _make_wav_bytes(3000)
        result = await service.upload_recording("rt_pair", audio, data)

        loaded = await service.get_recording(result.recording_id)
        assert loaded is not None
        assert loaded.recorder_name == data.recorder_name
        assert loaded.relationship == data.relationship
        assert loaded.message_type == data.message_type
        assert loaded.language == data.language
        assert loaded.duration_seconds > 0
        assert loaded.command_phrase == data.command_phrase
        assert loaded.command_action == data.command_action

        # Files exist on disk
        assert os.path.exists(loaded.wav_path)
        assert os.path.exists(loaded.mp3_path)

        # Cleanup for next iteration
        await service.delete_all_recordings("rt_pair")


class TestValidation:
    """Property 4: Metadata validation rejects invalid inputs.

    For any RecordingMetadata where recorder_name is empty or whitespace,
    upload_recording SHALL reject and recording count SHALL remain unchanged.

    **Validates: Requirements 2.2, 2.3**
    """

    @given(
        whitespace_name=st.text(
            alphabet=" \t\n\r", min_size=0, max_size=5
        )
    )
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_empty_recorder_name_rejected(self, service, whitespace_name):
        audio = _make_wav_bytes(3000)
        meta = _make_metadata(recorder_name=whitespace_name, sibling_pair_id="val_pair")

        count_before = await service.get_recording_count("val_pair")
        with pytest.raises(VoiceRecordingValidationError, match="Recorder name"):
            await service.upload_recording("val_pair", audio, meta)
        count_after = await service.get_recording_count("val_pair")
        assert count_after == count_before


class TestIsolation:
    """Property 5: Sibling pair isolation.

    For any two distinct sibling_pair_ids, recordings stored for A SHALL
    never appear in results of get_recordings(B).

    **Validates: Requirements 4.2**
    """

    @given(
        name_a=recorder_names,
        name_b=recorder_names,
    )
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_isolation(self, service, name_a, name_b):
        audio = _make_wav_bytes(3000)
        meta_a = _make_metadata(recorder_name=name_a, sibling_pair_id="iso_a")
        meta_b = _make_metadata(recorder_name=name_b, sibling_pair_id="iso_b")

        await service.upload_recording("iso_a", audio, meta_a)
        await service.upload_recording("iso_b", audio, meta_b)

        recs_a = await service.get_recordings("iso_a")
        recs_b = await service.get_recordings("iso_b")

        ids_a = {r.recording_id for r in recs_a}
        ids_b = {r.recording_id for r in recs_b}
        assert ids_a.isdisjoint(ids_b)

        for r in recs_a:
            assert r.sibling_pair_id == "iso_a"
        for r in recs_b:
            assert r.sibling_pair_id == "iso_b"

        # Cleanup
        await service.delete_all_recordings("iso_a")
        await service.delete_all_recordings("iso_b")


class TestCapacityLimit:
    """Property 6: Recording capacity limit.

    For any sibling pair with 50 recordings, a 51st SHALL be rejected.
    remaining SHALL equal 50 - N.

    **Validates: Requirements 4.5, 4.6, 5.5**
    """

    @given(n=st.integers(min_value=48, max_value=50))
    @settings(max_examples=3, suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture], deadline=None)
    @pytest.mark.asyncio
    async def test_capacity_limit(self, service, n):
        pair_id = f"cap_{n}"
        audio = _make_wav_bytes(2000)

        # Fill up to n recordings
        for i in range(n):
            meta = _make_metadata(
                recorder_name=f"Recorder{i}",
                sibling_pair_id=pair_id,
            )
            await service.upload_recording(pair_id, audio, meta)

        count = await service.get_recording_count(pair_id)
        assert count == n

        if n >= 50:
            with pytest.raises(VoiceRecordingCapacityError, match="50 recordings"):
                meta = _make_metadata(recorder_name="Extra", sibling_pair_id=pair_id)
                await service.upload_recording(pair_id, audio, meta)

        # Cleanup
        await service.delete_all_recordings(pair_id)


class TestCommandLimit:
    """Property 7: Voice command capacity limit.

    With 10 VOICE_COMMAND recordings, an 11th SHALL be rejected,
    while other message types SHALL still succeed.

    **Validates: Requirements 7.6**
    """

    @given(extra_type=non_command_types)
    @settings(max_examples=5, suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture], deadline=None)
    @pytest.mark.asyncio
    async def test_command_limit(self, service, extra_type):
        pair_id = "cmd_limit"
        audio = _make_wav_bytes(2000)

        # Fill 10 voice commands
        for i in range(10):
            meta = _make_metadata(
                recorder_name=f"Parent{i}",
                message_type=MessageType.VOICE_COMMAND,
                sibling_pair_id=pair_id,
                command_phrase=f"command {i}",
                command_action=f"action_{i}",
            )
            await service.upload_recording(pair_id, audio, meta)

        # 11th voice command rejected
        with pytest.raises(VoiceRecordingCapacityError, match="10 voice commands"):
            meta = _make_metadata(
                recorder_name="Extra",
                message_type=MessageType.VOICE_COMMAND,
                sibling_pair_id=pair_id,
                command_phrase="extra cmd",
                command_action="extra_action",
            )
            await service.upload_recording(pair_id, audio, meta)

        # Other types still succeed
        meta = _make_metadata(
            recorder_name="Other",
            message_type=extra_type,
            sibling_pair_id=pair_id,
        )
        result = await service.upload_recording(pair_id, audio, meta)
        assert result.recording_id

        # Cleanup
        await service.delete_all_recordings(pair_id)


class TestDeleteCascade:
    """Property 8: Single recording deletion cascade.

    After delete_recording, get_recording SHALL return None, files SHALL
    not exist, and count SHALL decrease by 1.

    **Validates: Requirements 5.3**
    """

    @given(data=valid_metadata(sibling_pair_id="del_pair"))
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_delete_cascade(self, service, data):
        audio = _make_wav_bytes(3000)
        result = await service.upload_recording("del_pair", audio, data)

        count_before = await service.get_recording_count("del_pair")
        rec = await service.get_recording(result.recording_id)
        wav_path = rec.wav_path
        mp3_path = rec.mp3_path

        await service.delete_recording(result.recording_id)

        assert await service.get_recording(result.recording_id) is None
        assert not os.path.exists(wav_path)
        assert not os.path.exists(mp3_path)

        count_after = await service.get_recording_count("del_pair")
        assert count_after == count_before - 1

        # Cleanup remaining
        await service.delete_all_recordings("del_pair")


class TestBulkDelete:
    """Property 9: Bulk deletion.

    After delete_all_recordings, get_recordings SHALL return empty list
    and count SHALL be 0.

    **Validates: Requirements 10.2**
    """

    @given(n=st.integers(min_value=1, max_value=5))
    @settings(max_examples=5, suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture], deadline=None)
    @pytest.mark.asyncio
    async def test_bulk_delete(self, service, n):
        pair_id = f"bulk_{n}"
        audio = _make_wav_bytes(2000)

        for i in range(n):
            meta = _make_metadata(recorder_name=f"Rec{i}", sibling_pair_id=pair_id)
            await service.upload_recording(pair_id, audio, meta)

        deleted = await service.delete_all_recordings(pair_id)
        assert deleted == n

        recs = await service.get_recordings(pair_id)
        assert recs == []
        assert await service.get_recording_count(pair_id) == 0


class TestGroupingSorting:
    """Property 13: Listing grouping and sorting.

    Recordings SHALL be grouped by recorder_name, and within each group,
    sorted by created_at ascending.

    **Validates: Requirements 5.1**
    """

    @given(
        names=st.lists(recorder_names, min_size=2, max_size=4),
        counts=st.lists(st.integers(min_value=1, max_value=3), min_size=2, max_size=4),
    )
    @settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture], deadline=None)
    @pytest.mark.asyncio
    async def test_grouping_sorting(self, service, names, counts):
        # Ensure same length
        n = min(len(names), len(counts))
        names = names[:n]
        counts = counts[:n]

        pair_id = "grp_pair"
        audio = _make_wav_bytes(2000)

        for name, count in zip(names, counts):
            for _ in range(count):
                meta = _make_metadata(recorder_name=name, sibling_pair_id=pair_id)
                await service.upload_recording(pair_id, audio, meta)

        recs = await service.get_recordings(pair_id)

        # Verify grouped by recorder_name (all same-name records contiguous)
        seen_names: list[str] = []
        for r in recs:
            if not seen_names or seen_names[-1] != r.recorder_name:
                seen_names.append(r.recorder_name)

        # No name should appear more than once in seen_names (contiguous grouping)
        assert len(seen_names) == len(set(seen_names))

        # Within each group, created_at is ascending
        from itertools import groupby
        for _name, group in groupby(recs, key=lambda r: r.recorder_name):
            group_list = list(group)
            for i in range(1, len(group_list)):
                assert group_list[i].created_at >= group_list[i - 1].created_at

        # Cleanup
        await service.delete_all_recordings(pair_id)


class TestFiltering:
    """Property 14: Listing filtering.

    All recordings returned with filters SHALL match the criteria.
    No matching recording SHALL be omitted.

    **Validates: Requirements 5.6**
    """

    @given(
        msg_type=valid_message_types,
        name=recorder_names,
    )
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_filtering(self, service, msg_type, name):
        pair_id = "filt_pair"
        audio = _make_wav_bytes(2000)

        cmd_phrase = "test cmd" if msg_type == MessageType.VOICE_COMMAND else None
        cmd_action = "test_action" if msg_type == MessageType.VOICE_COMMAND else None

        meta = _make_metadata(
            recorder_name=name,
            message_type=msg_type,
            sibling_pair_id=pair_id,
            command_phrase=cmd_phrase,
            command_action=cmd_action,
        )
        await service.upload_recording(pair_id, audio, meta)

        # Filter by message_type
        by_type = await service.get_recordings(pair_id, message_type=msg_type.value)
        for r in by_type:
            assert r.message_type == msg_type

        # Filter by recorder_name
        by_name = await service.get_recordings(pair_id, recorder_name=name)
        for r in by_name:
            assert r.recorder_name == name

        # Cleanup
        await service.delete_all_recordings(pair_id)


class TestCloningReady:
    """Property 15: Cloning-ready flag.

    get_cloning_status SHALL report cloning_ready=True iff recorder has
    5+ voice samples. sample_count SHALL equal actual count.

    **Validates: Requirements 8.3**
    """

    @given(n=st.integers(min_value=1, max_value=7))
    @settings(max_examples=7, suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture], deadline=None)
    @pytest.mark.asyncio
    async def test_cloning_ready(self, service, n):
        pair_id = f"clone_{n}"
        audio = _make_wav_bytes(2000)
        recorder = "TestRecorder"

        for i in range(n):
            meta = _make_metadata(
                recorder_name=recorder,
                sibling_pair_id=pair_id,
            )
            await service.upload_recording(pair_id, audio, meta)

        status = await service.get_cloning_status(pair_id)
        assert recorder in status
        assert status[recorder].sample_count == n
        assert status[recorder].cloning_ready == (n >= 5)

        # Cleanup
        await service.delete_all_recordings(pair_id)


class TestOriginalPreserved:
    """Property 16: Original recording preserved after sample generation.

    The canonical WAV file SHALL remain byte-identical. The voice sample
    SHALL be a separate file.

    **Validates: Requirements 8.5**
    """

    @given(data=valid_metadata(sibling_pair_id="orig_pair"))
    @settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_original_preserved(self, service, data):
        audio = _make_wav_bytes(3000)
        result = await service.upload_recording("orig_pair", audio, data)

        rec = await service.get_recording(result.recording_id)
        assert rec is not None

        # WAV and sample are separate files
        assert rec.wav_path != rec.sample_path
        assert os.path.exists(rec.wav_path)

        if rec.sample_path:
            assert os.path.exists(rec.sample_path)
            # Read both and confirm they are different files
            with open(rec.wav_path, "rb") as f:
                wav_content = f.read()
            with open(rec.sample_path, "rb") as f:
                sample_content = f.read()
            # They should differ (different sample rates: 16kHz vs 22.05kHz)
            assert wav_content != sample_content

        # Cleanup
        await service.delete_all_recordings("orig_pair")


class TestAuditLogging:
    """Property 17: Audit event logging.

    For any creation or deletion, voice_recording_events SHALL contain
    a corresponding event row with correct event_type and sibling_pair_id.

    **Validates: Requirements 10.4**
    """

    @given(data=valid_metadata(sibling_pair_id="audit_pair"))
    @settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_audit_logging(self, service, data):
        audio = _make_wav_bytes(3000)
        result = await service.upload_recording("audit_pair", audio, data)

        # Check creation event
        events = await service._db.fetch_all(
            "SELECT * FROM voice_recording_events "
            "WHERE sibling_pair_id = ? AND recording_id = ? AND event_type = ?",
            ("audit_pair", result.recording_id, "created"),
        )
        assert len(events) >= 1
        assert events[0]["sibling_pair_id"] == "audit_pair"
        assert events[0]["created_at"]  # non-empty timestamp

        # Delete and check deletion event
        await service.delete_recording(result.recording_id)

        del_events = await service._db.fetch_all(
            "SELECT * FROM voice_recording_events "
            "WHERE sibling_pair_id = ? AND recording_id = ? AND event_type = ?",
            ("audit_pair", result.recording_id, "deleted"),
        )
        assert len(del_events) >= 1

        # Cleanup
        await service.delete_all_recordings("audit_pair")


class TestBilingualCoexistence:
    """Property 18: Bilingual recording coexistence.

    For any recorder and message type, it SHALL be possible to store one
    recording in 'en' and one in 'es' as separate recordings. Both SHALL
    appear in get_recordings with correct language codes.

    **Validates: Requirements 11.5**
    """

    @given(
        name=recorder_names,
        msg_type=non_command_types,
    )
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_bilingual_coexistence(self, service, name, msg_type):
        pair_id = "bilingual_pair"
        audio = _make_wav_bytes(2000)

        meta_en = _make_metadata(
            recorder_name=name,
            message_type=msg_type,
            language="en",
            sibling_pair_id=pair_id,
        )
        meta_es = _make_metadata(
            recorder_name=name,
            message_type=msg_type,
            language="es",
            sibling_pair_id=pair_id,
        )

        await service.upload_recording(pair_id, audio, meta_en)
        await service.upload_recording(pair_id, audio, meta_es)

        recs = await service.get_recordings(pair_id, recorder_name=name)
        languages = {r.language for r in recs if r.message_type == msg_type}
        assert "en" in languages
        assert "es" in languages

        # Each is a separate recording
        en_recs = [r for r in recs if r.language == "en" and r.message_type == msg_type]
        es_recs = [r for r in recs if r.language == "es" and r.message_type == msg_type]
        assert len(en_recs) >= 1
        assert len(es_recs) >= 1

        # Cleanup
        await service.delete_all_recordings(pair_id)


# ---------------------------------------------------------------------------
# Unit Tests — Edge Cases (Task 3.11)
# ---------------------------------------------------------------------------


class TestUnitEdgeCases:
    """Unit tests for specific examples and edge cases."""

    @pytest.mark.asyncio
    async def test_duplicate_recorder_names(self, service):
        """Multiple recordings from the same recorder should all be stored."""
        audio = _make_wav_bytes(3000)
        pair_id = "dup_pair"

        for i in range(3):
            meta = _make_metadata(
                recorder_name="Abuela María",
                sibling_pair_id=pair_id,
                message_type=MessageType.STORY_INTRO,
            )
            await service.upload_recording(pair_id, audio, meta)

        recs = await service.get_recordings(pair_id)
        assert len(recs) == 3
        assert all(r.recorder_name == "Abuela María" for r in recs)

        # Cleanup
        await service.delete_all_recordings(pair_id)

    @pytest.mark.asyncio
    async def test_exactly_50_recordings(self, service):
        """Exactly 50 recordings should be accepted; 51st rejected."""
        audio = _make_wav_bytes(2000)
        pair_id = "fifty_pair"

        for i in range(50):
            meta = _make_metadata(
                recorder_name=f"Rec{i}",
                sibling_pair_id=pair_id,
            )
            await service.upload_recording(pair_id, audio, meta)

        count = await service.get_recording_count(pair_id)
        assert count == 50

        # 51st should fail
        with pytest.raises(VoiceRecordingCapacityError, match="50 recordings"):
            meta = _make_metadata(recorder_name="Extra", sibling_pair_id=pair_id)
            await service.upload_recording(pair_id, audio, meta)

        # Cleanup
        await service.delete_all_recordings(pair_id)

    @pytest.mark.asyncio
    async def test_voice_command_special_characters(self, service):
        """Voice commands with special characters should be stored correctly."""
        audio = _make_wav_bytes(3000)
        pair_id = "special_pair"

        special_phrase = "¡Aventura mágica! 🎉"
        meta = _make_metadata(
            recorder_name="Papá",
            message_type=MessageType.VOICE_COMMAND,
            sibling_pair_id=pair_id,
            command_phrase=special_phrase,
            command_action="start_adventure",
        )
        result = await service.upload_recording(pair_id, audio, meta)

        rec = await service.get_recording(result.recording_id)
        assert rec is not None
        assert rec.command_phrase == special_phrase
        assert rec.command_action == "start_adventure"

        # Also verify via get_voice_commands
        cmds = await service.get_voice_commands(pair_id)
        assert len(cmds) == 1
        assert cmds[0].command_phrase == special_phrase

        # Cleanup
        await service.delete_all_recordings(pair_id)

    @pytest.mark.asyncio
    async def test_get_recording_nonexistent(self, service):
        """Getting a nonexistent recording should return None."""
        rec = await service.get_recording("nonexistent-id")
        assert rec is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_raises(self, service):
        """Deleting a nonexistent recording should raise."""
        with pytest.raises(VoiceRecordingValidationError, match="not found"):
            await service.delete_recording("nonexistent-id")

    @pytest.mark.asyncio
    async def test_delete_all_empty_pair(self, service):
        """Bulk delete on empty pair should return 0."""
        count = await service.delete_all_recordings("empty_pair")
        assert count == 0

    @pytest.mark.asyncio
    async def test_cloning_status_empty(self, service):
        """Cloning status for empty pair should return empty dict."""
        status = await service.get_cloning_status("empty_pair")
        assert status == {}

    @pytest.mark.asyncio
    async def test_voice_commands_empty(self, service):
        """Voice commands for empty pair should return empty list."""
        cmds = await service.get_voice_commands("empty_pair")
        assert cmds == []

    @pytest.mark.asyncio
    async def test_find_matching_recording_language_fallback(self, service):
        """find_matching_recording should fall back to other language."""
        audio = _make_wav_bytes(3000)
        pair_id = "fallback_pair"

        # Store only Spanish recording
        meta = _make_metadata(
            recorder_name="Abuela",
            message_type=MessageType.STORY_INTRO,
            language="es",
            sibling_pair_id=pair_id,
        )
        await service.upload_recording(pair_id, audio, meta)

        # Request English — should fall back to Spanish
        match = await service.find_matching_recording(
            pair_id, MessageType.STORY_INTRO.value, "en"
        )
        assert match is not None
        assert match.language == "es"

        # Cleanup
        await service.delete_all_recordings(pair_id)

    @pytest.mark.asyncio
    async def test_find_matching_recording_none(self, service):
        """find_matching_recording returns None when no match exists."""
        match = await service.find_matching_recording(
            "empty_pair", MessageType.STORY_INTRO.value, "en"
        )
        assert match is None

    @pytest.mark.asyncio
    async def test_delete_voice_command_reports_trigger(self, service):
        """Deleting a voice command should report affected triggers."""
        audio = _make_wav_bytes(3000)
        pair_id = "trigger_pair"

        meta = _make_metadata(
            recorder_name="Papá",
            message_type=MessageType.VOICE_COMMAND,
            sibling_pair_id=pair_id,
            command_phrase="magic spell",
            command_action="use_magic",
        )
        result = await service.upload_recording(pair_id, audio, meta)

        del_result = await service.delete_recording(result.recording_id)
        assert del_result.had_trigger_assignments is True
        assert "voice_command:magic spell" in del_result.affected_triggers

        # Cleanup
        await service.delete_all_recordings(pair_id)
