import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useSiblingStore } from '../stores/siblingStore';
import './DualPrompt.css';

const NUDGE_DELAY_MS = 15_000;

/**
 * DualPrompt — interactive prompt addressing both children by name
 * with distinct roles. Shows a gentle nudge after 15 s if one child
 * hasn't responded, and acknowledges both responses once they arrive.
 *
 * Props:
 *  - child1Name  (string)  first child's display name
 *  - child2Name  (string)  second child's display name
 *  - promptText  (string)  the current story prompt / question
 *  - child1Responded (bool) whether child 1 has answered
 *  - child2Responded (bool) whether child 2 has answered
 *  - onRespond   (fn)      callback when a child responds: onRespond(childId)
 */
export default function DualPrompt({
  child1Name = 'Child 1',
  child2Name = 'Child 2',
  promptText = '',
  child1Responded = false,
  child2Responded = false,
  onRespond,
}) {
  const { childRoles, waitingForChild } = useSiblingStore();

  const [showNudge, setShowNudge] = useState(false);
  const nudgeTimer = useRef(null);

  // Determine which child (if any) still hasn't responded
  const silentChild = !child1Responded && child2Responded
    ? { name: child1Name, id: 'child1' }
    : child1Responded && !child2Responded
      ? { name: child2Name, id: 'child2' }
      : null;

  const bothResponded = child1Responded && child2Responded;

  // ── 15-second nudge timer ──────────────────────────────────
  const clearNudge = useCallback(() => {
    if (nudgeTimer.current) {
      clearTimeout(nudgeTimer.current);
      nudgeTimer.current = null;
    }
    setShowNudge(false);
  }, []);

  useEffect(() => {
    // Reset nudge whenever responses change
    clearNudge();

    if (silentChild && !bothResponded) {
      nudgeTimer.current = setTimeout(() => setShowNudge(true), NUDGE_DELAY_MS);
    }

    return clearNudge;
  }, [child1Responded, child2Responded, silentChild, bothResponded, clearNudge]);

  // Also respect the store-level waitingForChild flag
  const nudgeTarget = showNudge
    ? silentChild
    : waitingForChild
      ? { name: waitingForChild === 'child1' ? child1Name : child2Name, id: waitingForChild }
      : null;

  // ── Render ─────────────────────────────────────────────────
  return (
    <div className="dual-prompt glass-panel" style={{ padding: '28px' }}>
      {/* Header */}
      <div className="dual-prompt__header">
        <h2 className="dual-prompt__title">
          ✨ {child1Name} &amp; {child2Name}'s Turn! ✨
        </h2>
        {promptText && (
          <p className="dual-prompt__subtitle">{promptText}</p>
        )}
      </div>

      {/* Both-responded acknowledgment */}
      {bothResponded && (
        <div className="dual-prompt__ack" role="status" aria-live="polite">
          <span className="dual-prompt__ack-text">
            🎉 Great job, {child1Name} &amp; {child2Name}! Both of you answered!
          </span>
        </div>
      )}

      {/* Gentle nudge */}
      {!bothResponded && nudgeTarget && (
        <div className="dual-prompt__nudge" role="status" aria-live="polite">
          <span className="dual-prompt__nudge-text">
            💫 Hey {nudgeTarget.name}, we'd love to hear from you too!
          </span>
        </div>
      )}

      {/* Role cards */}
      <div className="dual-prompt__roles">
        {/* Child 1 */}
        <div
          className={`dual-prompt__role-card dual-prompt__role-card--child1${
            !child1Responded && child2Responded ? ' dual-prompt__role-card--waiting' : ''
          }`}
        >
          <span className="dual-prompt__child-emoji" aria-hidden="true">🌟</span>
          <div className="dual-prompt__child-name dual-prompt__child-name--child1">
            {child1Name}
          </div>
          {childRoles.child1 && (
            <div className="dual-prompt__child-role">{childRoles.child1}</div>
          )}
          {child1Responded ? (
            <span className="dual-prompt__status dual-prompt__status--responded">
              ✅ Answered
            </span>
          ) : (
            <span className="dual-prompt__status dual-prompt__status--waiting">
              ⏳ Waiting…
            </span>
          )}
          {!child1Responded && onRespond && (
            <button
              className="btn-magic"
              style={{
                marginTop: 12,
                padding: '10px 24px',
                fontSize: '1.1rem',
                background: 'linear-gradient(135deg, var(--color-accent-pink), var(--color-accent-purple))',
                color: '#fff',
              }}
              onClick={() => onRespond('child1')}
              aria-label={`${child1Name} responds`}
            >
              {child1Name}, answer! 🗣️
            </button>
          )}
        </div>

        {/* Child 2 */}
        <div
          className={`dual-prompt__role-card dual-prompt__role-card--child2${
            !child2Responded && child1Responded ? ' dual-prompt__role-card--waiting' : ''
          }`}
        >
          <span className="dual-prompt__child-emoji" aria-hidden="true">⭐</span>
          <div className="dual-prompt__child-name dual-prompt__child-name--child2">
            {child2Name}
          </div>
          {childRoles.child2 && (
            <div className="dual-prompt__child-role">{childRoles.child2}</div>
          )}
          {child2Responded ? (
            <span className="dual-prompt__status dual-prompt__status--responded">
              ✅ Answered
            </span>
          ) : (
            <span className="dual-prompt__status dual-prompt__status--waiting">
              ⏳ Waiting…
            </span>
          )}
          {!child2Responded && onRespond && (
            <button
              className="btn-magic"
              style={{
                marginTop: 12,
                padding: '10px 24px',
                fontSize: '1.1rem',
                background: 'linear-gradient(135deg, var(--color-accent-blue), var(--color-accent-purple))',
                color: '#fff',
              }}
              onClick={() => onRespond('child2')}
              aria-label={`${child2Name} responds`}
            >
              {child2Name}, answer! 🗣️
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
