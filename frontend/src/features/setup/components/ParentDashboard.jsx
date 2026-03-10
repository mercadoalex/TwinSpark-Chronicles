import React, { useState, useEffect } from 'react';
import { Activity, Clock, Users, ArrowLeft, Settings, Database } from 'lucide-react';
import './ParentDashboard.css';
import SessionHistory from './dashboard/SessionHistory';
import AnalyticsChart from './dashboard/AnalyticsChart';

// Main dashboard container
export default function ParentDashboard({ onBack }) {
    const [activeTab, setActiveTab] = useState('overview');
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

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
        </div>
    );
}
