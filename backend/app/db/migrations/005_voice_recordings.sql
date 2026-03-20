-- Voice Recording System tables.
-- Adds voice recordings storage and audit event logging
-- for family voice messages integrated into story sessions.

-- Voice recordings
CREATE TABLE IF NOT EXISTS voice_recordings (
    recording_id TEXT PRIMARY KEY,
    sibling_pair_id TEXT NOT NULL,
    recorder_name TEXT NOT NULL,
    relationship TEXT NOT NULL,
    message_type TEXT NOT NULL,
    language TEXT NOT NULL DEFAULT 'en',
    duration_seconds REAL NOT NULL,
    wav_path TEXT NOT NULL,
    mp3_path TEXT NOT NULL,
    sample_path TEXT,
    command_phrase TEXT,
    command_action TEXT,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_vr_sibling_pair ON voice_recordings(sibling_pair_id);
CREATE INDEX IF NOT EXISTS idx_vr_message_type ON voice_recordings(sibling_pair_id, message_type);
CREATE INDEX IF NOT EXISTS idx_vr_recorder ON voice_recordings(sibling_pair_id, recorder_name);

-- Voice recording audit events
CREATE TABLE IF NOT EXISTS voice_recording_events (
    event_id TEXT PRIMARY KEY,
    sibling_pair_id TEXT NOT NULL,
    recording_id TEXT,
    event_type TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_vre_sibling_pair ON voice_recording_events(sibling_pair_id);
