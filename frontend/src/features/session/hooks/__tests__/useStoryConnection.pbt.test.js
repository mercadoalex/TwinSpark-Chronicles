/**
 * Property-Based Tests for useStoryConnection hook
 *
 * Feature: app-component-split, Property 1: connectToAI registers exactly 11 subscriptions
 *
 * **Validates: Requirements 4.4**
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import fc from 'fast-check';

// ── Track websocketService.on() calls ──────────────────────────

let onCalls = [];
const mockConnect = vi.fn(() => Promise.resolve());

vi.mock('../../services/websocketService', () => ({
  websocketService: {
    connect: (...args) => mockConnect(...args),
    disconnect: vi.fn(),
    on: vi.fn((eventType, callback) => {
      onCalls.push({ eventType, callback });
      const unsub = vi.fn();
      return unsub;
    }),
    send: vi.fn(),
    isConnected: vi.fn(() => false),
  },
}));

// ── Mock stores ────────────────────────────────────────────────

vi.mock('../../../../stores/sessionStore', () => {
  const store = {
    setConnected: vi.fn(),
    setConnectionState: vi.fn(),
    setError: vi.fn(),
    setReconnecting: vi.fn(),
    previousDurationSeconds: 0,
    getState: () => store,
  };
  return {
    useSessionStore: Object.assign(vi.fn((sel) => (typeof sel === 'function' ? sel(store) : store)), store),
  };
});

vi.mock('../../../../stores/storyStore', () => {
  const store = {
    addAsset: vi.fn(),
    setCurrentBeat: vi.fn(),
    setGenerating: vi.fn(),
    currentAssets: { narration: '', child1_perspective: '', child2_perspective: '', image: '', choices: [] },
    reset: vi.fn(),
    getState: () => store,
  };
  return {
    useStoryStore: Object.assign(vi.fn((sel) => (typeof sel === 'function' ? sel(store) : store)), store),
  };
});

vi.mock('../../../../stores/audioStore', () => {
  const store = { ttsEnabled: false, getState: () => store };
  return {
    useAudioStore: Object.assign(vi.fn((sel) => (typeof sel === 'function' ? sel(store) : store)), store),
  };
});

vi.mock('../../../../stores/setupStore', () => {
  const store = {
    language: 'en',
    currentStep: 'story',
    getProfiles: vi.fn(() => ({ c1_name: 'A', c2_name: 'B' })),
    getState: () => store,
  };
  return {
    useSetupStore: Object.assign(vi.fn((sel) => (typeof sel === 'function' ? sel(store) : store)), store),
  };
});

vi.mock('../../../../stores/siblingStore', () => {
  const store = { setChildRoles: vi.fn(), setWaitingForChild: vi.fn(), getState: () => store };
  return {
    useSiblingStore: Object.assign(vi.fn((sel) => (typeof sel === 'function' ? sel(store) : store)), store),
  };
});

vi.mock('../../../../stores/parentControlsStore', () => {
  const store = { sessionTimeLimitMinutes: 30, getState: () => store };
  return {
    useParentControlsStore: Object.assign(vi.fn((sel) => (typeof sel === 'function' ? sel(store) : store)), store),
  };
});

vi.mock('../../../../stores/sessionPersistenceStore', () => {
  const store = { syncLocalToServer: vi.fn(), saveToLocalStorage: vi.fn(), getState: () => store };
  return {
    useSessionPersistenceStore: Object.assign(vi.fn((sel) => (typeof sel === 'function' ? sel(store) : store)), store),
  };
});

vi.mock('../../../../stores/drawingStore', () => {
  const store = { startSession: vi.fn(), endSession: vi.fn(), flushSyncQueue: vi.fn(() => []), getState: () => store };
  return {
    useDrawingStore: Object.assign(vi.fn((sel) => (typeof sel === 'function' ? sel(store) : store)), store),
  };
});

vi.mock('../../../audio/hooks/useAudioFeedback', () => ({
  useAudioFeedback: () => ({ playSuccess: vi.fn(), playError: vi.fn() }),
}));

vi.mock('../../../audio/hooks/useAudio', () => ({
  useAudio: () => ({ speak: vi.fn() }),
}));

// Import after mocks
const { useStoryConnection } = await import('../useStoryConnection');

// ── Arbitrary: valid profiles ──────────────────────────────────

const genderArb = fc.constantFrom('girl', 'boy', 'non-binary');
const spiritArb = fc.constantFrom('Dragon', 'Unicorn', 'Owl', 'Dolphin', 'Phoenix', 'Tiger');
const nameArb = fc.string({ minLength: 1, maxLength: 30 }).filter(s => s.trim().length > 0);
const toyArb = fc.string({ minLength: 1, maxLength: 20 }).filter(s => s.trim().length > 0);

const profilesArb = fc.record({
  c1_name: nameArb,
  c1_gender: genderArb,
  c1_personality: fc.constantFrom('brave', 'creative', 'wise', 'friendly', 'resilient', 'confident'),
  c1_spirit: spiritArb,
  c1_toy: toyArb,
  c2_name: nameArb,
  c2_gender: genderArb,
  c2_personality: fc.constantFrom('brave', 'creative', 'wise', 'friendly', 'resilient', 'confident'),
  c2_spirit: spiritArb,
  c2_toy: toyArb,
});

// ── Tests ──────────────────────────────────────────────────────

describe('useStoryConnection – PBT', () => {
  beforeEach(() => {
    onCalls = [];
    mockConnect.mockClear();
  });

  it('connectToAI registers exactly 11 subscriptions for any valid profiles', () => {
    const EXPECTED_EVENTS = [
      'connected',
      'disconnected',
      'CREATIVE_ASSET',
      'STORY_COMPLETE',
      'STATUS',
      'MECHANIC_WARNING',
      'error',
      'story_segment',
      'VOICE_COMMAND_MATCH',
      'DRAWING_PROMPT',
      'DRAWING_END',
    ];

    fc.assert(
      fc.property(profilesArb, (profiles) => {
        onCalls = [];
        mockConnect.mockClear();

        const { result } = renderHook(() => useStoryConnection());

        act(() => {
          result.current.connectToAI('en', profiles);
        });

        // Exactly 11 subscriptions registered
        expect(onCalls).toHaveLength(11);

        // Each expected event type is subscribed exactly once
        const subscribedEvents = onCalls.map(c => c.eventType);
        for (const evt of EXPECTED_EVENTS) {
          expect(subscribedEvents.filter(e => e === evt)).toHaveLength(1);
        }

        // The hook stores exactly 11 unsubscribe refs
        expect(result.current.unsubscribers.current).toHaveLength(11);

        // Each unsubscriber is a function
        for (const unsub of result.current.unsubscribers.current) {
          expect(typeof unsub).toBe('function');
        }
      }),
      { numRuns: 100 },
    );
  });
});
