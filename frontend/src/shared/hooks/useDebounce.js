/**
 * useDebounce Hook
 * Debounces a value
 */

import { useState, useEffect } from 'react';

/**
 * Hook for debouncing a value
 * @template T
 * @param {T} value - Value to debounce
 * @param {number} [delay=500] - Delay in milliseconds
 * @returns {T} Debounced value
 */
export function useDebounce(value, delay = 500) {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    // Set debounced value after delay
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    // Cleanup timeout if value changes before delay
    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}