import React, { useEffect, useRef, useState } from 'react';
import webrtcManager from '../services/webrtc';
import ConnectionStatus from './ConnectionStatus';

const AudioReceiver = ({ sessionId, activeSpeaker, socketConnected }) => {
  const audioRef = useRef(null);
  const [rtcStatus, setRtcStatus] = useState('listening');

  useEffect(() => {
    if (audioRef.current) {
      webrtcManager.setAudioElement(audioRef.current);
    }
    webrtcManager.onStateChange = (state) => {
      setRtcStatus(state);
    };
    if (sessionId) {
      webrtcManager.initReceiver(sessionId);
    }
  }, [sessionId]);

  return (
    <div className="glass-card" style={{ padding: '2.5rem', textAlign: 'center', border: '1px solid var(--accent-primary)' }}>
      {/* Hidden/Styled HTML Audio element */}
      <audio ref={audioRef} autoPlay style={{ display: 'none' }} />

      <div style={{ marginBottom: '1.5rem', display: 'flex', justifyContent: 'center' }}>
        <ConnectionStatus socketStatus={socketConnected} rtcStatus={rtcStatus} micStatus={false} />
      </div>

      <div style={{ margin: '2rem 0' }}>
        <span style={{ fontSize: '4rem', display: 'block', marginBottom: '1rem' }}>
          🔊
        </span>
        <h2 style={{ fontSize: '2rem', fontWeight: '800' }}>
          AUDITORIUM RECEIVER ACTIVE
        </h2>
        <p style={{ color: 'var(--text-muted)', marginTop: '0.5rem', fontSize: '1rem' }}>
          Output: <strong>Laptop Speakers / Auditorium Sound System</strong>
        </p>
      </div>

      {activeSpeaker ? (
        <div className="glass-card mic-live-pulse" style={{ padding: '1.75rem', background: 'rgba(16, 185, 129, 0.1)', border: '1px solid var(--accent-success)' }}>
          <span className="status-pill active" style={{ marginBottom: '0.5rem' }}>
            🟢 RECEIVING AUDIO
          </span>
          <h3 style={{ fontSize: '2.2rem', fontWeight: '800', margin: '0.5rem 0' }}>
            🎤 {activeSpeaker.name}
          </h3>
          <p style={{ fontSize: '0.95rem', color: 'var(--accent-success)' }}>
            Playing remote WebRTC stream live to auditorium audience
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
          <h4 style={{ color: 'var(--text-muted)' }}>Waiting for next authorized speaker...</h4>
        </div>
      )}

      <div style={{ marginTop: '2rem', padding: '1rem', background: 'rgba(239, 68, 68, 0.08)', borderRadius: 'var(--radius-sm)', border: '1px solid rgba(239, 68, 68, 0.2)' }}>
        <span style={{ fontSize: '0.85rem', color: '#f87171', fontWeight: '600' }}>
          🔒 Microphone Input: Disabled on Receiver (Feedback Safety Enforcement)
        </span>
      </div>
    </div>
  );
};

export default AudioReceiver;
