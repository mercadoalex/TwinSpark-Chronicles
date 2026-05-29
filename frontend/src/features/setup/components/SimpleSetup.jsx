import React, { useState, useCallback } from 'react';
import SpiritAnimalPicker from './SpiritAnimalPicker';
import { useSetupStore } from '../../../stores/setupStore';
import './SimpleSetup.css';

// Inline translations for the setup flow (language is selected in step 1)
const SETUP_TEXT = {
  en: {
    pickLanguage: '🌍 Pick your language',
    enterNames: "✏️ Enter your children's names",
    child1Label: 'Child 1',
    child2Label: 'Child 2',
    placeholder1: "First child's name",
    placeholder2: "Second child's name",
    next: 'Next →',
    readyTitle: '🎉 Ready to pick spirit animals!',
    letsGo: "Let's go! 🚀",
  },
  es: {
    pickLanguage: '🌍 Elige tu idioma',
    enterNames: '✏️ Escribe los nombres de tus hijos',
    child1Label: 'Niño/a 1',
    child2Label: 'Niño/a 2',
    placeholder1: 'Nombre del primer niño/a',
    placeholder2: 'Nombre del segundo niño/a',
    next: 'Siguiente →',
    readyTitle: '🎉 ¡A elegir animal espiritual!',
    letsGo: '¡Vamos! 🚀',
  },
};

/**
 * Simplified parent setup flow for the new interaction model.
 *
 * Flow (5 total steps):
 *   1. Language selection (English / Spanish) — big flag/icon buttons
 *   2. Enter both children's names — two text inputs, standard keyboard
 *   3. Confirmation — "Ready to pick spirit animals!" with both names
 *   4. Spirit Animal Picker for child 1
 *   5. Spirit Animal Picker for child 2
 *
 * After all steps complete, calls onComplete with the full setup data.
 *
 * Requirements: 6.1, 6.2
 *
 * @param {Object} props
 * @param {(data: { language: string, child1Name: string, child2Name: string, child1Spirit: string, child2Spirit: string }) => void} props.onComplete
 */
function SimpleSetup({ onComplete }) {
  const [step, setStep] = useState('language'); // language | names | confirm | spirit1 | spirit2
  const [language, setLanguage] = useState('');
  const [child1Name, setChild1Name] = useState('');
  const [child2Name, setChild2Name] = useState('');
  const [child1Spirit, setChild1Spirit] = useState('');

  const setupStore = useSetupStore;

  // Get text for current language (defaults to English before selection)
  const txt = SETUP_TEXT[language] || SETUP_TEXT.en;

  // Step 1: Language selection
  const handleLanguageSelect = useCallback((lang) => {
    setLanguage(lang);
    setupStore.getState().setLanguage(lang);
    setStep('names');
  }, [setupStore]);

  // Step 2: Names submission
  const handleNamesSubmit = useCallback((e) => {
    e.preventDefault();
    if (child1Name.trim() && child2Name.trim()) {
      setupStore.getState().setChild1({ name: child1Name.trim() });
      setupStore.getState().setChild2({ name: child2Name.trim() });
      setStep('confirm');
    }
  }, [child1Name, child2Name, setupStore]);

  // Step 3: Confirmation → transition to spirit animal picks
  const handleConfirm = useCallback(() => {
    setStep('spirit1');
  }, []);

  // Step 4: Child 1 picks spirit animal
  const handleSpirit1Select = useCallback((animalId) => {
    setChild1Spirit(animalId);
    setupStore.getState().setChild1({ spirit: animalId });
    setStep('spirit2');
  }, [setupStore]);

  // Step 5: Child 2 picks spirit animal → complete
  const handleSpirit2Select = useCallback((animalId) => {
    setupStore.getState().setChild2({ spirit: animalId });
    setupStore.getState().completeSetup();

    if (onComplete) {
      onComplete({
        language,
        child1Name: child1Name.trim(),
        child2Name: child2Name.trim(),
        child1Spirit,
        child2Spirit: animalId,
      });
    }
  }, [onComplete, language, child1Name, child2Name, child1Spirit, setupStore]);

  // --- Render each step ---

  if (step === 'language') {
    return (
      <div className="simple-setup" aria-label="Setup">
        <div className="simple-setup__screen simple-setup__screen--language">
          <h1 className="simple-setup__title">🌍 Pick your language</h1>
          <div className="simple-setup__language-buttons">
            <button
              className="simple-setup__lang-btn"
              onClick={() => handleLanguageSelect('en')}
              aria-label="English"
            >
              <span className="simple-setup__lang-icon" aria-hidden="true">🇺🇸</span>
              <span className="simple-setup__lang-label">English</span>
            </button>
            <button
              className="simple-setup__lang-btn"
              onClick={() => handleLanguageSelect('es')}
              aria-label="Español"
            >
              <span className="simple-setup__lang-icon" aria-hidden="true">🇪🇸</span>
              <span className="simple-setup__lang-label">Español</span>
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (step === 'names') {
    return (
      <div className="simple-setup" aria-label="Setup">
        <div className="simple-setup__screen simple-setup__screen--names">
          <h1 className="simple-setup__title">{txt.enterNames}</h1>
          <form className="simple-setup__names-form" onSubmit={handleNamesSubmit}>
            <div className="simple-setup__input-group">
              <label className="simple-setup__label" htmlFor="child1-name">
                {txt.child1Label}
              </label>
              <input
                id="child1-name"
                className="simple-setup__input"
                type="text"
                value={child1Name}
                onChange={(e) => setChild1Name(e.target.value)}
                placeholder={txt.placeholder1}
                autoComplete="off"
                maxLength={20}
              />
            </div>
            <div className="simple-setup__input-group">
              <label className="simple-setup__label" htmlFor="child2-name">
                {txt.child2Label}
              </label>
              <input
                id="child2-name"
                className="simple-setup__input"
                type="text"
                value={child2Name}
                onChange={(e) => setChild2Name(e.target.value)}
                placeholder={txt.placeholder2}
                autoComplete="off"
                maxLength={20}
              />
            </div>
            <button
              className="simple-setup__next-btn"
              type="submit"
              disabled={!child1Name.trim() || !child2Name.trim()}
            >
              {txt.next}
            </button>
          </form>
        </div>
      </div>
    );
  }

  if (step === 'confirm') {
    return (
      <div className="simple-setup" aria-label="Setup">
        <div className="simple-setup__screen simple-setup__screen--confirm">
          <h1 className="simple-setup__title">{txt.readyTitle}</h1>
          <div className="simple-setup__confirm-names">
            <p className="simple-setup__confirm-name">
              <span className="simple-setup__confirm-emoji" aria-hidden="true">⭐</span>
              {child1Name.trim()}
            </p>
            <p className="simple-setup__confirm-name">
              <span className="simple-setup__confirm-emoji" aria-hidden="true">⭐</span>
              {child2Name.trim()}
            </p>
          </div>
          <button
            className="simple-setup__next-btn simple-setup__next-btn--big"
            onClick={handleConfirm}
          >
            {txt.letsGo}
          </button>
        </div>
      </div>
    );
  }

  if (step === 'spirit1') {
    return (
      <div className="simple-setup" aria-label="Setup">
        <SpiritAnimalPicker
          key="spirit-picker-child1"
          childName={child1Name.trim()}
          language={language}
          onSelect={handleSpirit1Select}
        />
      </div>
    );
  }

  if (step === 'spirit2') {
    return (
      <div className="simple-setup" aria-label="Setup">
        <SpiritAnimalPicker
          key="spirit-picker-child2"
          childName={child2Name.trim()}
          language={language}
          onSelect={handleSpirit2Select}
        />
      </div>
    );
  }

  return null;
}

export default SimpleSetup;
