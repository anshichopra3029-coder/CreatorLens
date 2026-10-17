"""Performance diagnosis evidence, Gemini validation, and saved retrieval."""

import json
from types import SimpleNamespace

import pytest

from app.core.config import settings
from app.schemas.diagnosis import HistoryPoint, PeerMetric
from app.services.diagnosis import build_evidence, generate_diagnosis

VIDEO_ID = "dQw4w9WgXcQ"
WATCH = f"https://www.youtube.com/watch?v={VIDEO_ID}"


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    monkeypatch.setattr(settings, "gemini_api_key", "")
    monkeypatch.setattr(settings, "gemini_model", "gemini-3.8-flash")
    return tmp_path


def _evidence(**overrides: object):
    values = dict(
        subject_id="abc",
        title="Fold a crane",
        views=1000,
        likes=50,
        comments=10,
        history=[HistoryPoint(observed_at="2026-02-01T00:00:00+00:00", views=1000)],
    )
    values.update(overrides)
    return build_evidence(**values)  # type: ignore[arg-type]


def _diagnosis_payload(evidence, *, evidence_text: str | None = None, level: str | None = None) -> dict:
    cited = evidence_text or evidence.observations[0]
    return {
        "summary": "The calculated counts are available, and the evidence level matches the saved observations.",
        "strengths": [
            {
                "title": "Counts are present",
                "explanation": "Views, likes, and comments were available for the rate calculation.",
                "evidence": cited,
                "baseline": evidence.baseline_label,
            }
        ],
        "improvements": [
            {
                "title": "Comparison limits",
                "explanation": "The diagnosis can only use the observations that were calculated.",
                "evidence": evidence.observations[-1],
                "possible_causes": ["Possible explanation: the file or snapshot does not include a viewer-level reason."],
            }
        ],
        "actions": [
            {
                "priority": "Medium",
                "action": "Save another dated view count for this video and compare the difference.",
                "reason": "A second dated count is what makes a change measurable.",
                "evidence": cited,
                "success_measure": "Compare the later view count with the earlier saved count after the next snapshot.",
            }
        ],
        "evidence_quality": {
            "level": level or evidence.evidence_level,
            "reasons": evidence.evidence_reasons,
            "limitations": evidence.limitations,
        },
    }


class _Responder:
    def __init__(self, outputs: list[object]) -> None:
        self.outputs = outputs
        self.calls = 0

    def create(self, **kwargs: object) -> SimpleNamespace:
        self.calls += 1
        output = self.outputs[min(self.calls - 1, len(self.outputs) - 1)]
        if isinstance(output, Exception):
            raise output
        return SimpleNamespace(output_text=output)


def test_valid_counts_calculate_engagement_rate():
    evidence = _evidence()
    assert evidence.engagement_rate == 6.0
    assert evidence.engagement_formula == "(likes + comments) / views * 100"
    assert evidence.like_rate == 5.0
    assert evidence.comment_rate == 1.0
    assert evidence.scenario == "single_snapshot"
    assert evidence.evidence_level == "Limited evidence"
    assert any("6.00%" in line for line in evidence.observations)
    assert any("no median baseline was calculated" in line for line in evidence.observations)


def test_zero_views_do_not_divide():
    evidence = _evidence(views=0, likes=5, comments=1)
    assert evidence.engagement_rate is None
    assert evidence.like_rate is None
    assert any("not calculated" in line for line in evidence.observations)


def test_missing_likes_stay_missing():
    evidence = _evidence(likes=None)
    assert evidence.likes is None
    assert evidence.engagement_rate is None
    assert any("unavailable like count" in line for line in evidence.observations)


def test_negative_counts_are_treated_as_missing():
    evidence = _evidence(views=-5, likes=-1, comments=None)
    assert evidence.views is None
    assert evidence.likes is None
    assert evidence.engagement_rate is None


def test_single_snapshot_has_no_creator_baseline():
    evidence = _evidence(peers=[PeerMetric(video_id="b", title="Other", engagement_rate=9.0)])
    assert evidence.peer_sample_size == 1
    assert evidence.baseline_rate is None
    assert evidence.evidence_level == "Limited evidence"
    assert any("fewer than three" in line for line in evidence.observations)


def test_three_peers_create_a_median_baseline():
    peers = [
        PeerMetric(video_id="b", title="Blue", engagement_rate=2.0),
        PeerMetric(video_id="c", title="Green", engagement_rate=4.0),
        PeerMetric(video_id="d", title="Red", engagement_rate=8.0),
    ]
    evidence = _evidence(peers=peers)
    assert evidence.scenario == "multi_video"
    assert evidence.baseline_rate == 4.0
    assert evidence.evidence_level == "Moderate evidence"
    assert any("above the median of 3 other videos" in line for line in evidence.observations)


def test_dated_history_records_the_view_difference():
    history = [
        HistoryPoint(observed_at="2026-01-01", views=10),
        HistoryPoint(observed_at="2026-01-02", views=20),
        HistoryPoint(observed_at="2026-01-02T09:00:00+00:00", views=25),
    ]
    evidence = _evidence(views=25, history=history)
    assert evidence.dated_view_points == 2
    assert evidence.scenario == "historical_snapshots"
    assert evidence.evidence_level == "Moderate evidence"
    assert any("from 10 on 2026-01-01 to 25 on 2026-01-02, a difference of 15" in line for line in evidence.observations)


def test_eight_dated_counts_are_stronger_evidence():
    history = [HistoryPoint(observed_at=f"2026-01-{day:02d}", views=day * 10) for day in range(1, 9)]
    evidence = _evidence(views=80, history=history)
    assert evidence.dated_view_points == 8
    assert evidence.evidence_level == "Stronger evidence"


def test_uploaded_file_history_and_comparison_are_saved(isolated):
    from app.services.analytics_analysis import analyze_upload

    rows = ["video_id,title,date,views,likes,comments"]
    rows.extend(f"crane,Fold a crane,2026-01-{day:02d},{day * 10},{day},1" for day in range(1, 11))
    rows.extend(
        [
            "wings,Shape the wings,2026-01-10,100,1,0",
            "base,Start the base,2026-01-10,100,5,0",
            "finish,Finish the fold,2026-01-10,100,20,0",
        ]
    )
    saved = analyze_upload(("\n".join(rows) + "\n").encode(), "studio.csv", user_id="test-user")
    evidence = saved.diagnosis_evidence
    assert evidence is not None
    assert evidence.subject_id == "crane"
    assert evidence.dated_view_points == 10
    assert evidence.peer_sample_size == 3
    assert evidence.evidence_level == "Stronger evidence"
    assert saved.diagnosis_status == "calculated"
    assert saved.diagnosis is not None
    assert "above the median" in saved.diagnosis.summary or "below the median" in saved.diagnosis.summary
    again_id = saved.id
    from app.services.analytics_store import get_analysis

    loaded = get_analysis(again_id, "test-user")
    assert loaded is not None
    assert loaded.diagnosis_evidence is not None
    assert loaded.diagnosis_evidence.subject_id == "crane"


def test_invalid_csv_still_rejects_before_a_diagnosis(member, isolated):
    response = member.post(
        "/api/analytics/analyses",
        files={"file": ("notes.csv", b"video_id,title\nabc,Hello\n", "text/csv")},
    )
    assert response.status_code == 400
    assert member.get("/api/analytics/analyses").json()["count"] == 0


def test_gemini_diagnosis_is_saved_with_the_video(isolated):
    settings.gemini_api_key = "test-gemini-key"
    from app.services.youtube_analysis import analyze_video

    class _Extractor:
        def __call__(self, url: str) -> dict:
            return {
                "id": VIDEO_ID,
                "title": "How to fold a paper crane",
                "channel": "Paper Desk",
                "channel_id": "UC1",
                "upload_date": "20260102",
                "duration": 20,
                "view_count": 1000,
                "like_count": 50,
                "comment_count": 10,
                "availability": "public",
            }

    class _Client:
        def __init__(self) -> None:
            self.interactions = self
            self.calls = 0
            self.evidence = None

        def create(self, **kwargs: object) -> SimpleNamespace:
            self.calls += 1
            prompt = str(kwargs.get("input"))
            if "Performance Diagnosis" not in prompt:
                narrative = {
                    "executive_summary": "A folding lesson.",
                    "intended_audience": "Beginners.",
                    "main_topic": "Paper folding",
                    "subtopics": [],
                    "key_takeaways": ["The title names the task."],
                    "hook_assessment": "Not assessed.",
                    "hook_evidence": [],
                    "structure_notes": [],
                    "title_assessment": "The title names the task.",
                    "description_assessment": "No description was supplied.",
                    "cta_assessment": "No call to action was in the metadata.",
                    "strengths": [],
                    "weaknesses": [],
                    "recommendations": [],
                    "suggested_titles": [],
                    "thumbnail_concepts": [],
                    "suggested_description": "",
                    "content_ideas": [],
                    "limitations": "Metadata only.",
                }
                return SimpleNamespace(output_text=json.dumps(narrative))
            start = prompt.index("{")
            raw = json.loads(prompt[start:])
            self.evidence = raw
            payload = _diagnosis_payload(SimpleNamespace(**{
                "observations": raw["observations"],
                "baseline_label": raw["baseline_label"],
                "evidence_level": raw["evidence_level"],
                "evidence_reasons": raw["evidence_reasons"],
                "limitations": raw["limitations"],
            }))
            return SimpleNamespace(output_text=json.dumps(payload))

    fake = _Client()
    saved = analyze_video(WATCH, user_id="test-user", extractor=_Extractor(), client=fake)
    assert saved.narrative_status == "generated"
    assert saved.diagnosis_status == "generated"
    assert saved.diagnosis is not None
    assert saved.diagnosis.evidence_quality.level == "Limited evidence"
    assert saved.diagnosis.actions[0].priority == "Medium"
    assert "test-gemini-key" not in saved.model_dump_json()
    from app.services.youtube_store import get_analysis

    loaded = get_analysis(saved.id, "test-user")
    assert loaded is not None
    assert loaded.diagnosis is not None
    assert loaded.metadata.video_id == VIDEO_ID


def test_malformed_gemini_output_does_not_invent_a_diagnosis():
    settings.gemini_api_key = "test-gemini-key"
    evidence = _evidence()
    client = SimpleNamespace(interactions=_Responder(["{not json", "{still bad"]))
    diagnosis, status, message = generate_diagnosis(evidence, client)
    assert diagnosis.source == "evidence_rules"
    assert status == "calculated"
    assert "structure" in message
    assert "cannot show growth" in diagnosis.summary
    assert len(diagnosis.actions) >= 3
    assert client.interactions.calls == 2


def test_slow_gemini_falls_back_to_calculated_sections(monkeypatch):
    import time

    monkeypatch.setattr("app.services.diagnosis.GEMINI_TIMEOUT_SECONDS", 0.2)
    settings.gemini_api_key = "test-gemini-key"

    class _Slow:
        def create(self, **kwargs: object) -> SimpleNamespace:
            time.sleep(2)
            return SimpleNamespace(output_text="{}")

    evidence = _evidence()
    diagnosis, status, message = generate_diagnosis(evidence, SimpleNamespace(interactions=_Slow()))
    assert status == "calculated"
    assert diagnosis.source == "evidence_rules"
    assert len(diagnosis.actions) >= 3
    assert "timed out" in message


def test_timeout_and_rate_limit_are_explicit():
    settings.gemini_api_key = "test-gemini-key"
    evidence = _evidence()
    timed_out = SimpleNamespace(interactions=_Responder([TimeoutError("timed out")]))
    diagnosis, status, message = generate_diagnosis(evidence, timed_out)
    assert diagnosis.source == "evidence_rules"
    assert status == "calculated"
    assert "timed out" in message
    limited = SimpleNamespace(interactions=_Responder([RuntimeError("429 rate limit")]))
    _, status, message = generate_diagnosis(evidence, limited)
    assert "rate-limited" in message


def test_changed_evidence_level_is_rejected():
    settings.gemini_api_key = "test-gemini-key"
    evidence = _evidence()
    payload = _diagnosis_payload(evidence, level="Stronger evidence")
    client = SimpleNamespace(interactions=_Responder([json.dumps(payload), json.dumps(payload)]))
    diagnosis, status, message = generate_diagnosis(evidence, client)
    assert diagnosis.evidence_quality.level == "Limited evidence"
    assert status == "calculated"
    assert "evidence level" in message


def test_missing_gemini_key_keeps_the_evidence(isolated):
    from app.services.youtube_analysis import analyze_video

    class _Extractor:
        def __call__(self, url: str) -> dict:
            return {
                "id": VIDEO_ID,
                "title": "How to fold a paper crane",
                "channel": "Paper Desk",
                "upload_date": "20260102",
                "view_count": 1000,
                "like_count": 50,
                "comment_count": 10,
                "availability": "public",
            }

    saved = analyze_video(WATCH, user_id="test-user", extractor=_Extractor())
    assert saved.diagnosis is not None
    assert saved.diagnosis_status == "calculated"
    assert saved.diagnosis.source == "evidence_rules"
    assert len(saved.diagnosis.actions) >= 3
    assert "creator average" in saved.diagnosis.summary
    assert saved.diagnosis_evidence is not None
    assert saved.diagnosis_evidence.engagement_rate == 6.0
    assert saved.file_saved is True
