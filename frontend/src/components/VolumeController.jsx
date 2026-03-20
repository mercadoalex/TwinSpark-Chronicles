import React from 'react';
import { useSceneAudioStore } from '../stores/sceneAudioStore';
import './VolumeController.css';

export default function VolumeController() {
  const ambientVolume = useSceneAudioStore((s) => s.ambientVolume);
  const sfxVolume = useSceneAudioStore((s) => s.sfxVolume);
  const isMuted = useSceneAudioStore((s) => s.isMuted);
  const setAmbientVolume = useSceneAudioStore((s) => s.setAmbientVolume);
  const setSfxVolume = useSceneAudioStore((s) => s.setSfxVolume);
  const toggleMute = useSceneAudioStore((s) => s.toggleMute);

  return (
    <div className="volume-controller">
      <div className="volume-controller__slider-group">
        <label className="volume-controller__label" htmlFor="ambient-volume">
          🌲 Ambient
        </label>
        <input
          id="ambient-volume"
          type="range"
          className="volume-controller__slider"
          min={0}
          max={100}
          step={5}
          value={isMuted ? 0 : ambientVolume}
          onChange={(e) => setAmbientVolume(Number(e.target.value))}
          aria-label="Ambient audio volume"
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuenow={isMuted ? 0 : ambientVolume}
          disabled={isMuted}
        />
        <span className="volume-controller__value">{isMuted ? 0 : ambientVolume}%</span>
      </div>

      <div className="volume-controller__slider-group">
        <label className="volume-controller__label" htmlFor="sfx-volume">
          ✨ Effects
        </label>
        <input
          id="sfx-volume"
          type="range"
          className="volume-controller__slider"
          min={0}
          max={100}
          step={5}
          value={isMuted ? 0 : sfxVolume}
          onChange={(e) => setSfxVolume(Number(e.target.value))}
          aria-label="Sound effects volume"
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuenow={isMuted ? 0 : sfxVolume}
          disabled={isMuted}
        />
        <span className="volume-controller__value">{isMuted ? 0 : sfxVolume}%</span>
      </div>

      <button
        className={`volume-controller__mute ${isMuted ? 'volume-controller__mute--active' : ''}`}
        onClick={toggleMute}
        aria-pressed={isMuted}
        aria-label="Mute all scene audio"
      >
        {isMuted ? '🔇' : '🔊'} {isMuted ? 'Unmute' : 'Mute'}
      </button>
    </div>
  );
}
