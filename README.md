# 🎤 CrowdMic

> **"One microphone system for thousands of voices."**

CrowdMic is a production-quality full-stack real-time virtual microphone and Q&A management platform for large auditorium events, pre-placement talks, college seminars, town halls, and conferences.

---

## 📌 Problem & Solution

In large event halls with 1,000–3,000+ attendees, passing a physical microphone around takes valuable time and interrupts event flow. 

**CrowdMic** replaces physical microphones with a web-based virtual microphone system:
1. **Students & Professionals** use their smartphones or laptops as virtual microphones via the CrowdMic website.
2. A single **Auditorium Receiver Laptop** connected to the auditorium's central sound system receives real-time audio over **WebRTC** and plays it through the speakers.
3. An **Event Moderator** manages the queue, approves speakers, controls turn timers, and moderates questions.

---

## 🏗️ Architecture Overview

```text
Student Phone 🎤  ───┐
                    ├── WebRTC Audio (1-Way) ──> Auditorium Receiver Laptop 💻 ──> 🔊 Venue Speakers
Professional Phone 🎤 ──┘                                 │
   │                                                      │
   └─────────────────── Socket.IO Real-time Control ──────┘
                        Queue, Signals, Permissions
```

### Audio Safety Architecture
- **WebRTC**: Real-time peer-to-peer 1-way audio streaming. Raw audio is **never** sent over Socket.IO.
- **Auditorium Receiver**: Plays incoming WebRTC audio through HTML `<audio>` element. Microphone capture on receiver is **disabled** to prevent acoustic feedback.
- **Microphone Access**: Students can **only** publish audio after explicit moderator authorization.

---

## 🛠️ Technology Stack

- **Frontend**: React, React Router v6, Socket.IO Client, WebRTC Browser APIs, Vanilla CSS (Glassmorphic Theme).
- **Backend**: Python 3.10+, FastAPI, `python-socketio` (ASGI AsyncServer), PyMongo / Motor, PyJWT, Passlib (bcrypt).
- **Database**: MongoDB (`users`, `sessions`, `queue_entries`, `questions`, `speaker_history`, `session_analytics`). Included fallback memory store for instant zero-config evaluation.
- **AI / NLP**: TF-IDF & Jaccard similarity engine for duplicate question detection and category classification.

---

## 📁 Repository Structure

```text
CrowdMIC/
├── backend/
│   ├── app/
│   │   ├── config/settings.py
│   │   ├── database/mongodb.py
│   │   ├── models/ (user, session, queue, question)
│   │   ├── routes/ (auth, sessions, queue, questions, analytics)
│   │   ├── services/ (auth_service, session_service, queue_service, ai_service, memory_store)
│   │   ├── utils/security.py
│   │   ├── websocket/ (socket_manager, events)
│   │   └── main.py
│   ├── requirements.txt
│   ├── .env.example
│   └── .env
│
├── frontend/
│   ├── src/
│   │   ├── components/ (Navbar, Queue, SpeakerCard, MicButton, Timer, AudioReceiver, QuestionBoard, ConnectionStatus, AnalyticsView)
│   │   ├── context/ (AuthContext, SessionContext)
│   │   ├── hooks/ (useSocket, useWebRTC)
│   │   ├── pages/ (Login, Register, StudentDashboard, StudentSession, ProfessionalDashboard, ProfessionalSession, ModeratorDashboard, ModeratorSession, Receiver, ReceiverSession, AdminDashboard)
│   │   ├── services/ (api, socket, webrtc)
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
└── README.md
```

---

## ⚙️ Environment Variables

Copy `.env.example` in `backend/` to `.env`:

```env
MONGODB_URI=mongodb://localhost:27017
DATABASE_NAME=crowdmic
JWT_SECRET=crowdmic_super_secret_jwt_key_2026_change_in_production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
FRONTEND_URL=http://localhost:5173
PORT=8000

# STUN/TURN Servers
STUN_SERVER=stun:stun.l.google.com:19002
TURN_SERVER=
TURN_USERNAME=
TURN_PASSWORD=
```

---

## 🚀 Quick Start & Local Setup

### 1. Start Backend

```bash
cd backend
python -m venv venv
# On Windows PowerShell:
.\venv\Scripts\activate
# On macOS/Linux:
# source venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

The application will be accessible at: `http://localhost:5173`

---

## 🎬 Step-by-Step Demo Flow

Follow this demonstration procedure with multiple browser tabs or devices:

### Device 1: Auditorium Receiver (Laptop)
1. Open `http://localhost:5173/login` -> Register / Login as **Auditorium Receiver** role.
2. Navigate to Receiver page (`/receiver`).
3. Click **Connect Auditorium Receiver** on an active talk or enter session code (e.g. `ABC123`).
4. Notice **Microphone is Disabled** and status shows **"Auditorium Receiver Active"**.

### Device 2: Moderator (Laptop/Desktop)
1. Register / Login as **Moderator** role.
2. Go to `/moderator/dashboard` -> Create session:
   - Company: `ABC Technologies`
   - Title: `Pre Placement Talk 2026`
   - Code generated: `ABC123`
3. Open **Moderator Control Room**.

### Device 3: Student (Phone / Tab 3)
1. Register / Login as **Student** role.
2. Join session `ABC123`.
3. Click **✋ RAISE HAND TO SPEAK**.
4. Student enters queue (#1 position).

### Moderator & WebRTC Audio Execution:
1. Moderator sees Student in queue and clicks **`[ALLOW 🎤]`**.
2. Student receives instant Socket.IO permission notification: **"You are now live!"**
3. Student clicks **"START MICROPHONE NOW"**.
4. WebRTC Peer Connection initializes offer -> Receiver sends answer -> Stream connects.
5. Student speaks into phone microphone.
6. **Auditorium Receiver laptop plays student's live voice through its speakers!**
7. 60s Timer counts down -> Moderator clicks **`[END TURN]`** or timer expires -> Student is automatically muted.

---

## 🔧 WebRTC & Socket.IO Signaling Details

1. **Signaling**: SDP Offers, Answers, and ICE Candidates are exchanged via Socket.IO events (`webrtc_offer`, `webrtc_answer`, `webrtc_ice_candidate`).
2. **Server Authorization**: The backend checks that only the active speaker authorized by the moderator can initiate WebRTC signaling targeting the receiver.
3. **P2P Audio**: WebRTC establishes a direct RTP audio stream between speaker device and receiver laptop.

---

## 🌐 Browser Security & Microphone Permissions

- Modern browsers restrict `getUserMedia()` microphone access to secure origins (`https://` or `localhost`).
- For cross-device testing over Wi-Fi, run Chrome with `--unsafely-treat-insecure-origin-as-secure="http://<YOUR_LOCAL_IP>:5173"`.
