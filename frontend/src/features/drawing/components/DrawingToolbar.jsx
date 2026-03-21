import { useCallback } from 'react';
import {
  useDrawingStore,
  PALETTE_COLORS,
  BRUSH_SIZES,
  STAMP_SHAPES,
} from '../../../stores/drawingStore';
import { usePhotoUxEffects } from '../../../shared/hooks/usePhotoUxEffects';
import './DrawingToolbar.css';

const STAMP_ICONS = {
  star: '⭐',
  heart: '❤️',
  circle: '⚫',
  lightning: '⚡',
};

const BRUSH_SIZE_LABELS = {
  thin: 'Thin',
  medium: 'Medium',
  thick: 'Thick',
};

/**
 * Keyboard handler factory for lists of items.
 * Arrow keys cycle through items, Enter selects the focused one.
 */
function makeKeyHandler(items, currentIndex, onSelect) {
  return (e) => {
    if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
      e.preventDefault();
      const next = (currentIndex + 1) % items.length;
      onSelect(items[next]);
    } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
      e.preventDefault();
      const prev = (currentIndex - 1 + items.length) % items.length;
      onSelect(items[prev]);
    } else if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      onSelect(items[currentIndex]);
    }
  };
}

/**
 * DrawingToolbar — color palette, brush sizes, eraser, undo, stamp tools.
 *
 * @param {{ siblingId: string }} props
 */
export default function DrawingToolbar({ siblingId }) {
  const selectedColor = useDrawingStore((s) => s.selectedColor);
  const selectedBrushSize = useDrawingStore((s) => s.selectedBrushSize);
  const selectedTool = useDrawingStore((s) => s.selectedTool);
  const selectedStamp = useDrawingStore((s) => s.selectedStamp);
  const undoStacks = useDrawingStore((s) => s.undoStacks);

  const setColor = useDrawingStore((s) => s.setColor);
  const setBrushSize = useDrawingStore((s) => s.setBrushSize);
  const setTool = useDrawingStore((s) => s.setTool);
  const setStamp = useDrawingStore((s) => s.setStamp);
  const undoLastStroke = useDrawingStore((s) => s.undoLastStroke);

  const { playSnap, playWhoosh, haptic } = usePhotoUxEffects();

  const undoStack = undoStacks[siblingId] || [];
  const isUndoDisabled = undoStack.length === 0;
  const isStampMode = selectedTool === 'stamp';

  // ── Color palette ────────────────────────────────────
  const colorIndex = PALETTE_COLORS.indexOf(selectedColor);

  const handleColorKey = useCallback(
    (e) => {
      const idx = PALETTE_COLORS.indexOf(selectedColor);
      const handler = makeKeyHandler(PALETTE_COLORS, idx, (c) => {
        setColor(c);
        if (selectedTool === 'eraser') setTool('brush');
      });
      handler(e);
    },
    [selectedColor, selectedTool, setColor, setTool]
  );

  const handleColorClick = useCallback(
    (color) => {
      setColor(color);
      if (selectedTool === 'eraser') setTool('brush');
      playSnap();
      haptic(30);
    },
    [setColor, setTool, selectedTool, playSnap, haptic]
  );

  // ── Brush sizes ──────────────────────────────────────
  const brushKeys = Object.keys(BRUSH_SIZES);
  const brushIndex = brushKeys.indexOf(selectedBrushSize);

  const handleBrushKey = useCallback(
    (e) => {
      const idx = brushKeys.indexOf(selectedBrushSize);
      const handler = makeKeyHandler(brushKeys, idx, (size) => {
        setBrushSize(size);
        if (selectedTool !== 'brush') setTool('brush');
      });
      handler(e);
    },
    [selectedBrushSize, selectedTool, setBrushSize, setTool]
  );

  const handleBrushClick = useCallback(
    (size) => {
      setBrushSize(size);
      if (selectedTool !== 'brush') setTool('brush');
    },
    [setBrushSize, setTool, selectedTool]
  );

  // ── Eraser ───────────────────────────────────────────
  const handleEraserClick = useCallback(() => {
    setTool(selectedTool === 'eraser' ? 'brush' : 'eraser');
    playWhoosh();
  }, [setTool, selectedTool, playWhoosh]);

  // ── Undo ─────────────────────────────────────────────
  const handleUndo = useCallback(() => {
    if (!isUndoDisabled) undoLastStroke(siblingId);
  }, [isUndoDisabled, undoLastStroke, siblingId]);

  // ── Stamp mode toggle ────────────────────────────────
  const handleStampToggle = useCallback(() => {
    if (isStampMode) {
      setTool('brush');
      setStamp(null);
    } else {
      setTool('stamp');
      if (!selectedStamp) setStamp(STAMP_SHAPES[0]);
    }
  }, [isStampMode, setTool, setStamp, selectedStamp]);

  // ── Stamp shape selection ────────────────────────────
  const stampIndex = STAMP_SHAPES.indexOf(selectedStamp);

  const handleStampKey = useCallback(
    (e) => {
      const idx = STAMP_SHAPES.indexOf(selectedStamp);
      const handler = makeKeyHandler(STAMP_SHAPES, idx >= 0 ? idx : 0, (shape) => {
        setStamp(shape);
        if (selectedTool !== 'stamp') setTool('stamp');
      });
      handler(e);
    },
    [selectedStamp, selectedTool, setStamp, setTool]
  );

  const handleStampClick = useCallback(
    (shape) => {
      setStamp(shape);
      if (selectedTool !== 'stamp') setTool('stamp');
      playSnap();
      haptic(30);
    },
    [setStamp, setTool, selectedTool, playSnap, haptic]
  );

  return (
    <div className="drawing-toolbar" role="toolbar" aria-label="Drawing tools">
      {/* ── Color Palette ─────────────────────────── */}
      <div className="drawing-toolbar__section">
        <span className="drawing-toolbar__label">Color</span>
        <div className="drawing-toolbar__colors" role="radiogroup" aria-label="Color palette">
          {PALETTE_COLORS.map((color, i) => (
            <button
              key={color}
              className={`drawing-toolbar__color-swatch${
                selectedColor === color && selectedTool !== 'eraser'
                  ? ' drawing-toolbar__color-swatch--selected'
                  : ''
              }`}
              style={{ backgroundColor: color, '--swatch-color': color }}
              onClick={() => handleColorClick(color)}
              onKeyDown={handleColorKey}
              tabIndex={i === (colorIndex >= 0 ? colorIndex : 0) ? 0 : -1}
              role="radio"
              aria-checked={selectedColor === color && selectedTool !== 'eraser'}
              aria-label={`Color ${i + 1}`}
            />
          ))}
        </div>
      </div>

      {/* ── Brush Size ────────────────────────────── */}
      <div className="drawing-toolbar__section">
        <span className="drawing-toolbar__label">Size</span>
        <div className="drawing-toolbar__brushes" role="radiogroup" aria-label="Brush size">
          {brushKeys.map((size, i) => (
            <button
              key={size}
              className={`drawing-toolbar__brush-btn${
                selectedBrushSize === size ? ' drawing-toolbar__brush-btn--selected' : ''
              }`}
              onClick={() => handleBrushClick(size)}
              onKeyDown={handleBrushKey}
              tabIndex={i === (brushIndex >= 0 ? brushIndex : 0) ? 0 : -1}
              role="radio"
              aria-checked={selectedBrushSize === size}
              aria-label={`${BRUSH_SIZE_LABELS[size]} brush`}
            >
              <span
                className="drawing-toolbar__brush-dot"
                style={{
                  width: BRUSH_SIZES[size] * 3,
                  height: BRUSH_SIZES[size] * 3,
                }}
              />
            </button>
          ))}
        </div>
      </div>

      {/* ── Tools (eraser, undo, stamp toggle) ────── */}
      <div className="drawing-toolbar__section">
        <span className="drawing-toolbar__label">Tools</span>
        <div className="drawing-toolbar__tools">
          <button
            className={`drawing-toolbar__tool-btn${
              selectedTool === 'eraser' ? ' drawing-toolbar__tool-btn--active' : ''
            }`}
            onClick={handleEraserClick}
            aria-pressed={selectedTool === 'eraser'}
            aria-label="Eraser"
          >
            <span className="drawing-toolbar__tool-icon" aria-hidden="true">🧹</span>
            <span className="drawing-toolbar__tool-text">Eraser</span>
          </button>

          <button
            className={`drawing-toolbar__tool-btn${
              isUndoDisabled ? ' drawing-toolbar__tool-btn--disabled' : ''
            }`}
            onClick={handleUndo}
            disabled={isUndoDisabled}
            aria-label="Undo last stroke"
            aria-disabled={isUndoDisabled}
          >
            <span className="drawing-toolbar__tool-icon" aria-hidden="true">↩️</span>
            <span className="drawing-toolbar__tool-text">Undo</span>
          </button>

          <button
            className={`drawing-toolbar__tool-btn${
              isStampMode ? ' drawing-toolbar__tool-btn--active' : ''
            }`}
            onClick={handleStampToggle}
            aria-pressed={isStampMode}
            aria-label="Stamp mode"
          >
            <span className="drawing-toolbar__tool-icon" aria-hidden="true">⭐</span>
            <span className="drawing-toolbar__tool-text">Stamps</span>
          </button>
        </div>
      </div>

      {/* ── Stamp Shapes (visible when stamp mode active) */}
      {isStampMode && (
        <div className="drawing-toolbar__section">
          <span className="drawing-toolbar__label">Shape</span>
          <div className="drawing-toolbar__stamps" role="radiogroup" aria-label="Stamp shape">
            {STAMP_SHAPES.map((shape, i) => (
              <button
                key={shape}
                className={`drawing-toolbar__stamp-btn${
                  selectedStamp === shape ? ' drawing-toolbar__stamp-btn--selected' : ''
                }`}
                onClick={() => handleStampClick(shape)}
                onKeyDown={handleStampKey}
                tabIndex={i === (stampIndex >= 0 ? stampIndex : 0) ? 0 : -1}
                role="radio"
                aria-checked={selectedStamp === shape}
                aria-label={`${shape} stamp`}
              >
                <span aria-hidden="true">{STAMP_ICONS[shape]}</span>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
