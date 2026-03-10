import React, { useState, useEffect } from 'react';
import { Clock, Calendar, Star, Shield, Zap } from 'lucide-react';

export default function SessionHistory() {
    const [sessions, setSessions] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchSessions = async () => {
            try {
                const res = await fetch('http://localhost:8000/api/dashboard/sessions');
                if (res.ok) {
                    const data = await res.json();
                    setSessions(data);
                }
            } catch (err) {
                console.error("Failed to fetch sessions", err);
            } finally {
                setLoading(false);
            }
        };
        fetchSessions();
    }, []);

    if (loading) {
        return <div style={{ color: 'white', padding: '20px' }}>Loading history...</div>;
    }

    if (sessions.length === 0) {
        return (
            <div style={{ color: 'rgba(255,255,255,0.7)', padding: '20px', textAlign: 'center' }}>
                <Star size={48} style={{ opacity: 0.5, marginBottom: '15px' }} />
                <p>No adventures recorded yet! Time to start the first story.</p>
            </div>
        );
    }

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {sessions.map((session, index) => (
                <div
                    key={session.session_id || index}
                    style={{
                        background: 'rgba(0,0,0,0.2)',
                        border: '1px solid rgba(255,255,255,0.1)',
                        borderRadius: '15px',
                        padding: '20px',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '15px'
                    }}
                >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '10px' }}>
                        <h4 style={{ margin: 0, fontSize: '1.2rem', color: '#fff', display: 'flex', alignItems: 'center', gap: '10px' }}>
                            <span style={{ color: '#ec4899' }}>{session.title || "The Unknown Adventure"}</span>
                        </h4>
                        <div style={{ display: 'flex', gap: '15px', color: 'rgba(255,255,255,0.6)', fontSize: '0.9rem' }}>
                            <span style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                                <Calendar size={16} />
                                {new Date(session.started_at).toLocaleDateString()}
                            </span>
                            <span style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                                <Clock size={16} />
                                {session.duration_minutes || '< 1'} min
                            </span>
                        </div>
                    </div>

                    <div style={{ display: 'flex', gap: '20px' }}>
                        <div style={{ flex: 1, color: 'rgba(255,255,255,0.8)' }}>
                            <p style={{ margin: '0 0 10px 0', fontSize: '0.9rem', color: 'var(--color-accent-blue)' }}>THEME: {session.theme || 'Fantasy'}</p>

                            <div style={{ marginTop: '10px' }}>
                                <strong style={{ display: 'block', marginBottom: '5px', fontSize: '0.9rem', color: 'rgba(255,255,255,0.5)' }}>SKILLS PRACTICED:</strong>
                                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                                    {session.skills_practiced && session.skills_practiced.length > 0 ? (
                                        session.skills_practiced.map(skill => (
                                            <span key={skill} style={{ background: 'rgba(16, 185, 129, 0.2)', color: '#10b981', padding: '4px 10px', borderRadius: '12px', fontSize: '0.8rem' }}>
                                                {skill}
                                            </span>
                                        ))
                                    ) : (
                                        <span style={{ color: 'rgba(255,255,255,0.4)', fontSize: '0.8rem' }}>None recorded</span>
                                    )}
                                </div>
                            </div>
                        </div>

                        <div style={{ flex: 1, borderLeft: '1px solid rgba(255,255,255,0.1)', paddingLeft: '20px' }}>
                            <strong style={{ display: 'block', marginBottom: '5px', fontSize: '0.9rem', color: 'rgba(255,255,255,0.5)' }}>EMOTIONS ADDRESSED:</strong>
                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                                {session.emotions_addressed && session.emotions_addressed.length > 0 ? (
                                    session.emotions_addressed.map(emotion => (
                                        <span key={emotion} style={{ background: 'rgba(245, 158, 11, 0.2)', color: '#f59e0b', padding: '4px 10px', borderRadius: '12px', fontSize: '0.8rem' }}>
                                            {emotion}
                                        </span>
                                    ))
                                ) : (
                                    <span style={{ color: 'rgba(255,255,255,0.4)', fontSize: '0.8rem' }}>None recorded</span>
                                )}
                            </div>

                            <div style={{ marginTop: '15px' }}>
                                {session.has_divergence && (
                                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: '5px', background: 'rgba(139, 92, 246, 0.2)', color: '#8b5cf6', padding: '4px 10px', borderRadius: '12px', fontSize: '0.8rem' }}>
                                        <Zap size={14} /> Divergence Path Used ({session.reunion_count} reunions)
                                    </span>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            ))}
        </div>
    );
}
