/**
 * Store Composition Hooks
 *
 * Thin hooks that compose multiple Zustand stores using individual selectors.
 * Each field is subscribed independently — components only re-render when
 * a field they actually use changes.
 */

import { useMemo } from 'react';
import { useSessionStore } from './sessionStore';
import { useStoryStore } from './storyStore';
import { useAudioStore } from './audioStore';
import { useSetupStore } from './setupStore';
import { useParentControlsStore } from '../stores/parentControlsStore';
import { useSiblingStore } from '../stores/siblingStore';
import { useDrawingStore } from './drawingStore';
import { useMultimodalStore } from './multimodalStore';
import { useSceneAudioStore } from './sceneAudioStore';

/**
 * Composes sessionStore + storyStore + audioStore for story display components.
 */
export function useStorySession() {
  const currentBeat = useStoryStore((s) => s.currentBeat);
  const isGenerating = useStoryStore((s) => s.isGenerating);
  const connected = useSessionStore((s) => s.isConnected);
  const connectionState = useSessionStore((s) => s.connectionState);
  const ttsEnabled = useAudioStore((s) => s.ttsEnabled);
  const language = useAudioStore((s) => s.ttsLanguage);

  return { currentBeat, isGenerating, connected, connectionState, ttsEnabled, language };
}

/**
 * Composes setupStore for profile access with memoized profiles payload.
 */
export function useChildProfiles() {
  const child1 = useSetupStore((s) => s.child1);
  const child2 = useSetupStore((s) => s.child2);
  const language = useSetupStore((s) => s.language);
  const isComplete = useSetupStore((s) => s.isComplete);

  const profiles = useMemo(
    () => useSetupStore.getState().getProfiles(),
    [child1, child2, language]
  );

  return { child1, child2, profiles, language, isComplete };
}


/**
 * Composes sessionStore + parentControlsStore + siblingStore for session control UI.
 */
export function useSessionControls() {
  const sessionId = useSessionStore((s) => s.sessionId);
  const connected = useSessionStore((s) => s.isConnected);
  const reconnecting = useSessionStore((s) => s.isReconnecting);
  const siblingScore = useSiblingStore((s) => s.siblingDynamicsScore);
  const sessionSummary = useSiblingStore((s) => s.sessionSummary);
  const timeLimitMinutes = useParentControlsStore((s) => s.sessionTimeLimitMinutes);

  return { sessionId, connected, reconnecting, siblingScore, sessionSummary, timeLimitMinutes };
}

/**
 * Composes drawingStore for drawing components.
 * Maps remainingTime → timeRemaining for consumer clarity.
 */
export function useDrawingSession() {
  const isActive = useDrawingStore((s) => s.isActive);
  const prompt = useDrawingStore((s) => s.prompt);
  const timeRemaining = useDrawingStore((s) => s.remainingTime);
  const strokes = useDrawingStore((s) => s.strokes);

  return { isActive, prompt, timeRemaining, strokes };
}

/**
 * Composes multimodalStore + sceneAudioStore for media state.
 * Maps currentEmotions → lastEmotion for consumer clarity.
 */
export function useMediaCapture() {
  const audioUnlocked = useSceneAudioStore((s) => s.audioUnlocked);
  const cameraActive = useMultimodalStore((s) => s.cameraActive);
  const lastEmotion = useMultimodalStore((s) => s.currentEmotions);

  return { audioUnlocked, cameraActive, lastEmotion };
}
