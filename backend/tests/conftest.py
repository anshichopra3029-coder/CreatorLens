from fastapi.testclient import TestClient
import pytest

from app.core.config import settings
from app.main import app
from app.services.auth_store import latest_email_body


class SessionClient(TestClient):
    csrf = ""

    def request(self, method: str, url: str, **kwargs: object):
        headers = dict(kwargs.pop("headers", None) or {})
        if method.upper() not in {"GET", "HEAD", "OPTIONS"} and self.csrf:
            headers.setdefault("X-CSRF-Token", self.csrf)
        kwargs["headers"] = headers
        return super().request(method, url, **kwargs)


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    from app.services.auth import _ATTEMPTS

    _ATTEMPTS.clear()
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    monkeypatch.setattr(settings, "gemini_api_key", "")
    monkeypatch.setattr(settings, "app_env", "test")
    return tmp_path


@pytest.fixture
def client():
    with SessionClient(app) as test_client:
        yield test_client


def login_verified(client: SessionClient, email: str, name: str = "Ada Creator") -> dict:
    password = "correct-horse-1"
    created = client.post("/api/auth/register", json={"name": name, "email": email, "password": password})
    assert created.status_code == 202
    body = latest_email_body(email, "verify")
    assert body is not None
    token = body.split("token=", 1)[1].strip()
    verified = client.post("/api/auth/verify", json={"token": token})
    assert verified.status_code == 204
    signed_in = client.post("/api/auth/login", json={"email": email, "password": password})
    assert signed_in.status_code == 200
    client.csrf = signed_in.json()["csrf_token"]
    return signed_in.json()


@pytest.fixture
def member(client, isolated):
    from app.services.auth import _ATTEMPTS

    _ATTEMPTS.clear()
    login_verified(client, "ada@example.com")
    return client
