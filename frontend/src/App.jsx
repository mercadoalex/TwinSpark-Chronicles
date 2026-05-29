import React from 'react';
import SimpleSetup from './features/setup/components/SimpleSetup';
import StoryScreen from './features/story/components/StoryScreen';
import { PrivacyModal } from './features/setup';
import CelebrationOverlay from './shared/components/CelebrationOverlay';
import { useSetupStore } from './stores/setupStore';
import { useStoryLoopStore } from './stores/storyLoopStore';
import './App.css';

function App() {
  const isComplete = useSetupStore((s) => s.isComplete);
  const privacyAccepted = useSetupStore((s) => s.privacyAccepted);
  const language = useSetupStore((s) => s.language);

  const [showSetupCelebration, setShowSetupCelebration] = React.useState(false);
  const [showSettings, setShowSettings] = React.useState(false);

  const handlePrivacyAccept = () => {
    useSetupStore.getState().acceptPrivacy();
  };

  const handleResetGame = () => {
    // Clear all persisted state
    useSetupStore.getState().reset();
    useStoryLoopStore.getState().reset();
    localStorage.removeItem('twinspark_story_session');
    localStorage.removeItem('setup-storage');
    localStorage.removeItem('scene-audio-storage');
    setShowSettings(false);
    // Force reload to clear all state
    window.location.reload();
  };

  const handleChangeLanguage = (lang) => {
    useSetupStore.getState().setLanguage(lang);
    setShowSettings(false);
  };

  return (
    <div className="app-container">
      {/* Privacy gate */}
      {!privacyAccepted && (
        <PrivacyModal onAccept={handlePrivacyAccept} />
      )}

      {/* Logo + Settings — shown after privacy accepted */}
      {privacyAccepted && (
        <header className="app-header">
          <h1 className="app-logo">✨ TwinSpark ✨</h1>
          <button
            className="app-settings-btn"
            onClick={() => setShowSettings(!showSettings)}
            aria-label="Settings"
          >
            ⚙️
          </button>
        </header>
      )}

      {/* Settings panel */}
      {showSettings && (
        <div className="app-settings-panel">
          <h3 className="app-settings-title">Settings</h3>
          <div className="app-settings-options">
            <button
              className="app-settings-option"
              onClick={() => handleChangeLanguage(language === 'en' ? 'es' : 'en')}
            >
              🌍 {language === 'en' ? 'Cambiar a Español' : 'Switch to English'}
            </button>
            <button
              className="app-settings-option app-settings-option--danger"
              onClick={handleResetGame}
            >
              🔄 {language === 'es' ? 'Reiniciar juego' : 'Reset game'}
            </button>
          </div>
          <button
            className="app-settings-close"
            onClick={() => setShowSettings(false)}
          >
            ✕
          </button>
        </div>
      )}

      {/* Setup flow */}
      {privacyAccepted && !isComplete && (
        <SimpleSetup
          onComplete={() => {
            setShowSetupCelebration(true);
            setTimeout(() => setShowSetupCelebration(false), 2500);
          }}
        />
      )}

      {/* Story experience */}
      {isComplete && <StoryScreen />}

      {/* Setup celebration */}
      {showSetupCelebration && (
        <CelebrationOverlay type="confetti" duration={2500} particleCount={60} />
      )}
    </div>
  );
}

export default App;
