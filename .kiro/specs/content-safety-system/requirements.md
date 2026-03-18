# Requirements Document

## Introduction

The Content Safety System provides comprehensive protection for children (ages 4–8) using Twin Spark Chronicles. It enforces age-appropriate content at every stage of the AI-powered story generation pipeline — from Gemini API safety settings, through post-generation text analysis, to runtime session controls. The system also gives parents configurable controls over session duration, content themes, and an emergency stop mechanism.

## Glossary

- **Content_Filter**: The backend service that scans generated text against a blocklist and content-rating rules before delivery to the frontend.
- **Content_Rating**: A classification assigned to generated content: SAFE (deliver immediately), REVIEW (flag for regeneration), or BLOCKED (discard and regenerate).
- **Gemini_Safety_Settings**: The harm-category threshold configuration applied to all Google Gemini API calls.
- **Session_Timer**: The frontend component that tracks elapsed session time against a parent-configured limit.
- **Emergency_Stop**: A persistent UI control that immediately halts the active storytelling session.
- **Parent_Controls**: A configuration interface allowing parents to set session limits, content preferences, and theme restrictions.
- **Blocklist**: A curated set of keywords and phrases that must not appear in content delivered to children.
- **Orchestrator**: The backend agent coordinator (`AgentOrchestrator`) that sequences story generation, image creation, and voice synthesis.
- **Storyteller_Agent**: The backend agent that calls Gemini to generate story text.
- **Story_Segment**: A single unit of generated story text returned by the Storyteller_Agent.

## Requirements

### Requirement 1: Gemini Safety Settings Configuration

**User Story:** As a developer, I want all Gemini API calls to use strict safety settings, so that the model itself blocks harmful content before it reaches the application.

#### Acceptance Criteria

1. THE Gemini_Safety_Settings SHALL set all four harm categories (HARM_CATEGORY_HARASSMENT, HARM_CATEGORY_HATE_SPEECH, HARM_CATEGORY_SEXUALLY_EXPLICIT, HARM_CATEGORY_DANGEROUS_CONTENT) to BLOCK_LOW_AND_ABOVE threshold.
2. WHEN the Storyteller_Agent initializes a Gemini model, THE Storyteller_Agent SHALL apply the Gemini_Safety_Settings to the model configuration.
3. WHEN the Gemini API blocks a response due to safety settings, THE Storyteller_Agent SHALL return a child-friendly fallback Story_Segment instead of an error.


### Requirement 2: Post-Generation Content Analysis

**User Story:** As a parent, I want all AI-generated story text to be analyzed for age-appropriateness after generation, so that no harmful content reaches my children.

#### Acceptance Criteria

1. WHEN the Storyteller_Agent returns a Story_Segment, THE Content_Filter SHALL scan the text before the Orchestrator delivers it to the frontend.
2. THE Content_Filter SHALL assign a Content_Rating of SAFE, REVIEW, or BLOCKED to each scanned Story_Segment.
3. WHEN the Content_Filter assigns a Content_Rating of SAFE, THE Orchestrator SHALL deliver the Story_Segment to the frontend.
4. WHEN the Content_Filter assigns a Content_Rating of REVIEW or BLOCKED, THE Orchestrator SHALL discard the Story_Segment and request a new generation from the Storyteller_Agent.
5. WHEN the Orchestrator retries generation after a REVIEW or BLOCKED rating, THE Orchestrator SHALL retry a maximum of 3 times before returning a pre-written safe fallback Story_Segment.

### Requirement 3: Keyword and Phrase Blocklist

**User Story:** As a developer, I want a configurable blocklist of keywords and phrases, so that specific inappropriate terms are caught even if the AI model does not flag them.

#### Acceptance Criteria

1. THE Content_Filter SHALL maintain a Blocklist of keywords and phrases that are inappropriate for children aged 4–8.
2. WHEN a Story_Segment contains any word or phrase from the Blocklist, THE Content_Filter SHALL assign a Content_Rating of BLOCKED to that Story_Segment.
3. THE Blocklist SHALL be stored as an external configuration file that can be updated without code changes.
4. THE Content_Filter SHALL perform case-insensitive matching when scanning Story_Segments against the Blocklist.

### Requirement 4: Content Rating System

**User Story:** As a developer, I want a structured content rating system, so that generated content is consistently classified and handled based on its safety level.

#### Acceptance Criteria

1. THE Content_Filter SHALL classify each Story_Segment into exactly one Content_Rating: SAFE, REVIEW, or BLOCKED.
2. THE Content_Filter SHALL assign a Content_Rating of BLOCKED when a Story_Segment contains Blocklist matches.
3. THE Content_Filter SHALL assign a Content_Rating of REVIEW when a Story_Segment contains themes outside the parent-configured allowed themes in Parent_Controls.
4. THE Content_Filter SHALL assign a Content_Rating of SAFE when a Story_Segment passes all Blocklist and theme checks.
5. WHEN the Content_Filter assigns a Content_Rating, THE Content_Filter SHALL log the rating, the reason, and the session identifier.

### Requirement 5: Session Time Limits

**User Story:** As a parent, I want to set a maximum session duration for my children, so that screen time is controlled.

#### Acceptance Criteria

1. THE Parent_Controls SHALL allow parents to configure a session time limit of 15, 30, 45, or 60 minutes.
2. WHEN no session time limit is configured, THE Session_Timer SHALL default to 30 minutes.
3. WHEN the remaining session time reaches 5 minutes, THE Session_Timer SHALL display a visible warning to the children.
4. WHEN the remaining session time reaches 0 minutes, THE Session_Timer SHALL trigger a gentle session wrap-up sequence that concludes the current story arc.
5. WHILE a session is active, THE Session_Timer SHALL display the remaining time in a child-friendly format.


### Requirement 6: Emergency Stop

**User Story:** As a parent, I want an always-visible emergency stop button, so that I can immediately halt a storytelling session if needed.

#### Acceptance Criteria

1. WHILE a storytelling session is active, THE Emergency_Stop SHALL be visible on the screen at all times.
2. WHEN a user activates the Emergency_Stop, THE Emergency_Stop SHALL immediately halt all story generation, image generation, and voice synthesis operations.
3. WHEN a user activates the Emergency_Stop, THE Emergency_Stop SHALL save the current session state before exiting.
4. WHEN a user activates the Emergency_Stop, THE Emergency_Stop SHALL navigate the user to a safe landing screen within 2 seconds.
5. WHEN the Emergency_Stop halts a session, THE Orchestrator SHALL cancel all in-flight API requests for that session.

### Requirement 7: Parent Controls for Content Preferences

**User Story:** As a parent, I want to configure content preferences for my children's stories, so that the generated content aligns with my family's values.

#### Acceptance Criteria

1. THE Parent_Controls SHALL allow parents to select allowed story themes from a predefined list (e.g., friendship, nature, space, animals, problem-solving).
2. THE Parent_Controls SHALL allow parents to set a story complexity level (simple, moderate, or advanced).
3. THE Parent_Controls SHALL allow parents to add custom restricted words or phrases to the Blocklist.
4. WHEN a parent updates content preferences, THE Parent_Controls SHALL apply the updated preferences to all subsequent story generations in the same session without requiring a restart.
5. THE Parent_Controls SHALL persist preferences across sessions using local storage.

### Requirement 8: Content Filtering Pipeline Integration

**User Story:** As a developer, I want the content filtering to be integrated into the orchestrator pipeline, so that all generated content passes through safety checks before reaching children.

#### Acceptance Criteria

1. WHEN the Orchestrator receives a Story_Segment from the Storyteller_Agent, THE Orchestrator SHALL pass the Story_Segment through the Content_Filter before proceeding to image or voice generation.
2. WHEN the Orchestrator generates story choices or perspective text, THE Orchestrator SHALL pass each text through the Content_Filter.
3. IF the Content_Filter is unavailable due to an error, THEN THE Orchestrator SHALL use the pre-written safe fallback Story_Segment instead of delivering unfiltered content.
4. THE Content_Filter SHALL complete analysis of a Story_Segment within 500 milliseconds.
