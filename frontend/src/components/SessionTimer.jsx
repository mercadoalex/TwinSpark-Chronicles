import React, { useEffect, useRef, useState, useCallback } from 'react';
import { Timer } from 'lucide-react';
import { useParentControlsStore } from '../stores/parentControlsStore';
import { websocketService } from '../features/session/services/websocketService';
import { useAnnounce } from '../shared/hooks';
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

export default function SessionTimer({ onTimeUp }) {
  const limitMinutes = useParentControlsStore((s) => s.sessionTimeLimitMinutes);
  const [secondsLeft, setSecondsLeft] = useState(limitMinutes * 60);
  const [showWarning, setShowWarning] = useState(false);
  const intervalRef = useRef(null);
  const wrapUpSent = useRef(false);
  const warningAnnounced = useRef(false);
  const endAnnounced = useRef(false);
  const { announce } = useAnnounce();

  // Reset timer when limit changes
  useEffect(() => {
    setSecondsLeft(limitMinutes * 60);
    wrapUpSent.current = false;
    warningAnnounced.current = false;
    endAnnounced.current = false;
    setShowWarning(false);
  }, [limitMinutes]);

  // Countdown tick
  useEffect(() => {
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
  }, [limitMinutes]);

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

  // Time's up — send wrap-up, then force navigate after 5s
  useEffect(() => {
    if (secondsLeft === 0 && !wrapUpSent.current) {
      wrapUpSent.current = true;
      // Try to trigger wrap-up via WebSocket
      try {
        websocketService.send({ type: 'WRAP_UP', reason: 'session_time_limit' });
      } catch (_) { /* best effort */ }

      // Force navigate to landing after 5s
      const timeout = setTimeout(() => {
        if (onTimeUp) onTimeUp();
      }, 5000);
      return () => clearTimeout(timeout);
    }
  }, [secondsLeft, onTimeUp]);

  const isWarning = secondsLeft <= WARNING_THRESHOLD && secondsLeft > 0;
  const isExpired = secondsLeft === 0;

  return (
    <>
      <div className={`session-timer ${isWarning ? 'session-timer--warning' : ''} ${isExpired ? 'session-timer--expired' : ''}`}>
        <Timer size={18} />
        <span className="session-timer__time">{formatTime(secondsLeft)}</span>
      </div>

      {showWarning && secondsLeft > 0 && secondsLeft <= WARNING_THRESHOLD && (
        <div className="session-timer-warning-overlay">
          <div className="session-timer-warning-card">
            <Timer size={28} />
            <p>Only {Math.ceil(secondsLeft / 60)} minute{Math.ceil(secondsLeft / 60) !== 1 ? 's' : ''} left!</p>
            <button onClick={() => setShowWarning(false)}>OK</button>
          </div>
        </div>
      )}
    </>
  );
}
