'use client';

import { useEffect, useRef, useCallback } from 'react';

interface UsePollingOptions {
  /** Interval in milliseconds between polls */
  interval: number;
  /** Whether polling is enabled */
  enabled: boolean;
  /** Stop polling when this function returns true */
  stopWhen?: (data: unknown) => boolean;
  /** Callback when an error occurs */
  onError?: (error: Error) => void;
}

/**
 * Custom hook that polls an async function at a given interval.
 * Auto-stops when the stopWhen condition is met.
 * Cleans up on unmount.
 */
export function usePolling<T = unknown>(
  pollFn: () => Promise<T>,
  options: UsePollingOptions
) {
  const { interval, enabled, stopWhen, onError } = options;
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const mountedRef = useRef(true);
  const pollFnRef = useRef(pollFn);
  const stopWhenRef = useRef(stopWhen);
  const onErrorRef = useRef(onError);

  // Keep refs up to date
  pollFnRef.current = pollFn;
  stopWhenRef.current = stopWhen;
  onErrorRef.current = onError;

  const executePoll = useCallback(async () => {
    if (!mountedRef.current || !enabled) return;

    try {
      const result = await pollFnRef.current();
      if (!mountedRef.current) return;

      if (stopWhenRef.current && stopWhenRef.current(result)) {
        return; // Stop polling
      }

      // Schedule next poll
      if (mountedRef.current && enabled) {
        timeoutRef.current = setTimeout(executePoll, interval);
      }
    } catch (err) {
      if (!mountedRef.current) return;

      if (onErrorRef.current) {
        onErrorRef.current(err instanceof Error ? err : new Error(String(err)));
      }

      // Still continue polling on error
      if (mountedRef.current && enabled) {
        timeoutRef.current = setTimeout(executePoll, interval);
      }
    }
  }, [interval, enabled]);

  useEffect(() => {
    mountedRef.current = true;

    if (enabled) {
      timeoutRef.current = setTimeout(executePoll, interval);
    }

    return () => {
      mountedRef.current = false;
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
        timeoutRef.current = null;
      }
    };
  }, [enabled, interval, executePoll]);
}
