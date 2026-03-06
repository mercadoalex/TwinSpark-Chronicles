import React, { useState, useEffect, useRef } from 'react';
import DualStoryDisplay from './components/DualStoryDisplay';
import MultimodalControls from './components/MultimodalControls';
import AlertModal from './components/AlertModal';
import CharacterSetup from './components/CharacterSetup';
import ExitModal from './components/ExitModal';
import VoiceOnlyMode from './components/VoiceOnlyMode';
import LoadingAnimation from './components/LoadingAnimation';
import MagicMirror from './components/MagicMirror';
import { useFeedback } from './components/VisualFeedback';
import { Mic, Eye, Menu } from 'lucide-react';
import { translations } from './locales';
import './App.css';

function App() {
  // ===========================================
  // STATE MANAGEMENT
  // ===========================================
  
  // Audio/Visual Controls
  const [isListening, setIsListening] = useState(true);
  const [hasCamera, setHasCamera] = useState(true);
  const [isConnected, setIsConnected] = useState(false);
  
  // Language & Display Mode
  const [selectedLanguage, setSelectedLanguage] = useState(null);
  const [voiceOnlyMode, setVoiceOnlyMode] = useState(false);
  
  // Story State
  const [storyBeat, setStoryBeat] = useState(null);
  const [mechanics, setMechanics] = useState(null);
  
  // Privacy & Setup Flow
  const [showPrivacyModal, setShowPrivacyModal] = useState(true);
  const [privacyAccepted, setPrivacyAccepted] = useState(false);
  const [setupStep, setSetupStep] = useState(0); // 0=language, 1=character, 2=story, 3=end
  const [playerProfiles, setPlayerProfiles] = useState(null);
  
  // Exit Modal
  const [showExitModal, setShowExitModal] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  
  // Alerts & Feedback
  const [alertMessage, setAlertMessage] = useState(null);
  const ws = useRef(null); // WebSocket reference
  const { showFeedback, FeedbackComponent } = useFeedback();
  
  // Get translations for selected language (default to English)
  const t = selectedLanguage ? translations[selectedLanguage] : translations.en;

  const [currentAssets, setCurrentAssets] = useState({
    narration: '',
    child1_perspective: '',
    child2_perspective: '',
    image: null,
    choices: []
  });

  // Añade este state para contar assets recibidos
  const [assetsReceived, setAssetsReceived] = useState(0);
  const [totalAssets, setTotalAssets] = useState(0);

  // ===========================================
  // AUDIO FEEDBACK SYSTEM
  // ===========================================
  
  /**
   * Plays a beep sound using Web Audio API
   * @param {number} freq - Frequency in Hz (default: 880)
   * @param {number} duration - Duration in seconds (default: 0.3)
   */
  const playBeep = (freq = 880, duration = 0.3) => {
    try {
      const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();
      osc.connect(gain);
      gain.connect(audioCtx.destination);
      osc.type = 'sine';
      osc.frequency.setValueAtTime(freq, audioCtx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.0001, audioCtx.currentTime + duration);
      osc.start();
      osc.stop(audioCtx.currentTime + duration);
    } catch (e) {
      console.error("Audio context error", e);
    }
  };

  // ===========================================
  // WEBSOCKET CONNECTION
  // ===========================================
  
  /**
   * Connects to the TwinSpark AI backend via WebSocket
   * @param {string} lang - Language code (en, es, hi)
   * @param {object} profiles - Character profiles for both children
   */
  const connectToAI = (lang, profiles) => {
    // Close existing connection if any
    if (ws.current) {
      ws.current.onclose = null;
      ws.current.onerror = null;
      ws.current.onmessage = null;
      ws.current.close();
      ws.current = null;
    }

    console.log(`🔌 Attempting connection to TwinSpark AI in language: ${lang}...`);

    // Build query parameters from profiles
    const params = new URLSearchParams({
      lang: lang,
      c1_name: profiles.c1_name,
      c1_gender: profiles.c1_gender,
      c1_personality: profiles.c1_personality || 'brave',
      c1_spirit: profiles.c1_spirit_animal || 'Dragon',
      c1_toy: profiles.c1_toy_name || 'Bruno',
      c2_name: profiles.c2_name,
      c2_gender: profiles.c2_gender,
      c2_personality: profiles.c2_personality || 'wise',
      c2_spirit: profiles.c2_spirit_animal || 'Owl',
      c2_toy: profiles.c2_toy_name || 'Book'
    });

    console.log("🔌 WebSocket URL:", `ws://localhost:8000/ws/session?${params.toString()}`);

    // Create new WebSocket connection
    ws.current = new WebSocket(`ws://localhost:8000/ws/session?${params.toString()}`);

    // Connection opened
    ws.current.onopen = () => {
      console.log('✅ Connected to TwinSpark AI Engine');
      setIsConnected(true);
      playBeep(1200, 0.2); // Success beep
    };

    // Message received from backend
    ws.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log("📩 WebSocket Message:", data);

      if (data.type === 'CREATIVE_ASSET') {
        console.log(`🎨 Asset received: ${data.media_type}`, data);
        
        // Update assets immediately using functional update
        setCurrentAssets(prev => {
          const updated = { ...prev };
          
          if (data.media_type === 'text') {
            // Check metadata to determine which perspective
            const content = data.content;
            console.log("📝 Text content:", content);
            
            // Try to determine perspective from metadata or content
            if (data.metadata?.child === 'c1' || content.includes(playerProfiles?.c1_name)) {
              updated.child1_perspective = content;
              console.log("→ Set as Child 1 perspective");
            } else if (data.metadata?.child === 'c2' || content.includes(playerProfiles?.c2_name)) {
              updated.child2_perspective = content;
              console.log("→ Set as Child 2 perspective");
            } else {
              // Narration/shared text
              updated.narration = content;
              console.log("→ Set as Narration");
            }
          } else if (data.media_type === 'image') {
            console.log("🖼️ RAW Image data:", data);
            console.log("🖼️ Image URL:", data.content);
            console.log("🖼️ Current assets before update:", prev);
            updated.image = data.content;
            console.log("🖼️ Updated assets after:", updated);
          } else if (data.media_type === 'interactive') {
            updated.choices = typeof data.content === 'string' 
              ? data.content.split('\n').filter(c => c.trim())
              : data.content;
            console.log("🎮 Choices:", updated.choices);
          }
          
          console.log("📦 Updated assets:", updated);
          return updated;
        });
        
        setAssetsReceived(prev => prev + 1);
        
      } else if (data.type === 'STORY_COMPLETE') {
        console.log("✅ STORY_COMPLETE received!");
        
        // Use setTimeout to ensure all state updates have processed
        setTimeout(() => {
          setCurrentAssets(current => {
            console.log("🎬 Building storyBeat from:", current);
            
            const newBeat = {
              narration: current.narration || "The adventure begins...",
              child1_perspective: current.child1_perspective || `${playerProfiles?.c1_name} sees something magical...`,
              child2_perspective: current.child2_perspective || `${playerProfiles?.c2_name} feels excited...`,
              scene_image_url: current.image,
              choices: current.choices.length > 0 ? current.choices : ["Continue the adventure"]
            };
            
            console.log("🎬 Setting storyBeat:", newBeat);
            setStoryBeat(newBeat);
            
            // Speak the narration
            if ('speechSynthesis' in window && newBeat.narration) {
              const utterance = new SpeechSynthesisUtterance(newBeat.narration);
              utterance.lang = selectedLanguage === 'es' ? 'es-MX' : (selectedLanguage === 'hi' ? 'hi-IN' : 'en-US');
              window.speechSynthesis.speak(utterance);
              utterance.onend = () => playBeep(440, 0.4);
            }
            
            // Reset for next beat
            return {
              narration: '',
              child1_perspective: '',
              child2_perspective: '',
              image: null,
              choices: []
            };
          });
          
          setAssetsReceived(0);
        }, 100); // Small delay to ensure all state updates processed
      }
      
      // ...rest of handlers (STATUS, MECHANIC_WARNING, etc.)
    };

    // Connection closed
    ws.current.onclose = (event) => {
      console.log('❌ Disconnected, code:', event.code);
      setIsConnected(false);
      
      // Auto-reconnect if unexpected disconnect during story
      if (event.code === 1006 && setupStep === 2 && profiles) {
        console.log('⏳ Retrying in 3 seconds...');
        setTimeout(() => connectToAI(lang, profiles), 3000);
      }
    };

    // Connection error
    ws.current.onerror = (err) => {
      console.error('❌ WebSocket Error:', err);
    };
  };

  // ===========================================
  // LIFECYCLE & CLEANUP
  // ===========================================
  
  // Cleanup WebSocket on unmount
  useEffect(() => {
    return () => {
      if (ws.current) {
        ws.current.onclose = null;
        ws.current.close();
      }
    };
  }, []);

  // ===========================================
  // EVENT HANDLERS
  // ===========================================
  
  /**
   * Handles language selection
   * @param {string} lang - Language code (en, es, hi)
   */
  const handleLanguageSelect = (lang) => {
    setSelectedLanguage(lang);
    setSetupStep(1); // Move to character setup
    showFeedback('success', `${lang.toUpperCase()} selected!`, 1500);
    playBeep(1000, 0.2);
  };

  /**
   * Handles completion of character setup
   * @param {object} profiles - Character profiles from CharacterSetup component
   */
  const handleSetupComplete = (profiles) => {
    console.log("📋 Received profiles from CharacterSetup:", profiles);
    
    // MAP spirit animals to personality traits
    const spiritToPersonality = {
      'dragon': 'brave',
      'unicorn': 'creative',
      'owl': 'wise',
      'dolphin': 'friendly',
      'phoenix': 'resilient',
      'tiger': 'confident'
    };
    
    // Ensure all required fields have defaults
    const enrichedProfiles = {
      c1_name: profiles.c1_name || "Child 1",
      c1_gender: profiles.c1_gender || "girl",
      c1_personality: spiritToPersonality[profiles.c1_spirit_animal?.toLowerCase()] || 'brave',  // ← FIX
      c1_spirit_animal: profiles.c1_spirit_animal || 'Dragon',
      c1_toy_name: profiles.c1_toy_name || 'Bruno',
      c2_name: profiles.c2_name || "Child 2",
      c2_gender: profiles.c2_gender || "boy",
      c2_personality: spiritToPersonality[profiles.c2_spirit_animal?.toLowerCase()] || 'wise',   // ← FIX
      c2_spirit_animal: profiles.c2_spirit_animal || 'Owl',
      c2_toy_name: profiles.c2_toy_name || 'Book'
    };

    console.log("🔌 Enriched profiles:", enrichedProfiles);
    
    setPlayerProfiles(enrichedProfiles);
    setSetupStep(2); // Move to story mode
    connectToAI(selectedLanguage, enrichedProfiles); // Connect WebSocket
  };

  /**
   * Handles saving session and exiting
   */
  const handleSaveAndExit = async () => {
    setIsSaving(true);
    try {
      // Save session to backend
      await fetch('http://localhost:8000/api/session/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          profiles: playerProfiles,
          last_beat: storyBeat,
          language: selectedLanguage
        })
      });
    } catch (err) {
      console.error("Failed to save session:", err);
    } finally {
      setIsSaving(false);
      if (ws.current) ws.current.close();
      setShowExitModal(false);
      setSetupStep(3); // Move to end screen
    }
  };

  /**
   * Handles exiting without saving
   */
  const handleExitWithoutSaving = () => {
    if (ws.current) ws.current.close();
    setShowExitModal(false);
    setSetupStep(3); // Move to end screen
  };

  /**
   * Handles privacy acceptance
   */
  const handlePrivacyAccept = () => {
    setPrivacyAccepted(true);
    setShowPrivacyModal(false);
    playBeep(1200, 0.2);
  };

  // ===========================================
  // RENDER
  // ===========================================
  
  return (
    <div className="app-container" style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '100vh',
      padding: '20px'
    }}>
      {/* MAIN TITLE */}
      <h1 className="glow-text" style={{
        fontFamily: 'var(--font-heading)',
        fontSize: '4rem',
        fontWeight: 900,
        marginBottom: '40px',
        textAlign: 'center',
        textShadow: '0 2px 10px rgba(139, 92, 246, 0.4), 0 4px 20px rgba(236, 72, 153, 0.3)',
        letterSpacing: '2px',
        color: '#ffffff'
      }}>
        TwinSpark Chronicles
      </h1>

      {/* ===========================================
          STEP 0: PRIVACY MODAL (PARENT CONSENT)
          =========================================== */}
      {showPrivacyModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          width: '100vw',
          height: '100vh',
          background: 'rgba(0, 0, 0, 0.9)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 9999,
          animation: 'fadeIn 0.3s ease'
        }}>
          <div style={{
            background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.2), rgba(236, 72, 153, 0.2))',
            border: '2px solid rgba(239, 68, 68, 0.6)',
            borderRadius: '20px',
            padding: '40px',
            maxWidth: '600px',
            textAlign: 'center',
            boxShadow: '0 0 50px rgba(239, 68, 68, 0.5)',
            animation: 'slideDown 0.5s ease'
          }}>
            <h2 style={{ fontSize: '2rem', color: '#fff', marginBottom: '20px' }}>
              🛡️ Parent's Safety Gate
            </h2>
            <div style={{
              textAlign: 'left',
              color: 'rgba(255,255,255,0.9)',
              lineHeight: '1.8',
              marginBottom: '30px'
            }}>
              <p style={{ marginBottom: '15px' }}>
                <strong>This magical experience uses:</strong>
              </p>
              <ul style={{ paddingLeft: '25px' }}>
                <li>📸 <strong>Camera:</strong> Local gesture detection (nothing recorded)</li>
                <li>🎙️ <strong>Microphone:</strong> Voice commands (not stored)</li>
                <li>✨ <strong>AI:</strong> To generate avatars and personalized stories</li>
              </ul>
              <p style={{ marginTop: '15px', fontSize: '0.9rem', opacity: 0.8 }}>
                No data is stored on our servers. All processing is local or through secure APIs.
              </p>
            </div>
            <button
              onClick={handlePrivacyAccept}
              className="btn-magic"
              style={{
                background: 'linear-gradient(135deg, #22c55e, #16a34a)',
                padding: '15px 40px',
                fontSize: '1.2rem',
                fontWeight: 'bold',
                border: '2px solid #22c55e',
                boxShadow: '0 0 20px rgba(34, 197, 94, 0.5)'
              }}
            >
              ✓ I Understand & Agree
            </button>
          </div>
        </div>
      )}

      {/* ===========================================
          STEP 1: LANGUAGE SELECTION
          =========================================== */}
      {setupStep === 0 && privacyAccepted && (
        <div className="glass-panel" style={{
          padding: '50px',
          textAlign: 'center',
          maxWidth: '500px',
          width: '100%',
          margin: '0 auto',
          animation: 'float 6s ease-in-out infinite'
        }}>
          <p style={{
            fontSize: '1.5rem',
            color: 'rgba(255,255,255,0.9)',
            marginBottom: '30px',
            fontFamily: 'var(--font-body)'
          }}>
            Choose your language to begin:
          </p>
          <div style={{ 
            display: 'flex', 
            flexDirection: 'column', 
            gap: '20px',
            alignItems: 'center'
          }}>
            {/* English Button */}
            <button
              className="lang-button btn-magic"
              onClick={() => handleLanguageSelect('en')}
              style={{
                background: 'linear-gradient(135deg, #a855f7 0%, #ec4899 100%)',
                fontSize: '1.5rem',
                padding: '20px',
                width: '100%'
              }}
            >
              🇺🇸 English 🇬🇧
            </button>
            
            {/* Spanish Button */}
            <button
              className="lang-button btn-magic"
              onClick={() => handleLanguageSelect('es')}
              style={{
                background: 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)',
                fontSize: '1.5rem',
                padding: '20px',
                width: '100%'
              }}
            >
              🇲🇽 Español 🇪🇸
            </button>
            
            {/* Hindi Button */}
            <button
              className="lang-button btn-magic"
              onClick={() => handleLanguageSelect('hi')}
              style={{
                background: 'linear-gradient(135deg, #f59e0b 0%, #ef4444 100%)',
                fontSize: '1.5rem',
                padding: '20px',
                width: '100%'
              }}
            >
              🇮🇳 हिंदी 🪷
            </button>
          </div>
        </div>
      )}

      {/* ===========================================
          STEP 2: CHARACTER SETUP
          =========================================== */}
      {setupStep === 1 && (
        <CharacterSetup t={t} onComplete={handleSetupComplete} />
      )}

      {/* ===========================================
          STEP 3: STORY EXPERIENCE
          =========================================== */}
      {setupStep === 2 && (
        <React.Fragment>
          {/* View Mode Toggle Buttons */}
          <div style={{ 
            display: 'flex', 
            gap: '15px', 
            marginBottom: '30px'
          }}>
            {/* Full Story View Button */}
            <button
              onClick={() => setVoiceOnlyMode(false)}
              className="btn-magic"
              style={{
                background: !voiceOnlyMode 
                  ? 'linear-gradient(135deg, var(--color-accent-pink) 0%, var(--color-accent-purple) 100%)'
                  : 'rgba(255,255,255,0.1)',
                padding: '12px 30px',
                display: 'flex',
                alignItems: 'center',
                gap: '10px'
              }}
            >
              <Eye size={24} />
              <span>Full Story</span>
            </button>
            
            {/* Voice Only Mode Button */}
            <button
              onClick={() => setVoiceOnlyMode(true)}
              className="btn-magic"
              style={{
                background: voiceOnlyMode 
                  ? 'linear-gradient(135deg, var(--color-accent-pink) 0%, var(--color-accent-purple) 100%)'
                  : 'rgba(255,255,255,0.1)',
                padding: '12px 30px',
                display: 'flex',
                alignItems: 'center',
                gap: '10px'
              }}
            >
              <Mic size={24} />
              <span>Voice Only</span>
            </button>
          </div>

          {/* Connection Status */}
          <p style={{
            fontSize: '1.2rem',
            color: isConnected ? '#8b5cf6' : 'rgba(255,255,255,0.7)',
            marginBottom: '30px'
          }}>
            {isConnected ? t.connected : t.connecting}
          </p>

          {/* Conditional Rendering: Voice Only vs Full Story */}
          {voiceOnlyMode ? (
            // VOICE ONLY MODE - Minimal UI, audio-first
            <VoiceOnlyMode
              onVoiceInput={() => setIsListening(!isListening)}
              isListening={isListening}
              currentStory={storyBeat ? storyBeat.child1_perspective : null}
              childName={playerProfiles?.c1_name}
              t={t}
            />
          ) : (
            // FULL STORY MODE - Visual + Audio
            <>
              {/* Story Display */}
              {storyBeat ? (
                <DualStoryDisplay 
                  storyBeat={storyBeat} 
                  t={t} 
                  profiles={playerProfiles} 
                />
              ) : (
                <div className="glass-panel" style={{ padding: '40px', textAlign: 'center' }}>
                  <LoadingAnimation 
                    type="story" 
                    message={t.waiting || "Waiting for the story to begin..."} 
                  />
                </div>
              )}

              {/* Game Mechanics Prompt */}
              {mechanics && storyBeat && (
                <div className="glass-panel" style={{
                  padding: '25px 50px',
                  marginTop: '20px',
                  textAlign: 'center'
                }}>
                  <h3 style={{ fontSize: '1.8rem', color: '#fff' }}>
                    {mechanics.prompt}
                  </h3>
                </div>
              )}

              {/* Multimodal Controls (Voice, Gesture, etc.) */}
              <div style={{ marginTop: 'auto', paddingTop: '40px' }}>
                <MultimodalControls 
                  isListening={isListening} 
                  hasCamera={hasCamera} 
                  t={t} 
                />
              </div>

              {/* Magic Mirror (Emotion Detection) */}
              <MagicMirror />
            </>
          )}
        </React.Fragment>
      )}

      {/* ===========================================
          STEP 4: END SCREEN
          =========================================== */}
      {setupStep === 3 && (
        <div style={{ textAlign: 'center', marginTop: '100px' }}>
          <h1 style={{ color: 'white', fontSize: '3rem' }}>
            Thanks for playing!
          </h1>
        </div>
      )}

      {/* ===========================================
          GLOBAL MODALS & OVERLAYS
          =========================================== */}
      
      {/* Alert Modal for warnings/errors */}
      <AlertModal 
        message={alertMessage} 
        onClose={() => setAlertMessage(null)} 
      />
      
      {/* Visual Feedback Component (toasts, animations) */}
      {FeedbackComponent}
      
      {/* Exit Modal for saving progress */}
      {showExitModal && (
        <ExitModal
          onSave={handleSaveAndExit}
          onExit={handleExitWithoutSaving}
          onClose={() => setShowExitModal(false)}
          isSaving={isSaving}
        />
      )}
    </div>
  );
}

export default App;