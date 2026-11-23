import React, { useContext } from 'react';
import { SessionContext } from '../context/SessionContext';
import { AuthContext } from '../context/AuthContext';

const Queue = ({ isModerator = false }) => {
  const { queue, allowSpeaker } = useContext(SessionContext);
  const { user } = useContext(AuthContext);

  return (
    <div className="glass-card" style={{ padding: '1.25rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <h3 style={{ fontSize: '1.1rem', fontWeight: '700' }}>✋ Speaking Queue</h3>
        <span className="status-pill active">{queue.length} Waiting</span>
      </div>

      {queue.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '2rem 1rem', color: 'var(--text-muted)' }}>
          <span style={{ fontSize: '2rem', display: 'block', marginBottom: '0.5rem' }}>⌛</span>
          <p style={{ fontSize: '0.9rem' }}>No one in the queue yet.</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          {queue.map((entry, index) => {
            const myUserId = user?.id || user?._id;
            const isUserSelf = myUserId && String(myUserId) === String(entry.userId);

            return (
              <div
                key={entry.id || index}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justify: 'space-between',
                  padding: '0.85rem 1rem',
                  borderRadius: 'var(--radius-sm)',
                  background: isUserSelf ? 'rgba(99, 102, 241, 0.15)' : 'rgba(255, 255, 255, 0.03)',
                  border: isUserSelf ? '1px solid var(--accent-primary)' : '1px solid var(--border-subtle)'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <div style={{
                    width: '32px',
                    height: '32px',
                    borderRadius: '50%',
                    background: entry.status === 'speaking' ? 'var(--accent-success)' : 'var(--accent-primary)',
                    color: '#fff',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontWeight: '700',
                    fontSize: '0.85rem'
                  }}>
                    #{entry.position}
                  </div>
                  <div>
                    <h4 style={{ fontSize: '0.95rem', fontWeight: '600' }}>
                      {entry.userName} {isUserSelf && <span style={{ color: 'var(--accent-primary)', fontSize: '0.8rem' }}>(You)</span>}
                    </h4>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'capitalize' }}>
                      {entry.status === 'next' ? '⚡ Next in Queue' : entry.status}
                    </span>
                  </div>
                </div>

                {isModerator && (
                  <button
                    onClick={() => allowSpeaker(entry.id, entry.userId, entry.userName)}
                    className="btn btn-success"
                    style={{ padding: '0.4rem 0.85rem', fontSize: '0.8rem' }}
                  >
                    ALLOW 🎤
                  </button>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default Queue;
