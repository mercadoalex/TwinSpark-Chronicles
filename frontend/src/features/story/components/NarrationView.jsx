import React, { useState, useEffect, useRef } from 'react';
import './NarrationView.css';

/**
 * NarrationView — Single-narrative display with scene illustration and text.
 *
 * Layout (portrait):
 *   Top 50-60%: scene illustration (crossfade transitions)
 *   Middle 15-20%: narration text (large rounded font, 22px, sentence highlighting)
 *   Bottom 25-30%: interaction controls slot (children prop)
 *
 * Requirements: 5.1, 5.2, 5.3, 5.4, 5.6, 11.1, 11.2, 11.3, 11.4, 11.6
 *
 * @param {Object} props
 * @param {Object|null} props.beat - Current story beat { narration, illustrationUrl, suggestions, perspective, isMilestone }
 * @param {number} props.highlightedSentence - Index of sentence currently being read by TTS
 * @param {string} props.activeTwinAvatar - Avatar URL or emoji for the active twin
 * @param {string} props.activeTwinColor - Color string for the active twin's accent
 * @param {React.ReactNode} props.children - Interaction controls slot (mic button, suggestion cards, etc.)
 */
function NarrationView({ beat, highlightedSentence = 0, activeTwinAvatar, activeTwinColor, children }) {
  const [currentImage, setCurrentImage] = useState(null);
  const [previousImage, setPreviousImage] = useState(null);
  const [isTransitioning, setIsTransitioning] = useState(false);
  const transitionTimeoutRef = useRef(null);

  // Handle crossfade animation on beat change (Req 5.4)
  useEffect(() => {
    const newUrl = beat?.illustrationUrl || null;

    if (newUrl !== currentImage) {
      // Start crossfade transition
      setPreviousImage(currentImage);
      setCurrentImage(newUrl);
      setIsTransitioning(true);

      // Clear previous timeout
      if (transitionTimeoutRef.current) {
        clearTimeout(transitionTimeoutRef.current);
      }

      // End transition after crossfade duration (400ms)
      transitionTimeoutRef.current = setTimeout(() => {
        setPreviousImage(null);
        setIsTransitioning(false);
      }, 400);
    }

    return () => {
      if (transitionTimeoutRef.current) {
        clearTimeout(transitionTimeoutRef.current);
      }
    };
  }, [beat?.illustrationUrl]); // eslint-disable-line react-hooks/exhaustive-deps

  /**
   * Split narration into sentences on sentence-ending punctuation (.!?)
   * and wrap each in a span for TTS highlighting (Req 4.3, 5.2).
   */
  const renderNarration = () => {
    if (!beat?.narration) return null;

    // Split on sentence-ending punctuation, keeping the delimiter
    const parts = beat.narration.split(/([.!?]+)/);
    const sentences = [];
    let current = '';

    for (let i = 0; i < parts.length; i++) {
      current += parts[i];
      // If this part is punctuation (delimiter), push the sentence
      if (/^[.!?]+$/.test(parts[i])) {
        if (current.trim()) {
          sentences.push(current.trim());
        }
        current = '';
      }
    }
    // Remaining text without trailing punctuation
    if (current.trim()) {
      sentences.push(current.trim());
    }

    return sentences.map((sentence, idx) => (
      <span
        key={idx}
        className={`narration-view__sentence ${
          idx === highlightedSentence ? 'narration-view__sentence--highlighted' : ''
        }`}
      >
        {sentence}{' '}
      </span>
    ));
  };

  /**
   * Render the active twin avatar overlay on the scene illustration (Req 5.6).
   */
  const renderAvatarOverlay = () => {
    if (!activeTwinAvatar) return null;

    const isUrl = activeTwinAvatar.startsWith('http') || activeTwinAvatar.startsWith('/');

    return (
      <div
        className="narration-view__avatar-overlay"
        style={{ '--avatar-color': activeTwinColor || 'rgba(255, 255, 255, 0.6)' }}
        aria-label="Active twin"
      >
        {isUrl ? (
          <img src={activeTwinAvatar} alt="Active twin avatar" />
        ) : (
          <span aria-hidden="true">{activeTwinAvatar}</span>
        )}
      </div>
    );
  };

  return (
    <div className="narration-view" aria-label="Story narration view">
      {/* Scene Illustration — top 50-60% (Req 5.1) */}
      <div className="narration-view__scene">
        {/* Current image with crossfade */}
        {currentImage ? (
          <img
            className={`narration-view__illustration ${
              !isTransitioning ? 'narration-view__illustration--active' : ''
            } ${isTransitioning ? 'narration-view__illustration--active' : ''}`}
            src={currentImage}
            alt="Story scene illustration"
          />
        ) : (
          <div className="narration-view__placeholder">
            <span className="narration-view__placeholder-icon" aria-hidden="true">✨</span>
          </div>
        )}

        {/* Previous image fading out during transition */}
        {isTransitioning && previousImage && (
          <img
            className="narration-view__illustration narration-view__illustration--exiting"
            src={previousImage}
            alt=""
            aria-hidden="true"
          />
        )}

        {/* Gradient fade for text readability */}
        <div className="narration-view__scene-fade" />

        {/* Active twin avatar overlay (Req 5.6) */}
        {renderAvatarOverlay()}
      </div>

      {/* Narration Text — middle 15-20% (Req 5.2, 11.2) */}
      <div className="narration-view__text-area" aria-live="polite">
        <p className="narration-view__narration">
          {renderNarration()}
        </p>
      </div>

      {/* Interaction Controls Slot — bottom 25-30% (Req 11.2, 11.3) */}
      <div className="narration-view__controls">
        {children}
      </div>
    </div>
  );
}

export default NarrationView;
