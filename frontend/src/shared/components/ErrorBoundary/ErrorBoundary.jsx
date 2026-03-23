import { Component } from 'react';
import './ErrorBoundary.css';

/**
 * Reusable error boundary that catches render errors in its subtree.
 *
 * Props:
 *  - children: ReactNode
 *  - fallback: ReactNode | (error, resetFn) => ReactNode
 *  - onError: (error, errorInfo) => void
 *  - onReset: () => void
 *  - resetKeys: any[]
 */
class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('[ErrorBoundary]', error, errorInfo.componentStack);
    this.props.onError?.(error, errorInfo);
  }

  componentDidUpdate(prevProps) {
    if (this.state.hasError && this.props.resetKeys) {
      const changed = this.props.resetKeys.some(
        (key, i) => key !== prevProps.resetKeys?.[i]
      );
      if (changed) {
        this.resetErrorBoundary();
      }
    }
  }

  resetErrorBoundary = () => {
    this.props.onReset?.();
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      const { fallback } = this.props;
      if (typeof fallback === 'function') {
        return fallback(this.state.error, this.resetErrorBoundary);
      }
      return fallback ?? null;
    }
    return this.props.children;
  }
}

export default ErrorBoundary;
