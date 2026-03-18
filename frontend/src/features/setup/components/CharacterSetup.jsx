import React, { useState, useRef, useEffect } from 'react';
import PhotoUploader from './PhotoUploader';
import PhotoGallery from './PhotoGallery';
import CharacterMapping from './CharacterMapping';
import ParentApprovalScreen from './ParentApprovalScreen';
import { usePhotoStore } from '../../../stores/photoStore';
import './CharacterSetup.css';

const stepLabels = {
  name: 'Name',
  gender: 'Gender',
  spirit: 'Spirit Animal',
  photos: 'Family Photos',
};

const spirits = [
  { value: 'dragon', emoji: '🐉', label: 'Dragon', color: '#ef4444' },
  { value: 'unicorn', emoji: '🦄', label: 'Unicorn', color: '#d946ef' },
  { value: 'owl', emoji: '🦉', label: 'Owl', color: '#a78bfa' },
  { value: 'dolphin', emoji: '🐬', label: 'Dolphin', color: '#38bdf8' },
  { value: 'phoenix', emoji: '🔥', label: 'Phoenix', color: '#f59e0b' },
  { value: 'tiger', emoji: '🐯', label: 'Tiger', color: '#fb923c' },
];

const genders = [
  { value: 'girl', emoji: '👧', label: 'Girl' },
  { value: 'boy', emoji: '👦', label: 'Boy' },
  { value: 'other', emoji: '🌈', label: 'Other' },
];

export default function CharacterSetup({ t, onComplete }) {
  const [childNum, setChildNum] = useState(1);
  const [wizardStep, setWizardStep] = useState('name'); // name → gender → spirit → photos → done
  const [formData, setFormData] = useState({
    c1_name: '', c1_gender: '', c1_spirit_animal: '', c1_toy_name: '',
    c2_name: '', c2_gender: '', c2_spirit_animal: '', c2_toy_name: '',
  });
  const [bounceCard, setBounceCard] = useState(null);
  const [photoRefreshKey, setPhotoRefreshKey] = useState(0);
  const [transitionClass, setTransitionClass] = useState('animation-fade-in');
  const [nameError, setNameError] = useState('');
  const nameRef = useRef(null);
  const stepHeadingRef = useRef(null);

  const prefix = `c${childNum}_`;
  const childColor = childNum === 1 ? 'var(--color-child1)' : 'var(--color-child2)';
  const childEmoji = childNum === 1 ? '🌟' : '⭐';

  // Step ordering for directional transitions
  const stepOrder = ['name', 'gender', 'spirit', 'photos'];

  const goToStep = (nextStep) => {
    const curIdx = stepOrder.indexOf(wizardStep);
    const nextIdx = stepOrder.indexOf(nextStep);
    setTransitionClass(nextIdx >= curIdx ? 'animation-slide-in-right' : 'animation-slide-in-left');
    setWizardStep(nextStep);
  };

  // Fetch review count for the badge on photos step
  const stats = usePhotoStore((s) => s.stats);
  const loadPhotos = usePhotoStore((s) => s.loadPhotos);
  const reviewCount = stats?.review_count ?? 0;

  // Derive sibling pair ID for photo APIs (needed early for stats fetch)
  const siblingPairId = formData.c1_name && formData.c2_name
    ? [formData.c1_name, formData.c2_name].sort().join(':')
    : '';

  // Auto-focus name input on name step, heading on other steps
  useEffect(() => {
    if (wizardStep === 'name' && nameRef.current) {
      setTimeout(() => nameRef.current?.focus(), 400);
    } else if (stepHeadingRef.current) {
      setTimeout(() => stepHeadingRef.current?.focus(), 400);
    }
  }, [wizardStep, childNum]);

  // Fetch photo stats when entering photos step (for review badge)
  useEffect(() => {
    if (wizardStep === 'photos' && siblingPairId) {
      loadPhotos(siblingPairId);
    }
  }, [wizardStep, siblingPairId, loadPhotos]);

  const set = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Clear name error when typing
    if (field === `${prefix}name`) setNameError('');
    // Bounce animation
    setBounceCard(value);
    setTimeout(() => setBounceCard(null), 400);
  };

  const handleNameSubmit = (e) => {
    e.preventDefault();
    if (formData[`${prefix}name`].trim()) {
      setNameError('');
      goToStep('gender');
    } else {
      setNameError('Please enter a name');
    }
  };

  const handleGenderPick = (val) => {
    set(`${prefix}gender`, val);
    setTimeout(() => goToStep('spirit'), 350);
  };

  const handleSpiritPick = (val) => {
    set(`${prefix}spirit_animal`, val);
    setTimeout(() => {
      if (childNum === 1) {
        // Move to child 2 — reset to name step with fresh fade-in
        setChildNum(2);
        setTransitionClass('animation-fade-in');
        setWizardStep('name');
      } else {
        // Both kids done — go to optional photo step
        setFormData(prev => ({ ...prev, [`${prefix}spirit_animal`]: val }));
        goToStep('photos');
      }
    }, 500);
  };

  // ── NAME STEP ──────────────────────────────────────
  if (wizardStep === 'name') {
    return (
      <section aria-label={`Step: ${stepLabels.name}`}>
        <div className={`wizard-container ${transitionClass}`} key={`name-${childNum}`}>
          <div className="wizard-child-badge" style={{ color: childColor }}>
            <span className="wizard-child-badge__emoji" aria-hidden="true">{childEmoji}</span>
            <span>Child {childNum}</span>
          </div>

          <h2 className="wizard-question" ref={stepHeadingRef} tabIndex={-1}>
            What's your name?
          </h2>

          <form onSubmit={handleNameSubmit} className="wizard-name-form" noValidate>
            <label htmlFor={`child-${childNum}-name`} className="sr-only">
              Name for Child {childNum}
            </label>
            <input
              ref={nameRef}
              id={`child-${childNum}-name`}
              type="text"
              className="wizard-name-input"
              style={{ borderColor: childColor }}
              value={formData[`${prefix}name`]}
              onChange={e => set(`${prefix}name`, e.target.value)}
              placeholder="Type here…"
              maxLength={20}
              autoComplete="off"
              aria-invalid={nameError ? 'true' : undefined}
              aria-describedby={nameError ? `child-${childNum}-name-error` : undefined}
            />
            <button
              type="submit"
              className="wizard-next-btn"
              disabled={!formData[`${prefix}name`].trim()}
              aria-label="Next step"
            >
              <span className="wizard-next-btn__arrow">→</span>
            </button>
          </form>

          {nameError && (
            <p id={`child-${childNum}-name-error`} className="wizard-hint" role="alert" style={{ color: '#f87171' }}>
              {nameError}
            </p>
          )}

          <p className="wizard-hint">
            {childNum === 1 ? "Let's meet the first adventurer!" : "Now the second hero!"}
          </p>
        </div>
      </section>
    );
  }

  // ── GENDER STEP ────────────────────────────────────
  if (wizardStep === 'gender') {
    return (
      <section aria-label={`Step: ${stepLabels.gender}`}>
        <div className={`wizard-container ${transitionClass}`} key={`gender-${childNum}`}>
          <div className="wizard-child-badge" style={{ color: childColor }}>
            <span className="wizard-child-badge__emoji" aria-hidden="true">{childEmoji}</span>
            <span>{formData[`${prefix}name`]}</span>
          </div>

          <h2 className="wizard-question" ref={stepHeadingRef} tabIndex={-1}>
            Who are you?
          </h2>

          <div className="wizard-card-grid wizard-card-grid--3" role="group" aria-label="Gender options">
            {genders.map(g => (
              <button
                key={g.value}
                className={`wizard-card ${bounceCard === g.value ? 'wizard-card--bounce' : ''}`}
                onClick={() => handleGenderPick(g.value)}
              >
                <span className="wizard-card__emoji" aria-hidden="true">{g.emoji}</span>
                <span className="wizard-card__label">{g.label}</span>
              </button>
            ))}
          </div>
        </div>
      </section>
    );
  }

  // ── SPIRIT ANIMAL STEP ─────────────────────────────
  if (wizardStep === 'spirit') {
    return (
      <section aria-label={`Step: ${stepLabels.spirit}`}>
        <div className={`wizard-container ${transitionClass}`} key={`spirit-${childNum}`}>
          <div className="wizard-child-badge" style={{ color: childColor }}>
            <span className="wizard-child-badge__emoji" aria-hidden="true">{childEmoji}</span>
            <span>{formData[`${prefix}name`]}</span>
          </div>

          <h2 className="wizard-question" ref={stepHeadingRef} tabIndex={-1}>
            Pick your spirit animal!
          </h2>

          <div className="wizard-card-grid wizard-card-grid--3" role="group" aria-label="Spirit animal options">
            {spirits.map(s => (
              <button
                key={s.value}
                className={`wizard-card wizard-card--spirit ${bounceCard === s.value ? 'wizard-card--bounce' : ''}`}
                onClick={() => handleSpiritPick(s.value)}
                style={{ '--spirit-color': s.color }}
              >
                <span className="wizard-card__emoji wizard-card__emoji--big" aria-hidden="true">{s.emoji}</span>
                <span className="wizard-card__label">{s.label}</span>
              </button>
            ))}
          </div>
        </div>
      </section>
    );
  }

  const handleFinish = () => {
    onComplete(formData);
  };

  // ── PHOTOS STEP (optional) ─────────────────────────
  if (wizardStep === 'photos') {
    return (
      <section aria-label={`Step: ${stepLabels.photos}`}>
        <div className={`wizard-container ${transitionClass}`} key="photos">
          <h2 className="wizard-question" ref={stepHeadingRef} tabIndex={-1}>
            Add family photos?
            {reviewCount > 0 && (
              <span className="wizard-review-badge" aria-label={`${reviewCount} photos to review`}>{reviewCount}</span>
            )}
          </h2>

          <PhotoUploader
            siblingPairId={siblingPairId}
            onUploadComplete={() => setPhotoRefreshKey(k => k + 1)}
          />

          <PhotoGallery
            siblingPairId={siblingPairId}
            refreshKey={photoRefreshKey}
          />

          <CharacterMapping
            siblingPairId={siblingPairId}
            onMappingSaved={() => {}}
          />

          {reviewCount > 0 && (
            <ParentApprovalScreen
              siblingPairId={siblingPairId}
              onComplete={() => loadPhotos(siblingPairId)}
            />
          )}

          <div style={{ display: 'flex', gap: '12px', marginTop: '16px' }}>
            <button
              className="wizard-card"
              onClick={handleFinish}
              style={{ padding: '12px 24px', minWidth: '120px' }}
            >
              <span className="wizard-card__emoji" aria-hidden="true">⏭️</span>
              <span className="wizard-card__label">Skip</span>
            </button>
            <button
              className="wizard-card wizard-card--spirit"
              onClick={handleFinish}
              style={{ padding: '12px 24px', minWidth: '120px', '--spirit-color': '#4ade80' }}
            >
              <span className="wizard-card__emoji" aria-hidden="true">🚀</span>
              <span className="wizard-card__label">Go!</span>
            </button>
          </div>
        </div>
      </section>
    );
  }

  return null;
}
