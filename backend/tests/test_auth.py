"""Account, verification, and ownership tests."""

from app.services.auth_store import latest_email_body
from tests.conftest import login_verified


def test_saved_analyses_are_readable_without_signing_in(client, isolated):
    listed = client.get("/api/youtube/analyses")
    assert listed.status_code == 200
    assert listed.json()["count"] == 0


def test_duplicate_email_and_bad_password_are_rejected(client, isolated):
    login_verified(client, "ada@example.com")
    duplicate = client.post(
        "/api/auth/register",
        json={"name": "Ada", "email": "ada@example.com", "password": "correct-horse-1"},
    )
    assert duplicate.status_code == 409
    client.csrf = ""
    wrong = client.post("/api/auth/login", json={"email": "ada@example.com", "password": "wrong-password-1"})
    assert wrong.status_code == 401


def test_expired_verification_link_is_rejected(client, isolated, monkeypatch):
    client.post(
        "/api/auth/register",
        json={"name": "Ada", "email": "ada@example.com", "password": "correct-horse-1"},
    )
    body = latest_email_body("ada@example.com", "verify")
    assert body is not None
    token = body.split("token=", 1)[1].strip()
    monkeypatch.setattr("app.services.auth_store._now", lambda: __import__("datetime").datetime(2099, 1, 1, tzinfo=__import__("datetime").timezone.utc))
    response = client.post("/api/auth/verify", json={"token": token})
    assert response.status_code == 400


def test_saved_analysis_is_readable_without_a_session(client, isolated, monkeypatch):
    from app.services.youtube_analysis import analyze_video

    login_verified(client, "ada@example.com", "Ada")
    ada = client.get("/api/auth/session").json()["user"]["id"]
    monkeypatch.setattr("app.services.youtube_client._extract", lambda url: {
        "id": "dQw4w9WgXcQ",
        "title": "Ada video",
        "description": "A description.",
        "channel": "Ada",
        "channel_id": "UCAda",
        "thumbnail": "https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg",
        "upload_date": "20260102",
        "duration": 20,
        "view_count": 10,
        "like_count": 2,
        "comment_count": 1,
        "availability": "public",
    })
    saved = analyze_video("https://www.youtube.com/watch?v=dQw4w9WgXcQ", user_id=ada)
    assert client.get(f"/api/youtube/analyses/{saved.id}").status_code == 200

    anonymous = client.__class__(client.app)
    visible = anonymous.get(f"/api/youtube/analyses/{saved.id}")
    assert visible.status_code == 200
    assert anonymous.get("/api/youtube/analyses").json()["count"] == 1
    assert "Ada video" in visible.text


def test_logout_and_password_reset_end_the_session(client, isolated):
    login_verified(client, "ada@example.com")
    assert client.get("/api/account").status_code == 200
    assert client.post("/api/auth/logout").status_code == 204
    assert client.get("/api/account").status_code == 200
    forgot = client.post("/api/auth/forgot", json={"email": "ada@example.com"})
    assert forgot.status_code == 202
    body = latest_email_body("ada@example.com", "reset")
    assert body is not None
    token = body.split("token=", 1)[1].strip()
    reset = client.post("/api/auth/reset", json={"token": token, "password": "new-password-2"})
    assert reset.status_code == 204
    signed_in = client.post("/api/auth/login", json={"email": "ada@example.com", "password": "new-password-2"})
    assert signed_in.status_code == 200
