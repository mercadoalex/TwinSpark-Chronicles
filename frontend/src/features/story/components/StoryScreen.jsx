import React, { useEffect, useRef, useCallback } from 'react';

// New interaction model components
import NarrationView from './NarrationView';
import TurnIndicator from './TurnIndicator';
import VoiceInputController from './VoiceInputController';
import SuggestionCards from './SuggestionCards';
import CelebrationAnimator from './CelebrationAnimator';
import ThemePicker from './ThemePicker';
import WelcomeBack from './WelcomeBack';

// Stores & hooks
import { useStoryLoopStore } from '../../../stores/storyLoopStore';
import { useSessionContinuity } from '../hooks/useSessionContinuity';
import { useStoryTTS } from '../hooks/useStoryTTS';
import { useSetupStore } from '../../../stores/setupStore';

// TTS service for card long-press
import { ttsService } from '../../audio/services/ttsService';

/**
 * StoryScreen — Main story experience using the new voice-first interaction model.
 *
 * Integrates:
 * - storyLoopStore as the central state machine
 * - useSessionContinuity for session persistence (auto-resume or theme picker)
 * - useStoryTTS for narration reading with sentence highlighting
 * - WebSocket connection for real-time story beat communication
 *
 * Layout (portrait, vertical stacking):
 * - TurnIndicator at top (visible during awaiting_input/recording)
 * - NarrationView with scene + text + controls slot
 * - Inside controls slot: VoiceInputController + SuggestionCards
 * - CelebrationAnimator for milestones and processing
 *
 * Requirements: 10.4, 11.1, 11.2, 11.3, 11.4
 */
export default function StoryScreen() {
  // Story loop state machine
  const phase = useStoryLoopStore((s) => s.phase);
  const activeTwin = useStoryLoopStore((s) => s.activeTwin);
  const currentBeat = useStoryLoopStore((s) => s.currentBeat);
  const suggestions = useStoryLoopStore((s) => s.suggestions);
  const highlightedSentence = useStoryLoopStore((s) => s.highlightedSentence);
  const isRecording = useStoryLoopStore((s) => s.isRecording);

  // Story loop actions
  const submitVoiceInput = useStoryLoopStore((s) => s.submitVoiceInput);
  const submitCardSelection = useStoryLoopStore((s) => s.submitCardSelection);
  const onTTSComplete = useStoryLoopStore((s) => s.onTTSComplete);
  const startRecording = useStoryLoopStore((s) => s.startRecording);
  const cancelRecording = useStoryLoopStore((s) => s.cancelRecording);
  const receiveBeat = useStoryLoopStore((s) => s.receiveBeat);
  const setHighlightedSentence = useStoryLoopStore((s) => s.setHighlightedSentence);
  const setError = useStoryLoopStore((s) => s.setError);

  // Session continuity
  const {
    hasSession,
    sessionData,
    isResuming,
    showWelcomeBack,
    startNewSession,
    saveSession,
    onWelcomeBackComplete,
  } = useSessionContinuity();

  // Setup store for twin names
  const setup = useSetupStore();

  // WebSocket ref
  const wsRef = useRef(null);
  const reconnectTimerRef = useRef(null);

  // Build twin config from setup store or session data
  const twinConfig = sessionData?.twinConfig || {
    twin1: {
      id: 'twin1',
      name: setup.child1?.name || 'Twin 1',
      avatar: '🦊',
      color: '#FF6B6B',
    },
    twin2: {
      id: 'twin2',
      name: setup.child2?.name || 'Twin 2',
      avatar: '🦄',
      color: '#6B9FFF',
    },
  };

  const activeTwinConfig = twinConfig[activeTwin] || twinConfig.twin1;

  // --- TTS Integration ---
  const { isSpeaking, isPaused, pause, resume } = useStoryTTS({
    narration: currentBeat?.narration || '',
    onComplete: onTTSComplete,
    onSentenceChange: setHighlightedSentence,
  });

  // --- WebSocket Connection ---
  const connectWebSocket = useCallback(() => {
    if (!sessionData?.sessionId) return;

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = 'localhost:8000'; // Backend server
    const wsUrl = `${protocol}//${host}/ws/story-loop/${sessionData.sessionId}`;

    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('🔌 Story loop WebSocket connected');
        // Send start_session to trigger the opening story beat
        ws.send(JSON.stringify({
          type: 'start_session',
          theme: sessionData?.theme || 'a magical adventure',
          twin_names: {
            twin1: twinConfig.twin1?.name || 'Twin 1',
            twin2: twinConfig.twin2?.name || 'Twin 2',
          },
        }));
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          handleWebSocketMessage(message);
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err);
        }
      };

      ws.onerror = (err) => {
        console.error('WebSocket error:', err);
      };

      ws.onclose = () => {
        console.log('🔌 Story loop WebSocket disconnected');
        // Attempt reconnect after 3 seconds
        reconnectTimerRef.current = setTimeout(() => {
          if (sessionData?.sessionId) {
            connectWebSocket();
          }
        }, 3000);
      };
    } catch (err) {
      console.error('Failed to connect WebSocket:', err);
    }
  }, [sessionData?.sessionId]); // eslint-disable-line react-hooks/exhaustive-deps

  /**
   * Handle incoming WebSocket messages.
   */
  const handleWebSocketMessage = useCallback((message) => {
    switch (message.type) {
      case 'story_beat':
        // Receive a new story beat from the backend
        receiveBeat({
          narration: message.narration,
          illustrationUrl: message.illustration_url,
          suggestions: (message.suggestions || []).map((s) => ({
            id: s.id,
            label: s.label,
            illustrationUrl: s.illustration_url,
            storyDirection: s.story_direction,
          })),
          perspective: message.perspective,
          isMilestone: message.is_milestone || false,
        });
        // Persist session state
        saveSession({
          activeTwin: useStoryLoopStore.getState().activeTwin,
          turnCount: useStoryLoopStore.getState().turnCount,
        });
        break;

      case 'transcript_result':
        // Voice transcript received — submit to story loop
        if (message.confidence >= 0.4 && message.text) {
          submitVoiceInput(message.text);
        }
        break;

      case 'transcript_error':
        // Transcript failed — show error in voice controller
        // The VoiceInputController handles its own error state
        cancelRecording();
        break;

      default:
        break;
    }
  }, [receiveBeat, submitVoiceInput, cancelRecording, saveSession]);

  // Connect WebSocket when session is active and not resuming
  useEffect(() => {
    if (hasSession && sessionData?.sessionId && !isResuming) {
      connectWebSocket();
    }

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
      }
    };
  }, [hasSession, sessionData?.sessionId, isResuming, connectWebSocket]);

  // --- Send messages to backend ---

  /**
   * Send voice input audio data to backend via WebSocket.
   * In the current implementation, the VoiceInputController handles recording
   * and we send the transcript text. In production, raw audio would be sent.
   */
  const sendVoiceInput = useCallback((transcript) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'voice_input',
        text: transcript,
        active_twin: activeTwin,
        session_id: sessionData?.sessionId,
      }));
    }
    submitVoiceInput(transcript);
  }, [activeTwin, sessionData?.sessionId, submitVoiceInput]);

  /**
   * Send card selection to backend via WebSocket.
   */
  const sendCardSelection = useCallback((cardId) => {
    const card = suggestions.find((c) => c.id === cardId);
    if (!card) return;

    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'card_selection',
        card_id: cardId,
        story_direction: card.storyDirection,
        active_twin: activeTwin,
        session_id: sessionData?.sessionId,
      }));
    }
    submitCardSelection(cardId);
  }, [activeTwin, sessionData?.sessionId, suggestions, submitCardSelection]);

  // --- Event Handlers ---

  const handleThemeSelect = useCallback((themeId) => {
    startNewSession(themeId, twinConfig);
  }, [startNewSession, twinConfig]);

  const handleCardLongPress = useCallback((cardId) => {
    const card = suggestions.find((c) => c.id === cardId);
    if (card) {
      ttsService.speak(card.label, 'en', { rate: 0.9, pitch: 1.1 });
    }
  }, [suggestions]);

  const handleRecordingStart = useCallback(() => {
    startRecording();
  }, [startRecording]);

  const handleRecordingEnd = useCallback(() => {
    // Recording ended — VoiceInputController handles the transition
  }, []);

  const handleNarrationTap = useCallback(() => {
    if (isSpeaking && !isPaused) {
      pause();
    } else if (isPaused) {
      resume();
    }
  }, [isSpeaking, isPaused, pause, resume]);

  // --- Render ---

  // Show WelcomeBack animation during session resume
  if (showWelcomeBack) {
    return (
      <WelcomeBack
        twinConfig={twinConfig}
        onComplete={onWelcomeBackComplete}
      />
    );
  }

  // Show ThemePicker when no active session
  if (!hasSession) {
    return <ThemePicker onSelect={handleThemeSelect} />;
  }

  // Main story loop
  const isInputPhase = phase === 'awaiting_input' || phase === 'recording';

  return (
    <div className="story-screen" aria-label="Story experience">
      {/* Turn Indicator — top of screen, visible during input phases */}
      <TurnIndicator
        activeTwin={activeTwinConfig}
        isVisible={isInputPhase}
      />

      {/* Narration View — scene + text + controls */}
      <NarrationView
        beat={currentBeat}
        highlightedSentence={highlightedSentence}
        activeTwinAvatar={activeTwinConfig.avatar}
        activeTwinColor={activeTwinConfig.color}
      >
        {/* Controls slot: Voice Input + Suggestion Cards */}
        <div className="story-screen__controls" onClick={handleNarrationTap}>
          <VoiceInputController
            isActive={phase === 'awaiting_input'}
            activeTwinColor={activeTwinConfig.color}
            onTranscript={sendVoiceInput}
            onRecordingStart={handleRecordingStart}
            onRecordingEnd={handleRecordingEnd}
          />
          <SuggestionCards
            cards={suggestions}
            isActive={phase === 'awaiting_input'}
            onCardTap={sendCardSelection}
            onCardLongPress={handleCardLongPress}
          />
        </div>
      </NarrationView>

      {/* Celebration Animator — milestones + processing */}
      <CelebrationAnimator
        isMilestone={currentBeat?.isMilestone || false}
        isProcessing={phase === 'processing'}
      />
    </div>
  );
}
