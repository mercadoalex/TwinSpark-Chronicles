import { describe, it, expect, vi, beforeEach } from 'vitest';
import { reportError } from '../errorReporter';

describe('errorReporter', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('sends correct payload to backend', async () => {
    const mockFetch = vi.fn().mockResolvedValue({ ok: true });
    vi.stubGlobal('fetch', mockFetch);

    const error = new Error('test error');
    const errorInfo = { componentStack: '\n    in MyComponent' };

    await reportError(error, errorInfo, 'MyComponent');

    expect(mockFetch).toHaveBeenCalledTimes(1);
    const [url, options] = mockFetch.mock.calls[0];
    expect(url).toBe('/api/monitoring/errors/frontend');
    expect(options.method).toBe('POST');

    const body = JSON.parse(options.body);
    expect(body.message).toBe('test error');
    expect(body.stack).toContain('Error: test error');
    expect(body.component_stack).toBe('\n    in MyComponent');
    expect(body.component_name).toBe('MyComponent');
  });

  it('includes ISO timestamp in payload', async () => {
    const mockFetch = vi.fn().mockResolvedValue({ ok: true });
    vi.stubGlobal('fetch', mockFetch);

    await reportError(new Error('ts test'), {}, 'Comp');

    const body = JSON.parse(mockFetch.mock.calls[0][1].body);
    expect(body.timestamp).toBeTruthy();
    // Should be parseable as a date
    const parsed = new Date(body.timestamp);
    expect(parsed.getTime()).not.toBeNaN();
  });

  it('handles network failure silently', async () => {
    const mockFetch = vi.fn().mockRejectedValue(new TypeError('Network error'));
    vi.stubGlobal('fetch', mockFetch);
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    // Should not throw
    await reportError(new Error('fail'), {}, 'Comp');

    expect(consoleSpy).toHaveBeenCalledTimes(1);
    expect(consoleSpy.mock.calls[0][0]).toContain('Failed to report error');
  });

  it('defaults componentName to unknown', async () => {
    const mockFetch = vi.fn().mockResolvedValue({ ok: true });
    vi.stubGlobal('fetch', mockFetch);

    await reportError(new Error('x'), {});

    const body = JSON.parse(mockFetch.mock.calls[0][1].body);
    expect(body.component_name).toBe('unknown');
  });
});
