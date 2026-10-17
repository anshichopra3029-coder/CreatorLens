"""Analytics CSV validation, metrics, persistence, and mocked Gemini."""

import json
from types import SimpleNamespace

import pytest

from app.core.config import settings

SECRET = "test-gemini-key"


def _csv(rows: list[str]) -> bytes:
    return ("video_id,title,date,views,likes,comments\n" + "\n".join(rows) + "\n").encode()


def _daily() -> bytes:
    rows = [f"crane,Fold a crane,2026-01-{day:02d},{day * 10},{day},1" for day in range(1, 11)]
    return _csv(rows)


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    monkeypatch.setattr(settings, "gemini_api_key", "")
    monkeypatch.setattr(settings, "gemini_model", "gemini-3.8-flash")
    return tmp_path


def test_missing_metric_column_is_rejected(client, isolated):
    response = client.post(
        "/api/analytics/preview",
        files={"file": ("notes.csv", b"video_id,title\nabc,Hello\n", "text/csv")},
    )
    assert response.status_code == 400
    assert "views" in response.json()["detail"]


def test_duplicate_date_is_rejected(member, isolated):
    raw = _csv(
        [
            "crane,Fold a crane,2026-01-01,10,1,1",
            "crane,Fold a crane,2026-01-01,12,1,1",
        ]
    )
    response = member.post("/api/analytics/analyses", files={"file": ("views.csv", raw, "text/csv")})
    assert response.status_code == 400
    assert "already recorded" in response.json()["detail"]
    assert member.get("/api/analytics/analyses").json()["count"] == 0


def test_non_csv_is_rejected(client, isolated):
    response = client.post(
        "/api/analytics/preview",
        files={"file": ("notes.txt", b"video_id,views\n", "text/plain")},
    )
    assert response.status_code == 400


def test_blank_likes_stay_missing_and_history_is_saved(member, isolated):
    raw = b"video_id,title,date,views\ncrane,Fold a crane,2026-01-01,80\n"
    response = member.post("/api/analytics/analyses", files={"file": ("views.csv", raw, "text/csv")})
    assert response.status_code == 200
    body = response.json()
    assert body["summary"]["videos"][0]["views"] == 80
    assert body["summary"]["videos"][0]["likes"] is None
    assert body["summary"]["average_engagement_rate"] is None
    assert body["prediction"]["trained"] is False
    assert body["file_saved"] is True
    again = member.get(f"/api/analytics/analyses/{body['id']}")
    assert again.status_code == 200
    assert again.json()["summary"]["total_latest_views"] == 80


def test_daily_file_trains_a_forecast_and_survives_gemini_failure(member, isolated):
    settings.gemini_api_key = SECRET

    class _Broken:
        def create(self, **kwargs: object) -> SimpleNamespace:
            raise RuntimeError("rate limit")

    class _Client:
        def __init__(self) -> None:
            self.interactions = _Broken()

    from app.services.analytics_analysis import analyze_upload

    user_id = member.get("/api/auth/session").json()["user"]["id"]
    saved = analyze_upload(_daily(), "daily.csv", user_id=user_id, client=_Client())
    assert saved.summary.average_engagement_rate == 11.0
    assert saved.prediction.trained is True
    assert saved.prediction.method == "linear_regression"
    assert saved.prediction.holdout_start == "2026-01-09"
    assert saved.narrative_status == "unavailable"
    assert saved.narrative is None
    assert SECRET not in saved.model_dump_json()
    listed = member.get("/api/analytics/analyses")
    assert listed.json()["count"] == 1
    assert listed.json()["analyses"][0]["prediction_eligible"] is True


def test_gemini_narrative_uses_the_schema(isolated):
    settings.gemini_api_key = SECRET
    payload = {
        "executive_summary": "Views rose across the ten dated rows.",
        "strengths": ["The series has a view count on every day."],
        "weaknesses": ["Likes stay small relative to views."],
        "recommendations": ["Keep the daily count and add a shares column if you have one."],
        "content_ideas": ["A follow-up fold", "A shorter version", "A materials list"],
        "next_actions": ["Export another week", "Add impressions if the analytics export has them"],
        "additional_data": "Impressions and click-through rate are absent from this file.",
        "limitations": "Based only on the uploaded counts.",
    }

    class _Gemini:
        def create(self, **kwargs: object) -> SimpleNamespace:
            assert kwargs["model"] == "gemini-3.8-flash"
            return SimpleNamespace(output_text=json.dumps(payload))

    class _Client:
        def __init__(self) -> None:
            self.interactions = _Gemini()

    from app.services.analytics_analysis import analyze_upload

    saved = analyze_upload(_daily(), "daily.csv", user_id="test-user", client=_Client())
    assert saved.narrative is not None
    assert saved.narrative.executive_summary.startswith("Views rose")
    assert len(saved.narrative.content_ideas) == 3
    assert SECRET not in saved.model_dump_json()
