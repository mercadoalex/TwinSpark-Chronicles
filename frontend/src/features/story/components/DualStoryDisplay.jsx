import React from 'react';

function DualStoryDisplay({ storyBeat, t, profiles, onChoice }) {
  console.log("📖 DualStoryDisplay rendering with:", storyBeat);
  console.log("🖼️ Scene image URL:", storyBeat?.scene_image_url);
  
  if (!storyBeat) {
    return (
      <div style={{ 
        textAlign: 'center', 
        padding: '40px',
        color: '#FFD700',
        fontSize: '1.5rem'
      }}>
        ✨ Preparing your magical adventure...
      </div>
    );
  }

  return (
    <div className="dual-story-container" style={{
      padding: '20px',
      maxWidth: '1200px',
      margin: '0 auto'
    }}>
      {/* Scene Image */}
      {storyBeat?.scene_image_url && (
        <div className="scene-image" style={{
          width: '100%',
          maxWidth: '800px',
          margin: '0 auto 30px',
          borderRadius: '20px',
          overflow: 'hidden',
          boxShadow: '0 10px 40px rgba(0,0,0,0.3)'
        }}>
          <img 
            src={storyBeat.scene_image_url.startsWith('http') 
              ? storyBeat.scene_image_url 
              : `http://localhost:8000${storyBeat.scene_image_url}`}
            alt="Scene" 
            style={{
              width: '100%',
              height: 'auto',
              display: 'block'
            }}
            onLoad={() => console.log("✅ Image loaded successfully")}
            onError={(e) => console.error("❌ Image failed to load:", e.target.src)}
          />
        </div>
      )}

      {/* Narration */}
      {storyBeat?.narration && (
        <div style={{
          textAlign: 'center',
          fontSize: '1.3rem',
          color: '#FFD700',
          marginBottom: '40px',
          fontStyle: 'italic',
          textShadow: '0 0 10px rgba(255,215,0,0.5)'
        }}>
          {storyBeat.narration}
        </div>
      )}

      {/* Dual Perspectives */}
      <div className="perspectives-container" style={{
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        gap: '30px',
        marginBottom: '40px'
      }}>
        {/* Child 1 Perspective */}
        <div className="perspective-card" style={{
          background: 'linear-gradient(135deg, rgba(255,182,193,0.2) 0%, rgba(255,105,180,0.2) 100%)',
          padding: '30px',
          borderRadius: '20px',
          border: '2px solid rgba(255,182,193,0.5)',
          boxShadow: '0 5px 20px rgba(255,105,180,0.3)'
        }}>
          <h3 style={{
            fontSize: '1.5rem',
            color: '#FF69B4',
            marginBottom: '15px',
            textShadow: '0 0 10px rgba(255,105,180,0.5)'
          }}>
            {profiles?.c1_name}'s {t?.perspective || 'Magic'} ✨
          </h3>
          <p style={{
            fontSize: '1.1rem',
            lineHeight: '1.6',
            color: '#fff'
          }}>
            {storyBeat?.child1_perspective || `${profiles?.c1_name} is ready for adventure!`}
          </p>
        </div>

        {/* Child 2 Perspective */}
        <div className="perspective-card" style={{
          background: 'linear-gradient(135deg, rgba(147,112,219,0.2) 0%, rgba(138,43,226,0.2) 100%)',
          padding: '30px',
          borderRadius: '20px',
          border: '2px solid rgba(147,112,219,0.5)',
          boxShadow: '0 5px 20px rgba(138,43,226,0.3)'
        }}>
          <h3 style={{
            fontSize: '1.5rem',
            color: '#9370DB',
            marginBottom: '15px',
            textShadow: '0 0 10px rgba(138,43,226,0.5)'
          }}>
            {profiles?.c2_name}'s {t?.perspective || 'Magic'} 🦄
          </h3>
          <p style={{
            fontSize: '1.1rem',
            lineHeight: '1.6',
            color: '#fff'
          }}>
            {storyBeat?.child2_perspective || `${profiles?.c2_name} feels the magic!`}
          </p>
        </div>
      </div>

      {/* INTERACTIVE CHOICES - NUEVO */}
      {storyBeat?.choices && storyBeat.choices.length > 0 && (
        <div className="choices-container" style={{
          marginTop: '40px',
          display: 'flex',
          flexDirection: 'column',
          gap: '15px',
          alignItems: 'center'
        }}>
          <h3 style={{
            fontSize: '1.8rem',
            color: '#FFD700',
            textShadow: '0 0 15px rgba(255,215,0,0.8)',
            marginBottom: '20px',
            animation: 'pulse 2s infinite'
          }}>
            ✨ What happens next? ✨
          </h3>
          <div style={{
            display: 'flex',
            gap: '20px',
            flexWrap: 'wrap',
            justifyContent: 'center',
            maxWidth: '900px'
          }}>
            {storyBeat.choices.map((choice, idx) => (
              <button
                key={idx}
                className="choice-button"
                onClick={() => {
                  console.log(`🎯 Button clicked: ${choice}`);
                  onChoice(choice);
                }}
                style={{
                  padding: '20px 40px',
                  fontSize: '1.2rem',
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  border: '3px solid rgba(255,255,255,0.3)',
                  borderRadius: '15px',
                  color: 'white',
                  cursor: 'pointer',
                  boxShadow: '0 8px 20px rgba(102,126,234,0.4)',
                  transition: 'all 0.3s ease',
                  fontFamily: 'Comic Sans MS, cursive, sans-serif',
                  fontWeight: 'bold',
                  minWidth: '250px',
                  textAlign: 'center'
                }}
                onMouseEnter={(e) => {
                  e.target.style.transform = 'translateY(-5px) scale(1.05)';
                  e.target.style.boxShadow = '0 12px 30px rgba(102,126,234,0.6)';
                }}
                onMouseLeave={(e) => {
                  e.target.style.transform = 'translateY(0) scale(1)';
                  e.target.style.boxShadow = '0 8px 20px rgba(102,126,234,0.4)';
                }}
              >
                {choice}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default DualStoryDisplay;
