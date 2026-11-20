import React, { useState, useEffect, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import { SessionContext } from '../context/SessionContext';

const ModeratorDashboard = () => {
  const [companyName, setCompanyName] = useState('');
  const [title, setTitle] = useState('');
  const [duration, setDuration] = useState(60);
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(false);
  const { joinSessionByCode } = useContext(SessionContext);
  const navigate = useNavigate();

  useEffect(() => {
    fetchSessions();
  }, []);

  const fetchSessions = async () => {
    try {
      const res = await api.get('/sessions');
      setSessions(res.data || []);
    } catch (e) {
      console.error('Failed to fetch sessions:', e);
    }
  };

  const handleCreateSession = async (e) => {
    e.preventDefault();
    if (!companyName || !title) return;
    setLoading(true);
    try {
      const res = await api.post('/sessions', {
        companyName,
        title,
        speakerTimerDuration: parseInt(duration),
        allowProfMic: true
      });
      const newSession = res.data;
      joinSessionByCode(newSession.sessionCode);
      navigate(`/moderator/session/${newSession.sessionCode}`);
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to create session');
    } finally {
      setLoading(false);
    }
  };

  const handleOpenModerator = (sessionCode) => {
    joinSessionByCode(sessionCode);
    navigate(`/moderator/session/${sessionCode}`);
  };

  return (
    <div style={{ maxWidth: '900px', margin: '0 auto' }}>
      <div className="glass-card" style={{ padding: '2rem', marginBottom: '2rem' }}>
        <h2 style={{ fontSize: '1.6rem', fontWeight: '800' }}>🎛️ Moderator Control Dashboard</h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem', marginTop: '0.25rem', marginBottom: '1.5rem' }}>
          Create a new event session to manage auditorium student speaking queue and Q&A.
        </p>

        <form onSubmit={handleCreateSession} style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
          <div className="form-group">
            <label className="form-label">Company / Host Name</label>
            <input
              type="text"
              className="form-input"
              required
              placeholder="e.g. ABC Technologies"
              value={companyName}
              onChange={(e) => setCompanyName(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label className="form-label">Event / Talk Title</label>
            <input
              type="text"
              className="form-input"
              required
              placeholder="e.g. Pre Placement Talk 2026"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label className="form-label">Speaker Turn Timer</label>
            <select
              className="form-select"
              value={duration}
              onChange={(e) => setDuration(e.target.value)}
            >
              <option value={30}>30 Seconds</option>
              <option value={60}>60 Seconds (Default)</option>
              <option value={90}>90 Seconds</option>
              <option value={120}>120 Seconds</option>
            </select>
          </div>

          <div style={{ display: 'flex', alignItems: 'flex-end', marginBottom: '1.25rem' }}>
            <button type="submit" className="btn btn-primary btn-lg" style={{ width: '100%' }} disabled={loading}>
              {loading ? 'Creating...' : '🚀 CREATE SESSION'}
            </button>
          </div>
        </form>
      </div>

      <h3 style={{ fontSize: '1.2rem', fontWeight: '700', marginBottom: '1rem' }}>Active & Managed Sessions</h3>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem' }}>
        {sessions.map((s) => (
          <div key={s.id} className="glass-card" style={{ padding: '1.25rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span className="status-pill active">{s.companyName}</span>
              <span style={{ fontFamily: 'var(--font-mono)', fontWeight: '700', color: 'var(--accent-primary)' }}>{s.sessionCode}</span>
            </div>
            <h4 style={{ fontSize: '1.15rem', fontWeight: '700', margin: '0.75rem 0' }}>{s.title}</h4>
            <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1rem' }}>
              <button onClick={() => handleOpenModerator(s.sessionCode)} className="btn btn-primary" style={{ flex: 1 }}>
                Open Control Room 🎛️
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ModeratorDashboard;
