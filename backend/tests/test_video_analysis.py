"""Video-analysis tests.

The success case uses a stand-in client. It checks that a schema-valid payload
is parsed. It does not call Gemini.
"""

import json
from types import SimpleNamespace

import pytest

from app.core.config import settings
from app.services.video_analysis import MISSING_API_KEY_DETAIL, VideoAnalysisError, analyze_video_bytes
from app.services.video_criteria import CATEGORY_CRITERIA, COMMON_CHECKS

SECRET = "test-key-not-real"

VALID_OUTPUT = {
    "category": "Education",
    "summary": "A person explains halves by drawing a circle.",
    "strengths": [
        {
            "criterion": "The video states what the viewer should learn.",
            "observation": "The speaker says the lesson is about halves.",
            "timestamp": "00:03",
        }
    ],
    "suggestions": [
        {
            "criterion": "The ending gives the viewer a way to check or apply the lesson.",
            "suggestion": "Add one practice question before the video ends.",
            "evidence": "The video ends after the drawing without a question.",
            "timestamp": "00:20",
        }
    ],
    "evidence": [
        {"observation": "A circle is split into two parts.", "timestamp": "00:08"},
    ],
    "confidence_note": "The spoken lesson is clear, so Education is a confident match.",
}


class _File:
    def __init__(self, state: str) -> None:
        self.name = "files/test"
        self.uri = "https://generativelanguage.googleapis.com/files/test"
        self.mime_type = "video/mp4"
        self.state = SimpleNamespace(name=state)


class _Files:
    def __init__(self, state: str) -> None:
        self.state = state
        self.deleted: list[str] = []

    def upload(self, *, file: str, config: dict | None = None) -> _File:
        assert config is not None
        assert config["mime_type"] == "video/mp4"
        assert file
        return _File(self.state)

    def get(self, *, name: str) -> _File:
        assert name == "files/test"
        return _File("ACTIVE")

    def delete(self, *, name: str) -> None:
        self.deleted.append(name)


class _Interactions:
    def __init__(self, output: str) -> None:
        self.output = output
        self.kwargs: dict | None = None

    def create(self, **kwargs: object) -> SimpleNamespace:
        self.kwargs = kwargs
        return SimpleNamespace(output_text=self.output)


class _Client:
    def __init__(self, output: str | None = None, state: str = "ACTIVE") -> None:
        self.files = _Files(state)
        self.interactions = _Interactions(output if output is not None else json.dumps(VALID_OUTPUT))


def test_ai_status_reports_missing_key_without_calling_gemini(client, monkeypatch):
    monkeypatch.setattr(settings, "gemini_api_key", "")
    response = client.get("/api/ai/status")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "not_configured"
    assert body["api_key_configured"] is False
    assert body["provider"] == "gemini"
    assert body["live_call_made"] is False
    assert body["message"] == MISSING_API_KEY_DETAIL


def test_ai_status_does_not_reveal_a_configured_key(client, monkeypatch):
    monkeypatch.setattr(settings, "gemini_api_key", SECRET)
    monkeypatch.setattr(settings, "gemini_model", "gemini-3.8-flash")
    response = client.get("/api/ai/status")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "configured"
    assert body["api_key_configured"] is True
    assert body["sdk_installed"] is True
    assert body["model"] == "gemini-3.8-flash"
    assert body["live_call_made"] is False
    assert SECRET not in response.text


def test_analyze_without_key_returns_an_error_and_no_analysis(client, monkeypatch):
    monkeypatch.setattr(settings, "gemini_api_key", "")
    response = client.post(
        "/api/videos/analyze",
        files={"file": ("clip.mp4", b"not-a-real-video", "video/mp4")},
    )
    assert response.status_code == 503
    assert response.json() == {"detail": MISSING_API_KEY_DETAIL}
    assert "strengths" not in response.text


def test_analyze_rejects_a_non_video_before_calling_gemini(client, monkeypatch):
    monkeypatch.setattr(settings, "gemini_api_key", SECRET)
    response = client.post(
        "/api/videos/analyze",
        files={"file": ("notes.csv", b"a,b\n1,2\n", "text/csv")},
    )
    assert response.status_code == 415
    assert "category" not in response.json()


def test_analyze_rejects_an_empty_video(client, monkeypatch):
    monkeypatch.setattr(settings, "gemini_api_key", SECRET)
    response = client.post(
        "/api/videos/analyze",
        files={"file": ("clip.mp4", b"", "video/mp4")},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "The uploaded video is empty."


def test_analyze_rejects_an_oversize_video(client, monkeypatch):
    monkeypatch.setattr(settings, "gemini_api_key", SECRET)
    monkeypatch.setattr(settings, "max_video_size_mb", 1)
    response = client.post(
        "/api/videos/analyze",
        files={"file": ("clip.mp4", b"x" * (1024 * 1024 + 1), "video/mp4")},
    )
    assert response.status_code == 413
    assert "1 MB" in response.json()["detail"]


def test_schema_valid_model_payload_is_parsed_without_a_network_call(monkeypatch):
    monkeypatch.setattr(settings, "gemini_api_key", SECRET)
    monkeypatch.setattr(settings, "gemini_model", "gemini-3.8-flash")
    fake = _Client()
    result = analyze_video_bytes(
        b"video-bytes",
        filename="clip.mp4",
        mime_type="video/mp4",
        client=fake,
    )
    assert result.category == "Education"
    assert result.summary.startswith("A person explains")
    assert result.strengths[0].timestamp == "00:03"
    assert result.suggestions[0].evidence.startswith("The video ends")
    assert result.evidence[0].observation.startswith("A circle")
    assert result.analysis_performed is True
    assert result.is_demo is False
    assert result.file_saved is False
    assert result.provider == "gemini"
    assert result.model == "gemini-3.8-flash"
    assert len(result.criteria_applied) == len(COMMON_CHECKS) + len(CATEGORY_CRITERIA["Education"])
    assert fake.files.deleted == ["files/test"]
    assert fake.interactions.kwargs is not None
    assert fake.interactions.kwargs["model"] == "gemini-3.8-flash"
    assert fake.interactions.kwargs["response_format"]["mime_type"] == "application/json"
    video_part = fake.interactions.kwargs["input"][0]
    assert video_part["type"] == "video"
    assert video_part["uri"].endswith("/files/test")


def test_invalid_model_json_does_not_become_an_analysis(monkeypatch):
    monkeypatch.setattr(settings, "gemini_api_key", SECRET)
    fake = _Client(output='{"category": "Tutorial", "summary": "nope"}')
    with pytest.raises(VideoAnalysisError) as caught:
        analyze_video_bytes(
            b"video-bytes",
            filename="clip.mp4",
            mime_type="video/mp4",
            client=fake,
        )
    assert caught.value.status_code == 502
    assert "did not match" in caught.value.detail
    assert "Tutorial" not in caught.value.detail


def test_failed_gemini_file_does_not_return_an_analysis(monkeypatch):
    monkeypatch.setattr(settings, "gemini_api_key", SECRET)
    fake = _Client(state="FAILED")
    with pytest.raises(VideoAnalysisError) as caught:
        analyze_video_bytes(
            b"video-bytes",
            filename="clip.mp4",
            mime_type="video/mp4",
            client=fake,
        )
    assert caught.value.status_code == 502
    assert "could not process" in caught.value.detail
    assert fake.files.deleted == ["files/test"]


def test_processing_timeout_fails_without_waiting(monkeypatch):
    monkeypatch.setattr(settings, "gemini_api_key", SECRET)
    monkeypatch.setattr(settings, "gemini_file_timeout_seconds", 0)
    fake = _Client(state="PROCESSING")
    with pytest.raises(VideoAnalysisError) as caught:
        analyze_video_bytes(
            b"video-bytes",
            filename="clip.mp4",
            mime_type="video/mp4",
            client=fake,
        )
    assert "timeout" in caught.value.detail


def test_rejected_api_key_error_does_not_echo_the_key(monkeypatch):
    monkeypatch.setattr(settings, "gemini_api_key", SECRET)

    class _BadFiles:
        def upload(self, *, file: str, config: dict | None = None) -> None:
            error = RuntimeError(f"API key not valid: {SECRET}")
            error.code = 401  # type: ignore[attr-defined]
            raise error

    class _BadClient:
        files = _BadFiles()
        interactions = _Interactions("{}")

    with pytest.raises(VideoAnalysisError) as caught:
        analyze_video_bytes(
            b"video-bytes",
            filename="clip.mp4",
            mime_type="video/mp4",
            client=_BadClient(),
        )
    assert caught.value.detail == "Gemini rejected the API key. No analysis was created."
    assert SECRET not in caught.value.detail


def test_each_video_category_has_its_own_criteria():
    assert set(CATEGORY_CRITERIA) == {"Education", "Vlog", "Recipe", "Product Review"}
    assert all(CATEGORY_CRITERIA[name] for name in CATEGORY_CRITERIA)
    assert len(COMMON_CHECKS) >= 1


def test_service_index_lists_ai_status(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["ai_status"] == "/api/ai/status"


def test_csv_upload_is_unchanged(client):
    content = (
        b"post_id,platform,category,post_datetime,views,likes,comments,shares,followers_gained\n"
        b"p1,Instagram,Tutorial,2026-10-01,1000,50,10,5,2\n"
    )
    response = client.post("/api/upload", files={"file": ("posts.csv", content, "text/csv")})
    assert response.status_code == 200
    body = response.json()
    assert body["analysis_performed"] is False
    assert body["file_saved"] is False
    assert body["is_demo"] is False
