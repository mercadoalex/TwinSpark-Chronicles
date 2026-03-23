import { useState } from 'react';
import costumeCatalog from '../data/costumeCatalog';
import CelebrationOverlay from '../../../shared/components/CelebrationOverlay';

export default function CostumeSelector({
  childNum,
  childName,
  childColor,
  childEmoji,
  onSelect,
  renderProgress,
  transitionClass,
}) {
  const [bounceCard, setBounceCard] = useState(null);
  const [showSparkle, setShowSparkle] = useState(false);

  const handlePick = (costumeId) => {
    setBounceCard(costumeId);
    setShowSparkle(true);
    setTimeout(() => setShowSparkle(false), 800);
    setTimeout(() => onSelect(costumeId), 350);
  };

  return (
    <section aria-label="Step: Costume">
      {renderProgress()}
      <div className={`wizard-container ${transitionClass}`} key={`costume-${childNum}`}>
        <div className="wizard-child-badge" style={{ color: childColor }}>
          <span className="wizard-child-badge__emoji" aria-hidden="true">{childEmoji}</span>
          <span>{childName}</span>
        </div>

        <h2 className="wizard-question" tabIndex={-1}>
          Pick your costume!
        </h2>

        <div className="wizard-card-grid wizard-card-grid--3" role="group" aria-label="Costume options">
          {costumeCatalog.map((c) => (
            <button
              key={c.id}
              className={`wizard-card wizard-card--spirit ${bounceCard === c.id ? 'wizard-card--bounce' : ''}`}
              onClick={() => handlePick(c.id)}
              aria-label={c.label}
              style={{ '--spirit-color': c.color }}
            >
              <span className="wizard-card__emoji wizard-card__emoji--big" aria-hidden="true">{c.emoji}</span>
              <span className="wizard-card__label">{c.label}</span>
            </button>
          ))}
        </div>
        {showSparkle && <CelebrationOverlay type="sparkle" duration={800} particleCount={10} />}
      </div>
    </section>
  );
}
