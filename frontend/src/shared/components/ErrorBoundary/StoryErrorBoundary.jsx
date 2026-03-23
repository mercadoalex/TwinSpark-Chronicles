import ErrorBoundary from './ErrorBoundary';
import FallbackUI from './FallbackUI';

function StoryErrorBoundary({ children, onReset }) {
  return (
    <ErrorBoundary
      fallback={(error, reset) => (
        <FallbackUI
          emoji="📖"
          message="Oops! The story got lost"
          buttonLabel="Try Again"
          buttonEmoji="🔄"
          onAction={reset}
          variant="story"
        />
      )}
      onError={(error, info) => console.error('[StoryError]', error, info.componentStack)}
      onReset={onReset}
    >
      {children}
    </ErrorBoundary>
  );
}

export default StoryErrorBoundary;
