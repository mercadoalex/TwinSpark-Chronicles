# Requirements Document

## Introduction

Family Photo Integration enables parents and children to upload real family photos and have them woven into AI-generated story scenes. Instead of generic illustrated characters, the story features recognizable family members — making each adventure deeply personal and delivering a premium "WOOOAW" experience for young children (target age 6). The feature spans photo capture/upload, face extraction, content safety scanning of uploaded images, style-transfer into the Pixar/Disney illustration aesthetic, and seamless compositing into scene images produced by the Visual Storytelling Agent.

## Glossary

- **Photo_Uploader**: The frontend component that allows a parent or child to capture or select family photos via camera or gallery picker.
- **Photo_Service**: The backend service responsible for receiving, validating, storing, and managing uploaded family photos.
- **Face_Extractor**: The backend module that detects and extracts individual face regions from an uploaded family photo.
- **Content_Scanner**: The subsystem (extending the existing ContentFilter) that scans uploaded images for age-appropriateness and safety before they enter the pipeline.
- **Style_Transfer_Agent**: The backend agent that transforms a cropped face photo into a Pixar/Disney-style illustrated character portrait consistent with the story's art direction, leveraging Imagen 3.
- **Scene_Compositor**: The module within the Visual Storytelling Agent that composites style-transferred family member portraits into generated scene illustrations.
- **Photo_Store**: The persistent storage layer (via DatabaseConnection) that holds photo metadata and binary blobs (or file-system references) for uploaded family photos.
- **Family_Member**: A person identified in an uploaded photo who can be mapped to a story character.
- **Character_Mapping**: The association between a Family_Member and a story character role (e.g., "Ale → brave explorer", "Grandma → wise guide").
- **Photo_Gallery**: The UI view where parents can review, label, and manage all uploaded family photos before starting a story.

## Requirements

### Requirement 1: Photo Upload

**User Story:** As a parent, I want to upload family photos from my device camera or gallery, so that my children's stories feature real family members.

#### Acceptance Criteria

1. WHEN a parent taps the photo upload button, THE Photo_Uploader SHALL present options to capture a new photo via the device camera or select an existing photo from the device gallery.
2. WHEN a photo is selected or captured, THE Photo_Uploader SHALL display a preview of the photo and a confirm/retake control before uploading.
3. WHEN a confirmed photo is submitted, THE Photo_Service SHALL accept images in JPEG or PNG format with a maximum file size of 10 MB.
4. IF an uploaded file exceeds 10 MB or is not in JPEG or PNG format, THEN THE Photo_Service SHALL reject the upload and return a descriptive error message indicating the constraint violated.
5. WHEN a valid photo is received, THE Photo_Service SHALL resize the image to a maximum dimension of 1024 pixels on the longest side while preserving the aspect ratio.
6. WHEN a photo is successfully processed, THE Photo_Service SHALL store the image data and metadata in the Photo_Store and return a unique photo identifier to the client.
7. THE Photo_Uploader SHALL provide drag-and-drop upload support on desktop browsers in addition to the tap-based flow.

### Requirement 2: Content Safety for Photos

**User Story:** As a parent, I want uploaded photos to be scanned for safety, so that only age-appropriate images enter the storytelling pipeline.

#### Acceptance Criteria

1. WHEN a photo is received by the Photo_Service, THE Content_Scanner SHALL scan the image for inappropriate or unsafe content before any further processing occurs.
2. IF the Content_Scanner rates an image as BLOCKED, THEN THE Photo_Service SHALL reject the photo, delete any temporary data, and return a parent-friendly message explaining the rejection without exposing explicit details.
3. IF the Content_Scanner rates an image as REVIEW, THEN THE Photo_Service SHALL flag the photo for parent approval before the photo becomes available for story use.
4. WHEN the Content_Scanner rates an image as SAFE, THE Photo_Service SHALL proceed with face extraction and storage.
5. THE Content_Scanner SHALL complete image safety analysis within 3 seconds per photo under normal network conditions.

### Requirement 3: Face Detection and Extraction

**User Story:** As a parent, I want the system to automatically detect faces in my uploaded photos, so that each family member can be individually mapped to a story character.

#### Acceptance Criteria

1. WHEN a photo passes content safety scanning, THE Face_Extractor SHALL detect all human faces present in the image.
2. WHEN faces are detected, THE Face_Extractor SHALL crop each face into an individual portrait with consistent padding (20% margin around the face bounding box).
3. IF no faces are detected in an uploaded photo, THEN THE Face_Extractor SHALL notify the parent that no faces were found and suggest uploading a clearer photo.
4. WHEN face portraits are extracted, THE Face_Extractor SHALL store each portrait in the Photo_Store linked to the original photo identifier.
5. THE Face_Extractor SHALL detect faces in photos containing between 1 and 10 people.

### Requirement 4: Family Member Labeling and Character Mapping

**User Story:** As a parent, I want to label detected faces with family member names and assign them to story character roles, so that the AI knows who is who in the story.

#### Acceptance Criteria

1. WHEN face portraits are extracted, THE Photo_Gallery SHALL display each detected face as a card with an editable name label field.
2. WHEN a parent enters a name for a face portrait, THE Photo_Gallery SHALL save the Family_Member name to the Photo_Store.
3. WHEN a story session is being configured, THE Character_Mapping component SHALL present a list of available Family_Members and allow the parent to assign each Family_Member to a story character role.
4. THE Character_Mapping component SHALL require at minimum the two sibling protagonists to be mapped to Family_Members before a story session can start with photo integration enabled.
5. IF a parent does not assign a Family_Member to a character role, THEN THE Character_Mapping component SHALL allow the story to proceed using the default AI-generated avatar for that role.
6. WHEN a Character_Mapping is saved, THE Photo_Service SHALL persist the mapping in the Photo_Store associated with the sibling pair identifier.

### Requirement 5: Style Transfer — Photo to Illustration

**User Story:** As a parent, I want family member photos to be transformed into the story's Pixar/Disney illustration style, so that real faces blend naturally into the story art.

#### Acceptance Criteria

1. WHEN a Character_Mapping is finalized for a story session, THE Style_Transfer_Agent SHALL generate an illustrated portrait for each mapped Family_Member using the cropped face portrait as a reference.
2. THE Style_Transfer_Agent SHALL produce illustrations in a Pixar/Disney animation style consistent with the existing Visual Storytelling Agent art direction (bright colors, soft lighting, child-friendly aesthetic).
3. WHEN generating an illustrated portrait, THE Style_Transfer_Agent SHALL preserve recognizable facial features (hair color, skin tone, eye shape) of the Family_Member while applying the cartoon style.
4. THE Style_Transfer_Agent SHALL generate each illustrated portrait within 10 seconds.
5. WHEN an illustrated portrait is generated, THE Style_Transfer_Agent SHALL store the result in the Photo_Store linked to the Family_Member and the story session.
6. IF style transfer fails for a Family_Member, THEN THE Style_Transfer_Agent SHALL fall back to the existing AI-generated avatar and log the failure for diagnostics.

### Requirement 6: Scene Compositing with Family Faces

**User Story:** As a child, I want to see my family members inside the story illustrations, so that the adventure feels like it is really happening to us.

#### Acceptance Criteria

1. WHEN the Visual Storytelling Agent generates a scene illustration for a story session with photo integration enabled, THE Scene_Compositor SHALL composite the style-transferred portraits of mapped Family_Members into the scene at character positions.
2. THE Scene_Compositor SHALL scale and position each Family_Member portrait to match the character's pose and placement within the scene composition.
3. THE Scene_Compositor SHALL blend composited portraits with the scene background using consistent lighting, color grading, and shadow direction so that characters appear naturally part of the illustration.
4. WHEN a scene contains characters without a mapped Family_Member, THE Scene_Compositor SHALL use the default AI-generated character illustration for those characters.
5. THE Scene_Compositor SHALL produce the final composited scene image within 5 seconds after receiving the base scene and portrait assets.

### Requirement 7: Photo Gallery Management

**User Story:** As a parent, I want to view, manage, and delete uploaded family photos, so that I stay in control of personal data used in stories.

#### Acceptance Criteria

1. THE Photo_Gallery SHALL display all uploaded photos and extracted face portraits for the current sibling pair, organized by upload date.
2. WHEN a parent selects a photo in the Photo_Gallery, THE Photo_Gallery SHALL show the full image with all detected faces highlighted.
3. WHEN a parent requests deletion of a photo, THE Photo_Service SHALL remove the photo, all associated face portraits, and all derived style-transferred illustrations from the Photo_Store.
4. WHEN a photo is deleted, THE Photo_Service SHALL invalidate any Character_Mappings that referenced the deleted Family_Members and notify the parent of affected mappings.
5. THE Photo_Gallery SHALL display a count of photos stored and a storage usage indicator.

### Requirement 8: Photo Data Persistence

**User Story:** As a parent, I want uploaded photos and character mappings to persist across sessions, so that I do not have to re-upload photos every time we play.

#### Acceptance Criteria

1. THE Photo_Store SHALL persist all photo data, face portraits, style-transferred illustrations, Family_Member labels, and Character_Mappings across application restarts.
2. WHEN a sibling pair starts a new story session, THE Photo_Service SHALL load all previously stored Family_Members and Character_Mappings for that sibling pair.
3. THE Photo_Store SHALL associate all photo data with a sibling pair identifier so that different families using the same device have isolated photo libraries.
4. FOR ALL valid photo records, storing then loading a photo record SHALL produce an equivalent record (round-trip property).

### Requirement 9: Interaction Design for Young Children

**User Story:** As a 6-year-old child, I want the photo features to be easy and fun to use with big buttons and voice guidance, so that I can help pick family photos without needing to read.

#### Acceptance Criteria

1. THE Photo_Uploader SHALL use large touch targets (minimum 48x48 CSS pixels) and colorful icons instead of text labels for all primary actions.
2. WHEN a photo upload or face labeling step is active, THE Photo_Uploader SHALL play a short voice prompt (via Google Cloud TTS) explaining what to do.
3. THE Photo_Gallery SHALL support swipe gestures for browsing photos on touch devices.
4. WHEN a face is successfully detected and extracted, THE Photo_Uploader SHALL play a celebratory animation and sound effect to reward the child.
5. THE Photo_Uploader SHALL present a maximum of 3 action choices at any time to avoid overwhelming a young child.
