/**
 * Property-based tests for wizardReducer (Tasks 8.2–8.5).
 *
 * Property 1: wizardStep is always in STEP_ORDER
 * Property 2: childNum is always 1 or 2
 * Property 3: reducer never mutates input state
 */

import { describe, it, expect } from 'vitest';
import fc from 'fast-check';
import {
  wizardReducer,
  initialState,
  STEP_ORDER,
  ActionTypes,
} from '../wizardReducer';

// ── Arbitrary: valid actions ───────────────────────────────────

const stepArb = fc.constantFrom(...STEP_ORDER);
const genderArb = fc.constantFrom('girl', 'boy', 'non-binary');
const spiritArb = fc.constantFrom('Dragon', 'Unicorn', 'Owl', 'Dolphin');
const costumeArb = fc.constantFrom('knight_armor', 'space_suit', 'princess_gown');
const toyArb = fc.constantFrom('teddy', 'robot', 'doll');
const nameArb = fc.string({ minLength: 1, maxLength: 20 });

const actionArb = fc.oneof(
  stepArb.map((step) => ({ type: ActionTypes.GO_TO_STEP, step })),
  fc.record({ field: nameArb, value: nameArb }).map((r) => ({
    type: ActionTypes.SET_FIELD, field: r.field, value: r.value,
  })),
  nameArb.map((error) => ({ type: ActionTypes.SET_NAME_ERROR, error })),
  nameArb.map((error) => ({ type: ActionTypes.SET_TOY_ERROR, error })),
  genderArb.map((value) => ({ type: ActionTypes.PICK_GENDER, value })),
  spiritArb.map((value) => ({ type: ActionTypes.PICK_SPIRIT, value })),
  costumeArb.map((value) => ({ type: ActionTypes.PICK_COSTUME, value })),
  toyArb.map((value) => ({ type: ActionTypes.PICK_PRESET_TOY, value })),
  fc.constant({ type: ActionTypes.SET_TOY_PHOTO, preview: 'data:img', file: {} }),
  fc.constant({ type: ActionTypes.NEXT_CHILD }),
  fc.constant({ type: ActionTypes.CLEAR_BOUNCE }),
  fc.constant({ type: ActionTypes.SHOW_SPARKLE }),
  fc.constant({ type: ActionTypes.HIDE_SPARKLE }),
  fc.constant({ type: ActionTypes.SET_PHOTO_REFRESH }),
  nameArb.map((cn) => ({ type: ActionTypes.SET_TRANSITION, className: cn })),
);

const actionSeqArb = fc.array(actionArb, { minLength: 1, maxLength: 30 });

/** Deep-freeze an object recursively (throws on mutation). */
function deepFreeze(obj) {
  if (obj === null || typeof obj !== 'object') return obj;
  Object.freeze(obj);
  for (const val of Object.values(obj)) {
    if (val !== null && typeof val === 'object' && !Object.isFrozen(val)) {
      deepFreeze(val);
    }
  }
  return obj;
}

// ── Property 1: wizardStep always in STEP_ORDER (Task 8.3) ────

describe('Property: wizardStep is always in STEP_ORDER', () => {
  it('holds for any sequence of valid actions', () => {
    fc.assert(
      fc.property(actionSeqArb, (actions) => {
        let state = { ...initialState, formData: { ...initialState.formData } };
        for (const action of actions) {
          state = wizardReducer(state, action);
          expect(STEP_ORDER).toContain(state.wizardStep);
        }
      }),
      { numRuns: 20 },
    );
  });
});

// ── Property 2: childNum always 1 or 2 (Task 8.4) ─────────────

describe('Property: childNum is always 1 or 2', () => {
  it('holds for any sequence of valid actions', () => {
    fc.assert(
      fc.property(actionSeqArb, (actions) => {
        let state = { ...initialState, formData: { ...initialState.formData } };
        for (const action of actions) {
          state = wizardReducer(state, action);
          expect([1, 2]).toContain(state.childNum);
        }
      }),
      { numRuns: 20 },
    );
  });
});

// ── Property 3: reducer never mutates input state (Task 8.5) ───

describe('Property: reducer never mutates input state', () => {
  it('deep-frozen state survives any action without throwing', () => {
    fc.assert(
      fc.property(actionSeqArb, (actions) => {
        let state = deepFreeze(
          JSON.parse(JSON.stringify(initialState)),
        );
        for (const action of actions) {
          const next = wizardReducer(state, action);
          // Next state should be a new reference (or same if unknown action)
          // The key invariant: no TypeError from frozen mutation
          expect(STEP_ORDER).toContain(next.wizardStep);
          state = deepFreeze(JSON.parse(JSON.stringify(next)));
        }
      }),
      { numRuns: 20 },
    );
  });
});
