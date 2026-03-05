import React, { useState, useEffect, useRef } from 'react';
import DualStoryDisplay from './components/DualStoryDisplay';
import MultimodalControls from './components/MultimodalControls';
import AlertModal from './components/AlertModal';
import CharacterSetup from './components/CharacterSetup';
import ExitModal from './components/ExitModal';
import VoiceOnlyMode from './components/VoiceOnlyMode';
import LoadingAnimation from './components/LoadingAnimation';
import { useFeedback } from './components/VisualFeedback';
import { Mic, Eye, Menu } from 'lucide-react';
import { translations } from './locales';
import './App.css';

function App() {
  const [isListening, setIsListening] = useState(true);
  const [hasCamera, setHasCamera] = useState(true);
  const [isConnected, setIsConnected] = useState(false);
  const [selectedLanguage, setSelectedLanguage] = useState(null);
  const [voiceOnlyMode, setVoiceOnlyMode] = useState(false);
  const [storyBeat, setStoryBeat] = useState(null);
  const [mechanics, setMechanics] = useState(null);

  // 0: Language Selection, 1: Character Setup, 2: Main Story Flow, 3: Goodbye
  const [setupStep, setSetupStep] = useState(0);
  const [playerProfiles, setPlayerProfiles] = useState(null);

  // Exit Flow State
  const [showExitModal, setShowExitModal] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  const [alertMessage, setAlertMessage] = useState(null);
  const ws = useRef(null);
  
  // Use the feedback hook
  const { showFeedback, FeedbackComponent } = useFeedback();

  const t = selectedLanguage ? translations[selectedLanguage] : translations.en;

  // Connection logic is now triggered dynamically AFTER profile setup
  const connectToAI = (lang, profiles) => {
    if (ws.current?.readyState === WebSocket.OPEN) return;

    console.log(`Attempting connection to TwinSpark AI in language: ${lang}...`);

    // Build connection URL with dynamic players!
    const params = new URLSearchParams({
      lang: lang,
      c1_name: profiles.c1_name,
      c1_gender: profiles.c1_gender,
      c2_name: profiles.c2_name,
      c2_gender: profiles.c2_gender
    });

    ws.current = new WebSocket(`ws://localhost:8000/ws/session?${params.toString()}`);

    ws.current.onopen = () => {
      console.log('✅ Connected to TwinSpark AI Engine');
      setIsConnected(true);
    };

    ws.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log("WebSocket Message:", data);

      if (data.type === 'STORY_UPDATE') {
        const newBeat = data.data.beats[0];
        setStoryBeat(newBeat);
        setMechanics(data.mechanics);
      } else if (data.type === 'MECHANIC_WARNING') {
        setAlertMessage(data.message);
      }
    };

    ws.current.onclose = () => {
      console.log('❌ Disconnected from TwinSpark AI Engine');
      setIsConnected(false);
      // Try to reconnect only if we're in the story phase
      setTimeout(() => {
        if (setupStep === 2 && playerProfiles) {
          connectToAI(selectedLanguage, playerProfiles);
        }
      }, 2000);
    };

    ws.current.onerror = (err) => {
      console.error('WebSocket Error:', err);
      ws.current.close();
    };
  };

  useEffect(() => {
    return () => {
      if (ws.current) {
        ws.current.onclose = null;
        ws.current.close();
      }
    };
  }, []);

  const handleLanguageSelect = (lang) => {
    setSelectedLanguage(lang);
    setSetupStep(1); // Move to Character Setup
    showFeedback('success', `${lang.toUpperCase()} selected!`, 1500);
  };

  const handleSetupComplete = (profiles) => {
    setPlayerProfiles(profiles);
    setSetupStep(2); // Move to Main Story Flow
    connectToAI(selectedLanguage, profiles);
  };

  const handleSaveAndExit = async () => {
    setIsSaving(true);
    try {
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
      setSetupStep(3); // Go to Goodbye Screen
    }
  };

  const handleExitWithoutSaving = () => {
    if (ws.current) ws.current.close();
    setShowExitModal(false);
    setSetupStep(3);
  };

  // Simulate pushing the "push-to-talk" button for prototyping
  const handleSimulatedVoiceCommand = (childId, command) => {
    if (ws.current && isConnected) {
      ws.current.send(JSON.stringify({
        action: command,
        user_id: childId
      }));
    }
  };

  return (
    <div className="app-container" style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      padding: '40px 20px',
      minHeight: '100vh',
    }}>

      {/* Magical Header */}
      <h1 className="glow-text" style={{
        fontFamily: 'var(--font-heading)',
        fontSize: '4rem',
        fontWeight: 900,
        marginBottom: '10px',
        textAlign: 'center',
        paddingTop: '20px'
      }}>
        TwinSpark Chronicles
      </h1>

      {setupStep === 0 && (
        // Language Selection Screen
        <div className="glass-panel" style={{
          padding: '50px',
          textAlign: 'center',
          maxWidth: '600px',
          marginTop: '60px',
          animation: 'float 6s ease-in-out infinite'
        }}>
          <h2 style={{ fontSize: '2.5rem', marginBottom: '10px', color: '#fff' }}>
            Ready for Magic? ✨
          </h2>
          <p style={{ fontSize: '1.2rem', color: 'rgba(255,255,255,0.8)', marginBottom: '40px' }}>
            Choose your language to begin the adventure!
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <button
              className="lang-button btn-magic"
              onClick={() => handleLanguageSelect('en')}
              style={{
                background: 'linear-gradient(135deg, #a855f7 0%, #ec4899 100%)',
                width: '100%'
              }}
            >
              🇺🇸 English 🇬🇧
            </button>
            <button
              className="lang-button btn-magic"
              onClick={() => handleLanguageSelect('es')}
              style={{
                background: 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)',
                width: '100%'
              }}
            >
              🇲🇽 Español 🇪🇸
            </button>
            <button
              className="lang-button btn-magic"
              onClick={() => handleLanguageSelect('hi')}
              style={{
                background: 'linear-gradient(135deg, #f59e0b 0%, #ef4444 100%)',
                width: '100%'
              }}
            >
              🇮🇳 हिंदी 🪷
            </button>
          </div>
        </div>
      )}

      {setupStep === 1 && (
        // Registration Screen
        <CharacterSetup t={t} onComplete={handleSetupComplete} />
      )}

      {setupStep === 2 && (
        <React.Fragment>
          {/* Mode Toggle Buttons */}
          <div style={{ 
            display: 'flex', 
            gap: '15px', 
            marginBottom: '30px',
            animation: 'slideUp 0.5s ease-out'
          }}>
            <button
              onClick={() => setVoiceOnlyMode(false)}
              className="btn-magic"
              style={{
                background: !voiceOnlyMode 
                  ? 'linear-gradient(135deg, var(--color-accent-blue) 0%, var(--color-accent-purple) 100%)'
                  : 'rgba(255,255,255,0.1)',
                padding: '12px 30px',
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
                border: !voiceOnlyMode ? '2px solid var(--color-accent-blue)' : '2px solid transparent'
              }}
            >
              <Eye size={24} />
              <span>Full Story</span>
            </button>
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
                gap: '10px',
                border: voiceOnlyMode ? '2px solid var(--color-accent-pink)' : '2px solid transparent'
              }}
            >
              <Mic size={24} />
              <span>Voice Only</span>
            </button>
          </div>

          <p style={{
            fontSize: '1.2rem',
            color: isConnected ? '#8b5cf6' : 'rgba(255,255,255,0.7)',
            marginBottom: '30px',
            fontWeight: isConnected ? 'bold' : 'normal'
          }}>
            {isConnected ? t.connected : t.connecting}
          </p>

          {/* Voice-Only Mode */}
          {voiceOnlyMode ? (
            <VoiceOnlyMode
              onVoiceInput={() => {
                setIsListening(!isListening);
                showFeedback('sparkle', 'Great job!', 1500);
              }}
              isListening={isListening}
              currentStory={storyBeat ? storyBeat.child1_perspective : null}
              childName={playerProfiles?.c1_name}
              t={t}
            />
          ) : (
            <>
              {/* Main Content Area - Full Story Mode */}
              {storyBeat ? (
                <DualStoryDisplay storyBeat={storyBeat} t={t} profiles={playerProfiles} />
              ) : (
                <div className="glass-panel" style={{ padding: '40px', textAlign: 'center' }}>
                  <LoadingAnimation type="story" message={t.waiting || "Waiting for the story to begin..."} />
                </div>
              )}

              {/* Dynamic Interaction Prompt powered by AI Engine */}
              {mechanics && storyBeat && (
                <div className="glass-panel" style={{
                  padding: '25px 50px',
                  marginTop: '20px',
                  marginBottom: '40px',
                  textAlign: 'center',
                  background: mechanics.simultaneous_mode ? 'rgba(236, 72, 153, 0.2)' : 'rgba(255, 255, 255, 0.12)',
                  border: mechanics.simultaneous_mode ? '2px solid var(--color-accent-pink)' : '2px solid rgba(255, 255, 255, 0.3)',
                  boxShadow: mechanics.simultaneous_mode ? '0 0 20px rgba(236, 72, 153, 0.4)' : 'none',
                  transition: 'all 0.5s ease',
                  animation: 'bounce-in 0.5s ease-out'
                }}>
                  <h3 style={{
                    fontSize: '1.8rem',
                    fontFamily: 'var(--font-heading)',
                    color: '#fff',
                    marginBottom: '10px'
                  }}>
                    {mechanics.prompt}
                  </h3>
                  <p style={{
                    color: 'rgba(255,255,255,0.7)',
                    fontSize: '1rem',
                    marginTop: '10px'
                  }}>
                    {t.instruction}
                  </p>
                </div>
              )}

              {/* Controls stick to bottom gracefully */}
              <div style={{ marginTop: 'auto', paddingTop: '40px' }}>
                <MultimodalControls isListening={isListening} hasCamera={hasCamera} t={t} />
              </div>
            </>
          )}
        </React.Fragment>
      )}

      {/* GOODBYE SCREEN */}
      {setupStep === 3 && (
        <div style={{
          display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100vh', textAlign: 'center'
        }}>
          <div style={{ fontSize: '5rem', marginBottom: '20px' }}>🪄</div>
          <h1 style={{ color: 'white', fontFamily: 'var(--font-heading)', fontSize: '3rem' }}>Thanks for playing!</h1>
          <p style={{ color: 'rgba(255,255,255,0.8)', fontSize: '1.2rem', marginTop: '15px' }}>
            Your story has been safely paused in the TwinSpark realm.<br />It is now safe to close this window.
          </p>
        </div>
      )}

      {/* Custom Alert Modal for Mechanic Warnings */}
      <AlertModal message={alertMessage} onClose={() => setAlertMessage(null)} />

      {/* Visual Feedback Component */}
      {FeedbackComponent}

      {/* Exit Modal Flow */}
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
