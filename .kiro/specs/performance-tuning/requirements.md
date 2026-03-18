# Requirements Document

## Introduction

Performance tuning for the Twin Spark Chronicles style transfer and compositing pipeline. The current implementation re-processes style transfers and face extractions on every request, loads all images eagerly on the frontend, and processes characters sequentially. This feature introduces caching strategies, lazy loading, parallel processing, and cache management to reduce latency and resource consumption.

## Glossary

- **Pipeline**: The sequence of face extraction, style transfer, and scene compositing that transforms family photos into story illustrations.
- **Style_Transfer_Cache**: An in-memory and disk-backed cache that stores previously generated style-transferred portrait images, keyed by face content hash and style parameters.
- **Face_Crop_Cache**: An in-memory cache that stores extracted face crop bytes, keyed by photo content hash, to avoid re-running face detection on unchanged photos.
- **Cache_Manager**: A component responsible for enforcing TTL expiration, size limits, and eviction policies across all caches.
- **Image_Loader**: The frontend component responsible for loading and displaying images in photo galleries and story scenes.
- **Scene_Compositor**: The backend service that composites style-transferred portraits onto AI-generated base scene images.
- **Style_Transfer_Agent**: The backend agent that transforms face crops into illustrated character portraits using Imagen 3.
- **Face_Extractor**: The backend service that detects and crops individual faces from uploaded photos.
- **Photo_Service**: The backend service coordinating the photo upload, validation, scanning, and face extraction lifecycle.
- **Content_Hash**: A SHA-256 digest of image bytes used as a stable cache key that survives ID changes.

## Requirements

### Requirement 1: Style Transfer Result Caching

**User Story:** As a sibling user, I want previously style-transferred portraits to load instantly without re-calling the AI model, so that story sessions start faster.

#### Acceptance Criteria

1. WHEN a style transfer is requested for a face crop whose Content_Hash matches an existing cached portrait, THE Style_Transfer_Agent SHALL return the cached portrait without invoking Imagen 3.
2. WHEN a style transfer is requested for a face crop with no matching cache entry, THE Style_Transfer_Agent SHALL invoke Imagen 3, store the result in the Style_Transfer_Cache, and return the generated portrait.
3. THE Style_Transfer_Cache SHALL key entries by the combination of face crop Content_Hash and character role, so that the same face with different roles produces distinct cached portraits.
4. WHEN a cached portrait file is missing from disk but the cache record exists, THE Style_Transfer_Agent SHALL regenerate the portrait and update the cache entry.

### Requirement 2: Face Crop Caching

**User Story:** As a sibling user, I want face extraction results to be reused when the same photo is processed again, so that the upload pipeline completes faster.

#### Acceptance Criteria

1. WHEN a photo is uploaded whose Content_Hash matches a previously processed photo, THE Face_Extractor SHALL return the cached face crops without re-running face detection.
2. THE Face_Crop_Cache SHALL store extracted face crop bytes and bounding box metadata keyed by photo Content_Hash.
3. WHEN the source photo is deleted, THE Face_Crop_Cache SHALL evict all cache entries associated with that photo Content_Hash.

### Requirement 3: Frontend Lazy Loading for Photo Gallery

**User Story:** As a sibling user, I want the photo gallery to load images progressively as I scroll, so that the gallery opens quickly even with many photos.

#### Acceptance Criteria

1. THE Image_Loader SHALL defer loading of photo gallery thumbnails until the thumbnail is within 200 pixels of the visible viewport.
2. WHILE a gallery thumbnail is loading, THE Image_Loader SHALL display a placeholder skeleton with dimensions matching the expected thumbnail size.
3. WHEN a gallery thumbnail finishes loading, THE Image_Loader SHALL fade the image in over 200 milliseconds replacing the skeleton placeholder.
4. THE Image_Loader SHALL use the HTML `loading="lazy"` attribute on all gallery `<img>` elements as a baseline lazy loading mechanism.

### Requirement 4: Frontend Lazy Loading for Story Scene Images

**User Story:** As a sibling user, I want story scene illustrations to load efficiently without blocking the narration text, so that the story feels responsive.

#### Acceptance Criteria

1. WHEN a new story beat is received, THE Image_Loader SHALL begin loading the scene image in the background while immediately displaying the narration text.
2. WHILE a scene image is loading, THE Image_Loader SHALL display a blurred low-resolution placeholder or a themed skeleton animation.
3. WHEN the scene image finishes loading, THE Image_Loader SHALL crossfade from the placeholder to the full image over 300 milliseconds.
4. IF a scene image fails to load within 10 seconds, THEN THE Image_Loader SHALL display a fallback illustration and log the failure.

### Requirement 5: Parallel Portrait Generation

**User Story:** As a sibling user, I want all character portraits to be generated simultaneously rather than one at a time, so that story setup completes faster.

#### Acceptance Criteria

1. WHEN generating portraits for a session with multiple character mappings, THE Style_Transfer_Agent SHALL process all portrait generation requests concurrently using asyncio task groups.
2. IF one portrait generation fails during concurrent processing, THEN THE Style_Transfer_Agent SHALL use the default avatar for that character and continue processing the remaining portraits.
3. THE Style_Transfer_Agent SHALL limit concurrent Imagen 3 API calls to a configurable maximum (default: 3) to avoid rate limiting.

### Requirement 6: Scene Compositing Optimization

**User Story:** As a developer, I want the scene compositor to process images efficiently, so that composited scenes render faster.

#### Acceptance Criteria

1. THE Scene_Compositor SHALL use NumPy array operations for color grading instead of per-pixel Python loops.
2. THE Scene_Compositor SHALL use NumPy array operations for shadow generation instead of per-pixel Python loops.
3. WHEN compositing multiple portraits, THE Scene_Compositor SHALL pre-scale all portraits in a single batch before compositing onto the base scene.

### Requirement 7: Cache TTL and Eviction

**User Story:** As a developer, I want caches to have configurable time-to-live and size limits, so that disk and memory usage remain bounded.

#### Acceptance Criteria

1. THE Cache_Manager SHALL enforce a configurable TTL (default: 7 days) on Style_Transfer_Cache entries, evicting expired entries on access and during periodic cleanup.
2. THE Cache_Manager SHALL enforce a configurable maximum disk size (default: 500 MB) for the Style_Transfer_Cache, evicting least-recently-used entries when the limit is exceeded.
3. THE Cache_Manager SHALL enforce a configurable maximum entry count (default: 200) for the Face_Crop_Cache, evicting least-recently-used entries when the limit is exceeded.
4. THE Cache_Manager SHALL expose a `/api/cache/stats` endpoint returning current cache sizes, hit rates, and eviction counts.
5. THE Cache_Manager SHALL run a background cleanup task at a configurable interval (default: every 60 minutes) to remove expired entries.

### Requirement 8: Content Hash Computation

**User Story:** As a developer, I want a stable content-based key for cache lookups, so that caches remain valid regardless of photo ID or file path changes.

#### Acceptance Criteria

1. THE Photo_Service SHALL compute a SHA-256 Content_Hash of the resized image bytes during the upload pipeline, before face extraction.
2. THE Photo_Service SHALL store the Content_Hash in the photos database table alongside the photo record.
3. THE Style_Transfer_Agent SHALL use the face crop Content_Hash (not the face_id) as the primary cache lookup key.
4. THE Face_Extractor SHALL use the photo Content_Hash (not the photo_id) as the primary cache lookup key.

### Requirement 9: Cache Invalidation on Source Deletion

**User Story:** As a sibling user, I want cached data to be cleaned up when I delete a photo, so that stale data does not consume storage.

#### Acceptance Criteria

1. WHEN a photo is deleted, THE Photo_Service SHALL evict all Face_Crop_Cache entries associated with that photo Content_Hash.
2. WHEN a photo is deleted, THE Photo_Service SHALL evict all Style_Transfer_Cache entries for face crops that belonged to the deleted photo.
3. WHEN a face crop is deleted, THE Style_Transfer_Agent SHALL evict all Style_Transfer_Cache entries keyed by that face crop Content_Hash.
