# Implementation Plan: Character Costume Customization

## Overview

Add a costume selection step to the character setup wizard, positioned between spirit animal and toy companion. A static costume catalog provides 8+ age-appropriate outfits that flow through the orchestrator into storyteller, visual, and style transfer agents. Parents can swap costumes via the parent dashboard. Implementation starts with the shared catalog, then frontend wizard changes, then backend agent integration, then parent dashboard and cache invalidation.

## Tasks

- [x] 1. Create costume catalog and data layer
  - [x] 1.1 Create frontend costume catalog
    - Create `frontend/src/features/setup/data/costumeCatalog.js`
    - Export a static array of 8+ costume entries, each with `id`, `label`, `emoji`, `color`, `promptFragment`
    - Include costumes spanning fantasy, adventure, and everyday themes (knight armor, space suit, princess gown, pirate outfit, superhero cape, wizard robe, explorer gear, fairy wings)
    - Ensure all `promptFragment` values are ≤20 words
    - _Requirements: 1.1, 1.2, 1.3, 1.4_

  - [x] 1.2 Create backend costume catalog mirror
    - Create `backend/app/data/costume_catalog.py`
    - Define `COSTUME_CATALOG` dict keyed by costume ID, each with `label`, `emoji`, `prompt_fragment`
    - Include a `get_costume_prompt(costume_id)` helper that returns the prompt fragment or the default `"wearing adventure clothes"`
    - Include a `is_valid_costume(costume_id)` validation helper
    - _Requirements: 1.2, 1.4, 4.2, 4.4_

  - [ ]* 1.3 Write property test for catalog well-formedness (frontend)
    - **Property 1: Catalog entries are well-formed**
    - **Validates: Requirements 1.2, 1.4**
    - Use fast-check with `numRuns: 100`, verify all entries have non-empty fields, unique IDs, promptFragment ≤20 words

  - [ ]* 1.4 Write property test for valid catalog entry (backend)
    - **Property 4: Stored costume ID is a valid catalog entry**
    - **Validates: Requirements 4.2**
    - Use Hypothesis with `max_examples=100`, generate random strings, verify only catalog IDs pass `is_valid_costume`

- [x] 2. Implement CostumeSelector component and wizard integration
  - [x] 2.1 Create CostumeSelector component
    - Create `frontend/src/features/setup/components/CostumeSelector.jsx`
    - Render a grid of tappable costume cards from the catalog
    - Each card: `<button>` with `aria-label` containing costume label, minimum 44×44px tap target
    - On tap: apply `wizard-card--bounce` animation, call `onSelect(costumeId)` after 350ms
    - Support keyboard selection via Enter/Space
    - Display child badge (name + emoji) consistent with other wizard steps
    - Props: `childNum`, `childName`, `childColor`, `childEmoji`, `onSelect`, `renderProgress`, `transitionClass`
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7_

  - [x] 2.2 Update wizard reducer for costume step
    - In `frontend/src/features/setup/reducers/wizardReducer.js`:
    - Add `'costume'` to `STEP_ORDER` between `'spirit'` and `'toy'`
    - Add `PICK_COSTUME` action type
    - Add `c1_costume: ''` and `c2_costume: ''` to `initialState.formData`
    - Implement `PICK_COSTUME` handler: set `formData[prefix + 'costume']`, trigger bounce + sparkle, transition to `'toy'` after 500ms
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

  - [x] 2.3 Integrate CostumeSelector into CharacterSetup
    - In `frontend/src/features/setup/components/CharacterSetup.jsx`:
    - Import `CostumeSelector` and `costumeCatalog`
    - Add `stepLabels.costume = 'Costume'`
    - Add `wizardStep === 'costume'` branch rendering `<CostumeSelector>`
    - Update `handleSpiritPick` to transition to `'costume'` instead of `'toy'`
    - Add `handleCostumePick(val)` dispatching `PICK_COSTUME`, then `GO_TO_STEP` to `'toy'` after 500ms
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

  - [ ]* 2.4 Write property test for ARIA labels
    - **Property 2: ARIA labels match costume names**
    - **Validates: Requirements 2.5**
    - Use fast-check with `numRuns: 100`, verify each rendered button has aria-label containing the costume label

  - [ ]* 2.5 Write property test for wizard formData
    - **Property 3: Wizard formData includes costume selections**
    - **Validates: Requirements 3.6, 5.1**
    - Use fast-check with `numRuns: 100`, verify formData contains c1_costume and c2_costume matching selected IDs

- [x] 3. Checkpoint — Verify frontend wizard flow
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Update stores and enriched profiles
  - [x] 4.1 Add costume field to setupStore
    - In `frontend/src/stores/setupStore.js`:
    - Add `costume: ''` to `child1` and `child2` objects
    - Update `getProfiles()` to include `c1_costume` and `c2_costume`
    - Update `reset()` to clear costume fields
    - Existing `persist` middleware already partializes child objects
    - _Requirements: 4.1, 5.1_

  - [x] 4.2 Enrich profiles with costume data in SetupScreen
    - In `frontend/src/features/setup/components/SetupScreen.jsx`:
    - In `handleSetupComplete`, map `profiles.c1_costume` and `profiles.c2_costume` into `enrichedProfiles`
    - Look up `promptFragment` from catalog for each costume ID
    - Fall back to `"adventure_clothes"` if no costume selected
    - _Requirements: 4.1, 4.2, 5.1_

- [x] 5. Backend orchestrator costume injection
  - [x] 5.1 Inject costume into character context
    - In the orchestrator's character context building logic:
    - Read `costume` from character profiles for each child
    - Use `get_costume_prompt(costume_id)` to resolve `costume_prompt`
    - Default to `"adventure_clothes"` / `"wearing adventure clothes"` if missing
    - Add `costume` and `costume_prompt` keys to each child's context dict
    - _Requirements: 4.3, 4.4_

  - [ ]* 5.2 Write property test for orchestrator costume injection
    - **Property 5: Orchestrator injects costume into character context**
    - **Validates: Requirements 4.3, 4.4**
    - Use Hypothesis with `max_examples=100`, generate profiles with/without costume, verify context always has correct costume_prompt

  - [ ]* 5.3 Write property test for costume persistence round-trip
    - **Property 6: Costume persistence round-trip**
    - **Validates: Requirements 5.2, 5.3**
    - Use Hypothesis with `max_examples=100`, save snapshot with costume, load back, verify equality

  - [ ]* 5.4 Write property test for sibling pair isolation
    - **Property 7: Sibling pair costume isolation**
    - **Validates: Requirements 5.4**
    - Use Hypothesis with `max_examples=100`, update costume for one pair, verify other pair unchanged

- [x] 6. Agent prompt modifications
  - [x] 6.1 Update StorytellerAgent prompt
    - In `StorytellerAgent._build_prompt`:
    - Append `costume_prompt` to each character's line in the CHARACTER INFO section
    - Fall back to `"wearing adventure clothes"` if `costume_prompt` missing
    - _Requirements: 6.1, 6.3_

  - [x] 6.2 Update VisualAgent prompt
    - In `VisualAgent._build_visual_prompt`:
    - Replace hardcoded `"wearing adventure clothes"` / `"wearing explorer outfit"` with `c1.get('costume_prompt', 'wearing adventure clothes')` and `c2.get('costume_prompt', 'wearing explorer outfit')`
    - _Requirements: 7.1, 7.2, 7.3_

  - [x] 6.3 Update StyleTransferAgent prompt
    - In `StyleTransferAgent.generate_portrait`:
    - Append `costume_prompt` to the style transfer prompt
    - Fall back to existing default if no costume set
    - _Requirements: 8.1, 8.3_

  - [ ]* 6.4 Write property test for storyteller prompt
    - **Property 8: Storyteller prompt contains costume fragment**
    - **Validates: Requirements 6.1, 6.3**
    - Use Hypothesis with `max_examples=100`, generate character contexts with costume_prompt, verify substring in built prompt

  - [ ]* 6.5 Write property test for visual prompt
    - **Property 9: Visual prompt contains both costume fragments**
    - **Validates: Requirements 7.1, 7.2, 7.3**
    - Use Hypothesis with `max_examples=100`, generate pairs of costume_prompts, verify both substrings in built prompt

  - [ ]* 6.6 Write property test for style transfer prompt
    - **Property 10: Style transfer prompt contains costume fragment**
    - **Validates: Requirements 8.1, 8.3**
    - Use Hypothesis with `max_examples=100`, generate costume_prompt strings, verify presence in generated prompt

- [x] 7. Checkpoint — Verify agent integration
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Cache invalidation and parent dashboard
  - [x] 8.1 Add cache invalidation on costume change
    - When costume changes (via parent dashboard or re-setup), call `StyleTransferCache.evict(face_content_hash)` for the affected sibling
    - _Requirements: 8.2, 9.4_

  - [x] 8.2 Create PUT /api/costume endpoint
    - Add `PUT /api/costume/{sibling_pair_id}/{child_num}` to `backend/app/main.py`
    - Body: `{ "costume": "knight_armor" }`
    - Validate costume ID against `COSTUME_CATALOG`, return 422 for invalid IDs
    - Update `character_profiles` JSON in `session_snapshots`
    - Evict style transfer cache for the affected sibling
    - Return `{ "ok": true, "costume": "...", "costume_prompt": "..." }`
    - Return 404 for non-existent sibling_pair_id
    - _Requirements: 9.3, 9.4_

  - [x] 8.3 Add costume display and change to ParentDashboard
    - Display current costume (emoji + label) for each sibling
    - On tap, open CostumeSelector modal/overlay
    - On confirm, call `PUT /api/costume/{sibling_pair_id}/{child_num}`
    - Update UI on success
    - _Requirements: 9.1, 9.2, 9.3_

  - [ ]* 8.4 Write property test for cache invalidation
    - **Property 11: Cache invalidation on costume change**
    - **Validates: Requirements 8.2, 9.4**
    - Use Hypothesis with `max_examples=100`, put portrait in cache, evict by face hash, verify cache miss

  - [ ]* 8.5 Write property test for dashboard update persistence
    - **Property 12: Dashboard costume update persists**
    - **Validates: Requirements 9.3**
    - Use Hypothesis with `max_examples=100`, submit valid costume via PUT, verify snapshot reflects new value

- [x] 9. Final checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property tests validate universal correctness properties from the design document
- Backend tests use Hypothesis with `max_examples=100`; frontend property tests use fast-check with `numRuns: 100`
- No new database tables or migrations needed — costume data lives in the existing `character_profiles` JSON column
- Run frontend tests with: `npm run test` from `frontend/` directory (vitest --run)
- Run backend tests with: `source venv/bin/activate && python3 -m pytest tests/ -x -q --tb=short` from `backend/` directory
- After pytest: `pkill -f "python.*pytest"` (CacheManager cleanup loop causes hang)
