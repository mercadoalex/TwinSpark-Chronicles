import React, { useState } from 'react';

// ✅ CORRECTO: Importar desde shared components (barrel exports)
import { LoadingAnimation } from '../../../shared/components';
import { ChildFriendlyButton } from '../../../shared/components';

// O mejor aún, en una sola línea:
// import { LoadingAnimation, ChildFriendlyButton } from '../../../shared/components';

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

  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    
    if (!formData.c1_name || !formData.c2_name) {
      alert(t?.enterNames || 'Please enter both names!');
      return;
    }

    setIsLoading(true);

    setTimeout(() => {
      onComplete(formData);
      setIsLoading(false);
    }, 1000);
  };

  const handleChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

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

      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '30px' }}>
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
