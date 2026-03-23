import React, { useEffect } from 'react';

/* ── CSS keyframe animations (injected once) ── */
const STYLE_ID = 'virtual-keyboard-keyframes';
function injectKeyframes() {
  if (document.getElementById(STYLE_ID)) return;
  const sheet = document.createElement('style');
  sheet.id = STYLE_ID;
  sheet.textContent = `
    @keyframes vk-fade-in {
      0%   { opacity: 0; transform: scale(0.92); }
      100% { opacity: 1; transform: scale(1); }
    }
    @keyframes vk-key-pop {
      0%   { transform: scale(1); }
      50%  { transform: scale(0.9); }
      100% { transform: scale(1); }
    }
  `;
  document.head.appendChild(sheet);
}

/* ── Keyboard layout: 7 columns × 4 rows + bottom row ── */
const ROWS = [
  ['Q', 'W', 'E', 'R', 'T', 'Y', 'U'],
  ['I', 'O', 'P', 'A', 'S', 'D', 'F'],
  ['G', 'H', 'J', 'K', 'L', 'Z', 'X'],
  ['C', 'V', 'B', 'N', 'M', '←', '␣'],
];

/* ── Color palette for letter keys — fun gradients for kids ── */
const KEY_COLORS = [
  'linear-gradient(135deg, #f472b6, #ec4899)',
  'linear-gradient(135deg, #a78bfa, #8b5cf6)',
  'linear-gradient(135deg, #60a5fa, #3b82f6)',
  'linear-gradient(135deg, #34d399, #10b981)',
  'linear-gradient(135deg, #fbbf24, #f59e0b)',
  'linear-gradient(135deg, #fb7185, #f43f5e)',
  'linear-gradient(135deg, #38bdf8, #0ea5e9)',
];

function getKeyColor(index) {
  return KEY_COLORS[index % KEY_COLORS.length];
}

/* ── Styles ── */
const styles = {
  overlay: {
    position: 'fixed',
    inset: 0,
    zIndex: 9999,
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    background: 'rgba(7, 11, 26, 0.85)',
    backdropFilter: 'blur(8px)',
    animation: 'vk-fade-in 0.25s var(--ease-smooth) both',
  },
  panel: {
    background: 'rgba(21, 29, 53, 0.95)',
    border: '1px solid var(--color-glass-border)',
    borderRadius: 'var(--radius-lg)',
    padding: '24px',
    boxShadow: 'var(--shadow-float)',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '16px',
    maxWidth: '480px',
    width: '90vw',
  },
  display: {
    fontFamily: 'var(--font-display)',
    fontSize: '1.6rem',
    color: 'var(--color-gold)',
    background: 'var(--color-glass)',
    border: '2px solid var(--color-glass-border)',
    borderRadius: 'var(--radius-sm)',
    padding: '10px 20px',
    minHeight: '48px',
    width: '100%',
    textAlign: 'center',
    letterSpacing: '2px',
    wordBreak: 'break-all',
  },
  grid: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
    width: '100%',
  },
  row: {
    display: 'flex',
    justifyContent: 'center',
    gap: '6px',
  },
  key: {
    minWidth: '48px',
    minHeight: '48px',
    border: 'none',
    borderRadius: 'var(--radius-sm)',
    fontFamily: 'var(--font-display)',
    fontSize: '1.2rem',
    fontWeight: 700,
    color: '#fff',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    textShadow: '0 1px 3px rgba(0,0,0,0.3)',
    boxShadow: '0 3px 10px rgba(0,0,0,0.3)',
    transition: 'transform 0.1s var(--ease-bounce), box-shadow 0.1s',
    flex: '1 1 0',
  },
  backspaceKey: {
    background: 'linear-gradient(135deg, #fb7185, #e11d48)',
  },
  spaceKey: {
    background: 'linear-gradient(135deg, #38bdf8, #0284c7)',
  },
  doneButton: {
    minWidth: '48px',
    minHeight: '48px',
    border: 'none',
    borderRadius: 'var(--radius-md)',
    fontFamily: 'var(--font-display)',
    fontSize: '1.2rem',
    fontWeight: 700,
    color: '#fff',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '8px',
    padding: '10px 32px',
    background: 'linear-gradient(135deg, var(--color-gold), var(--color-amber))',
    boxShadow: '0 4px 20px rgba(251, 191, 36, 0.4)',
    textShadow: '0 1px 3px rgba(0,0,0,0.2)',
    transition: 'transform 0.1s var(--ease-bounce), box-shadow 0.1s',
  },
  cancelHint: {
    fontFamily: 'var(--font-body)',
    fontSize: '0.8rem',
    color: 'rgba(255,255,255,0.4)',
    marginTop: '-8px',
  },
};

export default function VirtualKeyboard({ targetValue, onCharacter, onBackspace, onDone, onCancel }) {
  useEffect(() => { injectKeyframes(); }, []);

  const handleKeyClick = (key) => {
    if (key === '←') {
      onBackspace();
    } else if (key === '␣') {
      onCharacter(' ');
    } else {
      onCharacter(key);
    }
  };

  let colorIndex = 0;

  return (
    <div style={styles.overlay} aria-label="Virtual keyboard" role="dialog">
      <div style={styles.panel}>
        {/* Current value display */}
        <div style={styles.display} aria-live="polite" aria-atomic="true">
          {targetValue || '\u00A0'}
        </div>

        {/* Key grid */}
        <div style={styles.grid} role="grid">
          {ROWS.map((row, rowIdx) => (
            <div key={rowIdx} style={styles.row} role="row">
              {row.map((key) => {
                const isBackspace = key === '←';
                const isSpace = key === '␣';
                const isSpecial = isBackspace || isSpace;

                let keyStyle;
                if (isBackspace) {
                  keyStyle = { ...styles.key, ...styles.backspaceKey };
                } else if (isSpace) {
                  keyStyle = { ...styles.key, ...styles.spaceKey };
                } else {
                  keyStyle = { ...styles.key, background: getKeyColor(colorIndex++) };
                }

                let ariaLabel;
                if (isBackspace) ariaLabel = 'Delete last letter';
                else if (isSpace) ariaLabel = 'Space';

                return (
                  <button
                    key={key}
                    role="gridcell"
                    style={keyStyle}
                    aria-label={ariaLabel}
                    onClick={() => handleKeyClick(key)}
                    type="button"
                  >
                    {key}
                  </button>
                );
              })}
            </div>
          ))}

          {/* Done row */}
          <div style={styles.row} role="row">
            <button
              role="gridcell"
              style={styles.doneButton}
              aria-label="Done"
              onClick={onDone}
              type="button"
            >
              ✓ Done
            </button>
          </div>
        </div>

        <span style={styles.cancelHint}>Press B to cancel</span>
      </div>
    </div>
  );
}
