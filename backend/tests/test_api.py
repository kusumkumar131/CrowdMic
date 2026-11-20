from fastapi.testclient import TestClient
from app.main import fastapi_app

client = TestClient(fastapi_app)

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["app"] == "CrowdMic API"
    assert data["status"] == "online"

def test_register_and_login():
    # Register student
    reg_payload = {
        "name": "Test Student",
        "email": "student_test@example.com",
        "password": "password123",
        "role": "student"
    }
    response = client.post("/auth/register", json=reg_payload)
    assert response.status_code == 200
    data = response.json()
    assert "token" in data
    assert data["user"]["email"] == "student_test@example.com"

    # Login student
    login_payload = {
        "email": "student_test@example.com",
        "password": "password123"
    }
    login_res = client.post("/auth/login", json=login_payload)
    assert login_res.status_code == 200
    assert "token" in login_res.json()
