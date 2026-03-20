import React, { useState, useEffect, useRef } from 'react';
import { audioFeedbackService } from '../../audio/services/audioFeedbackService';
import './ContinueScreen.css';

const spiritEmoji = {
  dragon: '🐉',
  unicorn: '🦄',
  owl: '🦉',
  dolphin: '🐬',
  phoenix: '🔥',
  tiger: '🐯',
  wolf: '🐺',
  bear: '🐻',
};

/**
 * @param {Object} props
 * @param {Object} props.snapshot - The availableSession from sessionPersistenceStore
 * @param {Function} props.onContinue - Called when "Continue Story" is tapped
 * @param {Function} props.onNewAdventure - Called when "New Adventure" is confirmed
 */
export default function ContinueScreen({ snapshot, onContinue, onNewAdventure }) {
  const [showConfirm, setShowConfirm] = useState(false);
  const greetingRef = useRef(null);

  useEffect(() => {
    if (greetingRef.current) {
      greetingRef.current.focus();
    }
  }, []);

  const profiles = snapshot.character_profiles;
  const lastScene =
    snapshot.story_history?.length > 0
      ? snapshot.story_history[snapshot.story_history.length - 1]
      : null;
  const lastImage = lastScene?.scene_image_url;

  const c1Spirit = spiritEmoji[profiles.c1_spirit?.toLowerCase()] || '✨';
  const c2Spirit = spiritEmoji[profiles.c2_spirit?.toLowerCase()] || '✨';

  useEffect(() => {
    audioFeedbackService.playSequence([
      { frequency: 523, duration: 0.15 },
      { frequency: 659, duration: 0.15, delay: 100 },
      { frequency: 784, duration: 0.25, delay: 100 },
    ]);
  }, []);

  const handleNewAdventure = () => {
    if (showConfirm) {
      onNewAdventure();
    } else {
      setShowConfirm(true);
    }
  };

  return (
    <div className="continue-screen">
      {lastImage && (
        <div
          className="continue-screen__bg-image"
          style={{ backgroundImage: `url(${lastImage})` }}
          aria-hidden="true"
        />
      )}

      <div className="continue-screen__overlay">
        <h2
          className="continue-screen__greeting"
          data-testid="greeting"
          ref={greetingRef}
          tabIndex={-1}
        >
          Welcome back, {profiles.c1_name} &amp; {profiles.c2_name}!
        </h2>

        <div className="continue-screen__spirits">
          <span className="continue-screen__spirit-badge" data-testid="spirit-c1">
            <span className="continue-screen__spirit-emoji" aria-hidden="true">{c1Spirit}</span>
            <span className="continue-screen__spirit-name">{profiles.c1_name}</span>
          </span>
          <span className="continue-screen__spirit-badge" data-testid="spirit-c2">
            <span className="continue-screen__spirit-emoji" aria-hidden="true">{c2Spirit}</span>
            <span className="continue-screen__spirit-name">{profiles.c2_name}</span>
          </span>
        </div>

        <div className="continue-screen__actions">
          <button
            className="continue-screen__card continue-screen__card--continue"
            onClick={onContinue}
            data-testid="continue-button"
            aria-label="Continue Story"
          >
            <span className="continue-screen__card-icon" aria-hidden="true">✨</span>
            <span className="continue-screen__card-label">Continue Story</span>
          </button>

          {!showConfirm && (
            <button
              className="continue-screen__card continue-screen__card--new"
              onClick={() => setShowConfirm(true)}
              data-testid="new-adventure-button"
              aria-label="Start New Adventure"
            >
              <span className="continue-screen__card-icon" aria-hidden="true">🌟</span>
              <span className="continue-screen__card-label">New Adventure</span>
            </button>
          )}
        </div>

        {showConfirm && (
          <div className="continue-screen__confirm" data-testid="confirm-dialog">
            <p className="continue-screen__confirm-text">
              Start fresh? Your saved story will be gone.
            </p>
            <div className="continue-screen__confirm-buttons">
              <button
                className="continue-screen__confirm-yes"
                onClick={handleNewAdventure}
                data-testid="confirm-yes"
              >
                Yes, new adventure!
              </button>
              <button
                className="continue-screen__confirm-no"
                onClick={() => setShowConfirm(false)}
                data-testid="confirm-no"
              >
                Keep my story
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
