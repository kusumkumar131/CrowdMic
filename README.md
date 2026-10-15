# CrowdMic

CrowdMic is a real-time auditorium Q&A MVP. Students join with a session code, enter a moderated queue, and send microphone audio directly to one designated receiver over WebRTC. FastAPI and MongoDB manage accounts, session membership, queue state, and turns. Socket.IO carries control events and WebRTC signaling only; it never carries the audio stream.

## Architecture

```text
Student phone ── REST + Socket.IO ── FastAPI ── MongoDB (metadata)
      │                                  │
      └────────── WebRTC audio ──────────┴── Receiver laptop → PA
```

## Requirements

- Python 3.11 or newer
- Node.js 20 or newer
- MongoDB 6+ (local Community Server or an Atlas database)
- HTTPS in production; browsers allow microphone access on localhost during development

## Windows local setup

1. Start MongoDB locally or create an Atlas database. Copy `backend/.env.example` to `backend/.env` and set `MONGODB_URI`, `JWT_SECRET` (use a long random value), and `FRONTEND_ORIGINS`.
2. Open PowerShell in `backend`: `py -m venv .venv`, then `.venv\Scripts\Activate.ps1`, then `pip install -r requirements.txt`.
3. Start the API and Socket.IO server from `backend`: `uvicorn app.main:application --host 0.0.0.0 --port 8000 --reload`.
4. Copy `frontend/.env.example` to `frontend/.env`, then in `frontend` run `npm install` and `npm run dev`.
5. Visit `http://localhost:5173`. Register a moderator account, create a session, then register a receiver and student account in separate browser profiles. Use the generated six-character session code to join each role.

## Audio test (two browsers/devices)

1. Use one browser on a phone as a student and another browser on a laptop as a receiver. The receiver laptop should be connected to headphones or the PA input before playback.
2. Join the same code on both. The receiver screen should show **Audio ready**.
3. In a moderator browser, open the created session and approve the student from the queue.
4. Grant microphone permission on the student browser. Speak into the phone; the laptop receiver should play the live audio. Press **Mute PA** to mute receiver playback.
5. End the turn in the moderator view and confirm the student microphone stops and the receiver returns to standby.

WebRTC needs STUN to establish peer connectivity. The default Google STUN URL is for development. For restrictive NATs, configure a TURN service in `backend/.env` using `TURN_URL`, `TURN_USERNAME`, and `TURN_CREDENTIAL`; use short-lived credentials in production. Socket.IO relays SDP and ICE messages only between the active speaker and the session receiver. One session has one active speaker slot acquired with an atomic MongoDB conditional update.

## API overview

All routes are under `/api` unless stated. Authenticated routes use `Authorization: Bearer <JWT>`.

| Method | Path | Role | Purpose |
|---|---|---|---|
| POST | `/auth/register` | Public | Create a student, moderator, or receiver account |
| POST | `/auth/login` | Public | Login and obtain a JWT |
| GET | `/auth/me` | Any | Current profile |
| GET | `/sessions` | Any | List active sessions (moderators see their own) |
| POST | `/sessions` | Moderator | Create session with speaking limit |
| POST | `/sessions/join` | Student | Join session using code |
| GET | `/sessions/{code}` | Member | Session and current queue state |
| POST/DELETE | `/sessions/{code}/queue` | Student | Raise hand / cancel request |
| POST | `/sessions/{code}/approve/{entry_id}` | Session moderator | Atomically activate a queued speaker |
| POST | `/sessions/{code}/end-turn` | Session moderator | End active turn |
| POST | `/sessions/{code}/queue/{entry_id}/skip` | Session moderator | Skip pending request |
| GET | `/sessions/{code}/history` | Session moderator | Recent completed turns |
| GET | `/webrtc-config` | Any | Configured ICE servers |
| GET | `/health` | Public | API and MongoDB health |

Socket.IO authenticates its connection with `{auth:{token}}`. `session:join` joins an authorized session room. `queue:update`, `speaker:approved`, `speaker:revoked`, `session:member`, and `receiver:status` are server events. `receiver:claim` claims the receiver endpoint. `webrtc:signal` accepts `{to, data}` and relays only for the current speaker/receiver pair. A receiver can only be claimed by one account at a time.

## Tests and current scope

Backend unit and route tests live in `backend/tests`; run `pytest` from `backend`. Frontend production bundle check: `npm run build` from `frontend`.

The receiver should be a receiver-role account (registration currently allows all roles for convenient local setup; production deployments should restrict moderator/receiver account creation to an administrator). MongoDB must be running for authenticated use. Browser autoplay policy may require clicking **Play audio** once. Output-device selection depends on browser support for `HTMLMediaElement.setSinkId`. For public deployment, use HTTPS, a production JWT secret, rate limiting at the edge, and TURN credentials with expiry. The MVP has no account recovery, email verification, multi-receiver mixing, or persistent audit UI.
