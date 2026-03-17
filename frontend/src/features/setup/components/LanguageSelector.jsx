import React from 'react';

const languages = [
  { code: 'en', name: 'English', flag: '🇺🇸' },
  { code: 'es', name: 'Español', flag: '🇪🇸' },
  { code: 'hi', name: 'हिन्दी', flag: '🇮🇳' },
];

function LanguageSelector({ onSelect }) {
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      gap: '48px',
      padding: '40px 20px',
      animation: 'fadeInUp 0.6s var(--ease-smooth)',
    }}>
      <p style={{
        fontFamily: 'var(--font-display)',
        fontSize: '1.3rem',
        fontWeight: 600,
        color: 'rgba(255, 255, 255, 0.55)',
        textAlign: 'center',
        maxWidth: '500px',
      }}>
        Choose your language
      </p>

      <div style={{
        display: 'flex',
        gap: '16px',
        flexWrap: 'wrap',
        justifyContent: 'center',
      }}>
        {languages.map((lang) => (
          <button
            key={lang.code}
            onClick={() => onSelect(lang.code)}
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '14px',
              padding: '32px 40px',
              minWidth: '180px',
              background: 'var(--color-glass)',
              backdropFilter: 'blur(12px)',
              WebkitBackdropFilter: 'blur(12px)',
              border: '1.5px solid var(--color-glass-border)',
              borderRadius: 'var(--radius-lg)',
              color: 'rgba(255, 255, 255, 0.9)',
              cursor: 'pointer',
              fontFamily: 'var(--font-display)',
              fontSize: '1.15rem',
              fontWeight: 600,
              transition: 'all 0.25s var(--ease-bounce)',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = 'translateY(-6px) scale(1.04)';
              e.currentTarget.style.borderColor = 'rgba(251, 191, 36, 0.4)';
              e.currentTarget.style.boxShadow = '0 12px 40px rgba(251, 191, 36, 0.12)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = '';
              e.currentTarget.style.borderColor = '';
              e.currentTarget.style.boxShadow = '';
            }}
          >
            <span style={{ fontSize: '2.8rem' }}>{lang.flag}</span>
            <span>{lang.name}</span>
          </button>
        ))}
      </div>

      <p style={{
        fontSize: '0.85rem',
        color: 'rgba(255, 255, 255, 0.3)',
        textAlign: 'center',
        fontWeight: 500,
      }}>
        AI-powered interactive storytelling for siblings
      </p>
    </div>
  );
}

export default LanguageSelector;
