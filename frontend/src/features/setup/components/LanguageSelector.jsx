import React from 'react';

function LanguageSelector({ onSelect }) {
  const languages = [
    { code: 'en', name: 'English', flag: '🇺🇸', emoji: '🗽' },
    { code: 'es', name: 'Español', flag: '🇪🇸', emoji: '💃' },
    { code: 'hi', name: 'हिन्दी', flag: '🇮🇳', emoji: '🪔' }
  ];

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '100vh',
      padding: '20px'
    }}>
      <h1 style={{
        fontSize: '3.5rem',
        color: '#FFD700',
        marginBottom: '20px',
        textShadow: '0 0 20px rgba(255, 215, 0, 0.8)',
        fontFamily: 'Comic Sans MS, cursive, sans-serif',
        textAlign: 'center'
      }}>
        ✨ TwinSpark Chronicles ✨
      </h1>
      
      <p style={{
        fontSize: '1.5rem',
        color: 'white',
        marginBottom: '50px',
        textAlign: 'center',
        maxWidth: '600px'
      }}>
        Choose your language / Elige tu idioma / अपनी भाषा चुनें
      </p>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '30px',
        maxWidth: '800px',
        width: '100%'
      }}>
        {languages.map((lang) => (
          <button
            key={lang.code}
            onClick={() => onSelect(lang.code)}
            style={{
              padding: '40px 30px',
              background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.9) 0%, rgba(118, 75, 162, 0.9) 100%)',
              border: '3px solid rgba(255, 255, 255, 0.3)',
              borderRadius: '25px',
              color: 'white',
              cursor: 'pointer',
              fontSize: '1.3rem',
              fontWeight: 'bold',
              fontFamily: 'Comic Sans MS, cursive, sans-serif',
              boxShadow: '0 10px 30px rgba(102, 126, 234, 0.4)',
              transition: 'all 0.3s ease',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '15px'
            }}
            onMouseEnter={(e) => {
              e.target.style.transform = 'translateY(-10px) scale(1.05)';
              e.target.style.boxShadow = '0 20px 50px rgba(102, 126, 234, 0.6)';
            }}
            onMouseLeave={(e) => {
              e.target.style.transform = 'translateY(0) scale(1)';
              e.target.style.boxShadow = '0 10px 30px rgba(102, 126, 234, 0.4)';
            }}
          >
            <span style={{ fontSize: '3rem' }}>{lang.flag}</span>
            <span style={{ fontSize: '1.5rem' }}>{lang.name}</span>
            <span style={{ fontSize: '2rem' }}>{lang.emoji}</span>
          </button>
        ))}
      </div>

      <p style={{
        fontSize: '1rem',
        color: 'rgba(255, 255, 255, 0.6)',
        marginTop: '50px',
        textAlign: 'center',
        maxWidth: '500px',
        fontStyle: 'italic'
      }}>
        An AI-powered interactive storytelling experience for children ages 4-8
      </p>
    </div>
  );
}

export default LanguageSelector;