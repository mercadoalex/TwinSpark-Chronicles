import React, { useState, useEffect } from 'react';
import { useWebSocket } from '../features/session/hooks/useWebSocket';
import { Volume2, Image as ImageIcon, Sparkles, AlertCircle } from 'lucide-react';

const Story = ({ profiles, language }) => {
  const [assets, setAssets] = useState([]);
  const [status, setStatus] = useState('Connecting...');
  const [error, setError] = useState(null);
  
  console.log('🎬 Story component rendered with profiles:', profiles);

  // Build WebSocket URL with profiles
  const wsUrl = `ws://localhost:8000/ws/session?` + new URLSearchParams({
    lang: language,
    c1_name: profiles.child1.name,
    c1_gender: profiles.child1.gender,
    c1_personality: profiles.child1.personality,
    c1_spirit: profiles.child1.spiritAnimal,
    c1_toy: profiles.child1.favoriteToy,
    c2_name: profiles.child2.name,
    c2_gender: profiles.child2.gender,
    c2_personality: profiles.child2.personality,
    c2_spirit: profiles.child2.spiritAnimal,
    c2_toy: profiles.child2.favoriteToy
  }).toString();

  console.log('🔗 WebSocket URL:', wsUrl);

  const handleMessage = (data) => {
    console.log('📥 Story received message:', data);
    
    switch (data.type) {
      case 'CONNECTED':
        console.log('✅ Connection confirmed:', data.message);
        setStatus(data.message);
        break;
        
      case 'SESSION_STARTED':
        console.log('✅ Session started:', data.data);
        setStatus('Session started! Generating story...');
        break;
        
      case 'STATUS':
        console.log('📊 Status update:', data.message);
        setStatus(data.message);
        break;
        
      case 'CREATIVE_ASSET':
        console.log('🎨 Creative asset received:', data);
        setAssets(prev => {
          const newAssets = [...prev, data];
          console.log('📦 Total assets now:', newAssets.length);
          return newAssets;
        });
        setStatus('Receiving story...');
        break;
        
      case 'STORY_COMPLETE':
        console.log('✅ Story complete!');
        setStatus('Story ready!');
        break;
        
      case 'ERROR':
        console.error('❌ Error from server:', data.message);
        setError(data.message);
        setStatus('Error occurred');
        break;
        
      case 'HEARTBEAT':
        console.log('💓 Heartbeat received');
        break;
        
      default:
        console.log('❓ Unknown message type:', data.type);
    }
  };

  const { isConnected, connectionError, sendMessage } = useWebSocket(wsUrl, handleMessage);

  useEffect(() => {
    console.log('🔌 Connection status changed:', isConnected);
    if (isConnected) {
      setStatus('Connected! Waiting for story...');
    } else {
      setStatus('Connecting to TwinSpark AI...');
    }
  }, [isConnected]);

  useEffect(() => {
    if (connectionError) {
      console.error('❌ Connection error:', connectionError);
      setError('Failed to connect to server');
    }
  }, [connectionError]);

  const renderAsset = (asset, index) => {
    console.log('🎨 Rendering asset:', asset.media_type, index);
    
    switch (asset.media_type) {
      case 'text':
        return (
          <div 
            key={index}
            className="creative-text"
            style={{
              animation: 'fadeInUp 0.6s ease-out',
              marginBottom: '20px',
              padding: '20px',
              background: asset.metadata?.type === 'narration' 
                ? 'linear-gradient(135deg, rgba(139, 92, 246, 0.2), rgba(236, 72, 153, 0.2))'
                : 'rgba(255,255,255,0.05)',
              borderRadius: '15px',
              fontSize: asset.metadata?.type === 'narration' ? '1.3rem' : '1.1rem'
            }}
          >
            {asset.metadata?.type === 'narration' && (
              <Sparkles size={20} style={{ marginRight: '10px', color: '#a855f7' }} />
            )}
            {asset.content}
          </div>
        );
      
      case 'image':
        return (
          <div 
            key={index}
            className="creative-image"
            style={{
              animation: 'scaleIn 0.8s ease-out',
              marginBottom: '30px',
              position: 'relative'
            }}
          >
            {asset.metadata?.generated ? (
              <img 
                src={asset.content} 
                alt="Scene"
                style={{
                  width: '100%',
                  maxWidth: '600px',
                  borderRadius: '20px',
                  boxShadow: '0 10px 40px rgba(168, 85, 247, 0.4)'
                }}
              />
            ) : (
              <div style={{
                padding: '40px',
                background: 'rgba(168, 85, 247, 0.1)',
                borderRadius: '20px',
                border: '2px dashed #a855f7',
                textAlign: 'center'
              }}>
                <ImageIcon size={48} color="#a855f7" />
                <p style={{ marginTop: '15px', color: 'rgba(255,255,255,0.7)' }}>
                  🎨 Generating scene: {asset.content.substring(0, 50)}...
                </p>
              </div>
            )}
          </div>
        );
      
      case 'audio':
        return (
          <div 
            key={index}
            className="creative-audio"
            style={{
              animation: 'fadeIn 0.5s ease-out',
              marginBottom: '15px',
              padding: '15px',
              background: 'rgba(236, 72, 153, 0.1)',
              borderRadius: '10px',
              display: 'flex',
              alignItems: 'center',
              gap: '10px'
            }}
          >
            <Volume2 size={20} color="#ec4899" />
            <span style={{ fontSize: '0.9rem', color: 'rgba(255,255,255,0.8)' }}>
              🎵 {asset.content}
            </span>
          </div>
        );
      
      case 'interactive':
        const choices = asset.content.split('\n').filter(c => c.trim());
        return (
          <div 
            key={index}
            className="creative-choices"
            style={{
              animation: 'slideUp 0.8s ease-out',
              marginTop: '30px'
            }}
          >
            <h3 style={{ fontSize: '1.5rem', marginBottom: '20px', textAlign: 'center' }}>
              What will you do?
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
              {choices.map((choice, idx) => (
                <button
                  key={idx}
                  onClick={() => {
                    console.log('🎯 Choice clicked:', choice);
                    sendMessage({ type: 'CHOICE', choice, child_id: idx === 0 ? 'c1' : idx === 1 ? 'c2' : 'both' });
                  }}
                  style={{
                    padding: '20px',
                    fontSize: '1.1rem',
                    background: `linear-gradient(135deg, ${
                      idx === 0 ? '#a855f7, #ec4899' : 
                      idx === 1 ? '#3b82f6, #8b5cf6' :
                      '#f59e0b, #ef4444'
                    })`,
                    border: 'none',
                    borderRadius: '15px',
                    color: 'white',
                    cursor: 'pointer',
                    transition: 'transform 0.2s',
                  }}
                  onMouseEnter={(e) => e.target.style.transform = 'scale(1.05)'}
                  onMouseLeave={(e) => e.target.style.transform = 'scale(1)'}
                >
                  {choice}
                </button>
              ))}
            </div>
          </div>
        );
      
      default:
        return null;
    }
  };

  console.log('🎨 Rendering Story component, assets count:', assets.length);

  return (
    <div style={{ padding: '20px', maxWidth: '800px', margin: '0 auto' }}>
      {/* Status Banner */}
      <div style={{
        padding: '15px',
        background: error ? '#ef4444' : isConnected ? '#10b981' : '#f59e0b',
        borderRadius: '10px',
        marginBottom: '20px',
        textAlign: 'center',
        color: 'white',
        fontWeight: 'bold'
      }}>
        {error ? (
          <>
            <AlertCircle size={20} style={{ marginRight: '10px', verticalAlign: 'middle' }} />
            {error}
          </>
        ) : (
          <>
            {!isConnected && '🔌 '}
            {isConnected && assets.length === 0 && '✨ '}
            {isConnected && assets.length > 0 && '📖 '}
            {status}
          </>
        )}
      </div>

      {/* Debug Info */}
      <details style={{ marginBottom: '20px', padding: '10px', background: 'rgba(0,0,0,0.3)', borderRadius: '5px' }}>
        <summary style={{ cursor: 'pointer', fontWeight: 'bold' }}>🐛 Debug Info</summary>
        <pre style={{ fontSize: '0.8rem', overflow: 'auto', marginTop: '10px' }}>
          {JSON.stringify({
            isConnected,
            assetsCount: assets.length,
            status,
            error,
            profiles: {
              child1: profiles.child1.name,
              child2: profiles.child2.name
            }
          }, null, 2)}
        </pre>
      </details>

      {/* Story Assets */}
      <div className="creative-stream">
        {assets.map((asset, index) => renderAsset(asset, index))}
      </div>

      {/* Loading State */}
      {isConnected && assets.length === 0 && !error && (
        <div style={{ textAlign: 'center', padding: '60px' }}>
          <div className="spinner" style={{
            border: '4px solid rgba(168, 85, 247, 0.3)',
            borderTop: '4px solid #a855f7',
            borderRadius: '50%',
            width: '60px',
            height: '60px',
            animation: 'spin 1s linear infinite',
            margin: '0 auto 20px'
          }}></div>
          <p style={{ fontSize: '1.2rem', color: 'rgba(255,255,255,0.8)' }}>
            The Creative Director is crafting your adventure...
          </p>
        </div>
      )}
    </div>
  );
};

export default Story;