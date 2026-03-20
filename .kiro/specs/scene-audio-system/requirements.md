# Requirements Document

## Introduction

The Scene Audio System brings immersive, premium-quality ambient soundscapes and sound effects to Twin Spark Chronicles. When Ale & Sofi explore a forest, they hear birds chirping and wind rustling through leaves. When they enter a castle, echoing footsteps and crackling torches surround them. Every choice tap, page turn, and celebration moment is punctuated with satisfying audio feedback. The backend uses AI to analyze scene descriptions and select the perfect ambient audio, while smooth crossfades during scene transitions keep the magic seamless. Parents retain full control over volume and muting, and the system respects accessibility preferences throughout.

## Glossary

- **Scene_Audio_Manager**: The frontend MobX/Zustand store responsible for managing ambient audio loops, sound effect playback, volume state, crossfade logic, and mute controls.
- **Ambient_Track**: A looping audio file representing a scene's soundscape (e.g., forest birds, ocean waves, castle echoes, space hum).
- **Sound_Effect**: A short, non-looping audio clip triggered by UI interactions or story events (e.g., choice selection whoosh, page turn, celebration fanfare).
- **Scene_Audio_Mapper**: The backend Python service that analyzes a scene description string and returns an appropriate Ambient_Track identifier and optional Sound_Effect list.
- **Crossfade_Engine**: The frontend audio logic that smoothly transitions between two Ambient_Tracks by fading one out while fading the next in over a configurable duration.
- **Audio_Theme**: A named collection of Ambient_Tracks and Sound_Effects associated with a scene environment (e.g., "forest", "ocean", "castle", "space", "village", "cave").
- **Volume_Controller**: The parent-facing UI component that provides volume sliders and a master mute toggle for ambient audio and sound effects independently.
- **TransitionEngine**: The existing React component that handles animated scene transitions between story beats.
- **DualStoryDisplay**: The existing React component that renders story scene content including narration, perspectives, and choice cards.
- **Audio_Store**: The existing Zustand store (`audioStore.js`) that manages TTS and voice recording playback state.
- **Playback_Integrator**: The existing backend Python service that coordinates voice recording playback during story sessions.

## Requirements

### Requirement 1: Ambient Audio Playback

**User Story:** As a child using Twin Spark Chronicles, I want to hear ambient sounds that match the story scene, so that the adventure feels real and immersive.

#### Acceptance Criteria

1. WHEN a new story beat is rendered with a scene description, THE Scene_Audio_Manager SHALL begin playing the corresponding Ambient_Track as a seamless loop.
2. WHILE an Ambient_Track is playing, THE Scene_Audio_Manager SHALL loop the Ambient_Track continuously without audible gaps or clicks at the loop boundary.
3. WHILE no scene description is available for the current story beat, THE Scene_Audio_Manager SHALL continue playing the previously active Ambient_Track.
4. IF the Ambient_Track file fails to load, THEN THE Scene_Audio_Manager SHALL log the error and continue the story experience without ambient audio.
5. THE Scene_Audio_Manager SHALL support a minimum of six Audio_Themes: "forest", "ocean", "castle", "space", "village", and "cave".

### Requirement 2: AI-Driven Scene-to-Audio Mapping

**User Story:** As a child, I want the ambient sounds to automatically match what is happening in the story, so that I do not have to think about audio and can stay immersed.

#### Acceptance Criteria

1. WHEN the backend generates a new story beat, THE Scene_Audio_Mapper SHALL analyze the scene description text and return an Audio_Theme identifier.
2. THE Scene_Audio_Mapper SHALL map scene descriptions to Audio_Themes using keyword matching against a configurable theme-to-keywords dictionary.
3. IF the scene description does not match any known Audio_Theme keywords, THEN THE Scene_Audio_Mapper SHALL return a default Audio_Theme of "village".
4. THE Scene_Audio_Mapper SHALL return the mapping result within 50 milliseconds for keyword-based matching.
5. WHEN the Scene_Audio_Mapper returns an Audio_Theme, THE response SHALL include the theme identifier, a primary Ambient_Track path, and an optional list of supplementary Sound_Effect paths.

### Requirement 3: Sound Effects for UI Interactions

**User Story:** As a child, I want to hear fun sounds when I tap choices, turn pages, and celebrate, so that every interaction feels rewarding and magical.

#### Acceptance Criteria

1. WHEN a child taps a choice card in DualStoryDisplay, THE Scene_Audio_Manager SHALL play a "choice_select" Sound_Effect within 100 milliseconds of the tap event.
2. WHEN the TransitionEngine begins a scene transition, THE Scene_Audio_Manager SHALL play a "page_turn" Sound_Effect synchronized with the transition animation start.
3. WHEN a CelebrationOverlay is triggered, THE Scene_Audio_Manager SHALL play a "celebration" Sound_Effect synchronized with the particle animation start.
4. THE Scene_Audio_Manager SHALL support at least three distinct Sound_Effect categories: "choice_select", "page_turn", and "celebration".
5. WHILE a Sound_Effect is playing, THE Scene_Audio_Manager SHALL allow the Ambient_Track to continue playing simultaneously without interruption.
6. IF a Sound_Effect file fails to load, THEN THE Scene_Audio_Manager SHALL skip the Sound_Effect silently without blocking the UI interaction.

### Requirement 4: Crossfade Between Ambient Tracks

**User Story:** As a child, I want the background sounds to change smoothly when the scene changes, so that the transition feels natural and not jarring.

#### Acceptance Criteria

1. WHEN the Audio_Theme changes between consecutive story beats, THE Crossfade_Engine SHALL fade out the current Ambient_Track and fade in the new Ambient_Track over a configurable duration.
2. THE Crossfade_Engine SHALL use a default crossfade duration of 2000 milliseconds.
3. WHILE a crossfade is in progress, THE Crossfade_Engine SHALL maintain the combined volume of both tracks at a level that does not exceed the configured ambient volume setting.
4. WHEN the TransitionEngine triggers a scene transition, THE Crossfade_Engine SHALL synchronize the ambient audio crossfade with the visual transition timing.
5. IF the same Audio_Theme is active for consecutive story beats, THEN THE Crossfade_Engine SHALL continue the current Ambient_Track without restarting or crossfading.
6. IF a crossfade is interrupted by a new scene change, THEN THE Crossfade_Engine SHALL cancel the in-progress crossfade and begin a new crossfade to the latest Audio_Theme.

### Requirement 5: Volume Controls and Mute Toggle

**User Story:** As a parent, I want to control the volume of ambient sounds and sound effects independently, so that I can adjust the audio experience for my children's comfort.

#### Acceptance Criteria

1. THE Volume_Controller SHALL provide separate volume sliders for ambient audio and sound effects, each ranging from 0 to 100.
2. THE Volume_Controller SHALL provide a master mute toggle that silences all scene audio (ambient and sound effects) with a single tap.
3. WHEN the master mute toggle is activated, THE Scene_Audio_Manager SHALL immediately silence all ambient audio and sound effects without affecting TTS or voice recording playback in the Audio_Store.
4. THE Volume_Controller SHALL persist volume and mute settings across browser sessions using local storage.
5. WHEN volume settings are changed, THE Scene_Audio_Manager SHALL apply the new volume level to currently playing audio within 100 milliseconds.
6. THE Volume_Controller SHALL render within the existing parent controls panel with touch targets of at least 56 pixels in height.

### Requirement 6: Integration with TransitionEngine

**User Story:** As a child, I want the sound effects to match the visual transitions between scenes, so that the experience feels polished and coordinated.

#### Acceptance Criteria

1. WHEN the TransitionEngine enters the "preparing" state, THE Scene_Audio_Manager SHALL preload the Ambient_Track for the incoming scene.
2. WHEN the TransitionEngine enters the "animating" state, THE Scene_Audio_Manager SHALL trigger the crossfade and play the "page_turn" Sound_Effect.
3. WHEN the TransitionEngine enters the "idle" state after a transition, THE Scene_Audio_Manager SHALL confirm the new Ambient_Track is playing at full configured volume.
4. WHILE the TransitionEngine is in "preparing" or "animating" state, THE Scene_Audio_Manager SHALL duck the ambient audio volume to 60% of the configured level to allow transition Sound_Effects to be clearly audible.
5. IF the TransitionEngine completes a reduced-motion instant swap, THEN THE Scene_Audio_Manager SHALL perform an instant audio swap without crossfade or transition Sound_Effects.

### Requirement 7: Accessibility and System Audio Compliance

**User Story:** As a parent of a child with sensory sensitivities, I want the audio system to respect accessibility settings, so that the experience is comfortable for all children.

#### Acceptance Criteria

1. WHEN the user's system has the "prefers-reduced-motion" media query active, THE Scene_Audio_Manager SHALL disable all transition Sound_Effects and perform instant audio swaps instead of crossfades.
2. THE Scene_Audio_Manager SHALL initialize with ambient audio muted and require an explicit user interaction before playing any audio, in compliance with browser autoplay policies.
3. WHEN the browser blocks audio autoplay, THE Scene_Audio_Manager SHALL display a child-friendly "Tap to hear sounds" prompt and resume audio playback after the first user interaction.
4. THE Volume_Controller sliders SHALL be operable via keyboard with arrow key increments of 5 units.
5. THE Volume_Controller mute toggle SHALL have an accessible label that announces the current mute state to screen readers.
6. WHILE the device is in silent or do-not-disturb mode, THE Scene_Audio_Manager SHALL respect the system audio routing and not override system volume restrictions.

### Requirement 8: Backend Audio Theme API

**User Story:** As a developer, I want a backend API endpoint that maps scene descriptions to audio themes, so that the frontend can request the correct audio for each scene.

#### Acceptance Criteria

1. THE Scene_Audio_Mapper SHALL expose a `POST /api/audio/scene-theme` endpoint that accepts a JSON body with a `scene_description` string field.
2. WHEN a valid scene description is provided, THE Scene_Audio_Mapper SHALL return a JSON response containing `theme` (string), `ambient_track` (string path), and `sound_effects` (array of string paths).
3. IF the `scene_description` field is missing or empty, THEN THE Scene_Audio_Mapper SHALL return a 422 status code with a descriptive error message.
4. THE Scene_Audio_Mapper SHALL serialize the response using Pydantic models for type safety and validation.
5. FOR ALL valid scene descriptions, mapping to a theme and then mapping back from that theme SHALL produce the same `ambient_track` path (round-trip consistency).

### Requirement 9: Audio Asset Preloading

**User Story:** As a child, I want the sounds to play instantly without delays, so that the magic is not broken by loading pauses.

#### Acceptance Criteria

1. WHEN the application initializes, THE Scene_Audio_Manager SHALL preload all Sound_Effect audio files (choice_select, page_turn, celebration) into memory.
2. WHEN the Scene_Audio_Mapper returns an Audio_Theme for an upcoming scene, THE Scene_Audio_Manager SHALL begin preloading the corresponding Ambient_Track before the transition starts.
3. THE Scene_Audio_Manager SHALL cache previously loaded Ambient_Tracks in memory to enable instant replay when revisiting a previously encountered Audio_Theme.
4. IF preloading an audio file takes longer than 5000 milliseconds, THEN THE Scene_Audio_Manager SHALL cancel the preload attempt and proceed without that audio asset.
5. THE Scene_Audio_Manager SHALL limit the audio cache to a maximum of 10 Ambient_Tracks to manage memory usage.

### Requirement 10: Coordination with Existing Audio Systems

**User Story:** As a developer, I want the scene audio system to coexist with TTS and voice recording playback, so that all audio sources work together without conflicts.

#### Acceptance Criteria

1. WHILE TTS narration is playing via the Audio_Store, THE Scene_Audio_Manager SHALL duck the ambient audio volume to 30% of the configured level.
2. WHILE a voice recording is playing via the Audio_Store, THE Scene_Audio_Manager SHALL duck the ambient audio volume to 30% of the configured level.
3. WHEN TTS narration or voice recording playback ends, THE Scene_Audio_Manager SHALL restore the ambient audio volume to the configured level over 500 milliseconds.
4. THE Scene_Audio_Manager SHALL use the Web Audio API for ambient audio and sound effects to enable precise volume control and mixing independent of the HTML Audio elements used by the Audio_Store.
5. WHEN the Audio_Store reset action is called, THE Scene_Audio_Manager SHALL also reset its own state and stop all ambient audio and sound effects.
