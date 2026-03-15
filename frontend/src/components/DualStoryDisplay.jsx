import React from 'react';
import { useSiblingStore } from '../stores/siblingStore';
import './DualStoryDisplay.css';

/**
 * DualStoryDisplay — renders a story moment with sibling dynamics awareness.
 * Highlights the current protagonist child, shows role-specific text from
 * childRoles, and displays the story text with protagonist emphasis.
 *
 * Requirements: 5.5 (protagonist alternation), 6.2 (role-specific prompts),
 *               7.4 (both children as equally capable heroes)
 *
 * Props:
 *  - storyMoment   (object)  the current story moment data
 *    - text              (string)  story narrative text
 *    - protagonist_child_id (string|null) ID of the current protagonist
 *    - child_roles       (object)  { childId: roleDescription }
 *    - interactive        (object)  optional interactive prompt data
 *    - image             (string)  optional scene image URL
 *  - child1Id      (string)  first child's ID (e.g. "child1")
 *  - child2Id      (string)  second child's ID (e.g. "child2")
 *  - child1Name    (string)  first child's display name
 *  - child2Name    (string)  second child's display name
 *  - onNext        (fn)      callback to continue the story
 */
export default function DualStoryDisplay({
  storyMoment,
  child1Id = 'child1',
  child2Id = 'child2',
  child1Name = 'Child 1',
  child2Name = 'Child 2',
  onNext,
}) {
  const { childRoles } = useSiblingStore();

  if (!storyMoment) {
    return (
      <div className="dual-story-display__loading">
        <div className="dual-story-display__spinner" />
        <p>Creating your magical moment…</p>
      </div>
    );
  }

  const protagonistId = storyMoment.protagonist_child_id ?? null;
  const isChild1Protagonist = protagonistId === child1Id;
  const isChild2Protagonist = protagonistId === child2Id;

  // Merge roles: prefer storyMoment.child_roles, fall back to store
  const mergedRoles = {
    [child1Id]: storyMoment.child_roles?.[child1Id] || childRoles.child1 || null,
    [child2Id]: storyMoment.child_roles?.[child2Id] || childRoles.child2 || null,
  };

  const nameFor = (id) => (id === child1Id ? child1Name : child2Name);

  return (
    <div className="dual-story-display">
      {/* Scene image */}
      {storyMoment.image && (
        <div className="dual-story-display__scene">
          <img
            src={storyMoment.image}
            alt="Story scene"
            className="dual-story-display__scene-img"
          />
        </div>
      )}

      {/* Protagonist banner */}
      {protagonistId && (
        <div
          className={`dual-story-display__protagonist-banner dual-story-display__protagonist-banner--${
            isChild1Protagonist ? 'child1' : 'child2'
          }`}
          role="status"
          aria-live="polite"
        >
          <span className="dual-story-display__protagonist-star" aria-hidden="true">
            {isChild1Protagonist ? '🌟' : '⭐'}
          </span>
          <span className="dual-story-display__protagonist-label">
            {nameFor(protagonistId)}'s moment to shine!
          </span>
        </div>
      )}

      {/* Story text */}
      <div className="dual-story-display__text-container glass-panel">
        <p className="dual-story-display__text">{storyMoment.text}</p>
      </div>

      {/* Role cards */}
      {(mergedRoles[child1Id] || mergedRoles[child2Id]) && (
        <div className="dual-story-display__roles">
          {[child1Id, child2Id].map((id) => {
            const isProtagonist = id === protagonistId;
            const childIdx = id === child1Id ? 'child1' : 'child2';
            return (
              <div
                key={id}
                className={`dual-story-display__role-card dual-story-display__role-card--${childIdx}${
                  isProtagonist ? ' dual-story-display__role-card--protagonist' : ''
                }`}
              >
                <span className="dual-story-display__role-emoji" aria-hidden="true">
                  {childIdx === 'child1' ? '🌟' : '⭐'}
                </span>
                <div className={`dual-story-display__role-name dual-story-display__role-name--${childIdx}`}>
                  {nameFor(id)}
                  {isProtagonist && (
                    <span className="dual-story-display__protagonist-badge">
                      ★ Lead
                    </span>
                  )}
                </div>
                {mergedRoles[id] && (
                  <div className="dual-story-display__role-desc">
                    {mergedRoles[id]}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Interactive prompt */}
      {storyMoment.interactive && (
        <div className="dual-story-display__interactive">
          <p className="dual-story-display__interactive-text">
            {storyMoment.interactive.text}
          </p>
          {storyMoment.interactive.expects_response && onNext && (
            <button
              className="dual-story-display__continue-btn"
              onClick={onNext}
            >
              Continue Adventure →
            </button>
          )}
        </div>
      )}
    </div>
  );
}
