import React from 'react';
import './CharacterSetup.css';

const languages = [
  { code: 'en', name: 'English', flag: '🇺🇸' },
  { code: 'es', name: 'Español', flag: '🇪🇸' },
  { code: 'hi', name: 'हिन्दी', flag: '🇮🇳' },
];

function LanguageSelector({ onSelect }) {
  return (
    <div className="wizard-container animation-fade-in">
      <h2 className="wizard-question">
        Pick your language
      </h2>

      <div className="wizard-card-grid wizard-card-grid--3">
        {languages.map((lang) => (
          <button
            key={lang.code}
            className="wizard-card"
            onClick={() => onSelect(lang.code)}
          >
            <span className="wizard-card__emoji wizard-card__emoji--big">{lang.flag}</span>
            <span className="wizard-card__label">{lang.name}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

export default LanguageSelector;
