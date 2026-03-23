# Requirements Document

## Introduction

The Toy Companion Visual feature brings each child's toy companion to life within Twin Spark Chronicles. Currently the toy companion fields (`c1_toy`, `c2_toy`) exist in the data model but are invisible — defaulting to "Bruno" and "Book" with no setup UI and no visual presence during stories. This feature adds a dedicated setup wizard step where each child picks and names their toy companion, optionally photographs their real toy, and then sees that toy as a floating sidekick avatar during story playback.

## Glossary

- **Setup_Wizard**: The multi-step character creation flow in `CharacterSetup.jsx` that guides children through name, gender, spirit animal, and photo steps.
- **Toy_Step**: A new wizard step inserted into the Setup_Wizard between the spirit animal step and the photos step, where each child configures their toy companion.
- **Toy_Companion**: A named toy character associated with a child, represented by either a user-uploaded photo or a preset illustration.
- **Toy_Photo**: A user-captured or uploaded image of a child's real physical toy, stored on the backend.
- **Preset_Toy**: A predefined toy type (e.g., teddy bear, robot, bunny) with an emoji or illustration, used as a fallback when no Toy_Photo is provided.
- **Companion_Avatar**: A small floating visual element displayed on the story scene in `DualStoryDisplay`, representing a child's Toy_Companion.
- **Toy_Service**: A backend service responsible for storing, retrieving, and serving Toy_Photo images and Toy_Companion metadata.
- **DualStoryDisplay**: The React component that renders the cinematic story scene, narration, perspectives, and choice cards.
- **Photo_Capture**: The process of using the device camera or file picker to acquire a Toy_Photo image.

## Requirements

### Requirement 1: Toy Companion Setup Step

**User Story:** As a child (age 6), I want to pick and name my toy companion during setup, so that my favorite toy becomes part of my story adventure.

#### Acceptance Criteria

1. WHEN the spirit animal step completes for a child, THE Setup_Wizard SHALL navigate to the Toy_Step before proceeding to the photos step.
2. THE Toy_Step SHALL display a text input for the toy companion name, pre-populated with the existing default value ("Bruno" for child 1, "Book" for child 2).
3. WHEN the child enters a toy name, THE Toy_Step SHALL accept names between 1 and 20 characters in length.
4. THE Toy_Step SHALL display a grid of Preset_Toy options, each represented by a large emoji and a label (teddy bear 🧸, robot 🤖, bunny 🐰, dinosaur 🦕, kitty 🐱, puppy 🐶).
5. WHEN the child taps a Preset_Toy card, THE Toy_Step SHALL select that preset and apply a visual bounce animation consistent with existing wizard card interactions.
6. THE Toy_Step SHALL display a Photo_Capture button that allows the child to take or upload a photo of their real toy.
7. WHEN a Toy_Photo is successfully captured, THE Toy_Step SHALL display a circular thumbnail preview of the captured image and deselect any previously selected Preset_Toy.
8. WHEN the child has provided a toy name and either selected a Preset_Toy or captured a Toy_Photo, THE Toy_Step SHALL enable a "Next" button to proceed.
9. IF the child taps "Next" without providing a toy name, THEN THE Toy_Step SHALL display an inline validation message prompting for a name.

### Requirement 2: Toy Photo Capture and Upload

**User Story:** As a child, I want to take a photo of my real toy, so that my actual toy appears as a character in the story.

#### Acceptance Criteria

1. WHEN the child taps the Photo_Capture button, THE Toy_Step SHALL open the device camera or file picker using an HTML file input with `accept="image/*"` and `capture="environment"` attributes.
2. WHEN an image file is selected, THE Toy_Step SHALL validate that the file size is at most 10 MB.
3. IF the selected file exceeds 10 MB, THEN THE Toy_Step SHALL display an error message "Photo is too big! Try a smaller one 📸" and discard the file.
4. WHEN a valid image is selected, THE Toy_Step SHALL display a circular thumbnail preview of the image within 500 ms.
5. WHEN the child confirms the Toy_Step, THE Toy_Service SHALL upload the Toy_Photo to the backend and store it in the `assets/toy_photos/` directory.
6. THE Toy_Service SHALL resize uploaded Toy_Photo images to a maximum dimension of 512 pixels while preserving aspect ratio.
7. THE Toy_Service SHALL return a URL path for the stored Toy_Photo that the frontend can use to display the image.

### Requirement 3: Toy Photo Backend Storage

**User Story:** As the system, I want to persist toy companion data, so that toy photos and metadata survive across sessions.

#### Acceptance Criteria

1. THE Toy_Service SHALL expose a `POST /api/toy-photo/{sibling_pair_id}/{child_number}` endpoint that accepts a multipart image upload.
2. THE Toy_Service SHALL expose a `GET /api/toy-photo/{sibling_pair_id}/{child_number}` endpoint that returns the stored Toy_Photo metadata including the image URL.
3. THE Toy_Service SHALL validate uploaded images using the same image validation logic as the existing Photo_Service (file type, file size, image integrity).
4. THE Toy_Service SHALL store Toy_Photo metadata (child number, file path, original filename, upload timestamp) in a JSON sidecar file alongside the image.
5. WHEN a new Toy_Photo is uploaded for a child that already has one, THE Toy_Service SHALL replace the previous Toy_Photo and delete the old file from disk.
6. IF the uploaded file is not a valid image, THEN THE Toy_Service SHALL return an HTTP 400 response with a descriptive error message.

### Requirement 4: Toy Companion Data in Setup Store

**User Story:** As a developer, I want toy companion data persisted in the Zustand setup store, so that it flows through to the story session.

#### Acceptance Criteria

1. THE Setup_Wizard SHALL store the selected toy name, toy type (preset or photo), and toy image URL for each child in the form data.
2. WHEN setup completes, THE Setup_Wizard SHALL include `c1_toy_name`, `c1_toy_type`, `c1_toy_image`, `c2_toy_name`, `c2_toy_type`, and `c2_toy_image` in the enriched profiles object.
3. THE useSetupStore SHALL persist `toy`, `toyType`, and `toyImage` fields for each child alongside existing fields (name, gender, personality, spirit).
4. WHEN the app reloads with persisted setup data, THE useSetupStore SHALL restore toy companion data from local storage.

### Requirement 5: Companion Avatar in Story Display

**User Story:** As a child, I want to see my toy companion floating next to my name during the story, so that my toy feels like a real sidekick in the adventure.

#### Acceptance Criteria

1. THE DualStoryDisplay SHALL render a Companion_Avatar adjacent to each child's existing floating avatar on the story scene.
2. WHEN a child has a Toy_Photo, THE Companion_Avatar SHALL display the Toy_Photo as a circular image with a 40px diameter.
3. WHEN a child has a Preset_Toy and no Toy_Photo, THE Companion_Avatar SHALL display the preset emoji at a size matching the avatar style.
4. THE Companion_Avatar SHALL float with a gentle bobbing animation offset from the child avatar's animation by 0.5 seconds.
5. THE Companion_Avatar SHALL include a subtle glow border matching the child's theme color (pink for child 1, blue for child 2).
6. WHEN the story scene has no image loaded, THE Companion_Avatar SHALL not be rendered.

### Requirement 6: Companion Avatar in Perspective Cards

**User Story:** As a child, I want to see my toy companion next to my name in the perspective cards, so that my toy is always with me in the story.

#### Acceptance Criteria

1. WHEN the perspective cards are expanded, THE DualStoryDisplay SHALL display the Companion_Avatar next to each child's name emoji in the perspective card header.
2. WHEN a child has a Toy_Photo, THE perspective card Companion_Avatar SHALL display the Toy_Photo as a 28px circular image.
3. WHEN a child has a Preset_Toy and no Toy_Photo, THE perspective card Companion_Avatar SHALL display the preset emoji at 1.2rem font size.

### Requirement 7: Toy Step Accessibility and Child-Friendliness

**User Story:** As a 6-year-old child who is learning to read, I want the toy setup step to be very visual with minimal text, so that I can use it without help.

#### Acceptance Criteria

1. THE Toy_Step SHALL use emoji and illustrations as the primary communication method, with text labels as secondary.
2. THE Toy_Step SHALL use a minimum tap target size of 48px for all interactive elements.
3. THE Toy_Step SHALL provide `aria-label` attributes on all interactive elements describing their purpose.
4. THE Toy_Step SHALL support gamepad navigation using the existing `useGamepad` hook and `FocusNavigator` component.
5. WHEN a Preset_Toy card receives gamepad focus, THE Toy_Step SHALL apply a visible focus ring consistent with existing wizard card focus styles.

### Requirement 8: Toy Companion Data in Story Context

**User Story:** As the AI story engine, I want to receive toy companion names and types, so that the AI can reference the toy companions in generated story text.

#### Acceptance Criteria

1. WHEN a story session starts, THE session profiles SHALL include `c1_toy`, `c1_toy_type`, `c1_toy_image`, `c2_toy`, `c2_toy_type`, and `c2_toy_image` fields.
2. THE CharacterData backend model SHALL include `toy_type` and `toy_image_url` optional fields alongside the existing `toy_name` field.
3. WHEN the AI generates story text, THE story context SHALL include each child's toy companion name so the AI can weave the toy into the narrative.
