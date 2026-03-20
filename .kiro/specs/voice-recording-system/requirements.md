# Requirements Document

## Introduction

The Voice Recording System enables family members — grandparents, parents, and siblings — to record personal voice messages that are woven into TwinSpark Chronicles story sessions. Instead of relying solely on synthesized TTS voices, stories can feature real family voices delivering bedtime intros, encouragement, silly sound effects, and custom voice commands. This transforms storytelling from a generic AI experience into something deeply personal: Ale and Sofi hear abuela's actual voice welcoming them to an adventure, or papá cheering them on when they make a brave choice. The system handles recording, storage, metadata tagging, playback integration with the Orchestrator, and prepares voice samples for future voice cloning/synthesis capabilities.

## Glossary

- **Voice_Recorder**: The frontend component that captures audio from a family member's microphone, provides recording controls, and submits the audio to the backend.
- **Voice_Recording_Service**: The backend service responsible for receiving, validating, processing, storing, and retrieving voice recordings.
- **Recording_Store**: The persistent storage layer (via DatabaseConnection and filesystem) that holds voice recording audio files and associated metadata.
- **Voice_Recording**: A single audio recording made by a family member, consisting of an audio file and metadata (recorder identity, message type, duration, language, timestamps).
- **Family_Recorder**: The person who created a voice recording, identified by name and relationship to the children (e.g., "Abuela María", "Papá").
- **Message_Type**: A category describing the purpose of a recording: STORY_INTRO, ENCOURAGEMENT, SOUND_EFFECT, VOICE_COMMAND, or CUSTOM.
- **Playback_Integrator**: The backend module within the Orchestrator that selects and triggers voice recording playback at appropriate moments during story generation.
- **Voice_Library**: The UI view where parents can browse, preview, manage, and assign voice recordings to story trigger points.
- **Trigger_Point**: A story event or condition that causes a voice recording to be played (e.g., session start, brave decision, story chapter transition).
- **Voice_Sample**: A processed audio excerpt suitable for future voice cloning or synthesis model training.
- **Audio_Normalizer**: The backend module that normalizes audio levels, trims silence, and converts recordings to a standard format for consistent playback quality.

## Requirements

### Requirement 1: Voice Recording Capture

**User Story:** As a family member, I want to record a voice message for Ale and Sofi using my device microphone, so that the children hear my real voice during their story adventures.

#### Acceptance Criteria

1. WHEN a family member taps the record button, THE Voice_Recorder SHALL request microphone access and begin capturing audio from the device microphone.
2. WHILE recording is active, THE Voice_Recorder SHALL display a real-time waveform visualization and an elapsed-time counter so the recorder can see that audio is being captured.
3. WHEN the elapsed time reaches 60 seconds, THE Voice_Recorder SHALL automatically stop recording and notify the family member that the maximum duration has been reached.
4. WHEN the family member taps the stop button, THE Voice_Recorder SHALL stop capturing audio and present a playback preview with options to re-record or confirm.
5. IF the device microphone is unavailable or permission is denied, THEN THE Voice_Recorder SHALL display a clear message explaining that microphone access is required and provide a link to device settings.
6. THE Voice_Recorder SHALL capture audio at a minimum sample rate of 16 kHz mono to ensure clarity for child listeners.

### Requirement 2: Recording Metadata and Tagging

**User Story:** As a parent, I want each voice recording to be tagged with who recorded it, what type of message it is, and in which language, so that the system can select the right recording at the right moment in a story.

#### Acceptance Criteria

1. WHEN a recording is confirmed, THE Voice_Recorder SHALL prompt the family member to provide a recorder name, select a relationship (grandparent, parent, sibling, other), and choose a Message_Type (STORY_INTRO, ENCOURAGEMENT, SOUND_EFFECT, VOICE_COMMAND, or CUSTOM).
2. WHEN metadata is submitted, THE Voice_Recording_Service SHALL validate that the recorder name is non-empty and the Message_Type is one of the five defined categories.
3. IF required metadata fields are missing or invalid, THEN THE Voice_Recording_Service SHALL reject the submission and return a descriptive error indicating which fields need correction.
4. WHEN a recording is stored, THE Voice_Recording_Service SHALL persist the following metadata alongside the audio: recorder name, relationship, Message_Type, language code (en or es), duration in seconds, sibling pair identifier, and creation timestamp.
5. THE Voice_Recording_Service SHALL automatically detect the language of the recording based on the active session language setting and store the corresponding language code.

### Requirement 3: Audio Processing and Normalization

**User Story:** As a child listener, I want all voice recordings to sound clear and at a consistent volume, so that grandma's quiet phone recording and papá's loud laptop recording both sound good during the story.

#### Acceptance Criteria

1. WHEN a confirmed recording is received by the Voice_Recording_Service, THE Audio_Normalizer SHALL convert the audio to WAV format at 16 kHz, 16-bit, mono as the canonical storage format.
2. WHEN processing a recording, THE Audio_Normalizer SHALL normalize the audio peak amplitude to -3 dBFS to ensure consistent playback volume across recordings from different devices.
3. WHEN processing a recording, THE Audio_Normalizer SHALL trim leading and trailing silence exceeding 500 milliseconds from the audio.
4. IF the processed recording duration is less than 1 second after trimming, THEN THE Voice_Recording_Service SHALL reject the recording and inform the family member that the recording is too short.
5. WHEN processing is complete, THE Audio_Normalizer SHALL generate an MP3 version of the normalized audio for efficient streaming playback during stories.
6. THE Audio_Normalizer SHALL complete all processing steps within 3 seconds for a 60-second recording.

### Requirement 4: Voice Recording Storage and Persistence

**User Story:** As a parent, I want voice recordings to persist across app sessions and be associated with our family, so that recordings made by grandparents months ago are still available for tonight's story.

#### Acceptance Criteria

1. THE Recording_Store SHALL persist all voice recording audio files and metadata across application restarts.
2. THE Recording_Store SHALL associate all voice recordings with a sibling pair identifier so that different families using the same device have isolated voice libraries.
3. WHEN a voice recording is stored, THE Voice_Recording_Service SHALL save both the canonical WAV file and the streaming MP3 file to the Recording_Store and return a unique recording identifier.
4. WHEN a recording is requested by identifier, THE Voice_Recording_Service SHALL return the recording metadata and a streamable audio URL.
5. THE Recording_Store SHALL enforce a maximum of 50 voice recordings per sibling pair to manage storage usage.
6. IF a sibling pair has reached the 50-recording limit, THEN THE Voice_Recording_Service SHALL reject new uploads and suggest deleting older recordings.
7. FOR ALL valid voice recordings, storing then loading a recording by identifier SHALL produce equivalent metadata and audio content (round-trip property).

### Requirement 5: Voice Library Management

**User Story:** As a parent, I want to browse, preview, and delete voice recordings in a library view, so that I stay in control of which family voices are used in stories.

#### Acceptance Criteria

1. THE Voice_Library SHALL display all voice recordings for the current sibling pair, grouped by Family_Recorder and sorted by creation date within each group.
2. WHEN a parent taps a recording in the Voice_Library, THE Voice_Library SHALL play the MP3 audio preview inline without navigating away from the library view.
3. WHEN a parent requests deletion of a recording, THE Voice_Recording_Service SHALL remove the audio files (WAV and MP3), all associated metadata, and any Trigger_Point assignments from the Recording_Store.
4. WHEN a recording is deleted, THE Voice_Recording_Service SHALL notify the parent if any active story Trigger_Points were using the deleted recording.
5. THE Voice_Library SHALL display the total number of recordings and remaining capacity (out of 50) for the sibling pair.
6. THE Voice_Library SHALL allow filtering recordings by Message_Type and by Family_Recorder.

### Requirement 6: Story Playback Integration

**User Story:** As a child, I want to hear abuela's real voice welcoming me to the adventure and papá cheering me on when I'm brave, so that the story feels like my whole family is part of it.

#### Acceptance Criteria

1. WHEN a story session begins and a STORY_INTRO recording exists for the active sibling pair, THE Playback_Integrator SHALL play the STORY_INTRO recording before the first story segment is narrated.
2. WHEN the Orchestrator generates a story moment tagged with a brave decision or achievement, THE Playback_Integrator SHALL play a matching ENCOURAGEMENT recording if one exists for the active sibling pair.
3. WHEN the Storyteller_Agent generates dialogue for a character mapped to a Family_Recorder via Character_Mapping, THE Playback_Integrator SHALL play the most relevant recording from that Family_Recorder instead of synthesized TTS audio.
4. WHEN a SOUND_EFFECT recording is available and the story context matches a playful or silly moment, THE Playback_Integrator SHALL mix the sound effect recording into the story audio.
5. IF no matching voice recording exists for a Trigger_Point, THEN THE Playback_Integrator SHALL fall back to the existing Google Cloud TTS voice synthesis without interrupting the story flow.
6. THE Playback_Integrator SHALL insert a 500-millisecond fade-in and fade-out on voice recording playback to blend smoothly with the surrounding TTS narration.
7. THE Playback_Integrator SHALL deliver the audio data to the frontend within 1 second of the Trigger_Point being reached.

### Requirement 7: Voice Command Customization

**User Story:** As a parent, I want to record custom voice commands that my children can use to control the story, so that Ale and Sofi can say a special family phrase to trigger story actions.

#### Acceptance Criteria

1. WHEN a parent records a VOICE_COMMAND type recording, THE Voice_Recorder SHALL prompt the parent to specify the command phrase (e.g., "¡Aventura mágica!") and the associated story action (e.g., "start adventure", "call for help", "use magic").
2. WHEN a VOICE_COMMAND recording is stored, THE Voice_Recording_Service SHALL persist the command phrase and associated action alongside the audio metadata.
3. WHEN a child speaks during a story session, THE STT_Service SHALL compare the transcribed speech against registered VOICE_COMMAND phrases for the active sibling pair.
4. WHEN a spoken phrase matches a registered VOICE_COMMAND with a similarity score above 0.7, THE Playback_Integrator SHALL trigger the associated story action and play the parent's recorded command audio as confirmation feedback.
5. IF a spoken phrase does not match any registered VOICE_COMMAND, THEN THE STT_Service SHALL process the speech as normal story input without error.
6. THE Voice_Recording_Service SHALL support a maximum of 10 custom voice commands per sibling pair.

### Requirement 8: Voice Sample Preparation for Future Cloning

**User Story:** As a product developer, I want voice recordings to be stored in a format suitable for future voice cloning model training, so that the system can eventually synthesize family member voices for full story narration.

#### Acceptance Criteria

1. WHEN a voice recording passes audio normalization, THE Voice_Recording_Service SHALL generate a Voice_Sample by extracting a clean speech segment (removing background noise above a signal-to-noise threshold of 20 dB).
2. THE Voice_Recording_Service SHALL store each Voice_Sample in WAV format at 22.05 kHz, 16-bit, mono — the standard input format for voice cloning models.
3. WHEN a Family_Recorder has 5 or more Voice_Samples stored, THE Voice_Recording_Service SHALL flag that Family_Recorder as "cloning-ready" in the metadata.
4. THE Voice_Recording_Service SHALL store Voice_Samples in a dedicated directory structure organized by Family_Recorder identifier for batch processing.
5. THE Voice_Sample generation SHALL preserve the original recording without modification — the Voice_Sample is an additional derived artifact.

### Requirement 9: Interaction Design for Young Children

**User Story:** As a 6-year-old child, I want the voice recording features to be fun and easy to use with big colorful buttons and voice guidance, so that I can record silly sounds for the story without needing to read.

#### Acceptance Criteria

1. THE Voice_Recorder SHALL use large touch targets (minimum 48x48 CSS pixels) and animated icons (pulsing microphone, bouncing waveform) instead of text labels for all primary recording actions.
2. WHEN the recording flow is active, THE Voice_Recorder SHALL play a short TTS voice prompt (via the existing Voice_Agent) explaining the current step in the active session language (English or Spanish).
3. WHEN a recording is successfully saved, THE Voice_Recorder SHALL play a celebratory animation (confetti burst) and a cheerful sound effect to reward the child.
4. THE Voice_Recorder SHALL present a maximum of 3 action choices at any time (record, play, done) to avoid overwhelming a young child.
5. WHILE recording is active, THE Voice_Recorder SHALL display a large animated character (from the child's story avatar) that reacts to the audio input level, making the recording feel like a game.

### Requirement 10: Privacy and Parental Controls

**User Story:** As a parent, I want full control over voice recordings including who can record, what gets stored, and the ability to delete everything, so that my family's voice data is handled responsibly.

#### Acceptance Criteria

1. WHEN a non-parent user attempts to access the Voice_Library management features (delete, assign triggers), THE Voice_Recording_Service SHALL require parent authentication via the existing parent PIN mechanism.
2. THE Voice_Recording_Service SHALL provide a "delete all recordings" action that removes all voice recordings, Voice_Samples, metadata, and Trigger_Point assignments for a sibling pair in a single operation.
3. WHEN a parent requests bulk deletion, THE Voice_Recording_Service SHALL require confirmation and complete the deletion within 5 seconds.
4. THE Voice_Recording_Service SHALL log all recording creation and deletion events with timestamps for parental audit purposes.
5. THE Recording_Store SHALL store all audio files on the local device filesystem in development mode and in encrypted cloud storage in production mode.
6. THE Voice_Recording_Service SHALL exclude voice recordings and Voice_Samples from any analytics, telemetry, or third-party data sharing.

### Requirement 11: Bilingual Support

**User Story:** As a bilingual family, I want to record voice messages in both English and Spanish and have the system play the right language version during stories, so that abuela can record in Spanish and grandpa can record in English.

#### Acceptance Criteria

1. WHEN a story session is active in a specific language, THE Playback_Integrator SHALL prefer voice recordings tagged with the matching language code (en or es).
2. IF no recording in the active session language exists for a Trigger_Point, THEN THE Playback_Integrator SHALL fall back to a recording in the other language from the same Family_Recorder.
3. IF no recording from the same Family_Recorder exists in either language, THEN THE Playback_Integrator SHALL fall back to TTS synthesis in the active session language.
4. THE Voice_Library SHALL display a language badge (🇺🇸 or 🇪🇸) on each recording to indicate the tagged language.
5. THE Voice_Recorder SHALL allow a family member to record the same Message_Type in both languages, storing each as a separate Voice_Recording.
