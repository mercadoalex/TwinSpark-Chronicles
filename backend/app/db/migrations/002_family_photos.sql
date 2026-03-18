-- Family Photo Integration tables.
-- Adds photo uploads, face portraits, character mappings, and
-- cached style-transferred portraits.

-- Photo uploads
CREATE TABLE IF NOT EXISTS photos (
    photo_id TEXT PRIMARY KEY,
    sibling_pair_id TEXT NOT NULL,
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_size_bytes INTEGER NOT NULL,
    width INTEGER NOT NULL,
    height INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'safe',  -- safe | review | blocked
    uploaded_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_photos_sibling_pair ON photos(sibling_pair_id);

-- Extracted face portraits
CREATE TABLE IF NOT EXISTS face_portraits (
    face_id TEXT PRIMARY KEY,
    photo_id TEXT NOT NULL,
    face_index INTEGER NOT NULL,
    crop_path TEXT NOT NULL,
    bbox_x REAL NOT NULL,
    bbox_y REAL NOT NULL,
    bbox_width REAL NOT NULL,
    bbox_height REAL NOT NULL,
    family_member_name TEXT,
    FOREIGN KEY (photo_id) REFERENCES photos(photo_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_face_portraits_photo ON face_portraits(photo_id);

-- Character-to-family-member mappings
CREATE TABLE IF NOT EXISTS character_mappings (
    mapping_id TEXT PRIMARY KEY,
    sibling_pair_id TEXT NOT NULL,
    character_role TEXT NOT NULL,
    face_id TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (face_id) REFERENCES face_portraits(face_id) ON DELETE SET NULL,
    UNIQUE(sibling_pair_id, character_role)
);

CREATE INDEX IF NOT EXISTS idx_character_mappings_sibling ON character_mappings(sibling_pair_id);

-- Cached style-transferred portraits
CREATE TABLE IF NOT EXISTS style_transferred_portraits (
    portrait_id TEXT PRIMARY KEY,
    face_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    file_path TEXT NOT NULL,
    generated_at TEXT NOT NULL,
    FOREIGN KEY (face_id) REFERENCES face_portraits(face_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_style_portraits_face ON style_transferred_portraits(face_id);
