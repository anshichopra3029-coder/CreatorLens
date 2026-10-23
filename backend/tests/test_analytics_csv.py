"""Analytics CSV validation, metrics, and saved forecasts."""

import json
from types import SimpleNamespace

import pytest

from app.core.config import settings

DAILY = "\n".join(
    ["video_id,title,date,views,likes,comments"]
    + [f"abc,Fold,{date},{(index + 1) * 10},{(index + 1)},1" for index, date in enumerate(
        [f"2026-01-{day:02d}" for day in range(1, 11)]
    )]
)


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    monkeypatch.setattr(settings, "gemini_api_key", "")
    monkeypatch.setattr(settings, "max_upload_rows", 20000)
    return tmp_path


def test_missing_metric_column_is_rejected(client, isolated):
    response = client.post(
        "/api/analytics/preview",
        files={"file": ("notes.csv", b"video_id,title\nabc,Fold\n", "text/csv")},
    )
    assert response.status_code == 400
    assert "views" in response.json()["detail"]


def test_duplicate_date_is_rejected(member, isolated):
    raw = b"video_id,date,views\nabc,2026-01-01,10\nabc,2026-01-01,12\n"
    response = member.post("/api/analytics/analyses", files={"file": ("dup.csv", raw, "text/csv")})
    assert response.status_code == 400
    assert "already recorded" in response.json()["detail"]
    assert member.get("/api/analytics/analyses").json()["count"] == 0


def test_latest_row_engagement_and_forecast_are_saved(member, isolated):
    response = member.post(
        "/api/analytics/analyses",
        files={"file": ("daily.csv", DAILY.encode(), "text/csv")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["summary"]["video_count"] == 1
    assert body["summary"]["total_latest_views"] == 100
    assert body["summary"]["average_engagement_rate"] == 11.0
    assert body["summary"]["engagement_formula"] == "(likes + comments) / views * 100"
    assert body["prediction"]["trained"] is True
    assert body["prediction"]["method"] == "holt_linear"
    assert body["narrative"] is None
    saved = member.get(f"/api/analytics/analyses/{body['id']}")
    assert saved.status_code == 200
    assert saved.json()["prediction"]["trained"] is True


def test_shares_change_the_formula(isolated):
    from app.services.analytics_analysis import summarize
    from app.services.analytics_csv import parse_analytics_csv

    raw = b"video_id,views,likes,comments,shares\nabc,100,10,5,5\n"
    parsed = parse_analytics_csv(raw, "shares.csv", max_rows=100)
    summary = summarize(parsed)
    assert summary.videos[0].engagement_rate == 20.0
    assert "shares" in summary.engagement_formula


def test_blank_counts_are_not_zero(isolated):
    from app.services.analytics_csv import parse_analytics_csv

    raw = b"video_id,views,likes,comments\nabc,80,,\n"
    parsed = parse_analytics_csv(raw, "partial.csv", max_rows=100)
    assert parsed.observations[0].views == 80
    assert parsed.observations[0].likes is None
    assert parsed.observations[0].comments is None


def test_gemini_failure_keeps_the_metrics(isolated):
    settings.gemini_api_key = "test-gemini-key"

    class Broken:
        def create(self, **kwargs: object) -> SimpleNamespace:
            raise RuntimeError("quota")

    class Client:
        interactions = Broken()

    from app.services.analytics_analysis import analyze_upload

    saved = analyze_upload(DAILY.encode(), "daily.csv", user_id="test-user", client=Client())
    assert saved.summary.total_latest_views == 100
    assert saved.narrative_status == "unavailable"
    assert saved.prediction.trained is True
    assert "test-gemini-key" not in saved.model_dump_json()


def test_gemini_narrative_uses_the_schema(isolated):
    settings.gemini_api_key = "test-gemini-key"
    settings.gemini_model = "gemini-3.8-flash"

    class Gemini:
        def create(self, **kwargs: object) -> SimpleNamespace:
            payload = {
                "executive_summary": "Views rose across the supplied dates.",
                "strengths": ["Views increased on every dated row."],
                "weaknesses": ["Comments stay at 1."],
                "recommendations": ["Keep the daily posting cadence shown in the file."],
                "content_ideas": ["A follow-up", "A shorter cut", "A materials list"],
                "next_actions": ["Export another week before trusting the line."],
                "additional_data": "Impressions were not in the file.",
                "limitations": "The file does not show why views changed.",
            }
            assert kwargs["model"] == "gemini-3.8-flash"
            return SimpleNamespace(output_text=json.dumps(payload))

    class Client:
        interactions = Gemini()

    from app.services.analytics_analysis import analyze_upload

    saved = analyze_upload(DAILY.encode(), "daily.csv", user_id="test-user", client=Client())
    assert saved.narrative is not None
    assert saved.narrative.executive_summary.startswith("Views rose")
    assert len(saved.narrative.content_ideas) == 3
