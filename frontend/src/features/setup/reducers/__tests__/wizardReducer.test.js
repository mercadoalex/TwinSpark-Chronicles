import { describe, it, expect } from 'vitest';
import { wizardReducer, initialState, ActionTypes, STEP_ORDER } from '../wizardReducer';

// Deep-freeze helper to verify immutability
function deepFreeze(obj) {
  Object.freeze(obj);
  Object.getOwnPropertyNames(obj).forEach((prop) => {
    const val = obj[prop];
    if (val !== null && typeof val === 'object' && !Object.isFrozen(val)) {
      deepFreeze(val);
    }
  });
  return obj;
}

describe('wizardReducer', () => {
  // 7.2 — GO_TO_STEP transition directions
  describe('GO_TO_STEP', () => {
    it('forward navigation produces animation-slide-in-right', () => {
      const state = { ...initialState, wizardStep: 'name' };
      const result = wizardReducer(state, { type: ActionTypes.GO_TO_STEP, step: 'gender' });
      expect(result.wizardStep).toBe('gender');
      expect(result.transitionClass).toBe('animation-slide-in-right');
    });

    it('backward navigation produces animation-slide-in-left', () => {
      const state = { ...initialState, wizardStep: 'spirit' };
      const result = wizardReducer(state, { type: ActionTypes.GO_TO_STEP, step: 'name' });
      expect(result.wizardStep).toBe('name');
      expect(result.transitionClass).toBe('animation-slide-in-left');
    });

    it('same step produces animation-slide-in-right', () => {
      const state = { ...initialState, wizardStep: 'gender' };
      const result = wizardReducer(state, { type: ActionTypes.GO_TO_STEP, step: 'gender' });
      expect(result.transitionClass).toBe('animation-slide-in-right');
    });
  });

  // 7.3 — PICK_GENDER and PICK_SPIRIT
  describe('PICK_GENDER', () => {
    it('sets c1_gender for child 1 and enables sparkle', () => {
      const result = wizardReducer(initialState, { type: ActionTypes.PICK_GENDER, value: 'girl' });
      expect(result.formData.c1_gender).toBe('girl');
      expect(result.bounceCard).toBe('girl');
      expect(result.showSparkle).toBe(true);
    });

    it('sets c2_gender for child 2', () => {
      const state = { ...initialState, childNum: 2 };
      const result = wizardReducer(state, { type: ActionTypes.PICK_GENDER, value: 'boy' });
      expect(result.formData.c2_gender).toBe('boy');
      expect(result.formData.c1_gender).toBe('');
    });
  });

  describe('PICK_SPIRIT', () => {
    it('sets c1_spirit_animal for child 1 and enables sparkle', () => {
      const result = wizardReducer(initialState, { type: ActionTypes.PICK_SPIRIT, value: 'dragon' });
      expect(result.formData.c1_spirit_animal).toBe('dragon');
      expect(result.bounceCard).toBe('dragon');
      expect(result.showSparkle).toBe(true);
    });

    it('sets c2_spirit_animal for child 2', () => {
      const state = { ...initialState, childNum: 2 };
      const result = wizardReducer(state, { type: ActionTypes.PICK_SPIRIT, value: 'phoenix' });
      expect(result.formData.c2_spirit_animal).toBe('phoenix');
    });
  });

  // Costume step and PICK_COSTUME
  describe('PICK_COSTUME', () => {
    it('sets c1_costume for child 1 and enables sparkle', () => {
      const result = wizardReducer(initialState, { type: ActionTypes.PICK_COSTUME, value: 'knight_armor' });
      expect(result.formData.c1_costume).toBe('knight_armor');
      expect(result.bounceCard).toBe('knight_armor');
      expect(result.showSparkle).toBe(true);
    });

    it('sets c2_costume for child 2', () => {
      const state = { ...initialState, childNum: 2 };
      const result = wizardReducer(state, { type: ActionTypes.PICK_COSTUME, value: 'space_suit' });
      expect(result.formData.c2_costume).toBe('space_suit');
      expect(result.formData.c1_costume).toBe('');
    });
  });

  describe('STEP_ORDER includes costume', () => {
    it('has costume between spirit and toy', () => {
      const spiritIdx = STEP_ORDER.indexOf('spirit');
      const costumeIdx = STEP_ORDER.indexOf('costume');
      const toyIdx = STEP_ORDER.indexOf('toy');
      expect(costumeIdx).toBe(spiritIdx + 1);
      expect(costumeIdx).toBe(toyIdx - 1);
    });
  });

  // 7.4 — PICK_PRESET_TOY and SET_TOY_PHOTO
  describe('PICK_PRESET_TOY', () => {
    it('sets toy_type to preset and toy_image to value', () => {
      const result = wizardReducer(initialState, { type: ActionTypes.PICK_PRESET_TOY, value: 'teddy' });
      expect(result.formData.c1_toy_type).toBe('preset');
      expect(result.formData.c1_toy_image).toBe('teddy');
      expect(result.bounceCard).toBe('teddy');
      expect(result.toyPhotoPreview).toBeNull();
      expect(result.toyPhotoFile).toBeNull();
      expect(result.toyError).toBe('');
    });
  });

  describe('SET_TOY_PHOTO', () => {
    it('sets toy_type to photo and clears toy_image', () => {
      const fakeFile = { name: 'toy.png' };
      const result = wizardReducer(initialState, {
        type: ActionTypes.SET_TOY_PHOTO,
        preview: 'data:image/png;base64,abc',
        file: fakeFile,
      });
      expect(result.formData.c1_toy_type).toBe('photo');
      expect(result.formData.c1_toy_image).toBe('');
      expect(result.toyPhotoPreview).toBe('data:image/png;base64,abc');
      expect(result.toyPhotoFile).toBe(fakeFile);
      expect(result.toyError).toBe('');
      expect(result.bounceCard).toBeNull();
    });
  });

  // 7.5 — NEXT_CHILD
  describe('NEXT_CHILD', () => {
    it('resets to child 2, name step, fade-in, clears toy photo state', () => {
      const state = {
        ...initialState,
        wizardStep: 'toy',
        toyPhotoPreview: 'data:image/png;base64,xyz',
        toyPhotoFile: { name: 'file.png' },
        toyError: 'some error',
      };
      const result = wizardReducer(state, { type: ActionTypes.NEXT_CHILD });
      expect(result.childNum).toBe(2);
      expect(result.wizardStep).toBe('name');
      expect(result.transitionClass).toBe('animation-fade-in');
      expect(result.toyPhotoPreview).toBeNull();
      expect(result.toyPhotoFile).toBeNull();
      expect(result.toyError).toBe('');
    });
  });

  // 7.6 — SET_FIELD name clears nameError; non-name does not
  describe('SET_FIELD', () => {
    it('clears nameError when setting name field', () => {
      const state = { ...initialState, nameError: 'Please enter a name' };
      const result = wizardReducer(state, {
        type: ActionTypes.SET_FIELD,
        field: 'c1_name',
        value: 'Luna',
      });
      expect(result.formData.c1_name).toBe('Luna');
      expect(result.nameError).toBe('');
    });

    it('does not clear nameError when setting non-name field', () => {
      const state = { ...initialState, nameError: 'Please enter a name' };
      const result = wizardReducer(state, {
        type: ActionTypes.SET_FIELD,
        field: 'c1_toy_name',
        value: 'Teddy',
      });
      expect(result.formData.c1_toy_name).toBe('Teddy');
      expect(result.nameError).toBe('Please enter a name');
    });
  });

  // 7.7 — Unknown action returns same state reference
  describe('unknown action', () => {
    it('returns the exact same state reference', () => {
      const result = wizardReducer(initialState, { type: 'TOTALLY_UNKNOWN' });
      expect(result).toBe(initialState);
    });
  });

  // 7.8 — Immutability: deep-freeze state before dispatch, verify no mutation
  describe('immutability', () => {
    it('does not mutate state on GO_TO_STEP', () => {
      const frozen = deepFreeze({ ...initialState, formData: { ...initialState.formData } });
      expect(() => wizardReducer(frozen, { type: ActionTypes.GO_TO_STEP, step: 'gender' })).not.toThrow();
    });

    it('does not mutate state on PICK_GENDER', () => {
      const frozen = deepFreeze({ ...initialState, formData: { ...initialState.formData } });
      expect(() => wizardReducer(frozen, { type: ActionTypes.PICK_GENDER, value: 'girl' })).not.toThrow();
    });

    it('does not mutate state on SET_FIELD', () => {
      const frozen = deepFreeze({ ...initialState, formData: { ...initialState.formData } });
      expect(() => wizardReducer(frozen, { type: ActionTypes.SET_FIELD, field: 'c1_name', value: 'X' })).not.toThrow();
    });

    it('does not mutate state on NEXT_CHILD', () => {
      const frozen = deepFreeze({ ...initialState, formData: { ...initialState.formData } });
      expect(() => wizardReducer(frozen, { type: ActionTypes.NEXT_CHILD })).not.toThrow();
    });

    it('does not mutate state on PICK_PRESET_TOY', () => {
      const frozen = deepFreeze({ ...initialState, formData: { ...initialState.formData } });
      expect(() => wizardReducer(frozen, { type: ActionTypes.PICK_PRESET_TOY, value: 'teddy' })).not.toThrow();
    });

    it('does not mutate state on PICK_COSTUME', () => {
      const frozen = deepFreeze({ ...initialState, formData: { ...initialState.formData } });
      expect(() => wizardReducer(frozen, { type: ActionTypes.PICK_COSTUME, value: 'knight_armor' })).not.toThrow();
    });
  });
});
