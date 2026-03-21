import { useDrawingStore } from '../../../stores/drawingStore';
import './DrawingCountdown.css';

const RADIUS = 20;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

/**
 * Get ring color based on percentage of time remaining.
 * >= 30%: green, >= 10%: yellow, < 10%: red
 */
function getRingColor(percentage) {
  if (percentage >= 0.3) return '#43A047';
  if (percentage >= 0.1) return '#F9A825';
  return '#E53935';
}

/**
 * DrawingCountdown — compact circular SVG countdown ring.
 *
 * Reads `remainingTime` and `duration` from the drawing store.
 * Renders a circular ring with stroke-dashoffset to indicate progress,
 * and displays the remaining seconds as centered text.
 */
export default function DrawingCountdown() {
  const remainingTime = useDrawingStore((s) => s.remainingTime);
  const duration = useDrawingStore((s) => s.duration);

  const percentage = duration > 0 ? remainingTime / duration : 0;
  const dashOffset = CIRCUMFERENCE * (1 - percentage);
  const color = getRingColor(percentage);

  return (
    <div
      className={`drawing-countdown${remainingTime < 10 && remainingTime > 0 ? ' drawing-countdown--urgent' : ''}`}
      role="timer"
      aria-label={`${remainingTime} seconds remaining`}
    >
      <svg
        className="drawing-countdown-ring"
        viewBox="0 0 48 48"
        width="48"
        height="48"
      >
        {/* Background track */}
        <circle
          className="drawing-countdown-track"
          cx="24"
          cy="24"
          r={RADIUS}
          fill="none"
          strokeWidth="4"
        />
        {/* Animated progress ring */}
        <circle
          className="drawing-countdown-progress"
          cx="24"
          cy="24"
          r={RADIUS}
          fill="none"
          strokeWidth="4"
          stroke={color}
          strokeDasharray={CIRCUMFERENCE}
          strokeDashoffset={dashOffset}
          strokeLinecap="round"
        />
      </svg>
      <span className="drawing-countdown-text" style={{ color }}>
        {remainingTime}
      </span>
    </div>
  );
}
