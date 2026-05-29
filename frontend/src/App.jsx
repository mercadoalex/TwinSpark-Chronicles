import React from 'react';
import { translations } from './locales';

// Screen containers
import SimpleSetup from './features/setup/components/SimpleSetup';
import { StoryScreen } from './features/story';

// Shared components
import {
  AlertModal,
  AppContainer,
  SkipLink,
  CelebrationOverlay,
} from './shared/components';

// Feature components
import { PrivacyModal } from './features/setup';
import VoiceCommandToast from './features/story/components/VoiceCommandToast';

// Hooks & stores
import { useSetupStore } from './stores/setupStore';
import { useAudioFeedback } from './features/audio/hooks/useAudioFeedback';

import './App.css';

function App() {
  const isComplete = useSetupStore(s => s.isComplete);
  const privacyAccepted = useSetupStore(s => s.privacyAccepted);
  const language = useSetupStore(s => s.language);
  const t = language ? translations[language] : translations.en;

  const { playSuccess } = useAudioFeedback();

  // UI state that stays in App shell
  const [alertMessage, setAlertMessage] = React.useState(null);
  const [showSetupCelebration, setShowSetupCelebration] = React.useState(false);
  const [voiceCommandMatch, setVoiceCommandMatch] = React.useState(null);

  const handlePrivacyAccept = () => {
    useSetupStore.getState().acceptPrivacy();
    playSuccess();
  };

  // Compute whether any modal is open for aria-hidden on background content
  const isAnyModalOpen = Boolean(alertMessage || !privacyAccepted);

  return (
    <AppContainer>
      {/* Skip navigation link — first focusable element */}
      <SkipLink />

      {/* Main app content — hidden from assistive tech when modals are open */}
      <div aria-hidden={isAnyModalOpen || undefined}>
        {privacyAccepted && !isComplete && (
          <SimpleSetup
            onComplete={() => {
              setShowSetupCelebration(true);
              setTimeout(() => setShowSetupCelebration(false), 2500);
            }}
          />
        )}

        {isComplete && (
          <StoryScreen
            t={t}
            onAlert={setAlertMessage}
            onVoiceCommand={setVoiceCommandMatch}
          />
        )}
      </div>

      {/* Modals layer (outside aria-hidden) */}
      {!privacyAccepted && (
        <PrivacyModal onAccept={handlePrivacyAccept} t={t} />
      )}

      <AlertModal
        message={alertMessage}
        onClose={() => setAlertMessage(null)}
      />

      <VoiceCommandToast match={voiceCommandMatch} t={t} />

      {showSetupCelebration && (
        <CelebrationOverlay type="confetti" duration={2500} particleCount={60} />
      )}
    </AppContainer>
  );
}

export default App;
