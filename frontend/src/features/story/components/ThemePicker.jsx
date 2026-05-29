import React, { useState, useCallback, useRef, useEffect } from 'react';
import CelebrationOverlay from '../../../shared/components/CelebrationOverlay';
import { ttsService } from '../../audio/services/ttsService';
import './ThemePicker.css';

/**
 * ThemePicker — Adventure theme selection for new stories.
 *
 * Presents 2-3 large illustrated theme cards (forest, space, ocean) that
 * children can tap to start a new adventure. No reading required — TTS
 * speaks the theme name when a card is tapped/focused, and big emoji
 * illustrations communicate the theme visually.
 *
 * On tap: brief celebration animation (sparkles), then calls onSelect
 * with the selected theme ID.
 *
 * Requirements: 7.3, 7.4, 7.5
 *
 * @param {Object} props
 * @param {(themeId: string) => void} props.onSelect - Callback with selected theme ID
 */

const THEMES = [
  {
    id: 'enchanted-forest',
    name: 'Enchanted Forest',
    emoji: '🌲',
    color: '#2d8a4e',
    bgGradient: 'linear-gradient(145deg, #1a5c32, #3da864)',
  },
  {
    id: 'outer-space',
    name: 'Outer Space',
    emoji: '🚀',
    color: '#4a3d99',
    bgGradient: 'linear-gradient(145deg, #1e1b4b, #5b4fc7)',
  },
  {
    id: 'ocean-kingdom',
    name: 'Ocean Kingdom',
    emoji: '🌊',
    color: '#1a6b8a',
    bgGradient: 'linear-gradient(145deg, #0c4a6e, #38bdf8)',
  },
];

function ThemePicker({ onSelect }) {
  const [selectedTheme, setSelectedTheme] = useState(null);
  const [showCelebration, setShowCelebration] = useState(false);
  const celebrationTimerRef = useRef(null);

  // Cleanup timers on unmount
  useEffect(() => {
    return () => {
      if (celebrationTimerRef.current) {
        clearTimeout(celebrationTimerRef.current);
      }
    };
  }, []);

  /**
   * Speak theme name via TTS when card is focused/tapped (Req 7.4, 12.1).
   */
  const speakThemeName = useCallback((themeName) => {
    ttsService.speak(themeName, 'en', { rate: 0.9, pitch: 1.1 });
  }, []);

  /**
   * Handle card tap — speak name, show celebration, then call onSelect (Req 7.5).
   */
  const handleCardTap = useCallback((theme) => {
    if (selectedTheme) return; // Prevent double-tap

    setSelectedTheme(theme.id);
    speakThemeName(theme.name);
    setShowCelebration(true);

    // After celebration animation, call onSelect
    celebrationTimerRef.current = setTimeout(() => {
      setShowCelebration(false);
      if (onSelect) {
        onSelect(theme.id);
      }
    }, 1500);
  }, [selectedTheme, speakThemeName, onSelect]);

  /**
   * Handle focus — TTS reads theme name (Req 7.4).
   */
  const handleCardFocus = useCallback((theme) => {
    if (!selectedTheme) {
      speakThemeName(theme.name);
    }
  }, [selectedTheme, speakThemeName]);

  return (
    <div className="theme-picker" role="group" aria-label="Choose your adventure">
      {/* Title — visual only, TTS handles communication */}
      <div className="theme-picker__header" aria-hidden="true">
        <span className="theme-picker__title-icon">✨</span>
        <span className="theme-picker__title-text">Choose Your Adventure</span>
        <span className="theme-picker__title-icon">✨</span>
      </div>

      {/* Theme cards (Req 7.3) */}
      <div className="theme-picker__cards">
        {THEMES.map((theme) => (
          <button
            key={theme.id}
            className={`theme-picker__card ${
              selectedTheme === theme.id ? 'theme-picker__card--selected' : ''
            } ${selectedTheme && selectedTheme !== theme.id ? 'theme-picker__card--dimmed' : ''}`}
            style={{
              '--theme-color': theme.color,
              '--theme-bg': theme.bgGradient,
            }}
            onClick={() => handleCardTap(theme)}
            onFocus={() => handleCardFocus(theme)}
            disabled={!!selectedTheme}
            aria-label={theme.name}
          >
            {/* Big emoji illustration — primary visual (Req 12.1) */}
            <span className="theme-picker__emoji" aria-hidden="true">
              {theme.emoji}
            </span>

            {/* Theme name — secondary text */}
            <span className="theme-picker__name">
              {theme.name}
            </span>
          </button>
        ))}
      </div>

      {/* Launch celebration animation (Req 7.5) */}
      {showCelebration && (
        <CelebrationOverlay
          type="star-shower"
          duration={1500}
          particleCount={35}
        />
      )}
    </div>
  );
}

export default ThemePicker;
