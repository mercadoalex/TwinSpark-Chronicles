import React, { useState, useEffect, useRef } from 'react';
import { audioFeedbackService } from '../../audio/services/audioFeedbackService';

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

const GLOW_KEYFRAMES = `
@keyframes sparkleGlow {
  0% { box-shadow: 0 0 10px rgba(255, 215, 0, 0.4), 0 0 20px rgba(168, 85, 247, 0.3); }
  50% { box-shadow: 0 0 25px rgba(255, 215, 0, 0.8), 0 0 50px rgba(168, 85, 247, 0.6); }
  100% { box-shadow: 0 0 10px rgba(255, 215, 0, 0.4), 0 0 20px rgba(168, 85, 247, 0.3); }
}
@keyframes gentleBounce {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.04); }
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}
`;

/**
 * @param {Object} props
 * @param {Object} props.snapshot - The availableSession from sessionPersistenceStore
 * @param {Function} props.onContinue - Called when "Continue Story" is tapped
 * @param {Function} props.onNewAdventure - Called when "New Adventure" is confirmed
 */
export default function ContinueScreen({ snapshot, onContinue, onNewAdventure }) {
  const [showConfirm, setShowConfirm] = useState(false);
  const greetingRef = useRef(null);
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false);

  useEffect(() => {
    const mql = window.matchMedia('(prefers-reduced-motion: reduce)');
    setPrefersReducedMotion(mql.matches);
    const handler = (e) => setPrefersReducedMotion(e.matches);
    mql.addEventListener('change', handler);
    return () => mql.removeEventListener('change', handler);
  }, []);

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
    <div style={containerStyle}>
      <style>{GLOW_KEYFRAMES}</style>

      {lastImage && <div style={bgImageStyle(lastImage)} aria-hidden="true" />}

      <div style={overlayStyle}>
        <h2 style={greetingStyle} data-testid="greeting" ref={greetingRef} tabIndex={-1}>
          Welcome back, {profiles.c1_name} &amp; {profiles.c2_name}!
        </h2>

        <div style={spiritsRowStyle}>
          <span style={spiritBadgeStyle} data-testid="spirit-c1">
            <span style={spiritEmojiStyle}>{c1Spirit}</span>
            <span style={spiritNameStyle}>{profiles.c1_name}</span>
          </span>
          <span style={spiritBadgeStyle} data-testid="spirit-c2">
            <span style={spiritEmojiStyle}>{c2Spirit}</span>
            <span style={spiritNameStyle}>{profiles.c2_name}</span>
          </span>
        </div>

        <button
          onClick={onContinue}
          style={prefersReducedMotion ? continueButtonReducedStyle : continueButtonStyle}
          data-testid="continue-button"
          aria-label="Continue Story"
        >
          ✨ Continue Story ✨
        </button>

        {!showConfirm ? (
          <button
            onClick={() => setShowConfirm(true)}
            style={newAdventureButtonStyle}
            data-testid="new-adventure-button"
            aria-label="Start New Adventure"
          >
            🌟 New Adventure
          </button>
        ) : (
          <div style={confirmContainerStyle} data-testid="confirm-dialog">
            <p style={confirmTextStyle}>Start fresh? Your saved story will be gone.</p>
            <div style={confirmButtonsStyle}>
              <button
                onClick={handleNewAdventure}
                style={confirmYesStyle}
                data-testid="confirm-yes"
              >
                Yes, new adventure!
              </button>
              <button
                onClick={() => setShowConfirm(false)}
                style={confirmNoStyle}
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

/* ── Styles ─────────────────────────────────────────── */

const containerStyle = {
  position: 'relative',
  width: '100%',
  minHeight: '100vh',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  overflow: 'hidden',
  background: 'linear-gradient(135deg, #1a1040 0%, #2d1b69 50%, #1a1040 100%)',
};

const bgImageStyle = (url) => ({
  position: 'absolute',
  inset: 0,
  backgroundImage: `url(${url})`,
  backgroundSize: 'cover',
  backgroundPosition: 'center',
  filter: 'blur(8px) brightness(0.4)',
  zIndex: 0,
});

const overlayStyle = {
  position: 'relative',
  zIndex: 1,
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  gap: '24px',
  padding: '40px 24px',
  animation: 'fadeIn 0.6s ease-out',
};

const greetingStyle = {
  color: '#fff',
  fontSize: 'clamp(1.4rem, 4vw, 2rem)',
  fontWeight: 700,
  textAlign: 'center',
  textShadow: '0 2px 12px rgba(0,0,0,0.5)',
  margin: 0,
};

const spiritsRowStyle = {
  display: 'flex',
  gap: '32px',
  justifyContent: 'center',
  flexWrap: 'wrap',
};

const spiritBadgeStyle = {
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  gap: '4px',
};

const spiritEmojiStyle = {
  fontSize: '48px',
  lineHeight: 1,
};

const spiritNameStyle = {
  color: '#e0d4f7',
  fontSize: '1.1rem',
  fontWeight: 600,
};

const continueButtonStyle = {
  minHeight: '80px',
  padding: '0 48px',
  fontSize: 'clamp(1.2rem, 3vw, 1.6rem)',
  fontWeight: 700,
  color: '#1a1040',
  background: 'linear-gradient(135deg, #ffd700, #ffaa00)',
  border: 'none',
  borderRadius: '40px',
  cursor: 'pointer',
  animation: 'sparkleGlow 2s ease-in-out infinite, gentleBounce 3s ease-in-out infinite',
  letterSpacing: '0.5px',
};

const continueButtonReducedStyle = {
  minHeight: '80px',
  padding: '0 48px',
  fontSize: 'clamp(1.2rem, 3vw, 1.6rem)',
  fontWeight: 700,
  color: '#1a1040',
  background: 'linear-gradient(135deg, #ffd700, #ffaa00)',
  border: 'none',
  borderRadius: '40px',
  cursor: 'pointer',
  animation: 'none',
  letterSpacing: '0.5px',
};

const newAdventureButtonStyle = {
  minHeight: '48px',
  padding: '0 28px',
  fontSize: '1rem',
  fontWeight: 600,
  color: '#e0d4f7',
  background: 'rgba(255,255,255,0.1)',
  border: '2px solid rgba(255,255,255,0.25)',
  borderRadius: '24px',
  cursor: 'pointer',
  backdropFilter: 'blur(4px)',
};

const confirmContainerStyle = {
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  gap: '12px',
  padding: '16px 24px',
  background: 'rgba(0,0,0,0.5)',
  borderRadius: '16px',
  backdropFilter: 'blur(8px)',
};

const confirmTextStyle = {
  color: '#ffd700',
  fontSize: '1rem',
  margin: 0,
  textAlign: 'center',
};

const confirmButtonsStyle = {
  display: 'flex',
  gap: '12px',
  flexWrap: 'wrap',
  justifyContent: 'center',
};

const confirmYesStyle = {
  padding: '10px 24px',
  fontSize: '1rem',
  fontWeight: 600,
  color: '#fff',
  background: '#e74c3c',
  border: 'none',
  borderRadius: '20px',
  cursor: 'pointer',
  minHeight: '44px',
};

const confirmNoStyle = {
  padding: '10px 24px',
  fontSize: '1rem',
  fontWeight: 600,
  color: '#e0d4f7',
  background: 'rgba(255,255,255,0.15)',
  border: '2px solid rgba(255,255,255,0.3)',
  borderRadius: '20px',
  cursor: 'pointer',
  minHeight: '44px',
};
