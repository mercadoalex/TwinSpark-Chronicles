import React, { useState, useEffect, useRef } from 'react';
import './DualStoryDisplay.css';

const choiceIcons = ['🌙', '⚡', '🌿', '🔮', '🌊', '🦋'];

function DualStoryDisplay({ storyBeat, t, profiles, onChoice }) {
  const [selectedIdx, setSelectedIdx] = useState(null);
  const [showPerspectives, setShowPerspectives] = useState(false);
  const narrationRef = useRef(null);
  const prevBeatRef = useRef(null);

  // Move focus to narration text when a new story beat loads (Req 9.3)
  useEffect(() => {
    if (storyBeat?.narration && storyBeat !== prevBeatRef.current) {
      prevBeatRef.current = storyBeat;
      // Delay to ensure DOM has rendered after loading animation is replaced
      requestAnimationFrame(() => {
        narrationRef.current?.focus();
      });
    }
  }, [storyBeat]);

  if (!storyBeat) {
    return (
      <div className="story-empty">
        <div className="story-empty__sparkle" aria-hidden="true">✨</div>
        <p className="story-empty__text">Preparing your magical adventure…</p>
      </div>
    );
  }

  const handleChoiceTap = (choice, idx) => {
    setSelectedIdx(idx);
    // Satisfying bounce then send
    setTimeout(() => {
      onChoice(choice);
      setSelectedIdx(null);
      setShowPerspectives(false);
    }, 400);
  };

  const togglePerspectives = () => setShowPerspectives(p => !p);

  // Descriptive alt text from scene_description or fallback (Req 5.1)
  const sceneAlt = storyBeat?.scene_description || 'Illustration for the current story scene';

  return (
    <section className="story-stage-main" aria-label="Story content">
      {/* ── Cinematic scene image ──────────────────── */}
      {storyBeat?.scene_image_url && (
        <div className="story-scene">
          <img
            className="story-scene__img"
            src={storyBeat.scene_image_url.startsWith('http')
              ? storyBeat.scene_image_url
              : `http://localhost:8000${storyBeat.scene_image_url}`}
            alt={sceneAlt}
          />
          <div className="story-scene__fade" />

          {/* Floating child avatars on the scene */}
          <div className="story-scene__avatars">
            <div className="story-scene__avatar story-scene__avatar--c1">
              <span aria-hidden="true">🌟</span>
              <span className="story-scene__avatar-name">{profiles?.c1_name}</span>
            </div>
            <div className="story-scene__avatar story-scene__avatar--c2">
              <span aria-hidden="true">⭐</span>
              <span className="story-scene__avatar-name">{profiles?.c2_name}</span>
            </div>
          </div>
        </div>
      )}

      {/* ── Narration — short, voice-first (Req 4.1) ── */}
      {storyBeat?.narration && (
        <div
          className="story-narration"
          onClick={togglePerspectives}
          ref={narrationRef}
          tabIndex={-1}
          aria-live="polite"
        >
          <p className="story-narration__text">{storyBeat.narration}</p>
          <span className="story-narration__tap-hint">
            {showPerspectives ? '▲ hide details' : '▼ tap for details'}
          </span>
        </div>
      )}

      {/* ── Expandable perspectives ────────────────── */}
      {showPerspectives && (
        <div className="story-perspectives">
          <div className="story-card story-card--child1">
            <span className="story-card__emoji" aria-hidden="true">🌟</span>
            <span className="story-card__name story-card__name--child1">
              {profiles?.c1_name}
            </span>
            <p className="story-card__text">
              {storyBeat?.child1_perspective}
            </p>
          </div>
          <div className="story-card story-card--child2">
            <span className="story-card__emoji" aria-hidden="true">⭐</span>
            <span className="story-card__name story-card__name--child2">
              {profiles?.c2_name}
            </span>
            <p className="story-card__text">
              {storyBeat?.child2_perspective}
            </p>
          </div>
        </div>
      )}

      {/* ── Choice cards — BIG tappable ────────────── */}
      {storyBeat?.choices && storyBeat.choices.length > 0 && (
        <div className="story-choices">
          <h3 className="story-choices__title">What happens next?</h3>
          <div className="story-choices__grid">
            {storyBeat.choices.map((choice, idx) => (
              <button
                key={idx}
                className={`story-choice-card ${selectedIdx === idx ? 'story-choice-card--selected' : ''}`}
                onClick={() => handleChoiceTap(choice, idx)}
                disabled={selectedIdx !== null}
              >
                <span className="story-choice-card__icon" aria-hidden="true">
                  {choiceIcons[idx % choiceIcons.length]}
                </span>
                <span className="story-choice-card__text">{choice}</span>
                <div className="story-choice-card__glow" />
              </button>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}

export default DualStoryDisplay;
