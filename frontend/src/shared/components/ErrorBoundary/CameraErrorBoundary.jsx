import ErrorBoundary from './ErrorBoundary';

function CameraErrorBoundary({ children }) {
  return (
    <ErrorBoundary
      fallback={null}
      onError={(error, info) => console.error('[CameraError]', error, info.componentStack)}
    >
      {children}
    </ErrorBoundary>
  );
}

export default CameraErrorBoundary;
