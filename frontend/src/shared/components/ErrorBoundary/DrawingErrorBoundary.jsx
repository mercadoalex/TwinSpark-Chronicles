import ErrorBoundary from './ErrorBoundary';
import FallbackUI from './FallbackUI';

function DrawingErrorBoundary({ children, onReset }) {
  return (
    <ErrorBoundary
      fallback={(error, reset) => (
        <FallbackUI
          emoji="🖍️"
          message="The crayons need a break"
          buttonLabel="Try Again"
          buttonEmoji="🎨"
          onAction={reset}
          variant="drawing"
        />
      )}
      onError={(error, info) => console.error('[DrawingError]', error, info.componentStack)}
      onReset={onReset}
    >
      {children}
    </ErrorBoundary>
  );
}

export default DrawingErrorBoundary;
