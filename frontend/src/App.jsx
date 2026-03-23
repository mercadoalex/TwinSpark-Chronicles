import React, { useEffect } from 'react';
import { translations } from './locales';

// Screen containers
import { SetupScreen } from './features/setup';
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
import { useGamepad } from './shared/hooks/useGamepad';
import ConnectionIndicator from './shared/components/ConnectionIndicator';
import VirtualKeyboard from './features/setup/components/VirtualKeyboard';
import { useGamepadStore } from './stores/gamepadStore';
import * as FocusNavigator from './shared/hooks/FocusNavigator';
import { useAudioFeedback } from './features/audio/hooks/useAudioFeedback';

import './App.css';

function App() {
  const isComplete = useSetupStore(s => s.isComplete);
  const privacyAccepted = useSetupStore(s => s.privacyAccepted);
  const language = useSetupStore(s => s.language);
  const t = language ? translations[language] : translations.en;

  const { playSuccess } = useAudioFeedback();

  // Gamepad support
  useGamepad();
  const virtualKeyboardOpen = useGamepadStore(s => s.virtualKeyboardOpen);
  const virtualKeyboardTarget = useGamepadStore(s => s.virtualKeyboardTarget);

  // UI state that stays in App shell
  const [alertMessage, setAlertMessage] = React.useState(null);
  const [showSetupCelebration, setShowSetupCelebration] = React.useState(false);
  const [voiceCommandMatch, setVoiceCommandMatch] = React.useState(null);

  const handlePrivacyAccept = () => {
    useSetupStore.getState().acceptPrivacy();
    playSuccess();
  };

  // Click-sync: update gamepad focus when user clicks with mouse/touch
  useEffect(() => {
    const handleClick = (e) => {
      if (useGamepadStore.getState().connected) {
        FocusNavigator.syncToElement(e.target);
      }
    };
    document.addEventListener('click', handleClick);
    return () => document.removeEventListener('click', handleClick);
  }, []);

  // Compute whether any modal is open for aria-hidden on background content
  const isAnyModalOpen = Boolean(alertMessage || !privacyAccepted);

  return (
    <AppContainer>
      {/* Skip navigation link — first focusable element */}
      <SkipLink />

      {/* Main app content — hidden from assistive tech when modals are open */}
      <div aria-hidden={isAnyModalOpen || undefined}>
        {privacyAccepted && !isComplete && (
          <SetupScreen
            t={t}
            onSetupCelebration={() => {
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

      {/* Gamepad connection indicator */}
      <ConnectionIndicator />

      {/* Virtual keyboard overlay for gamepad text entry */}
      {virtualKeyboardOpen && (
        <VirtualKeyboard
          targetValue={
            (() => {
              const el = document.activeElement?.tagName === 'INPUT' || document.activeElement?.tagName === 'TEXTAREA'
                ? document.activeElement
                : document.getElementById(virtualKeyboardTarget);
              return el ? el.value : '';
            })()
          }
          onCharacter={(char) => {
            const el = document.activeElement?.tagName === 'INPUT' || document.activeElement?.tagName === 'TEXTAREA'
              ? document.activeElement
              : document.getElementById(virtualKeyboardTarget);
            if (el) {
              const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
                window.HTMLInputElement.prototype, 'value'
              )?.set || Object.getOwnPropertyDescriptor(
                window.HTMLTextAreaElement.prototype, 'value'
              )?.set;
              if (nativeInputValueSetter) {
                nativeInputValueSetter.call(el, el.value + char);
              } else {
                el.value = el.value + char;
              }
              el.dispatchEvent(new Event('input', { bubbles: true }));
            }
          }}
          onBackspace={() => {
            const el = document.activeElement?.tagName === 'INPUT' || document.activeElement?.tagName === 'TEXTAREA'
              ? document.activeElement
              : document.getElementById(virtualKeyboardTarget);
            if (el && el.value.length > 0) {
              const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
                window.HTMLInputElement.prototype, 'value'
              )?.set || Object.getOwnPropertyDescriptor(
                window.HTMLTextAreaElement.prototype, 'value'
              )?.set;
              if (nativeInputValueSetter) {
                nativeInputValueSetter.call(el, el.value.slice(0, -1));
              } else {
                el.value = el.value.slice(0, -1);
              }
              el.dispatchEvent(new Event('input', { bubbles: true }));
            }
          }}
          onDone={() => useGamepadStore.getState().closeVirtualKeyboard()}
          onCancel={() => useGamepadStore.getState().closeVirtualKeyboard()}
        />
      )}
    </AppContainer>
  );
}

export default App;
