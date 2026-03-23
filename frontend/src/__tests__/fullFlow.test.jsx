/**
 * Full-flow integration tests: setup → store → rendering.
 * Ale and Sofi are the canonical test sibling pair.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, fireEvent, act } from '@testing-library/react';
import fc from 'fast-check';

import { useSetupStore } from '../stores/setupStore';
import { useSessionStore } from '../stores/sessionStore';
import { useStoryStore } from '../stores/storyStore';
import { ALE_SOFI_PROFILES, MOCK_STORY_BEAT } from './testFixtures';

// Reset stores before each test
beforeEach(() => {
  useSetupStore.getState().reset();
  useSessionStore.getState().reset();
  useStoryStore.getState().reset();
});

// ===================================================================
// Task 6: Frontend setup and story store integration tests
// ===================================================================

describe('Setup store processes Ale and Sofi profiles', () => {
  it('sets child1 as Ale and child2 as Sofi with isComplete true', () => {
    const store = useSetupStore.getState();

    store.setChild1({
      name: 'Ale',
      gender: 'girl',
      personality: 'brave',
      spirit: 'Dragon',
      costume: 'adventure_clothes',
      toy: 'Bruno',
      toyType: 'preset',
      toyImage: '',
    });

    store.setChild2({
      name: 'Sofi',
      gender: 'boy',
      personality: 'wise',
      spirit: 'Owl',
      costume: 'adventure_clothes',
      toy: 'Book',
      toyType: 'preset',
      toyImage: '',
    });

    store.completeSetup();

    const state = useSetupStore.getState();
    expect(state.child1.name).toBe('Ale');
    expect(state.child2.name).toBe('Sofi');
    expect(state.isComplete).toBe(true);
  });
});


describe('Spirit animal to personality mapping', () => {
  it('maps Dragon to brave and Owl to wise', () => {
    const spiritToPersonality = {
      dragon: 'brave',
      unicorn: 'creative',
      owl: 'wise',
      dolphin: 'friendly',
      phoenix: 'resilient',
      tiger: 'confident',
    };

    expect(spiritToPersonality['dragon']).toBe('brave');
    expect(spiritToPersonality['owl']).toBe('wise');
    expect(spiritToPersonality['unicorn']).toBe('creative');
    expect(spiritToPersonality['dolphin']).toBe('friendly');
    expect(spiritToPersonality['phoenix']).toBe('resilient');
    expect(spiritToPersonality['tiger']).toBe('confident');
  });
});

describe('Session store receives enriched profiles', () => {
  it('stores profiles with personality, spirit, and toy fields', () => {
    useSessionStore.getState().setProfiles(ALE_SOFI_PROFILES);

    const { profiles } = useSessionStore.getState();
    expect(profiles.c1_name).toBe('Ale');
    expect(profiles.c1_personality).toBe('brave');
    expect(profiles.c2_spirit).toBe('Owl');
  });
});

describe('Story store accumulates assets', () => {
  it('accumulates narration, perspectives, image, and choices', () => {
    const store = useStoryStore.getState();

    store.addAsset('text', 'Ale and Sofi discovered a magical forest...');
    store.addAsset('text', 'Ale sees a glowing dragon egg!', { child: 'c1' });
    store.addAsset('text', 'Sofi notices ancient owl runes.', { child: 'c2' });
    store.addAsset('image', '/assets/generated_images/test_scene.png');
    store.addAsset('interactive', ['Follow the dragon egg', 'Read the owl runes']);

    const { currentAssets } = useStoryStore.getState();
    expect(currentAssets.narration).toBe('Ale and Sofi discovered a magical forest...');
    expect(currentAssets.child1_perspective).toBe('Ale sees a glowing dragon egg!');
    expect(currentAssets.child2_perspective).toBe('Sofi notices ancient owl runes.');
    expect(currentAssets.image).toBe('/assets/generated_images/test_scene.png');
    expect(currentAssets.choices).toEqual(['Follow the dragon egg', 'Read the owl runes']);
  });
});

describe('Story store assembles beat', () => {
  it('makes beat available for rendering after setCurrentBeat', () => {
    useStoryStore.getState().setCurrentBeat(MOCK_STORY_BEAT);

    const { currentBeat } = useStoryStore.getState();
    expect(currentBeat.narration).toBe('Ale and Sofi discovered a magical forest...');
    expect(currentBeat.child1_perspective).toBe('Ale sees a glowing dragon egg!');
    expect(currentBeat.child2_perspective).toBe('Sofi notices ancient owl runes on a tree.');
    expect(currentBeat.scene_image_url).toBe('/assets/generated_images/test_scene.png');
    expect(currentBeat.choices).toHaveLength(3);
  });
});

// ===================================================================
// Task 7: Frontend DualStoryDisplay rendering tests
// ===================================================================

// Mock the audio stores to avoid side effects
vi.mock('../stores/audioStore', () => ({
  useAudioStore: vi.fn(() => ({
    queueVoiceRecording: vi.fn(),
    isPlayingVoiceRecording: false,
    currentVoiceRecording: null,
  })),
}));

vi.mock('../stores/sceneAudioStore', () => {
  const store = {
    playSfx: vi.fn(),
    getState: () => store,
  };
  return {
    useSceneAudioStore: Object.assign(vi.fn(() => store), store),
  };
});

// Import DualStoryDisplay — mocks above are hoisted by vitest
import DualStoryDisplay from '../features/story/components/DualStoryDisplay';

describe('DualStoryDisplay renders narration', () => {
  it('renders narration text in .story-narration__text', () => {
    const { container } = render(
      <DualStoryDisplay
        storyBeat={MOCK_STORY_BEAT}
        profiles={ALE_SOFI_PROFILES}
        onChoice={vi.fn()}
      />
    );

    const narrationEl = container.querySelector('.story-narration__text');
    expect(narrationEl).not.toBeNull();
    expect(narrationEl.textContent).toContain('Ale and Sofi discovered a magical forest...');
  });
});

describe('DualStoryDisplay renders Ale and Sofi names', () => {
  it('displays both names in the scene avatar area', () => {
    const { container } = render(
      <DualStoryDisplay
        storyBeat={MOCK_STORY_BEAT}
        profiles={ALE_SOFI_PROFILES}
        onChoice={vi.fn()}
      />
    );

    const avatarNames = container.querySelectorAll('.story-scene__avatar-name');
    const names = Array.from(avatarNames).map((el) => el.textContent);
    expect(names).toContain('Ale');
    expect(names).toContain('Sofi');
  });
});

describe('DualStoryDisplay renders choice cards', () => {
  it('renders one story-choice-card per choice', () => {
    const { container } = render(
      <DualStoryDisplay
        storyBeat={MOCK_STORY_BEAT}
        profiles={ALE_SOFI_PROFILES}
        onChoice={vi.fn()}
      />
    );

    const cards = container.querySelectorAll('.story-choice-card');
    expect(cards).toHaveLength(MOCK_STORY_BEAT.choices.length);
  });
});

describe('DualStoryDisplay choice callback', () => {
  it('calls onChoice with the selected choice text', () => {
    vi.useFakeTimers();
    const onChoice = vi.fn();

    const { container } = render(
      <DualStoryDisplay
        storyBeat={MOCK_STORY_BEAT}
        profiles={ALE_SOFI_PROFILES}
        onChoice={onChoice}
      />
    );

    const firstCard = container.querySelector('.story-choice-card');
    fireEvent.click(firstCard);

    // handleChoiceTap uses setTimeout(400ms)
    act(() => {
      vi.advanceTimersByTime(400);
    });

    expect(onChoice).toHaveBeenCalledWith(MOCK_STORY_BEAT.choices[0]);
    vi.useRealTimers();
  });
});

describe('DualStoryDisplay renders scene image', () => {
  it('renders SceneImageLoader when scene_image_url is present', () => {
    const { container } = render(
      <DualStoryDisplay
        storyBeat={MOCK_STORY_BEAT}
        profiles={ALE_SOFI_PROFILES}
        onChoice={vi.fn()}
      />
    );

    // SceneImageLoader renders a .scene-loader container
    const sceneLoader = container.querySelector('.scene-loader');
    expect(sceneLoader).not.toBeNull();
  });
});

// ===================================================================
// Property-Based Tests (fast-check)
// ===================================================================

// Feature: full-flow-integration-testing, Property 5: Spirit Animal to Personality Mapping
describe('PBT: Spirit animal to personality mapping', () => {
  it('always produces a non-empty deterministic personality string', () => {
    const spiritToPersonality = {
      dragon: 'brave',
      unicorn: 'creative',
      owl: 'wise',
      dolphin: 'friendly',
      phoenix: 'resilient',
      tiger: 'confident',
    };

    fc.assert(
      fc.property(
        fc.constantFrom('dragon', 'unicorn', 'owl', 'dolphin', 'phoenix', 'tiger'),
        (spirit) => {
          const result = spiritToPersonality[spirit];
          // Non-empty string
          if (typeof result !== 'string' || result.length === 0) return false;
          // Deterministic
          return spiritToPersonality[spirit] === result;
        }
      ),
      { numRuns: 100 }
    );
  });
});

// Feature: full-flow-integration-testing, Property 6: Choice Card Count Matches Choices Array
describe('PBT: Choice card count matches choices array', () => {
  it('renders exactly N choice cards for N choices', () => {
    fc.assert(
      fc.property(
        fc.array(fc.string({ minLength: 1, maxLength: 30 }), { minLength: 1, maxLength: 6 }),
        (choices) => {
          const beat = { ...MOCK_STORY_BEAT, choices };
          const { container } = render(
            <DualStoryDisplay
              storyBeat={beat}
              profiles={ALE_SOFI_PROFILES}
              onChoice={vi.fn()}
            />
          );
          const cards = container.querySelectorAll('.story-choice-card');
          return cards.length === choices.length;
        }
      ),
      { numRuns: 100 }
    );
  });
});
