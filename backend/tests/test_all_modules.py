import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from app.main import fastapi_app
from app.services.ai_service import classify_question, compute_jaccard_similarity, detect_duplicates_and_prioritize
from app.websocket.socket_manager import set_active_speaker, get_active_speaker, active_sockets

client = TestClient(fastapi_app)

# Helper fixture / functions
def get_auth_header(role="moderator", email_suffix=""):
    email = f"{role}_{email_suffix}@test.com" if email_suffix else f"{role}_fixture@test.com"
    reg_res = client.post("/auth/register", json={
        "name": f"Test {role.capitalize()}",
        "email": email,
        "password": "password123",
        "role": role
    })
    if reg_res.status_code == 200:
        token = reg_res.json()["token"]
    else:
        login_res = client.post("/auth/login", json={"email": email, "password": "password123"})
        token = login_res.json()["token"]
    return {"Authorization": f"Bearer {token}"}

# ----------------- 1. AUTH MODULE -----------------
def test_auth_registration_and_login():
    email = f"user_{datetime.utcnow().timestamp()}@test.com"
    # Registration
    reg = client.post("/auth/register", json={
        "name": "Alice Student",
        "email": email,
        "password": "securepassword",
        "role": "student"
    })
    assert reg.status_code == 200
    reg_data = reg.json()
    assert "token" in reg_data
    assert reg_data["user"]["email"] == email.lower()
    assert reg_data["user"]["role"] == "student"

    # Duplicate registration should fail
    dup = client.post("/auth/register", json={
        "name": "Alice Student",
        "email": email,
        "password": "securepassword",
        "role": "student"
    })
    assert dup.status_code == 400

    # Successful login
    login = client.post("/auth/login", json={"email": email, "password": "securepassword"})
    assert login.status_code == 200
    assert "token" in login.json()

    # Invalid password login
    bad_login = client.post("/auth/login", json={"email": email, "password": "wrongpassword"})
    assert bad_login.status_code == 401

    # /auth/me with valid token
    headers = {"Authorization": f"Bearer {login.json()['token']}"}
    me = client.get("/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["email"] == email.lower()

    # /auth/me without token
    unauth = client.get("/auth/me")
    assert unauth.status_code == 401

# ----------------- 2. SESSIONS MODULE -----------------
def test_session_lifecycle():
    mod_headers = get_auth_header(role="moderator", email_suffix="sess_mod")
    stud_headers = get_auth_header(role="student", email_suffix="sess_stu")

    # Student cannot create session
    denied = client.post("/sessions", headers=stud_headers, json={
        "companyName": "Google",
        "title": "Tech Talk 2026",
        "speakerTimerDuration": 60
    })
    assert denied.status_code == 403

    # Moderator creates session
    created = client.post("/sessions", headers=mod_headers, json={
        "companyName": "DeepMind",
        "title": "AGI Seminar 2026",
        "speakerTimerDuration": 90,
        "allowProfMic": True
    })
    assert created.status_code == 200
    session_data = created.json()
    session_id = session_data["id"]
    session_code = session_data["sessionCode"]
    assert session_data["status"] == "active"
    assert session_data["speakerTimerDuration"] == 90

    # Retrieve session by Code
    by_code = client.get(f"/sessions/{session_code}", headers=stud_headers)
    assert by_code.status_code == 200
    assert by_code.json()["id"] == session_id

    # Retrieve session by ID
    by_id = client.get(f"/sessions/{session_id}", headers=stud_headers)
    assert by_id.status_code == 200
    assert by_id.json()["companyName"] == "DeepMind"

    # List active sessions
    active_list = client.get("/sessions", headers=stud_headers)
    assert active_list.status_code == 200
    assert any(s["id"] == session_id for s in active_list.json())

    # Moderator updates status to paused
    paused = client.patch(f"/sessions/{session_id}/status", headers=mod_headers, json={"status": "paused"})
    assert paused.status_code == 200
    assert paused.json()["status"] == "paused"

    # Moderator ends session
    ended = client.patch(f"/sessions/{session_id}/status", headers=mod_headers, json={"status": "ended"})
    assert ended.status_code == 200
    assert ended.json()["status"] == "ended"

# ----------------- 3. QUEUE MODULE -----------------
def test_queue_workflow():
    mod_headers = get_auth_header(role="moderator", email_suffix="q_mod")
    stu1_headers = get_auth_header(role="student", email_suffix="q_stu1")
    stu2_headers = get_auth_header(role="student", email_suffix="q_stu2")

    # Create active session
    sess_res = client.post("/sessions", headers=mod_headers, json={
        "companyName": "Tesla",
        "title": "Robotics Q&A"
    })
    session_id = sess_res.json()["id"]

    # Student 1 joins queue
    q1 = client.post(f"/sessions/{session_id}/queue", headers=stu1_headers)
    assert q1.status_code == 200
    entry1 = q1.json()
    assert entry1["position"] == 1
    assert entry1["status"] == "next"

    # Student 2 joins queue
    q2 = client.post(f"/sessions/{session_id}/queue", headers=stu2_headers)
    assert q2.status_code == 200
    entry2 = q2.json()
    assert entry2["position"] == 2
    assert entry2["status"] == "waiting"

    # Duplicate entry by Student 1 fails
    dup_q = client.post(f"/sessions/{session_id}/queue", headers=stu1_headers)
    assert dup_q.status_code == 400

    # Moderator trying to join queue is rejected
    mod_q = client.post(f"/sessions/{session_id}/queue", headers=mod_headers)
    assert mod_q.status_code == 403

    # View queue
    queue_list = client.get(f"/sessions/{session_id}/queue", headers=stu1_headers)
    assert queue_list.status_code == 200
    assert len(queue_list.json()) == 2

    # Student 1 cancels hand / leaves queue
    leave_res = client.delete(f"/sessions/{session_id}/queue", headers=stu1_headers)
    assert leave_res.status_code == 200

    # Queue re-evaluated: Student 2 becomes #1 and 'next'
    updated_queue = client.get(f"/sessions/{session_id}/queue", headers=stu2_headers)
    assert updated_queue.status_code == 200
    entries = updated_queue.json()
    assert len(entries) == 1
    assert entries[0]["position"] == 1
    assert entries[0]["status"] == "next"

# ----------------- 4. AI SERVICE & QUESTIONS MODULE -----------------
def test_ai_classification_and_similarity():
    # Unit tests for classification
    assert classify_question("What programming languages and react framework do you use?") == "Technical"
    assert classify_question("Can you describe the HR interview selection rounds?") == "HR"
    assert classify_question("Is there a stipend for the summer internship project?") == "Internship"
    assert classify_question("What is the career growth and mentorship path?") == "Career"
    assert classify_question("Where is the new office location and headquarters?") == "Company"
    assert classify_question("What is the average CTC salary and bonus allowance?") == "Salary"
    assert classify_question("Is work from home or hybrid culture allowed?") == "Work Culture"
    assert classify_question("Hello, nice to meet everyone!") == "General"

    # Similarity checks
    sim_exact = compute_jaccard_similarity("what is the ctc salary package", "what is the ctc salary package")
    assert sim_exact == 1.0

    sim_partial = compute_jaccard_similarity("what is the salary package", "what is the base salary compensation")
    assert 0.0 < sim_partial < 1.0

    # Duplicate detection
    existing = [{"text": "What is the expected stipend for summer internship?"}]
    is_dup, score, priority, cat = detect_duplicates_and_prioritize("What is the stipend for the summer internship project?", existing)
    assert is_dup is True
    assert cat == "Internship"
    assert priority > 1.0

def test_questions_api_and_moderation():
    mod_headers = get_auth_header(role="moderator", email_suffix="qa_mod")
    stu_headers = get_auth_header(role="student", email_suffix="qa_stu")

    sess_res = client.post("/sessions", headers=mod_headers, json={
        "companyName": "Microsoft",
        "title": "Campus Hiring"
    })
    session_id = sess_res.json()["id"]

    # Post initial question
    q1 = client.post(f"/sessions/{session_id}/questions", headers=stu_headers, json={
        "text": "What tech stack and python framework does the team use?"
    })
    assert q1.status_code == 200
    q1_data = q1.json()
    assert q1_data["category"] == "Technical"
    assert q1_data["isDuplicate"] is False
    assert q1_data["status"] == "active"
    q1_id = q1_data["id"]

    # Post duplicate question
    q2 = client.post(f"/sessions/{session_id}/questions", headers=stu_headers, json={
        "text": "What python tech stack and framework does your team use?"
    })
    assert q2.status_code == 200
    q2_data = q2.json()
    assert q2_data["isDuplicate"] is True

    # List questions (sorted by priority)
    q_list = client.get(f"/sessions/{session_id}/questions", headers=stu_headers)
    assert q_list.status_code == 200
    assert len(q_list.json()) == 2

    # Moderator flags question
    flag_res = client.post(f"/sessions/{session_id}/questions/{q1_id}/flag", headers=mod_headers)
    assert flag_res.status_code == 200

    # Student cannot flag question
    denied = client.post(f"/sessions/{session_id}/questions/{q1_id}/flag", headers=stu_headers)
    assert denied.status_code == 403

# ----------------- 5. ANALYTICS MODULE -----------------
def test_analytics_module():
    mod_headers = get_auth_header(role="moderator", email_suffix="an_mod")
    stu_headers = get_auth_header(role="student", email_suffix="an_stu")

    sess_res = client.post("/sessions", headers=mod_headers, json={
        "companyName": "Amazon",
        "title": "AWS Seminar"
    })
    session_id = sess_res.json()["id"]

    # Post questions in different categories
    client.post(f"/sessions/{session_id}/questions", headers=stu_headers, json={
        "text": "What is the base salary and bonus package?"
    })
    client.post(f"/sessions/{session_id}/questions", headers=stu_headers, json={
        "text": "How many rounds are in the HR interview?"
    })

    # Join queue
    client.post(f"/sessions/{session_id}/queue", headers=stu_headers)

    analytics = client.get(f"/sessions/{session_id}/analytics", headers=mod_headers)
    assert analytics.status_code == 200
    data = analytics.json()
    assert data["sessionId"] == session_id
    assert data["questionsAsked"] == 2
    assert "Salary" in data["categories"]
    assert "HR" in data["categories"]
    assert "averageSpeakingTime" in data
    assert "duplicateQuestions" in data
    assert data["totalParticipants"] >= 10

# ----------------- 6. ACTIVE SPEAKER TRACKING -----------------
def test_active_speaker_state():
    test_session = "sess_test_123"
    assert get_active_speaker(test_session) is None

    speaker = {"userId": "user1", "name": "Bob", "role": "student"}
    set_active_speaker(test_session, speaker)
    assert get_active_speaker(test_session) == speaker

    set_active_speaker(test_session, None)
    assert get_active_speaker(test_session) is None
