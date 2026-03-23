import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import ErrorBoundary from '../ErrorBoundary';

// Suppress console.error from React error boundary logging
beforeEach(() => {
  vi.spyOn(console, 'error').mockImplementation(() => {});
});

function ThrowingChild({ shouldThrow = true }) {
  if (shouldThrow) throw new Error('Test error');
  return <div>Normal content</div>;
}

describe('ErrorBoundary', () => {
  it('renders children when no error', () => {
    render(
      <ErrorBoundary fallback={<div>Fallback</div>}>
        <div>Hello</div>
      </ErrorBoundary>
    );
    expect(screen.getByText('Hello')).toBeDefined();
  });

  it('renders static fallback on error', () => {
    render(
      <ErrorBoundary fallback={<div>Something went wrong</div>}>
        <ThrowingChild />
      </ErrorBoundary>
    );
    expect(screen.getByText('Something went wrong')).toBeDefined();
  });

  it('renders function fallback with error and reset', () => {
    render(
      <ErrorBoundary fallback={(err, reset) => (
        <div>
          <span>{err.message}</span>
          <button onClick={reset}>Reset</button>
        </div>
      )}>
        <ThrowingChild />
      </ErrorBoundary>
    );
    expect(screen.getByText('Test error')).toBeDefined();
    expect(screen.getByText('Reset')).toBeDefined();
  });

  it('calls onError callback', () => {
    const onError = vi.fn();
    render(
      <ErrorBoundary fallback={<div>Fallback</div>} onError={onError}>
        <ThrowingChild />
      </ErrorBoundary>
    );
    expect(onError).toHaveBeenCalledOnce();
    expect(onError.mock.calls[0][0].message).toBe('Test error');
  });

  it('logs to console.error', () => {
    render(
      <ErrorBoundary fallback={<div>Fallback</div>}>
        <ThrowingChild />
      </ErrorBoundary>
    );
    expect(console.error).toHaveBeenCalled();
  });

  it('reset clears error state', () => {
    let resetFn;
    const { rerender } = render(
      <ErrorBoundary fallback={(err, reset) => {
        resetFn = reset;
        return <div>Error</div>;
      }}>
        <ThrowingChild shouldThrow={true} />
      </ErrorBoundary>
    );
    expect(screen.getByText('Error')).toBeDefined();

    // After reset, re-render with non-throwing child
    rerender(
      <ErrorBoundary fallback={(err, reset) => {
        resetFn = reset;
        return <div>Error</div>;
      }}>
        <ThrowingChild shouldThrow={false} />
      </ErrorBoundary>
    );
    resetFn();
  });

  it('calls onReset callback on reset', () => {
    const onReset = vi.fn();
    let resetFn;
    render(
      <ErrorBoundary
        fallback={(err, reset) => {
          resetFn = reset;
          return <button onClick={reset}>Reset</button>;
        }}
        onReset={onReset}
      >
        <ThrowingChild />
      </ErrorBoundary>
    );
    fireEvent.click(screen.getByText('Reset'));
    expect(onReset).toHaveBeenCalledOnce();
  });

  it('resetKeys auto-reset clears error when keys change', () => {
    const { rerender } = render(
      <ErrorBoundary fallback={<div>Error</div>} resetKeys={[1]}>
        <ThrowingChild />
      </ErrorBoundary>
    );
    expect(screen.getByText('Error')).toBeDefined();

    rerender(
      <ErrorBoundary fallback={<div>Error</div>} resetKeys={[2]}>
        <ThrowingChild shouldThrow={false} />
      </ErrorBoundary>
    );
    expect(screen.getByText('Normal content')).toBeDefined();
  });

  it('resetKeys no-op when not errored', () => {
    const onReset = vi.fn();
    const { rerender } = render(
      <ErrorBoundary fallback={<div>Error</div>} resetKeys={[1]} onReset={onReset}>
        <div>OK</div>
      </ErrorBoundary>
    );
    rerender(
      <ErrorBoundary fallback={<div>Error</div>} resetKeys={[2]} onReset={onReset}>
        <div>OK</div>
      </ErrorBoundary>
    );
    expect(onReset).not.toHaveBeenCalled();
  });

  it('renders null when no fallback provided', () => {
    const { container } = render(
      <ErrorBoundary>
        <ThrowingChild />
      </ErrorBoundary>
    );
    expect(container.innerHTML).toBe('');
  });
});
