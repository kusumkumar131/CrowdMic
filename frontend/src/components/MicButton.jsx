import React from 'react';

const MicButton = ({
  isLive,
  isGranted,
  inQueue,
  queuePosition,
  onRaiseHand,
  onCancelHand,
  onStartMic,
  onStopMic,
  onEndTurn
}) => {
  if (isLive) {
    return (
      <div style={{ textAlign: 'center', margin: '1.5rem 0' }}>
        <button
          onClick={onEndTurn}
          className="btn btn-danger btn-lg mic-live-pulse"
          style={{ width: '100%', maxWidth: '320px', height: '100px', borderRadius: '50px', fontSize: '1.25rem', display: 'flex', flexDirection: 'column', gap: '0.2rem' }}
        >
          <span style={{ fontSize: '2rem' }}>🎤</span>
          <span>YOU ARE LIVE (Tap to Stop)</span>
        </button>
        <p style={{ marginTop: '0.75rem', fontSize: '0.85rem', color: 'var(--accent-success)', fontWeight: '600' }}>
          🔊 Audio is broadcasting to Auditorium Receiver Speakers
        </p>
      </div>
    );
  }

  if (isGranted) {
    return (
      <div style={{ textAlign: 'center', margin: '1.5rem 0' }}>
        <button
          onClick={onStartMic}
          className="btn btn-success btn-lg mic-live-pulse"
          style={{ width: '100%', maxWidth: '320px', height: '100px', borderRadius: '50px', fontSize: '1.25rem', display: 'flex', flexDirection: 'column', gap: '0.2rem' }}
        >
          <span style={{ fontSize: '2rem' }}>🎙️</span>
          <span>START MICROPHONE NOW</span>
        </button>
        <p style={{ marginTop: '0.75rem', fontSize: '0.85rem', color: 'var(--accent-warning)', fontWeight: '600' }}>
          Moderator has granted microphone permission! Tap to speak.
        </p>
      </div>
    );
  }

  if (inQueue) {
    return (
      <div style={{ textAlign: 'center', margin: '1.5rem 0' }}>
        <button
          onClick={onCancelHand}
          className="btn btn-secondary btn-lg"
          style={{ width: '100%', maxWidth: '320px', height: '80px', borderRadius: '40px', fontSize: '1.1rem' }}
        >
          <span>✋ In Queue (#{queuePosition}) — Tap to Cancel</span>
        </button>
        <p style={{ marginTop: '0.75rem', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
          Please wait for the moderator to approve your turn.
        </p>
      </div>
    );
  }

  return (
    <div style={{ textAlign: 'center', margin: '1.5rem 0' }}>
      <button
        onClick={onRaiseHand}
        className="btn btn-primary btn-lg"
        style={{ width: '100%', maxWidth: '320px', height: '90px', borderRadius: '45px', fontSize: '1.3rem', display: 'flex', flexDirection: 'column', gap: '0.2rem' }}
      >
        <span style={{ fontSize: '1.8rem' }}>✋</span>
        <span>RAISE HAND TO SPEAK</span>
      </button>
      <p style={{ marginTop: '0.75rem', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
        Tap to enter the virtual microphone queue.
      </p>
    </div>
  );
};

export default MicButton;
