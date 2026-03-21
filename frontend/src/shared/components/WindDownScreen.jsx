import { useState, useEffect, useCallback } from 'react';
import './WindDownScreen.css';

const STAR_COLORS = ['#fbbf24', '#fde68a', '#f472b6', '#a78bfa', '#38bdf8'];
const STAR_COUNT = 20;

function prefersReducedMotion() {
  return (
    typeof window !== 'undefined' &&
    window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
  );
}

/**
 * WindDownScreen — magical goodbye overlay for session endings.
 * CSS-only animations reusing CelebrationOverlay's star particle pattern.
 *
 * Props:
 *   childNames       — array of two strings, e.g. ['Ale', 'Sofi']
 *   duration         — total animation duration in ms (default 8000)
 *   onComplete       — callback when animation finishes (navigate to landing)
 *   adventureSummary — optional string for adventure summary text
 */
export default function WindDownScreen({
  childNames = [],
  duration = 8000,
  onComplete,
  adventureSummary,
}) {
  const [phase, setPhase] = useState('stars'); // 'stars' -> 'farewell' -> 'dark'
  const reduced = prefersReducedMotion();

  const name1 = childNames[0] || 'Friend';
  const name2 = childNames[1] || 'Friend';

  const stableOnComplete = useCallback(() => {
    if (onComplete) onComplete();
  }, [onComplete]);

  useEffect(() => {
    // Phase transitions: stars (40%) -> farewell (40%) -> dark (20%) -> complete
    const starsDuration = duration * 0.4;
    const farewellDuration = duration * 0.4;

    const t1 = setTimeout(() => setPhase('farewell'), starsDuration);
    const t2 = setTimeout(() => setPhase('dark'), starsDuration + farewellDuration);
    const t3 = setTimeout(stableOnComplete, duration);

    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
      clearTimeout(t3);
    };
  }, [duration, stableOnComplete]);

  // Generate star particles (skip for reduced motion)
  const stars = reduced
    ? []
    : Array.from({ length: STAR_COUNT }, (_, i) => ({
        x: Math.random() * 100,
        delay: Math.random() * (duration * 0.3),
        dur: 1500 + Math.random() * 2000,
        color: STAR_COLORS[i % STAR_COLORS.length],
        scale: 0.5 + Math.random() * 0.8,
      }));

  return (
    <div
      className={`wind-down wind-down--${phase}`}
      style={{ '--wd-duration': `${duration}ms` }}
      role="status"
      aria-live="assertive"
    >
      {/* Star-trail particles */}
      {stars.map((s, i) => (
        <span
          key={i}
          className="wind-down__star"
          style={{
            '--x': s.x,
            '--delay': `${s.delay}ms`,
            '--star-dur': `${s.dur}ms`,
            '--color': s.color,
            '--scale': s.scale,
          }}
          aria-hidden="true"
        />
      ))}

      {/* Goodbye message */}
      <div className="wind-down__message">
        <span className="wind-down__emoji" aria-hidden="true">
          🌙
        </span>
        <h2 className="wind-down__title">
          Great adventure, {name1} &amp; {name2}!
        </h2>
        {adventureSummary && (
          <p className="wind-down__summary">{adventureSummary}</p>
        )}
        <p className="wind-down__farewell">See you next time, storytellers ✨</p>
      </div>
    </div>
  );
}
