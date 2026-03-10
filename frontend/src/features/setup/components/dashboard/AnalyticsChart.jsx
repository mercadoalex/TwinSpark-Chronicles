import React, { useState, useEffect } from 'react';

// A simple mock chart component since we don't have a charting library like recharts installed yet.
export default function AnalyticsChart({ title, endpoint }) {
    const [data, setData] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const res = await fetch(`http://localhost:8000${endpoint}`);
                if (res.ok) {
                    const result = await res.json();
                    setData(result.data || []);
                }
            } catch (err) {
                console.error("Failed to fetch chart data", err);
                // Fallback mock data if API fails or is not implemented yet
                setData([
                    { label: 'Mon', value: 20 },
                    { label: 'Tue', value: 45 },
                    { label: 'Wed', value: 30 },
                    { label: 'Thu', value: 60 },
                    { label: 'Fri', value: 40 },
                    { label: 'Sat', value: 85 },
                    { label: 'Sun', value: 50 }
                ]);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, [endpoint]);

    if (loading) {
        return <div style={{ height: '200px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'rgba(255,255,255,0.5)' }}>Loading chart...</div>;
    }

    // Find max value for relative scaling
    const maxVal = Math.max(...data.map(d => d.value), 100);

    return (
        <div style={{ display: 'flex', flexDirection: 'column', height: '100%', minHeight: '250px' }}>
            <h4 style={{ margin: '0 0 20px 0', color: 'rgba(255,255,255,0.9)', fontSize: '1.1rem' }}>{title}</h4>

            <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', flex: 1, padding: '10px 0', borderBottom: '1px solid rgba(255,255,255,0.2)' }}>
                {data.map((item, i) => {
                    const heightPercent = (item.value / maxVal) * 100;
                    return (
                        <div key={i} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '10px', width: `${100 / data.length}%` }}>
                            <div
                                style={{
                                    height: `${heightPercent}%`,
                                    width: '60%',
                                    background: 'linear-gradient(to top, rgba(139, 92, 246, 0.4), rgba(236, 72, 153, 0.8))',
                                    borderRadius: '6px 6px 0 0',
                                    minHeight: '4px',
                                    transition: 'height 0.5s ease-out'
                                }}
                                title={`${item.value}`}
                            />
                            <span style={{ color: 'rgba(255,255,255,0.5)', fontSize: '0.8rem' }}>{item.label}</span>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
