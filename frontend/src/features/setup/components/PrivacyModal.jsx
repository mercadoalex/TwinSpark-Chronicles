import React from 'react';

function PrivacyModal({ onAccept, t }) {
  return (
    <div className="privacy-overlay" style={{
      position: 'fixed', inset: 0,
      background: 'rgba(7, 11, 26, 0.95)',
      backdropFilter: 'blur(16px)',
      WebkitBackdropFilter: 'blur(16px)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      zIndex: 10000, padding: '20px',
      animation: 'fadeIn 0.4s var(--ease-smooth)',
    }}>
      <div className="glass-panel" style={{
        padding: '44px',
        borderRadius: 'var(--radius-xl)',
        maxWidth: '640px',
        width: '100%',
        textAlign: 'center',
        animation: 'fadeInUp 0.5s var(--ease-bounce)',
        position: 'relative',
        overflow: 'hidden',
      }}>
        {/* Subtle glow orb */}
        <div style={{
          position: 'absolute', top: '-60px', right: '-60px',
          width: '200px', height: '200px',
          background: 'radial-gradient(circle, rgba(167,139,250,0.15), transparent 70%)',
          borderRadius: '50%', filter: 'blur(40px)', pointerEvents: 'none',
        }} />

        {/* Lock icon */}
        <div style={{
          width: '64px', height: '64px', margin: '0 auto 20px',
          background: 'linear-gradient(135deg, var(--color-violet), var(--color-coral))',
          borderRadius: '50%', display: 'flex', alignItems: 'center',
          justifyContent: 'center', fontSize: '2rem',
          boxShadow: '0 8px 30px rgba(167, 139, 250, 0.3)',
        }}>🔒</div>

        <h2 style={{
          fontFamily: 'var(--font-display)', fontSize: '2rem', fontWeight: 700,
          marginBottom: '16px',
          background: 'linear-gradient(135deg, var(--color-gold), var(--color-coral))',
          WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
          backgroundClip: 'text',
        }}>
          {t?.parentalConsent || 'Parent / Guardian Notice'}
        </h2>

        <p style={{
          fontSize: '1.05rem', lineHeight: 1.7, fontWeight: 500,
          color: 'rgba(255,255,255,0.75)', marginBottom: '24px',
        }}>
          {t?.privacyMessage || (
            <>
              <span style={{ color: 'var(--color-gold)' }}>TwinSpark Chronicles</span> is
              an interactive storytelling experience for children ages 4–8.
            </>
          )}
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
              padding: '8px 16px', borderRadius: 'var(--radius-full)',
              background: 'var(--color-glass)', border: '1px solid var(--color-glass-border)',
              fontSize: '0.9rem', fontWeight: 600, color: 'rgba(255,255,255,0.8)',
            }}>
              {f.icon} {f.label}
            </span>
          ))}
        </div>

        {/* Privacy note */}
        <div style={{
          padding: '16px 20px', borderRadius: 'var(--radius-md)',
          background: 'rgba(52, 211, 153, 0.06)',
          border: '1px solid rgba(52, 211, 153, 0.2)',
          marginBottom: '28px', textAlign: 'left',
        }}>
          <p style={{
            fontSize: '0.95rem', color: 'rgba(255,255,255,0.8)',
            lineHeight: 1.6, margin: 0, fontWeight: 500,
          }}>
            <span style={{ color: 'var(--color-emerald)' }}>✓ Privacy First</span> — We
            do not collect or store personal data. All interactions are real-time and
            deleted immediately.
          </p>
        </div>

        <p style={{
          fontSize: '0.85rem', color: 'rgba(255,255,255,0.4)',
          marginBottom: '24px', fontStyle: 'italic',
        }}>
          By clicking below, you confirm you are a parent/guardian and consent to your
          child using this app.
        </p>

        <button
          onClick={onAccept}
          className="btn-magic"
          style={{
            padding: '16px 48px', fontSize: '1.15rem',
            background: 'linear-gradient(135deg, var(--color-emerald), #059669)',
            boxShadow: '0 8px 30px rgba(52, 211, 153, 0.3)',
          }}
        >
          ✓ {t?.accept || 'I Accept & Continue'}
        </button>

        <p style={{
          fontSize: '0.8rem', color: 'rgba(255,255,255,0.3)',
          marginTop: '20px',
        }}>
          {t?.privacyFooter || 'You can exit at any time using the Exit button.'}
        </p>
      </div>
    </div>
  );
}

export default PrivacyModal;
