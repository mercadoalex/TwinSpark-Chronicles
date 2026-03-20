import { useState, useEffect, useRef, useCallback } from 'react';
import { useGalleryStore } from '../../../stores/galleryStore';
import CelebrationOverlay from '../../../shared/components/CelebrationOverlay';
import './StoryReader.css';

/**
 * StoryReader — Full-screen immersive reader for a single storybook.
 * Displays one beat at a time with page-turn transitions, swipe navigation,
 * and expandable perspective cards matching DualStoryDisplay patterns.
 */
export default function StoryReader({ storybookId, onClose }) {
  const { selectedStorybook, isLoading, error } = useGalleryStore();
  const [currentBeatIndex, setCurrentBeatIndex] = useState(0);
  const [showPerspectives, setShowPerspectives] = useState(false);
  const [transitionClass, setTransitionClass] = useState('');
  const [direction, setDirection] = useState('forward');

  // Touch/swipe tracking
  const touchStartX = useRef(0);

  // Fetch detail on mount, clear on unmount
  useEffect(() => {
    useGalleryStore.getState().fetchStorybookDetail(storybookId);
    return () => {
      useGalleryStore.getState().clearSelectedStorybook();
    };
  }, [storybookId]);

  const beats = selectedStorybook?.beats || [];
  const totalBeats = beats.length;
  const currentBeat = beats[currentBeatIndex];
  const isLastBeat = currentBeatIndex === totalBeats - 1;

  const navigateTo = useCallback((newIndex, dir) => {
    if (newIndex < 0 || newIndex >= totalBeats) return;
    setDirection(dir);
    setTransitionClass('reader-beat--exiting');
    setTimeout(() => {
      setCurrentBeatIndex(newIndex);
      setShowPerspectives(false);
      setTransitionClass('reader-beat--entering');
      setTimeout(() => setTransitionClass(''), 350);
    }, 300);
  }, [totalBeats]);

  const goForward = useCallback(() => {
    navigateTo(currentBeatIndex + 1, 'forward');
  }, [currentBeatIndex, navigateTo]);

  const goBackward = useCallback(() => {
    navigateTo(currentBeatIndex - 1, 'backward');
  }, [currentBeatIndex, navigateTo]);

  // Swipe gesture handlers
  const handleTouchStart = useCallback((e) => {
    touchStartX.current = e.touches[0].clientX;
  }, []);

  const handleTouchEnd = useCallback((e) => {
    const delta = touchStartX.current - e.changedTouches[0].clientX;
    if (Math.abs(delta) > 50) {
      if (delta > 0 && currentBeatIndex < totalBeats - 1) {
        goForward();
      } else if (delta < 0 && currentBeatIndex > 0) {
        goBackward();
      }
    }
  }, [currentBeatIndex, totalBeats, goForward, goBackward]);

  // Image error fallback
  const handleImageError = useCallback((e) => {
    e.target.style.display = 'none';
    if (e.target.nextSibling) {
      e.target.nextSibling.style.display = 'flex';
    }
  }, []);

  // Loading state
  if (isLoading) {
    return (
      <div className="reader-overlay" role="dialog" aria-label="Story reader">
        <div className="reader-loading">
          <div className="loading-spinner" />
          <p>Opening your adventure…</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error || (!isLoading && !selectedStorybook)) {
    return (
      <div className="reader-overlay" role="dialog" aria-label="Story reader">
        <div className="reader-loading">
          <p>Oops, we couldn't find that story!</p>
          <button className="reader-end__btn" onClick={onClose}>
            Back to Gallery
          </button>
        </div>
      </div>
    );
  }

  // "The End" card on last beat after viewing
  const showEndCard = isLastBeat && !transitionClass;

  return (
    <div
      className="reader-overlay"
      role="dialog"
      aria-label={`Reading: ${selectedStorybook.title}`}
      onTouchStart={handleTouchStart}
      onTouchEnd={handleTouchEnd}
    >
      {/* Header with page indicator and close */}
      <div className="reader-header">
        <span className="reader-page-indicator" aria-live="polite">
          {currentBeatIndex + 1} / {totalBeats}
        </span>
        <button
          className="reader-header__close"
          onClick={onClose}
          aria-label="Close reader"
        >
          ✕
        </button>
      </div>

      {/* Beat content */}
      {currentBeat && (
        <div
          className={`reader-beat ${transitionClass} ${direction === 'backward' ? 'reader-beat--reverse' : ''}`}
        >
          {/* Scene image */}
          <div className="reader-beat__scene">
            {currentBeat.scene_image_url ? (
              <>
                <img
                  src={
                    currentBeat.scene_image_url.startsWith('http')
                      ? currentBeat.scene_image_url
                      : `http://localhost:8000${currentBeat.scene_image_url}`
                  }
                  alt={`Scene ${currentBeatIndex + 1}`}
                  onError={handleImageError}
                />
                <span
                  className="reader-beat__scene-fallback"
                  style={{ display: 'none' }}
                  aria-hidden="true"
                >
                  📖
                </span>
              </>
            ) : (
              <span className="reader-beat__scene-fallback" aria-hidden="true">
                📖
              </span>
            )}
            <div className="reader-beat__scene-fade" />
          </div>

          {/* Narration — tappable to toggle perspectives */}
          <div
            className="reader-beat__narration"
            onClick={() => setShowPerspectives((p) => !p)}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                setShowPerspectives((p) => !p);
              }
            }}
          >
            <p className="reader-beat__narration-text">{currentBeat.narration}</p>
            <span className="reader-beat__tap-hint">
              {showPerspectives ? '▲ hide details' : '▼ tap for details'}
            </span>
          </div>

          {/* Expandable perspective cards */}
          {showPerspectives && (
            <div className="reader-perspectives">
              {currentBeat.child1_perspective && (
                <div className="reader-card reader-card--child1">
                  <span className="reader-card__emoji" aria-hidden="true">🌟</span>
                  <p className="reader-card__text">{currentBeat.child1_perspective}</p>
                </div>
              )}
              {currentBeat.child2_perspective && (
                <div className="reader-card reader-card--child2">
                  <span className="reader-card__emoji" aria-hidden="true">⭐</span>
                  <p className="reader-card__text">{currentBeat.child2_perspective}</p>
                </div>
              )}
            </div>
          )}

          {/* "You chose:" badge */}
          {currentBeat.choice_made && (
            <div className="reader-beat__choice">
              <span className="reader-beat__choice-label">You chose:</span>
              <span className="reader-beat__choice-text">{currentBeat.choice_made}</span>
            </div>
          )}
        </div>
      )}

      {/* "The End" card */}
      {showEndCard && (
        <div className="reader-end">
          <CelebrationOverlay type="sparkle" duration={3000} particleCount={30} />
          <h2 className="reader-end__title">The End ✨</h2>
          <p className="reader-end__subtitle">What a wonderful adventure!</p>
          <button className="reader-end__btn" onClick={onClose}>
            Back to Gallery
          </button>
        </div>
      )}

      {/* Navigation arrows */}
      <div className="reader-nav">
        <button
          className="reader-nav__btn"
          onClick={goBackward}
          disabled={currentBeatIndex === 0}
          aria-label="Previous page"
        >
          ◀
        </button>
        <button
          className="reader-nav__btn"
          onClick={goForward}
          disabled={isLastBeat}
          aria-label="Next page"
        >
          ▶
        </button>
      </div>
    </div>
  );
}
