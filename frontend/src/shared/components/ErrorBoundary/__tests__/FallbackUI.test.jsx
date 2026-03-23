import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import FallbackUI from '../FallbackUI';

describe('FallbackUI', () => {
  it('renders emoji', () => {
    render(<FallbackUI emoji="📖" message="Oops" buttonLabel="Retry" onAction={() => {}} />);
    expect(screen.getByText('📖')).toBeDefined();
  });

  it('renders message text', () => {
    render(<FallbackUI emoji="📖" message="Something broke" buttonLabel="Retry" onAction={() => {}} />);
    expect(screen.getByText('Something broke')).toBeDefined();
  });

  it('renders button with label', () => {
    render(<FallbackUI emoji="📖" message="Oops" buttonLabel="Try Again" onAction={() => {}} />);
    expect(screen.getByRole('button', { name: /Try Again/ })).toBeDefined();
  });

  it('renders button emoji when provided', () => {
    render(<FallbackUI emoji="📖" message="Oops" buttonLabel="Retry" buttonEmoji="🔄" onAction={() => {}} />);
    expect(screen.getByText('🔄')).toBeDefined();
  });

  it('does not render button emoji when not provided', () => {
    const { container } = render(
      <FallbackUI emoji="📖" message="Oops" buttonLabel="Retry" onAction={() => {}} />
    );
    expect(container.querySelector('.error-fallback__button-emoji')).toBeNull();
  });

  it('calls onAction when button clicked', () => {
    const onAction = vi.fn();
    render(<FallbackUI emoji="📖" message="Oops" buttonLabel="Retry" onAction={onAction} />);
    fireEvent.click(screen.getByRole('button'));
    expect(onAction).toHaveBeenCalledOnce();
  });

  it('applies variant CSS class', () => {
    const { container } = render(
      <FallbackUI emoji="📖" message="Oops" buttonLabel="Retry" onAction={() => {}} variant="story" />
    );
    expect(container.querySelector('.error-fallback--story')).not.toBeNull();
  });

  it('applies default variant when none specified', () => {
    const { container } = render(
      <FallbackUI emoji="📖" message="Oops" buttonLabel="Retry" onAction={() => {}} />
    );
    expect(container.querySelector('.error-fallback--default')).not.toBeNull();
  });

  it('has role="alert" for accessibility', () => {
    render(<FallbackUI emoji="📖" message="Oops" buttonLabel="Retry" onAction={() => {}} />);
    expect(screen.getByRole('alert')).toBeDefined();
  });

  it('marks emoji as aria-hidden', () => {
    const { container } = render(
      <FallbackUI emoji="📖" message="Oops" buttonLabel="Retry" onAction={() => {}} />
    );
    const emojiEl = container.querySelector('.error-fallback__emoji');
    expect(emojiEl.getAttribute('aria-hidden')).toBe('true');
  });
});
