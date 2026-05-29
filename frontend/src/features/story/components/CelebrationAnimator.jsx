import React, { useState, useEffect, useRef } from 'react';
import CelebrationOverlay from '../../../shared/components/CelebrationOverlay';
import './CelebrationAnimator.css';

/**
 * CelebrationAnimator — Handles milestone celebrations and fun loading animations.
 *
 * Two modes:
 * 1. Milestone celebration: Triggers sparkles/confetti/star burst via CelebrationOverlay
 *    when `isMilestone` becomes true. Auto-dismisses after 1.5-2 seconds.
 * 2. Processing animation: Shows bouncing stars and swirling sparkles while
 *    `isProcessing` is true, replacing a standard spinner with child-friendly fun.
 *
 * Reduced-motion: replaces all animations with a simple opacity pulse/fade.
 *
 * Requirements: 8.4, 8.5, 8.7
 *
 * @param {Object} props
 * @param {boolean} props.isMilestone - Triggers celebration effect on story milestone beats
 * @param {boolean} props.isProcessing - Shows fun loading animation during AI generation
 */
function CelebrationAnimator({ isMilestone = false, isProcessing = false }) {
  const [showCelebration, setShowCelebration] = useState(false);
  const celebrationTimerRef = useRef(null);

  // Trigger celebration when isMilestone becomes true
  useEffect(() => {
    if (isMilestone) {
      setShowCelebration(true);

      // Auto-dismiss after 1.8 seconds (within 1.5-2s range)
      celebrationTimerRef.current = setTimeout(() => {
        setShowCelebration(false);
      }, 1800);
    }

    return () => {
      if (celebrationTimerRef.current) {
        clearTimeout(celebrationTimerRef.current);
      }
    };
  }, [isMilestone]);

  return (
    <>
      {/* Milestone celebration — reuses CelebrationOverlay for particle effects (Req 8.4) */}
      {showCelebration && (
        <CelebrationOverlay
          type="star-shower"
          duration={1800}
          particleCount={40}
        />
      )}

      {/* Fun processing/loading animation — bouncing stars + swirling sparkles (Req 8.5) */}
      {isProcessing && (
        <div
          className="celebration-animator__processing"
          role="status"
          aria-label="Creating your story..."
        >
          <div className="celebration-animator__orbit" aria-hidden="true">
            <span className="celebration-animator__star celebration-animator__star--1">⭐</span>
            <span className="celebration-animator__star celebration-animator__star--2">✨</span>
            <span className="celebration-animator__star celebration-animator__star--3">🌟</span>
            <span className="celebration-animator__star celebration-animator__star--4">💫</span>
          </div>
          <div className="celebration-animator__bounce" aria-hidden="true">
            <span className="celebration-animator__dot celebration-animator__dot--1" />
            <span className="celebration-animator__dot celebration-animator__dot--2" />
            <span className="celebration-animator__dot celebration-animator__dot--3" />
          </div>
        </div>
      )}
    </>
  );
}

export default CelebrationAnimator;
