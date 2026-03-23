import ErrorBoundary from './ErrorBoundary';
import FallbackUI from './FallbackUI';

function SetupErrorBoundary({ children, onReset }) {
  return (
    <ErrorBoundary
      fallback={(error, reset) => (
        <FallbackUI
          emoji="🌟"
          message="Let's start over!"
          buttonLabel="Start Fresh"
          buttonEmoji="✨"
          onAction={() => { reset(); onReset?.(); }}
          variant="setup"
        />
      )}
      onError={(error, info) => console.error('[SetupError]', error, info.componentStack)}
      onReset={onReset}
    >
      {children}
    </ErrorBoundary>
  );
}

export default SetupErrorBoundary;
