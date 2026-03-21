-- Collaborative Drawing tables.
-- Adds persistent storage for drawing metadata so siblings'
-- collaborative drawings are saved alongside their stories.

-- Drawings
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

CREATE INDEX IF NOT EXISTS idx_drawings_session
    ON drawings(session_id);

CREATE INDEX IF NOT EXISTS idx_drawings_pair
    ON drawings(sibling_pair_id, created_at DESC);
