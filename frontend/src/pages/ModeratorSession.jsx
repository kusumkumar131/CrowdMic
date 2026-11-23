import React, { useContext, useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { SessionContext } from '../context/SessionContext';
import SpeakerCard from '../components/SpeakerCard';
import Queue from '../components/Queue';
import QuestionBoard from '../components/QuestionBoard';
import AnalyticsView from '../components/AnalyticsView';
import ConnectionStatus from '../components/ConnectionStatus';

const ModeratorSession = () => {
  const { sessionId: sessionCodeParam } = useParams();
  const { session, activeSpeaker, socketConnected, joinSessionByCode, refreshQueue, endSpeaker, muteSpeaker } = useContext(SessionContext);
  const [activeTab, setActiveTab] = useState('controls'); // controls, questions, analytics

  useEffect(() => {
    if (sessionCodeParam && (!session || session.sessionCode !== sessionCodeParam.toUpperCase())) {
      joinSessionByCode(sessionCodeParam);
    }
  }, [sessionCodeParam]);

  const effectiveSessionId = session?.id || sessionCodeParam;

  useEffect(() => {
    if (!effectiveSessionId) return;
    refreshQueue(effectiveSessionId);
    const interval = setInterval(() => {
      refreshQueue(effectiveSessionId);
    }, 3000);
    return () => clearInterval(interval);
  }, [effectiveSessionId]);

  return (
    <div style={{ maxWidth: '1100px', margin: '0 auto' }}>
      {/* Session Overview Header */}
      <div className="glass-card" style={{ padding: '1.25rem', marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <span className="role-badge moderator">🎛️ MODERATOR CONTROL ROOM</span>
              <span className="status-pill active">Code: <strong>{session?.sessionCode}</strong></span>
            </div>
            <h2 style={{ fontSize: '1.6rem', fontWeight: '800', marginTop: '0.3rem' }}>
              {session?.companyName} — {session?.title}
            </h2>
          </div>

          <ConnectionStatus socketStatus={socketConnected} rtcStatus="connected" micStatus={false} />
        </div>

        {/* Tab Navigation */}
        <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1.25rem', borderTop: '1px solid var(--border-subtle)', paddingTop: '1rem' }}>
          <button
            onClick={() => setActiveTab('controls')}
            className={`btn ${activeTab === 'controls' ? 'btn-primary' : 'btn-secondary'}`}
          >
            🎛️ Live Queue & Mic Control
          </button>
          <button
            onClick={() => setActiveTab('questions')}
            className={`btn ${activeTab === 'questions' ? 'btn-primary' : 'btn-secondary'}`}
          >
            💬 Q&A & AI Categorization
          </button>
          <button
            onClick={() => setActiveTab('analytics')}
            className={`btn ${activeTab === 'analytics' ? 'btn-primary' : 'btn-secondary'}`}
          >
            📊 Analytics & Insights
          </button>
        </div>
      </div>

      {activeTab === 'controls' && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 380px', gap: '1.5rem' }}>
          <div>
            <SpeakerCard
              activeSpeaker={activeSpeaker}
              timerDuration={session?.speakerTimerDuration || 60}
              onEndTurn={endSpeaker}
              onMute={muteSpeaker}
              isModerator={true}
            />
          </div>

          <div>
            <Queue isModerator={true} />
          </div>
        </div>
      )}

      {activeTab === 'questions' && (
        <QuestionBoard sessionId={session?.id} isModerator={true} />
      )}

      {activeTab === 'analytics' && (
        <AnalyticsView sessionId={session?.id} />
      )}
    </div>
  );
};

export default ModeratorSession;
