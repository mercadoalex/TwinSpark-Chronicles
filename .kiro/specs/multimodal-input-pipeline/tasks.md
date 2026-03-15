# Implementation Plan: Multimodal Input Pipeline

## Overview

Incrementally build the multimodal input pipeline: start with backend data models and services (face detection, emotion, STT, input fusion), then extend the WebSocket handler, update the orchestrator, build frontend capture services and UI, and wire everything together.

## Tasks

- [x] 1. Create backend data models and core service stubs
  - [x] 1.1 Create Pydantic models in `backend/app/models/multimodal.py`
    - Define `EmotionCategory` enum, `FaceBBox`, `EmotionResult`, `TranscriptResult`, `MultimodalInputEvent` models
    - Implement `to_orchestrator_context()` and `_get_primary_emotion()` on `MultimodalInputEvent`
    - _Requirements: 5.1, 6.1, 6.6, 7.1, 7.2, 9.1, 9.2_

  - [ ]* 1.2 Write property test: Serialization round-trip (Property 1)
    - **Property 1: Serialization round-trip**
    - Use Hypothesis to generate random valid `MultimodalInputEvent` objects, serialize to JSON, deserialize back, and assert equivalence
    - **Validates: Requirements 7.1, 7.2, 7.3**

  - [ ]* 1.3 Write property test: Emotion category validity (Property 7)
    - **Property 7: Emotion category validity**
    - Assert every `EmotionResult` has an `emotion` field that is one of the six valid `EmotionCategory` values
    - **Validates: Requirements 5.1**

  - [ ]* 1.4 Write property test: Orchestrator context mapping (Property 12)
    - **Property 12: Orchestrator context mapping**
    - For any `MultimodalInputEvent`, `to_orchestrator_context()` returns `user_input` matching transcript text (or `None` if empty) and `emotion` matching highest-confidence emotion (or `"neutral"`)
    - **Validates: Requirements 9.1, 9.2**

- [x] 2. Implement Face_Detector service
  - [x] 2.1 Create `backend/app/services/face_detector.py`
    - Initialize MediaPipe Face Detection with short-range model and min confidence 0.5
    - Implement `detect(frame_bytes) -> list[FaceBBox]` that decodes JPEG, runs detection, returns bounding boxes
    - Ensure processing completes within 200ms for 640x480 frames
    - _Requirements: 4.1, 4.2, 4.3, 4.5, 4.6_

  - [ ]* 2.2 Write property test: Face detection confidence threshold (Property 4)
    - **Property 4: Face detection confidence threshold**
    - For any face in the output list, confidence >= 0.5
    - **Validates: Requirements 4.6**

- [x] 3. Implement Emotion_Detector service
  - [x] 3.1 Create `backend/app/services/emotion_detector.py`
    - Use MediaPipe Face Mesh landmarks or a small CNN for classification
    - Implement `classify(frame_bytes, bbox) -> EmotionResult` returning one of 6 emotion categories
    - Return `neutral` when confidence < 0.3
    - Process each face independently; complete within 100ms per face
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

  - [ ]* 3.2 Write property test: Low-confidence emotion defaults to neutral (Property 5)
    - **Property 5: Low-confidence emotion defaults to neutral**
    - For any raw classification with confidence < 0.3, output must be `EmotionCategory.NEUTRAL`
    - **Validates: Requirements 5.3**

  - [ ]* 3.3 Write property test: Face-to-emotion count preservation (Property 6)
    - **Property 6: Face-to-emotion count preservation**
    - For N input face bounding boxes, exactly N `EmotionResult` objects are returned
    - **Validates: Requirements 5.6**

- [x] 4. Implement STT_Service
  - [x] 4.1 Create `backend/app/services/stt_service.py`
    - Integrate Google Cloud Speech-to-Text with async transcription
    - Support `en-US` and `es-ES` based on session language
    - Apply child-optimized config: automatic punctuation, speech context with child vocabulary
    - Discard transcripts with confidence < 0.4 (return empty `TranscriptResult`)
    - Timeout at 3 seconds; return `stt_unavailable` error if API unreachable
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_

  - [ ]* 4.2 Write property test: Low-confidence transcript filtering (Property 3)
    - **Property 3: Low-confidence transcript filtering**
    - For any `TranscriptResult` with confidence < 0.4, result must have `is_empty=True` and `text=""`; for confidence >= 0.4, text is preserved
    - **Validates: Requirements 3.4**

- [x] 5. Implement Input_Manager (signal fusion)
  - [x] 5.1 Create `backend/app/services/input_manager.py`
    - Implement `fuse(transcript, emotions, faces_detected, timestamp) -> MultimodalInputEvent`
    - Include speech deduplication via `speech_id` tracking
    - Produce event within 500ms of last signal
    - Handle audio-only mode (no camera): emotions empty, face_detected=False
    - Handle camera-only mode (no mic): transcript empty
    - Emit `all_inputs_unavailable` when neither modality is available
    - Implement safe JSON deserialization that logs and discards malformed messages
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 7.1, 7.2, 7.3, 7.4_

  - [ ]* 5.2 Write property test: Malformed JSON resilience (Property 2)
    - **Property 2: Malformed JSON resilience**
    - For any arbitrary string that is not valid JSON or doesn't conform to schema, deserialization returns error without unhandled exception
    - **Validates: Requirements 7.4**

  - [ ]* 5.3 Write property test: Fusion completeness (Property 8)
    - **Property 8: Fusion completeness**
    - For any combination of transcript, emotions, and face_detected, `fuse()` produces a `MultimodalInputEvent` containing all signals and a valid ISO 8601 timestamp
    - **Validates: Requirements 6.1, 6.6**

  - [ ]* 5.4 Write property test: Audio-only degradation (Property 9)
    - **Property 9: Audio-only degradation**
    - When camera unavailable, event has empty emotions, `face_detected=False`, and transcript unchanged
    - **Validates: Requirements 1.3, 6.3**

  - [ ]* 5.5 Write property test: Camera-only degradation (Property 10)
    - **Property 10: Camera-only degradation**
    - When mic unavailable, event has `transcript.text=""`, `transcript.is_empty=True`, and camera data unchanged
    - **Validates: Requirements 2.5, 6.4**

  - [ ]* 5.6 Write property test: No duplicate events (Property 11)
    - **Property 11: No duplicate events for same speech segment**
    - Calling `fuse()` multiple times with the same `speech_id` produces at most one event
    - **Validates: Requirements 6.7**

- [x] 6. Checkpoint — Verify backend services
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Extend WebSocket handler for multimodal messages
  - [x] 7.1 Update `backend/app/main.py` WebSocket endpoint
    - Add handling for `camera_frame` and `audio_segment` message types
    - Decode base64 frame/audio data
    - Route camera frames to `FaceDetector` → `EmotionDetector` → `InputManager` using `asyncio.create_task`
    - Route audio segments to `STTService` → `InputManager` using `asyncio.create_task`
    - Forward resulting `MultimodalInputEvent` to orchestrator
    - Ensure concurrent processing does not block story generation messages
    - Add session cleanup: discard buffered frames/audio within 5 seconds of session end
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 11.3, 11.5_

  - [x] 7.2 Send feedback messages to frontend
    - Send `emotion_feedback` messages after emotion detection
    - Send `transcript_feedback` messages after STT
    - Send `input_status` messages on modality changes
    - _Requirements: 10.3, 10.4_

- [x] 8. Update Orchestrator for multimodal input
  - [x] 8.1 Modify `backend/app/agents/orchestrator.py`
    - Add `process_multimodal_event(event: MultimodalInputEvent)` method
    - Pass transcript as `user_input` to storyteller
    - Include detected emotion in story context when not "neutral"
    - When emotion is "scared", instruct storyteller to reduce intensity and add comforting elements
    - Handle two-face perspective matching using character names
    - Store detected emotion in memory agent via `store_story_moment()`
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

  - [ ]* 8.2 Write property test: Emotion stored in memory (Property 13)
    - **Property 13: Emotion stored in memory**
    - For any event with non-empty emotions processed by orchestrator, the `EmotionCategory` is included in moment data passed to `memory_agent.store_story_moment()`
    - **Validates: Requirements 9.4**

  - [ ]* 8.3 Write property test: Backend retains only derived data (Property 14)
    - **Property 14: Backend retains only derived data**
    - After processing, raw frame bytes and audio bytes are not referenced by any persistent storage; only derived emotion and transcript are retained
    - **Validates: Requirements 11.3, 11.4**

- [x] 9. Checkpoint — Verify backend integration
  - Ensure all tests pass, ask the user if questions arise.

- [x] 10. Build frontend Camera_Service
  - [x] 10.1 Create `frontend/src/features/camera/services/cameraService.js`
    - Request webcam via `getUserMedia` with 640x480 constraint
    - Capture frames at configurable rate (1-5 fps) using canvas
    - Mirror video preview horizontally via CSS transform
    - Encode frames as JPEG (quality 60-80) and return base64
    - Emit `camera_unavailable` on permission denial
    - Emit `camera_lost` on stream disconnect; retry once after 3 seconds
    - Only activate after privacy consent from PrivacyModal
    - Never persist frames to disk or localStorage
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 11.1, 11.6_

- [x] 11. Build frontend Audio_Input_Service
  - [x] 11.1 Create `frontend/src/features/camera/services/audioInputService.js`
    - Request mic via `getUserMedia`, capture at 16kHz mono using Web Audio API
    - Implement client-side VAD: detect speech onset, buffer until 800ms silence
    - Emit base64-encoded audio segments on speech end
    - Emit `mic_unavailable` on permission denial
    - Emit `mic_lost` on stream disconnect; retry once after 3 seconds
    - Never persist audio to disk or localStorage
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 11.2_

- [x] 12. Create multimodal Zustand store and React hook
  - [x] 12.1 Create `frontend/src/stores/multimodalStore.js`
    - Track camera/mic active state, current emotions, last transcript, speaking state
    - Track error states (`cameraError`, `micError`, `allInputsUnavailable`)
    - Track privacy consent and input buffer (max 5 seconds during disconnect)
    - _Requirements: 1.3, 2.5, 6.5, 8.6, 10.1, 10.2_

  - [x] 12.2 Create `frontend/src/features/camera/hooks/useMultimodalInput.js`
    - Coordinate Camera_Service and Audio_Input_Service
    - Send `camera_frame` and `audio_segment` messages over existing WebSocket
    - Listen for `emotion_feedback`, `transcript_feedback`, `input_status` from backend
    - Buffer up to 5 seconds of input data during WebSocket disconnect, retransmit on reconnect
    - Manage `startCapture(privacyConsented)` and `stopCapture()` lifecycle
    - _Requirements: 8.1, 8.2, 8.3, 8.6, 10.3, 10.4_

- [x] 13. Build frontend UI feedback components
  - [x] 13.1 Create `frontend/src/features/camera/components/CameraPreview.jsx`
    - Show mirrored camera preview
    - Display animated border or emoji overlay when emotion is detected
    - Show friendly camera-off icon when camera unavailable (no technical error messages)
    - _Requirements: 1.5, 10.1, 10.3_

  - [x] 13.2 Create `frontend/src/features/camera/components/MultimodalFeedback.jsx`
    - Show speech bubble overlay with transcribed text for 3 seconds
    - Show animated "listening" indicator during active speech (VAD)
    - Show friendly mic-off icon when mic unavailable (no technical error messages)
    - Show "ask a parent for help" message with large help icon when all inputs unavailable
    - _Requirements: 10.2, 10.4, 10.5, 10.6_

- [x] 14. Wire frontend components into the app
  - [x] 14.1 Integrate multimodal capture into session flow
    - Start capture after privacy consent and session start
    - Stop capture on session end
    - Connect `CameraPreview` and `MultimodalFeedback` to the story view
    - _Requirements: 1.1, 2.1, 11.6_

- [x] 15. Final checkpoint — End-to-end verification
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Backend uses Python (FastAPI, Pydantic, Hypothesis for tests); frontend uses JavaScript (React, Zustand, fast-check for tests)
- Each task references specific requirements for traceability
- Checkpoints at tasks 6, 9, and 15 ensure incremental validation
- Property tests validate universal correctness properties from the design document
- No raw media is persisted — only derived text and emotion labels are stored
