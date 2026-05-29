import React from 'react';
import './TurnIndicator.css';

/**
 * TurnIndicator — Shows whose turn it is with avatar, name, and pulsing glow.
 *
 * Communicates turn status through visual cues (avatar, color, animation)
 * without relying on text comprehension. The name is displayed as secondary
 * reinforcement but the component works entirely through visual cues for
 * non-readers.
 *
 * Positioned at top of screen, visible to both children simultaneously.
 * Shown only during `awaiting_input` and `recording` phases.
 * Minimum 72px height for the indicator area.
 *
 * Requirements: 1.4, 8.1, 8.3, 11.5, 12.4
 *
 * @param {Object} props
 * @param {Object} props.activeTwin - The active twin config { name, avatar, color }
 * @param {string} props.activeTwin.name - Twin's display name
 * @param {string} props.activeTwin.avatar - Emoji (e.g. "🌟") or image URL
 * @param {string} props.activeTwin.color - Twin's assigned color (e.g. "#FF6B6B")
 * @param {boolean} props.isVisible - Whether the indicator is shown (awaiting_input or recording)
 */
function TurnIndicator({ activeTwin, isVisible }) {
  if (!activeTwin) return null;

  const { name, avatar, color } = activeTwin;
  const isImageUrl = avatar && (avatar.startsWith('http') || avatar.startsWith('/'));

  return (
    <div
      className={`turn-indicator ${isVisible ? 'turn-indicator--visible' : ''}`}
      style={{ '--twin-color': color || '#fff' }}
      role="status"
      aria-live="polite"
      aria-label={isVisible ? `${name}'s turn` : ''}
    >
      {/* Avatar with pulsing glow in twin's color (Req 1.4, 8.3) */}
      <div className="turn-indicator__avatar" aria-hidden="true">
        {isImageUrl ? (
          <img src={avatar} alt="" />
        ) : (
          <span>{avatar || '⭐'}</span>
        )}
      </div>

      {/* Name — secondary reinforcement for non-readers (Req 12.4) */}
      <span className="turn-indicator__name" aria-hidden="true">
        {name}
      </span>

      {/* Pulsing dot — extra visual cue that it's their turn */}
      <span className="turn-indicator__pulse-dot" aria-hidden="true" />
    </div>
  );
}

export default TurnIndicator;
