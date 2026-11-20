import React, { useState, useEffect } from 'react';
import api from '../services/api';

const AdminDashboard = () => {
  const [sessions, setSessions] = useState([]);

  useEffect(() => {
    fetchSessions();
  }, []);

  const fetchSessions = async () => {
    try {
      const res = await api.get('/sessions');
      setSessions(res.data || []);
    } catch (e) {
      console.error('Failed to load admin sessions:', e);
    }
  };

  const handleEndSession = async (id) => {
    try {
      await api.patch(`/sessions/${id}/status`, { status: 'ended' });
      fetchSessions();
    } catch (e) {
      console.error('Failed to end session:', e);
    }
  };

  return (
    <div style={{ maxWidth: '1000px', margin: '0 auto' }}>
      <div className="glass-card" style={{ padding: '2rem', marginBottom: '2rem' }}>
        <h2 style={{ fontSize: '1.8rem', fontWeight: '800' }}>⚙️ Platform Administration</h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem', marginTop: '0.25rem' }}>
          Overview of all CrowdMic system events, active sessions, and database activity.
        </p>
      </div>

      <h3 style={{ fontSize: '1.2rem', fontWeight: '700', marginBottom: '1rem' }}>Active & Past Event Sessions</h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        {sessions.length === 0 ? (
          <div className="glass-card" style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
            No registered sessions found.
          </div>
        ) : (
          sessions.map((s) => (
            <div key={s.id} className="glass-card" style={{ padding: '1.25rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <span className="status-pill active">{s.status.toUpperCase()}</span>
                <h4 style={{ fontSize: '1.2rem', fontWeight: '700', margin: '0.4rem 0' }}>
                  {s.companyName} — {s.title}
                </h4>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                  Code: <strong style={{ color: 'var(--accent-primary)', fontFamily: 'var(--font-mono)' }}>{s.sessionCode}</strong> | Duration: {s.speakerTimerDuration}s
                </p>
              </div>

              {s.status !== 'ended' && (
                <button onClick={() => handleEndSession(s.id)} className="btn btn-danger">
                  End Session
                </button>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default AdminDashboard;
