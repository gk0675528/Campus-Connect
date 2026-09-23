import uuid
from pathlib import Path

from fastapi.testclient import TestClient

from main import app


def test_runtime_requirements_include_db_and_email_runtime_support():
    req_path = Path(__file__).resolve().parents[1] / "backend" / "requirements.txt"
    requirements = req_path.read_text(encoding="utf-8")

    assert "aiosqlite" in requirements.lower()
    assert "email-validator" in requirements.lower()


def test_register_and_login_persist_user():
    with TestClient(app) as client:
        unique = uuid.uuid4().hex[:8]
        email = f"auth-{unique}@example.com"
        username = f"auth{unique}"

        register_response = client.post(
            "/api/auth/register",
            json={
                "email": email,
                "username": username,
                "password": "secret123",
                "first_name": "Auth",
                "last_name": "Smoke",
            },
        )
        assert register_response.status_code == 201, register_response.text

        login_response = client.post(
            "/api/auth/login",
            json={"email": email, "password": "secret123"},
        )
        assert login_response.status_code == 200, login_response.text

        payload = login_response.json()
        assert payload["access_token"]
        assert payload["refresh_token"]
        assert payload["token_type"] == "bearer"
