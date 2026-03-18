import React, { useState, useEffect } from 'react';
import { X, Plus, Trash2, Camera } from 'lucide-react';
import { useParentControlsStore, AVAILABLE_THEMES } from '../stores/parentControlsStore';
import { usePhotoStore } from '../stores/photoStore';
import './ParentControls.css';

const TIME_OPTIONS = [15, 30, 45, 60];
const COMPLEXITY_OPTIONS = ['simple', 'moderate', 'advanced'];

export default function ParentControls({ onClose, onReviewPhotos }) {
  const store = useParentControlsStore();
  const photos = usePhotoStore((s) => s.photos);
  const pendingCount = photos.filter((p) => p.status === 'review').length;
  const [newWord, setNewWord] = useState('');

  // Close on Escape key
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        e.stopPropagation();
        onClose();
      }
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  const handleAddWord = () => {
    if (newWord.trim()) {
      store.addBlockedWord(newWord);
      setNewWord('');
    }
  };

  return (
    <div className="parent-controls-overlay" onClick={onClose}>
      <div className="parent-controls" onClick={(e) => e.stopPropagation()}>
        <div className="pc-header">
          <h2 className="pc-title">Parent Controls</h2>
          <button className="pc-close" onClick={onClose} aria-label="Close">
            <X size={20} />
          </button>
        </div>

        {/* Theme toggles */}
        <section className="pc-section">
          <h3 className="pc-label">Allowed Themes</h3>
          <div className="pc-themes">
            {AVAILABLE_THEMES.map((theme) => (
              <button
                key={theme}
                className={`pc-theme-chip ${store.allowedThemes.includes(theme) ? 'pc-theme-chip--on' : ''}`}
                onClick={() => store.toggleTheme(theme)}
              >
                {theme}
              </button>
            ))}
          </div>
        </section>

        {/* Complexity */}
        <section className="pc-section">
          <h3 className="pc-label">Story Complexity</h3>
          <div className="pc-complexity">
            {COMPLEXITY_OPTIONS.map((level) => (
              <button
                key={level}
                className={`pc-complexity-btn ${store.complexityLevel === level ? 'pc-complexity-btn--active' : ''}`}
                onClick={() => store.setComplexityLevel(level)}
              >
                {level}
              </button>
            ))}
          </div>
        </section>

        {/* Custom blocked words */}
        <section className="pc-section">
          <h3 className="pc-label">Custom Blocked Words</h3>
          <div className="pc-word-input">
            <input
              type="text"
              value={newWord}
              onChange={(e) => setNewWord(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleAddWord()}
              placeholder="Add a word…"
              className="pc-input"
            />
            <button className="pc-add-btn" onClick={handleAddWord} aria-label="Add word">
              <Plus size={18} />
            </button>
          </div>
          <div className="pc-word-list">
            {store.customBlockedWords.map((word) => (
              <span key={word} className="pc-word-tag">
                {word}
                <button onClick={() => store.removeBlockedWord(word)} aria-label={`Remove ${word}`}>
                  <Trash2 size={12} />
                </button>
              </span>
            ))}
          </div>
        </section>

        {/* Session time limit */}
        <section className="pc-section">
          <h3 className="pc-label">Session Time Limit</h3>
          <div className="pc-time-options">
            {TIME_OPTIONS.map((min) => (
              <button
                key={min}
                className={`pc-time-btn ${store.sessionTimeLimitMinutes === min ? 'pc-time-btn--active' : ''}`}
                onClick={() => store.setSessionTimeLimit(min)}
              >
                {min} min
              </button>
            ))}
          </div>
        </section>

        {/* Review Photos */}
        <section className="pc-section">
          <h3 className="pc-label">Photo Review</h3>
          <button
            className="pc-review-btn"
            onClick={onReviewPhotos}
            aria-label={pendingCount > 0
              ? `Review ${pendingCount} pending photo${pendingCount > 1 ? 's' : ''}`
              : 'No photos to review'}
          >
            <Camera size={18} />
            <span>Review Photos</span>
            {pendingCount > 0
              ? <span className="pc-review-badge">{pendingCount}</span>
              : <span className="pc-review-secondary">No photos to review</span>}
          </button>
        </section>
      </div>
    </div>
  );
}
