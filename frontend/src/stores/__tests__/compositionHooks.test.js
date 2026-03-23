import { describe, it, expect, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import {
  useStorySession,
  useChildProfiles,
  useSessionControls,
  useDrawingSession,
  useMediaCapture,
} from '../compositionHooks';
import { useStoryStore } from '../storyStore';
import { useSessionStore } from '../sessionStore';
import { useAudioStore } from '../audioStore';
import { useSetupStore } from '../setupStore';
import { useParentControlsStore } from '../parentControlsStore';
import { useSiblingStore } from '../siblingStore';
import { useDrawingStore } from '../drawingStore';
import { useMultimodalStore } from '../multimodalStore';
import { useSceneAudioStore } from '../sceneAudioStore';

// Reset all stores before each test
beforeEach(() => {
  useStoryStore.setState(useStoryStore.getInitialState());
  useSessionStore.setState(useSessionStore.getInitialState());
  useAudioStore.setState(useAudioStore.getInitialState());
  useSetupStore.setState(useSetupStore.getInitialState());
  useSiblingStore.setState(useSiblingStore.getInitialState());
  useDrawingStore.setState(useDrawingStore.getInitialState());
  useMultimodalStore.setState(useMultimodalStore.getInitialState());
});

describe('useStorySession', () => {
  it('returns correct shape with default values', () => {
    const { result } = renderHook(() => useStorySession());
    expect(result.current).toEqual({
      currentBeat: null,
      isGenerating: false,
      connected: false,
      connectionState: 'DISCONNECTED',
      ttsEnabled: true,
      language: 'en',
    });
  });

  it('reflects store state changes', () => {
    const { result } = renderHook(() => useStorySession());
    act(() => {
      useStoryStore.setState({ currentBeat: { narration: 'test' }, isGenerating: true });
      useSessionStore.setState({ isConnected: true, connectionState: 'CONNECTED' });
      useAudioStore.setState({ ttsEnabled: false, ttsLanguage: 'es' });
    });
    expect(result.current.currentBeat).toEqual({ narration: 'test' });
    expect(result.current.isGenerating).toBe(true);
    expect(result.current.connected).toBe(true);
    expect(result.current.connectionState).toBe('CONNECTED');
    expect(result.current.ttsEnabled).toBe(false);
    expect(result.current.language).toBe('es');
  });
});

describe('useChildProfiles', () => {
  it('returns correct shape with default values', () => {
    const { result } = renderHook(() => useChildProfiles());
    expect(result.current.child1).toEqual({ name: '', gender: '', personality: '', spirit: '', costume: '', toy: '', toyType: '', toyImage: '' });
    expect(result.current.child2).toEqual({ name: '', gender: '', personality: '', spirit: '', costume: '', toy: '', toyType: '', toyImage: '' });
    expect(result.current.language).toBe('en');
    expect(result.current.isComplete).toBe(false);
    expect(result.current.profiles).toBeDefined();
  });

  it('reflects store state changes', () => {
    const { result } = renderHook(() => useChildProfiles());
    act(() => {
      useSetupStore.setState({
        child1: { name: 'Luna', gender: 'girl', personality: '', spirit: 'dragon', toy: 'teddy', toyType: '', toyImage: '' },
        language: 'es',
        isComplete: true,
      });
    });
    expect(result.current.child1.name).toBe('Luna');
    expect(result.current.language).toBe('es');
    expect(result.current.isComplete).toBe(true);
  });

  it('profiles are memoized when deps unchanged', () => {
    const { result, rerender } = renderHook(() => useChildProfiles());
    const first = result.current.profiles;
    rerender();
    expect(result.current.profiles).toBe(first);
  });
});

describe('useSessionControls', () => {
  it('returns correct shape with default values', () => {
    const { result } = renderHook(() => useSessionControls());
    expect(result.current).toEqual({
      sessionId: '',
      connected: false,
      reconnecting: false,
      siblingScore: null,
      sessionSummary: null,
      timeLimitMinutes: 30,
    });
  });

  it('reflects store state changes from 3 stores', () => {
    const { result } = renderHook(() => useSessionControls());
    act(() => {
      useSessionStore.setState({ sessionId: 'abc', isConnected: true, isReconnecting: true });
      useSiblingStore.setState({ siblingDynamicsScore: 0.8, sessionSummary: 'Great session' });
      useParentControlsStore.setState({ sessionTimeLimitMinutes: 45 });
    });
    expect(result.current.sessionId).toBe('abc');
    expect(result.current.connected).toBe(true);
    expect(result.current.reconnecting).toBe(true);
    expect(result.current.siblingScore).toBe(0.8);
    expect(result.current.sessionSummary).toBe('Great session');
    expect(result.current.timeLimitMinutes).toBe(45);
  });
});

describe('useDrawingSession', () => {
  it('returns correct shape with remainingTime mapped to timeRemaining', () => {
    const { result } = renderHook(() => useDrawingSession());
    expect(result.current).toEqual({
      isActive: false,
      prompt: '',
      timeRemaining: 60,
      strokes: [],
    });
  });

  it('maps remainingTime to timeRemaining after state change', () => {
    const { result } = renderHook(() => useDrawingSession());
    act(() => {
      useDrawingStore.setState({ isActive: true, prompt: 'Draw a castle', remainingTime: 42 });
    });
    expect(result.current.isActive).toBe(true);
    expect(result.current.prompt).toBe('Draw a castle');
    expect(result.current.timeRemaining).toBe(42);
  });
});

describe('useMediaCapture', () => {
  it('returns correct shape with currentEmotions mapped to lastEmotion', () => {
    const { result } = renderHook(() => useMediaCapture());
    expect(result.current).toEqual({
      audioUnlocked: false,
      cameraActive: false,
      lastEmotion: [],
    });
  });

  it('maps currentEmotions to lastEmotion after state change', () => {
    const { result } = renderHook(() => useMediaCapture());
    const emotions = [{ face_id: 1, emotion: 'happy', confidence: 0.9 }];
    act(() => {
      useMultimodalStore.setState({ currentEmotions: emotions, cameraActive: true });
    });
    expect(result.current.lastEmotion).toEqual(emotions);
    expect(result.current.cameraActive).toBe(true);
  });
});

describe('selector isolation', () => {
  it('useStorySession does not re-render on unrelated storyStore changes', () => {
    let renderCount = 0;
    const { result } = renderHook(() => {
      renderCount++;
      return useStorySession();
    });
    const initialCount = renderCount;

    // Change an unrelated field (history) that useStorySession doesn't subscribe to
    act(() => {
      useStoryStore.setState({ history: [{ narration: 'old beat' }] });
    });
    // renderCount should not increase since history is not subscribed
    expect(renderCount).toBe(initialCount);
  });

  it('useDrawingSession does not re-render on unrelated drawingStore changes', () => {
    let renderCount = 0;
    renderHook(() => {
      renderCount++;
      return useDrawingSession();
    });
    const initialCount = renderCount;

    // Change selectedColor which useDrawingSession doesn't subscribe to
    act(() => {
      useDrawingStore.setState({ selectedColor: '#FF0000' });
    });
    expect(renderCount).toBe(initialCount);
  });
});
