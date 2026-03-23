import React, { useState, useEffect } from 'react';
import { Activity, Clock, Users, ArrowLeft, Settings, Database } from 'lucide-react';
import './ParentDashboard.css';
import SessionHistory from './dashboard/SessionHistory';
import AnalyticsChart from './dashboard/AnalyticsChart';
import { useSetupStore } from '../../../stores/setupStore';
import costumeCatalog from '../data/costumeCatalog';

function getCostumeInfo(costumeId) {
    const entry = costumeCatalog.find(c => c.id === costumeId);
    return entry || { emoji: '👕', label: 'Default' };
}

// Main dashboard container
export default function ParentDashboard({ onBack }) {
    const [activeTab, setActiveTab] = useState('overview');
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [costumeModal, setCostumeModal] = useState(null); // { childNum, name }
    const [costumeUpdating, setCostumeUpdating] = useState(false);

    const child1 = useSetupStore(s => s.child1);
    const child2 = useSetupStore(s => s.child2);
    const setChild1 = useSetupStore(s => s.setChild1);
    const setChild2 = useSetupStore(s => s.setChild2);

    const siblingPairId = [child1.name, child2.name].sort().join(':');

    const handleCostumeChange = async (costumeId) => {
        if (!costumeModal || costumeUpdating) return;
        setCostumeUpdating(true);
        try {
            const res = await fetch(
                `http://localhost:8000/api/costume/${encodeURIComponent(siblingPairId)}/${costumeModal.childNum}`,
                {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ costume: costumeId }),
                }
            );
            if (!res.ok) throw new Error('Failed to update costume');
            // Update local store
            if (costumeModal.childNum === 1) setChild1({ costume: costumeId });
            else setChild2({ costume: costumeId });
            setCostumeModal(null);
        } catch (err) {
            console.error('Costume update failed:', err);
        } finally {
            setCostumeUpdating(false);
        }
    };

    useEffect(() => {
        // Fetch stats on mount
        const fetchDashboardData = async () => {
            try {
                setLoading(true);
                const res = await fetch('http://localhost:8000/api/dashboard/stats');
                if (!res.ok) throw new Error('Failed to load dashboard stats');
                const data = await res.json();
                setStats(data);
                setError(null);
            } catch (err) {
                console.error(err);
                setError("Could not connect to the Parent Dashboard API.");
            } finally {
                setLoading(false);
            }
        };

        fetchDashboardData();
    }, []);

    return (
        <div className="dashboard-container animation-fade-in">
            {/* Sidebar */}
            <div className="dashboard-sidebar">
                <h2 className="dashboard-title">
                    <Settings size={28} className="icon-spin" /> Parent Dashboard
                </h2>

                <nav className="dashboard-nav">
                    <button
                        className={`nav-btn ${activeTab === 'overview' ? 'active' : ''}`}
                        onClick={() => setActiveTab('overview')}
                    >
                        <Activity size={20} /> Overview
                    </button>

                    <button
                        className={`nav-btn ${activeTab === 'history' ? 'active' : ''}`}
                        onClick={() => setActiveTab('history')}
                    >
                        <Clock size={20} /> Session History
                    </button>

                    <button
                        className={`nav-btn ${activeTab === 'analytics' ? 'active' : ''}`}
                        onClick={() => setActiveTab('analytics')}
                    >
                        <Database size={20} /> Advanced Analytics
                    </button>

                    <button
                        className={`nav-btn ${activeTab === 'settings' ? 'active' : ''}`}
                        onClick={() => setActiveTab('settings')}
                    >
                        <Settings size={20} /> Privacy & Settings
                    </button>
                </nav>

                <button className="back-btn mt-auto" onClick={onBack}>
                    <ArrowLeft size={20} /> Back to Game
                </button>
            </div>

            {/* Main Content Area */}
            <div className="dashboard-main glass-panel">

                {loading ? (
                    <div className="loading-state">Loading dashboard data... 🪄</div>
                ) : error ? (
                    <div className="error-state">
                        <p>⚠️ {error}</p>
                        <button className="btn-magic" onClick={() => window.location.reload()}>Retry</button>
                    </div>
                ) : (
                    <>
                        {/* OVERVIEW TAB */}
                        {activeTab === 'overview' && stats && (
                            <div className="tab-content">
                                <h3 className="tab-header">Quick Stats</h3>

                                <div className="stats-grid">
                                    <div className="stat-card">
                                        <div className="stat-icon"><Activity size={32} /></div>
                                        <div className="stat-info">
                                            <span className="stat-value">{stats.total_sessions}</span>
                                            <span className="stat-label">Total Sessions Play</span>
                                        </div>
                                    </div>

                                    <div className="stat-card">
                                        <div className="stat-icon"><Clock size={32} /></div>
                                        <div className="stat-info">
                                            <span className="stat-value">{stats.total_duration_minutes}</span>
                                            <span className="stat-label">Minutes Played</span>
                                        </div>
                                    </div>

                                    <div className="stat-card">
                                        <div className="stat-icon"><Users size={32} /></div>
                                        <div className="stat-info">
                                            <span className="stat-value">{stats.average_bond_score || '0'}</span>
                                            <span className="stat-label">Bond Strength (0-1)</span>
                                        </div>
                                    </div>
                                </div>

                                {child1.name && child2.name && (
                                    <div className="costumes-section" style={{ marginTop: '24px' }}>
                                        <h4 style={{ color: 'white', marginBottom: '12px' }}>Costumes</h4>
                                        <div className="stats-grid">
                                            {[{ num: 1, child: child1 }, { num: 2, child: child2 }].map(({ num, child }) => {
                                                const info = getCostumeInfo(child.costume);
                                                return (
                                                    <button
                                                        key={num}
                                                        className="stat-card"
                                                        style={{ cursor: 'pointer', border: '1px solid rgba(255,255,255,0.15)' }}
                                                        onClick={() => setCostumeModal({ childNum: num, name: child.name })}
                                                        aria-label={`Change costume for ${child.name}`}
                                                    >
                                                        <div className="stat-icon" style={{ fontSize: '28px' }}>{info.emoji}</div>
                                                        <div className="stat-info">
                                                            <span className="stat-value" style={{ fontSize: '0.95rem' }}>{child.name}</span>
                                                            <span className="stat-label">{info.label}</span>
                                                        </div>
                                                    </button>
                                                );
                                            })}
                                        </div>
                                    </div>
                                )}

                                <div className="overview-charts-container">
                                    <div className="chart-wrapper">
                                        <AnalyticsChart title="Recent Playtime (minutes)" endpoint="/api/dashboard/duration-chart" />
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* HISTORY TAB */}
                        {activeTab === 'history' && (
                            <div className="tab-content">
                                <h3 className="tab-header">Session History</h3>
                                <SessionHistory />
                            </div>
                        )}

                        {/* ANALYTICS TAB */}
                        {activeTab === 'analytics' && (
                            <div className="tab-content">
                                <h3 className="tab-header">Deep Personality Analysis</h3>
                                <div style={{ color: 'rgba(255,255,255,0.8)' }}>
                                    <p>Check back to see how traits like leadership and conflict resolution evolve over time.</p>
                                    <AnalyticsChart title="Leadership Balance" endpoint="/api/dashboard/leadership-chart" />
                                </div>
                            </div>
                        )}

                        {/* SETTINGS TAB */}
                        {activeTab === 'settings' && (
                            <div className="tab-content">
                                <h3 className="tab-header">Advanced Settings</h3>
                                <div style={{
                                    background: 'rgba(255,255,255,0.05)',
                                    padding: '20px',
                                    borderRadius: '15px',
                                    border: '1px solid rgba(255,255,255,0.1)'
                                }}>
                                    <h4 style={{ color: 'white', marginBottom: '10px' }}>Privacy & Security</h4>
                                    <p style={{ color: 'rgba(255,255,255,0.7)', marginBottom: '20px', fontSize: '0.9rem' }}>
                                        The application remembers your previously approved parent consent for camera and microphone usage. You can revoke this consent below.
                                    </p>
                                    <button
                                        className="btn-magic"
                                        style={{ background: 'linear-gradient(135deg, #ef4444, #b91c1c)' }}
                                        onClick={() => {
                                            localStorage.removeItem('twinspark_privacy_accepted');
                                            alert("Privacy consent revoked. The app will now reload.");
                                            window.location.reload();
                                        }}
                                    >
                                        Revoke Privacy Consent
                                    </button>
                                </div>
                            </div>
                        )}
                    </>
                )}
            </div>
            {/* Costume Selector Modal */}
            {costumeModal && (
                <div
                    className="costume-modal-overlay"
                    style={{
                        position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)',
                        display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000,
                    }}
                    onClick={() => !costumeUpdating && setCostumeModal(null)}
                    role="dialog"
                    aria-label={`Pick costume for ${costumeModal.name}`}
                >
                    <div
                        style={{
                            background: 'linear-gradient(135deg, #1e1b4b, #312e81)',
                            borderRadius: '20px', padding: '28px', maxWidth: '480px', width: '90%',
                            border: '1px solid rgba(255,255,255,0.15)',
                        }}
                        onClick={e => e.stopPropagation()}
                    >
                        <h3 style={{ color: 'white', marginBottom: '16px', textAlign: 'center' }}>
                            Pick a costume for {costumeModal.name}
                        </h3>
                        <div style={{
                            display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)',
                            gap: '10px',
                        }}>
                            {costumeCatalog.map(c => (
                                <button
                                    key={c.id}
                                    disabled={costumeUpdating}
                                    onClick={() => handleCostumeChange(c.id)}
                                    aria-label={c.label}
                                    style={{
                                        background: 'rgba(255,255,255,0.08)', border: '2px solid',
                                        borderColor: (costumeModal.childNum === 1 ? child1.costume : child2.costume) === c.id
                                            ? c.color : 'transparent',
                                        borderRadius: '14px', padding: '12px 4px', cursor: 'pointer',
                                        display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '4px',
                                        minHeight: '44px', minWidth: '44px', opacity: costumeUpdating ? 0.5 : 1,
                                    }}
                                >
                                    <span style={{ fontSize: '24px' }} aria-hidden="true">{c.emoji}</span>
                                    <span style={{ color: 'white', fontSize: '0.7rem' }}>{c.label}</span>
                                </button>
                            ))}
                        </div>
                        <button
                            style={{
                                marginTop: '16px', width: '100%', padding: '10px',
                                background: 'rgba(255,255,255,0.1)', border: '1px solid rgba(255,255,255,0.2)',
                                borderRadius: '10px', color: 'white', cursor: 'pointer',
                            }}
                            onClick={() => setCostumeModal(null)}
                        >
                            Cancel
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}
