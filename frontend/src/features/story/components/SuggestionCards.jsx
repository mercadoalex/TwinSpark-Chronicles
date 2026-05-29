import React, { useRef, useCallback } from 'react';
import './SuggestionCards.css';

/**
 * SuggestionCards — Displays 2-3 illustrated "Spark" cards as optional inspiration.
 *
 * Cards appear in a horizontal row below the mic button. Each card has an
 * illustration and a short label (max 4 words). Tapping submits the card's
 * storyDirection as input (identical flow to voice). Long-pressing (500ms)
 * triggers TTS to read the card label aloud.
 *
 * Cards are optional — never required for progression. They serve as gentle
 * inspiration for shy moments or when the mic isn't available.
 *
 * Only tappable during `awaiting_input` phase (controlled by `isActive` prop).
 *
 * Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 8.1, 12.3
 *
 * @param {Object} props
 * @param {Array<{id: string, label: string, illustrationUrl: string|null, storyDirection: string}>} props.cards
 * @param {boolean} props.isActive - Only tappable during awaiting_input phase
 * @param {(cardId: string) => void} props.onCardTap - Callback when card is tapped
 * @param {(cardId: string) => void} props.onCardLongPress - Callback when card is long-pressed (triggers TTS)
 */
function SuggestionCards({ cards, isActive, onCardTap, onCardLongPress }) {
  // Track long-press timers per card
  const longPressTimers = useRef({});
  const isLongPress = useRef({});

  /**
   * Handle press start (touchstart / mousedown).
   * Starts a 500ms timer for long-press detection.
   */
  const handlePressStart = useCallback((cardId) => {
    if (!isActive) return;

    isLongPress.current[cardId] = false;

    longPressTimers.current[cardId] = setTimeout(() => {
      isLongPress.current[cardId] = true;
      if (onCardLongPress) {
        onCardLongPress(cardId);
      }
    }, 500);
  }, [isActive, onCardLongPress]);

  /**
   * Handle press end (touchend / mouseup).
   * If the timer hasn't fired (< 500ms), treat as a tap.
   */
  const handlePressEnd = useCallback((cardId) => {
    if (!isActive) return;

    // Clear the long-press timer
    if (longPressTimers.current[cardId]) {
      clearTimeout(longPressTimers.current[cardId]);
      longPressTimers.current[cardId] = null;
    }

    // If it wasn't a long press, treat as tap
    if (!isLongPress.current[cardId]) {
      if (onCardTap) {
        onCardTap(cardId);
      }
    }

    isLongPress.current[cardId] = false;
  }, [isActive, onCardTap]);

  /**
   * Handle press cancel (touchcancel / mouseleave).
   * Clears the long-press timer without triggering anything.
   */
  const handlePressCancel = useCallback((cardId) => {
    if (longPressTimers.current[cardId]) {
      clearTimeout(longPressTimers.current[cardId]);
      longPressTimers.current[cardId] = null;
    }
    isLongPress.current[cardId] = false;
  }, []);

  // Don't render if no cards provided
  if (!cards || cards.length === 0) return null;

  return (
    <div
      className={`suggestion-cards ${isActive ? 'suggestion-cards--active' : 'suggestion-cards--disabled'}`}
      role="group"
      aria-label="Story sparks — tap one for inspiration"
    >
      {cards.map((card) => (
        <button
          key={card.id}
          className="suggestion-cards__card"
          disabled={!isActive}
          aria-label={card.label}
          onTouchStart={() => handlePressStart(card.id)}
          onTouchEnd={() => handlePressEnd(card.id)}
          onTouchCancel={() => handlePressCancel(card.id)}
          onMouseDown={() => handlePressStart(card.id)}
          onMouseUp={() => handlePressEnd(card.id)}
          onMouseLeave={() => handlePressCancel(card.id)}
          onContextMenu={(e) => e.preventDefault()}
        >
          {/* Illustration — primary visual (Req 12.3) */}
          <div className="suggestion-cards__illustration" aria-hidden="true">
            {card.illustrationUrl ? (
              <img
                src={card.illustrationUrl}
                alt=""
                className="suggestion-cards__image"
                draggable={false}
              />
            ) : (
              <span className="suggestion-cards__placeholder-icon">✨</span>
            )}
          </div>

          {/* Label — secondary reinforcement, max 4 words (Req 3.2, 12.3) */}
          <span className="suggestion-cards__label">
            {card.label}
          </span>
        </button>
      ))}
    </div>
  );
}

export default SuggestionCards;
