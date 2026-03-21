import React, { useState, useRef, useCallback } from 'react';
import { useSessionPersistenceStore } from '../stores/sessionPersistenceStore';
import { useSessionStore } from '../stores/sessionStore';
import WindDownScreen from '../shared/components/WindDownScreen';
import './EmergencyStop.css';

const HOLD_DURATION_MS = 2000;
const HOLD_TICK_MS = 50;
const STOP_TIMEOUT_MS = 10000;

/**
 * Fixed-position red emergency stop button with press-and-hold confirmation gate.
 * Requires a 2-second hold to activate. Shows a conic-gradient progress ring
 * and pulsing arrow indicator during hold. On completion: saves snapshot,
 * calls emergency stop API, then triggers onStop (WindDownScreen).
 */
export default function EmergencyStop({ sessionId, onStop }) {
  const [stopping, setStopping] = useState(false);
  const [isHolding, setIsHolding] = useState(false);
  const [holdProgress, setHoldProgress] = useState(0);
  const [showWindDown, setShowWindDown] = useState(false);
  const profiles = useSessionStore((s) => s.profiles);

  const holdIntervalRef = useRef(null);
  const holdStartRef = useRef(null);
  const stopTimeoutRef = useRef(null);

  const clearHoldTimer = useCallback(() => {
    if (holdIntervalRef.current) {
      clearInterval(holdIntervalRef.current);
      holdIntervalRef.current = null;
    }
    holdStartRef.current = null;
  }, []);

  const resetHold = useCallback(() => {
    clearHoldTimer();
    setIsHolding(false);
    setHoldProgress(0);
  }, [clearHoldTimer]);

  const triggerStopSequence = useCallback(async () => {
    if (stopping) return;
    setStopping(true);
    clearHoldTimer();

    // 10-second total timeout for the full stop sequence
    const forceStop = () => {
      if (onStop) onStop();
    };
    stopTimeoutRef.current = setTimeout(forceStop, STOP_TIMEOUT_MS);

    // 1. Save snapshot (best effort — don't block on failure)
    try {
      await useSessionPersistenceStore.getState().saveSnapshot();
    } catch (_) { /* best effort */ }

    // 2. Call emergency stop API
    let apiOk = false;
    try {
      const resp = await fetch(
        `http://localhost:8000/api/emergency-stop/${sessionId}`,
        { method: 'POST' }
      );
      apiOk = resp.ok;
    } catch (_) { /* will retry */ }

    // Retry once in background if first call failed
    if (!apiOk) {
      setTimeout(async () => {
        try {
          await fetch(
            `http://localhost:8000/api/emergency-stop/${sessionId}`,
            { method: 'POST' }
          );
        } catch (_) { /* best effort */ }
      }, 1000);
    }

    // 3. Show WindDownScreen instead of calling onStop directly
    if (stopTimeoutRef.current) {
      clearTimeout(stopTimeoutRef.current);
      stopTimeoutRef.current = null;
    }
    setShowWindDown(true);
  }, [stopping, sessionId, clearHoldTimer]);

  const handlePointerDown = useCallback((e) => {
    if (stopping) return;
    e.preventDefault();

    setIsHolding(true);
    setHoldProgress(0);
    holdStartRef.current = Date.now();

    holdIntervalRef.current = setInterval(() => {
      const elapsed = Date.now() - holdStartRef.current;
      const progress = Math.min(elapsed / HOLD_DURATION_MS, 1);
      setHoldProgress(progress);

      if (progress >= 1) {
        clearInterval(holdIntervalRef.current);
        holdIntervalRef.current = null;
        triggerStopSequence();
      }
    }, HOLD_TICK_MS);
  }, [stopping, triggerStopSequence]);

  const handlePointerUp = useCallback(() => {
    if (!stopping) {
      resetHold();
    }
  }, [stopping, resetHold]);

  const handlePointerLeave = useCallback(() => {
    if (!stopping) {
      resetHold();
    }
  }, [stopping, resetHold]);

  const buttonClass = [
    'emergency-stop',
    stopping ? 'emergency-stop--active' : '',
    isHolding && !stopping ? 'emergency-stop--holding' : '',
  ].filter(Boolean).join(' ');

  return (
    <>
      <button
        className={buttonClass}
        style={{ '--hold-progress': holdProgress }}
        onPointerDown={handlePointerDown}
        onPointerUp={handlePointerUp}
        onPointerLeave={handlePointerLeave}
        aria-label="Emergency stop — press and hold for 2 seconds to end session"
        disabled={stopping}
      >
        <span className="emergency-stop__icon" aria-hidden="true">
          {isHolding && !stopping ? '▼' : '👋'}
        </span>
      </button>

      {showWindDown && (
        <WindDownScreen
          childNames={[profiles?.c1_name || 'Friend', profiles?.c2_name || 'Friend']}
          duration={4000}
          onComplete={() => { if (onStop) onStop(); }}
        />
      )}
    </>
  );
}
