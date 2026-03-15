# Requirements Document: Sibling Dynamics Engine

## Introduction

The Sibling Dynamics Engine is a 4-layer AI system that transforms TwinSpark Chronicles from a generic storytelling app into the world's first AI that truly understands sibling dynamics. Rather than treating two children as independent users, the engine models each child's personality, maps how they relate to each other, discovers where their strengths complement each other, and generates adaptive narratives that celebrate their unique bond. The target users are young siblings (ages 3–8, initially twins Ale & Sofi, age 6) playing together in a shared storytelling session.

## Glossary

- **Personality_Engine**: The Layer 1 subsystem responsible for building and maintaining an individual personality profile for each child based on observed behavior, choices, and emotional signals.
- **Relationship_Mapper**: The Layer 2 subsystem that models the dynamic between two siblings — leadership patterns, cooperation style, conflict triggers, and emotional attunement.
- **Complementary_Skills_Discoverer**: The Layer 3 subsystem that identifies where one child's strengths offset the other's weaknesses and surfaces opportunities for mutual growth.
- **Narrative_Generator**: The Layer 4 subsystem that produces adaptive story content in real time, informed by all three lower layers.
- **Personality_Profile**: A structured data object containing a child's observed traits, preferences, fears, strengths, interaction style, and emotional tendencies.
- **Relationship_Model**: A structured data object describing the sibling pair's interaction patterns, including leadership balance, cooperation score, conflict frequency, and emotional synchrony.
- **Skill_Map**: A structured data object pairing each child's identified strengths and growth areas with the other child's complementary attributes.
- **Story_Moment**: A single narrative segment delivered to the children, consisting of text, optional illustration, optional audio, and an interactive prompt.
- **Interaction_Event**: Any observable child action during a session — a spoken response, a choice selection, an emotional reaction, or a gesture.
- **Session**: A single continuous play period in which two siblings engage with the storytelling experience.
- **Orchestrator**: The existing backend coordinator that routes data between agents and manages the multimodal pipeline.
- **Sibling_Dynamics_Score**: A composite numeric indicator (0.0–1.0) summarizing the overall health and engagement of the sibling interaction at any point in a session.

---

## Requirements

### Requirement 1: Individual Personality Observation

**User Story:** As a parent, I want the AI to learn each child's unique personality over time, so that stories feel personally meaningful to each child.

#### Acceptance Criteria

1. WHEN a child makes a story choice during a Session, THE Personality_Engine SHALL record the choice and update the corresponding Personality_Profile within 2 seconds.
2. WHEN a child's emotion is detected via the multimodal pipeline, THE Personality_Engine SHALL incorporate the emotion reading into the child's Personality_Profile.
3. THE Personality_Engine SHALL maintain a separate Personality_Profile for each child in a sibling pair.
4. WHEN a Session begins and a returning child is identified, THE Personality_Engine SHALL load the child's existing Personality_Profile from persistent storage.
5. IF the Personality_Engine receives contradictory trait signals within a single Session, THEN THE Personality_Engine SHALL weight recent observations higher than older observations using a temporal decay function.

### Requirement 2: Personality Profile Structure

**User Story:** As a storyteller AI, I want a rich personality model for each child, so that I can craft story elements that resonate with each child's unique character.

#### Acceptance Criteria

1. THE Personality_Profile SHALL contain the following trait dimensions: curiosity level, boldness, empathy, creativity, patience, and humor preference.
2. THE Personality_Profile SHALL track each child's preferred story themes (e.g., exploration, puzzle-solving, nurturing, action).
3. THE Personality_Profile SHALL track each child's known fears and sensitivities so the Narrative_Generator can avoid distressing content.
4. THE Personality_Profile SHALL store a confidence score (0.0–1.0) for each trait, reflecting how many observations support the trait value.
5. WHEN fewer than 5 Interaction_Events have been recorded for a child, THE Personality_Engine SHALL mark the Personality_Profile as "emerging" and use conservative defaults for story generation.

### Requirement 3: Relationship Dynamic Mapping

**User Story:** As a parent, I want the AI to understand how my children interact with each other, so that stories encourage healthy sibling dynamics.

#### Acceptance Criteria

1. WHEN both children participate in a shared story choice, THE Relationship_Mapper SHALL record which child initiated the decision and which child followed.
2. THE Relationship_Mapper SHALL maintain a leadership_balance metric (0.0–1.0) where 0.5 indicates equal leadership and values closer to 0.0 or 1.0 indicate one child consistently leading.
3. WHEN the leadership_balance metric deviates beyond 0.3 from the midpoint (0.5), THE Relationship_Mapper SHALL flag the imbalance for the Narrative_Generator.
4. THE Relationship_Mapper SHALL track a cooperation_score (0.0–1.0) reflecting how often the siblings choose collaborative options over competitive ones.
5. WHEN a conflict pattern is detected (two consecutive disagreements on story choices), THE Relationship_Mapper SHALL record a conflict event and notify the Narrative_Generator.
6. THE Relationship_Mapper SHALL compute an emotional_synchrony metric measuring how often both children exhibit similar emotional states during the same Story_Moment.

### Requirement 4: Complementary Skills Discovery

**User Story:** As a parent, I want the AI to help my children discover how they complement each other, so that they learn to value each other's strengths.

#### Acceptance Criteria

1. WHEN both Personality_Profiles have a confidence score above 0.5 for at least 3 trait dimensions, THE Complementary_Skills_Discoverer SHALL generate a Skill_Map for the sibling pair.
2. THE Complementary_Skills_Discoverer SHALL identify at least one complementary pair where one child's strength (trait score above 0.7) aligns with the other child's growth area (trait score below 0.4).
3. WHEN a new complementary pair is identified, THE Complementary_Skills_Discoverer SHALL notify the Narrative_Generator so it can create story moments that highlight the pairing.
4. THE Complementary_Skills_Discoverer SHALL re-evaluate the Skill_Map after every 10 Interaction_Events to account for evolving profiles.
5. THE Skill_Map SHALL contain for each complementary pair: the strength holder, the growth-area holder, the trait dimension, and a suggested story scenario type.

### Requirement 5: Adaptive Narrative Generation

**User Story:** As a child playing with my sibling, I want stories that feel like they were made just for us, so that we stay engaged and have fun together.

#### Acceptance Criteria

1. WHEN generating a Story_Moment, THE Narrative_Generator SHALL incorporate data from the Personality_Profile of each child, the Relationship_Model, and the Skill_Map.
2. WHEN the Relationship_Mapper flags a leadership imbalance, THE Narrative_Generator SHALL create a story challenge that requires the less-active child to take the lead.
3. WHEN the Relationship_Mapper detects a conflict event, THE Narrative_Generator SHALL introduce a cooperative story challenge that requires both children to contribute.
4. WHEN the Complementary_Skills_Discoverer identifies a complementary pair, THE Narrative_Generator SHALL create a story scenario where the strength-holder teaches or assists the growth-area-holder.
5. THE Narrative_Generator SHALL alternate which child is the primary protagonist across consecutive Story_Moments so that both children feel equally featured.
6. THE Narrative_Generator SHALL produce each Story_Moment within 5 seconds of receiving the triggering Interaction_Event.

### Requirement 6: Dual-Child Interactive Prompts

**User Story:** As a child, I want the story to ask both me and my sibling to do things together, so that we play as a team.

#### Acceptance Criteria

1. THE Narrative_Generator SHALL produce interactive prompts that address both children by name.
2. WHEN generating an interactive prompt, THE Narrative_Generator SHALL assign a distinct role to each child based on the current Skill_Map and Relationship_Model.
3. WHEN a Story_Moment requires a choice, THE Narrative_Generator SHALL present the choice so that each child can voice a preference before the story continues.
4. IF only one child responds to an interactive prompt within 15 seconds, THEN THE Narrative_Generator SHALL gently encourage the silent child by name to participate.
5. WHEN both children respond to a prompt, THE Narrative_Generator SHALL acknowledge both responses and weave them into the next Story_Moment.

### Requirement 7: Emotional Safety and Adaptation

**User Story:** As a parent, I want the AI to keep the experience emotionally safe for both children, so that neither child feels upset or left out.

#### Acceptance Criteria

1. WHEN the Personality_Engine detects a known fear or sensitivity for either child, THE Narrative_Generator SHALL avoid story elements related to that fear.
2. IF a child's detected emotion shifts to "sad" or "scared" during a Session, THEN THE Narrative_Generator SHALL immediately soften the story tone and introduce comforting elements.
3. WHILE the Relationship_Mapper detects a cooperation_score below 0.3, THE Narrative_Generator SHALL prioritize cooperative story challenges over competitive ones.
4. THE Narrative_Generator SHALL present both children as equally capable heroes in the story, avoiding any framing where one child is consistently more powerful or important.
5. IF a child has not been addressed by name in the last 3 consecutive Story_Moments, THEN THE Narrative_Generator SHALL feature that child prominently in the next Story_Moment.

### Requirement 8: Session Continuity and Cross-Session Learning

**User Story:** As a returning user, I want the AI to remember what happened in previous sessions, so that the story world feels persistent and my children's growth is recognized.

#### Acceptance Criteria

1. WHEN a Session ends, THE Personality_Engine SHALL persist both Personality_Profiles and the Relationship_Model to durable storage.
2. WHEN a new Session begins with a previously seen sibling pair, THE Narrative_Generator SHALL reference at least one event from a prior Session in the opening Story_Moment.
3. THE Relationship_Mapper SHALL carry forward the leadership_balance, cooperation_score, and emotional_synchrony metrics across Sessions, applying a 0.9 decay factor to historical values.
4. WHEN the Complementary_Skills_Discoverer detects that a child's growth area has improved (trait score increased by 0.2 or more since first observation), THE Narrative_Generator SHALL celebrate the growth within the story narrative.
5. THE Personality_Engine SHALL retain Personality_Profiles for a minimum of 90 days of inactivity before archiving.

### Requirement 9: Sibling Dynamics Score and Parent Insights

**User Story:** As a parent, I want to see how my children's relationship is evolving through the stories, so that I can understand their dynamic better.

#### Acceptance Criteria

1. THE Relationship_Mapper SHALL compute a Sibling_Dynamics_Score (0.0–1.0) at the end of each Session, combining leadership_balance, cooperation_score, and emotional_synchrony with equal weighting.
2. WHEN a Session ends, THE Orchestrator SHALL make the Sibling_Dynamics_Score and a plain-language summary of the session's relationship dynamics available via the API.
3. THE plain-language summary SHALL describe in 2–3 sentences how the siblings interacted during the Session, highlighting cooperation moments and any growth observed.
4. IF the Sibling_Dynamics_Score drops by more than 0.2 compared to the previous Session, THEN THE Orchestrator SHALL include a suggestion in the summary for the parent on how to encourage positive sibling interaction.

### Requirement 10: Personality and Relationship Data Serialization

**User Story:** As a developer, I want personality and relationship data to be reliably serialized and deserialized, so that no child data is lost between sessions or system restarts.

#### Acceptance Criteria

1. THE Personality_Engine SHALL serialize each Personality_Profile to JSON format for storage.
2. THE Relationship_Mapper SHALL serialize the Relationship_Model to JSON format for storage.
3. THE Personality_Engine SHALL deserialize a stored JSON Personality_Profile back into a valid Personality_Profile object.
4. THE Relationship_Mapper SHALL deserialize a stored JSON Relationship_Model back into a valid Relationship_Model object.
5. FOR ALL valid Personality_Profiles, serializing to JSON then deserializing back SHALL produce an equivalent Personality_Profile (round-trip property).
6. FOR ALL valid Relationship_Models, serializing to JSON then deserializing back SHALL produce an equivalent Relationship_Model (round-trip property).

### Requirement 11: Integration with Existing Multimodal Pipeline

**User Story:** As a developer, I want the Sibling Dynamics Engine to consume data from the existing multimodal input pipeline, so that personality and relationship observations are grounded in real child behavior.

#### Acceptance Criteria

1. WHEN the existing multimodal pipeline emits a MultimodalInputEvent, THE Orchestrator SHALL route the event to the Personality_Engine and the Relationship_Mapper before passing it to the Narrative_Generator.
2. WHEN a MultimodalInputEvent contains emotion data for two faces, THE Personality_Engine SHALL update each child's Personality_Profile with the respective emotion.
3. WHEN a MultimodalInputEvent contains a transcript, THE Personality_Engine SHALL analyze the transcript for personality-relevant signals (e.g., assertive language, questions, empathetic statements).
4. IF a MultimodalInputEvent contains no usable data (empty transcript and no detected emotions), THEN THE Orchestrator SHALL skip the Personality_Engine and Relationship_Mapper updates and proceed directly to the Narrative_Generator.
5. THE Orchestrator SHALL complete the full pipeline (personality update, relationship update, narrative generation) within 8 seconds of receiving a MultimodalInputEvent.
