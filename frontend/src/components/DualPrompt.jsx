import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useSiblingStore } from '../stores/siblingStore';
import './DualPrompt.css';

const NUDGE_DELAY_MS = 15_000;

/**
 * DualPrompt — minimal floating turn indicator for both children.
 * Shows who's responded with simple avatar bubbles + gentle nudge.
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

  const silentChild = !child1Responded && child2Responded
    ? { name: child1Name, id: 'child1' }
    : child1Responded && !child2Responded
      ? { name: child2Name, id: 'child2' }
      : null;

  const bothResponded = child1Responded && child2Responded;

  const clearNudge = useCallback(() => {
    if (nudgeTimer.current) {
      clearTimeout(nudgeTimer.current);
      nudgeTimer.current = null;
    }
    setShowNudge(false);
  }, []);

  useEffect(() => {
    clearNudge();
    if (silentChild && !bothResponded) {
      nudgeTimer.current = setTimeout(() => setShowNudge(true), NUDGE_DELAY_MS);
    }
    return clearNudge;
  }, [child1Responded, child2Responded, silentChild, bothResponded, clearNudge]);

  const nudgeTarget = showNudge
    ? silentChild
    : waitingForChild
      ? { name: waitingForChild === 'child1' ? child1Name : child2Name, id: waitingForChild }
      : null;

  return (
    <div className="dual-prompt-bar">
      {/* Child 1 bubble */}
      <button
        className={`dp-bubble dp-bubble--c1 ${child1Responded ? 'dp-bubble--done' : 'dp-bubble--waiting'}`}
        onClick={() => !child1Responded && onRespond?.('child1')}
        disabled={child1Responded}
        aria-label={`${child1Name} ${child1Responded ? 'answered' : 'tap to answer'}`}
      >
        <span className="dp-bubble__emoji">🌟</span>
        <span className="dp-bubble__name">{child1Name}</span>
        {child1Responded
          ? <span className="dp-bubble__check">✓</span>
          : <span className="dp-bubble__pulse" />
        }
      </button>

      {/* Center status */}
      <div className="dp-center">
        {bothResponded ? (
          <span className="dp-center__text dp-center__text--done">🎉</span>
        ) : nudgeTarget ? (
          <span className="dp-center__text dp-center__text--nudge">
            💫 {nudgeTarget.name}?
          </span>
        ) : (
          <span className="dp-center__text">Your turn!</span>
        )}
      </div>

      {/* Child 2 bubble */}
      <button
        className={`dp-bubble dp-bubble--c2 ${child2Responded ? 'dp-bubble--done' : 'dp-bubble--waiting'}`}
        onClick={() => !child2Responded && onRespond?.('child2')}
        disabled={child2Responded}
        aria-label={`${child2Name} ${child2Responded ? 'answered' : 'tap to answer'}`}
      >
        <span className="dp-bubble__emoji">⭐</span>
        <span className="dp-bubble__name">{child2Name}</span>
        {child2Responded
          ? <span className="dp-bubble__check">✓</span>
          : <span className="dp-bubble__pulse" />
        }
      </button>
    </div>
  );
}
