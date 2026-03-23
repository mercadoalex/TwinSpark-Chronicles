import React, { useEffect } from 'react';
import LanguageSelector from './LanguageSelector';
import CharacterSetup from './CharacterSetup';
import costumeCatalog from '../data/costumeCatalog';
import { ContinueScreen } from '../../session';
import { useStoryConnection } from '../../session';
import { useSetupStore } from '../../../stores/setupStore';
import { useSessionStore } from '../../../stores/sessionStore';
import { useSessionPersistenceStore } from '../../../stores/sessionPersistenceStore';
import { useAudioFeedback } from '../../audio/hooks/useAudioFeedback';
import { useFeedback, SetupErrorBoundary } from '../../../shared/components';

export default function SetupScreen({ t, onSetupCelebration }) {
  const setup = useSetupStore();
  const persistence = useSessionPersistenceStore();
  const session = useSessionStore();
  const { playSuccess } = useAudioFeedback();
  const { showFeedback, FeedbackComponent } = useFeedback();
  const { connectToAI } = useStoryConnection();

  const handleLanguageSelect = (lang) => {
    setup.setLanguage(lang);
    showFeedback('success', `${lang.toUpperCase()} selected!`, 1500);
    playSuccess();
  };

  const handleSetupComplete = (profiles) => {
    console.log("📋 Received profiles from CharacterSetup:", profiles);

    const spiritToPersonality = {
      'dragon': 'brave',
      'unicorn': 'creative',
      'owl': 'wise',
      'dolphin': 'friendly',
      'phoenix': 'resilient',
      'tiger': 'confident'
    };

    const lookupCostumePrompt = (id) => {
      const entry = costumeCatalog.find(c => c.id === id);
      return entry ? entry.promptFragment : null;
    };

    const enrichedProfiles = {
      c1_name: profiles.c1_name || "Child 1",
      c1_gender: profiles.c1_gender || "girl",
      c1_personality: spiritToPersonality[profiles.c1_spirit_animal?.toLowerCase()] || 'brave',
      c1_spirit: profiles.c1_spirit_animal || 'Dragon',
      c1_costume: profiles.c1_costume || 'adventure_clothes',
      c1_costume_prompt: lookupCostumePrompt(profiles.c1_costume) || 'wearing adventure clothes',
      c1_toy: profiles.c1_toy_name || 'Bruno',
      c1_toy_type: profiles.c1_toy_type || 'preset',
      c1_toy_image: profiles.c1_toy_image || '',
      c2_name: profiles.c2_name || "Child 2",
      c2_gender: profiles.c2_gender || "boy",
      c2_personality: spiritToPersonality[profiles.c2_spirit_animal?.toLowerCase()] || 'wise',
      c2_spirit: profiles.c2_spirit_animal || 'Owl',
      c2_costume: profiles.c2_costume || 'adventure_clothes',
      c2_costume_prompt: lookupCostumePrompt(profiles.c2_costume) || 'wearing adventure clothes',
      c2_toy: profiles.c2_toy_name || 'Book',
      c2_toy_type: profiles.c2_toy_type || 'preset',
      c2_toy_image: profiles.c2_toy_image || ''
    };

    console.log("🔌 Enriched profiles:", enrichedProfiles);

    setup.setChild1({
      name: enrichedProfiles.c1_name,
      gender: enrichedProfiles.c1_gender,
      personality: enrichedProfiles.c1_personality,
      spirit: enrichedProfiles.c1_spirit,
      costume: enrichedProfiles.c1_costume,
      toy: enrichedProfiles.c1_toy,
      toyType: enrichedProfiles.c1_toy_type,
      toyImage: enrichedProfiles.c1_toy_image
    });

    setup.setChild2({
      name: enrichedProfiles.c2_name,
      gender: enrichedProfiles.c2_gender,
      personality: enrichedProfiles.c2_personality,
      spirit: enrichedProfiles.c2_spirit,
      costume: enrichedProfiles.c2_costume,
      toy: enrichedProfiles.c2_toy,
      toyType: enrichedProfiles.c2_toy_type,
      toyImage: enrichedProfiles.c2_toy_image
    });

    setup.completeSetup();
    session.setProfiles(enrichedProfiles);
    connectToAI(setup.language, enrichedProfiles);

    // Trigger setup-complete celebration confetti
    if (onSetupCelebration) onSetupCelebration();
  };

  const handleContinueStory = () => {
    try {
      persistence.restoreSession();

      // After restore, setupStore.isComplete is true and profiles are set
      // Connect to AI with the restored profiles
      const restoredSetup = useSetupStore.getState();
      const restoredProfiles = {
        c1_name: restoredSetup.child1.name,
        c1_gender: restoredSetup.child1.gender,
        c1_personality: restoredSetup.child1.personality,
        c1_spirit: restoredSetup.child1.spirit,
        c1_costume: restoredSetup.child1.costume,
        c1_toy: restoredSetup.child1.toy,
        c1_toy_type: restoredSetup.child1.toyType,
        c1_toy_image: restoredSetup.child1.toyImage,
        c2_name: restoredSetup.child2.name,
        c2_gender: restoredSetup.child2.gender,
        c2_personality: restoredSetup.child2.personality,
        c2_spirit: restoredSetup.child2.spirit,
        c2_costume: restoredSetup.child2.costume,
        c2_toy: restoredSetup.child2.toy,
        c2_toy_type: restoredSetup.child2.toyType,
        c2_toy_image: restoredSetup.child2.toyImage,
      };

      useSessionStore.getState().setProfiles(restoredProfiles);
      connectToAI(restoredSetup.language, restoredProfiles);

      // Clear the available session since we've restored it
      useSessionPersistenceStore.setState({ availableSession: null });
    } catch (err) {
      console.error('Failed to restore session:', err);
      // Discard and show normal setup
      useSessionPersistenceStore.setState({ availableSession: null });
    }
  };

  const handleNewAdventure = async () => {
    const setupState = useSetupStore.getState();
    const c1Name = setupState.child1?.name;
    const c2Name = setupState.child2?.name;

    if (c1Name && c2Name) {
      const siblingPairId = [c1Name, c2Name].sort().join(':');
      await persistence.deleteSession(siblingPairId);
    }

    // Clear available session and proceed to normal setup
    useSessionPersistenceStore.setState({ availableSession: null });
  };

  // Check for existing session after privacy + language
  useEffect(() => {
    if (setup.privacyAccepted && setup.language && setup.currentStep === 'characters') {
      const setupState = useSetupStore.getState();
      const c1Name = setupState.child1?.name;
      const c2Name = setupState.child2?.name;

      if (c1Name && c2Name) {
        const siblingPairId = [c1Name, c2Name].sort().join(':');
        persistence.loadSnapshot(siblingPairId);
      }
    }
  }, [setup.privacyAccepted, setup.language, setup.currentStep]);

  return (
    <>
      {/* Title */}
      <h1 className="app-title text-gradient logo-animation">
        TwinSpark Chronicles
      </h1>

      {FeedbackComponent}

      {/* Language Selection */}
      {setup.currentStep === 'language' && (
        <LanguageSelector onSelect={handleLanguageSelect} />
      )}

      {/* Continue Screen — shown when a saved session exists */}
      {setup.currentStep === 'characters' && persistence.availableSession && (
        <ContinueScreen
          snapshot={persistence.availableSession}
          onContinue={handleContinueStory}
          onNewAdventure={handleNewAdventure}
        />
      )}

      {/* Character Setup Wizard — shown when no saved session */}
      {setup.currentStep === 'characters' && !persistence.availableSession && (
        <SetupErrorBoundary onReset={() => setup.reset()}>
          <CharacterSetup
            onComplete={handleSetupComplete}
            language={setup.language}
            t={t}
          />
        </SetupErrorBoundary>
      )}
    </>
  );
}
