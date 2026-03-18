import React, { useRef } from 'react';
import { useFocusTrap } from '../../hooks';

export default function AlertModal({ message, onClose }) {
    const dialogRef = useRef(null);
    const isOpen = Boolean(message);

    useFocusTrap(dialogRef, isOpen, onClose);

    if (!message) return null;

    return (
        <div style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.6)',
            backdropFilter: 'blur(8px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            animation: 'fadeIn 0.3s ease'
        }}>
            <div
                ref={dialogRef}
                role="dialog"
                aria-modal="true"
                aria-labelledby="alert-modal-heading"
                className="glass-panel"
                style={{
                    padding: '40px 50px',
                    maxWidth: '500px',
                    textAlign: 'center',
                    border: '2px solid var(--color-accent-pink)',
                    boxShadow: '0 10px 30px rgba(236, 72, 153, 0.4)',
                    animation: 'slideUp 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275)'
                }}
            >

                <div style={{
                    fontSize: '4rem',
                    marginBottom: '20px',
                    animation: 'bounce 2s infinite'
                }}
                    aria-hidden="true"
                >
                    ✨
                </div>

                <h2
                    id="alert-modal-heading"
                    style={{
                        fontFamily: 'var(--font-heading)',
                        color: '#fff',
                        fontSize: '2rem',
                        marginBottom: '15px'
                    }}
                >
                    TwinSpark Magic
                </h2>

                <p style={{
                    fontSize: '1.2rem',
                    color: 'rgba(255,255,255,0.9)',
                    marginBottom: '30px',
                    lineHeight: '1.5'
                }}>
                    {message}
                </p>

                <button
                    onClick={onClose}
                    style={{
                        background: 'linear-gradient(135deg, var(--color-accent-pink), var(--color-accent-purple))',
                        color: 'white',
                        border: 'none',
                        padding: '12px 30px',
                        borderRadius: '50px',
                        fontSize: '1.2rem',
                        fontWeight: 'bold',
                        cursor: 'pointer',
                        boxShadow: '0 5px 15px rgba(236, 72, 153, 0.3)',
                        transition: 'transform 0.2s ease, box-shadow 0.2s ease',
                        minWidth: '44px',
                        minHeight: '44px',
                    }}
                    onMouseOver={(e) => e.currentTarget.style.transform = 'scale(1.05)'}
                    onMouseOut={(e) => e.currentTarget.style.transform = 'scale(1)'}
                >
                    OK!
                </button>
            </div>
        </div>
    );
}
