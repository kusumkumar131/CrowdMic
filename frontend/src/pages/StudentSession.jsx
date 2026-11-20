import React, { useContext, useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { SessionContext } from '../context/SessionContext';
import { AuthContext } from '../context/AuthContext';
import ConnectionStatus from '../components/ConnectionStatus';
import SpeakerCard from '../components/SpeakerCard';
import Queue from '../components/Queue';
import MicButton from '../components/MicButton';
import QuestionBoard from '../components/QuestionBoard';
import webrtcManager from '../services/webrtc';

const StudentSession = () => {
  const { sessionId: sessionCodeParam } = useParams();
  const { user } = useContext(AuthContext);
  const {
    session,
    queue,
    activeSpeaker,
    socketConnected,
    micGranted,
    joinSessionByCode,
    raiseHand,
    cancelHand,
    endSpeaker
  } = useContext(SessionContext);

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
      } else if (state === 'disconnected' || state === 'closed') {
        setIsLive(false);
      }
    };
  }, []);

  const handleStartMic = async () => {
    try {
      if (session) {
        await webrtcManager.startMicrophone(session.id, 'student');
      }
    } catch (e) {
      alert('Could not start microphone: ' + e.message);
    }
  };

  const handleStopMic = () => {
    webrtcManager.stopMicrophone();
    setIsLive(false);
    endSpeaker();
  };

  const myQueueEntry = queue.find((q) => user && q.userId === user.id);
  const inQueue = Boolean(myQueueEntry);
  const queuePosition = myQueueEntry ? myQueueEntry.position : null;

  return (
    <div style={{ maxWidth: '900px', margin: '0 auto' }}>
      <div className="glass-card" style={{ padding: '1.25rem', marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <span className="status-pill active">{session?.companyName || 'Placement Talk'}</span>
            <h2 style={{ fontSize: '1.5rem', fontWeight: '800', marginTop: '0.2rem' }}>
              {session?.title || 'Pre Placement Session'}
            </h2>
          </div>

          <ConnectionStatus socketStatus={socketConnected} rtcStatus={rtcStatus} micStatus={isLive} />
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 320px', gap: '1.5rem' }}>
        <div>
          <SpeakerCard
            activeSpeaker={activeSpeaker}
            timerDuration={session?.speakerTimerDuration || 60}
            onEndTurn={handleStopMic}
            isModerator={false}
          />

          <MicButton
            isLive={isLive}
            isGranted={micGranted}
            inQueue={inQueue}
            queuePosition={queuePosition}
            onRaiseHand={raiseHand}
            onCancelHand={cancelHand}
            onStartMic={handleStartMic}
            onStopMic={handleStopMic}
            onEndTurn={handleStopMic}
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

export default StudentSession;
