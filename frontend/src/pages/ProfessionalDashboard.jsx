import React, { useState, useEffect, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import { SessionContext } from '../context/SessionContext';

const ProfessionalDashboard = () => {
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
      navigate(`/professional/session/${c.toUpperCase()}`);
    }
  };

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto' }}>
      <div className="glass-card" style={{ padding: '2rem', marginBottom: '2rem' }}>
        <h2 style={{ fontSize: '1.6rem', fontWeight: '800' }}>💼 Professional & Speaker Portal</h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem', marginTop: '0.25rem' }}>
          Connect your device to broadcast company presentations and host student Q&A.
        </p>

        <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1.5rem' }}>
          <input
            type="text"
            className="form-input"
            placeholder="Enter Session Code (e.g. ABC123)"
            value={sessionCode}
            onChange={(e) => setSessionCode(e.target.value.toUpperCase())}
            style={{ textTransform: 'uppercase', fontFamily: 'var(--font-mono)', fontSize: '1.1rem' }}
          />
          <button onClick={() => handleJoin()} className="btn btn-primary btn-lg">
            JOIN AS SPEAKER
          </button>
        </div>
      </div>

      <h3 style={{ fontSize: '1.2rem', fontWeight: '700', marginBottom: '1rem' }}>Active Sessions</h3>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem' }}>
        {sessions.map((s) => (
          <div key={s.id} className="glass-card" style={{ padding: '1.25rem' }}>
            <span className="status-pill active">{s.companyName}</span>
            <h4 style={{ fontSize: '1.15rem', fontWeight: '700', margin: '0.75rem 0' }}>{s.title}</h4>
            <button onClick={() => handleJoin(s.sessionCode)} className="btn btn-secondary" style={{ width: '100%' }}>
              Join Presentation 🎙️
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ProfessionalDashboard;
