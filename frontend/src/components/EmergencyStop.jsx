import React, { useState } from 'react';
import { ShieldOff } from 'lucide-react';
import './EmergencyStop.css';

/**
 * Fixed-position red emergency stop button.
 * Calls POST /api/emergency-stop/{sessionId}, then navigates to safe screen.
 * Handles API failure gracefully — always navigates, retries once in background.
 */
export default function EmergencyStop({ sessionId, onStop }) {
  const [stopping, setStopping] = useState(false);

  const handleStop = async () => {
    if (stopping) return;
    setStopping(true);

    let apiOk = false;
    try {
      const resp = await fetch(
        `http://localhost:8000/api/emergency-stop/${sessionId}`,
        { method: 'POST' }
      );
      apiOk = resp.ok;
    } catch (_) { /* will retry */ }

    // Always navigate to safe screen within 2s
    if (onStop) onStop();

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
  };

  return (
    <button
      className={`emergency-stop ${stopping ? 'emergency-stop--active' : ''}`}
      onClick={handleStop}
      aria-label="Emergency stop — end session immediately"
      disabled={stopping}
    >
      <ShieldOff size={22} />
    </button>
  );
}
