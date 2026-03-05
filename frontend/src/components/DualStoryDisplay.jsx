import React from 'react';

export default function DualStoryDisplay({ storyBeat, t, profiles }) {
    if (!storyBeat) return null;

    return (
        <div style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: '24px',
            margin: '30px 0',
            width: '100%',
            maxWidth: '1200px'
        }}>

            {/* Ale's Side */}
            <div className="glass-panel" style={{
                padding: '30px',
                borderTop: '4px solid var(--color-accent-pink)',
                position: 'relative',
                overflow: 'hidden'
            }}>
                {/* Subtle background glow */}
                <div style={{
                    position: 'absolute',
                    top: '-50%',
                    left: '-50%',
                    width: '200%',
                    height: '200%',
                    background: 'radial-gradient(circle, rgba(236,72,153,0.05) 0%, transparent 50%)',
                    pointerEvents: 'none'
                }} />

                <div style={{ display: 'flex', alignItems: 'center', gap: '15px', marginBottom: '20px' }}>
                    {profiles?.c1_avatar && (
                        <img
                            src={profiles.c1_avatar}
                            alt={`${profiles.c1_name} Avatar`}
                            style={{
                                width: '60px', height: '60px', borderRadius: '50%',
                                border: '3px solid var(--color-accent-pink)',
                                boxShadow: '0 0 15px rgba(236,72,153,0.5)',
                                objectFit: 'cover'
                            }}
                        />
                    )}
                    <h2 style={{
                        color: 'var(--color-accent-pink)',
                        fontFamily: 'var(--font-heading)',
                        margin: 0,
                        fontSize: '2rem'
                    }}>
                        {profiles ? `${profiles.c1_name}'s Magic` : t.alesView}
                    </h2>
                </div>
                <p style={{
                    fontSize: '1.25rem',
                    lineHeight: '1.8',
                    textShadow: '0 2px 4px rgba(0,0,0,0.5)'
                }}>
                    {storyBeat.child1_perspective}
                </p>
            </div>

            {/* Sofi's Side */}
            <div className="glass-panel" style={{
                padding: '30px',
                borderTop: '4px solid var(--color-accent-blue)',
                position: 'relative',
                overflow: 'hidden'
            }}>
                <div style={{
                    position: 'absolute',
                    top: '-50%',
                    left: '-50%',
                    width: '200%',
                    height: '200%',
                    background: 'radial-gradient(circle, rgba(59,130,246,0.05) 0%, transparent 50%)',
                    pointerEvents: 'none'
                }} />

                <h2 style={{
                    color: 'var(--color-accent-blue)',
                    fontFamily: 'var(--font-heading)',
                    fontSize: '2rem',
                    marginBottom: '20px'
                }}>
                    {t.sofisView}
                </h2>
                <p style={{
                    fontSize: '1.25rem',
                    lineHeight: '1.8',
                    textShadow: '0 2px 4px rgba(0,0,0,0.5)'
                }}>
                    {storyBeat.child2_perspective}
                </p>
            </div>

        </div>
    );
}
