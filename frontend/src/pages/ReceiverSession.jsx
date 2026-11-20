import React, { useContext, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { SessionContext } from '../context/SessionContext';
import AudioReceiver from '../components/AudioReceiver';
import Queue from '../components/Queue';

const ReceiverSession = () => {
  const { sessionId: sessionCodeParam } = useParams();
  const { session, activeSpeaker, socketConnected, joinSessionByCode, refreshQueue } = useContext(SessionContext);

  useEffect(() => {
    if (sessionCodeParam && (!session || session.sessionCode !== sessionCodeParam.toUpperCase())) {
      joinSessionByCode(sessionCodeParam);
    }
  }, [sessionCodeParam]);

  useEffect(() => {
    if (!session?.id) return;
    refreshQueue(session.id);
    const interval = setInterval(() => {
      refreshQueue(session.id);
    }, 3000);
    return () => clearInterval(interval);
  }, [session?.id]);

  return (
    <div style={{ maxWidth: '1100px', margin: '0 auto' }}>
      {/* Session Title Header Banner */}
      <div className="glass-card" style={{ padding: '1.5rem', marginBottom: '1.5rem', textAlign: 'center' }}>
        <span className="role-badge receiver" style={{ fontSize: '0.9rem', marginBottom: '0.5rem' }}>
          💻 CENTRAL AUDITORIUM AUDIO RECEIVER
        </span>
        <h1 style={{ fontSize: '2.2rem', fontWeight: '800', margin: '0.3rem 0' }}>
          {session?.companyName || 'Placement Session'}
        </h1>
        <p style={{ color: 'var(--text-muted)', fontSize: '1.1rem' }}>
          {session?.title || 'Pre Placement Talk & Q&A'}
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: '1.5rem' }}>
        <div>
          <AudioReceiver
            sessionId={session?.id}
            activeSpeaker={activeSpeaker}
            socketConnected={socketConnected}
          />
        </div>

        <div>
          <Queue isModerator={false} />
        </div>
      </div>
    </div>
  );
};

export default ReceiverSession;
