import React, { useState, useEffect, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import { SessionContext } from '../context/SessionContext';

const Receiver = () => {
  const [sessions, setSessions] = useState([]);
  const [sessionCode, setSessionCode] = useState('');
  const { joinSessionByCode } = useContext(SessionContext);
  const navigate = useNavigate();

  useEffect(() => {
    fetchActiveSessions();
  }, []);

  const fetchActiveSessions = async () => {
    try {
      const res = await api.get('/sessions');
      setSessions(res.data || []);
    } catch (e) {
      console.error('Failed to load active sessions:', e);
    }
  };

  const handleJoin = (code) => {
    const c = code || sessionCode;
    if (c) {
      joinSessionByCode(c);
      navigate(`/receiver/session/${c.toUpperCase()}`);
    }
  };

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto', textAlign: 'center' }}>
      <div className="glass-card" style={{ padding: '2.5rem', marginBottom: '2rem', border: '1px solid var(--accent-primary)' }}>
        <span style={{ fontSize: '4rem', display: 'block', marginBottom: '0.5rem' }}>💻</span>
        <h2 style={{ fontSize: '2rem', fontWeight: '800' }}>CROWD MIC AUDITORIUM RECEIVER</h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '1rem', marginTop: '0.5rem', maxWidth: '500px', margin: '0.5rem auto 1.5rem auto' }}>
          Connect this auditorium laptop to receive live WebRTC audio streams from authorized speakers and broadcast through venue speakers.
        </p>

        <div style={{ display: 'flex', gap: '0.75rem', maxWidth: '440px', margin: '0 auto' }}>
          <input
            type="text"
            className="form-input"
            placeholder="Enter Session Code (e.g. ABC123)"
            value={sessionCode}
            onChange={(e) => setSessionCode(e.target.value.toUpperCase())}
            style={{ textTransform: 'uppercase', fontFamily: 'var(--font-mono)', fontSize: '1.2rem', textAlign: 'center' }}
          />
          <button onClick={() => handleJoin()} className="btn btn-success btn-lg">
            LAUNCH RECEIVER
          </button>
        </div>
      </div>

      <h3 style={{ fontSize: '1.2rem', fontWeight: '700', marginBottom: '1rem', textAlign: 'left' }}>Active Event Sessions</h3>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem' }}>
        {sessions.map((s) => (
          <div key={s.id} className="glass-card" style={{ padding: '1.25rem', textAlign: 'left' }}>
            <span className="status-pill active">{s.companyName}</span>
            <h4 style={{ fontSize: '1.15rem', fontWeight: '700', margin: '0.75rem 0' }}>{s.title}</h4>
            <button onClick={() => handleJoin(s.sessionCode)} className="btn btn-secondary" style={{ width: '100%', marginTop: '0.5rem' }}>
              Connect Auditorium Receiver 🔊
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Receiver;
