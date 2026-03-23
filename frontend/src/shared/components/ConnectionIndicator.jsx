import React from 'react';
import { useGamepadStore } from '../../stores/gamepadStore';

const GAMEPAD_SVG = "M16.5 5.5c2.5 0 4.5 2 4.5 4.5 0 1.6-.8 3-2.1 3.9L17 18.5c-.3.6-.9 1-1.5 1h-7c-.7 0-1.2-.4-1.5-1l-1.9-4.6C3.8 13 3 11.6 3 10c0-2.5 2-4.5 4.5-4.5h9zM8 9H7v1.5H5.5V12H7v1.5h1V12h1.5v-1.5H8V9zm6.5 1.25a1.25 1.25 0 1 0 0 2.5 1.25 1.25 0 0 0 0-2.5zm3-2a1.25 1.25 0 1 0 0 2.5 1.25 1.25 0 0 0 0-2.5z";

// Child signature colors from the design system
const CHILD_COLORS = ['#f472b6', '#60a5fa'];

export default function ConnectionIndicator() {
  const gamepads = useGamepadStore((s) => s.gamepads);
  const connectedCount = useGamepadStore((s) => s.connectedCount);

  const label =
    connectedCount === 0
      ? 'No controllers connected'
      : connectedCount === 1
        ? '1 controller connected'
        : '2 controllers connected';

  return (
    <div style={styles.container}>
      <div style={styles.icons}>
        {gamepads.map((gp, i) => (
          <svg
            key={i}
            style={{
              ...styles.icon,
              opacity: gp ? 0.85 : 0.15,
              filter: gp ? `drop-shadow(0 0 6px ${CHILD_COLORS[i]})` : 'none',
            }}
            viewBox="0 0 24 24"
            fill={gp ? CHILD_COLORS[i] : 'rgba(255,255,255,0.3)'}
            xmlns="http://www.w3.org/2000/svg"
            aria-hidden="true"
          >
            <path d={GAMEPAD_SVG} />
          </svg>
        ))}
      </div>
      <div aria-live="polite" style={styles.srOnly}>
        {label}
      </div>
    </div>
  );
}

const styles = {
  container: {
    position: 'fixed',
    bottom: 16,
    right: 16,
    zIndex: 100,
    pointerEvents: 'none',
  },
  icons: {
    display: 'flex',
    gap: 6,
  },
  icon: {
    width: 22,
    height: 22,
    transition: 'opacity 0.3s ease-in-out, filter 0.3s ease-in-out',
  },
  srOnly: {
    position: 'absolute',
    width: 1,
    height: 1,
    overflow: 'hidden',
    clip: 'rect(0,0,0,0)',
  },
};
