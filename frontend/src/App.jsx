import React, { useEffect, useRef } from 'react';
import { Mic, Eye, Settings } from 'lucide-react';
import { translations } from './locales';

// ==========================================
// FEATURE COMPONENTS
// ==========================================

// Setup Feature
import { 
  PrivacyModal, 
  LanguageSelector, 
  CharacterSetup,
  ParentDashboard 
} from './features/setup';

// Story Feature
import { DualStoryDisplay } from './features/story';

// Audio Feature
import { VoiceOnlyMode, MultimodalControls } from './features/audio';

// Camera / Multimodal Feature
import CameraPreview from './features/camera/components/CameraPreview.jsx';
import MultimodalFeedback from './features/camera/components/MultimodalFeedback.jsx';

// Session Feature
import { SessionStatus, MagicMirror } from './features/session';

// ==========================================
// SHARED COMPONENTS
// ==========================================

import {
  ChildFriendlyButton,
  AlertModal,
  ExitModal,
  LoadingAnimation,
  useFeedback,
  AppContainer
} from './shared/components';

// ==========================================
// SERVICES
// ==========================================

import { websocketService } from './features/session/services/websocketService';

// ==========================================
// SIBLING DYNAMICS COMPONENTS
// ==========================================

import SiblingDashboard from './components/SiblingDashboard.jsx';
import DualPrompt from './components/DualPrompt.jsx';

// ==========================================
// STORES
// ==========================================

import { useSessionStore } from './stores/sessionStore';
import { useStoryStore } from './stores/storyStore';
import { useAudioStore } from './stores/audioStore';
import { useSetupStore } from './stores/setupStore';
import { useSiblingStore } from './stores/siblingStore';

// ==========================================
// HOOKS
// ==========================================

import { useAudio } from './features/audio/hooks/useAudio';
import { useAudioFeedback } from './features/audio/hooks/useAudioFeedback';
import { useMultimodalInput } from './features/camera/hooks/useMultimodalInput.js';

// ==========================================
// STYLES
// ==========================================

import './App.css';

// ==========================================
// COMPONENT
// ==========================================

function App() {
  // ===========================================
  // ZUSTAND STORES
  // ===========================================
  
  const session = useSessionStore();
  const story = useStoryStore();
  const audio = useAudioStore();
  const setup = useSetupStore();
  const sibling = useSiblingStore();

  // ===========================================
  // CUSTOM HOOKS
  // ===========================================
  
  const { playSuccess, playError, playChoice } = useAudioFeedback();
  const { speak, stop: stopSpeech } = useAudio(setup.language);
  const { showFeedback, FeedbackComponent } = useFeedback();
  const { startCapture, stopCapture } = useMultimodalInput();

  // ===========================================
  // LOCAL STATE (UI only)
  // ===========================================
  
  const [isListening, setIsListening] = React.useState(true);
  const [hasCamera, setHasCamera] = React.useState(true);
  const [voiceOnlyMode, setVoiceOnlyMode] = React.useState(false);
  const [showExitModal, setShowExitModal] = React.useState(false);
  const [isSaving, setIsSaving] = React.useState(false);
  const [alertMessage, setAlertMessage] = React.useState(null);
  const [showDashboard, setShowDashboard] = React.useState(false);
  const [mechanics, setMechanics] = React.useState(null);
  const [child1Responded, setChild1Responded] = React.useState(false);
  const [child2Responded, setChild2Responded] = React.useState(false);

  const unsubscribers = useRef([]);
  const t = setup.language ? translations[setup.language] : translations.en;

  // ===========================================
  // WEBSOCKET CONNECTION HANDLER
  // ===========================================

  const connectToAI = (lang, profiles) => {
    console.log(`🔌 Connecting to TwinSpark AI in ${lang}...`);

    const params = {
      lang: lang,
      c1_name: profiles.c1_name,
      c1_gender: profiles.c1_gender,
      c1_personality: profiles.c1_personality || 'brave',
      c1_spirit: profiles.c1_spirit || 'Dragon',
      c1_toy: profiles.c1_toy || 'Bruno',
      c2_name: profiles.c2_name,
      c2_gender: profiles.c2_gender,
      c2_personality: profiles.c2_personality || 'wise',
      c2_spirit: profiles.c2_spirit || 'Owl',
      c2_toy: profiles.c2_toy || 'Book'
    };

    websocketService.connect(params)
      .then(() => {
        console.log('✅ Connected to TwinSpark AI Engine');
        session.setConnected(true);
        session.setConnectionState('CONNECTED');
        playSuccess();
      })
      .catch((error) => {
        console.error('❌ Connection failed:', error);
        session.setError('Failed to connect to AI engine');
        playError();
      });

    // Subscribe to WebSocket events
    const unsubscribeConnected = websocketService.on('connected', () => {
      session.setConnected(true);
      session.setConnectionState('CONNECTED');
      playSuccess();
    });

    const unsubscribeDisconnected = websocketService.on('disconnected', ({ code, reason }) => {
      console.log('❌ Disconnected:', code, reason);
      session.setConnected(false);
      session.setConnectionState('DISCONNECTED');

      if (code === 1006 && setup.currentStep === 'story') {
        session.setReconnecting(true, 1);
        setTimeout(() => connectToAI(lang, profiles), 3000);
      }
    });

    const unsubscribeAsset = websocketService.on('CREATIVE_ASSET', (data) => {
      console.log(`🎨 Asset received: ${data.media_type}`, data);
      
      const metadata = {
        child: data.metadata?.child,
        type: data.media_type
      };

      story.addAsset(data.media_type, data.content, metadata);
    });

    const unsubscribeComplete = websocketService.on('STORY_COMPLETE', () => {
      console.log('✅ STORY_COMPLETE received!');
      
      setTimeout(() => {
        const assets = story.currentAssets;
        const profiles = setup.getProfiles();

        const newBeat = {
          narration: assets.narration || "The adventure begins...",
          child1_perspective: assets.child1_perspective || 
            `${profiles.c1_name} sees something magical...`,
          child2_perspective: assets.child2_perspective || 
            `${profiles.c2_name} feels excited...`,
          scene_image_url: assets.image,
          choices: assets.choices.length > 0 
            ? assets.choices 
            : ["Continue the adventure"]
        };

        console.log('🎬 Setting storyBeat:', newBeat);
        story.setCurrentBeat(newBeat);

        if (audio.ttsEnabled && newBeat.narration) {
          speak(newBeat.narration, setup.language);
        }

        story.reset();
      }, 100);
    });

    const unsubscribeStatus = websocketService.on('STATUS', (data) => {
      console.log('📊 Status:', data.message);
      story.setGenerating(data.message.includes('Generating'));
    });

    const unsubscribeMechanic = websocketService.on('MECHANIC_WARNING', (data) => {
      console.log('⚠️ Mechanic:', data);
      setMechanics(data);
    });

    const unsubscribeError = websocketService.on('error', ({ error }) => {
      console.error('❌ WebSocket error:', error);
      session.setError('Connection error occurred');
      playError();
    });

    // Sibling dynamics: update store when story_segment includes sibling data
    const unsubscribeSiblingData = websocketService.on('story_segment', (data) => {
      if (data?.narrative_directives) {
        const dirs = data.narrative_directives;
        if (dirs.child_roles) {
          sibling.setChildRoles(dirs.child_roles);
        }
        if (dirs.waiting_for_child) {
          sibling.setWaitingForChild(dirs.waiting_for_child);
        }
      }
    });

    unsubscribers.current = [
      unsubscribeConnected,
      unsubscribeDisconnected,
      unsubscribeAsset,
      unsubscribeComplete,
      unsubscribeStatus,
      unsubscribeMechanic,
      unsubscribeError,
      unsubscribeSiblingData
    ];
  };

  // ===========================================
  // EVENT HANDLERS
  // ===========================================

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

    const enrichedProfiles = {
      c1_name: profiles.c1_name || "Child 1",
      c1_gender: profiles.c1_gender || "girl",
      c1_personality: spiritToPersonality[profiles.c1_spirit_animal?.toLowerCase()] || 'brave',
      c1_spirit: profiles.c1_spirit_animal || 'Dragon',
      c1_toy: profiles.c1_toy_name || 'Bruno',
      c2_name: profiles.c2_name || "Child 2",
      c2_gender: profiles.c2_gender || "boy",
      c2_personality: spiritToPersonality[profiles.c2_spirit_animal?.toLowerCase()] || 'wise',
      c2_spirit: profiles.c2_spirit_animal || 'Owl',
      c2_toy: profiles.c2_toy_name || 'Book'
    };

    console.log("🔌 Enriched profiles:", enrichedProfiles);

    setup.setChild1({
      name: enrichedProfiles.c1_name,
      gender: enrichedProfiles.c1_gender,
      personality: enrichedProfiles.c1_personality,
      spirit: enrichedProfiles.c1_spirit,
      toy: enrichedProfiles.c1_toy
    });

    setup.setChild2({
      name: enrichedProfiles.c2_name,
      gender: enrichedProfiles.c2_gender,
      personality: enrichedProfiles.c2_personality,
      spirit: enrichedProfiles.c2_spirit,
      toy: enrichedProfiles.c2_toy
    });

    setup.completeSetup();
    session.setProfiles(enrichedProfiles);
    connectToAI(setup.language, enrichedProfiles);
  };

  const handleChoice = async (choiceText) => {
    console.log("🎯 Choice selected:", choiceText);
    
    if (!websocketService.isConnected()) {
      console.error("❌ WebSocket not connected");
      setAlertMessage("Connection lost. Please refresh the page.");
      playError();
      return;
    }

    try {
      playChoice();
      story.setCurrentBeat(null);
      story.setGenerating(true);
      
      const success = websocketService.send({
        type: "MAKE_CHOICE",
        choice: choiceText
      });

      if (!success) {
        throw new Error('Failed to send choice');
      }

      console.log("📤 Choice sent successfully");
      
    } catch (error) {
      console.error("❌ Error sending choice:", error);
      setAlertMessage("Failed to send your choice. Please try again.");
      playError();
      story.setGenerating(false);
    }
  };

  const handleSaveAndExit = async () => {
    setIsSaving(true);
    try {
      // End sibling session to get dynamics score + summary
      if (session.profiles?.c1_name && session.profiles?.c2_name) {
        try {
          const endResp = await fetch(`http://localhost:8000/api/sessions/${session.sessionId || 'current'}/end`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              characters: {
                child1: { name: session.profiles.c1_name },
                child2: { name: session.profiles.c2_name },
              }
            })
          });
          if (endResp.ok) {
            const result = await endResp.json();
            sibling.setSiblingScore(result.sibling_dynamics_score);
            sibling.setSessionSummary(result.summary);
            if (result.suggestion) sibling.setParentSuggestion(result.suggestion);
          }
        } catch (err) {
          console.error("Failed to end sibling session:", err);
        }
      }

      await fetch('http://localhost:8000/api/session/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          profiles: session.profiles,
          last_beat: story.currentBeat,
          language: setup.language
        })
      });
      playSuccess();
    } catch (err) {
      console.error("Failed to save session:", err);
      playError();
    } finally {
      setIsSaving(false);
      websocketService.disconnect();
      stopCapture();
      setShowExitModal(false);
      setup.reset();
      story.reset();
      session.reset();
      sibling.reset();
    }
  };

  const handleExitWithoutSaving = () => {
    websocketService.disconnect();
    stopCapture();
    setShowExitModal(false);
    setup.reset();
    story.reset();
    session.reset();
    sibling.reset();
  };

  const handlePrivacyAccept = () => {
    setup.acceptPrivacy();
    playSuccess();
  };

  // ===========================================
  // LIFECYCLE
  // ===========================================

  // Start multimodal capture after privacy consent + session connected
  useEffect(() => {
    if (setup.isComplete && session.connected) {
      startCapture(true);
    }
  }, [setup.isComplete, session.connected, startCapture]);

  // Reset child response tracking when a new story beat arrives
  useEffect(() => {
    if (story.currentBeat) {
      setChild1Responded(false);
      setChild2Responded(false);
    }
  }, [story.currentBeat]);

  useEffect(() => {
    return () => {
      unsubscribers.current.forEach(unsubscribe => unsubscribe());
      unsubscribers.current = [];
      websocketService.disconnect();
      stopCapture();
      stopSpeech();
    };
  }, [stopSpeech, stopCapture]);

  // ===========================================
  // RENDER
  // ===========================================

  return (
    <AppContainer>
      {/* Settings button */}
      {!showDashboard && (
        <button
          className="settings-btn"
          onClick={() => setShowDashboard(true)}
          title="Parent Dashboard"
        >
          <Settings size={24} />
        </button>
      )}

      {/* Parent Dashboard */}
      {showDashboard && (
        <ParentDashboard onBack={() => setShowDashboard(false)} />
      )}

      {/* Sibling Dynamics — collapsible parent insights */}
      {setup.isComplete && (
        <div style={{ position: 'absolute', top: '60px', right: '20px', zIndex: 99, width: '300px' }}>
          <SiblingDashboard />
        </div>
      )}

      {/* ─── Privacy Modal ─────────────────────────── */}
      {!setup.privacyAccepted && (
        <PrivacyModal onAccept={handlePrivacyAccept} t={t} />
      )}

      {/* ─── After Privacy ─────────────────────────── */}
      {setup.privacyAccepted && (
        <>
          {/* Title */}
          <h1 className="app-title text-gradient logo-animation">
            TwinSpark Chronicles
          </h1>

          {/* Language Selection */}
          {setup.currentStep === 'language' && (
            <LanguageSelector onSelect={handleLanguageSelect} />
          )}

          {/* Character Setup */}
          {setup.currentStep === 'characters' && (
            <CharacterSetup
              onComplete={handleSetupComplete}
              language={setup.language}
              t={t}
            />
          )}

          {/* ─── Story Experience ───────────────────── */}
          {setup.isComplete && (
            <React.Fragment>
              {/* Mode toggle */}
              <div className="mode-toggle">
                <button
                  className={`mode-toggle__btn ${!voiceOnlyMode ? 'mode-toggle__btn--active' : ''}`}
                  onClick={() => setVoiceOnlyMode(false)}
                >
                  <Eye size={18} /> Full Story
                </button>
                <button
                  className={`mode-toggle__btn ${voiceOnlyMode ? 'mode-toggle__btn--active' : ''}`}
                  onClick={() => setVoiceOnlyMode(true)}
                >
                  <Mic size={18} /> Voice Only
                </button>
              </div>

              {/* Connection Status */}
              <SessionStatus t={t} />

              {voiceOnlyMode ? (
                <VoiceOnlyMode
                  onVoiceInput={() => setIsListening(!isListening)}
                  isListening={isListening}
                  currentStory={story.currentBeat?.child1_perspective}
                  childName={session.profiles?.c1_name}
                  t={t}
                />
              ) : (
                <div className="story-stage">
                  {/* Sibling turn indicator */}
                  {story.currentBeat && session.profiles?.c1_name && session.profiles?.c2_name && (
                    <DualPrompt
                      child1Name={session.profiles.c1_name}
                      child2Name={session.profiles.c2_name}
                      promptText={story.currentBeat?.narration}
                      child1Responded={child1Responded}
                      child2Responded={child2Responded}
                      onRespond={(childId) => {
                        if (childId === 'child1') setChild1Responded(true);
                        if (childId === 'child2') setChild2Responded(true);
                      }}
                    />
                  )}

                  {/* Story display or loading */}
                  {story.currentBeat ? (
                    <DualStoryDisplay
                      storyBeat={story.currentBeat}
                      t={t}
                      profiles={session.profiles}
                      onChoice={handleChoice}
                    />
                  ) : (
                    <div className="glass-panel story-waiting">
                      <LoadingAnimation
                        type="story"
                        message={story.isGenerating
                          ? "Creating your next adventure…"
                          : (t.waiting || "Waiting for the story to begin…")}
                      />
                    </div>
                  )}

                  {/* Mechanic overlay */}
                  {mechanics && story.currentBeat && (
                    <div className="glass-panel mechanic-overlay">
                      <p className="mechanic-overlay__text">{mechanics.prompt}</p>
                    </div>
                  )}

                  {/* Mic bar */}
                  <div className="mic-bar">
                    <ChildFriendlyButton
                      onClick={() => setIsListening(!isListening)}
                      variant={isListening ? 'danger' : 'success'}
                      icon={<Mic size={28} color="white" strokeWidth={2.5} />}
                    >
                      {isListening
                        ? (t.releaseToStop || "Recording…")
                        : (t.pushToTalk || "Push to Talk 🎤")}
                    </ChildFriendlyButton>

                    <MultimodalControls
                      isListening={isListening}
                      hasCamera={hasCamera}
                      t={t}
                    />
                  </div>

                  <MagicMirror />
                  <CameraPreview />
                  <MultimodalFeedback />
                </div>
              )}
            </React.Fragment>
          )}
        </>
      )}

      {/* ─── Modals ────────────────────────────────── */}
      <AlertModal
        message={alertMessage}
        onClose={() => setAlertMessage(null)}
      />

      {FeedbackComponent}

      {showExitModal && (
        <ExitModal
          onSave={handleSaveAndExit}
          onExit={handleExitWithoutSaving}
          onClose={() => setShowExitModal(false)}
          isSaving={isSaving}
        />
      )}
    </AppContainer>
  );
}

export default App;