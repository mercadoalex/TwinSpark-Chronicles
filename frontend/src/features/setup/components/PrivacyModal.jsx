import React, { useRef } from 'react';
import { useFocusTrap } from '../../../shared/hooks';

const noop = () => {};

function PrivacyModal({ onAccept, t }) {
  const dialogRef = useRef(null);
  useFocusTrap(dialogRef, true, noop);

  return (
    <div className="privacy-overlay" style={{
      position: 'fixed', inset: 0,
      background: 'linear-gradient(160deg, #e8deff 0%, #dbeafe 40%, #fce7f3 80%)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      zIndex: 10000, padding: '20px',
    }}>
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="privacy-modal-heading"
        style={{
          padding: '40px 32px',
          borderRadius: '32px',
          maxWidth: '500px',
          width: '100%',
          textAlign: 'center',
          background: '#ffffff',
          boxShadow: '0 8px 40px rgba(139, 92, 246, 0.15), 0 4px 16px rgba(244, 114, 182, 0.1)',
          border: '2px solid rgba(139, 92, 246, 0.15)',
        }}>

        {/* Lock icon */}
        <div style={{
          width: '72px', height: '72px', margin: '0 auto 20px',
          background: 'linear-gradient(135deg, #8b5cf6, #f472b6)',
          borderRadius: '50%', display: 'flex', alignItems: 'center',
          justifyContent: 'center', fontSize: '2.2rem',
          boxShadow: '0 6px 20px rgba(139, 92, 246, 0.3)',
        }}>🔒</div>

        <h2 id="privacy-modal-heading" style={{
          fontFamily: 'var(--font-display, "Baloo 2", cursive)',
          fontSize: '1.8rem', fontWeight: 700,
          marginBottom: '16px',
          color: '#2d1b69',
        }}>
          {t?.parentalConsent || 'Parent / Guardian Notice'}
        </h2>

        <p style={{
          fontSize: '1.05rem', lineHeight: 1.7, fontWeight: 500,
          color: '#4a4a6a', marginBottom: '24px',
        }}>
          <strong style={{ color: '#8b5cf6' }}>TwinSpark Chronicles</strong> is
          an interactive storytelling experience for children ages 4–8.
        </p>

        {/* Feature pills */}
        <div style={{
          display: 'flex', flexWrap: 'wrap', gap: '10px',
          justifyContent: 'center', marginBottom: '24px',
        }}>
          {[
            { icon: '🎤', label: 'Voice' },
            { icon: '📷', label: 'Camera' },
            { icon: '🤖', label: 'AI Stories' },
            { icon: '🔊', label: 'Speech' },
          ].map((f, i) => (
            <span key={i} style={{
              display: 'inline-flex', alignItems: 'center', gap: '6px',
              padding: '8px 16px', borderRadius: '20px',
              background: '#f3f0ff', border: '1px solid #e0d4fc',
              fontSize: '0.9rem', fontWeight: 600, color: '#5b21b6',
            }}>
              {f.icon} {f.label}
            </span>
          ))}
        </div>

        {/* Privacy note */}
        <div style={{
          padding: '16px 20px', borderRadius: '16px',
          background: '#ecfdf5',
          border: '1px solid #a7f3d0',
          marginBottom: '24px', textAlign: 'left',
        }}>
          <p style={{
            fontSize: '0.95rem', color: '#1e4a3a',
            lineHeight: 1.6, margin: 0, fontWeight: 500,
          }}>
            <span style={{ color: '#059669', fontWeight: 700 }}>✓ Privacy First</span> — We
            do not collect or store personal data. All interactions are real-time and
            deleted immediately.
          </p>
        </div>

        <p style={{
          fontSize: '0.85rem', color: '#8a8aaa',
          marginBottom: '24px', fontStyle: 'italic',
        }}>
          By clicking below, you confirm you are a parent/guardian and consent to your
          child using this app.
        </p>

        <button
          onClick={onAccept}
          style={{
            padding: '16px 48px', fontSize: '1.15rem',
            background: 'linear-gradient(135deg, #34d399, #059669)',
            boxShadow: '0 6px 20px rgba(52, 211, 153, 0.3)',
            minHeight: '56px',
            border: 'none',
            borderRadius: '28px',
            color: '#ffffff',
            fontWeight: 700,
            cursor: 'pointer',
            fontFamily: 'var(--font-body, "Quicksand", sans-serif)',
            transition: 'transform 0.15s ease, box-shadow 0.15s ease',
          }}
          onMouseDown={(e) => { e.currentTarget.style.transform = 'scale(0.95)'; }}
          onMouseUp={(e) => { e.currentTarget.style.transform = 'scale(1)'; }}
          onMouseLeave={(e) => { e.currentTarget.style.transform = 'scale(1)'; }}
        >
          ✓ {t?.accept || 'I Accept & Continue'}
        </button>

        <p style={{
          fontSize: '0.8rem', color: '#a0a0c0',
          marginTop: '20px',
        }}>
          {t?.privacyFooter || 'You can exit at any time using the Exit button.'}
        </p>
      </div>
    </div>
  );
}

export default PrivacyModal;
