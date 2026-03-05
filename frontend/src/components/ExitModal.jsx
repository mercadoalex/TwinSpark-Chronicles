import React from 'react';

export default function ExitModal({ onSave, onExit, onClose, isSaving }) {
    return (
        <div style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0,0,0,0.8)',
            backdropFilter: 'blur(10px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            animation: 'fadeIn 0.3s'
        }}>
            <div className="glass-panel" style={{
                padding: '40px',
                maxWidth: '500px',
                width: '90%',
                textAlign: 'center',
                background: 'rgba(20, 20, 40, 0.9)',
                border: '1px solid rgba(255,255,255,0.2)',
                boxShadow: '0 10px 30px rgba(0,0,0,0.5)',
                animation: 'slideUp 0.3s'
            }}>
                <div style={{ fontSize: '4rem', marginBottom: '20px' }}>🚪</div>
                <h2 style={{ color: 'white', marginBottom: '15px' }}>Leaving the Magic?</h2>
                <p style={{ color: 'rgba(255,255,255,0.8)', fontSize: '1.2rem', marginBottom: '30px' }}>
                    Do you want to save your adventure so you can continue it later?
                </p>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
                    <button
                        onClick={onSave}
                        disabled={isSaving}
                        style={{
                            padding: '15px',
                            borderRadius: '25px',
                            border: 'none',
                            background: 'linear-gradient(135deg, var(--color-accent-pink), var(--color-accent-purple))',
                            color: 'white',
                            fontSize: '1.1rem',
                            fontWeight: 'bold',
                            cursor: isSaving ? 'wait' : 'pointer',
                            opacity: isSaving ? 0.7 : 1,
                            transition: 'transform 0.2s'
                        }}
                        onMouseOver={(e) => !isSaving && (e.currentTarget.style.transform = 'scale(1.02)')}
                        onMouseOut={(e) => !isSaving && (e.currentTarget.style.transform = 'scale(1)')}
                    >
                        {isSaving ? 'Saving...' : '💾 Save & Exit'}
                    </button>

                    <button
                        onClick={onExit}
                        disabled={isSaving}
                        style={{
                            padding: '15px',
                            borderRadius: '25px',
                            border: '1px solid rgba(255,255,255,0.3)',
                            background: 'rgba(255,255,255,0.1)',
                            color: 'white',
                            fontSize: '1.1rem',
                            cursor: isSaving ? 'not-allowed' : 'pointer',
                            transition: 'background 0.2s'
                        }}
                        onMouseOver={(e) => !isSaving && (e.currentTarget.style.background = 'rgba(255,255,255,0.2)')}
                        onMouseOut={(e) => !isSaving && (e.currentTarget.style.background = 'rgba(255,255,255,0.1)')}
                    >
                        🏃 Exit without Saving
                    </button>

                    <button
                        onClick={onClose}
                        disabled={isSaving}
                        style={{
                            padding: '10px',
                            border: 'none',
                            background: 'transparent',
                            color: 'rgba(255,255,255,0.6)',
                            fontSize: '1rem',
                            cursor: isSaving ? 'not-allowed' : 'pointer',
                            marginTop: '10px'
                        }}
                    >
                        Cancel
                    </button>
                </div>
            </div>
        </div>
    );
}
