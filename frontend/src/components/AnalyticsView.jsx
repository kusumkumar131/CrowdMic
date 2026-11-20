import React, { useState, useEffect } from 'react';
import api from '../services/api';

const AnalyticsView = ({ sessionId }) => {
  const [data, setData] = useState(null);

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        const res = await api.get(`/sessions/${sessionId}/analytics`);
        setData(res.data);
      } catch (e) {
        console.error('Failed to load analytics:', e);
      }
    };
    if (sessionId) {
      fetchAnalytics();
    }
  }, [sessionId]);

  if (!data) return <p style={{ color: 'var(--text-muted)' }}>Loading analytics...</p>;

  return (
    <div className="glass-card" style={{ padding: '1.75rem' }}>
      <h3 style={{ fontSize: '1.3rem', fontWeight: '800', marginBottom: '1.25rem' }}>
        📊 Session Analytics & Metrics
      </h3>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
        <div className="glass-card" style={{ padding: '1rem', textAlign: 'center' }}>
          <span style={{ fontSize: '1.8rem', fontWeight: '800', color: 'var(--accent-primary)' }}>
            {data.totalParticipants}
          </span>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>Total Participants</p>
        </div>

        <div className="glass-card" style={{ padding: '1rem', textAlign: 'center' }}>
          <span style={{ fontSize: '1.8rem', fontWeight: '800', color: 'var(--accent-secondary)' }}>
            {data.questionsAsked}
          </span>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>Questions Asked</p>
        </div>

        <div className="glass-card" style={{ padding: '1rem', textAlign: 'center' }}>
          <span style={{ fontSize: '1.8rem', fontWeight: '800', color: 'var(--accent-success)' }}>
            {data.averageSpeakingTime}s
          </span>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>Avg Speaking Time</p>
        </div>

        <div className="glass-card" style={{ padding: '1rem', textAlign: 'center' }}>
          <span style={{ fontSize: '1.8rem', fontWeight: '800', color: 'var(--accent-warning)' }}>
            {data.duplicateQuestions}
          </span>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>Duplicates Flagged</p>
        </div>
      </div>

      <h4 style={{ fontSize: '0.95rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>Categories Breakdown</h4>
      <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
        {Object.entries(data.categories || {}).map(([cat, count]) => (
          <span key={cat} className="role-badge student" style={{ fontSize: '0.8rem' }}>
            {cat}: {count}
          </span>
        ))}
      </div>
    </div>
  );
};

export default AnalyticsView;
