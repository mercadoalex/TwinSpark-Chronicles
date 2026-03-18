-- Baseline migration: captures all 9 existing tables.
-- Uses IF NOT EXISTS so it is safe to run against databases with data.

-- SiblingDB tables

CREATE TABLE IF NOT EXISTS personality_profiles (
    child_id TEXT PRIMARY KEY,
    profile_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS relationship_models (
    sibling_pair_id TEXT PRIMARY KEY,
    model_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS skill_maps (
    sibling_pair_id TEXT PRIMARY KEY,
    skill_map_json TEXT NOT NULL,
    evaluated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS session_summaries (
    session_id TEXT PRIMARY KEY,
    sibling_pair_id TEXT NOT NULL,
    score REAL NOT NULL,
    summary TEXT NOT NULL,
    suggestion TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS initial_profiles (
    child_id TEXT PRIMARY KEY,
    profile_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

-- WorldDB tables

CREATE TABLE IF NOT EXISTS world_locations (
    id TEXT PRIMARY KEY,
    sibling_pair_id TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    state TEXT NOT NULL DEFAULT 'discovered',
    discovered_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(sibling_pair_id, name)
);

CREATE TABLE IF NOT EXISTS world_location_history (
    id TEXT PRIMARY KEY,
    location_id TEXT NOT NULL,
    previous_state TEXT NOT NULL,
    previous_description TEXT NOT NULL,
    changed_at TEXT NOT NULL,
    FOREIGN KEY (location_id) REFERENCES world_locations(id)
);

CREATE TABLE IF NOT EXISTS world_npcs (
    id TEXT PRIMARY KEY,
    sibling_pair_id TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    relationship_level INTEGER NOT NULL DEFAULT 1,
    met_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(sibling_pair_id, name)
);

CREATE TABLE IF NOT EXISTS world_items (
    id TEXT PRIMARY KEY,
    sibling_pair_id TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    collected_at TEXT NOT NULL,
    session_id TEXT NOT NULL,
    UNIQUE(sibling_pair_id, name)
);
