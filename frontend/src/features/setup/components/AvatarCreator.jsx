import React, { useState, useRef, useCallback, useEffect } from 'react';
import './AvatarCreator.css';

/**
 * Voice-guided avatar creation for kids.
 *
 * Guides each child through 4 short voice questions to build their avatar
 * description. Uses Web Speech API TTS to speak each question aloud.
 * Provides a big pulsing mic button (primary) and a text input fallback.
 *
 * Props:
 * @param {string} props.childName — the child's name
 * @param {string} props.language — 'en' or 'es'
 * @param {(result: { description: string, answers: { size: string, color: string, feature: string, special: string } }) => void} props.onComplete
 */

/** TTS rate tuned for child comprehension */
const TTS_RATE = 0.9;

/** Silence duration before auto-stop recording (ms) */
const SILENCE_DURATION_MS = 1500;
const SILENCE_THRESHOLD = 0.01;

/** Step emojis */
const STEP_EMOJIS = ['📏', '🎨', '🦋', '⭐'];

/** Step keys */
const STEP_KEYS = ['size', 'color', 'feature', 'special'];

/** Translations */
const TEXTS = {
  en: {
    questions: [
      (name) => `Hey ${name}! Let's create YOUR character! Is your creature big, tiny, or medium?`,
      (_, answers) => `A ${answers.size} creature! What color is it?`,
      (_, answers) => `Ooh, ${answers.color}! Does it have wings, a long tail, horns, or something else cool?`,
      () => `Almost done! What's something funny or special about it?`,
    ],
    summary: (answers) =>
      `Amazing! Your character is: A ${answers.size} ${answers.color} creature with ${answers.feature} that ${answers.special}!`,
    confirmBtn: "That's me! ✨",
    micLabel: 'Tap to speak',
    micRecording: 'Listening...',
    fallbackLabel: 'or type here',
    fallbackPlaceholder: 'Type your answer...',
    fallbackSubmit: 'OK ✓',
  },
  es: {
    questions: [
      (name) => `¡Hola ${name}! ¡Vamos a crear TU personaje! ¿Tu criatura es grande, pequeña o mediana?`,
      (_, answers) => `¡Una criatura ${answers.size}! ¿De qué color es?`,
      (_, answers) => `¡Ooh, ${answers.color}! ¿Tiene alas, una cola larga, cuernos, o algo más genial?`,
      () => `¡Casi listo! ¿Qué tiene de gracioso o especial?`,
    ],
    summary: (answers) =>
      `¡Increíble! Tu personaje es: Una criatura ${answers.size} ${answers.color} con ${answers.feature} que ${answers.special}!`,
    confirmBtn: '¡Ese soy yo! ✨',
    micLabel: 'Toca para hablar',
    micRecording: 'Escuchando...',
    fallbackLabel: 'o escribe aquí',
    fallbackPlaceholder: 'Escribe tu respuesta...',
    fallbackSubmit: 'OK ✓',
  },
};

/**
 * Speak text using Web Speech API TTS.
 */
function speakText(text, lang = 'en') {
  if (!window.speechSynthesis) return;
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.rate = TTS_RATE;
  utterance.pitch = 1.2;
  utterance.volume = 0.9;
  utterance.lang = lang === 'es' ? 'es-ES' : 'en-US';
  window.speechSynthesis.speak(utterance);
}

function AvatarCreator({ childName, language = 'en', onComplete }) {
  const [currentStep, setCurrentStep] = useState(0); // 0-3 = questions, 4 = summary
  const [answers, setAnswers] = useState({ size: '', color: '', feature: '', special: '' });
  const [textValue, setTextValue] = useState('');
  const [isRecording, setIsRecording] = useState(false);

  // Audio refs for mic recording
  const mediaStreamRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const animationFrameRef = useRef(null);
  const silenceTimerRef = useRef(null);
  const hasSpeechRef = useRef(false);
  const spokenRef = useRef(-1);

  const txt = TEXTS[language] || TEXTS.en;

  // Speak the current question when step changes
  useEffect(() => {
    if (currentStep < 4 && currentStep !== spokenRef.current) {
      spokenRef.current = currentStep;
      const questionFn = txt.questions[currentStep];
      const questionText = questionFn(childName, answers);
      // Small delay so the card animation plays first
      const timer = setTimeout(() => speakText(questionText, language), 300);
      return () => clearTimeout(timer);
    }
    if (currentStep === 4 && spokenRef.current !== 4) {
      spokenRef.current = 4;
      const summaryText = txt.summary(answers);
      const timer = setTimeout(() => speakText(summaryText, language), 300);
      return () => clearTimeout(timer);
    }
  }, [currentStep, childName, language, txt, answers]);

  // Cleanup audio on unmount
  useEffect(() => {
    return () => {
      stopAllAudio();
      if (window.speechSynthesis) window.speechSynthesis.cancel();
    };
  }, []);

  /**
   * Stop all audio resources.
   */
  const stopAllAudio = useCallback(() => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }
    if (silenceTimerRef.current) {
      clearTimeout(silenceTimerRef.current);
      silenceTimerRef.current = null;
    }
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach((track) => track.stop());
      mediaStreamRef.current = null;
    }
    if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }
  }, []);

  /**
   * Advance to next step with the given answer.
   */
  const advanceWithAnswer = useCallback(
    (answer) => {
      const key = STEP_KEYS[currentStep];
      const newAnswers = { ...answers, [key]: answer };
      setAnswers(newAnswers);
      setTextValue('');
      setCurrentStep((s) => s + 1);
    },
    [currentStep, answers]
  );

  /**
   * Monitor audio for silence detection (auto-stop after 1.5s silence).
   */
  const monitorAudio = useCallback(() => {
    const analyser = analyserRef.current;
    if (!analyser) return;

    const dataArray = new Uint8Array(analyser.fftSize);

    const tick = () => {
      if (!analyserRef.current) return;
      analyser.getByteTimeDomainData(dataArray);

      let sum = 0;
      for (let i = 0; i < dataArray.length; i++) {
        const normalized = (dataArray[i] - 128) / 128;
        sum += normalized * normalized;
      }
      const rms = Math.sqrt(sum / dataArray.length);

      if (rms < SILENCE_THRESHOLD) {
        if (!silenceTimerRef.current && hasSpeechRef.current) {
          silenceTimerRef.current = setTimeout(() => {
            finishRecording();
          }, SILENCE_DURATION_MS);
        }
      } else {
        hasSpeechRef.current = true;
        if (silenceTimerRef.current) {
          clearTimeout(silenceTimerRef.current);
          silenceTimerRef.current = null;
        }
      }

      animationFrameRef.current = requestAnimationFrame(tick);
    };

    animationFrameRef.current = requestAnimationFrame(tick);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  /**
   * Start recording from mic.
   */
  const startRecording = useCallback(async () => {
    if (isRecording) return;

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaStreamRef.current = stream;

      const audioContext = new (window.AudioContext || window.webkitAudioContext)();
      audioContextRef.current = audioContext;
      const source = audioContext.createMediaStreamSource(stream);
      const analyser = audioContext.createAnalyser();
      analyser.fftSize = 256;
      source.connect(analyser);
      analyserRef.current = analyser;

      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      hasSpeechRef.current = false;

      mediaRecorder.start();
      setIsRecording(true);
      monitorAudio();
    } catch {
      // If mic not available, user can use text fallback
      setIsRecording(false);
    }
  }, [isRecording, monitorAudio]);

  /**
   * Finish recording — stop and cleanup.
   * Since we don't have real STT yet, this just stops the recording state.
   * The user will use the text fallback to actually submit their answer.
   */
  const finishRecording = useCallback(() => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }
    if (silenceTimerRef.current) {
      clearTimeout(silenceTimerRef.current);
      silenceTimerRef.current = null;
    }
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach((track) => track.stop());
      mediaStreamRef.current = null;
    }
    if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }
    setIsRecording(false);
    // When real STT is wired, we'd call advanceWithAnswer(transcript) here
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  /**
   * Handle mic button tap.
   */
  const handleMicTap = useCallback(() => {
    if (isRecording) {
      hasSpeechRef.current = true;
      finishRecording();
    } else {
      startRecording();
    }
  }, [isRecording, startRecording, finishRecording]);

  /**
   * Handle text fallback submission.
   */
  const handleTextSubmit = useCallback(
    (e) => {
      e.preventDefault();
      if (textValue.trim()) {
        advanceWithAnswer(textValue.trim());
      }
    },
    [textValue, advanceWithAnswer]
  );

  /**
   * Handle confirm button on summary screen.
   */
  const handleConfirm = useCallback(() => {
    const description = `A ${answers.size} ${answers.color} creature with ${answers.feature} that ${answers.special}`;
    if (onComplete) {
      onComplete({ description, answers });
    }
  }, [answers, onComplete]);

  // ─── Summary Screen ───────────────────────────────
  if (currentStep === 4) {
    return (
      <div className="avatar-creator" aria-label="Avatar creation complete">
        <div className="avatar-creator__summary">
          <span className="avatar-creator__summary-emoji" aria-hidden="true">
            🎭
          </span>
          <p className="avatar-creator__summary-text">{txt.summary(answers)}</p>
          <button
            className="avatar-creator__confirm-btn"
            onClick={handleConfirm}
            aria-label={txt.confirmBtn}
          >
            {txt.confirmBtn}
          </button>
        </div>

        {/* Progress dots */}
        <div className="avatar-creator__progress" aria-hidden="true">
          {STEP_KEYS.map((_, i) => (
            <span key={i} className="avatar-creator__dot avatar-creator__dot--done" />
          ))}
        </div>
      </div>
    );
  }

  // ─── Question Screen ──────────────────────────────
  const questionFn = txt.questions[currentStep];
  const questionText = questionFn(childName, answers);

  return (
    <div className="avatar-creator" aria-label="Avatar creation">
      <div className="avatar-creator__card" key={currentStep}>
        {/* Animated emoji for this step */}
        <span className="avatar-creator__emoji" aria-hidden="true">
          {STEP_EMOJIS[currentStep]}
        </span>

        {/* Question text */}
        <p className="avatar-creator__question">{questionText}</p>

        {/* Input area: mic + text fallback */}
        <div className="avatar-creator__input-area">
          {/* Big mic button */}
          <button
            className={`avatar-creator__mic-btn ${isRecording ? 'avatar-creator__mic-btn--recording' : ''}`}
            onClick={handleMicTap}
            aria-label={isRecording ? txt.micRecording : txt.micLabel}
          >
            <span aria-hidden="true">{isRecording ? '🔴' : '🎤'}</span>
          </button>
          <span className="avatar-creator__mic-label">
            {isRecording ? txt.micRecording : txt.micLabel}
          </span>

          {/* Text fallback */}
          <form className="avatar-creator__fallback" onSubmit={handleTextSubmit}>
            <span className="avatar-creator__fallback-label">{txt.fallbackLabel}</span>
            <input
              className="avatar-creator__text-input"
              type="text"
              value={textValue}
              onChange={(e) => setTextValue(e.target.value)}
              placeholder={txt.fallbackPlaceholder}
              autoComplete="off"
              maxLength={40}
            />
            <button
              className="avatar-creator__text-submit"
              type="submit"
              disabled={!textValue.trim()}
            >
              {txt.fallbackSubmit}
            </button>
          </form>
        </div>
      </div>

      {/* Progress dots */}
      <div className="avatar-creator__progress" aria-hidden="true">
        {STEP_KEYS.map((_, i) => (
          <span
            key={i}
            className={`avatar-creator__dot ${
              i === currentStep
                ? 'avatar-creator__dot--active'
                : i < currentStep
                  ? 'avatar-creator__dot--done'
                  : ''
            }`}
          />
        ))}
      </div>
    </div>
  );
}

export default AvatarCreator;
