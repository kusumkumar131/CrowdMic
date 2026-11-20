import React, { useState, useEffect } from 'react';

const Timer = ({ initialSeconds = 60, onExpire }) => {
  const [seconds, setSeconds] = useState(initialSeconds);

  useEffect(() => {
    setSeconds(initialSeconds);
    const interval = setInterval(() => {
      setSeconds((prev) => {
        if (prev <= 1) {
          clearInterval(interval);
          if (onExpire) onExpire();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [initialSeconds]);

  const formatTime = (secs) => {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  const percentage = (seconds / initialSeconds) * 100;
  const isWarning = seconds <= 15;

  return (
    <div style={{ textAlign: 'center' }}>
      <div style={{
        fontFamily: 'var(--font-mono)',
        fontSize: '1.6rem',
        fontWeight: '700',
        color: isWarning ? 'var(--accent-danger)' : 'var(--accent-success)'
      }}>
        ⏱️ {formatTime(seconds)}
      </div>
      <div style={{
        width: '120px',
        height: '6px',
        background: 'rgba(255,255,255,0.1)',
        borderRadius: '3px',
        marginTop: '0.35rem',
        overflow: 'hidden'
      }}>
        <div style={{
          width: `${percentage}%`,
          height: '100%',
          background: isWarning ? 'var(--accent-danger)' : 'var(--accent-success)',
          transition: 'width 1s linear'
        }}></div>
      </div>
    </div>
  );
};

export default Timer;
