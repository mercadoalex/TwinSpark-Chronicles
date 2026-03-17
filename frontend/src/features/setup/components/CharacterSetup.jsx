import React, { useState } from 'react';
import { LoadingAnimation, ChildFriendlyButton } from '../../../shared/components';
import { AvatarCreator } from '../../avatar';

const spirits = [
  { value: 'dragon', label: '🐉 Dragon' },
  { value: 'unicorn', label: '🦄 Unicorn' },
  { value: 'owl', label: '🦉 Owl' },
  { value: 'dolphin', label: '🐬 Dolphin' },
  { value: 'phoenix', label: '🔥 Phoenix' },
  { value: 'tiger', label: '🐯 Tiger' },
];

const inputStyle = {
  width: '100%', padding: '12px 16px', fontSize: '1rem',
  fontFamily: 'var(--font-body)', fontWeight: 500,
  borderRadius: 'var(--radius-sm)',
  border: '1.5px solid var(--color-glass-border)',
  background: 'rgba(0,0,0,0.25)', color: '#fff',
  transition: 'border-color 0.2s',
  outline: 'none',
};

const labelStyle = {
  display: 'block', marginBottom: '6px',
  fontFamily: 'var(--font-display)', fontSize: '0.85rem',
  fontWeight: 600, color: 'rgba(255,255,255,0.55)',
  textTransform: 'uppercase', letterSpacing: '0.06em',
};

export default function CharacterSetup({ t, onComplete }) {
  const [formData, setFormData] = useState({
    c1_name: '', c1_gender: 'girl', c1_spirit_animal: 'dragon', c1_toy_name: '',
    c2_name: '', c2_gender: 'boy', c2_spirit_animal: 'owl', c2_toy_name: '',
  });
  const [step, setStep] = useState('form');
  const [avatars, setAvatars] = useState({ child1: null, child2: null });
  const [isLoading, setIsLoading] = useState(false);

  const set = (field, value) => setFormData(prev => ({ ...prev, [field]: value }));

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!formData.c1_name || !formData.c2_name) {
      alert(t?.enterNames || 'Please enter both names!');
      return;
    }
    const wantAvatars = window.confirm(t?.wantAvatars || 'Create avatars with photos? (Optional)');
    if (wantAvatars) { setStep('avatar1'); } else { onComplete(formData); }
  };

  if (step === 'avatar1') {
    return <AvatarCreator childMetadata={{ name: formData.c1_name, gender: formData.c1_gender, spiritAnimal: formData.c1_spirit_animal, toyName: formData.c1_toy_name }} onComplete={(d) => { setAvatars(p => ({ ...p, child1: d })); setStep('avatar2'); }} onSkip={() => { setAvatars(p => ({ ...p, child1: null })); setStep('avatar2'); }} />;
  }
  if (step === 'avatar2') {
    return <AvatarCreator childMetadata={{ name: formData.c2_name, gender: formData.c2_gender, spiritAnimal: formData.c2_spirit_animal, toyName: formData.c2_toy_name }} onComplete={(d) => onComplete({ ...formData, c1_avatar: avatars.child1, c2_avatar: d })} onSkip={() => onComplete({ ...formData, c1_avatar: avatars.child1, c2_avatar: null })} />;
  }
  if (isLoading) {
    return <div className="glass-panel" style={{ padding: '60px', textAlign: 'center' }}><LoadingAnimation type="setup" message={t?.creatingCharacters || 'Creating your characters…'} /></div>;
  }

  const ChildSection = ({ num, color, borderColor }) => (
    <div style={{
      padding: '24px', borderRadius: 'var(--radius-md)',
      background: `rgba(${color}, 0.04)`,
      border: `1.5px solid rgba(${color}, 0.2)`,
    }}>
      <h3 style={{
        fontFamily: 'var(--font-display)', fontSize: '1.2rem', fontWeight: 700,
        marginBottom: '18px', color: `rgba(${color}, 1)`,
      }}>
        {num === 1 ? '🌟' : '⭐'} {t?.[`child${num}`] || `Child ${num}`}
      </h3>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
        <div>
          <label style={labelStyle}>{t?.name || 'Name'}</label>
          <input type="text" value={formData[`c${num}_name`]} onChange={e => set(`c${num}_name`, e.target.value)} placeholder={t?.enterName || 'Enter name'} style={{ ...inputStyle, borderColor: `rgba(${color}, 0.3)` }} required />
        </div>
        <div>
          <label style={labelStyle}>{t?.gender || 'Gender'}</label>
          <select value={formData[`c${num}_gender`]} onChange={e => set(`c${num}_gender`, e.target.value)} style={{ ...inputStyle, borderColor: `rgba(${color}, 0.3)` }}>
            <option value="girl">{t?.girl || 'Girl'}</option>
            <option value="boy">{t?.boy || 'Boy'}</option>
            <option value="other">{t?.other || 'Other'}</option>
          </select>
        </div>
        <div>
          <label style={labelStyle}>{t?.spiritAnimal || 'Spirit Animal'}</label>
          <select value={formData[`c${num}_spirit_animal`]} onChange={e => set(`c${num}_spirit_animal`, e.target.value)} style={{ ...inputStyle, borderColor: `rgba(${color}, 0.3)` }}>
            {spirits.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
          </select>
        </div>
        <div>
          <label style={labelStyle}>{t?.favoriteToy || 'Favorite Toy'}</label>
          <input type="text" value={formData[`c${num}_toy_name`]} onChange={e => set(`c${num}_toy_name`, e.target.value)} placeholder={t?.toyName || 'e.g., Bruno'} style={{ ...inputStyle, borderColor: `rgba(${color}, 0.3)` }} />
        </div>
      </div>
    </div>
  );

  return (
    <div className="glass-panel" style={{
      padding: '36px', maxWidth: '760px', width: '100%',
      animation: 'fadeInUp 0.5s var(--ease-smooth)',
    }}>
      <h2 style={{
        fontFamily: 'var(--font-display)', fontSize: '1.8rem', fontWeight: 700,
        marginBottom: '28px', textAlign: 'center',
        background: 'linear-gradient(135deg, var(--color-gold), var(--color-coral))',
        WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
        backgroundClip: 'text',
      }}>
        {t?.createCharacters || 'Create Your Characters'}
      </h2>

      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        <ChildSection num={1} color="244, 114, 182" />
        <ChildSection num={2} color="96, 165, 250" />

        <ChildFriendlyButton type="submit" variant="primary" style={{ marginTop: '8px', alignSelf: 'center' }}>
          {t?.startAdventure || '🚀 Start Adventure'}
        </ChildFriendlyButton>
      </form>
    </div>
  );
}
