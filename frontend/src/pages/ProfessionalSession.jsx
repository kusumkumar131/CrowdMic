import React, { useContext, useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { SessionContext } from '../context/SessionContext';
import { AuthContext } from '../context/AuthContext';
import ConnectionStatus from '../components/ConnectionStatus';
import SpeakerCard from '../components/SpeakerCard';
import QuestionBoard from '../components/QuestionBoard';
import Queue from '../components/Queue';
import webrtcManager from '../services/webrtc';

const ProfessionalSession = () => {
  const { sessionId: sessionCodeParam } = useParams();
  const { user } = useContext(AuthContext);
  const { session, activeSpeaker, socketConnected, joinSessionByCode, endSpeaker } = useContext(SessionContext);

  const [rtcStatus, setRtcStatus] = useState('disconnected');
  const [isLive, setIsLive] = useState(false);

  useEffect(() => {
    if (sessionCodeParam && (!session || session.sessionCode !== sessionCodeParam.toUpperCase())) {
      joinSessionByCode(sessionCodeParam);
    }
  }, [sessionCodeParam]);

  useEffect(() => {
    webrtcManager.onStateChange = (state) => {
      setRtcStatus(state);
      if (state === 'connected') {
        setIsLive(true);
      } else if (state === 'disconnected') {
        setIsLive(false);
      }
    };
  }, []);

  const handleStartProfMic = async () => {
    try {
      if (session) {
        await webrtcManager.startMicrophone(session.id, 'professional');
      }
    } catch (e) {
      alert('Failed to connect microphone: ' + e.message);
    }
  };

  const handleStopProfMic = () => {
    webrtcManager.stopMicrophone();
    setIsLive(false);
    endSpeaker();
  };

  return (
    <div style={{ maxWidth: '960px', margin: '0 auto' }}>
      <div className="glass-card" style={{ padding: '1.25rem', marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <span className="role-badge professional">💼 Professional Speaker</span>
            <h2 style={{ fontSize: '1.5rem', fontWeight: '800', marginTop: '0.2rem' }}>
              {session?.companyName} — {session?.title}
            </h2>
          </div>
          <ConnectionStatus socketStatus={socketConnected} rtcStatus={rtcStatus} micStatus={isLive} />
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: '1.5rem' }}>
        <div>
          <div className="glass-card" style={{ padding: '1.5rem', marginBottom: '1.5rem', textAlign: 'center' }}>
            {isLive ? (
              <button onClick={handleStopProfMic} className="btn btn-danger btn-lg mic-live-pulse" style={{ width: '100%', height: '80px', borderRadius: '40px' }}>
                🎙️ STOP BROADCASTING (LIVE)
              </button>
            ) : (
              <button onClick={handleStartProfMic} className="btn btn-primary btn-lg" style={{ width: '100%', height: '80px', borderRadius: '40px' }}>
                🎙️ START PROFESSIONAL MICROPHONE
              </button>
            )}
          </div>

          <SpeakerCard
            activeSpeaker={activeSpeaker}
            timerDuration={120}
            onEndTurn={handleStopProfMic}
            isModerator={false}
          />

          <QuestionBoard sessionId={session?.id} isModerator={false} />
        </div>

        <div>
          <Queue isModerator={false} />
        </div>
      </div>
    </div>
  );
};

export default ProfessionalSession;
