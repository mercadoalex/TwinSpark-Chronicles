import { useState } from 'react';
import { useSiblingStore } from '../stores/siblingStore';
import './SiblingDashboard.css';

/**
 * Score-to-emoji mapping for a quick visual read.
 */
function scoreEmoji(score) {
  if (score >= 0.8) return '🌟';
  if (score >= 0.6) return '😊';
  if (score >= 0.4) return '🙂';
  if (score >= 0.2) return '😐';
  return '💛';
}

/**
 * Returns a CSS modifier class based on score range.
 */
function scoreTier(score) {
  if (score >= 0.6) return 'high';
  if (score >= 0.35) return 'mid';
  return 'low';
}

/**
 * SiblingDashboard — parent-facing collapsible panel showing
 * the Sibling Dynamics Score, session summary, and optional
 * parent suggestion when the score drops significantly.
 *
 * Requirements: 9.1, 9.2, 9.3, 9.4
 */
export default function SiblingDashboard() {
  const { siblingDynamicsScore, sessionSummary, parentSuggestion } =
    useSiblingStore();

  const [open, setOpen] = useState(false);

  const hasScore = siblingDynamicsScore != null;
  const hasData = hasScore || sessionSummary;

  return (
    <div className="sibling-dashboard">
      {/* Collapsible toggle */}
      <button
        className="sibling-dashboard__toggle"
        onClick={() => setOpen((prev) => !prev)}
        aria-expanded={open}
        aria-controls="sibling-dashboard-body"
      >
        <span className="sibling-dashboard__toggle-label">
          📊 Parent Insights
          {hasScore && (
            <span aria-hidden="true">{scoreEmoji(siblingDynamicsScore)}</span>
          )}
        </span>
        <span
          className={`sibling-dashboard__toggle-arrow${open ? ' sibling-dashboard__toggle-arrow--open' : ''}`}
          aria-hidden="true"
        >
          ▼
        </span>
      </button>

      {/* Panel body */}
      {open && (
        <div
          id="sibling-dashboard-body"
          className="sibling-dashboard__body glass-panel"
          role="region"
          aria-label="Sibling dynamics insights"
        >
          {!hasData && (
            <p className="sibling-dashboard__empty">
              No session data yet. Insights will appear after the session ends.
            </p>
          )}

          {/* Score indicator */}
          {hasScore && (
            <div className="sibling-dashboard__score-section">
              <div className="sibling-dashboard__score-label">
                Sibling Dynamics Score
              </div>
              <div
                className="sibling-dashboard__score-bar"
                role="progressbar"
                aria-valuenow={Math.round(siblingDynamicsScore * 100)}
                aria-valuemin={0}
                aria-valuemax={100}
                aria-label={`Sibling dynamics score: ${Math.round(siblingDynamicsScore * 100)}%`}
              >
                <div
                  className={`sibling-dashboard__score-fill sibling-dashboard__score-fill--${scoreTier(siblingDynamicsScore)}`}
                  style={{ width: `${siblingDynamicsScore * 100}%` }}
                />
              </div>
              <span className="sibling-dashboard__score-value">
                {Math.round(siblingDynamicsScore * 100)}%
              </span>
              <span className="sibling-dashboard__score-emoji" aria-hidden="true">
                {scoreEmoji(siblingDynamicsScore)}
              </span>
            </div>
          )}

          {/* Session summary */}
          {sessionSummary && (
            <div className="sibling-dashboard__summary">
              <div className="sibling-dashboard__summary-title">
                Session Summary
              </div>
              <p>{sessionSummary}</p>
            </div>
          )}

          {/* Parent suggestion (visible when score drop > 0.2) */}
          {parentSuggestion && (
            <div
              className="sibling-dashboard__suggestion"
              role="alert"
            >
              <div className="sibling-dashboard__suggestion-title">
                <span aria-hidden="true">💡</span> Suggestion
              </div>
              <p className="sibling-dashboard__suggestion-text">
                {parentSuggestion}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
