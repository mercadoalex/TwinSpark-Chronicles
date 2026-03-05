import React, { useState } from 'react';
import LoadingAnimation from './LoadingAnimation';

export default function CharacterSetup({ t, onComplete }) {
    const [wizardStep, setWizardStep] = useState(1);
    const [isGenerating, setIsGenerating] = useState(false);

    // Basic info
    const [child1Name, setChild1Name] = useState('');
    const [child1Gender, setChild1Gender] = useState('girl');
    const [child2Name, setChild2Name] = useState('');
    const [child2Gender, setChild2Gender] = useState('girl');

    // Personality (spirit animals)
    const [c1Personality, setC1Personality] = useState('dragon');
    const [c2Personality, setC2Personality] = useState('unicorn');

    // Rich character attributes (NEW!)
    const [c1Tool, setC1Tool] = useState('sword');
    const [c2Tool, setC2Tool] = useState('book');
    
    const [c1Outfit, setC1Outfit] = useState('knight_armor');
    const [c2Outfit, setC2Outfit] = useState('wizard_robe');
    
    const [c1Toy, setC1Toy] = useState('teddy_bear');
    const [c1ToyName, setC1ToyName] = useState('');
    const [c2Toy, setC2Toy] = useState('storybook');
    const [c2ToyName, setC2ToyName] = useState('');
    
    const [c1Place, setC1Place] = useState('castle');
    const [c2Place, setC2Place] = useState('forest');

    const handleNextStep = async (e) => {
        e.preventDefault();

        if (wizardStep === 1) {
            // Step 1: Names and genders
            if (child1Name.trim() && child2Name.trim()) {
                setWizardStep(2);
            }
        } else if (wizardStep === 2) {
            // Step 2: Spirit animals
            setWizardStep(3);
        } else if (wizardStep === 3) {
            // Step 3: Favorite tools
            setWizardStep(4);
        } else if (wizardStep === 4) {
            // Step 4: Favorite outfits
            setWizardStep(5);
        } else if (wizardStep === 5) {
            // Step 5: Favorite toys
            setWizardStep(6);
        } else if (wizardStep === 6) {
            // Step 6: Favorite places
            setWizardStep(7);
        } else if (wizardStep === 7) {
            // Step 7: Generate avatars and complete
            setWizardStep(8);
            setIsGenerating(true);

            try {
                console.log("Generating avatars with rich profiles...");
                const res1 = await fetch('http://localhost:8000/api/profile/generate_avatar', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        name: child1Name, 
                        gender: child1Gender, 
                        personality: c1Personality,
                        outfit: c1Outfit
                    })
                });
                const data1 = await res1.json();

                const res2 = await fetch('http://localhost:8000/api/profile/generate_avatar', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        name: child2Name, 
                        gender: child2Gender, 
                        personality: c2Personality,
                        outfit: c2Outfit
                    })
                });
                const data2 = await res2.json();

                onComplete({
                    c1_name: child1Name.trim(), 
                    c1_gender: child1Gender, 
                    c1_personality: c1Personality, 
                    c1_avatar: data1.avatar_url,
                    c1_spirit_animal: c1Personality,
                    c1_tool: c1Tool,
                    c1_outfit: c1Outfit,
                    c1_toy: c1Toy,
                    c1_toy_name: c1ToyName || null,
                    c1_place: c1Place,
                    
                    c2_name: child2Name.trim(), 
                    c2_gender: child2Gender, 
                    c2_personality: c2Personality, 
                    c2_avatar: data2.avatar_url,
                    c2_spirit_animal: c2Personality,
                    c2_tool: c2Tool,
                    c2_outfit: c2Outfit,
                    c2_toy: c2Toy,
                    c2_toy_name: c2ToyName || null,
                    c2_place: c2Place
                });

            } catch (err) {
                console.error("Avatar Gen Failed:", err);
                onComplete({
                    c1_name: child1Name.trim(), 
                    c1_gender: child1Gender, 
                    c1_personality: c1Personality,
                    c1_spirit_animal: c1Personality,
                    c1_tool: c1Tool,
                    c1_outfit: c1Outfit,
                    c1_toy: c1Toy,
                    c1_toy_name: c1ToyName || null,
                    c1_place: c1Place,
                    
                    c2_name: child2Name.trim(), 
                    c2_gender: child2Gender, 
                    c2_personality: c2Personality,
                    c2_spirit_animal: c2Personality,
                    c2_tool: c2Tool,
                    c2_outfit: c2Outfit,
                    c2_toy: c2Toy,
                    c2_toy_name: c2ToyName || null,
                    c2_place: c2Place
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
                    minHeight: '60px',
                    padding: '15px',
                    borderRadius: '20px',
                    fontSize: '1.2rem',
                    fontWeight: '700',
                    border: selected === 'boy' ? '3px solid #3b82f6' : '2px solid transparent',
                    background: selected === 'boy' ? 'rgba(59, 130, 246, 0.3)' : 'rgba(255,255,255,0.1)',
                    color: 'white',
                    cursor: 'pointer',
                    transition: 'all 0.3s',
                    boxShadow: selected === 'boy' ? '0 4px 15px rgba(59, 130, 246, 0.4)' : 'none'
                }}
            >
                👦 {t.boy}
            </button>
            <button
                type="button"
                onClick={() => onChange('girl')}
                style={{
                    flex: 1,
                    minHeight: '60px',
                    padding: '15px',
                    borderRadius: '20px',
                    fontSize: '1.2rem',
                    fontWeight: '700',
                    border: selected === 'girl' ? '3px solid #ec4899' : '2px solid transparent',
                    background: selected === 'girl' ? 'rgba(236, 72, 153, 0.3)' : 'rgba(255,255,255,0.1)',
                    color: 'white',
                    cursor: 'pointer',
                    transition: 'all 0.3s',
                    boxShadow: selected === 'girl' ? '0 4px 15px rgba(236, 72, 153, 0.4)' : 'none'
                }}
            >
                👧 {t.girl}
            </button>
        </div>
    );

    const PersonalitySelect = ({ selected, onChange, name }) => (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginTop: '15px' }}>
            {[
                { id: 'dragon', icon: '🐉', label: 'Dragon', trait: 'Bold' },
                { id: 'unicorn', icon: '🦄', label: 'Unicorn', trait: 'Creative' },
                { id: 'owl', icon: '🦉', label: 'Owl', trait: 'Wise' },
                { id: 'dolphin', icon: '🐬', label: 'Dolphin', trait: 'Playful' },
                { id: 'fox', icon: '🦊', label: 'Fox', trait: 'Clever' },
                { id: 'bear', icon: '🐻', label: 'Bear', trait: 'Strong' },
                { id: 'eagle', icon: '🦅', label: 'Eagle', trait: 'Free' },
                { id: 'cat', icon: '🐱', label: 'Cat', trait: 'Agile' },
            ].map(trait => (
                <label
                    key={trait.id}
                    style={{
                        display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '15px',
                        borderRadius: '15px', cursor: 'pointer', transition: 'all 0.2s',
                        border: selected === trait.id ? '3px solid #8b5cf6' : '2px solid rgba(255,255,255,0.2)',
                        background: selected === trait.id ? 'rgba(139, 92, 246, 0.3)' : 'rgba(255,255,255,0.05)',
                        transform: selected === trait.id ? 'scale(1.05)' : 'scale(1)',
                        boxShadow: selected === trait.id ? '0 8px 20px rgba(139, 92, 246, 0.4)' : 'none'
                    }}
                >
                    <input
                        type="radio" name={name} value={trait.id} checked={selected === trait.id}
                        onChange={() => onChange(trait.id)} style={{ display: 'none' }}
                    />
                    <span style={{ fontSize: '2.5rem', marginBottom: '5px' }}>{trait.icon}</span>
                    <span style={{ color: 'white', fontWeight: '700', fontSize: '1rem' }}>{trait.label}</span>
                    <span style={{ color: 'rgba(255,255,255,0.7)', fontSize: '0.8rem' }}>{trait.trait}</span>
                </label>
            ))}
        </div>
    );

    const ToolSelect = ({ selected, onChange, name }) => (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '10px', marginTop: '15px' }}>
            {[
                { id: 'sword', icon: '🗡️', label: 'Sword' },
                { id: 'book', icon: '📚', label: 'Book' },
                { id: 'paintbrush', icon: '🎨', label: 'Brush' },
                { id: 'magnifier', icon: '🔬', label: 'Magnifier' },
                { id: 'flute', icon: '🎵', label: 'Flute' },
                { id: 'shield', icon: '🛡️', label: 'Shield' },
                { id: 'wand', icon: '🪄', label: 'Wand' },
                { id: 'toolkit', icon: '🧰', label: 'Toolkit' },
            ].map(item => (
                <label key={item.id} className="choice-card" style={{
                    display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '12px',
                    borderRadius: '15px', cursor: 'pointer', transition: 'all 0.3s',
                    border: selected === item.id ? '3px solid var(--color-accent-blue)' : '2px solid rgba(255,255,255,0.2)',
                    background: selected === item.id ? 'rgba(59, 130, 246, 0.3)' : 'rgba(255,255,255,0.05)',
                    transform: selected === item.id ? 'scale(1.1)' : 'scale(1)',
                    boxShadow: selected === item.id ? '0 8px 20px rgba(59, 130, 246, 0.4)' : 'none'
                }}>
                    <input type="radio" name={name} value={item.id} checked={selected === item.id}
                        onChange={() => onChange(item.id)} style={{ display: 'none' }} />
                    <span style={{ fontSize: '2rem' }}>{item.icon}</span>
                    <span style={{ color: 'white', fontSize: '0.85rem', marginTop: '5px', textAlign: 'center' }}>{item.label}</span>
                </label>
            ))}
        </div>
    );

    const OutfitSelect = ({ selected, onChange, name }) => (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '10px', marginTop: '15px' }}>
            {[
                { id: 'royal_cape', icon: '👑', label: 'Royal Cape' },
                { id: 'wizard_robe', icon: '🧙', label: 'Wizard Robe' },
                { id: 'knight_armor', icon: '⚔️', label: 'Knight Armor' },
                { id: 'flower_crown', icon: '🌸', label: 'Flower Crown' },
                { id: 'colorful_scarf', icon: '🎭', label: 'Colorful Scarf' },
                { id: 'explorer_vest', icon: '🥾', label: 'Explorer Vest' },
                { id: 'performer_outfit', icon: '🎪', label: 'Performer' },
                { id: 'scientist_coat', icon: '🔬', label: 'Scientist Coat' },
            ].map(item => (
                <label key={item.id} className="choice-card" style={{
                    display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '12px',
                    borderRadius: '15px', cursor: 'pointer', transition: 'all 0.3s',
                    border: selected === item.id ? '3px solid var(--color-accent-pink)' : '2px solid rgba(255,255,255,0.2)',
                    background: selected === item.id ? 'rgba(236, 72, 153, 0.3)' : 'rgba(255,255,255,0.05)',
                    transform: selected === item.id ? 'scale(1.1)' : 'scale(1)',
                    boxShadow: selected === item.id ? '0 8px 20px rgba(236, 72, 153, 0.4)' : 'none'
                }}>
                    <input type="radio" name={name} value={item.id} checked={selected === item.id}
                        onChange={() => onChange(item.id)} style={{ display: 'none' }} />
                    <span style={{ fontSize: '2rem' }}>{item.icon}</span>
                    <span style={{ color: 'white', fontSize: '0.75rem', marginTop: '5px', textAlign: 'center', lineHeight: '1.2' }}>{item.label}</span>
                </label>
            ))}
        </div>
    );

    const ToySelect = ({ selected, onChange, name }) => (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '10px', marginTop: '15px' }}>
            {[
                { id: 'teddy_bear', icon: '🧸', label: 'Teddy Bear' },
                { id: 'train_set', icon: '🚂', label: 'Train Set' },
                { id: 'board_game', icon: '🎲', label: 'Board Game' },
                { id: 'soccer_ball', icon: '⚽', label: 'Soccer Ball' },
                { id: 'art_supplies', icon: '🎨', label: 'Art Supplies' },
                { id: 'telescope', icon: '🔭', label: 'Telescope' },
                { id: 'video_game', icon: '🎮', label: 'Video Game' },
                { id: 'storybook', icon: '📖', label: 'Storybook' },
            ].map(item => (
                <label key={item.id} className="choice-card" style={{
                    display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '12px',
                    borderRadius: '15px', cursor: 'pointer', transition: 'all 0.3s',
                    border: selected === item.id ? '3px solid var(--color-accent-green)' : '2px solid rgba(255,255,255,0.2)',
                    background: selected === item.id ? 'rgba(16, 185, 129, 0.3)' : 'rgba(255,255,255,0.05)',
                    transform: selected === item.id ? 'scale(1.1)' : 'scale(1)',
                    boxShadow: selected === item.id ? '0 8px 20px rgba(16, 185, 129, 0.4)' : 'none'
                }}>
                    <input type="radio" name={name} value={item.id} checked={selected === item.id}
                        onChange={() => onChange(item.id)} style={{ display: 'none' }} />
                    <span style={{ fontSize: '2rem' }}>{item.icon}</span>
                    <span style={{ color: 'white', fontSize: '0.75rem', marginTop: '5px', textAlign: 'center', lineHeight: '1.2' }}>{item.label}</span>
                </label>
            ))}
        </div>
    );

    const PlaceSelect = ({ selected, onChange, name }) => (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '10px', marginTop: '15px' }}>
            {[
                { id: 'beach', icon: '🏖️', label: 'Beach' },
                { id: 'mountains', icon: '🏔️', label: 'Mountains' },
                { id: 'castle', icon: '🏰', label: 'Castle' },
                { id: 'forest', icon: '🌳', label: 'Forest' },
                { id: 'theme_park', icon: '🎡', label: 'Theme Park' },
                { id: 'big_city', icon: '🏙️', label: 'Big City' },
                { id: 'camping', icon: '🏕️', label: 'Camping' },
                { id: 'island', icon: '🏝️', label: 'Island' },
            ].map(item => (
                <label key={item.id} className="choice-card" style={{
                    display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '12px',
                    borderRadius: '15px', cursor: 'pointer', transition: 'all 0.3s',
                    border: selected === item.id ? '3px solid var(--color-accent-orange)' : '2px solid rgba(255,255,255,0.2)',
                    background: selected === item.id ? 'rgba(245, 158, 11, 0.3)' : 'rgba(255,255,255,0.05)',
                    transform: selected === item.id ? 'scale(1.1)' : 'scale(1)',
                    boxShadow: selected === item.id ? '0 8px 20px rgba(245, 158, 11, 0.4)' : 'none'
                }}>
                    <input type="radio" name={name} value={item.id} checked={selected === item.id}
                        onChange={() => onChange(item.id)} style={{ display: 'none' }} />
                    <span style={{ fontSize: '2rem' }}>{item.icon}</span>
                    <span style={{ color: 'white', fontSize: '0.75rem', marginTop: '5px', textAlign: 'center', lineHeight: '1.2' }}>{item.label}</span>
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
            {/* Progress Indicator */}
            {wizardStep < 8 && (
                <div style={{ marginBottom: '30px' }}>
                    <p style={{ color: 'rgba(255,255,255,0.7)', fontSize: '0.9rem', marginBottom: '10px' }}>
                        Step {wizardStep} of 7
                    </p>
                    <div style={{
                        display: 'flex',
                        gap: '8px',
                        justifyContent: 'center',
                        alignItems: 'center'
                    }}>
                        {[1, 2, 3, 4, 5, 6, 7].map(step => (
                            <div
                                key={step}
                                style={{
                                    width: step === wizardStep ? '40px' : '12px',
                                    height: '12px',
                                    borderRadius: '10px',
                                    background: step <= wizardStep 
                                        ? 'linear-gradient(135deg, var(--color-accent-pink), var(--color-accent-purple))' 
                                        : 'rgba(255,255,255,0.2)',
                                    transition: 'all 0.3s ease',
                                    boxShadow: step === wizardStep ? '0 0 10px rgba(139, 92, 246, 0.6)' : 'none'
                                }}
                            />
                        ))}
                    </div>
                </div>
            )}

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
                            className="btn-magic"
                            style={{
                                background: 'linear-gradient(135deg, var(--color-accent-pink), var(--color-accent-purple))',
                                opacity: (!child1Name.trim() || !child2Name.trim()) ? 0.5 : 1,
                                cursor: (!child1Name.trim() || !child2Name.trim()) ? 'not-allowed' : 'pointer',
                                marginTop: '10px',
                                width: '100%'
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
                        {t.spiritTitle}
                    </h2>
                    <p style={{ fontSize: '1.2rem', color: 'rgba(255,255,255,0.8)', marginBottom: '30px' }}>
                        {t.spiritSubtitle}
                    </p>

                    <form onSubmit={handleNextStep} style={{ display: 'flex', flexDirection: 'column', gap: '30px' }}>
                        <div style={{ background: 'rgba(255,255,255,0.05)', padding: '20px', borderRadius: '20px', border: '1px solid rgba(255,255,255,0.1)' }}>
                            <h3 style={{ color: 'white', marginBottom: '5px' }}>{child1Name || t.child1Title}</h3>
                            <PersonalitySelect selected={c1Personality} onChange={setC1Personality} name="c1_trait" />
                        </div>

                        <div style={{ background: 'rgba(255,255,255,0.05)', padding: '20px', borderRadius: '20px', border: '1px solid rgba(255,255,255,0.1)' }}>
                            <h3 style={{ color: 'white', marginBottom: '5px' }}>{child2Name || t.child2Title}</h3>
                            <PersonalitySelect selected={c2Personality} onChange={setC2Personality} name="c2_trait" />
                        </div>

                        <button type="submit" className="btn-magic" style={{
                            background: 'linear-gradient(135deg, var(--color-accent-purple), var(--color-accent-blue))',
                            marginTop: '10px', width: '100%'
                        }}>
                            {t.nextTool}
                        </button>
                    </form>
                </>
            )}

            {wizardStep === 3 && (
                <>
                    <h2 style={{ fontSize: '2.5rem', marginBottom: '10px', color: '#fff' }}>
                        {t.toolTitle}
                    </h2>
                    <p style={{ fontSize: '1.2rem', color: 'rgba(255,255,255,0.8)', marginBottom: '30px' }}>
                        {t.toolSubtitle}
                    </p>

                    <form onSubmit={handleNextStep} style={{ display: 'flex', flexDirection: 'column', gap: '30px' }}>
                        <div style={{ background: 'rgba(255,255,255,0.05)', padding: '20px', borderRadius: '20px', border: '1px solid rgba(255,255,255,0.1)' }}>
                            <h3 style={{ color: 'white', marginBottom: '5px' }}>{child1Name}{t.toolLabel}</h3>
                            <ToolSelect selected={c1Tool} onChange={setC1Tool} name="c1_tool" />
                        </div>

                        <div style={{ background: 'rgba(255,255,255,0.05)', padding: '20px', borderRadius: '20px', border: '1px solid rgba(255,255,255,0.1)' }}>
                            <h3 style={{ color: 'white', marginBottom: '5px' }}>{child2Name}{t.toolLabel}</h3>
                            <ToolSelect selected={c2Tool} onChange={setC2Tool} name="c2_tool" />
                        </div>

                        <button type="submit" className="btn-magic" style={{
                            background: 'linear-gradient(135deg, var(--color-accent-blue), var(--color-accent-pink))',
                            marginTop: '10px', width: '100%'
                        }}>
                            {t.nextOutfit}
                        </button>
                    </form>
                </>
            )}

            {wizardStep === 4 && (
                <>
                    <h2 style={{ fontSize: '2.5rem', marginBottom: '10px', color: '#fff' }}>
                        {t.outfitTitle}
                    </h2>
                    <p style={{ fontSize: '1.2rem', color: 'rgba(255,255,255,0.8)', marginBottom: '30px' }}>
                        {t.outfitSubtitle}
                    </p>

                    <form onSubmit={handleNextStep} style={{ display: 'flex', flexDirection: 'column', gap: '30px' }}>
                        <div style={{ background: 'rgba(255,255,255,0.05)', padding: '20px', borderRadius: '20px', border: '1px solid rgba(255,255,255,0.1)' }}>
                            <h3 style={{ color: 'white', marginBottom: '5px' }}>{child1Name}{t.outfitLabel}</h3>
                            <OutfitSelect selected={c1Outfit} onChange={setC1Outfit} name="c1_outfit" />
                        </div>

                        <div style={{ background: 'rgba(255,255,255,0.05)', padding: '20px', borderRadius: '20px', border: '1px solid rgba(255,255,255,0.1)' }}>
                            <h3 style={{ color: 'white', marginBottom: '5px' }}>{child2Name}{t.outfitLabel}</h3>
                            <OutfitSelect selected={c2Outfit} onChange={setC2Outfit} name="c2_outfit" />
                        </div>

                        <button type="submit" className="btn-magic" style={{
                            background: 'linear-gradient(135deg, var(--color-accent-pink), var(--color-accent-green))',
                            marginTop: '10px', width: '100%'
                        }}>
                            {t.nextToy}
                        </button>
                    </form>
                </>
            )}

            {wizardStep === 5 && (
                <>
                    <h2 style={{ fontSize: '2.5rem', marginBottom: '10px', color: '#fff' }}>
                        {t.toyTitle}
                    </h2>
                    <p style={{ fontSize: '1.2rem', color: 'rgba(255,255,255,0.8)', marginBottom: '30px' }}>
                        {t.toySubtitle}
                    </p>

                    <form onSubmit={handleNextStep} style={{ display: 'flex', flexDirection: 'column', gap: '30px' }}>
                        <div style={{ background: 'rgba(255,255,255,0.05)', padding: '20px', borderRadius: '20px', border: '1px solid rgba(255,255,255,0.1)' }}>
                            <h3 style={{ color: 'white', marginBottom: '5px' }}>{child1Name}{t.toyLabel}</h3>
                            <ToySelect selected={c1Toy} onChange={setC1Toy} name="c1_toy" />
                            <input
                                type="text"
                                value={c1ToyName}
                                onChange={(e) => setC1ToyName(e.target.value)}
                                placeholder={t.toyNamePlaceholder}
                                style={{
                                    width: '100%', padding: '12px 20px', borderRadius: '25px', border: 'none',
                                    background: 'rgba(255,255,255,0.9)', fontSize: '1rem', marginTop: '15px', boxSizing: 'border-box'
                                }}
                            />
                        </div>

                        <div style={{ background: 'rgba(255,255,255,0.05)', padding: '20px', borderRadius: '20px', border: '1px solid rgba(255,255,255,0.1)' }}>
                            <h3 style={{ color: 'white', marginBottom: '5px' }}>{child2Name}{t.toyLabel}</h3>
                            <ToySelect selected={c2Toy} onChange={setC2Toy} name="c2_toy" />
                            <input
                                type="text"
                                value={c2ToyName}
                                onChange={(e) => setC2ToyName(e.target.value)}
                                placeholder={t.toyNamePlaceholder}
                                style={{
                                    width: '100%', padding: '12px 20px', borderRadius: '25px', border: 'none',
                                    background: 'rgba(255,255,255,0.9)', fontSize: '1rem', marginTop: '15px', boxSizing: 'border-box'
                                }}
                            />
                        </div>

                        <button type="submit" className="btn-magic" style={{
                            background: 'linear-gradient(135deg, var(--color-accent-green), var(--color-accent-orange))',
                            marginTop: '10px', width: '100%'
                        }}>
                            {t.nextPlace}
                        </button>
                    </form>
                </>
            )}

            {wizardStep === 6 && (
                <>
                    <h2 style={{ fontSize: '2.5rem', marginBottom: '10px', color: '#fff' }}>
                        {t.placeTitle}
                    </h2>
                    <p style={{ fontSize: '1.2rem', color: 'rgba(255,255,255,0.8)', marginBottom: '30px' }}>
                        {t.placeSubtitle}
                    </p>

                    <form onSubmit={handleNextStep} style={{ display: 'flex', flexDirection: 'column', gap: '30px' }}>
                        <div style={{ background: 'rgba(255,255,255,0.05)', padding: '20px', borderRadius: '20px', border: '1px solid rgba(255,255,255,0.1)' }}>
                            <h3 style={{ color: 'white', marginBottom: '5px' }}>{child1Name}{t.placeLabel}</h3>
                            <PlaceSelect selected={c1Place} onChange={setC1Place} name="c1_place" />
                        </div>

                        <div style={{ background: 'rgba(255,255,255,0.05)', padding: '20px', borderRadius: '20px', border: '1px solid rgba(255,255,255,0.1)' }}>
                            <h3 style={{ color: 'white', marginBottom: '5px' }}>{child2Name}{t.placeLabel}</h3>
                            <PlaceSelect selected={c2Place} onChange={setC2Place} name="c2_place" />
                        </div>

                        <button type="submit" className="btn-magic" style={{
                            background: 'linear-gradient(135deg, var(--color-accent-orange), var(--color-accent-purple))',
                            marginTop: '10px', width: '100%'
                        }}>
                            {t.createHeroes}
                        </button>
                    </form>
                </>
            )}

            {wizardStep === 7 && (
                <div style={{ textAlign: 'center', padding: '40px 20px' }}>
                    <h2 style={{ fontSize: '2.5rem', marginBottom: '30px', color: '#fff' }}>
                        {t.reviewTitle}
                    </h2>
                    
                    <div style={{ display: 'flex', gap: '20px', flexDirection: 'column', marginBottom: '30px' }}>
                        <div style={{ background: 'rgba(255,255,255,0.1)', padding: '20px', borderRadius: '20px' }}>
                            <h3 style={{ color: 'var(--color-accent-pink)', fontSize: '1.8rem' }}>{child1Name}</h3>
                            <p style={{ color: 'white', fontSize: '1.1rem', marginTop: '10px' }}>
                                {c1Personality === 'dragon' && '🐉 Dragon'} 
                                {c1Personality === 'unicorn' && '🦄 Unicorn'}
                                {c1Personality === 'owl' && '🦉 Owl'}
                                {c1Personality === 'dolphin' && '🐬 Dolphin'}
                                {c1Personality === 'fox' && '🦊 Fox'}
                                {c1Personality === 'bear' && '🐻 Bear'}
                                {c1Personality === 'eagle' && '🦅 Eagle'}
                                {c1Personality === 'cat' && '🐱 Cat'}
                                {' • '}
                                {t.reviewTool}: {c1Tool.replace('_', ' ')}
                                {' • '}
                                {t.reviewStyle}: {c1Outfit.replace(/_/g, ' ')}
                            </p>
                            <p style={{ color: 'rgba(255,255,255,0.8)', fontSize: '1rem', marginTop: '5px' }}>
                                {t.reviewTreasure}: {c1Toy.replace(/_/g, ' ')} {c1ToyName && `"${c1ToyName}"`}
                                {' • '}
                                {t.reviewDreams}: {c1Place.replace(/_/g, ' ')}
                            </p>
                        </div>

                        <div style={{ background: 'rgba(255,255,255,0.1)', padding: '20px', borderRadius: '20px' }}>
                            <h3 style={{ color: 'var(--color-accent-purple)', fontSize: '1.8rem' }}>{child2Name}</h3>
                            <p style={{ color: 'white', fontSize: '1.1rem', marginTop: '10px' }}>
                                {c2Personality === 'dragon' && '🐉 Dragon'}
                                {c2Personality === 'unicorn' && '🦄 Unicorn'}
                                {c2Personality === 'owl' && '🦉 Owl'}
                                {c2Personality === 'dolphin' && '🐬 Dolphin'}
                                {c2Personality === 'fox' && '🦊 Fox'}
                                {c2Personality === 'bear' && '🐻 Bear'}
                                {c2Personality === 'eagle' && '🦅 Eagle'}
                                {c2Personality === 'cat' && '🐱 Cat'}
                                {' • '}
                                {t.reviewTool}: {c2Tool.replace('_', ' ')}
                                {' • '}
                                {t.reviewStyle}: {c2Outfit.replace(/_/g, ' ')}
                            </p>
                            <p style={{ color: 'rgba(255,255,255,0.8)', fontSize: '1rem', marginTop: '5px' }}>
                                {t.reviewTreasure}: {c2Toy.replace(/_/g, ' ')} {c2ToyName && `"${c2ToyName}"`}
                                {' • '}
                                {t.reviewDreams}: {c2Place.replace(/_/g, ' ')}
                            </p>
                        </div>
                    </div>

                    <button onClick={handleNextStep} className="btn-magic" style={{
                        background: 'linear-gradient(135deg, var(--color-accent-pink), var(--color-accent-purple))',
                        width: '100%', fontSize: '1.3rem', padding: '20px'
                    }}>
                        {t.beginAdventure}
                    </button>
                </div>
            )}

            {wizardStep === 8 && (
                <LoadingAnimation 
                    type="avatar" 
                    message="Our AI is crafting your unique heroes! This takes about 10 seconds. 🪄"
                />
            )}
        </div>
    );
}
