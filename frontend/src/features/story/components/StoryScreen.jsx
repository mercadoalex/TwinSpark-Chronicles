import React, { useEffect, useRef } from 'react';
import { Mic, Settings, Map } from 'lucide-react';

// Feature components
import { ParentDashboard, ParentApprovalScreen } from '../../setup';
import TransitionEngine from './TransitionEngine';
import { DrawingCanvas } from '../../drawing';
import { SessionStatus, MagicMirror } from '../../session';
import { useStoryConnection } from '../../session';
import CameraPreview from '../../camera/components/CameraPreview.jsx';
import MultimodalFeedback from '../../camera/components/MultimodalFeedback.jsx';

// Shared components
import {
  AlertModal,
  ExitModal,
  LoadingAnimation,
  useFeedback,
  StoryErrorBoundary,
  DrawingErrorBoundary,
  CameraErrorBoundary,
} from '../../../shared/components';

// Sibling dynamics components
import SiblingDashboard from '../../../components/SiblingDashboard.jsx';
import DualPrompt from '../../../components/DualPrompt.jsx';
import ParentControls from '../../../components/ParentControls.jsx';
import SessionTimer from '../../../components/SessionTimer.jsx';
import EmergencyStop from '../../../components/EmergencyStop.jsx';

// World & Gallery
import WorldMapView from '../../world/components/WorldMapView.jsx';
import { GalleryView } from '../../gallery';

// Stores
import { useSessionStore } from '../../../stores/sessionStore';
import { useStoryStore } from '../../../stores/storyStore';
import { useAudioStore } from '../../../stores/audioStore';
import { useSetupStore } from '../../../stores/setupStore';
import { useSiblingStore } from '../../../stores/siblingStore';
import { useParentControlsStore } from '../../../stores/parentControlsStore';
import { useSessionPersistenceStore } from '../../../stores/sessionPersistenceStore';
import { useSceneAudioStore } from '../../../stores/sceneAudioStore';
import { useGalleryStore } from '../../../stores/galleryStore';
import { useDrawingStore } from '../../../stores/drawingStore';

// Hooks
import { useAudioFeedback } from '../../audio/hooks/useAudioFeedback';
import { useMultimodalInput } from '../../camera/hooks/useMultimodalInput.js';
import { websocketService } from '../../session/services/websocketService';

export default function StoryScreen({ t, onAlert, onVoiceCommand }) {
  // Stores
  const session = useSessionStore();
  const story = useStoryStore();
  const audio = useAudioStore();
  const setup = useSetupStore();
  const sibling = useSiblingStore();
  const persistence = useSessionPersistenceStore();
  const drawingStore = useDrawingStore();

  // Hooks
  const { playSuccess, playError, playChoice } = useAudioFeedback();
  const { startCapture, stopCapture } = useMultimodalInput();
  const { showFeedback, FeedbackComponent } = useFeedback();

  // Local state
  const [isListening, setIsListening] = React.useState(true);
  const [hasCamera, setHasCamera] = React.useState(true);
  const [showExitModal, setShowExitModal] = React.useState(false);
  const [isSaving, setIsSaving] = React.useState(false);
  const [showDashboard, setShowDashboard] = React.useState(false);
  const [showParentControls, setShowParentControls] = React.useState(false);
  const [showWorldMap, setShowWorldMap] = React.useState(false);
  const [showGallery, setShowGallery] = React.useState(false);
  const [showPhotoReview, setShowPhotoReview] = React.useState(false);
  const [mechanics, setMechanics] = React.useState(null);
  const [child1Responded, setChild1Responded] = React.useState(false);
  const [child2Responded, setChild2Responded] = React.useState(false);
  const [audioUnlocked, setAudioUnlocked] = React.useState(false);
  const [archivedToGallery, setArchivedToGallery] = React.useState(false);

  // Refs
  const mainRef = useRef(null);
  const drawingTickRef = useRef(null);

  // WebSocket connection hook
  const { connectToAI, disconnect, unsubscribers } = useStoryConnection({
    onVoiceCommand,
    onMechanics: setMechanics,
  });

  // ===========================================
  // EVENT HANDLERS
  // ===========================================

  const handleChoice = async (choiceText) => {
    console.log("🎯 Choice selected:", choiceText);
    
    if (!websocketService.isConnected()) {
      console.error("❌ WebSocket not connected");
      if (onAlert) onAlert("Connection lost. Please refresh the page.");
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
      if (onAlert) onAlert("Failed to send your choice. Please try again.");
      playError();
      story.setGenerating(false);
    }
  };

  const handleDrawingComplete = (strokes) => {
    websocketService.send({
      type: 'DRAWING_COMPLETE',
      strokes,
    });
    useDrawingStore.getState().endSession();
  };

  const handleSaveAndExit = async () => {
    setIsSaving(true);
    let archived = false;
    try {
      // 1. Save session snapshot FIRST so backend has story data for archival
      try {
        await persistence.saveSnapshot();
      } catch (snapErr) {
        console.error("Failed to save snapshot (continuing to end session):", snapErr);
      }

      // 2. End sibling session to get dynamics score + summary + archival
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
            // 3. Check for archival confirmation
            if (result.storybook_id) {
              archived = true;
              setArchivedToGallery(true);
            }
          }
        } catch (err) {
          console.error("Failed to end sibling session:", err);
        }
      }

      playSuccess();

      // 4. If archived, show brief toast before reset
      if (archived) {
        showFeedback('sparkle', 'Saved to gallery ✨', 1500);
        await new Promise(resolve => setTimeout(resolve, 1500));
      }
    } catch (err) {
      console.error("Failed to save session:", err);
      playError();
    } finally {
      setIsSaving(false);
      setArchivedToGallery(false);
      websocketService.disconnect();
      stopCapture();
      setShowExitModal(false);
      localStorage.removeItem('twinspark_session_snapshot');
      setup.reset();
      story.reset();
      session.reset();
      sibling.reset();
      useSceneAudioStore.getState().reset();
      useGalleryStore.getState().reset();
      useDrawingStore.getState().reset();
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
    useSceneAudioStore.getState().reset();
    useGalleryStore.getState().reset();
    useDrawingStore.getState().reset();
  };

  const handleEmergencyExit = () => {
    websocketService.disconnect();
    stopCapture();
    localStorage.removeItem('twinspark_session_snapshot');
    setup.reset();
    story.reset();
    session.reset();
    sibling.reset();
    useSceneAudioStore.getState().reset();
    useGalleryStore.getState().reset();
    useDrawingStore.getState().reset();
  };

  const handleUnlockAudio = async () => {
    const sceneAudio = useSceneAudioStore.getState();
    sceneAudio.initAudio();
    await sceneAudio.unlockAudio();
    await sceneAudio.preloadAllSfx();
  };

  // ===========================================
  // LIFECYCLE
  // ===========================================

  // Start multimodal capture after setup complete + session connected
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

  // Track sceneAudioStore.audioUnlocked for the unlock prompt
  useEffect(() => {
    const unsub = useSceneAudioStore.subscribe(
      (state) => state.audioUnlocked,
      (unlocked) => setAudioUnlocked(unlocked)
    );
    return unsub;
  }, []);

  // Drawing session tick — decrement countdown every second while active
  useEffect(() => {
    if (drawingStore.isActive) {
      drawingTickRef.current = setInterval(() => {
        useDrawingStore.getState().tick();
      }, 1000);
    } else {
      if (drawingTickRef.current) {
        clearInterval(drawingTickRef.current);
        drawingTickRef.current = null;
      }
    }
    return () => {
      if (drawingTickRef.current) {
        clearInterval(drawingTickRef.current);
        drawingTickRef.current = null;
      }
    };
  }, [drawingStore.isActive]);

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
          c1_toy_type: setupState.child1.toyType,
          c1_toy_image: setupState.child1.toyImage,
          c2_name: setupState.child2.name, c2_gender: setupState.child2.gender,
          c2_personality: setupState.child2.personality, c2_spirit: setupState.child2.spirit,
          c2_toy: setupState.child2.toy,
          c2_toy_type: setupState.child2.toyType,
          c2_toy_image: setupState.child2.toyImage,
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

  // Accessibility: Focus management on mount
  useEffect(() => {
    setTimeout(() => {
      if (mainRef.current) {
        mainRef.current.focus();
      }
    }, 100);
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      unsubscribers.current.forEach(unsubscribe => unsubscribe());
      unsubscribers.current = [];
      websocketService.disconnect();
      stopCapture();
    };
  }, [stopCapture]);

  // ===========================================
  // RENDER
  // ===========================================

  return (
    <>
      {/* Settings buttons */}
      {!showDashboard && (
        <div style={{ position: 'absolute', top: '20px', right: '20px', zIndex: 100, display: 'flex', gap: '8px' }}>
          <button
            className="settings-btn"
            onClick={() => setShowGallery(true)}
            title="Story Gallery"
            style={{ position: 'static' }}
          >
            📚
          </button>
          <button
            className="settings-btn"
            onClick={() => setShowWorldMap(true)}
            title="My World"
            style={{ position: 'static' }}
          >
            <Map size={20} />
          </button>
          <button
            className="settings-btn"
            onClick={() => setShowParentControls(true)}
            title="Parent Controls"
            style={{ position: 'static' }}
          >
            <Settings size={20} />
          </button>
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
      <div style={{ position: 'absolute', top: '60px', right: '20px', zIndex: 99, width: '300px' }}>
        <SiblingDashboard />
      </div>

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

      {/* Gallery overlay */}
      {showGallery && (
        <GalleryView
          siblingPairId={
            session.profiles?.c1_name && session.profiles?.c2_name
              ? [session.profiles.c1_name, session.profiles.c2_name].sort().join(':')
              : ''
          }
          onClose={() => setShowGallery(false)}
        />
      )}

      {/* Story Experience main area */}
      <main id="main-content" ref={mainRef} className="story-stage" aria-label="Story experience" tabIndex={-1}>
        {/* Session controls */}
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
          <StoryErrorBoundary>
            <TransitionEngine
              storyBeat={story.currentBeat}
              t={t}
              profiles={session.profiles}
              onChoice={handleChoice}
            />
          </StoryErrorBoundary>
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

        {/* Audio unlock prompt */}
        {!audioUnlocked && (
          <button
            className="audio-unlock-btn"
            onClick={handleUnlockAudio}
            aria-label="Enable scene audio"
          >
            🔊 Tap to hear sounds
          </button>
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
        <CameraErrorBoundary>
          <CameraPreview />
          <MultimodalFeedback />
        </CameraErrorBoundary>

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

        {/* Drawing Canvas overlay */}
        {drawingStore.isActive && (
          <DrawingErrorBoundary>
            <DrawingCanvas
              prompt={drawingStore.prompt}
              duration={drawingStore.duration}
              siblingId="child1"
              profiles={session.profiles}
              onComplete={handleDrawingComplete}
            />
          </DrawingErrorBoundary>
        )}
      </main>

      {/* Exit Modal — tightly coupled to save/exit logic */}
      {showExitModal && (
        <ExitModal
          onSave={handleSaveAndExit}
          onExit={handleExitWithoutSaving}
          onClose={() => setShowExitModal(false)}
          isSaving={isSaving}
        />
      )}

      {FeedbackComponent}
    </>
  );
}
