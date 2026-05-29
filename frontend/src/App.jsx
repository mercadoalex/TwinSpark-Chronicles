import React from 'react';
import SimpleSetup from './features/setup/components/SimpleSetup';
import StoryScreen from './features/story/components/StoryScreen';
import { PrivacyModal } from './features/setup';
import CelebrationOverlay from './shared/components/CelebrationOverlay';
import { useSetupStore } from './stores/setupStore';
import './App.css';

function App() {
  const isComplete = useSetupStore((s) => s.isComplete);
  const privacyAccepted = useSetupStore((s) => s.privacyAccepted);

  const [showSetupCelebration, setShowSetupCelebration] = React.useState(false);

  const handlePrivacyAccept = () => {
    useSetupStore.getState().acceptPrivacy();
  };

  return (
    <div className="app-container">
      {/* Privacy gate */}
      {!privacyAccepted && (
        <PrivacyModal onAccept={handlePrivacyAccept} />
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
