import React from 'react';
import Timer from './Timer';

const SpeakerCard = ({ activeSpeaker, timerDuration = 60, onEndTurn, onMute, isModerator = false }) => {
  if (!activeSpeaker) {
    return (
      <div className="glass-card" style={{ padding: '2rem', textAlign: 'center' }}>
        <span style={{ fontSize: '3rem', display: 'block', marginBottom: '0.5rem', opacity: 0.5 }}>🎙️</span>
        <h3 style={{ fontSize: '1.2rem', color: 'var(--text-muted)' }}>No Active Speaker</h3>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-dim)', marginTop: '0.25rem' }}>
          Moderator can approve the next student from queue to activate stage microphone.
        </p>
      </div>
    );
  }

  return (
    <div className="glass-card mic-live-pulse" style={{ padding: '1.75rem', border: '1px solid var(--accent-success)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <span className="status-pill active" style={{ marginBottom: '0.5rem' }}>
            🔴 LIVE SPEAKER
          </span>
          <h2 style={{ fontSize: '1.6rem', fontWeight: '800', marginTop: '0.3rem' }}>
            🎤 {activeSpeaker.name}
          </h2>
          <span className={`role-badge ${activeSpeaker.role}`} style={{ marginTop: '0.4rem' }}>
            {activeSpeaker.role}
          </span>
        </div>

        <Timer initialSeconds={timerDuration} onExpire={onEndTurn} />
      </div>

      {/* Audio Waveform Animation */}
      <div className="waveform-container">
        <div className="wave-bar"></div>
        <div className="wave-bar"></div>
        <div className="wave-bar"></div>
        <div className="wave-bar"></div>
        <div className="wave-bar"></div>
      </div>

      {isModerator && (
        <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1rem' }}>
          <button onClick={onMute} className="btn btn-secondary" style={{ flex: 1 }}>
            🔇 Mute Microphone
          </button>
          <button onClick={onEndTurn} className="btn btn-danger" style={{ flex: 1 }}>
            ⏹️ End Speaker Turn
          </button>
        </div>
      )}
    </div>
  );
};

export default SpeakerCard;
