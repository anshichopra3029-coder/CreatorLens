"""View history import, snapshot collection, and the Show forecast workflow.

Metadata extraction uses a stand-in. The CSV rows below are test data written for these checks.
"""

from datetime import datetime, timedelta, timezone

import pytest

from app.core.config import settings
from app.services.view_history import ViewHistoryError, record_snapshot
from app.services.youtube_analysis import analyze_video
from app.services.youtube_store import stored_observations

VIDEO_ID = "dQw4w9WgXcQ"
WATCH = f"https://www.youtube.com/watch?v={VIDEO_ID}"


def _info(views: int = 1000) -> dict:
    return {
        "id": VIDEO_ID,
        "title": "How to fold a paper crane",
        "description": "A short folding lesson.",
        "channel": "Paper Desk",
        "channel_id": "UCPaperDesk1",
        "thumbnail": "https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg",
        "upload_date": "20260102",
        "duration": 252,
        "view_count": views,
        "like_count": 50,
        "comment_count": 10,
        "availability": "public",
    }


@pytest.fixture
def saved(client, isolated, monkeypatch):
    monkeypatch.setattr(settings, "youtube_cache_seconds", 21600)
    return analyze_video(WATCH, user_id="local", extractor=lambda url: _info())


def _csv(rows: list[str], header: str = "observed_at,views") -> bytes:
    return ("\n".join([header, *rows]) + "\n").encode("utf-8")


def _upload(client, payload: bytes, name: str = "history.csv", video_id: str = VIDEO_ID):
    return client.post(f"/api/youtube/videos/{video_id}/observations", files={"file": (name, payload, "text/csv")})


def _daily_rows(days: int = 11, start_views: int = 100, per_day: int = 80) -> list[str]:
    now = datetime.now(timezone.utc).replace(microsecond=0, minute=0, second=0)
    return [
        f"{(now - timedelta(days=days - index)).isoformat()},{start_views + per_day * index}"
        for index in range(days)
    ]


def test_one_saved_snapshot_explains_that_more_history_is_needed(client, saved):
    listed = client.get("/api/youtube/videos").json()
    assert listed["count"] == 1
    assert listed["videos"][0]["observations"] == 1
    body = client.get(f"/api/youtube/videos/{VIDEO_ID}/forecast").json()
    assert body["prediction"]["status"] == "insufficient_data"
    assert body["prediction"]["latest_views"] == 1000
    assert body["prediction"]["latest_observed_at"] == saved.created_at
    assert [point["views"] for point in body["prediction"]["series"]] == [1000]
    assert [item["supported"] for item in body["prediction"]["horizons"]] == [False, False, False]
    assert all(item["predicted_views"] is None for item in body["prediction"]["horizons"])
    assert "one recorded view count" in body["prediction"]["message"]
    assert "import dated" in body["guidance"]


def test_invalid_csv_files_are_rejected_without_importing(client, saved):
    cases = [
        (_csv(["2026-10-01,100"], header="date_only"), "Missing column"),
            (_csv(["yesterday,100"]), "isn't a date we can read"),
        (_csv(["2026-10-01,-5"]), "whole number"),
        (_csv(["2026-10-01,12.5"]), "whole number"),
        (_csv(["2026-10-01,"]), "whole number"),
        (_csv(["2026-10-01,100", "2026-10-01T00:00:00Z,120"]), "repeats row 2"),
        (_csv(["2099-01-01,100"]), "in the future"),
        (_csv(["abcdefghijk,2026-10-01,100"], header="video_id,observed_at,views"), "is not dQw4w9WgXcQ"),
        (_csv([]), "no data rows"),
    ]
    for payload, expected in cases:
        response = _upload(client, payload)
        assert response.status_code == 422, (expected, response.text)
        assert expected in response.json()["detail"]
    assert _upload(client, b"").status_code == 400
    assert _upload(client, _csv(["2026-10-01,100"]), name="history.txt").status_code == 415
    assert stored_observations(VIDEO_ID, "local") == []


def test_incorrect_video_ids_return_clear_errors(client, saved):
    assert client.get("/api/youtube/videos/bad!id/forecast").status_code == 400
    missing = client.get("/api/youtube/videos/AAAAAAAAAAA/forecast")
    assert missing.status_code == 404
    assert "Analyze it" in missing.json()["detail"]
    assert _upload(client, _csv(["2026-10-01,100"]), video_id="AAAAAAAAAAA").status_code == 404


def test_valid_history_import_drives_show_forecast(client, saved):
    imported = _upload(client, _csv(_daily_rows()))
    assert imported.status_code == 200, imported.text
    result = imported.json()
    assert result["inserted"] == 11
    assert result["skipped_existing"] == 0

    body = client.get(f"/api/youtube/videos/{VIDEO_ID}/forecast").json()
    prediction = body["prediction"]
    assert [item["source"] for item in body["observations"]].count("csv") == 11
    assert prediction["status"] == "forecast"
    assert prediction["selection"] == "evaluated"
    assert prediction["method"] == "holt_linear"
    assert prediction["latest_views"] == 1000
    holt, naive = prediction["metrics"]
    assert holt["mae"] < naive["mae"]
    horizons = {item["label"]: item for item in prediction["horizons"]}
    assert set(horizons) == {"24 hours", "3 days", "7 days"}
    assert all(item["supported"] for item in horizons.values())
    assert horizons["24 hours"]["predicted_views"] > 1000
    assert horizons["7 days"]["predicted_views"] > horizons["24 hours"]["predicted_views"]
    assert horizons["24 hours"]["added_views"] == horizons["24 hours"]["predicted_views"] - 1000
    predicted_points = [point for point in prediction["series"] if point["views"] is None]
    assert len(predicted_points) == 3

    again = _upload(client, _csv(_daily_rows()))
    assert again.json()["inserted"] == 0
    assert again.json()["skipped_existing"] == 11


def test_short_history_import_is_provisional(client, saved):
    imported = _upload(client, _csv(_daily_rows(days=3)))
    assert imported.status_code == 200
    prediction = imported.json()["forecast"]["prediction"]
    assert prediction["selection"] == "provisional"
    assert prediction["method"] == "naive_last_value"
    assert all(metric["available"] is False for metric in prediction["metrics"])


def test_snapshots_wait_for_real_change_and_record_a_timestamp(client, saved):
    with pytest.raises(ViewHistoryError) as too_soon:
        record_snapshot(VIDEO_ID, "local", extractor=lambda url: _info(1050))
    assert too_soon.value.status_code == 429
    later = datetime.now(timezone.utc) + timedelta(hours=2)
    result = record_snapshot(VIDEO_ID, "local", extractor=lambda url: _info(1100), now=later)
    assert result.observations[-1].views == 1100
    assert result.observations[-1].source == "snapshot"
    assert stored_observations(VIDEO_ID, "local")[0][1] == 1100


def test_http_snapshot_too_soon_returns_429(client, saved, monkeypatch):
    monkeypatch.setattr("app.services.youtube_client._extract", lambda url: _info(1050))
    response = client.post(f"/api/youtube/videos/{VIDEO_ID}/snapshot")
    assert response.status_code == 429


def test_cached_reanalysis_does_not_save_a_duplicate(client, saved):
    again = analyze_video(WATCH, user_id="local", extractor=lambda url: _info())
    assert again.id == saved.id
    assert client.get("/api/youtube/analyses").json()["count"] == 1
    fresh = analyze_video(WATCH, user_id="local", extractor=lambda url: _info(1200), use_cache=False)
    assert fresh.id != saved.id
    assert client.get("/api/youtube/analyses").json()["count"] == 2
    listed = client.get("/api/youtube/videos").json()
    assert listed["count"] == 1
    assert listed["videos"][0]["analyses"] == 2
    assert listed["videos"][0]["latest_views"] == 1200
