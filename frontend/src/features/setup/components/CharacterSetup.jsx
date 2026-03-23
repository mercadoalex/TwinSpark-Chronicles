import { useReducer, useRef, useEffect } from 'react';
import PhotoUploader from './PhotoUploader';
import PhotoGallery from './PhotoGallery';
import CharacterMapping from './CharacterMapping';
import ParentApprovalScreen from './ParentApprovalScreen';
import CostumeSelector from './CostumeSelector';
import { usePhotoStore } from '../../../stores/photoStore';
import CelebrationOverlay from '../../../shared/components/CelebrationOverlay';
import { wizardReducer, initialState, ActionTypes, STEP_ORDER } from '../reducers/wizardReducer';
import './CharacterSetup.css';

const stepLabels = {
  name: 'Name',
  gender: 'Gender',
  spirit: 'Spirit Animal',
  costume: 'Costume',
  toy: 'Toy Companion',
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

const presetToys = [
  { value: 'teddy', emoji: '🧸', label: 'Teddy Bear' },
  { value: 'robot', emoji: '🤖', label: 'Robot' },
  { value: 'bunny', emoji: '🐰', label: 'Bunny' },
  { value: 'dino',  emoji: '🦕', label: 'Dinosaur' },
  { value: 'kitty', emoji: '🐱', label: 'Kitty' },
  { value: 'puppy', emoji: '🐶', label: 'Puppy' },
];

export default function CharacterSetup({ t, onComplete }) {
  const [state, dispatch] = useReducer(wizardReducer, initialState);
  const {
    childNum, wizardStep, formData, bounceCard,
    photoRefreshKey, transitionClass, nameError,
    showSparkle, toyPhotoPreview, toyPhotoFile, toyError,
  } = state;

  const nameRef = useRef(null);
  const stepHeadingRef = useRef(null);
  const toyFileRef = useRef(null);

  const prefix = `c${childNum}_`;
  const childColor = childNum === 1 ? 'var(--color-child1)' : 'var(--color-child2)';
  const childEmoji = childNum === 1 ? '🌟' : '⭐';

  // Progress indicator helper
  const renderProgress = () => {
    const curIdx = STEP_ORDER.indexOf(wizardStep);
    return (
      <div className="wizard-progress" aria-label={`Step ${curIdx + 1} of ${STEP_ORDER.length}`} role="progressbar" aria-valuenow={curIdx + 1} aria-valuemin={1} aria-valuemax={STEP_ORDER.length}>
        {STEP_ORDER.map((step, i) => (
          <span
            key={step}
            className={`wizard-progress__dot${i < curIdx ? ' wizard-progress__dot--completed' : ''}${i === curIdx ? ' wizard-progress__dot--current' : ''}`}
            aria-hidden="true"
          />
        ))}
      </div>
    );
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

  const handleNameSubmit = (e) => {
    e.preventDefault();
    if (formData[`${prefix}name`].trim()) {
      dispatch({ type: ActionTypes.SET_NAME_ERROR, error: '' });
      dispatch({ type: ActionTypes.GO_TO_STEP, step: 'gender' });
    } else {
      dispatch({ type: ActionTypes.SET_NAME_ERROR, error: 'Please enter a name' });
    }
  };

  const handleGenderPick = (val) => {
    dispatch({ type: ActionTypes.PICK_GENDER, value: val });
    setTimeout(() => dispatch({ type: ActionTypes.HIDE_SPARKLE }), 800);
    setTimeout(() => dispatch({ type: ActionTypes.GO_TO_STEP, step: 'spirit' }), 350);
  };

  const handleSpiritPick = (val) => {
    dispatch({ type: ActionTypes.PICK_SPIRIT, value: val });
    setTimeout(() => dispatch({ type: ActionTypes.HIDE_SPARKLE }), 800);
    setTimeout(() => dispatch({ type: ActionTypes.GO_TO_STEP, step: 'costume' }), 500);
  };

  const handleCostumePick = (val) => {
    dispatch({ type: ActionTypes.PICK_COSTUME, value: val });
    setTimeout(() => dispatch({ type: ActionTypes.HIDE_SPARKLE }), 800);
    setTimeout(() => dispatch({ type: ActionTypes.GO_TO_STEP, step: 'toy' }), 500);
  };

  const handleToyNext = () => {
    if (childNum === 1) {
      dispatch({ type: ActionTypes.NEXT_CHILD });
    } else {
      dispatch({ type: ActionTypes.GO_TO_STEP, step: 'photos' });
    }
  };

  // ── NAME STEP ──────────────────────────────────────
  if (wizardStep === 'name') {
    return (
      <section aria-label={`Step: ${stepLabels.name}`}>
        {renderProgress()}
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
              onChange={e => {
                dispatch({ type: ActionTypes.SET_FIELD, field: `${prefix}name`, value: e.target.value });
                setTimeout(() => dispatch({ type: ActionTypes.CLEAR_BOUNCE }), 400);
              }}
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
        {renderProgress()}
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
          {showSparkle && <CelebrationOverlay type="sparkle" duration={800} particleCount={10} />}
        </div>
      </section>
    );
  }

  // ── SPIRIT ANIMAL STEP ─────────────────────────────
  if (wizardStep === 'spirit') {
    return (
      <section aria-label={`Step: ${stepLabels.spirit}`}>
        {renderProgress()}
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
          {showSparkle && <CelebrationOverlay type="sparkle" duration={800} particleCount={10} />}
        </div>
      </section>
    );
  }

  // ── COSTUME STEP ──────────────────────────────────
  if (wizardStep === 'costume') {
    return (
      <CostumeSelector
        childNum={childNum}
        childName={formData[`${prefix}name`]}
        childColor={childColor}
        childEmoji={childEmoji}
        onSelect={handleCostumePick}
        renderProgress={renderProgress}
        transitionClass={transitionClass}
      />
    );
  }

  // ── TOY COMPANION STEP ───────────────────────────────
  if (wizardStep === 'toy') {
    const toyName = formData[`${prefix}toy_name`];
    const toyType = formData[`${prefix}toy_type`];
    const toyImage = formData[`${prefix}toy_image`];
    const canProceed = toyName.trim().length > 0 && (toyType === 'preset' || toyType === 'photo');

    const handlePresetPick = (val) => {
      dispatch({ type: ActionTypes.PICK_PRESET_TOY, value: val });
      setTimeout(() => dispatch({ type: ActionTypes.CLEAR_BOUNCE }), 400);
    };

    const handleToyPhoto = (e) => {
      const file = e.target.files?.[0];
      if (!file) return;
      if (file.size > 10 * 1024 * 1024) {
        dispatch({ type: ActionTypes.SET_TOY_ERROR, error: 'Photo is too big! Try a smaller one 📸' });
        e.target.value = '';
        return;
      }
      const reader = new FileReader();
      reader.onload = (ev) => {
        dispatch({ type: ActionTypes.SET_TOY_PHOTO, preview: ev.target.result, file });
      };
      reader.readAsDataURL(file);
      e.target.value = '';
    };

    const handleToyNextClick = async () => {
      if (!toyName.trim()) {
        dispatch({ type: ActionTypes.SET_TOY_ERROR, error: 'Please name your toy!' });
        return;
      }
      dispatch({ type: ActionTypes.SET_TOY_ERROR, error: '' });

      if (toyType === 'photo' && toyPhotoFile && siblingPairId) {
        try {
          const body = new FormData();
          body.append('file', toyPhotoFile);
          const res = await fetch(
            `http://localhost:8000/api/toy-photo/${encodeURIComponent(siblingPairId)}/${childNum}`,
            { method: 'POST', body }
          );
          if (!res.ok) throw new Error('upload failed');
          const data = await res.json();
          dispatch({ type: ActionTypes.SET_FIELD, field: `${prefix}toy_image`, value: data.image_url });
          setTimeout(() => dispatch({ type: ActionTypes.CLEAR_BOUNCE }), 400);
        } catch {
          dispatch({ type: ActionTypes.SET_TOY_ERROR, error: 'Oops! Try again 🔄' });
          return;
        }
      }

      handleToyNext();
    };

    return (
      <section aria-label={`Step: ${stepLabels.toy}`}>
        {renderProgress()}
        <div className={`wizard-container ${transitionClass}`} key={`toy-${childNum}`}>
          <div className="wizard-child-badge" style={{ color: childColor }}>
            <span className="wizard-child-badge__emoji" aria-hidden="true">{childEmoji}</span>
            <span>{formData[`${prefix}name`]}</span>
          </div>

          <h2 className="wizard-question" ref={stepHeadingRef} tabIndex={-1}>
            Name your toy friend!
          </h2>

          {/* Toy name input */}
          <div className="wizard-name-form">
            <label htmlFor={`child-${childNum}-toy-name`} className="sr-only">
              Toy name for {formData[`${prefix}name`]}
            </label>
            <input
              id={`child-${childNum}-toy-name`}
              type="text"
              className="wizard-name-input"
              style={{ borderColor: childColor }}
              value={toyName}
              onChange={e => {
                dispatch({ type: ActionTypes.SET_FIELD, field: `${prefix}toy_name`, value: e.target.value });
                setTimeout(() => dispatch({ type: ActionTypes.CLEAR_BOUNCE }), 400);
                if (toyError === 'Please name your toy!') dispatch({ type: ActionTypes.SET_TOY_ERROR, error: '' });
              }}
              placeholder={childNum === 1 ? 'Bruno' : 'Book'}
              maxLength={20}
              autoComplete="off"
              aria-invalid={toyError === 'Please name your toy!' ? 'true' : undefined}
              aria-describedby={toyError ? `child-${childNum}-toy-error` : undefined}
            />
          </div>

          {toyError && (
            <p id={`child-${childNum}-toy-error`} className="wizard-hint" role="alert" style={{ color: '#f87171' }}>
              {toyError}
            </p>
          )}

          <p className="wizard-hint">Pick a toy or snap a photo of yours!</p>

          {/* Preset toy grid */}
          <div className="wizard-card-grid wizard-card-grid--3" role="group" aria-label="Preset toy options">
            {presetToys.map(toy => (
              <button
                key={toy.value}
                className={`wizard-card wizard-card--spirit ${bounceCard === toy.value ? 'wizard-card--bounce' : ''} ${toyType === 'preset' && toyImage === toy.value ? 'wizard-card--toy-selected' : ''}`}
                onClick={() => handlePresetPick(toy.value)}
                aria-label={`Select ${toy.label}`}
                aria-pressed={toyType === 'preset' && toyImage === toy.value}
                style={{ '--spirit-color': childColor }}
              >
                <span className="wizard-card__emoji wizard-card__emoji--big" aria-hidden="true">{toy.emoji}</span>
                <span className="wizard-card__label">{toy.label}</span>
              </button>
            ))}
          </div>

          {/* Photo capture */}
          <input
            ref={toyFileRef}
            type="file"
            accept="image/*"
            capture="environment"
            style={{ display: 'none' }}
            onChange={handleToyPhoto}
            aria-hidden="true"
          />
          <button
            className="wizard-card toy-photo-btn"
            onClick={() => toyFileRef.current?.click()}
            aria-label="Take a photo of your toy"
          >
            <span className="wizard-card__emoji" aria-hidden="true">📸</span>
            <span className="wizard-card__label">
              {toyPhotoPreview ? 'Retake Photo' : 'Photo of My Toy'}
            </span>
          </button>

          {/* Photo thumbnail preview */}
          {toyPhotoPreview && (
            <div className="toy-photo-preview" style={{ '--spirit-color': childColor }}>
              <img
                src={toyPhotoPreview}
                alt="Your toy photo"
              />
            </div>
          )}

          {/* Next button */}
          <button
            className="wizard-next-btn"
            disabled={!canProceed}
            onClick={handleToyNextClick}
            aria-label="Next step"
          >
            <span className="wizard-next-btn__arrow">→</span>
          </button>
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
        {renderProgress()}
        <div className={`wizard-container ${transitionClass}`} key="photos">
          <h2 className="wizard-question" ref={stepHeadingRef} tabIndex={-1}>
            📸 Make the story yours!
            {reviewCount > 0 && (
              <span className="wizard-review-badge" aria-label={`${reviewCount} photos to review`}>{reviewCount}</span>
            )}
          </h2>

          <p style={{
            fontFamily: 'var(--font-body)',
            fontSize: 'clamp(1rem, 3vw, 1.25rem)',
            color: 'rgba(255, 255, 255, 0.85)',
            maxWidth: '480px',
            lineHeight: 1.7,
            textAlign: 'center',
            margin: '0 auto',
          }}>
            Add a family photo and your faces will appear <strong style={{ color: 'var(--color-gold)' }}>inside the story illustrations</strong>! The characters will look like you. ✨
          </p>

          <PhotoUploader
            siblingPairId={siblingPairId}
            onUploadComplete={() => dispatch({ type: ActionTypes.SET_PHOTO_REFRESH })}
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
              className="wizard-card wizard-review-slide-left"
              onClick={handleFinish}
              style={{ padding: '12px 24px', minWidth: '120px' }}
            >
              <span className="wizard-card__emoji" aria-hidden="true">⏭️</span>
              <span className="wizard-card__label">Skip</span>
            </button>
            <button
              className="wizard-card wizard-card--spirit wizard-review-slide-right"
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
