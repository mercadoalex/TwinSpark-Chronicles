import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import StoryErrorBoundary from '../StoryErrorBoundary';
import DrawingErrorBoundary from '../DrawingErrorBoundary';
import CameraErrorBoundary from '../CameraErrorBoundary';
import SetupErrorBoundary from '../SetupErrorBoundary';

beforeEach(() => {
  vi.spyOn(console, 'error').mockImplementation(() => {});
});

function ThrowingChild() {
  throw new Error('Test error');
}

describe('StoryErrorBoundary', () => {
  it('shows story fallback with book emoji and retry', () => {
    render(
      <StoryErrorBoundary>
        <ThrowingChild />
      </StoryErrorBoundary>
    );
    expect(screen.getByText('📖')).toBeDefined();
    expect(screen.getByText(/story got lost/i)).toBeDefined();
    expect(screen.getByRole('button', { name: /Try Again/ })).toBeDefined();
  });

  it('applies story variant class', () => {
    const { container } = render(
      <StoryErrorBoundary>
        <ThrowingChild />
      </StoryErrorBoundary>
    );
    expect(container.querySelector('.error-fallback--story')).not.toBeNull();
  });
});

describe('DrawingErrorBoundary', () => {
  it('shows drawing fallback with crayon emoji and retry', () => {
    render(
      <DrawingErrorBoundary>
        <ThrowingChild />
      </DrawingErrorBoundary>
    );
    expect(screen.getByText('🖍️')).toBeDefined();
    expect(screen.getByText(/crayons need a break/i)).toBeDefined();
    expect(screen.getByRole('button', { name: /Try Again/ })).toBeDefined();
  });

  it('applies drawing variant class', () => {
    const { container } = render(
      <DrawingErrorBoundary>
        <ThrowingChild />
      </DrawingErrorBoundary>
    );
    expect(container.querySelector('.error-fallback--drawing')).not.toBeNull();
  });
});

describe('CameraErrorBoundary', () => {
  it('renders nothing on error (silent hide)', () => {
    const { container } = render(
      <CameraErrorBoundary>
        <ThrowingChild />
      </CameraErrorBoundary>
    );
    expect(container.innerHTML).toBe('');
  });

  it('still logs the error', () => {
    render(
      <CameraErrorBoundary>
        <ThrowingChild />
      </CameraErrorBoundary>
    );
    expect(console.error).toHaveBeenCalled();
  });
});

describe('SetupErrorBoundary', () => {
  it('shows setup fallback with star emoji and reset button', () => {
    render(
      <SetupErrorBoundary>
        <ThrowingChild />
      </SetupErrorBoundary>
    );
    expect(screen.getByText('🌟')).toBeDefined();
    expect(screen.getByText(/start over/i)).toBeDefined();
    expect(screen.getByRole('button', { name: /Start Fresh/ })).toBeDefined();
  });

  it('calls onReset when reset button clicked', () => {
    const onReset = vi.fn();
    render(
      <SetupErrorBoundary onReset={onReset}>
        <ThrowingChild />
      </SetupErrorBoundary>
    );
    fireEvent.click(screen.getByRole('button', { name: /Start Fresh/ }));
    // Called twice: once by ErrorBoundary.resetErrorBoundary() and once directly in the button handler
    expect(onReset).toHaveBeenCalledTimes(2);
  });

  it('applies setup variant class', () => {
    const { container } = render(
      <SetupErrorBoundary>
        <ThrowingChild />
      </SetupErrorBoundary>
    );
    expect(container.querySelector('.error-fallback--setup')).not.toBeNull();
  });
});

describe('error isolation between sibling boundaries', () => {
  it('one boundary error does not affect sibling boundary', () => {
    render(
      <div>
        <StoryErrorBoundary>
          <ThrowingChild />
        </StoryErrorBoundary>
        <DrawingErrorBoundary>
          <div>Drawing works fine</div>
        </DrawingErrorBoundary>
      </div>
    );
    // Story boundary caught the error
    expect(screen.getByText(/story got lost/i)).toBeDefined();
    // Drawing boundary still renders normally
    expect(screen.getByText('Drawing works fine')).toBeDefined();
  });
});
