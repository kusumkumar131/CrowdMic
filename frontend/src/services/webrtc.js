import socketService from './socket';

const rtcConfig = {
  iceServers: [
    { urls: 'stun:stun.l.google.com:19002' },
    { urls: 'stun:stun1.l.google.com:19002' }
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
    this.onStateChange = null;

    this.setupSocketListeners();
  }

  setAudioElement(element) {
    this.audioElement = element;
  }

  setupSocketListeners() {
    this.socket.on('webrtc_offer', async (data) => {
      console.log('Received WebRTC offer from speaker:', data.senderName);
      if (this.role === 'receiver') {
        await this.handleOfferAndCreateAnswer(data);
      }
    });

    this.socket.on('webrtc_answer', async (data) => {
      console.log('Received WebRTC answer');
      if (this.peerConnection && data.sdp) {
        await this.peerConnection.setRemoteDescription(new RTCSessionDescription(data.sdp));
        this.updateState('connected');
      }
    });

    this.socket.on('webrtc_ice_candidate', async (data) => {
      if (this.peerConnection && data.candidate) {
        try {
          await this.peerConnection.addIceCandidate(new RTCIceCandidate(data.candidate));
        } catch (e) {
          console.error('Error adding ICE candidate:', e);
        }
      }
    });
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

      this.peerConnection.onconnectionstatechange = () => {
        if (this.peerConnection) {
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
    this.updateState('listening');
  }

  async handleOfferAndCreateAnswer(data) {
    try {
      this.updateState('connecting');

      if (this.peerConnection) {
        this.peerConnection.close();
      }

      this.peerConnection = new RTCPeerConnection(rtcConfig);
      this.remoteStream = new MediaStream();

      if (this.audioElement) {
        this.audioElement.srcObject = this.remoteStream;
      }

      this.peerConnection.ontrack = (event) => {
        console.log('Received remote audio track!');
        event.streams[0].getTracks().forEach((track) => {
          this.remoteStream.addTrack(track);
        });

        if (this.audioElement) {
          this.audioElement.play().catch(e => console.log('Audio autoplay prevented:', e));
        }
        this.updateState('receiving');
      };

      this.peerConnection.onicecandidate = (event) => {
        if (event.candidate) {
          this.socket.emit('webrtc_ice_candidate', {
            candidate: event.candidate,
            targetUserId: data.senderUserId,
            sessionId: this.sessionId
          });
        }
      };

      await this.peerConnection.setRemoteDescription(new RTCSessionDescription(data.sdp));
      const answer = await this.peerConnection.createAnswer();
      await this.peerConnection.setLocalDescription(answer);

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
