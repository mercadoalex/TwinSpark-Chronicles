-- Content hash columns for caching.
-- Adds SHA-256 content hash to photos and face_portraits tables
-- to serve as stable cache keys for style transfer and face crop caches.

ALTER TABLE photos ADD COLUMN content_hash TEXT;

ALTER TABLE face_portraits ADD COLUMN content_hash TEXT;
