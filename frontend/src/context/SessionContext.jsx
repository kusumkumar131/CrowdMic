import React, { createContext, useState, useEffect, useContext } from 'react';
import socketService from '../services/socket';
import { AuthContext } from './AuthContext';
import api from '../services/api';

export const SessionContext = createContext();

export const SessionProvider = ({ children }) => {
  const { user } = useContext(AuthContext);
  const [session, setSession] = useState(null);
  const [queue, setQueue] = useState([]);
  const [activeSpeaker, setActiveSpeaker] = useState(null);
  const [notification, setNotification] = useState(null);
  const [socketConnected, setSocketConnected] = useState(false);
  const [micGranted, setMicGranted] = useState(false);

  const socket = socketService.getSocket();

  useEffect(() => {
    socket.on('connect', () => setSocketConnected(true));
    socket.on('disconnect', () => setSocketConnected(false));

    socket.on('joined_session', (data) => {
      setSession(data.session);
      setActiveSpeaker(data.activeSpeaker);
    });

    socket.on('queue_updated', (data) => {
      setQueue(data.queue || []);
      setActiveSpeaker(data.activeSpeaker);
    });

    socket.on('speaker_allowed', (data) => {
      setActiveSpeaker(data.speaker);
    });

    socket.on('speaker_ended', () => {
      setActiveSpeaker(null);
      setMicGranted(false);
    });

    socket.on('mic_permission_granted', () => {
      setMicGranted(true);
    });

    socket.on('notification', (notif) => {
      setNotification(notif);
      setTimeout(() => setNotification(null), 5000);
    });

    return () => {
      socket.off('connect');
      socket.off('disconnect');
      socket.off('joined_session');
      socket.off('queue_updated');
      socket.off('speaker_allowed');
      socket.off('speaker_ended');
      socket.off('mic_permission_granted');
      socket.off('notification');
    };
  }, [user]);

  const joinSessionByCode = async (sessionCode) => {
    if (sessionCode) {
      try {
        const res = await api.get(`/sessions/${sessionCode}`);
        setSession(res.data);
      } catch (e) {
        console.error('Failed to fetch session via REST:', e);
      }
    }
    if (user && sessionCode) {
      socket.emit('join_session', {
        sessionCode: sessionCode.toUpperCase(),
        userId: user.id,
        name: user.name,
        role: user.role
      });
    }
  };

  const raiseHand = () => {
    socket.emit('raise_hand', {});
  };

  const cancelHand = () => {
    socket.emit('cancel_hand', {});
  };

  const allowSpeaker = (entryId, userId, userName) => {
    socket.emit('allow_speaker', { entryId, userId, userName });
  };

  const endSpeaker = () => {
    socket.emit('end_speaker', {});
  };

  const muteSpeaker = () => {
    socket.emit('mute_speaker', {});
  };

  const allowProfessionalMic = (userId, userName) => {
    socket.emit('allow_professional_mic', { userId, userName });
  };

  return (
    <SessionContext.Provider value={{
      session,
      setSession,
      queue,
      activeSpeaker,
      notification,
      socketConnected,
      micGranted,
      joinSessionByCode,
      raiseHand,
      cancelHand,
      allowSpeaker,
      endSpeaker,
      muteSpeaker,
      allowProfessionalMic
    }}>
      {children}
    </SessionContext.Provider>
  );
};
