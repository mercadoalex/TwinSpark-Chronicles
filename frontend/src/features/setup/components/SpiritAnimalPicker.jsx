import React, { useState, useEffect, useRef, useCallback } from 'react';
import CelebrationOverlay from '../../../shared/components/CelebrationOverlay';
import './SpiritAnimalPicker.css';

/**
 * Spirit animals available for selection.
 * Each has an id, emoji illustration, display name, accent color, and a fun sound word.
 */
const SPIRIT_ANIMALS = [
  { id: 'dragon', emoji: '🐉', name: 'Dragon', color: '#ef4444', sound: 'Roar!' },
  { id: 'unicorn', emoji: '🦄', name: 'Unicorn', color: '#d946ef', sound: 'Sparkle!' },
  { id: 'owl', emoji: '🦉', name: 'Owl', color: '#a78bfa', sound: 'Hoo hoo!' },
  { id: 'dolphin', emoji: '🐬', name: 'Dolphin', color: '#38bdf8', sound: 'Click click!' },
  { id: 'phoenix', emoji: '🔥', name: 'Phoenix', color: '#f59e0b', sound: 'Whoosh!' },
  { id: 'tiger', emoji: '🐯', name: 'Tiger', color: '#fb923c', sound: 'Grrr!' },
  { id: 'wolf', emoji: '🐺', name: 'Wolf', color: '#6366f1', sound: 'Awoo!' },
  { id: 'butterfly', emoji: '🦋', name: 'Butterfly', color: '#ec4899', sound: 'Flutter!' },
];

/** TTS rate for child comprehension */
const TTS_RATE = 0.9;

/**
 * Speak a text string using the Web Speech API.
 * @param {string} text - Text to speak
 */
function speakText(text) {
  if (!window.speechSynthesis) return;
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.rate = TTS_RATE;
  utterance.pitch = 1.2;
  utterance.volume = 0.9;
  window.speechSynthesis.speak(utterance);
}

/**
 * SpiritAnimalPicker — Horizontally swipeable gallery of spirit animal cards.
 *
 * No reading required: TTS speaks the animal name when a card scrolls into focus.
 * Tap to confirm selection → celebration animation + animal sound via TTS.
 * Minimum 6 spirit animal options. No virtual keyboard shown.
 *
 * Requirements: 6.3, 6.4, 6.5, 6.6, 6.7
 *
 * @param {Object} props
 * @param {string} props.childName - The child's name, displayed in the prompt
 * @param {(animalId: string) => void} props.onSelect - Callback when an animal is confirmed
 */
function SpiritAnimalPicker({ childName, onSelect }) {
  const [focusedIndex, setFocusedIndex] = useState(0);
  const [confirmed, setConfirmed] = useState(false);
  const [showCelebration, setShowCelebration] = useState(false);
  const galleryRef = useRef(null);
  const observerRef = useRef(null);
  const cardRefs = useRef([]);
  const lastSpokenRef = useRef(-1);

  // Speak the animal name when a new card comes into focus
  useEffect(() => {
    if (confirmed) return;
    if (focusedIndex !== lastSpokenRef.current) {
      lastSpokenRef.current = focusedIndex;
      const animal = SPIRIT_ANIMALS[focusedIndex];
      if (animal) {
        speakText(animal.name);
      }
    }
  }, [focusedIndex, confirmed]);

  // Set up IntersectionObserver to detect which card is centered
  useEffect(() => {
    const gallery = galleryRef.current;
    if (!gallery) return;

    observerRef.current = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting && entry.intersectionRatio >= 0.6) {
            const index = Number(entry.target.dataset.index);
            if (!isNaN(index)) {
              setFocusedIndex(index);
            }
          }
        });
      },
      {
        root: gallery,
        threshold: 0.6,
      }
    );

    cardRefs.current.forEach((card) => {
      if (card) observerRef.current.observe(card);
    });

    return () => {
      if (observerRef.current) {
        observerRef.current.disconnect();
      }
    };
  }, []);

  // Handle card tap — confirm selection with celebration
  const handleCardTap = useCallback(
    (index) => {
      if (confirmed) return;

      const animal = SPIRIT_ANIMALS[index];
      if (!animal) return;

      setConfirmed(true);
      setShowCelebration(true);

      // Speak the animal sound as celebration feedback
      speakText(`${animal.name}! ${animal.sound}`);

      // Dismiss celebration and notify parent after animation
      setTimeout(() => {
        setShowCelebration(false);
        if (onSelect) {
          onSelect(animal.id);
        }
      }, 2000);
    },
    [confirmed, onSelect]
  );

  return (
    <div className="spirit-animal-picker" aria-label="Pick your spirit animal">
      {/* Title — spoken by TTS automatically */}
      <h2 className="spirit-animal-picker__title">
        <span className="spirit-animal-picker__title-emoji" aria-hidden="true">✨</span>
        Pick your spirit animal, {childName}!
        <span className="spirit-animal-picker__title-emoji" aria-hidden="true">✨</span>
      </h2>

      <p className="spirit-animal-picker__hint" aria-hidden="true">
        ← Swipe to explore →
      </p>

      {/* Horizontally scrollable gallery with CSS scroll-snap */}
      <div
        className="spirit-animal-picker__gallery"
        ref={galleryRef}
        role="listbox"
        aria-label="Spirit animals"
      >
        {SPIRIT_ANIMALS.map((animal, index) => (
          <button
            key={animal.id}
            ref={(el) => { cardRefs.current[index] = el; }}
            data-index={index}
            className={`spirit-animal-picker__card ${
              focusedIndex === index ? 'spirit-animal-picker__card--focused' : ''
            } ${confirmed && focusedIndex === index ? 'spirit-animal-picker__card--confirmed' : ''}`}
            style={{ '--card-color': animal.color }}
            onClick={() => handleCardTap(index)}
            role="option"
            aria-selected={focusedIndex === index}
            aria-label={animal.name}
            disabled={confirmed}
          >
            <span className="spirit-animal-picker__card-emoji" aria-hidden="true">
              {animal.emoji}
            </span>
            <span className="spirit-animal-picker__card-name">
              {animal.name}
            </span>
            {focusedIndex === index && !confirmed && (
              <span className="spirit-animal-picker__card-tap-hint" aria-hidden="true">
                Tap me!
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Dot indicators */}
      <div className="spirit-animal-picker__dots" aria-hidden="true">
        {SPIRIT_ANIMALS.map((animal, index) => (
          <span
            key={animal.id}
            className={`spirit-animal-picker__dot ${
              focusedIndex === index ? 'spirit-animal-picker__dot--active' : ''
            }`}
            style={{ '--dot-color': animal.color }}
          />
        ))}
      </div>

      {/* Celebration overlay on selection */}
      {showCelebration && (
        <CelebrationOverlay
          type="star-shower"
          duration={2000}
          particleCount={50}
        />
      )}
    </div>
  );
}

export default SpiritAnimalPicker;
