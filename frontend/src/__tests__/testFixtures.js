/**
 * Shared Ale & Sofi test fixtures for full-flow integration tests.
 */

export const ALE_SOFI_PROFILES = {
  c1_name: 'Ale',
  c1_gender: 'girl',
  c1_personality: 'brave',
  c1_spirit: 'Dragon',
  c1_costume: 'adventure_clothes',
  c1_costume_prompt: 'wearing adventure clothes',
  c1_toy: 'Bruno',
  c1_toy_type: 'preset',
  c1_toy_image: '',
  c2_name: 'Sofi',
  c2_gender: 'boy',
  c2_personality: 'wise',
  c2_spirit: 'Owl',
  c2_costume: 'adventure_clothes',
  c2_costume_prompt: 'wearing adventure clothes',
  c2_toy: 'Book',
  c2_toy_type: 'preset',
  c2_toy_image: '',
};

export const MOCK_STORY_BEAT = {
  narration: 'Ale and Sofi discovered a magical forest...',
  child1_perspective: 'Ale sees a glowing dragon egg!',
  child2_perspective: 'Sofi notices ancient owl runes on a tree.',
  scene_image_url: '/assets/generated_images/test_scene.png',
  choices: ['Follow the dragon egg', 'Read the owl runes', 'Explore together'],
};
