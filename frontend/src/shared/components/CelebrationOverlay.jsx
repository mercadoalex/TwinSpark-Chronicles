import { useState, useEffect, useRef } from 'react';
import { useSceneAudioStore } from '../../stores/sceneAudioStore';
import './CelebrationOverlay.css';

const DEFAULT_COLORS = {
  confetti: ['#fbbf24', '#f472b6', '#a78bfa', '#34d399', '#fb7185', '#38bdf8', '#e879f9'],
  sparkle: ['#fbbf24', '#fde68a', '#fff'],
  'star-shower': ['#fbbf24', '#fde68a', '#f472b6'],
  shimmer: ['rgba(255,255,255,0.6)'],
};

const TYPE_CLASS_MAP = {
  confetti: 'celebration-particle--confetti',
  sparkle: 'celebration-particle--sparkle',
  'star-shower': 'celebration-particle--star',
  shimmer: 'celebration-particle--shimmer',
};

const MAX_PARTICLES = 100;

function prefersReducedMotion() {
  return (
    typeof window !== 'undefined' &&
    window.matchMedia &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches
  );
}

/**
 * CelebrationOverlay — lightweight particle celebration component.
 * Pure CSS animations, no canvas, no requestAnimationFrame.
 */
export default function CelebrationOverlay({
  type = 'confetti',
  duration = 2500,
  particleCount = 50,
  origin,
  colors,
}) {
  const [visible, setVisible] = useState(true);
  const timerRef = useRef(null);

  const clampedCount = Math.min(Math.max(particleCount, 0), MAX_PARTICLES);
  const palette = colors || DEFAULT_COLORS[type] || DEFAULT_COLORS.confetti;
  const particleClass = TYPE_CLASS_MAP[type] || TYPE_CLASS_MAP.confetti;

  useEffect(() => {
    timerRef.current = setTimeout(() => setVisible(false), duration);
    // Play celebration SFX on mount
    try { useSceneAudioStore.getState().playSfx('celebration'); } catch { /* silent */ }
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [duration]);

  // Respect prefers-reduced-motion
  if (prefersReducedMotion()) return null;
  if (!visible) return null;

  const particles = Array.from({ length: clampedCount }, (_, i) => {
    const x = origin ? origin.x + (Math.random() - 0.5) * 40 : Math.random() * 100;
    const y = origin ? origin.y + (Math.random() - 0.5) * 40 : Math.random() * 100;
    const delay = Math.random() * (duration * 0.4);
    const rotation = Math.random() * 720 - 360;
    const color = palette[i % palette.length];
    const scale = 0.5 + Math.random();

    return (
      <span
        key={i}
        className={`celebration-particle ${particleClass}`}
        style={{
          '--x': x,
          '--y': y,
          '--delay': `${delay}ms`,
          '--rotation': rotation,
          '--color': color,
          '--scale': scale,
          '--duration': `${duration}ms`,
        }}
      />
    );
  });

  return (
    <div className="celebration-overlay" aria-hidden="true">
      {particles}
    </div>
  );
}
