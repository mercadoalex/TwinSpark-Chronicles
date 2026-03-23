import { useRef, useCallback } from 'react';
import { websocketService } from '../services/websocketService';
import { useSessionStore } from '../../../stores/sessionStore';
import { useStoryStore } from '../../../stores/storyStore';
import { useAudioStore } from '../../../stores/audioStore';
import { useSetupStore } from '../../../stores/setupStore';
import { useSiblingStore } from '../../../stores/siblingStore';
import { useParentControlsStore } from '../../../stores/parentControlsStore';
import { useSessionPersistenceStore } from '../../../stores/sessionPersistenceStore';
import { useDrawingStore } from '../../../stores/drawingStore';
import { useAudioFeedback } from '../../audio/hooks/useAudioFeedback';
import { useAudio } from '../../audio/hooks/useAudio';

export function useStoryConnection({ onVoiceCommand, onMechanics } = {}) {
  const unsubscribers = useRef([]);
  const langRef = useRef(null);
  const profilesRef = useRef(null);
  const { playSuccess, playError } = useAudioFeedback();

  const language = useSetupStore(s => s.language);
  const { speak } = useAudio(language);

  const connectToAI = useCallback((lang, profiles) => {
    langRef.current = lang;
    profilesRef.current = profiles;

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
      c2_toy: profiles.c2_toy || 'Book',
      c1_toy_type: profiles.c1_toy_type || '',
      c1_toy_image: profiles.c1_toy_image || '',
      c2_toy_type: profiles.c2_toy_type || '',
      c2_toy_image: profiles.c2_toy_image || '',
      c1_costume: profiles.c1_costume || '',
      c2_costume: profiles.c2_costume || '',
      time_limit_minutes: useParentControlsStore.getState().sessionTimeLimitMinutes.toString(),
    };

    // Include previous duration if resuming from a snapshot
    const prevDuration = useSessionStore.getState().previousDurationSeconds;
    if (prevDuration > 0) {
      params.previous_duration_seconds = prevDuration.toString();
    }

    const session = useSessionStore.getState();
    const story = useStoryStore.getState();
    const setup = useSetupStore.getState();
    const sibling = useSiblingStore.getState();

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
      const s = useSessionStore.getState();
      s.setConnected(true);
      s.setConnectionState('CONNECTED');
      playSuccess();
      // Sync localStorage snapshot to server on reconnect
      useSessionPersistenceStore.getState().syncLocalToServer();
      // Replay any drawing strokes queued during disconnect
      const queued = useDrawingStore.getState().flushSyncQueue();
      queued.forEach((stroke) => {
        websocketService.send({ type: 'DRAWING_STROKE', stroke });
      });
    });

    const unsubscribeDisconnected = websocketService.on('disconnected', ({ code, reason }) => {
      console.log('❌ Disconnected:', code, reason);
      const s = useSessionStore.getState();
      s.setConnected(false);
      s.setConnectionState('DISCONNECTED');

      // Save to localStorage on disconnect
      useSessionPersistenceStore.getState().saveToLocalStorage();

      if (code === 1006 && useSetupStore.getState().currentStep === 'story') {
        s.setReconnecting(true, 1);
        setTimeout(() => connectToAI(langRef.current, profilesRef.current), 3000);
      }
    });

    const unsubscribeAsset = websocketService.on('CREATIVE_ASSET', (data) => {
      console.log(`🎨 Asset received: ${data.media_type}`, data);
      
      const metadata = {
        child: data.metadata?.child,
        type: data.media_type
      };

      useStoryStore.getState().addAsset(data.media_type, data.content, metadata);
    });

    const unsubscribeComplete = websocketService.on('STORY_COMPLETE', (data) => {
      console.log('✅ STORY_COMPLETE received!');
      
      setTimeout(() => {
        const st = useStoryStore.getState();
        const assets = st.currentAssets;
        const p = useSetupStore.getState().getProfiles();

        const newBeat = {
          narration: assets.narration || "The adventure begins...",
          child1_perspective: assets.child1_perspective || 
            `${p.c1_name} sees something magical...`,
          child2_perspective: assets.child2_perspective || 
            `${p.c2_name} feels excited...`,
          scene_image_url: assets.image,
          choices: assets.choices.length > 0 
            ? assets.choices 
            : ["Continue the adventure"],
          voice_recordings: data?.voice_recordings || null
        };

        console.log('🎬 Setting storyBeat:', newBeat);
        st.setCurrentBeat(newBeat);

        if (useAudioStore.getState().ttsEnabled && newBeat.narration) {
          speak(newBeat.narration, langRef.current);
        }

        st.reset();
      }, 100);
    });

    const unsubscribeStatus = websocketService.on('STATUS', (data) => {
      console.log('📊 Status:', data.message);
      useStoryStore.getState().setGenerating(data.message.includes('Generating'));
    });

    const unsubscribeMechanic = websocketService.on('MECHANIC_WARNING', (data) => {
      console.log('⚠️ Mechanic:', data);
      if (onMechanics) onMechanics(data);
    });

    const unsubscribeError = websocketService.on('error', ({ error }) => {
      console.error('❌ WebSocket error:', error);
      useSessionStore.getState().setError('Connection error occurred');
      playError();
    });

    // Sibling dynamics: update store when story_segment includes sibling data
    const unsubscribeSiblingData = websocketService.on('story_segment', (data) => {
      if (data?.narrative_directives) {
        const dirs = data.narrative_directives;
        const sib = useSiblingStore.getState();
        if (dirs.child_roles) {
          sib.setChildRoles(dirs.child_roles);
        }
        if (dirs.waiting_for_child) {
          sib.setWaitingForChild(dirs.waiting_for_child);
        }
      }
    });

    // Voice command match: show toast and play confirmation audio
    const unsubscribeVoiceCommand = websocketService.on('VOICE_COMMAND_MATCH', (data) => {
      if (data?.matched) {
        console.log('🎤 Voice command matched:', data.command_action);
        if (onVoiceCommand) onVoiceCommand(data);
      }
    });

    // Drawing session: start when orchestrator sends a drawing prompt
    const unsubscribeDrawingPrompt = websocketService.on('DRAWING_PROMPT', (data) => {
      console.log('🎨 Drawing prompt received:', data.prompt);
      useDrawingStore.getState().startSession(data.prompt, data.duration || 60);
    });

    // Drawing session: end when server signals drawing is over
    const unsubscribeDrawingEnd = websocketService.on('DRAWING_END', () => {
      console.log('🎨 Drawing session ended');
      useDrawingStore.getState().endSession();
    });

    unsubscribers.current = [
      unsubscribeConnected,
      unsubscribeDisconnected,
      unsubscribeAsset,
      unsubscribeComplete,
      unsubscribeStatus,
      unsubscribeMechanic,
      unsubscribeError,
      unsubscribeSiblingData,
      unsubscribeVoiceCommand,
      unsubscribeDrawingPrompt,
      unsubscribeDrawingEnd
    ];
  }, [playSuccess, playError, onVoiceCommand, onMechanics, speak]);

  const disconnect = useCallback(() => {
    unsubscribers.current.forEach(unsub => unsub());
    unsubscribers.current = [];
    websocketService.disconnect();
  }, []);

  return { connectToAI, disconnect, unsubscribers };
}
