import React, { useEffect, useRef, useState, useCallback } from 'react';
// Timer icon replaced with emoji for child-friendly design
import { useParentControlsStore } from '../stores/parentControlsStore';
import { useSessionStore } from '../stores/sessionStore';
import { websocketService } from '../features/session/services/websocketService';
import { useAnnounce } from '../shared/hooks';
import WindDownScreen from '../shared/components/WindDownScreen';
import './SessionTimer.css';

/**
 * Format seconds into MM:SS string.
 */
export function formatTime(totalSeconds) {
  const clamped = Math.max(0, Math.floor(totalSeconds));
  const m = Math.floor(clamped / 60);
  const s = clamped % 60;
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}

const WARNING_THRESHOLD = 5 * 60; // 5 minutes in seconds

const PAUSE_SAFETY_TIMEOUT = 60000; // 60 seconds

export default function SessionTimer({ onTimeUp }) {
  const limitMinutes = useParentControlsStore((s) => s.sessionTimeLimitMinutes);
  const profiles = useSessionStore((s) => s.profiles);
  const [secondsLeft, setSecondsLeft] = useState(limitMinutes * 60);
  const [showWarning, setShowWarning] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [sparkle, setSparkle] = useState(false);
  const [showWindDown, setShowWindDown] = useState(false);
  const intervalRef = useRef(null);
  const wrapUpSent = useRef(false);
  const warningAnnounced = useRef(false);
  const endAnnounced = useRef(false);
  const pauseTimeoutRef = useRef(null);
  const sparkleTimeoutRef = useRef(null);
  const { announce } = useAnnounce();

  // Reset timer when limit changes
  useEffect(() => {
    setSecondsLeft(limitMinutes * 60);
    wrapUpSent.current = false;
    warningAnnounced.current = false;
    endAnnounced.current = false;
    setShowWarning(false);
    setIsPaused(false);
  }, [limitMinutes]);

  // Countdown tick — pauses when isPaused is true
  useEffect(() => {
    if (isPaused) return; // don't start interval while paused

    intervalRef.current = setInterval(() => {
      setSecondsLeft((prev) => {
        if (prev <= 1) {
          clearInterval(intervalRef.current);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(intervalRef.current);
  }, [limitMinutes, isPaused]);

  // Subscribe to generation pause/resume WebSocket messages
  useEffect(() => {
    const unsubStart = websocketService.on('GENERATION_STARTED', () => {
      setIsPaused(true);

      // Safety timeout — auto-resume after 60s if GENERATION_COMPLETED never arrives
      clearTimeout(pauseTimeoutRef.current);
      pauseTimeoutRef.current = setTimeout(() => {
        setIsPaused(false);
      }, PAUSE_SAFETY_TIMEOUT);
    });

    const unsubComplete = websocketService.on('GENERATION_COMPLETED', () => {
      clearTimeout(pauseTimeoutRef.current);
      setIsPaused(false);
    });

    const unsubExtension = websocketService.on('TIME_EXTENSION_CONFIRMED', (data) => {
      const addedSeconds = (data.added_minutes || 0) * 60;
      setSecondsLeft((prev) => {
        const newVal = prev + addedSeconds;
        if (newVal > WARNING_THRESHOLD) {
          setShowWarning(false);
          warningAnnounced.current = false;
        }
        return newVal;
      });

      // Trigger sparkle animation for 1.5s
      setSparkle(true);
      clearTimeout(sparkleTimeoutRef.current);
      sparkleTimeoutRef.current = setTimeout(() => {
        setSparkle(false);
      }, 1500);
    });

    const unsubTimeLimit = websocketService.on('TIME_LIMIT_REACHED', () => {
      setSecondsLeft((prev) => (prev > 0 ? 0 : prev));
    });

    return () => {
      unsubStart();
      unsubComplete();
      unsubExtension();
      unsubTimeLimit();
      clearTimeout(pauseTimeoutRef.current);
      clearTimeout(sparkleTimeoutRef.current);
    };
  }, []);

  // Warning at 5 minutes
  useEffect(() => {
    if (secondsLeft <= WARNING_THRESHOLD && secondsLeft > 0) {
      setShowWarning(true);
      if (!warningAnnounced.current) {
        warningAnnounced.current = true;
        announce(`${Math.ceil(secondsLeft / 60)} minutes remaining in session`, 'assertive');
      }
    }
  }, [secondsLeft, announce]);

  // Announce session ended at zero
  useEffect(() => {
    if (secondsLeft === 0 && !endAnnounced.current) {
      endAnnounced.current = true;
      announce('Session time has ended', 'assertive');
    }
  }, [secondsLeft, announce]);

  // Time's up — send wrap-up, notify parent, log event, then show WindDownScreen
  useEffect(() => {
    if (secondsLeft === 0 && !wrapUpSent.current) {
      wrapUpSent.current = true;
      // Try to trigger wrap-up via WebSocket
      try {
        websocketService.send({ type: 'WRAP_UP', reason: 'session_time_limit' });
      } catch (_) { /* best effort */ }

      // Browser notification with children's names (skip silently if not granted)
      const c1 = profiles?.c1_name || 'Child 1';
      const c2 = profiles?.c2_name || 'Child 2';
      if (typeof Notification !== 'undefined' && Notification.permission === 'granted') {
        try {
          new Notification(`${c1} & ${c2}'s adventure time is up!`);
        } catch (_) { /* best effort */ }
      }

      // Store session_ended event to localStorage for parent review
      try {
        localStorage.setItem(
          'twinspark_last_session_end',
          JSON.stringify({
            reason: 'time_limit',
            timestamp: new Date().toISOString(),
            child_names: [c1, c2],
          })
        );
      } catch (_) { /* best effort */ }

      // Show WindDownScreen instead of forcing navigate after 5s
      setShowWindDown(true);
    }
  }, [secondsLeft, profiles]);

  const isWarning = secondsLeft <= WARNING_THRESHOLD && secondsLeft > 0;
  const isExpired = secondsLeft === 0;

  return (
    <>
      <div className={`session-timer ${isWarning ? 'session-timer--warning' : ''} ${isExpired ? 'session-timer--expired' : ''} ${isPaused ? 'session-timer--paused' : ''} ${sparkle ? 'session-timer--sparkle' : ''}`}>
        <span className="session-timer__icon" aria-hidden="true">{isWarning ? '⏳' : '⏰'}</span>
        <span className="session-timer__time">{formatTime(secondsLeft)}</span>
      </div>

      {showWarning && secondsLeft > 0 && secondsLeft <= WARNING_THRESHOLD && (
        <div className="session-timer-warning-overlay">
          <div className="session-timer-warning-card">
            <span aria-hidden="true" style={{ fontSize: '2rem' }}>⏳</span>
            <p>Only {Math.ceil(secondsLeft / 60)} minute{Math.ceil(secondsLeft / 60) !== 1 ? 's' : ''} left!</p>
            <button onClick={() => setShowWarning(false)}>OK</button>
          </div>
        </div>
      )}

      {showWindDown && (
        <WindDownScreen
          childNames={[profiles?.c1_name || 'Friend', profiles?.c2_name || 'Friend']}
          duration={8000}
          onComplete={() => { if (onTimeUp) onTimeUp(); }}
        />
      )}
    </>
  );
}
