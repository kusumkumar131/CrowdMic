from fastapi.testclient import TestClient
from app.main import app

def test_health_returns_status():
    # Database may be absent in local development; health endpoint remains explicit about that.
    response=TestClient(app).get('/api/health')
    assert response.status_code in (200,503)
    assert response.json()['status'] in ('ok','degraded')

def test_frontend_loopback_origin_is_allowed():
    response=TestClient(app).options(
        '/api/auth/register',
        headers={
            'Origin':'http://127.0.0.1:5173',
            'Access-Control-Request-Method':'POST',
            'Access-Control-Request-Headers':'content-type',
        },
    )
    assert response.status_code == 200
    assert response.headers['access-control-allow-origin'] == 'http://127.0.0.1:5173'
