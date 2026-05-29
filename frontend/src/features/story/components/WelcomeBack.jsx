import React, { useEffect, useRef } from 'react';
import './WelcomeBack.css';

/**
 * WelcomeBack — Brief "Welcome back!" animation shown on session resume.
 *
 * Displays both twins' avatars with a fun bounce-in entrance and a
 * "Welcome back!" message. Auto-dismisses after 2 seconds.
 * Supports reduced-motion preferences.
 *
 * Requirements: 7.2, 8.2, 8.7
 *
 * @param {Object} props
 * @param {Object} props.twinConfig - Twin configuration with twin1 and twin2
 * @param {Object} props.twinConfig.twin1 - First twin { name, avatar, color }
 * @param {Object} props.twinConfig.twin2 - Second twin { name, avatar, color }
 * @param {() => void} [props.onComplete] - Callback when animation finishes
 */
function WelcomeBack({ twinConfig, onComplete }) {
  const timerRef = useRef(null);

  const twin1 = twinConfig?.twin1 || { name: 'Twin 1', avatar: '🦊', color: '#FF6B6B' };
  const twin2 = twinConfig?.twin2 || { name: 'Twin 2', avatar: '🦄', color: '#6B9FFF' };

  // Auto-dismiss after 2 seconds (Req 7.1)
  useEffect(() => {
    timerRef.current = setTimeout(() => {
      if (onComplete) {
        onComplete();
      }
    }, 2000);

    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
    };
  }, [onComplete]);

  return (
    <div
      className="welcome-back"
      role="status"
      aria-label={`Welcome back ${twin1.name} and ${twin2.name}`}
    >
      {/* Avatars bounce in from sides */}
      <div className="welcome-back__avatars">
        <div
          className="welcome-back__avatar welcome-back__avatar--left"
          style={{ '--twin-color': twin1.color }}
        >
          <span className="welcome-back__avatar-icon" aria-hidden="true">
            {twin1.avatar}
          </span>
        </div>

        <div
          className="welcome-back__avatar welcome-back__avatar--right"
          style={{ '--twin-color': twin2.color }}
        >
          <span className="welcome-back__avatar-icon" aria-hidden="true">
            {twin2.avatar}
          </span>
        </div>
      </div>

      {/* Welcome message */}
      <div className="welcome-back__message" aria-hidden="true">
        <span className="welcome-back__sparkle">✨</span>
        <span className="welcome-back__text">Welcome back!</span>
        <span className="welcome-back__sparkle">✨</span>
      </div>
    </div>
  );
}

export default WelcomeBack;
