# Requirements Document

## Introduction

This document defines the requirements for the Multimodal Input Pipeline feature of TwinSpark Chronicles. The pipeline captures camera video, audio input, and facial emotion detection from two 6-year-old children (Ale & Sofi), fuses these signals into a unified input stream, and delivers them to the existing backend agent system over WebSocket. The pipeline must be child-friendly, handle small faces, tolerate noisy home environments, and degrade gracefully when hardware is unavailable.

## Glossary

- **Camera_Service**: The frontend module that manages webcam access via the browser MediaDevices API, captures video frames, and provides them to downstream consumers.
- **Audio_Input_Service**: The frontend module that captures microphone audio, performs voice activity detection, and streams audio segments for speech-to-text processing.
- **STT_Service**: The backend service that receives audio segments and converts them to text using Google Cloud Speech-to-Text, returning transcribed commands and story responses.
- **Face_Detector**: The backend service that uses MediaPipe Face Detection to locate child faces in video frames and extract face bounding boxes.
- **Emotion_Detector**: The backend service that analyzes detected face regions and classifies the child's emotional state into one of the supported emotion categories.
- **Input_Manager**: The backend service that fuses camera, audio, and emotion signals into a single timestamped multimodal input event and forwards it to the Orchestrator.
- **Orchestrator**: The existing AgentOrchestrator that coordinates storyteller, visual, voice, and memory agents (already built in `backend/app/agents/orchestrator.py`).
- **Multimodal_Input_Event**: A structured data object containing the fused result of speech transcript, detected emotion, face presence, and a timestamp.
- **Emotion_Category**: One of the supported emotion labels: happy, sad, surprised, angry, scared, neutral.
- **VAD**: Voice Activity Detection — the process of determining whether an audio segment contains human speech.
- **Confidence_Score**: A floating-point value between 0.0 and 1.0 representing the certainty of a detection or classification result.

## Requirements

### Requirement 1: Camera Access and Frame Capture

**User Story:** As a child user, I want the app to see me through the camera, so that the story can react to my expressions.

#### Acceptance Criteria

1. WHEN the story session starts, THE Camera_Service SHALL request webcam access from the browser using the MediaDevices API with a resolution constraint of 640x480 or lower.
2. WHEN the user grants camera permission, THE Camera_Service SHALL begin capturing video frames at a rate between 1 and 5 frames per second for processing (independent of the live preview frame rate).
3. WHEN the user denies camera permission, THE Camera_Service SHALL emit a "camera_unavailable" event and THE Input_Manager SHALL continue operating with audio-only input.
4. IF the camera stream disconnects during a session, THEN THE Camera_Service SHALL emit a "camera_lost" event, attempt reconnection once after 3 seconds, and fall back to audio-only mode if reconnection fails.
5. THE Camera_Service SHALL mirror the video preview horizontally so children see a natural mirror image of themselves.
6. THE Camera_Service SHALL encode captured frames as JPEG with a quality factor between 60 and 80 before transmitting them to the backend.

### Requirement 2: Audio Capture and Voice Activity Detection

**User Story:** As a child user, I want to talk to the story, so that my voice controls what happens next.

#### Acceptance Criteria

1. WHEN the story session starts, THE Audio_Input_Service SHALL request microphone access from the browser using the MediaDevices API.
2. WHEN the user grants microphone permission, THE Audio_Input_Service SHALL begin capturing audio using the Web Audio API at a sample rate of 16 kHz mono.
3. THE Audio_Input_Service SHALL perform client-side voice activity detection and transmit only audio segments that contain detected speech.
4. WHEN the VAD detects speech onset, THE Audio_Input_Service SHALL begin buffering audio data and continue until 800 milliseconds of silence is detected.
5. WHEN the user denies microphone permission, THE Audio_Input_Service SHALL emit a "mic_unavailable" event and THE Input_Manager SHALL continue operating with camera-only input.
6. IF the microphone stream disconnects during a session, THEN THE Audio_Input_Service SHALL emit a "mic_lost" event and attempt reconnection once after 3 seconds.

### Requirement 3: Speech-to-Text Processing

**User Story:** As a child user, I want the app to understand what I say, so that I can talk to the characters in the story.

#### Acceptance Criteria

1. WHEN the STT_Service receives an audio segment from the Audio_Input_Service, THE STT_Service SHALL transcribe the audio using Google Cloud Speech-to-Text.
2. THE STT_Service SHALL support English ("en-US") and Spanish ("es-ES") transcription based on the session language setting.
3. THE STT_Service SHALL return a transcript object containing the transcribed text and a Confidence_Score.
4. WHEN the Confidence_Score of a transcript is below 0.4, THE STT_Service SHALL discard the transcript and return an empty result.
5. THE STT_Service SHALL complete transcription of a single audio segment within 3 seconds of receiving it.
6. IF the Google Cloud Speech-to-Text API is unreachable, THEN THE STT_Service SHALL return an error event with the code "stt_unavailable" and THE Input_Manager SHALL continue operating with camera-only input.
7. THE STT_Service SHALL apply a child-optimized speech model configuration by enabling automatic punctuation and setting the speech context with common child vocabulary (e.g., "dragon", "magic", "adventure", "let's go", "yes", "no").

### Requirement 4: Face Detection

**User Story:** As a child user, I want the app to find my face, so that it can tell how I'm feeling.

#### Acceptance Criteria

1. WHEN the Face_Detector receives a video frame, THE Face_Detector SHALL detect all faces in the frame using MediaPipe Face Detection.
2. THE Face_Detector SHALL return a list of face bounding boxes, each with a Confidence_Score.
3. THE Face_Detector SHALL use the short-range detection model (optimized for faces within 2 meters of the camera) to handle children sitting close to a screen.
4. WHEN no face is detected in a frame, THE Face_Detector SHALL return an empty list.
5. THE Face_Detector SHALL process a single 640x480 frame within 200 milliseconds.
6. THE Face_Detector SHALL set a minimum detection confidence threshold of 0.5 to reduce false positives.

### Requirement 5: Emotion Detection from Facial Expressions

**User Story:** As a child user, I want the story to know when I'm happy or scared, so that the adventure changes to match my feelings.

#### Acceptance Criteria

1. WHEN the Emotion_Detector receives a face bounding box from the Face_Detector, THE Emotion_Detector SHALL classify the facial expression into one Emotion_Category: happy, sad, surprised, angry, scared, or neutral.
2. THE Emotion_Detector SHALL return the classified Emotion_Category along with a Confidence_Score.
3. WHEN the Confidence_Score of an emotion classification is below 0.3, THE Emotion_Detector SHALL return "neutral" as the default Emotion_Category.
4. THE Emotion_Detector SHALL use a lightweight classification approach suitable for real-time processing (MediaPipe Face Mesh landmarks or a small CNN model).
5. THE Emotion_Detector SHALL process a single face region within 100 milliseconds.
6. WHEN multiple faces are detected, THE Emotion_Detector SHALL classify each face independently and return an emotion result per face.

### Requirement 6: Multimodal Input Fusion

**User Story:** As a developer, I want a unified input event that combines speech, emotion, and face data, so that the Orchestrator can make informed story decisions.

#### Acceptance Criteria

1. THE Input_Manager SHALL combine the latest speech transcript, emotion classification, and face detection results into a single Multimodal_Input_Event.
2. THE Input_Manager SHALL produce a Multimodal_Input_Event within 500 milliseconds of receiving the last contributing signal (speech or emotion).
3. WHEN only audio input is available (camera unavailable), THE Input_Manager SHALL produce a Multimodal_Input_Event containing the speech transcript with the emotion field set to "neutral" and face_detected set to false.
4. WHEN only camera input is available (microphone unavailable), THE Input_Manager SHALL produce a Multimodal_Input_Event containing the detected emotion with the transcript field set to an empty string.
5. WHEN neither camera nor microphone is available, THE Input_Manager SHALL emit an "all_inputs_unavailable" event to the frontend.
6. THE Input_Manager SHALL include a UTC timestamp in ISO 8601 format in each Multimodal_Input_Event.
7. THE Input_Manager SHALL not produce duplicate Multimodal_Input_Events for the same speech segment.

### Requirement 7: Multimodal Input Event Serialization

**User Story:** As a developer, I want Multimodal_Input_Events to be serialized and deserialized reliably, so that data is not lost between frontend and backend.

#### Acceptance Criteria

1. THE Input_Manager SHALL serialize each Multimodal_Input_Event to JSON format for transmission over WebSocket.
2. THE Input_Manager SHALL deserialize received JSON messages back into Multimodal_Input_Event objects.
3. FOR ALL valid Multimodal_Input_Event objects, serializing to JSON then deserializing back SHALL produce an equivalent object (round-trip property).
4. WHEN the Input_Manager receives a malformed JSON message, THE Input_Manager SHALL log the error and discard the message without crashing.

### Requirement 8: WebSocket Integration for Multimodal Data

**User Story:** As a developer, I want multimodal input data to flow through the existing WebSocket connection, so that the system uses a single communication channel.

#### Acceptance Criteria

1. THE Camera_Service and Audio_Input_Service SHALL transmit captured data to the backend through the existing WebSocket connection at `/ws/{session_id}`.
2. WHEN the frontend sends a video frame, THE frontend SHALL send a WebSocket message with type "camera_frame" containing the base64-encoded JPEG frame data.
3. WHEN the frontend sends an audio segment, THE frontend SHALL send a WebSocket message with type "audio_segment" containing the base64-encoded audio data.
4. WHEN the backend produces a Multimodal_Input_Event, THE backend SHALL forward the event to the Orchestrator by calling `generate_rich_story_moment` with the multimodal context.
5. THE WebSocket handler SHALL process "camera_frame" and "audio_segment" messages concurrently without blocking story generation messages.
6. IF the WebSocket connection drops while multimodal data is being transmitted, THEN THE frontend SHALL buffer up to 5 seconds of input data and retransmit after reconnection.

### Requirement 9: Orchestrator Integration with Multimodal Input

**User Story:** As a developer, I want the Orchestrator to use emotion and speech data when generating stories, so that the narrative adapts to the children's reactions.

#### Acceptance Criteria

1. WHEN the Orchestrator receives a Multimodal_Input_Event, THE Orchestrator SHALL pass the speech transcript as the `user_input` parameter to the storyteller agent.
2. WHEN the Orchestrator receives a Multimodal_Input_Event with an Emotion_Category other than "neutral", THE Orchestrator SHALL include the detected emotion in the story context passed to the storyteller agent.
3. WHEN the detected Emotion_Category is "scared", THE Orchestrator SHALL instruct the storyteller agent to reduce story intensity and introduce comforting story elements.
4. THE Orchestrator SHALL store the detected Emotion_Category in the memory agent for session history tracking.
5. WHEN two faces are detected with different emotions, THE Orchestrator SHALL use the emotion of the child whose name matches the current story perspective.

### Requirement 10: Child-Friendly Error Handling and Feedback

**User Story:** As a child user, I want the app to keep working even if the camera or microphone has problems, so that my story is not interrupted.

#### Acceptance Criteria

1. WHEN the Camera_Service emits a "camera_unavailable" or "camera_lost" event, THE frontend SHALL display a friendly icon indicating camera is off without showing technical error messages.
2. WHEN the Audio_Input_Service emits a "mic_unavailable" or "mic_lost" event, THE frontend SHALL display a friendly icon indicating microphone is off without showing technical error messages.
3. THE frontend SHALL display a visual indicator (animated border or emoji overlay) on the camera preview when an emotion is successfully detected.
4. WHEN the STT_Service successfully transcribes speech, THE frontend SHALL briefly display the transcribed text in a speech bubble overlay for 3 seconds.
5. THE frontend SHALL provide an animated "listening" indicator when the VAD detects active speech.
6. IF all input modalities become unavailable, THEN THE frontend SHALL display a message prompting the child to ask a parent for help, using simple language and a large help icon.

### Requirement 11: Privacy and Safety for Child Data

**User Story:** As a parent, I want camera and audio data to be handled safely, so that my children's data is protected.

#### Acceptance Criteria

1. THE Camera_Service SHALL NOT persist any video frames to disk or local storage on the client.
2. THE Audio_Input_Service SHALL NOT persist any audio recordings to disk or local storage on the client.
3. THE backend SHALL NOT store raw video frames or audio recordings after processing is complete.
4. THE backend SHALL retain only the derived Emotion_Category and speech transcript text in the memory agent, not the source media.
5. WHEN a session ends, THE backend SHALL discard all buffered video frames and audio segments associated with that session within 5 seconds.
6. THE Camera_Service SHALL only activate after the parent has accepted the privacy consent in the existing PrivacyModal.
