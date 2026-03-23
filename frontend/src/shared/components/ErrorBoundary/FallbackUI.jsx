import './ErrorBoundary.css';

/**
 * Child-friendly fallback UI with large emoji, simple message, and action button.
 *
 * Props:
 *  - emoji: string (e.g. "📖")
 *  - message: string
 *  - buttonLabel: string
 *  - buttonEmoji: string (optional)
 *  - onAction: () => void
 *  - variant: 'story' | 'drawing' | 'setup' | 'default'
 */
function FallbackUI({ emoji, message, buttonLabel, buttonEmoji, onAction, variant = 'default' }) {
  return (
    <div className={`error-fallback error-fallback--${variant}`} role="alert">
      <span className="error-fallback__emoji" aria-hidden="true">{emoji}</span>
      <p className="error-fallback__message">{message}</p>
      <button className="error-fallback__button" onClick={onAction} type="button">
        {buttonEmoji && <span className="error-fallback__button-emoji" aria-hidden="true">{buttonEmoji}</span>}
        {buttonLabel}
      </button>
    </div>
  );
}

export default FallbackUI;
