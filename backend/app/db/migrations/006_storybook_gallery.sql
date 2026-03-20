-- Storybook Gallery tables.
-- Adds persistent storage for archived storybooks and their beats
-- so siblings can revisit completed adventures in the gallery.

-- Storybooks
CREATE TABLE IF NOT EXISTS storybooks (
    storybook_id   TEXT PRIMARY KEY,
    sibling_pair_id TEXT NOT NULL,
    title          TEXT NOT NULL,
    language       TEXT NOT NULL DEFAULT 'en',
    cover_image_url TEXT,
    beat_count     INTEGER NOT NULL DEFAULT 0,
    duration_seconds INTEGER NOT NULL DEFAULT 0,
    completed_at   TEXT NOT NULL,
    created_at     TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_storybooks_pair
    ON storybooks(sibling_pair_id, completed_at DESC);

-- Story beats
CREATE TABLE IF NOT EXISTS story_beats (
    beat_id        TEXT PRIMARY KEY,
    storybook_id   TEXT NOT NULL REFERENCES storybooks(storybook_id) ON DELETE CASCADE,
    beat_index     INTEGER NOT NULL,
    narration      TEXT NOT NULL,
    child1_perspective TEXT,
    child2_perspective TEXT,
    scene_image_url TEXT,
    choice_made    TEXT,
    available_choices TEXT,  -- JSON array
    created_at     TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_beats_storybook
    ON story_beats(storybook_id, beat_index ASC);
