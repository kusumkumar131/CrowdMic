import React from 'react';

const ConnectionStatus = ({ socketStatus, rtcStatus, micStatus }) => {
  const getBadge = (status) => {
    switch (status) {
      case 'connected':
      case 'receiving':
      case 'active':
        return { label: '🟢 Connected', class: 'active' };
      case 'connecting':
      case 'listening':
        return { label: '🟡 Connecting...', class: 'warning' };
      default:
        return { label: '🔴 Disconnected', class: 'offline' };
    }
  };

  const socketBadge = getBadge(socketStatus ? 'connected' : 'disconnected');
  const rtcBadge = getBadge(rtcStatus);
  const micBadge = getBadge(micStatus ? 'active' : 'disconnected');

  return (
    <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', alignItems: 'center' }}>
      <div className={`status-pill ${socketBadge.class}`} title="Socket.IO Real-time Connection">
        <span>Socket: {socketBadge.label}</span>
      </div>
      {rtcStatus && (
        <div className={`status-pill ${rtcBadge.class}`} title="WebRTC Audio Connection">
          <span>WebRTC: {rtcBadge.label}</span>
        </div>
      )}
      {micStatus !== undefined && (
        <div className={`status-pill ${micBadge.class}`} title="Microphone Access Status">
          <span>Mic: {micBadge.label}</span>
        </div>
      )}
    </div>
  );
};

export default ConnectionStatus;
