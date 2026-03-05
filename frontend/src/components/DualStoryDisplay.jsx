import React from 'react';

export default function DualStoryDisplay({ storyBeat, t, profiles }) {
    if (!storyBeat) return null;

    return (
        <div className="dual-story-container" style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: '24px',
            margin: '30px 0',
            width: '100%',
            maxWidth: '1200px',
            animation: 'slideUp 0.5s ease-out'
        }}>

            {/* Ale's Side */}
            <div className="glass-panel" style={{
                padding: '30px',
                borderTop: '4px solid var(--color-accent-pink)',
                position: 'relative',
                overflow: 'hidden',
                transition: 'transform 0.3s ease',
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

                <div style={{ display: 'flex', alignItems: 'center', gap: '15px', marginBottom: '20px', position: 'relative' }}>
                    {profiles?.c1_avatar && (
                        <img
                            src={profiles.c1_avatar}
                            alt={`${profiles.c1_name} Avatar`}
                            style={{
                                width: '70px', 
                                height: '70px', 
                                borderRadius: '50%',
                                border: '3px solid var(--color-accent-pink)',
                                boxShadow: '0 0 15px rgba(236,72,153,0.5)',
                                objectFit: 'cover',
                                transition: 'transform 0.3s ease'
                            }}
                            onMouseEnter={(e) => e.target.style.transform = 'scale(1.1)'}
                            onMouseLeave={(e) => e.target.style.transform = 'scale(1)'}
                        />
                    )}
                    <h2 style={{
                        color: 'var(--color-accent-pink)',
                        fontFamily: 'var(--font-heading)',
                        margin: 0,
                        fontSize: '2.2rem'
                    }}>
                        {profiles ? `${profiles.c1_name}'s Magic` : t.alesView}
                    </h2>
                </div>
                <p className="story-text" style={{
                    fontSize: '1.4rem',
                    lineHeight: '2',
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
                overflow: 'hidden',
                transition: 'transform 0.3s ease'
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

                <div style={{ display: 'flex', alignItems: 'center', gap: '15px', marginBottom: '20px', position: 'relative' }}>
                    {profiles?.c2_avatar && (
                        <img
                            src={profiles.c2_avatar}
                            alt={`${profiles.c2_name} Avatar`}
                            style={{
                                width: '70px', 
                                height: '70px', 
                                borderRadius: '50%',
                                border: '3px solid var(--color-accent-blue)',
                                boxShadow: '0 0 15px rgba(59,130,246,0.5)',
                                objectFit: 'cover',
                                transition: 'transform 0.3s ease'
                            }}
                            onMouseEnter={(e) => e.target.style.transform = 'scale(1.1)'}
                            onMouseLeave={(e) => e.target.style.transform = 'scale(1)'}
                        />
                    )}
                    <h2 style={{
                        color: 'var(--color-accent-blue)',
                        fontFamily: 'var(--font-heading)',
                        margin: 0,
                        fontSize: '2.2rem'
                    }}>
                        {profiles ? `${profiles.c2_name}'s Magic` : t.sofisView}
                    </h2>
                </div>
                <p className="story-text" style={{
                    fontSize: '1.4rem',
                    lineHeight: '2',
                    textShadow: '0 2px 4px rgba(0,0,0,0.5)'
                }}>
                    {storyBeat.child2_perspective}
                </p>
            </div>

        </div>
    );
}
