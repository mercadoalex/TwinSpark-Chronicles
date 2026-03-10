import React from 'react';

function PrivacyModal({ onAccept, t }) {
  return (
    <div 
      className="modal-overlay"
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        background: 'rgba(0, 0, 0, 0.92)',
        backdropFilter: 'blur(10px)',
        WebkitBackdropFilter: 'blur(10px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 10000,
        padding: '20px',
        animation: 'fadeIn 0.4s ease-out'
      }}
    >
      {/* Glass Magnifier Container */}
      <div 
        className="glass-panel"
        style={{
          background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.15) 0%, rgba(118, 75, 162, 0.15) 100%)',
          backdropFilter: 'blur(20px)',
          WebkitBackdropFilter: 'blur(20px)',
          padding: '50px',
          borderRadius: '40px',
          maxWidth: '700px',
          textAlign: 'center',
          boxShadow: `
            0 8px 32px 0 rgba(31, 38, 135, 0.37),
            inset 0 0 0 1px rgba(255, 255, 255, 0.18)
          `,
          border: '1px solid rgba(255, 255, 255, 0.18)',
          position: 'relative',
          overflow: 'hidden',
          animation: 'glassSlideUp 0.6s cubic-bezier(0.16, 1, 0.3, 1)'
        }}
      >
        {/* Shimmer effect overlay */}
        <div style={{
          position: 'absolute',
          top: 0,
          left: '-100%',
          width: '100%',
          height: '100%',
          background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent)',
          animation: 'shimmer 3s infinite'
        }} />

        {/* Decorative gradient orbs */}
        <div style={{
          position: 'absolute',
          top: '-50px',
          right: '-50px',
          width: '200px',
          height: '200px',
          background: 'radial-gradient(circle, rgba(139, 92, 246, 0.3) 0%, transparent 70%)',
          borderRadius: '50%',
          filter: 'blur(40px)',
          animation: 'float 6s ease-in-out infinite'
        }} />
        
        <div style={{
          position: 'absolute',
          bottom: '-30px',
          left: '-30px',
          width: '150px',
          height: '150px',
          background: 'radial-gradient(circle, rgba(236, 72, 153, 0.3) 0%, transparent 70%)',
          borderRadius: '50%',
          filter: 'blur(30px)',
          animation: 'float 4s ease-in-out infinite reverse'
        }} />

        {/* Content */}
        <div style={{ position: 'relative', zIndex: 1 }}>
          <div style={{
            width: '80px',
            height: '80px',
            margin: '0 auto 20px',
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            borderRadius: '50%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '3rem',
            boxShadow: '0 10px 30px rgba(102, 126, 234, 0.4)',
            animation: 'pulse 2s ease-in-out infinite'
          }}>
            🔒
          </div>

          <h2 style={{
            fontSize: '2.8rem',
            background: 'linear-gradient(135deg, #FFD700 0%, #FFA500 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text',
            marginBottom: '20px',
            fontWeight: '900',
            letterSpacing: '1px',
            textShadow: '0 0 30px rgba(255, 215, 0, 0.3)',
            fontFamily: 'Comic Sans MS, cursive, sans-serif'
          }}>
            {t?.parentalConsent || 'Parent/Guardian Notice'}
          </h2>
          
          <div style={{
            background: 'rgba(255, 255, 255, 0.05)',
            backdropFilter: 'blur(10px)',
            padding: '30px',
            borderRadius: '25px',
            marginBottom: '30px',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            textAlign: 'left'
          }}>
            <p style={{
              fontSize: '1.1rem',
              lineHeight: '1.9',
              color: 'rgba(255, 255, 255, 0.95)',
              marginBottom: '20px',
              fontWeight: '500'
            }}>
              {t?.privacyMessage || 
                <>
                  <strong style={{ color: '#FFD700' }}>TwinSpark Chronicles</strong> is an interactive storytelling experience designed for children ages 4-8.
                </>
              }
            </p>
            
            <div style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              gap: '15px',
              marginTop: '25px'
            }}>
              {[
                { icon: '🎤', text: 'Voice Interaction' },
                { icon: '📷', text: 'Camera (Optional)' },
                { icon: '🤖', text: 'AI Story Generation' },
                { icon: '🔊', text: 'Text-to-Speech' }
              ].map((item, idx) => (
                <div key={idx} style={{
                  background: 'rgba(255, 255, 255, 0.08)',
                  padding: '15px',
                  borderRadius: '15px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px',
                  border: '1px solid rgba(255, 255, 255, 0.1)'
                }}>
                  <span style={{ fontSize: '1.8rem' }}>{item.icon}</span>
                  <span style={{ color: 'white', fontSize: '0.95rem', fontWeight: '600' }}>
                    {item.text}
                  </span>
                </div>
              ))}
            </div>

            <div style={{
              marginTop: '25px',
              padding: '20px',
              background: 'rgba(16, 185, 129, 0.1)',
              borderRadius: '15px',
              border: '1px solid rgba(16, 185, 129, 0.3)'
            }}>
              <p style={{
                fontSize: '1rem',
                color: 'rgba(255, 255, 255, 0.9)',
                lineHeight: '1.6',
                margin: 0
              }}>
                <strong style={{ color: '#10b981' }}>✅ Privacy First:</strong> We DO NOT collect or store personal data. 
                All interactions are real-time and deleted immediately.
              </p>
            </div>
          </div>

          <p style={{
            fontSize: '1rem',
            color: 'rgba(255, 255, 255, 0.7)',
            marginBottom: '30px',
            fontStyle: 'italic'
          }}>
            By clicking "I Accept", you confirm you are a parent/guardian and consent to your child using this app.
          </p>
          
          <button
            onClick={onAccept}
            style={{
              padding: '20px 60px',
              fontSize: '1.5rem',
              background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
              border: 'none',
              borderRadius: '25px',
              color: 'white',
              cursor: 'pointer',
              fontWeight: 'bold',
              fontFamily: 'Comic Sans MS, cursive, sans-serif',
              boxShadow: '0 10px 30px rgba(16, 185, 129, 0.4)',
              transition: 'all 0.3s ease',
              position: 'relative',
              overflow: 'hidden'
            }}
            onMouseEnter={(e) => {
              e.target.style.transform = 'translateY(-3px) scale(1.05)';
              e.target.style.boxShadow = '0 15px 40px rgba(16, 185, 129, 0.6)';
            }}
            onMouseLeave={(e) => {
              e.target.style.transform = 'translateY(0) scale(1)';
              e.target.style.boxShadow = '0 10px 30px rgba(16, 185, 129, 0.4)';
            }}
          >
            <span style={{ position: 'relative', zIndex: 1 }}>
              ✅ {t?.accept || 'I Accept & Continue'}
            </span>
          </button>

          <p style={{
            fontSize: '0.85rem',
            color: 'rgba(255,255,255,0.5)',
            marginTop: '25px',
            fontStyle: 'italic'
          }}>
            {t?.privacyFooter || 'You can exit at any time using the Exit button.'}
          </p>
        </div>
      </div>

      <style>{`
        @keyframes fadeIn {
          from {
            opacity: 0;
          }
          to {
            opacity: 1;
          }
        }

        @keyframes glassSlideUp {
          from {
            opacity: 0;
            transform: translateY(50px) scale(0.95);
          }
          to {
            opacity: 1;
            transform: translateY(0) scale(1);
          }
        }

        @keyframes shimmer {
          0% {
            left: -100%;
          }
          100% {
            left: 100%;
          }
        }

        @keyframes float {
          0%, 100% {
            transform: translateY(0) scale(1);
          }
          50% {
            transform: translateY(-20px) scale(1.1);
          }
        }

        @keyframes pulse {
          0%, 100% {
            transform: scale(1);
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4);
          }
          50% {
            transform: scale(1.05);
            box-shadow: 0 15px 40px rgba(102, 126, 234, 0.6);
          }
        }
      `}</style>
    </div>
  );
}

export default PrivacyModal;