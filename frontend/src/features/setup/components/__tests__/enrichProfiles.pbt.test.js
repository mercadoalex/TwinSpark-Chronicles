/**
 * Property-Based Tests for enrichProfiles logic in SetupScreen
 *
 * Feature: app-component-split, Property 2: enrichProfiles always produces complete output
 *
 * **Validates: Requirements 2.5**
 */

import { describe, it, expect } from 'vitest';
import fc from 'fast-check';
import costumeCatalog from '../../data/costumeCatalog';

// ── Replicate the pure enrichment logic from SetupScreen.handleSetupComplete ──

const spiritToPersonality = {
  dragon: 'brave',
  unicorn: 'creative',
  owl: 'wise',
  dolphin: 'friendly',
  phoenix: 'resilient',
  tiger: 'confident',
};

const lookupCostumePrompt = (id) => {
  const entry = costumeCatalog.find((c) => c.id === id);
  return entry ? entry.promptFragment : null;
};

function enrichProfiles(profiles) {
  return {
    c1_name: profiles.c1_name || 'Child 1',
    c1_gender: profiles.c1_gender || 'girl',
    c1_personality:
      spiritToPersonality[profiles.c1_spirit_animal?.toLowerCase()] || 'brave',
    c1_spirit: profiles.c1_spirit_animal || 'Dragon',
    c1_costume: profiles.c1_costume || 'adventure_clothes',
    c1_costume_prompt:
      lookupCostumePrompt(profiles.c1_costume) || 'wearing adventure clothes',
    c1_toy: profiles.c1_toy_name || 'Bruno',
    c1_toy_type: profiles.c1_toy_type || 'preset',
    c1_toy_image: profiles.c1_toy_image || '',
    c2_name: profiles.c2_name || 'Child 2',
    c2_gender: profiles.c2_gender || 'girl',
    c2_personality:
      spiritToPersonality[profiles.c2_spirit_animal?.toLowerCase()] || 'wise',
    c2_spirit: profiles.c2_spirit_animal || 'Owl',
    c2_costume: profiles.c2_costume || 'adventure_clothes',
    c2_costume_prompt:
      lookupCostumePrompt(profiles.c2_costume) || 'wearing adventure clothes',
    c2_toy: profiles.c2_toy_name || 'Book',
    c2_toy_type: profiles.c2_toy_type || 'preset',
    c2_toy_image: profiles.c2_toy_image || '',
  };
}

// ── Required output fields ─────────────────────────────────────

const REQUIRED_STRING_FIELDS = [
  'c1_name',
  'c1_gender',
  'c1_personality',
  'c1_spirit',
  'c1_costume',
  'c1_costume_prompt',
  'c1_toy',
  'c1_toy_type',
  'c2_name',
  'c2_gender',
  'c2_personality',
  'c2_spirit',
  'c2_costume',
  'c2_costume_prompt',
  'c2_toy',
  'c2_toy_type',
];

const ALL_FIELDS = [
  ...REQUIRED_STRING_FIELDS,
  'c1_toy_image',
  'c2_toy_image',
];

const VALID_PERSONALITIES = ['brave', 'creative', 'wise', 'friendly', 'resilient', 'confident'];

// ── Arbitraries ────────────────────────────────────────────────

const genderArb = fc.constantFrom('girl', 'boy', 'non-binary');
const spiritArb = fc.constantFrom('Dragon', 'Unicorn', 'Owl', 'Dolphin', 'Phoenix', 'Tiger');
const costumeIdArb = fc.constantFrom(
  'knight_armor', 'space_suit', 'princess_gown', 'pirate_outfit',
  'superhero_cape', 'wizard_robe', 'explorer_gear', 'fairy_wings',
);
const nameArb = fc.string({ minLength: 1, maxLength: 30 }).filter((s) => s.trim().length > 0);
const toyNameArb = fc.string({ minLength: 1, maxLength: 20 }).filter((s) => s.trim().length > 0);

// Full valid profile (all fields present)
const fullProfileArb = fc.record({
  c1_name: nameArb,
  c1_gender: genderArb,
  c1_spirit_animal: spiritArb,
  c1_costume: costumeIdArb,
  c1_toy_name: toyNameArb,
  c1_toy_type: fc.constantFrom('preset', 'custom'),
  c1_toy_image: fc.string(),
  c2_name: nameArb,
  c2_gender: genderArb,
  c2_spirit_animal: spiritArb,
  c2_costume: costumeIdArb,
  c2_toy_name: toyNameArb,
  c2_toy_type: fc.constantFrom('preset', 'custom'),
  c2_toy_image: fc.string(),
});

// Sparse profile (some fields may be missing/empty — tests defaults)
const sparseProfileArb = fc.record({
  c1_name: fc.oneof(nameArb, fc.constant('')),
  c1_gender: fc.oneof(genderArb, fc.constant('')),
  c1_spirit_animal: fc.oneof(spiritArb, fc.constant(undefined)),
  c1_costume: fc.oneof(costumeIdArb, fc.constant('')),
  c1_toy_name: fc.oneof(toyNameArb, fc.constant('')),
  c1_toy_type: fc.oneof(fc.constantFrom('preset', 'custom'), fc.constant('')),
  c1_toy_image: fc.oneof(fc.string(), fc.constant('')),
  c2_name: fc.oneof(nameArb, fc.constant('')),
  c2_gender: fc.oneof(genderArb, fc.constant('')),
  c2_spirit_animal: fc.oneof(spiritArb, fc.constant(undefined)),
  c2_costume: fc.oneof(costumeIdArb, fc.constant('')),
  c2_toy_name: fc.oneof(toyNameArb, fc.constant('')),
  c2_toy_type: fc.oneof(fc.constantFrom('preset', 'custom'), fc.constant('')),
  c2_toy_image: fc.oneof(fc.string(), fc.constant('')),
});

// ── Tests ──────────────────────────────────────────────────────

describe('enrichProfiles – PBT', () => {
  it('always produces output with all required fields populated for any valid input', () => {
    fc.assert(
      fc.property(
        fc.oneof(fullProfileArb, sparseProfileArb),
        (rawProfiles) => {
          const result = enrichProfiles(rawProfiles);

          // All fields exist on the output
          for (const field of ALL_FIELDS) {
            expect(result).toHaveProperty(field);
            expect(typeof result[field]).toBe('string');
          }

          // Required string fields are never empty
          for (const field of REQUIRED_STRING_FIELDS) {
            expect(result[field].length).toBeGreaterThan(0);
          }

          // Personality is always one of the valid values
          expect(VALID_PERSONALITIES).toContain(result.c1_personality);
          expect(VALID_PERSONALITIES).toContain(result.c2_personality);

          // Costume prompt is always a non-empty string
          expect(result.c1_costume_prompt.length).toBeGreaterThan(0);
          expect(result.c2_costume_prompt.length).toBeGreaterThan(0);
        },
      ),
      { numRuns: 100 },
    );
  });
});
