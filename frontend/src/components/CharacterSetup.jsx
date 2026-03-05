import React, { useState } from 'react';

export default function CharacterSetup({ t, onComplete }) {
    const [wizardStep, setWizardStep] = useState(1);
    const [isGenerating, setIsGenerating] = useState(false);

    const [child1Name, setChild1Name] = useState('');
    const [child1Gender, setChild1Gender] = useState('girl');
    const [child2Name, setChild2Name] = useState('');
    const [child2Gender, setChild2Gender] = useState('girl');

    const [c1Personality, setC1Personality] = useState('playful');
    const [c2Personality, setC2Personality] = useState('playful');

    const handleNextStep = async (e) => {
        e.preventDefault();

        if (wizardStep === 1) {
            if (child1Name.trim() && child2Name.trim()) {
                setWizardStep(2);
            }
        } else if (wizardStep === 2) {
            setWizardStep(3);
            setIsGenerating(true);

            try {
                console.log("Generating avatars...");
                const res1 = await fetch('http://localhost:8000/api/profile/generate_avatar', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: child1Name, gender: child1Gender, personality: c1Personality })
                });
                const data1 = await res1.json();

                const res2 = await fetch('http://localhost:8000/api/profile/generate_avatar', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: child2Name, gender: child2Gender, personality: c2Personality })
                });
                const data2 = await res2.json();

                onComplete({
                    c1_name: child1Name.trim(), c1_gender: child1Gender, c1_personality: c1Personality, c1_avatar: data1.avatar_url,
                    c2_name: child2Name.trim(), c2_gender: child2Gender, c2_personality: c2Personality, c2_avatar: data2.avatar_url
                });

            } catch (err) {
                console.error("Avatar Gen Failed:", err);
                onComplete({
                    c1_name: child1Name.trim(), c1_gender: child1Gender, c1_personality: c1Personality,
                    c2_name: child2Name.trim(), c2_gender: child2Gender, c2_personality: c2Personality
                });
            }
        }
    };

    const GenderToggle = ({ selected, onChange, label }) => (
        <div style={{ display: 'flex', gap: '10px', marginTop: '10px' }}>
            <button
                type="button"
                onClick={() => onChange('boy')}
                style={{
                    flex: 1,
                    padding: '10px',
                    borderRadius: '20px',
                    border: selected === 'boy' ? '2px solid #3b82f6' : '2px solid transparent',
                    background: selected === 'boy' ? 'rgba(59, 130, 246, 0.2)' : 'rgba(255,255,255,0.1)',
                    color: 'white',
                    cursor: 'pointer',
                    transition: 'all 0.2s'
                }}
            >
                👦 {t.boy}
            </button>
            <button
                type="button"
                onClick={() => onChange('girl')}
                style={{
                    flex: 1,
                    padding: '10px',
                    borderRadius: '20px',
                    border: selected === 'girl' ? '2px solid #ec4899' : '2px solid transparent',
                    background: selected === 'girl' ? 'rgba(236, 72, 153, 0.2)' : 'rgba(255,255,255,0.1)',
                    color: 'white',
                    cursor: 'pointer',
                    transition: 'all 0.2s'
                }}
            >
                👧 {t.girl}
            </button>
        </div>
    );

    const PersonalitySelect = ({ selected, onChange, name }) => (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginTop: '15px' }}>
            {[
                { id: 'bold', icon: '🐉', label: 'Dragon' },
                { id: 'creative', icon: '🦄', label: 'Unicorn' },
                { id: 'analytical', icon: '🦉', label: 'Owl' },
                { id: 'playful', icon: '🐬', label: 'Dolphin' },
            ].map(trait => (
                <label
                    key={trait.id}
                    style={{
                        display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '15px',
                        borderRadius: '15px', cursor: 'pointer', transition: 'all 0.2s',
                        border: selected === trait.id ? '2px solid #8b5cf6' : '1px solid rgba(255,255,255,0.2)',
                        background: selected === trait.id ? 'rgba(139, 92, 246, 0.2)' : 'rgba(255,255,255,0.05)',
                    }}
                >
                    <input
                        type="radio" name={name} value={trait.id} checked={selected === trait.id}
                        onChange={() => onChange(trait.id)} style={{ display: 'none' }}
                    />
                    <span style={{ fontSize: '2rem' }}>{trait.icon}</span>
                    <span style={{ color: 'white', marginTop: '5px', fontSize: '0.9rem' }}>{trait.label}</span>
                </label>
            ))}
        </div>
    );

    return (
        <div className="glass-panel" style={{
            padding: '40px 50px',
            textAlign: 'center',
            maxWidth: '600px',
            marginTop: '40px',
            animation: 'slideUp 0.5s ease-out'
        }}>
            {wizardStep === 1 && (
                <>
                    <h2 style={{ fontSize: '2.5rem', marginBottom: '10px', color: '#fff' }}>
                        {t.setupTitle}
                    </h2>
                    <p style={{ fontSize: '1.2rem', color: 'rgba(255,255,255,0.8)', marginBottom: '30px' }}>
                        {t.setupSubtitle}
                    </p>

                    <form onSubmit={handleNextStep} style={{ display: 'flex', flexDirection: 'column', gap: '30px' }}>

                        <div style={{ background: 'rgba(255,255,255,0.05)', padding: '20px', borderRadius: '20px', border: '1px solid rgba(255,255,255,0.1)' }}>
                            <h3 style={{ color: 'var(--color-accent-pink)', marginBottom: '15px' }}>{t.child1Title}</h3>
                            <input
                                type="text"
                                value={child1Name}
                                onChange={(e) => setChild1Name(e.target.value)}
                                placeholder={t.namePlaceholder}
                                required
                                style={{ width: '100%', padding: '12px 20px', borderRadius: '25px', border: 'none', background: 'rgba(255,255,255,0.9)', fontSize: '1.1rem', boxSizing: 'border-box' }}
                            />
                            <GenderToggle selected={child1Gender} onChange={setChild1Gender} />
                        </div>

                        <div style={{ background: 'rgba(255,255,255,0.05)', padding: '20px', borderRadius: '20px', border: '1px solid rgba(255,255,255,0.1)' }}>
                            <h3 style={{ color: 'var(--color-accent-purple)', marginBottom: '15px' }}>{t.child2Title}</h3>
                            <input
                                type="text"
                                value={child2Name}
                                onChange={(e) => setChild2Name(e.target.value)}
                                placeholder={t.namePlaceholder}
                                required
                                style={{ width: '100%', padding: '12px 20px', borderRadius: '25px', border: 'none', background: 'rgba(255,255,255,0.9)', fontSize: '1.1rem', boxSizing: 'border-box' }}
                            />
                            <GenderToggle selected={child2Gender} onChange={setChild2Gender} />
                        </div>

                        <button
                            type="submit"
                            disabled={!child1Name.trim() || !child2Name.trim()}
                            style={{
                                background: 'linear-gradient(135deg, var(--color-accent-pink), var(--color-accent-purple))',
                                border: 'none', padding: '18px 40px', borderRadius: '50px', color: 'white', fontSize: '1.5rem', fontWeight: 'bold',
                                cursor: (!child1Name.trim() || !child2Name.trim()) ? 'not-allowed' : 'pointer',
                                opacity: (!child1Name.trim() || !child2Name.trim()) ? 0.5 : 1,
                                boxShadow: '0 4px 15px rgba(236, 72, 153, 0.4)', transition: 'transform 0.2s, opacity 0.2s', marginTop: '10px'
                            }}
                        >
                            Next Challenge ➡️
                        </button>
                    </form>
                </>
            )}

            {wizardStep === 2 && (
                <>
                    <h2 style={{ fontSize: '2.5rem', marginBottom: '10px', color: '#fff' }}>
                        Choose Your Spirit!
                    </h2>
                    <p style={{ fontSize: '1.2rem', color: 'rgba(255,255,255,0.8)', marginBottom: '30px' }}>
                        Which magical creature are you most like?
                    </p>

                    <form onSubmit={handleNextStep} style={{ display: 'flex', flexDirection: 'column', gap: '30px' }}>
                        <div style={{ background: 'rgba(255,255,255,0.05)', padding: '20px', borderRadius: '20px', border: '1px solid rgba(255,255,255,0.1)' }}>
                            <h3 style={{ color: 'white', marginBottom: '5px' }}>{child1Name || "Adventurer 1"}</h3>
                            <PersonalitySelect selected={c1Personality} onChange={setC1Personality} name="c1_trait" />
                        </div>

                        <div style={{ background: 'rgba(255,255,255,0.05)', padding: '20px', borderRadius: '20px', border: '1px solid rgba(255,255,255,0.1)' }}>
                            <h3 style={{ color: 'white', marginBottom: '5px' }}>{child2Name || "Adventurer 2"}</h3>
                            <PersonalitySelect selected={c2Personality} onChange={setC2Personality} name="c2_trait" />
                        </div>

                        <button
                            type="submit"
                            style={{
                                background: 'linear-gradient(135deg, var(--color-accent-pink), var(--color-accent-purple))',
                                border: 'none', padding: '18px 40px', borderRadius: '50px', color: 'white', fontSize: '1.5rem', fontWeight: 'bold',
                                cursor: 'pointer', boxShadow: '0 4px 15px rgba(236, 72, 153, 0.4)', transition: 'transform 0.2s', marginTop: '10px'
                            }}
                        >
                            {t.startMagic}
                        </button>
                    </form>
                </>
            )}

            {wizardStep === 3 && (
                <div style={{ padding: '40px 0' }}>
                    <div style={{ fontSize: '6rem', animation: 'spin 3s linear infinite', marginBottom: '30px' }}>
                        ✨
                    </div>
                    <h2 style={{ fontSize: '2rem', color: '#fff' }}>
                        Weaving Custom Avatars...
                    </h2>
                    <p style={{ fontSize: '1.2rem', color: 'rgba(255,255,255,0.7)', marginTop: '15px' }}>
                        Our AI takes about 10 seconds to summon your new heroes! 🪄
                    </p>
                </div>
            )}
        </div>
    );
}
