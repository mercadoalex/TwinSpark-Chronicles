# Tasks: Voice Recording System

## Task 1: Database Migration and Data Models
- [x] 1.1 Create `backend/app/models/voice_recording.py` with Pydantic models: `MessageType` enum, `RecordingMetadata`, `VoiceRecordingRecord`, `NormalizedAudio`, `VoiceRecordingResult`, `DeleteRecordingResult`, `VoiceCommandRecord`, `VoiceCommandMatch`, `PlaybackResult`, `CloneStatus`, `RecordingStats`
- [x] 1.2 Create `backend/app/db/migrations/005_voice_recordings.sql` with `voice_recordings` and `voice_recording_events` tables, indexes on sibling_pair_id, message_type, and recorder_name
- [x] 1.3 Verify migration applies cleanly by running the migration runner against a fresh SQLite database

## Task 2: Audio Normalizer
- [x] 2.1 Create `backend/app/services/audio_normalizer.py` with `AudioNormalizer` class: `normalize(audio_bytes) -> NormalizedAudio` that converts to WAV 16kHz/16-bit/mono, normalizes peak to -3 dBFS, trims silence >500ms, rejects <1s or >60s, generates MP3, generates voice sample at 22.05kHz
- [x] 2.2 Implement `_trim_silence(audio: AudioSegment) -> AudioSegment` using pydub's silence detection
- [x] 2.3 Implement `_generate_voice_sample(audio: AudioSegment) -> bytes` that resamples to 22.05kHz/16-bit/mono WAV
- [x] 2.4 Implement `_apply_fade(audio_bytes: bytes, fade_ms: int = 500) -> bytes` for fade-in/fade-out on playback audio
- [x] 2.5 Write property tests in `backend/tests/test_audio_normalizer.py` covering Properties 1 (normalization output invariant), 2 (silence trimming), and 19 (fade preserves duration) using Hypothesis with pydub-generated audio
- [x] 2.6 Write unit tests for edge cases: empty audio, corrupt bytes, exactly 1s audio, exactly 60s audio, audio with only silence

## Task 3: Voice Recording Service
- [x] 3.1 Create `backend/app/services/voice_recording_service.py` with `VoiceRecordingService` class, constructor taking `DatabaseConnection`, `AudioNormalizer`, and `storage_root`
- [x] 3.2 Implement `upload_recording(sibling_pair_id, audio_bytes, metadata) -> VoiceRecordingResult`: validate metadata, check capacity (50 max, 10 voice commands max), normalize audio, save files to disk, insert DB row, log creation event
- [x] 3.3 Implement `get_recordings(sibling_pair_id, message_type?, recorder_name?) -> list[VoiceRecordingRecord]`: query with optional filters, return grouped by recorder_name and sorted by created_at
- [x] 3.4 Implement `get_recording(recording_id) -> VoiceRecordingRecord | None`: fetch single recording by ID
- [x] 3.5 Implement `delete_recording(recording_id) -> DeleteRecordingResult`: remove WAV, MP3, sample files, delete DB row, log deletion event, report if trigger assignments were affected
- [x] 3.6 Implement `delete_all_recordings(sibling_pair_id) -> int`: bulk delete all recordings and files for a sibling pair, log event
- [x] 3.7 Implement `get_recording_count(sibling_pair_id) -> int` and `find_matching_recording(sibling_pair_id, message_type, language) -> VoiceRecordingRecord | None`
- [x] 3.8 Implement `get_voice_commands(sibling_pair_id) -> list[VoiceCommandRecord]` and `get_cloning_status(sibling_pair_id) -> dict[str, CloneStatus]`
- [x] 3.9 Implement `log_event(sibling_pair_id, event_type, recording_id?) -> None` for audit trail
- [x] 3.10 Write property tests in `backend/tests/test_voice_recording_service.py` covering Properties 3 (round-trip), 4 (validation), 5 (isolation), 6 (capacity limit), 7 (command limit), 8 (delete cascade), 9 (bulk delete), 13 (grouping/sorting), 14 (filtering), 15 (cloning-ready), 16 (original preserved), 17 (audit logging), 18 (bilingual coexistence)
- [x] 3.11 Write unit tests for specific examples and edge cases: duplicate recorder names, exactly 50 recordings, voice command with special characters

## Task 4: Playback Integrator
- [x] 4.1 Create `backend/app/services/playback_integrator.py` with `PlaybackIntegrator` class, constructor taking `VoiceRecordingService`, `VoicePersonalityAgent`, and `AudioNormalizer`
- [x] 4.2 Implement `get_story_intro_audio`, `get_encouragement_audio`, `get_character_audio`, `get_sound_effect` methods that query matching recordings and apply fade-in/fade-out, falling back to TTS
- [x] 4.3 Implement `_select_by_language(recordings, preferred_lang) -> VoiceRecordingRecord | None` with the language fallback chain: preferred → other language → None
- [x] 4.4 Implement `match_voice_command(sibling_pair_id, transcribed_text) -> VoiceCommandMatch | None` using `difflib.SequenceMatcher` with 0.7 threshold against registered commands
- [x] 4.5 Write property tests in `backend/tests/test_playback_integrator.py` covering Properties 10 (trigger selection), 11 (language fallback), 12 (command matching threshold)
- [x] 4.6 Write unit tests: no recordings returns TTS, exact phrase match, partial match at boundary (0.69 vs 0.71), Spanish session with only English recordings

## Task 5: FastAPI Endpoints
- [x] 5.1 Add voice recording endpoints to `backend/app/main.py`: POST upload (multipart), GET list, GET detail, DELETE single, DELETE all, GET stats, GET commands
- [x] 5.2 Add lazy-initialized `_voice_recording_service` singleton following the `_photo_service` pattern
- [x] 5.3 Wire parent PIN authentication check on DELETE and bulk-DELETE endpoints using the existing parent auth mechanism
- [x] 5.4 Write API integration tests: upload flow, list with filters, delete cascade, capacity rejection, 404 on missing recording

## Task 6: Orchestrator Integration
- [x] 6.1 Add PlaybackIntegrator initialization in the Orchestrator's `_ensure_db_initialized` method
- [x] 6.2 Add a voice recording step in `generate_rich_story_moment` between story generation and TTS: check for STORY_INTRO on first beat, ENCOURAGEMENT on brave decisions, SOUND_EFFECT on playful moments
- [x] 6.3 Extend the WebSocket `audio_segment` handler to call `match_voice_command` after STT transcription, triggering the matched action if found
- [x] 6.4 Add `voice_recordings` key to the rich story moment response containing any voice recording audio (base64 MP3) and metadata

## Task 7: Frontend Voice Recording Store
- [x] 7.1 Create `frontend/src/stores/voiceRecordingStore.js` with Zustand: recordings list, isRecording, isUploading, recordingCount, maxRecordings, filters, and actions (fetchRecordings, uploadRecording, deleteRecording, deleteAllRecordings, setFilter)
- [x] 7.2 Add API client functions for all voice recording endpoints

## Task 8: Frontend Voice Recorder Component
- [x] 8.1 Create `frontend/src/features/audio/components/VoiceRecorder.jsx`: MediaRecorder capture, real-time waveform via AnalyserNode, elapsed time counter, 60s auto-stop
- [x] 8.2 Add metadata form: recorder name input, relationship selector, message type selector, language auto-detect from session, command phrase/action fields for VOICE_COMMAND type
- [x] 8.3 Add child-friendly UI: 48x48px touch targets, pulsing mic icon, bouncing waveform, animated avatar reacting to audio level, max 3 visible actions
- [x] 8.4 Add playback preview with re-record/confirm flow
- [x] 8.5 Add confetti animation and cheerful sound on successful save
- [x] 8.6 Add microphone permission error handling with settings link
- [x] 8.7 Add i18n strings to `frontend/src/locales.js` for English and Spanish

## Task 9: Frontend Voice Library Component
- [-] 9.1 Create `frontend/src/features/audio/components/VoiceLibrary.jsx`: list recordings grouped by recorder, inline MP3 preview, language badges (🇺🇸/🇪🇸), count/capacity display
- [-] 9.2 Add filter controls for Message_Type and Family_Recorder
- [-] 9.3 Add delete single recording with confirmation dialog (warns about trigger assignments)
- [-] 9.4 Add delete all recordings with confirmation dialog
- [-] 9.5 Gate management actions behind parent PIN using existing `ParentControls` component
- [x] 9.6 Add i18n strings for Voice Library UI

## Task 10: Frontend Playback Integration
- [x] 10.1 Extend the story display components to handle `voice_recordings` in the rich story moment response, playing recording audio instead of TTS when present
- [x] 10.2 Add voice command feedback: when a voice command matches, play the confirmation audio and display a visual indicator
- [x] 10.3 Update `audioStore.js` to support voice recording playback alongside TTS (queue management)
