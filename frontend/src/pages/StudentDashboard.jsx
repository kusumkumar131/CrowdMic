import React, { useState, useEffect, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import { SessionContext } from '../context/SessionContext';

const StudentDashboard = () => {
  const [sessions, setSessions] = useState([]);
  const [sessionCode, setSessionCode] = useState('');
  const [error, setError] = useState('');
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

  const handleJoinByCode = (codeToJoin) => {
    const code = codeToJoin || sessionCode;
    if (!code) {
      setError('Please enter a session code');
      return;
    }
    joinSessionByCode(code);
    navigate(`/student/session/${code.toUpperCase()}`);
  };

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto' }}>
      <div className="glass-card" style={{ padding: '2rem', marginBottom: '2rem' }}>
        <h2 style={{ fontSize: '1.6rem', fontWeight: '800' }}>🎓 Student Portal</h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem', marginTop: '0.25rem' }}>
          Enter session code provided by the speaker or select an active session below.
        </p>

        <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1.5rem' }}>
          <input
            type="text"
            className="form-input"
            placeholder="Enter Session Code (e.g. ABC123)"
            value={sessionCode}
            onChange={(e) => setSessionCode(e.target.value.toUpperCase())}
            style={{ textTransform: 'uppercase', fontFamily: 'var(--font-mono)', fontSize: '1.1rem', letterSpacing: '0.1em' }}
          />
          <button onClick={() => handleJoinByCode()} className="btn btn-primary btn-lg" style={{ whiteSpace: 'nowrap' }}>
            JOIN SESSION
          </button>
        </div>
        {error && <p style={{ color: 'var(--accent-danger)', fontSize: '0.85rem', marginTop: '0.5rem' }}>{error}</p>}
      </div>

      <h3 style={{ fontSize: '1.2rem', fontWeight: '700', marginBottom: '1rem' }}>Active Seminars & Talks</h3>
      {sessions.length === 0 ? (
        <div className="glass-card" style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
          No active sessions at the moment. Ask your moderator for a session code.
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem' }}>
          {sessions.map((s) => (
            <div key={s.id} className="glass-card" style={{ padding: '1.25rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <span className="status-pill active">{s.companyName}</span>
                <span style={{ fontFamily: 'var(--font-mono)', fontWeight: '700', color: 'var(--accent-secondary)' }}>{s.sessionCode}</span>
              </div>
              <h4 style={{ fontSize: '1.15rem', fontWeight: '700', margin: '0.75rem 0 0.5rem 0' }}>{s.title}</h4>
              <button onClick={() => handleJoinByCode(s.sessionCode)} className="btn btn-secondary" style={{ width: '100%', marginTop: '1rem' }}>
                Join Talk 🎤
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default StudentDashboard;
