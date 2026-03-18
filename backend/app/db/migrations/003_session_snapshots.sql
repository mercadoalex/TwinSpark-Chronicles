-- Session Resumption tables.
-- Adds session snapshots for persisting story progress across browser sessions.

CREATE TABLE IF NOT EXISTS session_snapshots (
    id TEXT PRIMARY KEY,
    sibling_pair_id TEXT NOT NULL,
    character_profiles TEXT NOT NULL,
    story_history TEXT NOT NULL,
    current_beat TEXT,
    session_metadata TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_session_snapshots_pair
    ON session_snapshots(sibling_pair_id);
