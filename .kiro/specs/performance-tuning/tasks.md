# Implementation Plan: Performance Tuning

## Overview

Incrementally build the caching layer, frontend lazy loading, parallel processing, and compositor optimization. Start with data models and DB migration, then build caches bottom-up (StyleTransferCache → FaceCropCache → CacheManager), integrate caches into existing services, optimize the compositor, add frontend lazy loading components, wire up the stats endpoint, and finish with cache invalidation on deletion. Property tests validate each cache and optimization layer as it's built.

## Tasks

- [x] 1. Database migration and content hash utility
  - [x] 1.1 Create database migration `backend/app/db/migrations/004_content_hash.sql`
    - Add `content_hash TEXT` column to the `photos` table
    - Add `content_hash TEXT` column to the `face_portraits` table
    - _Requirements: 8.1, 8.2_

  - [x] 1.2 Create data models and content hash utility
    - Define `CachedFaceCrop`, `StyleTransferCacheEntry`, and `CacheStats` dataclasses as specified in the design
    - Implement `compute_content_hash(image_bytes: bytes) -> str` using SHA-256
    - Place utility in a shared location accessible by PhotoService, FaceExtractor, and StyleTransferAgent
    - _Requirements: 8.1, 8.2_

- [x] 2. StyleTransferCache — disk-backed LRU cache
  - [x] 2.1 Implement `StyleTransferCache` in `backend/app/services/style_transfer_cache.py`
    - Implement `get(face_content_hash, role)` returning cached portrait bytes or None, updating access time on hit
    - Implement `put(face_content_hash, role, portrait_bytes)` storing to disk, triggering LRU eviction when over max disk size (default 500 MB)
    - Implement `evict(face_content_hash, role=None)` removing specific or all entries for a face hash
    - Implement `cleanup_expired()` removing entries older than TTL (default 7 days)
    - Expose `stats` property with entry count, disk usage, hit/miss rates, eviction count
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 7.1, 7.2_

- [x] 3. FaceCropCache — in-memory LRU cache
  - [x] 3.1 Implement `FaceCropCache` in `backend/app/services/face_crop_cache.py`
    - Implement `get(photo_content_hash)` returning cached face crops or None, updating access time on hit
    - Implement `put(photo_content_hash, faces)` storing face crops, triggering LRU eviction when over max entries (default 200)
    - Implement `evict(photo_content_hash)` removing entry for the given hash
    - Expose `stats` property with entry count, hit/miss rates, eviction count
    - _Requirements: 2.1, 2.2, 7.3_

- [x] 4. CacheManager — coordinator, cleanup loop, and stats endpoint
  - [x] 4.1 Implement `CacheManager` in `backend/app/services/cache_manager.py`
    - Accept `StyleTransferCache` and `FaceCropCache` instances
    - Implement `start_cleanup_loop` / `stop_cleanup_loop` for background asyncio cleanup task (default every 60 minutes)
    - Implement `cleanup_expired` delegating to both caches
    - Implement `get_stats` returning aggregate `CacheStats`
    - Implement `invalidate_photo(photo_content_hash, face_content_hashes)` cascading eviction across both caches
    - Implement `invalidate_face(face_content_hash)` evicting style transfer entries for a face
    - _Requirements: 7.1, 7.4, 7.5, 9.1, 9.2, 9.3_

  - [x] 4.2 Add `GET /api/cache/stats` endpoint to `backend/app/main.py`
    - Wire endpoint to `CacheManager.get_stats()`
    - Return JSON with style transfer and face crop cache sizes, hit rates, and eviction counts
    - _Requirements: 7.4_

- [x] 5. Checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Integrate caching into PhotoService and FaceExtractor
  - [x] 6.1 Add content hash computation to `PhotoService.upload_photo`
    - Compute SHA-256 content hash of `resized_bytes` after resize, before face extraction
    - Store `content_hash` in the `photos` table via the existing DB insert
    - Pass `content_hash` to `FaceExtractor.extract_faces`
    - _Requirements: 8.1, 8.2_

  - [x] 6.2 Integrate `FaceCropCache` into `FaceExtractor.extract_faces`
    - Accept optional `content_hash` parameter
    - On cache hit, return cached face crops directly
    - On cache miss, run detection as before, compute per-face content hash, store in cache
    - _Requirements: 2.1, 2.2, 8.4_

  - [x] 6.3 Add cache invalidation to `PhotoService.delete_photo`
    - Look up `content_hash` from the photo record
    - Collect face `content_hash` values for all face crops belonging to the photo
    - Call `CacheManager.invalidate_photo(photo_content_hash, face_content_hashes)`
    - _Requirements: 2.3, 9.1, 9.2_

- [x] 7. Integrate caching and parallel generation into StyleTransferAgent
  - [x] 7.1 Add cache lookup to `StyleTransferAgent.generate_portrait`
    - Accept `face_content_hash` parameter
    - Check `StyleTransferCache` before calling Imagen 3
    - On cache miss, generate portrait, store in cache, return
    - Handle stale cache record (file missing from disk) by regenerating
    - _Requirements: 1.1, 1.2, 1.4, 8.3_

  - [x] 7.2 Implement parallel portrait generation in `StyleTransferAgent.generate_portraits_for_session`
    - Use `asyncio.TaskGroup` to process all character mappings concurrently
    - Use `asyncio.Semaphore(max_concurrent)` to limit concurrent Imagen 3 calls (default 3)
    - On per-character failure, use default avatar and continue processing remaining portraits
    - _Requirements: 5.1, 5.2, 5.3_

- [x] 8. SceneCompositor NumPy optimization
  - [x] 8.1 Replace per-pixel loops with NumPy operations in `SceneCompositor`
    - Rewrite `_apply_color_grading` to use NumPy array operations for vectorized blend
    - Rewrite `_create_shadow` to use NumPy array operations for alpha channel manipulation
    - Add `_batch_scale_portraits` method to pre-scale all portraits before the compositing loop
    - _Requirements: 6.1, 6.2, 6.3_

- [x] 9. Checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 10. Frontend LazyImage component
  - [x] 10.1 Create `LazyImage` component in `frontend/src/shared/components/LazyImage.jsx`
    - Use IntersectionObserver with configurable `rootMargin` (default 200px) to detect when image enters viewport
    - Show skeleton placeholder with matching dimensions until loaded
    - Fade in over configurable `fadeDuration` (default 200ms) on load
    - Set `loading="lazy"` attribute on `<img>` as baseline fallback
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

  - [x] 10.2 Integrate `LazyImage` into `PhotoGallery.jsx`
    - Replace existing `<img>` elements in the photo gallery grid with `LazyImage`
    - _Requirements: 3.1, 3.4_

- [x] 11. Frontend SceneImageLoader component
  - [x] 11.1 Create `SceneImageLoader` component in `frontend/src/features/story/components/SceneImageLoader.jsx`
    - Begin loading scene image immediately in background
    - Show blurred skeleton placeholder while loading
    - Crossfade from placeholder to full image over configurable `fadeDuration` (default 300ms)
    - Show fallback illustration and log failure if image fails to load within configurable `timeout` (default 10 seconds)
    - _Requirements: 4.1, 4.2, 4.3, 4.4_

  - [x] 11.2 Integrate `SceneImageLoader` into `DualStoryDisplay.jsx`
    - Replace existing scene image rendering with `SceneImageLoader`
    - Ensure narration text displays immediately while scene image loads in background
    - _Requirements: 4.1, 4.2_

- [x] 12. Wire CacheManager lifecycle into application startup/shutdown
  - [x] 12.1 Initialize caches and CacheManager in `backend/app/main.py`
    - Create `StyleTransferCache`, `FaceCropCache`, and `CacheManager` instances at app startup
    - Start the background cleanup loop on startup
    - Stop the cleanup loop on shutdown
    - Inject `CacheManager` into `PhotoService`, `FaceExtractor`, and `StyleTransferAgent`
    - _Requirements: 7.1, 7.5_

- [x] 13. Final checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x]* 14. Property-based tests (optional)
  - [x]* 14.1 Property 11 — Content hash correctness
    - Generate random byte sequences with Hypothesis; verify `compute_content_hash` returns `hashlib.sha256(input).hexdigest()`
    - **Validates: Requirements 8.1, 8.2**

  - [x]* 14.2 Property 1 — Style transfer cache round trip
    - Generate random face hashes, roles, and portrait bytes; verify put then get returns identical bytes
    - **Validates: Requirements 1.1, 1.2**

  - [x]* 14.3 Property 2 — Composite cache key distinctness
    - Generate a face hash and two distinct roles with different portrait bytes; verify each `(hash, role)` retrieves its own distinct portrait
    - **Validates: Requirements 1.3**

  - [x]* 14.4 Property 8 — TTL eviction
    - Insert entries, artificially age them past TTL, verify `get` returns None and `cleanup_expired` removes them
    - **Validates: Requirements 7.1**

  - [x]* 14.5 Property 9 — Style transfer cache disk size limit
    - Insert entries exceeding max disk size; verify total disk usage never exceeds limit and LRU entries are evicted first
    - **Validates: Requirements 7.2**

  - [x]* 14.6 Property 12 — Style transfer keyed by content hash not face ID
    - Generate two different face IDs with identical content hashes; verify cache hit for one serves the other
    - **Validates: Requirements 8.3**

  - [x]* 14.7 Property 3 — Face crop cache round trip
    - Generate random photo content hashes and face crop lists; verify put then get returns identical data
    - **Validates: Requirements 2.1, 2.2, 8.4**

  - [x]* 14.8 Property 10 — Face crop cache entry count limit
    - Insert entries exceeding max count; verify entry count never exceeds limit and LRU entries are evicted first
    - **Validates: Requirements 7.3**

  - [x]* 14.9 Property 13 — Cache invalidation cascade on photo deletion
    - Populate both caches for a photo and its faces; call `invalidate_photo`; verify both caches are clean
    - **Validates: Requirements 2.3, 9.1, 9.2**

  - [x]* 14.10 Property 14 — Cache invalidation on face deletion
    - Populate StyleTransferCache with entries across multiple roles for a face hash; call `invalidate_face`; verify no entries remain
    - **Validates: Requirements 9.3**

  - [x]* 14.11 Property 4 — Concurrent portrait generation preserves results
    - Generate random character mapping sets; mock Imagen 3; verify concurrent generation produces same results as sequential
    - **Validates: Requirements 5.1**

  - [x]* 14.12 Property 5 — Fault isolation in concurrent generation
    - Generate mappings where a subset fail; verify failed roles get default avatar bytes and successful roles get valid portraits
    - **Validates: Requirements 5.2**

  - [x]* 14.13 Property 6 — Concurrency limit enforcement
    - Generate N mappings exceeding concurrency limit; track simultaneous in-flight calls; verify max never exceeds configured limit
    - **Validates: Requirements 5.3**

  - [x]* 14.14 Property 7 — NumPy compositor equivalence
    - Generate random RGBA images and scene color tuples with Hypothesis; compare NumPy output to original per-pixel loop output within ±1 per channel tolerance
    - **Validates: Requirements 6.1, 6.2**

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property tests use Hypothesis (Python) with `@settings(max_examples=100)`
- Backend tests: `source venv/bin/activate && python3 -m pytest tests/ -x -q --tb=short` from `backend/`
- Frontend build: `npm run build` from `frontend/`
- Next DB migration is `004_content_hash.sql`
- Checkpoints ensure incremental validation
