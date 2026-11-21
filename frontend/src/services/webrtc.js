import socketService from './socket';

const rtcConfig = {
  iceServers: [
    { urls: 'stun:stun.l.google.com:19002' },
    { urls: 'stun:stun1.l.google.com:19002' },
    { urls: 'stun:stun2.l.google.com:19002' },
    { urls: 'stun:stun.services.mozilla.com' }
  ]
};

export class WebRTCManager {
  constructor() {
    this.peerConnection = null;
    this.localStream = null;
    this.remoteStream = null;
    this.socket = socketService.getSocket();
    this.connectionState = 'disconnected';
    this.audioElement = null;
    this.role = null;
    this.sessionId = null;
    this.candidateQueue = [];
    this.onStateChange = null;
    this.onAutoplayBlocked = null;

    this.setupSocketListeners();
  }

  setAudioElement(element) {
    this.audioElement = element;
    if (this.audioElement && this.remoteStream) {
      this.audioElement.srcObject = this.remoteStream;
    }
  }

  setupSocketListeners() {
    // 1. WebRTC Offer
    this.socket.on('webrtc_offer', async (data) => {
      console.log('Received WebRTC offer from speaker:', data.senderName, 'role:', this.role);
      if (this.role === 'receiver') {
        await this.handleOfferAndCreateAnswer(data);
      }
    });

    // 2. WebRTC Answer
    this.socket.on('webrtc_answer', async (data) => {
      console.log('Received WebRTC answer on speaker');
      if (this.peerConnection && data.sdp) {
        try {
          await this.peerConnection.setRemoteDescription(new RTCSessionDescription(data.sdp));
          console.log('Remote description set on speaker! Flushing candidate queue...');
          await this.flushCandidateQueue();
          this.updateState('connected');
        } catch (err) {
          console.error('Failed to set remote description on speaker:', err);
        }
      }
    });

    // 3. WebRTC ICE Candidate
    this.socket.on('webrtc_ice_candidate', async (data) => {
      if (!data.candidate) return;
      const candidate = new RTCIceCandidate(data.candidate);

      if (this.peerConnection && this.peerConnection.remoteDescription && this.peerConnection.remoteDescription.type) {
        try {
          await this.peerConnection.addIceCandidate(candidate);
        } catch (e) {
          console.error('Error adding ICE candidate:', e);
        }
      } else {
        // Queue candidate until setRemoteDescription finishes
        this.candidateQueue.push(candidate);
      }
    });
  }

  async flushCandidateQueue() {
    while (this.candidateQueue.length > 0) {
      const cand = this.candidateQueue.shift();
      if (this.peerConnection) {
        try {
          await this.peerConnection.addIceCandidate(cand);
        } catch (err) {
          console.error('Error adding queued ICE candidate:', err);
        }
      }
    }
  }

  updateState(state) {
    this.connectionState = state;
    if (this.onStateChange) {
      this.onStateChange(state);
    }
  }

  /**
   * Speaker (Student / Professional) Microphone Initialization
   */
  async startMicrophone(sessionId, userRole = 'student') {
    this.role = 'publisher';
    this.sessionId = sessionId;
    this.candidateQueue = [];

    try {
      this.updateState('connecting');

      // 1. Request microphone permission
      this.localStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        },
        video: false
      });

      // 2. Create RTCPeerConnection
      if (this.peerConnection) {
        this.peerConnection.close();
      }
      this.peerConnection = new RTCPeerConnection(rtcConfig);

      // 3. Add audio track
      this.localStream.getTracks().forEach((track) => {
        this.peerConnection.addTrack(track, this.localStream);
      });

      // 4. Handle ICE candidates
      this.peerConnection.onicecandidate = (event) => {
        if (event.candidate) {
          this.socket.emit('webrtc_ice_candidate', {
            candidate: event.candidate,
            sessionId: sessionId
          });
        }
      };

      this.peerConnection.oniceconnectionstatechange = () => {
        if (this.peerConnection) {
          console.log('Speaker ICE Connection State:', this.peerConnection.iceConnectionState);
          if (this.peerConnection.iceConnectionState === 'connected' || this.peerConnection.iceConnectionState === 'completed') {
            this.updateState('connected');
          } else if (this.peerConnection.iceConnectionState === 'failed' || this.peerConnection.iceConnectionState === 'disconnected') {
            this.updateState(this.peerConnection.iceConnectionState);
          }
        }
      };

      this.peerConnection.onconnectionstatechange = () => {
        if (this.peerConnection) {
          console.log('Speaker Connection State:', this.peerConnection.connectionState);
          this.updateState(this.peerConnection.connectionState);
        }
      };

      // 5. Create SDP Offer
      const offer = await this.peerConnection.createOffer();
      await this.peerConnection.setLocalDescription(offer);

      // 6. Send Offer via Socket.IO
      this.socket.emit('webrtc_offer', {
        sdp: offer,
        targetRole: 'receiver',
        sessionId: sessionId
      });

      return true;
    } catch (error) {
      console.error('Failed to access microphone or create WebRTC connection:', error);
      this.updateState('error');
      throw error;
    }
  }

  /**
   * Auditorium Receiver Initialization
   */
  async initReceiver(sessionId) {
    this.role = 'receiver';
    this.sessionId = sessionId;
    this.candidateQueue = [];
    this.updateState('listening');
  }

  async handleOfferAndCreateAnswer(data) {
    try {
      this.updateState('connecting');

      if (this.peerConnection) {
        this.peerConnection.close();
      }

      this.peerConnection = new RTCPeerConnection(rtcConfig);
      this.candidateQueue = [];

      // Ensure transceiver is set to receive audio
      try {
        this.peerConnection.addTransceiver('audio', { direction: 'recvonly' });
      } catch (e) {
        console.log('addTransceiver not supported or already configured:', e);
      }

      this.peerConnection.onicecandidate = (event) => {
        if (event.candidate) {
          this.socket.emit('webrtc_ice_candidate', {
            candidate: event.candidate,
            targetUserId: data.senderUserId,
            sessionId: this.sessionId
          });
        }
      };

      this.peerConnection.oniceconnectionstatechange = () => {
        if (this.peerConnection) {
          console.log('Receiver ICE Connection State:', this.peerConnection.iceConnectionState);
          if (this.peerConnection.iceConnectionState === 'connected' || this.peerConnection.iceConnectionState === 'completed') {
            this.updateState('receiving');
          }
        }
      };

      this.peerConnection.ontrack = (event) => {
        console.log('Received remote audio track:', event.track);
        let stream = null;
        if (event.streams && event.streams[0]) {
          stream = event.streams[0];
        } else {
          stream = new MediaStream([event.track]);
        }
        this.remoteStream = stream;

        if (this.audioElement) {
          this.audioElement.srcObject = stream;
          this.audioElement.volume = 1.0;
          this.audioElement.muted = false;
          const playPromise = this.audioElement.play();
          if (playPromise !== undefined) {
            playPromise.then(() => {
              console.log('Audio playing successfully on receiver speakers!');
            }).catch(e => {
              console.warn('Audio play was prevented by browser autoplay policy:', e);
              if (this.onAutoplayBlocked) {
                this.onAutoplayBlocked();
              }
            });
          }
        }
        this.updateState('receiving');
      };

      // Set remote offer
      await this.peerConnection.setRemoteDescription(new RTCSessionDescription(data.sdp));

      // Flush candidates that arrived before offer was set
      await this.flushCandidateQueue();

      // Create and set local answer
      const answer = await this.peerConnection.createAnswer();
      await this.peerConnection.setLocalDescription(answer);

      // Emit answer to speaker
      this.socket.emit('webrtc_answer', {
        sdp: answer,
        targetUserId: data.senderUserId,
        sessionId: this.sessionId
      });

    } catch (error) {
      console.error('Error handling WebRTC offer on receiver:', error);
      this.updateState('error');
    }
  }

  /**
   * Unlock audio playback with explicit user gesture
   */
  async unlockAudio() {
    if (this.audioElement) {
      try {
        this.audioElement.muted = false;
        await this.audioElement.play();
        return true;
      } catch (err) {
        console.log('Unlocked audio element context');
        return true;
      }
    }
    return false;
  }

  /**
   * Stop & Cleanup
   */
  stopMicrophone() {
    if (this.localStream) {
      this.localStream.getTracks().forEach((track) => track.stop());
      this.localStream = null;
    }
    if (this.peerConnection) {
      this.peerConnection.close();
      this.peerConnection = null;
    }
    this.updateState('disconnected');
  }
}

export const webrtcManager = new WebRTCManager();
export default webrtcManager;
