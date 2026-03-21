# Requirements Document

## Introduction

Character Costume Customization adds an outfit/costume selection step to the character setup wizard in Twin Spark Chronicles. Each sibling picks a costume for their character, which persists across sessions and influences both AI story narration and generated scene images. The feature integrates into the existing setup flow (name → gender → spirit animal → costume → photos) and feeds costume data through the storyteller, visual, and style transfer agents.

## Glossary

- **Costume_Selector**: The UI component in the character setup wizard that presents costume options as tappable cards for each sibling to choose from.
- **Costume_Record**: The persisted data structure storing a sibling's chosen costume, including the costume identifier and display metadata.
- **Costume_Catalog**: The predefined collection of available costume options, each with an identifier, display name, emoji, color theme, and descriptive text for AI prompt injection.
- **Character_Setup_Wizard**: The existing multi-step setup flow where siblings enter name, gender, and spirit animal — extended with a costume step.
- **Storyteller_Agent**: The AI agent that generates story narration text using Gemini 2.0, referencing character attributes in its prompts.
- **Visual_Agent**: The AI agent that generates scene images, including character appearance descriptions in its image prompts.
- **Style_Transfer_Agent**: The agent that generates illustrated character portraits from face photos, applying costume details to the portrait style.
- **Orchestrator**: The backend coordinator that passes character context (including costume) to all downstream agents.
- **Session_Snapshot**: The persisted session state (in the session_snapshots table) that includes character profiles and story progress.
- **Sibling_Pair_ID**: The unique identifier for a pair of siblings, used to scope costume persistence.

## Requirements

### Requirement 1: Costume Catalog Definition

**User Story:** As a developer, I want a predefined catalog of costume options, so that siblings have a curated set of age-appropriate outfits to choose from.

#### Acceptance Criteria

1. THE Costume_Catalog SHALL contain a minimum of 8 costume options.
2. WHEN the Costume_Catalog is loaded, THE Costume_Selector SHALL present each costume with a unique identifier, display name, emoji icon, theme color, and a descriptive prompt fragment for AI agents.
3. THE Costume_Catalog SHALL include costumes spanning fantasy, adventure, and everyday themes (e.g., knight armor, space suit, princess gown, pirate outfit, superhero cape, wizard robe, explorer gear, fairy wings).
4. THE Costume_Catalog SHALL assign each costume a prompt fragment of 20 words or fewer that the Storyteller_Agent and Visual_Agent can inject into their prompts.

### Requirement 2: Costume Selection UI

**User Story:** As a sibling (age 6), I want to pick a costume for my character by tapping a big colorful card, so that I can express my creativity during setup.

#### Acceptance Criteria

1. WHEN the Character_Setup_Wizard reaches the costume step, THE Costume_Selector SHALL display all available costumes as tappable cards in a grid layout.
2. THE Costume_Selector SHALL render each card with a minimum tap target of 44×44 CSS pixels.
3. WHEN a sibling taps a costume card, THE Costume_Selector SHALL apply a bounce animation and advance to the next setup step within 500 milliseconds.
4. THE Costume_Selector SHALL use CSS-first animations consistent with the existing wizard card style (bounce, slide transitions).
5. THE Costume_Selector SHALL include ARIA labels on each costume card describing the costume name for screen readers.
6. THE Costume_Selector SHALL support keyboard navigation, allowing selection via Enter or Space keys.
7. WHILE the costume step is active, THE Costume_Selector SHALL display the sibling's name and child badge consistent with other wizard steps.

### Requirement 3: Costume Step Integration in Setup Flow

**User Story:** As a sibling, I want the costume step to appear naturally after picking my spirit animal, so that the setup flow feels seamless.

#### Acceptance Criteria

1. WHEN a sibling completes the spirit animal step for child 1, THE Character_Setup_Wizard SHALL transition to the costume step for child 1.
2. WHEN a sibling completes the costume step for child 1, THE Character_Setup_Wizard SHALL transition to the name step for child 2.
3. WHEN a sibling completes the spirit animal step for child 2, THE Character_Setup_Wizard SHALL transition to the costume step for child 2.
4. WHEN a sibling completes the costume step for child 2, THE Character_Setup_Wizard SHALL transition to the photos step.
5. THE Character_Setup_Wizard SHALL include the costume step in the progress indicator dots.
6. THE Character_Setup_Wizard SHALL include costume data (c1_costume, c2_costume) in the formData passed to the onComplete callback.

### Requirement 4: Costume Data Model

**User Story:** As a developer, I want costume data modeled as a character attribute, so that it flows through the system like spirit_animal and toy_name.

#### Acceptance Criteria

1. THE CharacterData model SHALL include an optional costume field of type string.
2. THE Costume_Record SHALL store the costume identifier as a string matching a Costume_Catalog entry.
3. WHEN a session is started, THE Orchestrator SHALL include each sibling's costume in the character context dictionary passed to all agents.
4. IF a sibling has no costume selected, THEN THE Orchestrator SHALL use a default value of "adventure_clothes" in the character context.

### Requirement 5: Costume Persistence

**User Story:** As a sibling, I want my costume choice to be remembered next time we play, so that I don't have to pick again every session.

#### Acceptance Criteria

1. WHEN a sibling selects a costume, THE Character_Setup_Wizard SHALL include the costume value in the character profile data sent to the backend.
2. THE Session_Snapshot SHALL persist costume data as part of the character_profiles JSON field.
3. WHEN a session is resumed from a snapshot, THE Orchestrator SHALL restore each sibling's costume from the persisted character_profiles.
4. THE Costume_Record SHALL be scoped to the Sibling_Pair_ID, allowing each sibling pair to have independent costume selections.

### Requirement 6: Costume in Story Narration

**User Story:** As a sibling, I want the AI storyteller to mention what my character is wearing, so that the story feels personalized to my costume choice.

#### Acceptance Criteria

1. WHEN generating a story segment, THE Storyteller_Agent SHALL include each sibling's costume prompt fragment in the CHARACTER INFO section of the story prompt.
2. THE Storyteller_Agent SHALL reference the costume naturally in narration (e.g., "Ale adjusted her knight armor as she stepped into the cave") at least once per story scene.
3. IF a costume prompt fragment is missing from the character context, THEN THE Storyteller_Agent SHALL fall back to "adventure clothes" in the prompt.

### Requirement 7: Costume in Scene Images

**User Story:** As a sibling, I want to see my character wearing the costume I picked in the story pictures, so that the images match my choices.

#### Acceptance Criteria

1. WHEN generating a scene image prompt, THE Visual_Agent SHALL replace the hardcoded outfit description with the sibling's costume prompt fragment from the character context.
2. THE Visual_Agent SHALL include the costume description for both siblings in every scene image prompt.
3. IF a costume prompt fragment is missing from the character context, THEN THE Visual_Agent SHALL fall back to the current default outfit descriptions.

### Requirement 8: Costume in Character Portraits

**User Story:** As a sibling, I want my character portrait to show my chosen costume, so that my avatar looks like the character I imagined.

#### Acceptance Criteria

1. WHEN generating a style-transferred portrait, THE Style_Transfer_Agent SHALL append the costume prompt fragment to the style transfer prompt.
2. IF a costume is selected after a portrait has been cached, THEN THE Style_Transfer_Agent SHALL invalidate the cached portrait for that sibling so a new portrait reflecting the costume is generated.
3. IF no costume is selected, THEN THE Style_Transfer_Agent SHALL use the existing default prompt without costume modifications.

### Requirement 9: Costume Change from Parent Dashboard

**User Story:** As a parent, I want to be able to change my children's costumes between sessions, so that the experience stays fresh without re-running full setup.

#### Acceptance Criteria

1. THE ParentDashboard SHALL display each sibling's current costume selection.
2. WHEN a parent taps a sibling's costume display, THE ParentDashboard SHALL open the Costume_Selector allowing a new costume choice.
3. WHEN a parent confirms a costume change, THE ParentDashboard SHALL persist the updated costume to the character profile.
4. WHEN a costume is changed via the ParentDashboard, THE Style_Transfer_Agent SHALL invalidate any cached portrait for the affected sibling.
