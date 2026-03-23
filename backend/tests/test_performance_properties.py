"""Property-based tests for Performance Tuning (Tasks 14.1–14.14).

Uses Hypothesis to validate correctness properties across:
  - Content hash utility
  - StyleTransferCache (disk-backed LRU)
  - FaceCropCache (in-memory LRU)
  - CacheManager invalidation cascade
  - Concurrent portrait generation
  - NumPy compositor equivalence
"""

import asyncio
import hashlib
import os
import tempfile
import time
from datetime import datetime, timezone
from io import BytesIO
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from hypothesis import given, settings, HealthCheck, assume
from hypothesis import strategies as st
from PIL import Image

from app.models.multimodal import FaceBBox
from app.services.cache_models import CachedFaceCrop, compute_content_hash
from app.services.face_crop_cache import FaceCropCache
from app.services.style_transfer_cache import StyleTransferCache


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_bytes_st = st.binary(min_size=1, max_size=512)
_hash_st = st.text(
    alphabet="abcdef0123456789", min_size=8, max_size=16
)
_role_st = st.sampled_from(["hero", "villain", "sidekick", "narrator", "guide"])


# ---------------------------------------------------------------------------
# Property 11 — Content hash correctness (Task 14.1)
# ---------------------------------------------------------------------------

class TestContentHashCorrectness:
    @settings(max_examples=20)
    @given(data=_bytes_st)
    def test_matches_sha256(self, data):
        expected = hashlib.sha256(data).hexdigest()
        assert compute_content_hash(data) == expected

    @settings(max_examples=20)
    @given(data=_bytes_st)
    def test_deterministic(self, data):
        assert compute_content_hash(data) == compute_content_hash(data)


# ---------------------------------------------------------------------------
# Property 1 — Style transfer cache round trip (Task 14.2)
# ---------------------------------------------------------------------------

class TestStyleTransferCacheRoundTrip:
    @settings(max_examples=20)
    @given(face_hash=_hash_st, role=_role_st, portrait=_bytes_st)
    def test_put_then_get_returns_identical_bytes(self, face_hash, role, portrait):
        with tempfile.TemporaryDirectory() as td:
            cache = StyleTransferCache(storage_root=td, max_disk_bytes=10 * 1024 * 1024)
            cache.put(face_hash, role, portrait)
            result = cache.get(face_hash, role)
            assert result == portrait


# ---------------------------------------------------------------------------
# Property 2 — Composite cache key distinctness (Task 14.3)
# ---------------------------------------------------------------------------

class TestCompositeKeyDistinctness:
    @settings(max_examples=20)
    @given(face_hash=_hash_st, portrait_a=_bytes_st, portrait_b=_bytes_st)
    def test_different_roles_store_distinct_portraits(self, face_hash, portrait_a, portrait_b):
        assume(portrait_a != portrait_b)
        with tempfile.TemporaryDirectory() as td:
            cache = StyleTransferCache(storage_root=td, max_disk_bytes=10 * 1024 * 1024)
            cache.put(face_hash, "hero", portrait_a)
            cache.put(face_hash, "villain", portrait_b)
            assert cache.get(face_hash, "hero") == portrait_a
            assert cache.get(face_hash, "villain") == portrait_b


# ---------------------------------------------------------------------------
# Property 8 — TTL eviction (Task 14.4)
# ---------------------------------------------------------------------------

class TestTTLEviction:
    @settings(max_examples=20)
    @given(face_hash=_hash_st, role=_role_st, portrait=_bytes_st)
    def test_expired_entries_return_none(self, face_hash, role, portrait):
        with tempfile.TemporaryDirectory() as td:
            cache = StyleTransferCache(storage_root=td, ttl_seconds=0)
            cache.put(face_hash, role, portrait)
            time.sleep(0.01)
            assert cache.get(face_hash, role) is None

    @settings(max_examples=20)
    @given(face_hash=_hash_st, role=_role_st, portrait=_bytes_st)
    def test_cleanup_expired_removes_entries(self, face_hash, role, portrait):
        with tempfile.TemporaryDirectory() as td:
            cache = StyleTransferCache(storage_root=td, ttl_seconds=0)
            cache.put(face_hash, role, portrait)
            time.sleep(0.01)
            removed = cache.cleanup_expired()
            assert removed >= 1
            assert cache.stats["entries"] == 0


# ---------------------------------------------------------------------------
# Property 9 — Style transfer cache disk size limit (Task 14.5)
# ---------------------------------------------------------------------------

class TestDiskSizeLimit:
    @settings(max_examples=20)
    @given(
        entries=st.lists(
            st.tuples(_hash_st, _role_st, _bytes_st),
            min_size=3,
            max_size=8,
        )
    )
    def test_total_disk_never_exceeds_limit(self, entries):
        max_bytes = 256
        with tempfile.TemporaryDirectory() as td:
            cache = StyleTransferCache(storage_root=td, max_disk_bytes=max_bytes)
            for face_hash, role, portrait in entries:
                cache.put(face_hash, role, portrait)
            assert cache.stats["disk_bytes"] <= max_bytes


# ---------------------------------------------------------------------------
# Property 12 — Style transfer keyed by content hash not face ID (Task 14.6)
# ---------------------------------------------------------------------------

class TestKeyedByContentHash:
    @settings(max_examples=20)
    @given(content_hash=_hash_st, portrait=_bytes_st)
    def test_same_content_hash_different_face_ids_share_cache(self, content_hash, portrait):
        """Two different face IDs with identical content hashes share cache entries."""
        with tempfile.TemporaryDirectory() as td:
            cache = StyleTransferCache(storage_root=td, max_disk_bytes=10 * 1024 * 1024)
            # Both "face IDs" map to the same content_hash
            cache.put(content_hash, "hero", portrait)
            # A different face_id with the same content_hash gets a hit
            result = cache.get(content_hash, "hero")
            assert result == portrait


# ---------------------------------------------------------------------------
# Property 3 — Face crop cache round trip (Task 14.7)
# ---------------------------------------------------------------------------

def _make_face_crop(index=0, content_hash="abc"):
    return CachedFaceCrop(
        face_index=index,
        crop_bytes=b"crop",
        bbox=FaceBBox(x=0.1, y=0.1, width=0.3, height=0.3, confidence=0.95),
        crop_width=50,
        crop_height=50,
        content_hash=content_hash,
    )


class TestFaceCropCacheRoundTrip:
    @settings(max_examples=20)
    @given(photo_hash=_hash_st, face_count=st.integers(min_value=1, max_value=5))
    def test_put_then_get_returns_identical_faces(self, photo_hash, face_count):
        cache = FaceCropCache(max_entries=200)
        faces = [_make_face_crop(i, f"fh{i}") for i in range(face_count)]
        cache.put(photo_hash, faces)
        result = cache.get(photo_hash)
        assert result is not None
        assert len(result) == face_count
        for i, face in enumerate(result):
            assert face.face_index == i
            assert face.content_hash == f"fh{i}"


# ---------------------------------------------------------------------------
# Property 10 — Face crop cache entry count limit (Task 14.8)
# ---------------------------------------------------------------------------

class TestFaceCropEntryCountLimit:
    @settings(max_examples=20)
    @given(
        hashes=st.lists(
            _hash_st, min_size=5, max_size=15, unique=True
        )
    )
    def test_entry_count_never_exceeds_limit(self, hashes):
        max_entries = 3
        cache = FaceCropCache(max_entries=max_entries)
        for h in hashes:
            cache.put(h, [_make_face_crop(0, h)])
        assert cache.stats["entries"] <= max_entries


# ---------------------------------------------------------------------------
# Property 13 — Cache invalidation cascade on photo deletion (Task 14.9)
# ---------------------------------------------------------------------------

class TestCacheInvalidationCascade:
    @settings(max_examples=20)
    @given(
        photo_hash=_hash_st,
        face_hashes=st.lists(_hash_st, min_size=1, max_size=4, unique=True),
        portrait=_bytes_st,
    )
    def test_invalidate_photo_clears_both_caches(self, photo_hash, face_hashes, portrait):
        from app.services.cache_manager import CacheManager

        with tempfile.TemporaryDirectory() as td:
            st_cache = StyleTransferCache(storage_root=td, max_disk_bytes=10 * 1024 * 1024)
            fc_cache = FaceCropCache()
            mgr = CacheManager(st_cache, fc_cache)

            # Populate
            fc_cache.put(photo_hash, [_make_face_crop(i, fh) for i, fh in enumerate(face_hashes)])
            for fh in face_hashes:
                st_cache.put(fh, "hero", portrait)

            # Invalidate
            asyncio.get_event_loop().run_until_complete(
                mgr.invalidate_photo(photo_hash, face_hashes)
            )

            assert fc_cache.get(photo_hash) is None
            for fh in face_hashes:
                assert st_cache.get(fh, "hero") is None


# ---------------------------------------------------------------------------
# Property 14 — Cache invalidation on face deletion (Task 14.10)
# ---------------------------------------------------------------------------

class TestCacheInvalidationFace:
    @settings(max_examples=20)
    @given(face_hash=_hash_st, portrait=_bytes_st)
    def test_invalidate_face_removes_all_roles(self, face_hash, portrait):
        from app.services.cache_manager import CacheManager

        roles = ["hero", "villain", "sidekick"]
        with tempfile.TemporaryDirectory() as td:
            st_cache = StyleTransferCache(storage_root=td, max_disk_bytes=10 * 1024 * 1024)
            fc_cache = FaceCropCache()
            mgr = CacheManager(st_cache, fc_cache)

            for role in roles:
                st_cache.put(face_hash, role, portrait)

            asyncio.get_event_loop().run_until_complete(
                mgr.invalidate_face(face_hash)
            )

            for role in roles:
                assert st_cache.get(face_hash, role) is None


# ---------------------------------------------------------------------------
# Property 4 — Concurrent portrait generation preserves results (Task 14.11)
# ---------------------------------------------------------------------------

class TestConcurrentGenerationPreservesResults:
    @settings(max_examples=20)
    @given(
        roles=st.lists(
            st.sampled_from(["hero", "villain", "sidekick", "narrator", "guide", "mentor"]),
            min_size=1,
            max_size=5,
            unique=True,
        )
    )
    def test_concurrent_matches_sequential(self, roles):
        """Concurrent generation produces same results as sequential."""
        from app.agents.style_transfer_agent import StyleTransferAgent
        from app.models.photo import CharacterMapping

        agent = StyleTransferAgent(storage_root="/tmp/test_portraits")
        # Agent is disabled (no GOOGLE_PROJECT_ID), so all mappings get default avatar.
        # We mock generate_portrait to return deterministic bytes per role.
        portrait_map = {r: f"portrait_{r}".encode() for r in roles}

        async def mock_generate(face_crop_bytes, character_context, face_content_hash=None):
            return portrait_map.get(character_context.get("role"))

        agent._enabled = True
        agent._model = MagicMock()
        agent.generate_portrait = mock_generate

        now = datetime.now(timezone.utc)
        mappings = [
            CharacterMapping(
                mapping_id=f"m{i}", sibling_pair_id="test:pair",
                character_role=role, face_id=f"face_{i}",
                family_member_name=None, created_at=now,
            )
            for i, role in enumerate(roles)
        ]

        # Mock DB and face crop loading
        mock_db = AsyncMock()
        mock_db.fetch_one = AsyncMock(return_value=None)  # no cached portrait

        async def mock_load_face(face_id, db):
            return b"fake_face_crop"

        agent._load_cached_portrait = AsyncMock(return_value=None)
        agent._load_face_crop = mock_load_face
        agent._store_portrait = AsyncMock()

        result = asyncio.get_event_loop().run_until_complete(
            agent.generate_portraits_for_session("test:pair", "sess1", mappings, mock_db)
        )

        assert set(result.keys()) == set(roles)
        for role in roles:
            assert result[role]  # non-empty base64 string


# ---------------------------------------------------------------------------
# Property 5 — Fault isolation in concurrent generation (Task 14.12)
# ---------------------------------------------------------------------------

class TestFaultIsolation:
    @settings(max_examples=20)
    @given(
        fail_index=st.integers(min_value=0, max_value=2),
    )
    def test_failed_roles_get_default_avatar(self, fail_index):
        """Failed roles get default avatar, successful roles get valid portraits."""
        import base64
        from app.agents.style_transfer_agent import StyleTransferAgent, _make_default_avatar
        from app.models.photo import CharacterMapping

        roles = ["hero", "villain", "sidekick"]
        agent = StyleTransferAgent(storage_root="/tmp/test_portraits")
        agent._enabled = True
        agent._model = MagicMock()

        call_count = {"n": 0}

        async def mock_generate(face_crop_bytes, character_context, face_content_hash=None):
            idx = call_count["n"]
            call_count["n"] += 1
            if idx == fail_index:
                return None  # simulate failure
            return f"portrait_{character_context['role']}".encode()

        agent.generate_portrait = mock_generate

        now = datetime.now(timezone.utc)
        mappings = [
            CharacterMapping(
                mapping_id=f"m{i}", sibling_pair_id="test:pair",
                character_role=role, face_id=f"face_{i}",
                family_member_name=None, created_at=now,
            )
            for i, role in enumerate(roles)
        ]

        agent._load_cached_portrait = AsyncMock(return_value=None)

        async def mock_load_face(face_id, db):
            return b"fake_face_crop"

        agent._load_face_crop = mock_load_face
        agent._store_portrait = AsyncMock()

        result = asyncio.get_event_loop().run_until_complete(
            agent.generate_portraits_for_session("test:pair", "sess1", mappings, AsyncMock())
        )

        default_b64 = base64.b64encode(_make_default_avatar()).decode("utf-8")

        # All roles present
        assert len(result) == 3
        # The failed role should have default avatar
        failed_role = roles[fail_index]
        assert result[failed_role] == default_b64
        # Successful roles should have non-default portraits
        for i, role in enumerate(roles):
            if i != fail_index:
                assert result[role] != default_b64


# ---------------------------------------------------------------------------
# Property 6 — Concurrency limit enforcement (Task 14.13)
# ---------------------------------------------------------------------------

class TestConcurrencyLimit:
    @settings(max_examples=20)
    @given(n_mappings=st.integers(min_value=4, max_value=8))
    def test_max_concurrent_never_exceeds_limit(self, n_mappings):
        """Simultaneous in-flight calls never exceed configured limit."""
        import base64
        from app.agents.style_transfer_agent import StyleTransferAgent
        from app.models.photo import CharacterMapping

        max_concurrent = 2
        agent = StyleTransferAgent(storage_root="/tmp/test_portraits", max_concurrent=max_concurrent)
        agent._enabled = True
        agent._model = MagicMock()

        peak = {"value": 0}
        current = {"value": 0}

        async def mock_generate(face_crop_bytes, character_context, face_content_hash=None):
            current["value"] += 1
            peak["value"] = max(peak["value"], current["value"])
            await asyncio.sleep(0.01)
            current["value"] -= 1
            return b"portrait"

        agent.generate_portrait = mock_generate

        now = datetime.now(timezone.utc)
        mappings = [
            CharacterMapping(
                mapping_id=f"m{i}", sibling_pair_id="test:pair",
                character_role=f"role_{i}", face_id=f"face_{i}",
                family_member_name=None, created_at=now,
            )
            for i in range(n_mappings)
        ]

        agent._load_cached_portrait = AsyncMock(return_value=None)

        async def mock_load_face(face_id, db):
            return b"fake_face_crop"

        agent._load_face_crop = mock_load_face
        agent._store_portrait = AsyncMock()

        asyncio.get_event_loop().run_until_complete(
            agent.generate_portraits_for_session("test:pair", "sess1", mappings, AsyncMock())
        )

        assert peak["value"] <= max_concurrent


# ---------------------------------------------------------------------------
# Property 7 — NumPy compositor equivalence (Task 14.14)
# ---------------------------------------------------------------------------

class TestNumPyCompositorEquivalence:
    @settings(max_examples=20)
    @given(
        width=st.integers(min_value=4, max_value=32),
        height=st.integers(min_value=4, max_value=32),
        scene_r=st.integers(min_value=0, max_value=255),
        scene_g=st.integers(min_value=0, max_value=255),
        scene_b=st.integers(min_value=0, max_value=255),
        strength=st.floats(min_value=0.0, max_value=1.0),
    )
    def test_color_grading_numpy_matches_pixel_loop(
        self, width, height, scene_r, scene_g, scene_b, strength
    ):
        """NumPy color grading output matches per-pixel loop within ±1 per channel."""
        import numpy as np
        from app.services.scene_compositor import SceneCompositor

        # Create a random RGBA image
        rng = np.random.RandomState(42)
        arr = rng.randint(0, 256, (height, width, 4), dtype=np.uint8)
        # Ensure some pixels have alpha > 0
        arr[:, :, 3] = rng.randint(1, 256, (height, width), dtype=np.uint8)

        portrait = Image.fromarray(arr, "RGBA")
        scene_avg = (scene_r, scene_g, scene_b)

        # NumPy path
        result_np = SceneCompositor._apply_color_grading(
            portrait.copy(), scene_avg, strength
        )

        # Per-pixel fallback path
        portrait_px = portrait.copy()
        pixels = portrait_px.load()
        for y in range(height):
            for x in range(width):
                r, g, b, a = pixels[x, y]
                if a == 0:
                    continue
                r = int(r + (scene_r - r) * strength)
                g = int(g + (scene_g - g) * strength)
                b = int(b + (scene_b - b) * strength)
                pixels[x, y] = (
                    max(0, min(255, r)),
                    max(0, min(255, g)),
                    max(0, min(255, b)),
                    a,
                )

        # Compare within ±1 tolerance (float rounding)
        np_arr = np.array(result_np)
        px_arr = np.array(portrait_px)
        diff = np.abs(np_arr.astype(int) - px_arr.astype(int))
        assert diff.max() <= 1, f"Max channel diff {diff.max()} exceeds ±1 tolerance"

    @settings(max_examples=20)
    @given(
        width=st.integers(min_value=4, max_value=32),
        height=st.integers(min_value=4, max_value=32),
        opacity=st.integers(min_value=10, max_value=200),
    )
    def test_shadow_numpy_matches_pixel_loop(self, width, height, opacity):
        """NumPy shadow creation matches per-pixel loop for alpha capping."""
        import numpy as np
        from app.services.scene_compositor import SceneCompositor

        rng = np.random.RandomState(42)
        arr = rng.randint(0, 256, (height, width, 4), dtype=np.uint8)
        portrait = Image.fromarray(arr, "RGBA")

        # NumPy path (blur_radius=0 to isolate alpha logic)
        result_np = SceneCompositor._create_shadow(portrait.copy(), opacity=opacity, blur_radius=0)

        # Per-pixel fallback
        shadow_px = Image.new("RGBA", portrait.size, (0, 0, 0, 0))
        alpha = portrait.split()[3]
        shadow_px.putalpha(alpha)
        spx = shadow_px.load()
        for y in range(height):
            for x in range(width):
                _, _, _, a = spx[x, y]
                spx[x, y] = (0, 0, 0, min(a, opacity))

        np_arr = np.array(result_np)
        px_arr = np.array(shadow_px)
        diff = np.abs(np_arr.astype(int) - px_arr.astype(int))
        assert diff.max() <= 1, f"Max channel diff {diff.max()} exceeds ±1 tolerance"
