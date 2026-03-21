import { useRef, useEffect, useCallback, useState } from 'react';
import { useDrawingStore, BRUSH_SIZES, STAMP_SHAPES } from '../../../stores/drawingStore';
import { websocketService } from '../../session/services/websocketService';
import { usePhotoUxEffects } from '../../../shared/hooks/usePhotoUxEffects';
import CelebrationOverlay from '../../../shared/components/CelebrationOverlay';
import DrawingToolbar from './DrawingToolbar';
import DrawingCountdown from './DrawingCountdown';
import './DrawingCanvas.css';

/**
 * Stamp shape path renderers — draw pre-made shapes at a given position on canvas.
 * Each function draws centered at (cx, cy) with the given size.
 */
const STAMP_RENDERERS = {
  star: (ctx, cx, cy, size) => {
    const spikes = 5;
    const outerR = size;
    const innerR = size * 0.4;
    ctx.beginPath();
    for (let i = 0; i < spikes * 2; i++) {
      const r = i % 2 === 0 ? outerR : innerR;
      const angle = (Math.PI / 2) * -1 + (Math.PI / spikes) * i;
      const x = cx + Math.cos(angle) * r;
      const y = cy + Math.sin(angle) * r;
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.closePath();
    ctx.fill();
  },
  heart: (ctx, cx, cy, size) => {
    ctx.beginPath();
    const topY = cy - size * 0.4;
    ctx.moveTo(cx, cy + size * 0.6);
    ctx.bezierCurveTo(cx - size, cy - size * 0.2, cx - size * 0.5, topY - size * 0.5, cx, topY + size * 0.1);
    ctx.bezierCurveTo(cx + size * 0.5, topY - size * 0.5, cx + size, cy - size * 0.2, cx, cy + size * 0.6);
    ctx.closePath();
    ctx.fill();
  },
  circle: (ctx, cx, cy, size) => {
    ctx.beginPath();
    ctx.arc(cx, cy, size, 0, Math.PI * 2);
    ctx.fill();
  },
  lightning: (ctx, cx, cy, size) => {
    ctx.beginPath();
    ctx.moveTo(cx - size * 0.2, cy - size);
    ctx.lineTo(cx + size * 0.4, cy - size);
    ctx.lineTo(cx, cy - size * 0.1);
    ctx.lineTo(cx + size * 0.3, cy - size * 0.1);
    ctx.lineTo(cx - size * 0.3, cy + size);
    ctx.lineTo(cx, cy + size * 0.1);
    ctx.lineTo(cx - size * 0.3, cy + size * 0.1);
    ctx.closePath();
    ctx.fill();
  },
};

const CANVAS_BG = '#FFFFFF';

/**
 * DrawingCanvas — core collaborative drawing component.
 *
 * Renders an HTML5 Canvas with multi-touch support, real-time stroke sync
 * via WebSocket, and inline toolbar/countdown (delegated to child components).
 *
 * @param {{ prompt: string, duration: number, siblingId: string, profiles: object, onComplete: function }} props
 */
export default function DrawingCanvas({ prompt, duration, siblingId, profiles, onComplete }) {
  const canvasRef = useRef(null);
  const containerRef = useRef(null);
  const activePointersRef = useRef(new Map());
  const currentStrokeRef = useRef(null);
  const wsUnsubscribersRef = useRef([]);

  const [phase, setPhase] = useState('entering'); // entering | active | exiting | done
  const [announcement, setAnnouncement] = useState('');
  const [showCelebration, setShowCelebration] = useState(false);

  const { playChime, playWhoosh, haptic, hapticPattern } = usePhotoUxEffects();

  // Drawing store state
  const isActive = useDrawingStore((s) => s.isActive);
  const strokes = useDrawingStore((s) => s.strokes);
  const selectedColor = useDrawingStore((s) => s.selectedColor);
  const selectedBrushSize = useDrawingStore((s) => s.selectedBrushSize);
  const selectedTool = useDrawingStore((s) => s.selectedTool);
  const selectedStamp = useDrawingStore((s) => s.selectedStamp);
  const syncStatus = useDrawingStore((s) => s.syncStatus);

  // Store actions
  const addStroke = useDrawingStore((s) => s.addStroke);
  const addRemoteStroke = useDrawingStore((s) => s.addRemoteStroke);
  const queueStroke = useDrawingStore((s) => s.queueStroke);
  const endSession = useDrawingStore((s) => s.endSession);

  // ── Helpers ──────────────────────────────────────────

  /** Get effective color (eraser uses canvas background) */
  const getEffectiveColor = useCallback(() => {
    return selectedTool === 'eraser' ? CANVAS_BG : selectedColor;
  }, [selectedTool, selectedColor]);

  /** Get effective brush pixel size */
  const getEffectiveBrushPx = useCallback(() => {
    return BRUSH_SIZES[selectedBrushSize] || BRUSH_SIZES.medium;
  }, [selectedBrushSize]);

  /** Normalize pointer coords to 0.0–1.0 range */
  const normalizeCoords = useCallback((clientX, clientY) => {
    const canvas = canvasRef.current;
    if (!canvas) return { x: 0, y: 0 };
    const rect = canvas.getBoundingClientRect();
    return {
      x: Math.max(0, Math.min(1, (clientX - rect.left) / rect.width)),
      y: Math.max(0, Math.min(1, (clientY - rect.top) / rect.height)),
    };
  }, []);

  // ── Canvas rendering ─────────────────────────────────

  /** Clear canvas and redraw all strokes from store */
  const redrawCanvas = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const w = canvas.width;
    const h = canvas.height;

    // Clear to white
    ctx.fillStyle = CANVAS_BG;
    ctx.fillRect(0, 0, w, h);

    // Redraw all strokes
    for (const stroke of strokes) {
      if (stroke.tool === 'stamp' && stroke.stamp_shape && stroke.points.length > 0) {
        renderStamp(ctx, stroke, w, h);
      } else {
        renderBrushStroke(ctx, stroke, w, h);
      }
    }
  }, [strokes]);

  /** Render a single brush/eraser stroke */
  const renderBrushStroke = (ctx, stroke, w, h) => {
    if (!stroke.points || stroke.points.length === 0) return;
    ctx.save();
    ctx.strokeStyle = stroke.color;
    ctx.lineWidth = stroke.brush_size;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.beginPath();
    const p0 = stroke.points[0];
    ctx.moveTo(p0.x * w, p0.y * h);
    for (let i = 1; i < stroke.points.length; i++) {
      ctx.lineTo(stroke.points[i].x * w, stroke.points[i].y * h);
    }
    ctx.stroke();
    ctx.restore();
  };

  /** Render a stamp shape */
  const renderStamp = (ctx, stroke, w, h) => {
    const renderer = STAMP_RENDERERS[stroke.stamp_shape];
    if (!renderer || stroke.points.length === 0) return;
    ctx.save();
    ctx.fillStyle = stroke.color;
    const p = stroke.points[0];
    renderer(ctx, p.x * w, p.y * h, stroke.brush_size * 3);
    ctx.restore();
  };

  /** Render a stroke incrementally (for live drawing) */
  const renderStrokeLive = useCallback((stroke) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const w = canvas.width;
    const h = canvas.height;

    if (stroke.tool === 'stamp' && stroke.stamp_shape) {
      renderStamp(ctx, stroke, w, h);
      return;
    }

    if (stroke.points.length < 2) return;
    ctx.save();
    ctx.strokeStyle = stroke.color;
    ctx.lineWidth = stroke.brush_size;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.beginPath();
    const prev = stroke.points[stroke.points.length - 2];
    const curr = stroke.points[stroke.points.length - 1];
    ctx.moveTo(prev.x * w, prev.y * h);
    ctx.lineTo(curr.x * w, curr.y * h);
    ctx.stroke();
    ctx.restore();
  }, []);

  // ── Pointer event handlers ───────────────────────────

  const handlePointerDown = useCallback((e) => {
    if (phase !== 'active') return;
    const canvas = canvasRef.current;
    if (!canvas) return;

    canvas.setPointerCapture(e.pointerId);
    const coords = normalizeCoords(e.clientX, e.clientY);

    if (selectedTool === 'stamp' && selectedStamp) {
      // Stamp mode: single tap creates a stamp stroke
      const stamp = {
        sibling_id: siblingId,
        points: [coords],
        color: getEffectiveColor(),
        brush_size: getEffectiveBrushPx(),
        timestamp: new Date().toISOString(),
        tool: 'stamp',
        stamp_shape: selectedStamp,
      };
      commitStroke(stamp);
      playChime();
      haptic(50);
      return;
    }

    // Brush / eraser: start a new stroke
    const stroke = {
      sibling_id: siblingId,
      points: [coords],
      color: getEffectiveColor(),
      brush_size: getEffectiveBrushPx(),
      timestamp: new Date().toISOString(),
      tool: selectedTool,
      stamp_shape: null,
    };
    activePointersRef.current.set(e.pointerId, stroke);
    currentStrokeRef.current = stroke;
  }, [phase, siblingId, selectedTool, selectedStamp, normalizeCoords, getEffectiveColor, getEffectiveBrushPx, playChime, haptic]);

  const handlePointerMove = useCallback((e) => {
    if (phase !== 'active') return;
    const stroke = activePointersRef.current.get(e.pointerId);
    if (!stroke) return;

    // Use coalesced events for smoother input
    const events = e.getCoalescedEvents ? e.getCoalescedEvents() : [e];
    for (const ce of events) {
      const coords = normalizeCoords(ce.clientX, ce.clientY);
      stroke.points.push(coords);
    }

    // Live render the latest segment
    renderStrokeLive(stroke);
  }, [phase, normalizeCoords, renderStrokeLive]);

  const handlePointerUp = useCallback((e) => {
    const stroke = activePointersRef.current.get(e.pointerId);
    activePointersRef.current.delete(e.pointerId);
    if (!stroke || stroke.points.length === 0) return;

    commitStroke(stroke);
    currentStrokeRef.current = null;
  }, []);

  /** Commit a completed stroke: add to store, send via WebSocket */
  const commitStroke = useCallback((stroke) => {
    addStroke(stroke);

    const message = { type: 'DRAWING_STROKE', stroke };
    if (websocketService.isConnected()) {
      websocketService.send(message);
    } else {
      queueStroke(stroke);
    }
  }, [addStroke, queueStroke]);

  const handlePointerCancel = useCallback((e) => {
    // Treat cancel same as up — commit whatever we have
    handlePointerUp(e);
  }, [handlePointerUp]);

  // ── "We're Done!" handler ────────────────────────────

  const handleDone = useCallback(() => {
    playChime();
    hapticPattern([50, 30, 80]);
    setShowCelebration(true);
    websocketService.send({ type: 'DRAWING_EARLY_END' });
    if (onComplete) onComplete(strokes);
  }, [onComplete, strokes, playChime, hapticPattern]);

  // ── Canvas resize ────────────────────────────────────

  const resizeCanvas = useCallback(() => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;

    const rect = container.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    const w = Math.max(300, rect.width);
    const h = Math.max(300, rect.height);

    canvas.width = w * dpr;
    canvas.height = h * dpr;
    canvas.style.width = `${w}px`;
    canvas.style.height = `${h}px`;

    const ctx = canvas.getContext('2d');
    ctx.scale(dpr, dpr);

    // Redraw after resize
    redrawCanvas();
  }, [redrawCanvas]);

  // ── Effects ──────────────────────────────────────────

  // Setup canvas + resize observer
  useEffect(() => {
    resizeCanvas();
    const handleResize = () => resizeCanvas();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [resizeCanvas]);

  // Redraw when strokes change (handles undo)
  useEffect(() => {
    redrawCanvas();
  }, [strokes, redrawCanvas]);

  // Entrance animation → active phase
  useEffect(() => {
    if (phase === 'entering') {
      playWhoosh();
      setAnnouncement('Drawing started');
      const timer = setTimeout(() => setPhase('active'), 500);
      return () => clearTimeout(timer);
    }
  }, [phase, playWhoosh]);

  // Listen for WebSocket messages: remote strokes + session end
  useEffect(() => {
    const unsubStroke = websocketService.on('DRAWING_STROKE', (data) => {
      if (data.stroke && data.stroke.sibling_id !== siblingId) {
        addRemoteStroke(data.stroke);
      }
    });

    const unsubEnd = websocketService.on('DRAWING_END', () => {
      playChime();
      hapticPattern([50, 30, 80]);
      setShowCelebration(true);
      setPhase('exiting');
      setAnnouncement('Drawing complete');
      endSession();
      setTimeout(() => setPhase('done'), 600);
    });

    wsUnsubscribersRef.current = [unsubStroke, unsubEnd];

    return () => {
      wsUnsubscribersRef.current.forEach((unsub) => unsub());
      wsUnsubscribersRef.current = [];
    };
  }, [siblingId, addRemoteStroke, endSession, playChime, hapticPattern]);

  // Announce tool changes
  useEffect(() => {
    const toolLabel = selectedTool === 'stamp' && selectedStamp
      ? `Stamp: ${selectedStamp}`
      : selectedTool;
    setAnnouncement(`Tool: ${toolLabel}`);
  }, [selectedTool, selectedStamp]);

  // ── Render ───────────────────────────────────────────

  const phaseClass = phase === 'entering'
    ? 'drawing-canvas--entering'
    : phase === 'exiting'
      ? 'drawing-canvas--exiting'
      : '';

  return (
    <div
      className={`drawing-canvas-overlay ${phaseClass}`}
      role="region"
      aria-label="Collaborative drawing canvas"
    >
      {/* ARIA live region for announcements */}
      <div className="sr-only" aria-live="polite" aria-atomic="true">
        {announcement}
      </div>

      <div className="drawing-canvas-layout">
        {/* Prompt display */}
        <div className="drawing-canvas-header">
          <p className="drawing-canvas-prompt">{prompt}</p>
          <DrawingCountdown />
          <button
            className="drawing-canvas-done-btn"
            onClick={handleDone}
            aria-label="End drawing session"
          >
            We're Done!
          </button>
        </div>

        <div className="drawing-canvas-body">
          {/* Canvas area */}
          <div className="drawing-canvas-container" ref={containerRef}>
            <canvas
              ref={canvasRef}
              className="drawing-canvas"
              onPointerDown={handlePointerDown}
              onPointerMove={handlePointerMove}
              onPointerUp={handlePointerUp}
              onPointerCancel={handlePointerCancel}
              aria-label={`Drawing canvas. Prompt: ${prompt}`}
              role="img"
            />
          </div>

          {/* Toolbar */}
          <DrawingToolbar siblingId={siblingId} />
        </div>
      </div>

      {showCelebration && <CelebrationOverlay type="star-shower" duration={2500} particleCount={60} colors={['#fbbf24', '#fb7185', '#a78bfa', '#f472b6']} />}
    </div>
  );
}
