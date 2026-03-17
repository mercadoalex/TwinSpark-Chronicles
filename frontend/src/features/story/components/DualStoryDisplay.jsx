import React from 'react';
import './DualStoryDisplay.css';

function DualStoryDisplay({ storyBeat, t, profiles, onChoice }) {
  if (!storyBeat) {
    return (
      <div className="story-empty">
        <div className="story-empty__sparkle">✨</div>
        <p className="story-empty__text">Preparing your magical adventure…</p>
      </div>
    );
  }

  return (
    <div className="story-stage-main">
      {/* ── Cinematic scene image ──────────────────── */}
      {storyBeat?.scene_image_url && (
        <div className="story-scene">
          <img
            className="story-scene__img"
            src={storyBeat.scene_image_url.startsWith('http')
              ? storyBeat.scene_image_url
              : `http://localhost:8000${storyBeat.scene_image_url}`}
            alt="Story scene"
            onLoad={() => console.log('✅ Image loaded')}
            onError={(e) => console.error('❌ Image failed:', e.target.src)}
          />
          <div className="story-scene__fade" />
        </div>
      )}

      {/* ── Narration ──────────────────────────────── */}
      {storyBeat?.narration && (
        <div className="story-narration">
          <p className="story-narration__text">{storyBeat.narration}</p>
        </div>
      )}

      {/* ── Dual perspectives ──────────────────────── */}
      <div className="story-perspectives">
        {/* Child 1 */}
        <div className="story-card story-card--child1">
          <div className="story-card__header">
            <span className="story-card__avatar">🌟</span>
            <h3 className="story-card__name story-card__name--child1">
              {profiles?.c1_name || 'Child 1'}
            </h3>
          </div>
          <p className="story-card__text">
            {storyBeat?.child1_perspective || `${profiles?.c1_name} is ready for adventure!`}
          </p>
        </div>

        {/* Child 2 */}
        <div className="story-card story-card--child2">
          <div className="story-card__header">
            <span className="story-card__avatar">⭐</span>
            <h3 className="story-card__name story-card__name--child2">
              {profiles?.c2_name || 'Child 2'}
            </h3>
          </div>
          <p className="story-card__text">
            {storyBeat?.child2_perspective || `${profiles?.c2_name} feels the magic!`}
          </p>
        </div>
      </div>

      {/* ── Choices — "The Crossroads" ─────────────── */}
      {storyBeat?.choices && storyBeat.choices.length > 0 && (
        <div className="story-crossroads">
          <h3 className="story-crossroads__title">What happens next?</h3>
          <div className="story-crossroads__options">
            {storyBeat.choices.map((choice, idx) => (
              <button
                key={idx}
                className="story-crossroads__choice"
                onClick={() => onChoice(choice)}
              >
                <span className="story-crossroads__choice-icon">
                  {idx === 0 ? '🌙' : idx === 1 ? '⚡' : '🌿'}
                </span>
                <span className="story-crossroads__choice-text">{choice}</span>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default DualStoryDisplay;
