import React, { useEffect, useRef, useMemo } from 'react';
import { Mic, Settings, Map } from 'lucide-react';
import { translations } from './locales';

// ==========================================
// FEATURE COMPONENTS
// ==========================================

// Setup Feature
import { 
  PrivacyModal, 
  LanguageSelector, 
  CharacterSetup,
  ParentDashboard,
  ParentApprovalScreen 
} from './features/setup';

// Story Feature
import { DualStoryDisplay } from './features/story';

// Camera / Multimodal Feature
import CameraPreview from './features/camera/components/CameraPreview.jsx';
import MultimodalFeedback from './features/camera/components/MultimodalFeedback.jsx';

// Session Feature
import { SessionStatus, MagicMirror, ContinueScreen } from './features/session';

// ==========================================
// SHARED COMPONENTS
// ==========================================

import {
  AlertModal,
  ExitModal,
  LoadingAnimation,
  useFeedback,
  AppContainer,
  SkipLink
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
import ParentControls from './components/ParentControls.jsx';
import SessionTimer from './components/SessionTimer.jsx';
import EmergencyStop from './components/EmergencyStop.jsx';

// World Feature
import WorldMapView from './features/world/components/WorldMapView.jsx';

// ==========================================
// STORES
// ==========================================

import { useSessionStore } from './stores/sessionStore';
import { useStoryStore } from './stores/storyStore';
import { useAudioStore } from './stores/audioStore';
import { useSetupStore } from './stores/setupStore';
import { useSiblingStore } from './stores/siblingStore';
import { useParentControlsStore } from './stores/parentControlsStore';
import { useSessionPersistenceStore } from './stores/sessionPersistenceStore';

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
  const parentControls = useParentControlsStore();
  const persistence = useSessionPersistenceStore();

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
  const [showExitModal, setShowExitModal] = React.useState(false);
  const [isSaving, setIsSaving] = React.useState(false);
  const [alertMessage, setAlertMessage] = React.useState(null);
  const [showDashboard, setShowDashboard] = React.useState(false);
  const [showParentControls, setShowParentControls] = React.useState(false);
  const [showWorldMap, setShowWorldMap] = React.useState(false);
  const [showPhotoReview, setShowPhotoReview] = React.useState(false);
  const [mechanics, setMechanics] = React.useState(null);
  const [child1Responded, setChild1Responded] = React.useState(false);
  const [child2Responded, setChild2Responded] = React.useState(false);

  const unsubscribers = useRef([]);
  const mainRef = useRef(null);
  const prevSetupComplete = useRef(false);
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
      // Sync localStorage snapshot to server on reconnect
      useSessionPersistenceStore.getState().syncLocalToServer();
    });

    const unsubscribeDisconnected = websocketService.on('disconnected', ({ code, reason }) => {
      console.log('❌ Disconnected:', code, reason);
      session.setConnected(false);
      session.setConnectionState('DISCONNECTED');

      // Save to localStorage on disconnect
      useSessionPersistenceStore.getState().saveToLocalStorage();

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
        c1_toy: restoredSetup.child1.toy,
        c2_name: restoredSetup.child2.name,
        c2_gender: restoredSetup.child2.gender,
        c2_personality: restoredSetup.child2.personality,
        c2_spirit: restoredSetup.child2.spirit,
        c2_toy: restoredSetup.child2.toy,
      };

      session.setProfiles(restoredProfiles);
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

      // Save session snapshot via persistence store
      await persistence.saveSnapshot();
      playSuccess();
    } catch (err) {
      console.error("Failed to save session:", err);
      playError();
    } finally {
      setIsSaving(false);
      websocketService.disconnect();
      stopCapture();
      setShowExitModal(false);
      localStorage.removeItem('twinspark_session_snapshot');
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
    localStorage.removeItem('twinspark_session_snapshot');
    setup.reset();
    story.reset();
    session.reset();
    sibling.reset();
  };

  const handlePrivacyAccept = () => {
    setup.acceptPrivacy();
    playSuccess();
  };

  const handleEmergencyExit = () => {
    websocketService.disconnect();
    stopCapture();
    localStorage.removeItem('twinspark_session_snapshot');
    setup.reset();
    story.reset();
    session.reset();
    sibling.reset();
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

  // Auto-save on story beat completion
  useEffect(() => {
    if (story.history.length > 0 && setup.isComplete) {
      persistence.saveSnapshot();
    }
  }, [story.history.length]);

  // Delete session snapshot when story naturally completes
  useEffect(() => {
    if (story.isComplete && session.profiles?.c1_name && session.profiles?.c2_name) {
      const siblingPairId = [session.profiles.c1_name, session.profiles.c2_name].sort().join(':');
      persistence.deleteSession(siblingPairId);
      localStorage.removeItem('twinspark_session_snapshot');
    }
  }, [story.isComplete]);

  // beforeunload — fire-and-forget save via Beacon API
  useEffect(() => {
    const handleBeforeUnload = () => {
      if (!setup.isComplete) return;

      const setupState = useSetupStore.getState();
      const storyState = useStoryStore.getState();
      const siblingPairId = [setupState.child1.name, setupState.child2.name].sort().join(':');

      const payload = {
        sibling_pair_id: siblingPairId,
        character_profiles: {
          c1_name: setupState.child1.name, c1_gender: setupState.child1.gender,
          c1_personality: setupState.child1.personality, c1_spirit: setupState.child1.spirit,
          c1_toy: setupState.child1.toy,
          c2_name: setupState.child2.name, c2_gender: setupState.child2.gender,
          c2_personality: setupState.child2.personality, c2_spirit: setupState.child2.spirit,
          c2_toy: setupState.child2.toy,
        },
        story_history: storyState.history,
        current_beat: storyState.currentBeat || null,
        session_metadata: {
          language: setupState.language,
          story_beat_count: storyState.history.length,
          last_choice_made: storyState.history.length > 0 ? storyState.history[storyState.history.length - 1].choiceMade : null,
          session_duration_seconds: 0,
        },
      };

      navigator.sendBeacon(
        'http://localhost:8000/api/session/save',
        new Blob([JSON.stringify(payload)], { type: 'application/json' })
      );
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [setup.isComplete]);

  // visibilitychange — save when tab goes hidden
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.hidden && setup.isComplete) {
        persistence.saveSnapshot();
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
  }, [setup.isComplete]);

  // ===========================================
  // ACCESSIBILITY: Focus management on setup → story transition (Req 9.2)
  // ===========================================

  useEffect(() => {
    if (setup.isComplete && !prevSetupComplete.current) {
      // Transition from setup to story — focus the main content area
      setTimeout(() => {
        if (mainRef.current) {
          mainRef.current.focus();
        }
      }, 100);
    }
    prevSetupComplete.current = setup.isComplete;
  }, [setup.isComplete]);

  // Compute whether any modal is open for aria-hidden on background content
  const isAnyModalOpen = Boolean(
    alertMessage || showExitModal || (!setup.privacyAccepted)
  );

  // ===========================================
  // RENDER
  // ===========================================

  return (
    <AppContainer>
      {/* Skip navigation link — first focusable element (Req 12.1) */}
      <SkipLink />

      {/* Main app content — hidden from assistive tech when modals are open (Req 2.5) */}
      <div aria-hidden={isAnyModalOpen || undefined}>
        {/* Settings button — parent only */}
        {!showDashboard && (
          <div style={{ position: 'absolute', top: '20px', right: '20px', zIndex: 100, display: 'flex', gap: '8px' }}>
            {setup.isComplete && (
              <button
                className="settings-btn"
                onClick={() => setShowWorldMap(true)}
                title="My World"
                style={{ position: 'static' }}
              >
                <Map size={20} />
              </button>
            )}
            {setup.isComplete && (
              <button
                className="settings-btn"
                onClick={() => setShowParentControls(true)}
                title="Parent Controls"
                style={{ position: 'static' }}
              >
                <Settings size={20} />
              </button>
            )}
            <button
              className="settings-btn"
              onClick={() => setShowDashboard(true)}
              title="Parent Dashboard"
              style={{ position: 'static' }}
            >
              <Settings size={24} />
            </button>
          </div>
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

        {/* Parent Controls modal */}
        {showParentControls && (
          <ParentControls
            onClose={() => setShowParentControls(false)}
            onReviewPhotos={() => {
              setShowParentControls(false);
              setShowPhotoReview(true);
            }}
          />
        )}

        {/* Photo Review overlay */}
        {showPhotoReview && (
          <ParentApprovalScreen
            siblingPairId={
              session.profiles?.c1_name && session.profiles?.c2_name
                ? [session.profiles.c1_name, session.profiles.c2_name].sort().join(':')
                : ''
            }
            onComplete={() => setShowPhotoReview(false)}
          />
        )}

        {/* World Map overlay */}
        {showWorldMap && (
          <WorldMapView
            siblingPairId={
              session.profiles?.c1_name && session.profiles?.c2_name
                ? [session.profiles.c1_name, session.profiles.c2_name].sort().join(':')
                : ''
            }
            onClose={() => setShowWorldMap(false)}
          />
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
            <CharacterSetup
              onComplete={handleSetupComplete}
              language={setup.language}
              t={t}
            />
          )}

          {/* ─── Story Experience — always multimodal ── */}
          {setup.isComplete && (
            <main id="main-content" ref={mainRef} className="story-stage" aria-label="Story experience" tabIndex={-1}>
              {/* Session controls (Req 1.5) */}
              <nav aria-label="Session controls">
                {/* Connection Status */}
                <SessionStatus t={t} />

                {/* Session Timer & Emergency Stop */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                  <SessionTimer onTimeUp={handleEmergencyExit} />
                </div>
                <EmergencyStop
                  sessionId={session.sessionId || 'current'}
                  onStop={handleEmergencyExit}
                />
              </nav>

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

              {/* Floating mic button — always visible */}
              <button
                className={`floating-mic ${isListening ? 'floating-mic--active' : ''}`}
                onClick={() => setIsListening(!isListening)}
                aria-label={isListening ? 'Stop recording' : 'Start recording'}
              >
                <Mic size={32} color="white" strokeWidth={2.5} />
              </button>

              <MagicMirror />
              <CameraPreview />
              <MultimodalFeedback />

              {/* Save error warning — child-friendly icon, no text */}
              {persistence.saveStatus === 'error' && (
                <div style={{
                  position: 'fixed', bottom: '20px', left: '20px', zIndex: 200,
                  width: '48px', height: '48px', borderRadius: '50%',
                  background: 'rgba(255,165,0,0.2)', display: 'flex',
                  alignItems: 'center', justifyContent: 'center',
                  animation: 'pulse 2s ease-in-out infinite',
                }} title="Save issue">
                  <span style={{ fontSize: '24px' }} aria-hidden="true">☁️</span>
                </div>
              )}
            </main>
          )}
        </>
      )}
      </div>{/* end aria-hidden wrapper */}

      {/* ─── Modals (outside aria-hidden wrapper) ──── */}
      {!setup.privacyAccepted && (
        <PrivacyModal onAccept={handlePrivacyAccept} t={t} />
      )}

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