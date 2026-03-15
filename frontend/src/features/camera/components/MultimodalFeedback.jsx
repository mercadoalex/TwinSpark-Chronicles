import React from 'react';
import { useMultimodalStore } from '../../../stores/multimodalStore.js';
import './MultimodalFeedback.css';

/**
 * MultimodalFeedback
 *
 * Child-friendly overlay that shows:
 * - Speech bubble with transcribed text (auto-hides after 3s via store)
 * - Animated "listening" indicator when VAD detects speech
 * - Friendly mic-off icon when microphone is unavailable
 * - "Ask a parent for help" prompt when all inputs are down
 *
 * Designed for 6-year-old children — fun, friendly, no technical jargon.
 *
 * Requirements: 10.2, 10.4, 10.5, 10.6
 */
const MultimodalFeedback = () => {
  const {
    lastTranscript,
    transcriptVisible,
    isSpeaking,
    micError,
    micActive,
    allInputsUnavailable,
  } = useMultimodalStore();

  // All inputs unavailable — ask a parent for help
  if (allInputsUnavailable) {
    return (
      <div className="multimodal-feedback" aria-live="assertive">
        <div className="feedback-help">
          <span className="feedback-help__icon" aria-hidden="true">🆘</span>
          <p className="feedback-help__text">Ask a parent for help!</p>
        </div>
      </div>
    );
  }

  const micUnavailable = micError != null && !micActive;

  return (
    <div className="multimodal-feedback" aria-live="polite">
      {/* Speech bubble with transcribed text */}
      {transcriptVisible && lastTranscript?.text && (
        <div className="feedback-speech-bubble" role="status" aria-label="You said">
          <span className="feedback-speech-bubble__text">{lastTranscript.text}</span>
          <div className="feedback-speech-bubble__tail" aria-hidden="true" />
        </div>
      )}

      {/* Listening indicator — animated dots when VAD detects speech */}
      {isSpeaking && !micUnavailable && (
        <div className="feedback-listening" role="status" aria-label="Listening">
          <span className="feedback-listening__icon" aria-hidden="true">🎤</span>
          <span className="feedback-listening__dots">
            <span className="dot" />
            <span className="dot" />
            <span className="dot" />
          </span>
        </div>
      )}

      {/* Friendly mic-off icon — no technical error messages */}
      {micUnavailable && (
        <div className="feedback-mic-off" role="status" aria-label="Microphone is off">
          <span className="feedback-mic-off__icon" aria-hidden="true">🎤</span>
          <span className="feedback-mic-off__line" aria-hidden="true" />
        </div>
      )}
    </div>
  );
};

export default MultimodalFeedback;
