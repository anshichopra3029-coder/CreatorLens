"""YouTube analysis tests. Metadata extraction uses a stand-in, not the live site."""

import json
from types import SimpleNamespace

import pytest

from app.core.config import settings
from app.services.youtube_analysis import analyze_video
from app.services.youtube_client import YoutubeApiError

VIDEO_ID = "dQw4w9WgXcQ"
WATCH = f"https://www.youtube.com/watch?v={VIDEO_ID}"
GEMINI_SECRET = "test-gemini-key"


def _info(**overrides: object) -> dict:
    info: dict = {
        "id": VIDEO_ID,
        "title": "How to fold a paper crane",
        "description": "A short folding lesson. Subscribe for the next fold.",
        "channel": "Paper Desk",
        "channel_id": "UCPaperDesk1",
        "thumbnail": "https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg",
        "upload_date": "20260102",
        "duration": 252,
        "view_count": 1000,
        "like_count": 50,
        "comment_count": 10,
        "availability": "public",
        "categories": ["Howto & Style"],
        "tags": ["origami"],
    }
    info.update(overrides)
    return info


class _Extractor:
    def __init__(self, info: dict | None = None, error: Exception | None = None) -> None:
        self.info = _info() if info is None else info
        self.error = error
        self.calls: list[str] = []

    def __call__(self, url: str) -> dict:
        assert url == WATCH
        self.calls.append(url)
        if self.error is not None:
            raise self.error
        return self.info


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


def test_invalid_url_is_rejected(member, isolated):
    response = member.post("/api/youtube/preview", json={"url": "https://example.com/video"})
    assert response.status_code == 400
    assert "YouTube" in response.json()["detail"]
    assert member.get("/api/youtube/analyses").json()["count"] == 0


def test_metadata_does_not_require_a_youtube_api_key(client, isolated, monkeypatch):
    monkeypatch.setattr(settings, "youtube_api_key", "")
    monkeypatch.setattr("app.services.youtube_client._extract", lambda url: _info())
    response = client.post("/api/youtube/preview", json={"url": WATCH})
    assert response.status_code == 200
    body = response.json()
    assert body["statistics"]["views"] == 1000
    assert body["metadata"]["category"] == "Howto & Style"
    assert settings.youtube_api_key == "" or "key" not in body


def test_public_statistics_are_saved_and_reread(member, isolated):
    extractor = _Extractor()
    from app.services.youtube_analysis import preview_video

    preview = preview_video(WATCH, extractor=extractor)
    assert preview.statistics.views == 1000
    assert preview.statistics.engagement_rate == 6.0
    assert preview.transcript.available is False
    assert preview.analytics.audience_retention is None
    assert preview.metadata.duration_seconds == 252
    user_id = member.get("/api/auth/session").json()["user"]["id"]
    saved = analyze_video(WATCH, user_id=user_id, extractor=extractor)
    assert saved.file_saved is True
    assert saved.statistics.engagement_rate == 6.0
    assert saved.narrative_status == "unavailable"
    assert saved.narrative is None
    assert saved.metadata.channel_id == "UCPaperDesk1"
    assert saved.prediction.trained is False
    assert saved.prediction.eligible is False
    assert saved.views_per_day is not None
    assert saved.prediction.series == []
    assert GEMINI_SECRET not in saved.model_dump_json()
    again = member.get(f"/api/youtube/analyses/{saved.id}")
    assert again.status_code == 200
    assert again.json()["statistics"]["views"] == 1000
    assert again.json()["analytics"]["audience_retention"] is None
    listed = member.get("/api/youtube/analyses")
    assert listed.json()["count"] == 1
    assert extractor.calls == [WATCH]


def test_zero_views_do_not_invent_an_engagement_rate(isolated):
    saved = analyze_video(WATCH, user_id="test-user", extractor=_Extractor(info=_info(view_count=0, like_count=0, comment_count=0)))
    assert saved.statistics.views == 0
    assert saved.statistics.engagement_rate is None
    assert saved.views_per_day == 0.0


def test_hidden_likes_do_not_become_zero(isolated):
    info = _info(view_count=80)
    del info["like_count"]
    saved = analyze_video(WATCH, user_id="test-user", extractor=_Extractor(info=info))
    assert saved.statistics.views == 80
    assert saved.statistics.likes is None
    assert saved.statistics.likes_available is False
    assert saved.statistics.engagement_rate is None


def test_deleted_video_is_not_saved(isolated):
    extractor = _Extractor(error=YoutubeApiError(404, "That video is private, deleted, or unavailable. No statistics were saved."))
    from app.services.youtube_analysis import YoutubeProcessError

    with pytest.raises(YoutubeProcessError) as caught:
        analyze_video(WATCH, user_id="test-user", extractor=extractor)
    assert caught.value.status_code == 404
    from app.services.youtube_store import list_analyses

    assert list_analyses("test-user") == []


def test_missing_comment_count_is_not_zero(isolated):
    info = _info()
    del info["comment_count"]
    saved = analyze_video(WATCH, user_id="test-user", extractor=_Extractor(info=info))
    assert saved.comments_status == "unavailable"
    assert saved.comments == []
    assert saved.statistics.comments is None
    assert saved.statistics.views == 1000
    assert saved.statistics.engagement_rate is None


def test_rate_limit_is_explicit(isolated):
    extractor = _Extractor(error=YoutubeApiError(429, "YouTube rate-limited the metadata request. No new statistics were retrieved."))
    from app.services.youtube_analysis import YoutubeProcessError

    with pytest.raises(YoutubeProcessError) as caught:
        analyze_video(WATCH, user_id="test-user", extractor=extractor)
    assert caught.value.status_code == 429


def test_private_download_error_does_not_save_statistics(monkeypatch):
    from yt_dlp.utils import DownloadError

    class _Downloader:
        def __init__(self, options: dict) -> None:
            assert options["skip_download"] is True

        def __enter__(self) -> "_Downloader":
            return self

        def __exit__(self, *args: object) -> bool:
            return False

        def extract_info(self, url: str, download: bool = True) -> dict:
            assert download is False
            assert url == WATCH
            raise DownloadError("ERROR: Private video")

    monkeypatch.setattr("yt_dlp.YoutubeDL", _Downloader)
    from app.services.youtube_client import fetch_video

    with pytest.raises(YoutubeApiError) as caught:
        fetch_video(VIDEO_ID)
    assert caught.value.status_code == 404
    assert "Private video" not in caught.value.detail


def test_bot_check_is_reported_without_extractor_instructions(monkeypatch):
    from yt_dlp.utils import DownloadError

    class _Downloader:
        def __init__(self, options: dict) -> None:
            assert options["skip_download"] is True

        def __enter__(self) -> "_Downloader":
            return self

        def __exit__(self, *args: object) -> bool:
            return False

        def extract_info(self, url: str, download: bool = True) -> dict:
            raise DownloadError("Sign in to confirm you're not a bot. Use --cookies-from-browser")

    monkeypatch.setattr("yt_dlp.YoutubeDL", _Downloader)
    from app.services.youtube_client import fetch_video

    with pytest.raises(YoutubeApiError) as caught:
        fetch_video(VIDEO_ID)
    assert caught.value.status_code == 503
    assert "cookies" not in caught.value.detail.lower()
    assert "sign-in check" in caught.value.detail


def test_gemini_narrative_drops_transcript_claims(isolated):
    settings.gemini_api_key = GEMINI_SECRET
    fake = _Client()
    saved = analyze_video(WATCH, user_id="test-user", extractor=_Extractor(), client=fake)
    assert saved.narrative_status == "generated"
    assert saved.narrative is not None
    assert saved.narrative.hook_evidence == []
    assert "not watched" in saved.narrative.hook_assessment.lower()
    assert all(item.source != "transcript" for item in saved.narrative.strengths)
    assert fake.interactions.calls == 3
    assert saved.diagnosis_evidence is not None
    assert saved.diagnosis_evidence.evidence_level == "Limited evidence"
    assert saved.diagnosis is not None
    assert saved.diagnosis_status == "calculated"
    assert saved.diagnosis.source == "evidence_rules"
    assert GEMINI_SECRET not in saved.model_dump_json()


def test_oauth_status_has_no_retention_curve(client, isolated):
    response = client.get("/api/youtube/oauth/status")
    assert response.status_code == 200
    body = response.json()
    assert body["connected"] is False
    assert body["audience_retention"] is None
    assert body["impressions"] is None
    assert body["click_through_rate"] is None
