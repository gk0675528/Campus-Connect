import asyncio
import uuid
from datetime import timedelta
from pathlib import Path

from fastapi.testclient import TestClient
import pytest
from pydantic import ValidationError

from main import app
from core.config.security import create_access_token
from core.config.settings import Settings
from core.config import redis as redis_config


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


def test_refresh_token_cannot_access_protected_endpoint():
    with TestClient(app) as client:
        unique = uuid.uuid4().hex[:8]
        register_response = client.post(
            "/api/auth/register",
            json={
                "email": f"refresh-{unique}@example.com",
                "username": f"refresh{unique}",
                "password": "secret123",
                "first_name": "Refresh",
                "last_name": "Token",
            },
        )
        assert register_response.status_code == 201

        login_response = client.post(
            "/api/auth/login",
            json={
                "email": f"refresh-{unique}@example.com",
                "password": "secret123",
            },
        )
        refresh_token = login_response.json()["refresh_token"]

        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {refresh_token}"},
        )

        assert response.status_code == 401


def test_access_token_protects_current_user_endpoint():
    with TestClient(app) as client:
        unique = uuid.uuid4().hex[:8]
        email = f"protected-{unique}@example.com"
        register_response = client.post(
            "/api/auth/register",
            json={
                "email": email,
                "username": f"protected{unique}",
                "password": "secret123",
                "first_name": "Protected",
                "last_name": "Route",
            },
        )
        assert register_response.status_code == 201, register_response.text

        login_response = client.post(
            "/api/auth/login",
            json={"email": email, "password": "secret123"},
        )
        assert login_response.status_code == 200, login_response.text
        access_token = login_response.json()["access_token"]
        user_id = register_response.json()["id"]

        valid_response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert valid_response.status_code == 200, valid_response.text
        assert valid_response.json()["id"] == user_id

        assert client.get("/api/auth/me").status_code == 401
        assert client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid-token"},
        ).status_code == 401

        expired_token = create_access_token(
            {"sub": user_id},
            expires_delta=timedelta(seconds=-1),
        )
        assert client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"},
        ).status_code == 401


def test_registration_rejects_weak_password():
    with TestClient(app) as client:
        response = client.post(
            "/api/auth/register",
            json={
                "email": "weak-password@example.com",
                "username": "weakpassword",
                "password": "short",
                "first_name": "Weak",
                "last_name": "Password",
            },
        )

        assert response.status_code == 422


def test_production_requires_all_runtime_environment_variables(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@db.example/pathzeo")
    monkeypatch.setenv("REDIS_URL", "rediss://user:pass@redis.example/0")
    monkeypatch.setenv("SECRET_KEY", "t" * 64)
    monkeypatch.delenv("CORS_ORIGINS", raising=False)

    with pytest.raises(ValidationError, match="CORS_ORIGINS"):
        Settings()


def test_production_rejects_wildcard_cors_origin(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@db.example/pathzeo")
    monkeypatch.setenv("REDIS_URL", "rediss://user:pass@redis.example/0")
    monkeypatch.setenv("SECRET_KEY", "t" * 64)
    monkeypatch.setenv("CORS_ORIGINS", "*")

    with pytest.raises(ValidationError, match="explicit production origins"):
        Settings()


def test_local_cors_preflight_allows_frontend_origin():
    with TestClient(app) as client:
        response = client.options(
            "/api/auth/me",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "authorization",
            },
        )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
    assert response.headers["access-control-allow-credentials"] == "true"


def test_production_does_not_fall_back_when_redis_is_unavailable(monkeypatch):
    class UnavailableRedis:
        async def ping(self):
            raise ConnectionError("Redis unavailable")

    monkeypatch.setattr(redis_config.settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(redis_config, "redis_client", None)
    monkeypatch.setattr(
        redis_config.aioredis,
        "from_url",
        lambda *args, **kwargs: UnavailableRedis(),
    )

    with pytest.raises(RuntimeError, match="Redis is required in production"):
        asyncio.run(redis_config.connect_redis())
