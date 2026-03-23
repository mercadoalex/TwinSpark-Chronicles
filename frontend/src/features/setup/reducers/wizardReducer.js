export const STEP_ORDER = ['name', 'gender', 'spirit', 'costume', 'toy', 'photos'];

export const ActionTypes = {
  GO_TO_STEP:       'GO_TO_STEP',
  SET_FIELD:        'SET_FIELD',
  SET_NAME_ERROR:   'SET_NAME_ERROR',
  SET_TOY_ERROR:    'SET_TOY_ERROR',
  PICK_GENDER:      'PICK_GENDER',
  PICK_SPIRIT:      'PICK_SPIRIT',
  PICK_COSTUME:     'PICK_COSTUME',
  PICK_PRESET_TOY:  'PICK_PRESET_TOY',
  SET_TOY_PHOTO:    'SET_TOY_PHOTO',
  NEXT_CHILD:       'NEXT_CHILD',
  CLEAR_BOUNCE:     'CLEAR_BOUNCE',
  SHOW_SPARKLE:     'SHOW_SPARKLE',
  HIDE_SPARKLE:     'HIDE_SPARKLE',
  SET_PHOTO_REFRESH:'SET_PHOTO_REFRESH',
  SET_TRANSITION:   'SET_TRANSITION',
};

export const initialState = {
  childNum: 1,
  wizardStep: 'name',
  formData: {
    c1_name: '', c1_gender: '', c1_spirit_animal: '', c1_costume: '', c1_toy_name: '',
    c1_toy_type: '', c1_toy_image: '',
    c2_name: '', c2_gender: '', c2_spirit_animal: '', c2_costume: '', c2_toy_name: '',
    c2_toy_type: '', c2_toy_image: '',
  },
  bounceCard: null,
  photoRefreshKey: 0,
  transitionClass: 'animation-fade-in',
  nameError: '',
  showSparkle: false,
  toyPhotoPreview: null,
  toyPhotoFile: null,
  toyError: '',
};

export function wizardReducer(state, action) {
  const prefix = `c${state.childNum}_`;

  switch (action.type) {
    case ActionTypes.GO_TO_STEP: {
      const curIdx = STEP_ORDER.indexOf(state.wizardStep);
      const nextIdx = STEP_ORDER.indexOf(action.step);
      return {
        ...state,
        wizardStep: action.step,
        transitionClass: nextIdx >= curIdx
          ? 'animation-slide-in-right'
          : 'animation-slide-in-left',
      };
    }

    case ActionTypes.SET_FIELD: {
      const newFormData = { ...state.formData, [action.field]: action.value };
      const clearNameError = action.field === `${prefix}name` ? '' : state.nameError;
      return {
        ...state,
        formData: newFormData,
        nameError: clearNameError,
        bounceCard: action.value,
      };
    }

    case ActionTypes.SET_NAME_ERROR:
      return { ...state, nameError: action.error };

    case ActionTypes.SET_TOY_ERROR:
      return { ...state, toyError: action.error };

    case ActionTypes.PICK_GENDER:
      return {
        ...state,
        formData: { ...state.formData, [`${prefix}gender`]: action.value },
        bounceCard: action.value,
        showSparkle: true,
      };

    case ActionTypes.PICK_SPIRIT:
      return {
        ...state,
        formData: { ...state.formData, [`${prefix}spirit_animal`]: action.value },
        bounceCard: action.value,
        showSparkle: true,
      };

    case ActionTypes.PICK_COSTUME:
      return {
        ...state,
        formData: { ...state.formData, [`${prefix}costume`]: action.value },
        bounceCard: action.value,
        showSparkle: true,
      };

    case ActionTypes.PICK_PRESET_TOY:
      return {
        ...state,
        formData: {
          ...state.formData,
          [`${prefix}toy_type`]: 'preset',
          [`${prefix}toy_image`]: action.value,
        },
        bounceCard: action.value,
        toyPhotoPreview: null,
        toyPhotoFile: null,
        toyError: '',
      };

    case ActionTypes.SET_TOY_PHOTO:
      return {
        ...state,
        formData: {
          ...state.formData,
          [`${prefix}toy_type`]: 'photo',
          [`${prefix}toy_image`]: '',
        },
        toyPhotoPreview: action.preview,
        toyPhotoFile: action.file,
        toyError: '',
        bounceCard: null,
      };

    case ActionTypes.NEXT_CHILD:
      return {
        ...state,
        childNum: 2,
        wizardStep: 'name',
        transitionClass: 'animation-fade-in',
        toyPhotoPreview: null,
        toyPhotoFile: null,
        toyError: '',
      };

    case ActionTypes.CLEAR_BOUNCE:
      return { ...state, bounceCard: null };

    case ActionTypes.SHOW_SPARKLE:
      return { ...state, showSparkle: true };

    case ActionTypes.HIDE_SPARKLE:
      return { ...state, showSparkle: false };

    case ActionTypes.SET_PHOTO_REFRESH:
      return { ...state, photoRefreshKey: state.photoRefreshKey + 1 };

    case ActionTypes.SET_TRANSITION:
      return { ...state, transitionClass: action.className };

    default:
      return state;
  }
}
