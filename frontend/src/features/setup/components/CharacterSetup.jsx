import React, { useState } from 'react';
import { LoadingAnimation, ChildFriendlyButton } from '../../../shared/components';
import { AvatarCreator } from '../../avatar';

export default function CharacterSetup({ t, onComplete }) {
  const [formData, setFormData] = useState({
    c1_name: '',
    c1_gender: 'girl',
    c1_spirit_animal: 'dragon',
    c1_toy_name: '',
    c2_name: '',
    c2_gender: 'boy',
    c2_spirit_animal: 'owl',
    c2_toy_name: ''
  });

  const [step, setStep] = useState('form'); // 'form' | 'avatar1' | 'avatar2' | 'complete'
  const [avatars, setAvatars] = useState({ child1: null, child2: null });
  const [isLoading, setIsLoading] = useState(false);

  const handleChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleFormSubmit = (e) => {
    e.preventDefault();
    
    if (!formData.c1_name || !formData.c2_name) {
      alert(t?.enterNames || 'Please enter both names!');
      return;
    }

    // Preguntar si quieren crear avatares
    const wantAvatars = window.confirm(
      t?.wantAvatars || '¿Quieres crear avatares con fotos? (Opcional)'
    );

    if (wantAvatars) {
      setStep('avatar1');
    } else {
      // Continuar sin avatares
      onComplete(formData);
    }
  };

  const handleAvatar1Complete = (avatarData) => {
    setAvatars(prev => ({ ...prev, child1: avatarData }));
    setStep('avatar2');
  };

  const handleAvatar2Complete = (avatarData) => {
    setAvatars(prev => ({ ...prev, child2: avatarData }));
    
    // Completar setup con ambos avatares
    onComplete({
      ...formData,
      c1_avatar: avatars.child1,
      c2_avatar: avatarData
    });
  };

  const handleSkipAvatar1 = () => {
    setAvatars(prev => ({ ...prev, child1: null }));
    setStep('avatar2');
  };

  const handleSkipAvatar2 = () => {
    // Completar sin avatar del niño 2
    onComplete({
      ...formData,
      c1_avatar: avatars.child1,
      c2_avatar: null
    });
  };

  // RENDER: Avatar Capture Steps
  if (step === 'avatar1') {
    return (
      <AvatarCreator
        childMetadata={{
          name: formData.c1_name,
          gender: formData.c1_gender,
          spiritAnimal: formData.c1_spirit_animal,
          toyName: formData.c1_toy_name
        }}
        onComplete={handleAvatar1Complete}
        onSkip={handleSkipAvatar1}
      />
    );
  }

  if (step === 'avatar2') {
    return (
      <AvatarCreator
        childMetadata={{
          name: formData.c2_name,
          gender: formData.c2_gender,
          spiritAnimal: formData.c2_spirit_animal,
          toyName: formData.c2_toy_name
        }}
        onComplete={handleAvatar2Complete}
        onSkip={handleSkipAvatar2}
      />
    );
  }

  // RENDER: Loading State
  if (isLoading) {
    return (
      <div className="glass-panel" style={{ padding: '60px', textAlign: 'center' }}>
        <LoadingAnimation 
          type="setup" 
          message={t?.creatingCharacters || "Creating your characters..."} 
        />
      </div>
    );
  }

  // RENDER: Main Form
  return (
    <div className="glass-panel" style={{ padding: '40px', maxWidth: '800px' }}>
      <h2 style={{ 
        fontSize: '2.5rem', 
        marginBottom: '30px', 
        textAlign: 'center',
        color: '#fff'
      }}>
        {t?.createCharacters || 'Create Your Characters'}
      </h2>

      <form onSubmit={handleFormSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '30px' }}>
        {/* Child 1 */}
        <div className="character-section" style={{
          padding: '25px',
          background: 'rgba(139, 92, 246, 0.1)',
          borderRadius: '15px',
          border: '2px solid rgba(139, 92, 246, 0.3)'
        }}>
          <h3 style={{ fontSize: '1.8rem', marginBottom: '20px', color: '#a78bfa' }}>
            {t?.child1 || 'First Child'}
          </h3>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px' }}>
            <div>
              <label style={{ display: 'block', marginBottom: '8px', fontSize: '1.2rem', color: '#e9d5ff' }}>
                {t?.name || 'Name'}
              </label>
              <input
                type="text"
                value={formData.c1_name}
                onChange={(e) => handleChange('c1_name', e.target.value)}
                placeholder={t?.enterName || "Enter name"}
                style={{
                  width: '100%',
                  padding: '12px',
                  fontSize: '1.1rem',
                  borderRadius: '10px',
                  border: '2px solid rgba(139, 92, 246, 0.5)',
                  background: 'rgba(0,0,0,0.3)',
                  color: '#fff'
                }}
                required
              />
            </div>

            <div>
              <label style={{ display: 'block', marginBottom: '8px', fontSize: '1.2rem', color: '#e9d5ff' }}>
                {t?.gender || 'Gender'}
              </label>
              <select
                value={formData.c1_gender}
                onChange={(e) => handleChange('c1_gender', e.target.value)}
                style={{
                  width: '100%',
                  padding: '12px',
                  fontSize: '1.1rem',
                  borderRadius: '10px',
                  border: '2px solid rgba(139, 92, 246, 0.5)',
                  background: 'rgba(0,0,0,0.3)',
                  color: '#fff'
                }}
              >
                <option value="girl">{t?.girl || 'Girl'}</option>
                <option value="boy">{t?.boy || 'Boy'}</option>
                <option value="other">{t?.other || 'Other'}</option>
              </select>
            </div>

            <div>
              <label style={{ display: 'block', marginBottom: '8px', fontSize: '1.2rem', color: '#e9d5ff' }}>
                {t?.spiritAnimal || 'Spirit Animal'}
              </label>
              <select
                value={formData.c1_spirit_animal}
                onChange={(e) => handleChange('c1_spirit_animal', e.target.value)}
                style={{
                  width: '100%',
                  padding: '12px',
                  fontSize: '1.1rem',
                  borderRadius: '10px',
                  border: '2px solid rgba(139, 92, 246, 0.5)',
                  background: 'rgba(0,0,0,0.3)',
                  color: '#fff'
                }}
              >
                <option value="dragon">🐉 Dragon</option>
                <option value="unicorn">🦄 Unicorn</option>
                <option value="owl">🦉 Owl</option>
                <option value="dolphin">🐬 Dolphin</option>
                <option value="phoenix">🔥 Phoenix</option>
                <option value="tiger">🐯 Tiger</option>
              </select>
            </div>

            <div>
              <label style={{ display: 'block', marginBottom: '8px', fontSize: '1.2rem', color: '#e9d5ff' }}>
                {t?.favoriteToy || 'Favorite Toy'}
              </label>
              <input
                type="text"
                value={formData.c1_toy_name}
                onChange={(e) => handleChange('c1_toy_name', e.target.value)}
                placeholder={t?.toyName || "e.g., Bruno"}
                style={{
                  width: '100%',
                  padding: '12px',
                  fontSize: '1.1rem',
                  borderRadius: '10px',
                  border: '2px solid rgba(139, 92, 246, 0.5)',
                  background: 'rgba(0,0,0,0.3)',
                  color: '#fff'
                }}
              />
            </div>
          </div>
        </div>

        {/* Child 2 */}
        <div className="character-section" style={{
          padding: '25px',
          background: 'rgba(59, 130, 246, 0.1)',
          borderRadius: '15px',
          border: '2px solid rgba(59, 130, 246, 0.3)'
        }}>
          <h3 style={{ fontSize: '1.8rem', marginBottom: '20px', color: '#60a5fa' }}>
            {t?.child2 || 'Second Child'}
          </h3>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px' }}>
            <div>
              <label style={{ display: 'block', marginBottom: '8px', fontSize: '1.2rem', color: '#dbeafe' }}>
                {t?.name || 'Name'}
              </label>
              <input
                type="text"
                value={formData.c2_name}
                onChange={(e) => handleChange('c2_name', e.target.value)}
                placeholder={t?.enterName || "Enter name"}
                style={{
                  width: '100%',
                  padding: '12px',
                  fontSize: '1.1rem',
                  borderRadius: '10px',
                  border: '2px solid rgba(59, 130, 246, 0.5)',
                  background: 'rgba(0,0,0,0.3)',
                  color: '#fff'
                }}
                required
              />
            </div>

            <div>
              <label style={{ display: 'block', marginBottom: '8px', fontSize: '1.2rem', color: '#dbeafe' }}>
                {t?.gender || 'Gender'}
              </label>
              <select
                value={formData.c2_gender}
                onChange={(e) => handleChange('c2_gender', e.target.value)}
                style={{
                  width: '100%',
                  padding: '12px',
                  fontSize: '1.1rem',
                  borderRadius: '10px',
                  border: '2px solid rgba(59, 130, 246, 0.5)',
                  background: 'rgba(0,0,0,0.3)',
                  color: '#fff'
                }}
              >
                <option value="girl">{t?.girl || 'Girl'}</option>
                <option value="boy">{t?.boy || 'Boy'}</option>
                <option value="other">{t?.other || 'Other'}</option>
              </select>
            </div>

            <div>
              <label style={{ display: 'block', marginBottom: '8px', fontSize: '1.2rem', color: '#dbeafe' }}>
                {t?.spiritAnimal || 'Spirit Animal'}
              </label>
              <select
                value={formData.c2_spirit_animal}
                onChange={(e) => handleChange('c2_spirit_animal', e.target.value)}
                style={{
                  width: '100%',
                  padding: '12px',
                  fontSize: '1.1rem',
                  borderRadius: '10px',
                  border: '2px solid rgba(59, 130, 246, 0.5)',
                  background: 'rgba(0,0,0,0.3)',
                  color: '#fff'
                }}
              >
                <option value="dragon">🐉 Dragon</option>
                <option value="unicorn">🦄 Unicorn</option>
                <option value="owl">🦉 Owl</option>
                <option value="dolphin">🐬 Dolphin</option>
                <option value="phoenix">🔥 Phoenix</option>
                <option value="tiger">🐯 Tiger</option>
              </select>
            </div>

            <div>
              <label style={{ display: 'block', marginBottom: '8px', fontSize: '1.2rem', color: '#dbeafe' }}>
                {t?.favoriteToy || 'Favorite Toy'}
              </label>
              <input
                type="text"
                value={formData.c2_toy_name}
                onChange={(e) => handleChange('c2_toy_name', e.target.value)}
                placeholder={t?.toyName || "e.g., Book"}
                style={{
                  width: '100%',
                  padding: '12px',
                  fontSize: '1.1rem',
                  borderRadius: '10px',
                  border: '2px solid rgba(59, 130, 246, 0.5)',
                  background: 'rgba(0,0,0,0.3)',
                  color: '#fff'
                }}
              />
            </div>
          </div>
        </div>

        {/* Submit Button */}
        <ChildFriendlyButton
          type="submit"
          variant="primary"
          style={{
            fontSize: '1.6rem',
            padding: '20px 50px',
            marginTop: '20px'
          }}
        >
          {t?.startAdventure || '🚀 Start Adventure!'}
        </ChildFriendlyButton>
      </form>
    </div>
  );
}
