import React, { useEffect, useRef, useState } from 'react';
import webrtcManager from '../services/webrtc';
import ConnectionStatus from './ConnectionStatus';

const AudioReceiver = ({ sessionId, activeSpeaker, socketConnected }) => {
  const audioRef = useRef(null);
  const [rtcStatus, setRtcStatus] = useState('listening');
  const [audioUnlocked, setAudioUnlocked] = useState(false);
  const [autoplayBlocked, setAutoplayBlocked] = useState(false);

  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.volume = 1.0;
      audioRef.current.muted = false;
      webrtcManager.setAudioElement(audioRef.current);
    }

    webrtcManager.onStateChange = (state) => {
      setRtcStatus(state);
    };

    webrtcManager.onAutoplayBlocked = () => {
      setAutoplayBlocked(true);
    };

    if (sessionId) {
      webrtcManager.initReceiver(sessionId);
    }
  }, [sessionId]);

  const handleEnableAudio = async () => {
    if (audioRef.current) {
      try {
        audioRef.current.muted = false;
        audioRef.current.volume = 1.0;
        await webrtcManager.unlockAudio();
        setAudioUnlocked(true);
        setAutoplayBlocked(false);
      } catch (e) {
        console.log('Audio unlocked:', e);
        setAudioUnlocked(true);
        setAutoplayBlocked(false);
      }
    }
  };

  return (
    <div className="glass-card" style={{ padding: '2.5rem', textAlign: 'center', border: '1px solid var(--accent-primary)' }}>
      {/* HTML Audio element with controls for browser compatibility */}
      <audio
        ref={audioRef}
        autoPlay
        playsInline
        style={{
          width: '100%',
          maxWidth: '320px',
          margin: '0.75rem auto 1.25rem auto',
          display: 'block'
        }}
        controls
      />

      <div style={{ marginBottom: '1.5rem', display: 'flex', justifyContent: 'center' }}>
        <ConnectionStatus socketStatus={socketConnected} rtcStatus={rtcStatus} micStatus={false} />
      </div>

      <div style={{ margin: '1rem 0 1.5rem 0' }}>
        <span style={{ fontSize: '3.5rem', display: 'block', marginBottom: '0.5rem' }}>
          🔊
        </span>
        <h2 style={{ fontSize: '1.8rem', fontWeight: '800' }}>
          AUDITORIUM RECEIVER ACTIVE
        </h2>
        <p style={{ color: 'var(--text-muted)', marginTop: '0.4rem', fontSize: '0.95rem' }}>
          Output: <strong>Auditorium Sound System / Venue Speakers</strong>
        </p>

        {/* Browser Audio Unlock Banner */}
        <div style={{ marginTop: '1.25rem' }}>
          {!audioUnlocked ? (
            <button
              onClick={handleEnableAudio}
              className="btn btn-primary"
              style={{ padding: '0.75rem 1.75rem', fontSize: '1rem', fontWeight: '700', borderRadius: '50px' }}
            >
              🔊 CLICK TO ACTIVATE SPEAKERS
            </button>
          ) : (
            <span className="status-pill active" style={{ fontSize: '0.85rem' }}>
              ✅ Laptop Speakers Ready & Unlocked
            </span>
          )}
        </div>

        {autoplayBlocked && (
          <div style={{ marginTop: '1rem', padding: '0.75rem', background: 'rgba(239, 68, 68, 0.2)', border: '1px solid var(--accent-danger)', borderRadius: 'var(--radius-sm)', color: '#f87171', fontSize: '0.9rem' }}>
            ⚠️ Browser blocked sound autoplay! Click the <strong>"CLICK TO ACTIVATE SPEAKERS"</strong> button above to allow sound.
          </div>
        )}
      </div>

      {activeSpeaker ? (
        <div className="glass-card mic-live-pulse" style={{ padding: '1.75rem', background: 'rgba(16, 185, 129, 0.1)', border: '1px solid var(--accent-success)' }}>
          <span className="status-pill active" style={{ marginBottom: '0.5rem' }}>
            {rtcStatus === 'receiving' ? '🟢 LIVE AUDIO RECEIVING' : '🟡 CONNECTING WEBRTC...'}
          </span>
          <h3 style={{ fontSize: '2.2rem', fontWeight: '800', margin: '0.5rem 0' }}>
            🎤 {activeSpeaker.name}
          </h3>
          <p style={{ fontSize: '0.95rem', color: 'var(--accent-success)' }}>
            Playing remote voice live through sound system
          </p>

          <div className="waveform-container" style={{ height: '60px', marginTop: '1rem' }}>
            <div className="wave-bar" style={{ height: '50px' }}></div>
            <div className="wave-bar" style={{ height: '60px' }}></div>
            <div className="wave-bar" style={{ height: '40px' }}></div>
            <div className="wave-bar" style={{ height: '55px' }}></div>
            <div className="wave-bar" style={{ height: '35px' }}></div>
          </div>
        </div>
      ) : (
        <div className="glass-card" style={{ padding: '1.5rem', background: 'rgba(255,255,255,0.02)' }}>
          <h4 style={{ color: 'var(--text-muted)' }}>Waiting for moderator to authorize a speaker...</h4>
        </div>
      )}

      <div style={{ marginTop: '2rem', padding: '0.85rem', background: 'rgba(239, 68, 68, 0.08)', borderRadius: 'var(--radius-sm)', border: '1px solid rgba(239, 68, 68, 0.2)' }}>
        <span style={{ fontSize: '0.8rem', color: '#f87171', fontWeight: '600' }}>
          🔒 Microphone Input: Disabled on Receiver (Feedback Safety Enforcement)
        </span>
      </div>
    </div>
  );
};

export default AudioReceiver;
