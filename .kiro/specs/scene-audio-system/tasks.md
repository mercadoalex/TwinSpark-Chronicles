# Implementation Plan: Scene Audio System

## Overview

Implement an immersive scene audio system spanning backend (keyword-based scene-to-audio mapping API) and frontend (Web Audio API ambient loops, SFX, crossfade engine, volume controls, and integration with TransitionEngine/audioStore). Backend uses Python/FastAPI, frontend uses React/Zustand.

## Tasks

- [x] 1. Backend data models and SceneAudioMapper service
  - [x] 1.1 Create `backend/app/models/audio_theme.py` with Pydantic models: `SceneThemeRequest` (with `scene_description: str` field, min_length=1) and `AudioThemeResult` (with `theme: str`, `ambient_track: str`, `sound_effects: list[str]`)
    - Validate that `SceneThemeRequest` rejects empty strings
    - _Requirements: 8.4, 8.2_

  - [x] 1.2 Create `backend/app/services/scene_audio_mapper.py` with `SceneAudioMapper` class containing `THEME_KEYWORDS`, `THEME_TRACKS`, `THEME_SFX`, and `DEFAULT_THEME` constants, plus `map_scene(scene_description: str) -> AudioThemeResult` method
    - Implement keyword matching: lowercase description, count hits per theme, return highest count, ties broken by dict order, no match returns "village"
    - Support six themes: forest, ocean, castle, space, village, cave
    - `THEME_TRACKS` maps theme to `/audio/ambient/{theme}.mp3`
    - `THEME_SFX` maps theme to supplementary SFX paths
    - _Requirements: 1.5, 2.1, 2.2, 2.3, 2.4, 2.5_

  - [x] 1.3 Write unit tests in `backend/tests/test_scene_audio_mapper.py`: test each of the 6 themes with representative descriptions, test no-match returns "village", test multi-keyword tie-breaking, test case insensitivity, test description with keywords from multiple themes returns highest count
    - _Requirements: 2.1, 2.2, 2.3_

  - [ ]* 1.4 Write property tests in `backend/tests/test_scene_audio_mapper_props.py` using Hypothesis (max_examples=20)
    - **Property 1: Scene mapping always produces a valid result** — generate arbitrary non-empty strings, verify `map_scene` returns valid `AudioThemeResult` with theme in known set
    - **Validates: Requirements 2.1, 2.5, 8.2**

  - [ ]* 1.5 Write property test for keyword matching
    - **Property 2: Keyword matching selects the correct theme** — generate (theme, keyword) pairs from the dictionary, verify `map_scene(keyword)` returns that theme
    - **Validates: Requirements 2.2**

  - [ ]* 1.6 Write property test for default theme
    - **Property 3: No-match descriptions default to village** — generate strings from alphabet excluding all keyword characters, verify result theme is "village"
    - **Validates: Requirements 2.3**

  - [ ]* 1.7 Write property test for round-trip consistency
    - **Property 4: Theme-to-track round-trip consistency** — generate arbitrary non-empty strings, verify `result.ambient_track == THEME_TRACKS[result.theme]`
    - **Validates: Requirements 8.5**

- [ ] 2. Backend API endpoint
  - [x] 2.1 Add `POST /api/audio/scene-theme` endpoint to `backend/app/main.py`: accept `SceneThemeRequest` body, instantiate `SceneAudioMapper`, call `map_scene`, return `AudioThemeResult` as JSON
    - Return 422 with `{"detail": "scene_description is required and must be non-empty"}` for missing/empty description
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

  - [x] 2.2 Write API integration tests in `backend/tests/test_scene_audio_api.py` using FastAPI TestClient: test 200 response with valid description, test 422 for empty string, test 422 for missing field, test response shape matches `AudioThemeResult`
    - _Requirements: 8.1, 8.2, 8.3_

- [x] 3. Frontend sceneAudioStore (Zustand)
  - [x] 3.1 Create `frontend/src/stores/sceneAudioStore.js` with Zustand store using `persist` middleware (localStorage key `"scene-audio-storage"`): state includes `audioContext`, `ambientGainNode`, `sfxGainNode`, `currentTheme`, `isAmbientPlaying`, `ambientVolume` (default 70), `sfxVolume` (default 70), `isMuted` (default false), `audioUnlocked`, `isDucking`, `preloadCache`
    - Persist only `ambientVolume`, `sfxVolume`, `isMuted`
    - _Requirements: 5.4, 10.4_

  - [x] 3.2 Implement `initAudio` and `unlockAudio` actions: create `AudioContext` in suspended state, create `ambientGainNode` and `sfxGainNode` connected to destination, `unlockAudio` calls `audioContext.resume()` and sets `audioUnlocked: true`
    - _Requirements: 7.2, 7.3, 10.4_

  - [x] 3.3 Implement `playAmbient(theme, trackUrl)` and `stopAmbient()`: fetch track, decode via `AudioContext.decodeAudioData`, create looping `AudioBufferSourceNode` routed through `ambientGainNode`, cache decoded buffer in `preloadCache` (LRU, max 10 entries)
    - _Requirements: 1.1, 1.2, 9.3, 9.5_

  - [x] 3.4 Implement crossfade logic inside the store: `crossfadeTo(theme, trackUrl, durationMs=2000)` creates incoming source, ramps outgoing gain to 0 and incoming gain to target over `durationMs` using `linearRampToValueAtTime`, skips if same theme is already active, handles interruption by stopping outgoing immediately
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

  - [x] 3.5 Implement SFX playback: `playSfx(category)` plays pre-decoded `AudioBuffer` as one-shot `AudioBufferSourceNode` through `sfxGainNode`, `preloadAllSfx()` fetches and decodes choice_select, page_turn, celebration MP3s on init
    - Fire-and-forget pattern, multiple SFX can overlap
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 9.1_

  - [x] 3.6 Implement volume/mute actions: `setAmbientVolume(v)`, `setSfxVolume(v)`, `toggleMute()` — apply gain changes to nodes within 100ms, mute sets both gains to 0 without changing stored volume values
    - _Requirements: 5.1, 5.2, 5.3, 5.5_

  - [x] 3.7 Implement ducking: `duckAmbient(level)` ramps ambient gain to `ambientVolume * level`, `restoreAmbient(durationMs=500)` ramps back to `ambientVolume`
    - _Requirements: 6.4, 10.1, 10.2, 10.3_

  - [x] 3.8 Implement `preloadTrack(theme, url)` with 5000ms `AbortController` timeout, and `reset()` that stops all sources, disconnects nodes, clears cache, resets state to initial values
    - _Requirements: 9.2, 9.4, 10.5_

  - [x] 3.9 Add `audioStore` subscription: subscribe to `isSpeaking` and `isPlayingVoiceRecording` from `audioStore` — duck to 30% when either is true, restore over 500ms when both false; subscribe to `audioStore.reset` to trigger `sceneAudioStore.reset`
    - _Requirements: 10.1, 10.2, 10.3, 10.5_

  - [x] 3.10 Add `prefers-reduced-motion` support: when active, `crossfadeTo` performs instant swap (no ramp), `playSfx('page_turn')` is skipped, ambient audio continues normally
    - _Requirements: 7.1, 6.5_

- [x] 4. Frontend VolumeController component
  - [x] 4.1 Create `frontend/src/components/VolumeController.jsx` with two range sliders (ambient 0–100 step 5, SFX 0–100 step 5) and a mute toggle button, all wired to `sceneAudioStore` actions
    - Sliders: `min-height: 56px` touch targets, keyboard operable (arrow keys increment by 5)
    - Mute button: `aria-pressed` attribute reflecting `isMuted`, `aria-label="Mute all scene audio"`
    - Sliders: `aria-label="Ambient audio volume"` and `aria-label="Sound effects volume"`, `aria-valuemin`, `aria-valuemax`
    - _Requirements: 5.1, 5.2, 5.6, 7.4, 7.5_

  - [x] 4.2 Create `frontend/src/components/VolumeController.css` with styling matching the existing ParentControls panel aesthetic, 56px min-height touch targets on sliders
    - _Requirements: 5.6_

  - [x] 4.3 Integrate `VolumeController` into `frontend/src/components/ParentControls.jsx` as a new `<section className="pc-section">` with heading "Scene Audio"
    - _Requirements: 5.6_

- [x] 5. Integration with TransitionEngine, DualStoryDisplay, and CelebrationOverlay
  - [x] 5.1 Update `frontend/src/features/story/components/TransitionEngine.jsx` to import and call `sceneAudioStore` actions at state transitions:
    - `preparing` → call `preloadTrack(theme, url)` + `duckAmbient(0.6)`
    - `animating` → call `crossfadeTo(theme, url)` + `playSfx('page_turn')`
    - `idle` (after transition) → call `restoreAmbient(500)`
    - Reduced-motion instant swap → instant audio swap, no crossfade, no SFX
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

  - [x] 5.2 Update `frontend/src/features/story/components/DualStoryDisplay.jsx` to call `sceneAudioStore.getState().playSfx('choice_select')` in the `handleChoiceTap` function
    - _Requirements: 3.1_

  - [x] 5.3 Update `frontend/src/shared/components/CelebrationOverlay.jsx` to call `sceneAudioStore.getState().playSfx('celebration')` when the overlay mounts (inside the existing `useEffect`)
    - _Requirements: 3.3_

  - [x] 5.4 Add audio unlock prompt: show a "🔊 Tap to hear sounds" button when `audioUnlocked` is false, call `initAudio()` + `unlockAudio()` + `preloadAllSfx()` on first user interaction
    - Wire into the story stage area in `App.jsx` or `TransitionEngine.jsx`
    - _Requirements: 7.2, 7.3_

- [x] 6. Audio asset placeholders and directory structure
  - [x] 6.1 Create `frontend/public/audio/ambient/` directory with placeholder `.mp3` files for all 6 themes (forest, ocean, castle, space, village, cave) — can be short silent MP3s for development, to be replaced with real assets
    - _Requirements: 1.5_

  - [x] 6.2 Create `frontend/public/audio/sfx/` directory with placeholder `.mp3` files for choice_select, page_turn, celebration
    - _Requirements: 3.4_

- [ ] 7. Frontend property tests
  - [ ]* 7.1 Write property test in `frontend/src/stores/__tests__/sceneAudioStore.property.test.js` using fast-check (numRuns: 20)
    - **Property 5: Crossfade gain sum does not exceed configured volume** — generate volume (0–100) and progress t (0–1), verify `outGain + inGain <= volume`
    - **Validates: Requirements 4.3**

  - [ ]* 7.2 Write property test for ducking calculation
    - **Property 7: Ducking calculation correctness** — generate volume (0–100) and duck level (0–1), verify ducked volume equals `volume * level`, restore returns to original
    - **Validates: Requirements 6.4, 10.1, 10.2, 10.3**

  - [ ]* 7.3 Write property test for persistence round-trip
    - **Property 8: Volume settings persistence round-trip** — generate ambientVolume (0–100), sfxVolume (0–100), muted (boolean), serialize to persistence format, deserialize, verify equality
    - **Validates: Requirements 5.4**

  - [ ]* 7.4 Write property test for cache bounds
    - **Property 9: Audio cache is bounded** — generate sequence of 5–15 distinct theme strings, verify cache size ≤ 10 after all loads
    - **Validates: Requirements 9.3, 9.5**

- [x] 8. Final wiring and end-to-end validation
  - [x] 8.1 Ensure `sceneAudioStore.initAudio()` is called on first user gesture in the app flow, and `preloadAllSfx()` runs after audio context is unlocked
    - _Requirements: 7.2, 7.3, 9.1_

  - [x] 8.2 Ensure `sceneAudioStore.reset()` is called alongside `audioStore.reset()` in all exit/cleanup paths in `App.jsx` (handleSaveAndExit, handleExitWithoutSaving, handleEmergencyExit)
    - _Requirements: 10.5_

  - [x] 8.3 Verify error handling: ambient track 404 logs warning and continues without audio, SFX failure is silent, AudioContext creation failure makes all audio calls no-ops
    - _Requirements: 1.4, 3.6_

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property tests validate universal correctness properties from the design document
- Backend tests run with: `source venv/bin/activate && python3 -m pytest tests/ -x -q --tb=short` from `backend/`
- Frontend builds with: `npm run build` from `frontend/`
- Audio placeholder files allow development/testing before real audio assets are sourced
