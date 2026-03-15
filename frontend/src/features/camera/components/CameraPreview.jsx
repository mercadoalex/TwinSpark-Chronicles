import React, { useRef, useEffect } from 'react';
import { useMultimodalStore } from '../../../stores/multimodalStore.js';
import { cameraService } from '../services/cameraService.js';
import './CameraPreview.css';

/**
 * Emotion-to-display mapping for child-friendly overlays.
 * Each emotion gets a border color and emoji.
 */
const EMOTION_MAP = {
  happy: { emoji: '😊', borderColor: '#4caf50' },
  sad: { emoji: '😢', borderColor: '#2196f3' },
  surprised: { emoji: '😮', borderColor: '#ffeb3b' },
  angry: { emoji: '😠', borderColor: '#f44336' },
  scared: { emoji: '😨', borderColor: '#9c27b0' },
};

/**
 * Get the primary (highest confidence) emotion from the list,
 * excluding "neutral" since it has no visual indicator.
 */
function getPrimaryEmotion(emotions) {
  if (!emotions || emotions.length === 0) return null;
  const nonNeutral = emotions.filter((e) => e.emotion !== 'neutral');
  if (nonNeutral.length === 0) return null;
  return nonNeutral.reduce((best, e) =>
    e.confidence > best.confidence ? e : best
  );
}

/**
 * CameraPreview
 *
 * Shows a mirrored live camera preview with emotion overlays.
 * When camera is unavailable, displays a friendly camera-off icon
 * (no technical error messages — this is for 6-year-olds).
 *
 * Requirements: 1.5, 10.1, 10.3
 */
const CameraPreview = () => {
  const videoRef = useRef(null);
  const { cameraActive, cameraError, currentEmotions } = useMultimodalStore();

  const cameraAvailable = cameraActive && !cameraError;
  const primaryEmotion = getPrimaryEmotion(currentEmotions);
  const emotionDisplay = primaryEmotion ? EMOTION_MAP[primaryEmotion.emotion] : null;

  // Attach the camera stream to the video element
  useEffect(() => {
    const videoEl = videoRef.current;
    if (!videoEl) return;

    if (cameraAvailable && cameraService.stream) {
      videoEl.srcObject = cameraService.stream;
      videoEl.play().catch(() => {});
    } else {
      videoEl.srcObject = null;
    }

    return () => {
      if (videoEl) videoEl.srcObject = null;
    };
  }, [cameraAvailable]);

  // Camera unavailable — show friendly icon
  if (!cameraAvailable) {
    return (
      <div className="camera-preview camera-preview--off" aria-label="Camera is off">
        <div className="camera-off-icon">📷</div>
        <p className="camera-off-text">Camera is off</p>
      </div>
    );
  }

  // Camera active — show mirrored preview with optional emotion overlay
  const borderStyle = emotionDisplay
    ? { borderColor: emotionDisplay.borderColor }
    : {};

  return (
    <div
      className={`camera-preview${emotionDisplay ? ' camera-preview--emotion' : ''}`}
      style={borderStyle}
      aria-label="Camera preview"
    >
      <video
        ref={videoRef}
        className="camera-preview__video"
        style={{ transform: cameraService.getMirrorStyle() }}
        autoPlay
        playsInline
        muted
      />
      {emotionDisplay && (
        <span className="camera-preview__emoji" aria-label={primaryEmotion.emotion}>
          {emotionDisplay.emoji}
        </span>
      )}
    </div>
  );
};

export default CameraPreview;
