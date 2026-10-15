"""YouTube analysis tests. HTTP calls use a stand-in fetcher, not the live API."""

import json
from types import SimpleNamespace

import pytest

from app.core.config import settings
from app.services.youtube_analysis import analyze_video
from app.services.youtube_client import COMMENTS_URL, MISSING_YOUTUBE_KEY, VIDEOS_URL

VIDEO_ID = "dQw4w9WgXcQ"
WATCH = f"https://www.youtube.com/watch?v={VIDEO_ID}"
SECRET = "test-youtube-key"
GEMINI_SECRET = "test-gemini-key"


def _video_payload(statistics: dict | None = None, privacy: str = "public") -> dict:
    return {
        "items": [
            {
                "snippet": {
                    "title": "How to fold a paper crane",
                    "description": "A short folding lesson. Subscribe for the next fold.",
                    "channelTitle": "Paper Desk",
                    "publishedAt": "2026-01-02T00:00:00Z",
                    "thumbnails": {"high": {"url": "https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg"}},
                },
                "contentDetails": {"duration": "PT4M12S"},
                "statistics": statistics
                if statistics is not None
                else {"viewCount": "1000", "likeCount": "50", "commentCount": "10"},
                "status": {"privacyStatus": privacy},
            }
        ]
    }


class _Fetcher:
    def __init__(self, video: dict | None = None, comments: tuple[int, dict] | None = None) -> None:
        self.video = video if video is not None else _video_payload()
        self.comments = comments if comments is not None else (200, {"items": []})
        self.calls: list[str] = []

    def __call__(self, url: str, params: dict[str, str]) -> tuple[int, dict]:
        assert "key" not in params
        self.calls.append(url)
        if url == VIDEOS_URL:
            return 200, self.video
        if url == COMMENTS_URL:
            return self.comments
        raise AssertionError(url)


class _Gemini:
    def __init__(self) -> None:
        self.calls = 0

    def create(self, **kwargs: object) -> SimpleNamespace:
        self.calls += 1
        payload = {
            "executive_summary": "A paper-folding lesson.",
            "intended_audience": "Beginners who want a short craft video.",
            "main_topic": "Folding a paper crane",
            "subtopics": ["First folds"],
            "key_takeaways": ["The title states the task."],
            "hook_assessment": "The model tried to describe the opening.",
            "hook_evidence": [
                {"claim": "The opening is slow.", "evidence": "Imagined speech.", "source": "transcript"}
            ],
            "structure_notes": ["The description promises a lesson."],
            "title_assessment": "The title names the task.",
            "description_assessment": "The description mentions a subscribe line.",
            "cta_assessment": "The description asks viewers to subscribe.",
            "strengths": [
                {"claim": "The title is specific.", "evidence": "How to fold a paper crane", "source": "metadata"}
            ],
            "weaknesses": [],
            "recommendations": [
                {
                    "claim": "Keep the subscribe request, and add the result in the first line.",
                    "evidence": "Subscribe for the next fold.",
                    "source": "metadata",
                }
            ],
            "suggested_titles": ["Fold a paper crane in four minutes"],
            "thumbnail_concepts": ["Finished crane on a desk"],
            "suggested_description": "Watch a four-minute paper crane fold.",
            "content_ideas": ["A follow-up on the wings"],
            "limitations": "Based on the title and description.",
        }
        assert kwargs["model"] == "gemini-3.8-flash"
        return SimpleNamespace(output_text=json.dumps(payload))


class _Client:
    def __init__(self) -> None:
        self.interactions = _Gemini()


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    monkeypatch.setattr(settings, "youtube_api_key", "")
    monkeypatch.setattr(settings, "gemini_api_key", "")
    monkeypatch.setattr(settings, "gemini_model", "gemini-3.8-flash")
    monkeypatch.setattr(settings, "youtube_cache_seconds", 21600)
    return tmp_path


def test_supported_urls_extract_one_video_id():
    from app.services.youtube_urls import parse_youtube_video_id

    samples = [
        WATCH,
        f"https://youtu.be/{VIDEO_ID}",
        f"https://www.youtube.com/shorts/{VIDEO_ID}",
        f"https://www.youtube.com/embed/{VIDEO_ID}",
        f"https://m.youtube.com/watch?v={VIDEO_ID}&t=12s",
    ]
    assert {parse_youtube_video_id(sample) for sample in samples} == {VIDEO_ID}


def test_invalid_url_is_rejected(client, isolated):
    response = client.post("/api/youtube/preview", json={"url": "https://example.com/video"})
    assert response.status_code == 400
    assert "YouTube" in response.json()["detail"]
    assert client.get("/api/youtube/analyses").json()["count"] == 0


def test_missing_api_key_does_not_invent_statistics(client, isolated):
    response = client.post("/api/youtube/preview", json={"url": WATCH})
    assert response.status_code == 503
    assert response.json()["detail"] == MISSING_YOUTUBE_KEY
    assert "views" not in response.json()


def test_public_statistics_are_saved_and_reread(client, isolated):
    settings.youtube_api_key = SECRET
    fetcher = _Fetcher()
    from app.services.youtube_analysis import preview_video

    preview = preview_video(WATCH, fetcher=fetcher)
    assert preview.statistics.views == 1000
    assert preview.statistics.engagement_rate == 6.0
    assert preview.transcript.available is False
    assert preview.analytics.audience_retention is None
    assert preview.metadata.duration_seconds == 252
    saved = analyze_video(WATCH, fetcher=fetcher)
    assert saved.file_saved is True
    assert saved.statistics.engagement_rate == 6.0
    assert saved.narrative_status == "unavailable"
    assert saved.narrative is None
    assert SECRET not in saved.model_dump_json()
    again = client.get(f"/api/youtube/analyses/{saved.id}")
    assert again.status_code == 200
    assert again.json()["statistics"]["views"] == 1000
    assert again.json()["analytics"]["audience_retention"] is None
    listed = client.get("/api/youtube/analyses")
    assert listed.json()["count"] == 1
    assert fetcher.calls.count(VIDEOS_URL) == 1


def test_hidden_likes_do_not_become_zero(isolated):
    settings.youtube_api_key = SECRET
    fetcher = _Fetcher(video=_video_payload({"viewCount": "80"}))
    saved = analyze_video(WATCH, fetcher=fetcher)
    assert saved.statistics.views == 80
    assert saved.statistics.likes is None
    assert saved.statistics.likes_available is False
    assert saved.statistics.engagement_rate is None


def test_deleted_video_is_not_saved(isolated):
    settings.youtube_api_key = SECRET
    fetcher = _Fetcher(video={"items": []})
    from app.services.youtube_analysis import YoutubeProcessError

    with pytest.raises(YoutubeProcessError) as caught:
        analyze_video(WATCH, fetcher=fetcher)
    assert caught.value.status_code == 404
    from app.services.youtube_store import list_analyses

    assert list_analyses() == []


def test_disabled_comments_still_save_statistics(isolated):
    settings.youtube_api_key = SECRET
    fetcher = _Fetcher(comments=(403, {"error": {"errors": [{"reason": "commentsDisabled"}]}}))
    saved = analyze_video(WATCH, fetcher=fetcher)
    assert saved.comments_status == "disabled"
    assert saved.comments == []
    assert saved.statistics.views == 1000


def test_quota_error_is_explicit(isolated):
    settings.youtube_api_key = SECRET

    def fetcher(url: str, params: dict[str, str]) -> tuple[int, dict]:
        return 403, {"error": {"errors": [{"reason": "quotaExceeded"}]}}

    from app.services.youtube_analysis import YoutubeProcessError

    with pytest.raises(YoutubeProcessError) as caught:
        analyze_video(WATCH, fetcher=fetcher)
    assert caught.value.status_code == 429


def test_gemini_narrative_drops_transcript_claims(isolated):
    settings.youtube_api_key = SECRET
    settings.gemini_api_key = GEMINI_SECRET
    fake = _Client()
    saved = analyze_video(WATCH, fetcher=_Fetcher(), client=fake)
    assert saved.narrative_status == "generated"
    assert saved.narrative is not None
    assert saved.narrative.hook_evidence == []
    assert "not watched" in saved.narrative.hook_assessment.lower()
    assert all(item.source != "transcript" for item in saved.narrative.strengths)
    assert fake.interactions.calls == 1
    assert GEMINI_SECRET not in saved.model_dump_json()
    assert SECRET not in saved.model_dump_json()


def test_oauth_status_has_no_retention_curve(client, isolated):
    response = client.get("/api/youtube/oauth/status")
    assert response.status_code == 200
    body = response.json()
    assert body["connected"] is False
    assert body["audience_retention"] is None
    assert body["impressions"] is None
    assert body["click_through_rate"] is None
