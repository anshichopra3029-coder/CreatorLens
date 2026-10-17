"""Roast and Content Court tests. Counts come from saved analyses, not a live model."""

import json
from types import SimpleNamespace

import pytest

from app.core.config import settings
from app.schemas.youtube import YoutubeAnalysisResponse
from app.services.youtube_analysis import analyze_video
from app.services.youtube_store import get_analysis

QUIET_ID = "jNQXAC9IVRw"
STEADY_ID = "dQw4w9WgXcQ"


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    monkeypatch.setattr(settings, "gemini_api_key", "")
    monkeypatch.setattr(settings, "gemini_model", "gemini-3.8-flash")
    return tmp_path


def _save(
    video_id: str,
    *,
    title: str,
    views: int,
    likes: int,
    comments: int,
    description: str = "A saved description with a few words.",
    user_id: str = "test-user",
) -> YoutubeAnalysisResponse:
    url = f"https://www.youtube.com/watch?v={video_id}"
    info = {
        "id": video_id,
        "title": title,
        "description": description,
        "channel": "Paper Desk",
        "channel_id": "UCPaperDesk1",
        "thumbnail": f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg",
        "upload_date": "20260102",
        "duration": 19,
        "view_count": views,
        "like_count": likes,
        "comment_count": comments,
        "availability": "public",
        "categories": ["Film & Animation"],
        "tags": ["sample"],
    }

    def extract(requested: str) -> dict:
        assert requested == url
        return info

    return analyze_video(url, user_id=user_id, extractor=extract, use_cache=False)


class _Interactions:
    def __init__(self, text: str, error: Exception | None = None) -> None:
        self.text = text
        self.error = error
        self.calls = 0

    def create(self, **kwargs: object) -> SimpleNamespace:
        self.calls += 1
        if self.error is not None:
            raise self.error
        assert kwargs["model"] == "gemini-3.8-flash"
        return SimpleNamespace(output_text=self.text)


class _Client:
    def __init__(self, text: str, error: Exception | None = None) -> None:
        self.interactions = _Interactions(text, error)


def test_two_videos_are_roasted_from_their_own_counts(isolated):
    from app.services.roast import create_roast

    quiet = _save(QUIET_ID, title="Me at the zoo", views=75000, likes=400, comments=2)
    steady = _save(STEADY_ID, title="How to fold a paper crane", views=200, likes=40, comments=20)
    quiet_roast = create_roast(quiet.id, "friendly", user_id="test-user").roasts["friendly"]
    steady_roast = create_roast(steady.id, "friendly", user_id="test-user").roasts["friendly"]

    assert "75,000" in quiet_roast.opening
    assert "Me at the zoo" in quiet_roast.opening
    assert "200" in steady_roast.opening
    assert "paper crane" in steady_roast.opening
    assert "75,000" not in steady_roast.opening
    assert "200 views" not in quiet_roast.observation or "75,000" in quiet_roast.observation
    assert quiet_roast.opening != steady_roast.opening
    assert "click-through" not in quiet_roast.opening.lower()
    assert "retention" not in quiet_roast.verdict.summary.lower()


def test_three_styles_change_tone_and_keep_the_counts(isolated):
    from app.services.roast import create_roast

    saved = _save(QUIET_ID, title="Me at the zoo", views=75000, likes=400, comments=2)
    openings = []
    for style in ("friendly", "savage", "brutal"):
        roast = create_roast(saved.id, style, user_id="test-user").roasts[style]
        openings.append(roast.opening)
        assert "75,000" in roast.opening
        assert "2" in roast.observation
        assert roast.suspects
        assert all(item.claim_kind == "hypothesis" for item in roast.suspects)
        lowered = roast.opening.lower()
        assert "idiot" not in lowered
        assert "stupid" not in lowered
    assert len(set(openings)) == 3


def test_unsupported_criticism_stays_positive(isolated):
    from app.services.roast import create_roast

    saved = _save(STEADY_ID, title="How to fold a paper crane", views=200, likes=40, comments=20)
    roast = create_roast(saved.id, "brutal", user_id="test-user").roasts["brutal"]
    assert "No performance criticism is supported" in roast.opening
    assert "do not support a performance criticism" in roast.verdict.summary


def test_cached_roast_does_not_call_the_model_again(isolated, monkeypatch):
    from app.services.roast import create_roast

    saved = _save(QUIET_ID, title="Me at the zoo", views=75000, likes=400, comments=2)
    monkeypatch.setattr(settings, "gemini_api_key", "test-key")
    client = _Client('{"opening": "75,000 views and the comments section is a library."}')
    first = create_roast(saved.id, "friendly", user_id="test-user", client=client)
    assert first.roasts["friendly"].source == "gemini"
    assert client.interactions.calls == 1
    second = create_roast(saved.id, "friendly", user_id="test-user", client=client)
    assert client.interactions.calls == 1
    assert second.roasts["friendly"].take == 1
    again = create_roast(saved.id, "friendly", user_id="test-user", force=True, client=client)
    assert again.roasts["friendly"].take == 2
    assert client.interactions.calls == 2


def test_invented_or_insulting_openings_are_rejected(isolated, monkeypatch):
    from app.services.roast import create_roast

    saved = _save(QUIET_ID, title="Me at the zoo", views=75000, likes=400, comments=2)
    monkeypatch.setattr(settings, "gemini_api_key", "test-key")
    insult = _Client('{"opening": "You are an idiot with 75,000 views."}')
    kept = create_roast(saved.id, "friendly", user_id="test-user", client=insult)
    assert kept.roasts["friendly"].source == "evidence_rules"
    assert "idiot" not in kept.roasts["friendly"].opening.lower()
    invented = _Client('{"opening": "75,000 views because retention collapsed and the rate is pathetic."}')
    kept = create_roast(saved.id, "savage", user_id="test-user", client=invented)
    assert kept.roasts["savage"].source == "evidence_rules"
    assert "retention" not in kept.roasts["savage"].opening.lower()
    judged = _Client('{"opening": "75,000 views and the content sounds mundane."}')
    kept = create_roast(saved.id, "brutal", user_id="test-user", client=judged)
    assert kept.roasts["brutal"].source == "evidence_rules"
    assert "mundane" not in kept.roasts["brutal"].opening.lower()


def test_gemini_writes_a_full_set_at_high_temperature(isolated, monkeypatch):
    from app.services.roast import create_roast

    saved = _save(QUIET_ID, title="Me at the zoo", views=75000, likes=400, comments=2)
    monkeypatch.setattr(settings, "gemini_api_key", "test-key")
    draft = {
        "opening": "75,000 views walked into the zoo and only 2 of them said anything.",
        "bits": [
            "400 likes and 2 comments. The audience applauded from behind the glass.",
            "Me at the zoo: a title so short it fits on the ticket stub.",
            "About 200 likes per comment. That is a standing ovation with the sound off.",
            "This video hit 75K views and a 900% comment rate.",
            "The tags stayed home for this one.",
        ],
        "closer": "Okay, the court will now check what the numbers can really show.",
    }
    client = _Client(json.dumps(draft))
    seen: dict = {}
    original = client.interactions.create

    def capture(**kwargs: object):
        seen.update(kwargs)
        return original(**kwargs)

    client.interactions.create = capture
    roast = create_roast(saved.id, "savage", user_id="test-user", client=client).roasts["savage"]

    assert roast.source == "gemini"
    assert roast.opening == draft["opening"]
    assert len(roast.bits) == 4
    assert all("75K" not in bit and "900" not in bit for bit in roast.bits)
    assert roast.closer == draft["closer"]
    assert seen["generation_config"]["temperature"] == settings.roast_temperature
    assert settings.roast_temperature >= 1.0
    prompt = str(seen["input"])
    assert "full roast set" in prompt
    assert "Views: 75,000" in prompt


def test_calculated_roast_has_several_bits(isolated):
    from app.services.roast import create_roast

    saved = _save(QUIET_ID, title="Me at the zoo", views=75000, likes=400, comments=2)
    roast = create_roast(saved.id, "friendly", user_id="test-user").roasts["friendly"]
    assert roast.source == "evidence_rules"
    assert len(roast.bits) >= 3
    assert roast.closer


def test_model_failure_still_returns_the_calculated_roast(isolated, monkeypatch):
    from app.services.roast import create_roast

    saved = _save(QUIET_ID, title="Me at the zoo", views=75000, likes=400, comments=2)
    monkeypatch.setattr(settings, "gemini_api_key", "test-key")
    client = _Client("", error=TimeoutError("timed out"))
    record = create_roast(saved.id, "friendly", user_id="test-user", client=client)
    roast = record.roasts["friendly"]
    assert roast.source == "evidence_rules"
    assert "75,000" in roast.observation
    assert roast.clues[0].source
    assert "test-key" not in record.model_dump_json()


def test_challenge_reassesses_instead_of_defending(isolated):
    from app.services.roast import challenge_roast, create_roast

    saved = _save(QUIET_ID, title="Me at the zoo", views=75000, likes=400, comments=2)
    create_roast(saved.id, "brutal", user_id="test-user")
    record = challenge_roast(
        saved.id,
        "brutal",
        "The thumbnail is the real problem and the CTR proves it.",
        "It was posted today.",
        user_id="test-user",
    )
    reply = record.roasts["brutal"].challenge
    assert reply is not None
    assert reply.defended_original is False
    assert reply.reply != record.roasts["brutal"].verdict.summary
    assert "not in the saved public statistics" in reply.reply
    assert "early" in reply.reply
    assert "does not prove" in reply.reply or "cannot confirm" in reply.reply


def test_fix_is_cached_and_experiment_is_not_a_measured_win(member, isolated):
    from app.services.roast import build_fix, create_roast, save_experiment, update_experiment

    user_id = member.get("/api/auth/session").json()["user"]["id"]
    saved = _save(QUIET_ID, title="Me at the zoo", views=75000, likes=400, comments=2, description="", user_id=user_id)
    create_roast(saved.id, "friendly", user_id=user_id)
    fixed = build_fix(saved.id, "friendly", user_id=user_id)
    fixes = fixed.roasts["friendly"].fixes
    assert fixes is not None
    assert fixes.titles
    assert "not reviewed" in " ".join(fixes.thumbnail_concepts).lower() or "No thumbnail" in fixes.thumbnail_concepts[0]
    again = build_fix(saved.id, "friendly", user_id=user_id)
    assert again.roasts["friendly"].fixes == fixes

    stored = save_experiment(saved.id, "friendly", user_id=user_id)
    assert stored.experiment is not None
    assert stored.experiment.video_id == QUIET_ID
    assert stored.experiment.improvement_shown is False
    reloaded = get_analysis(saved.id, user_id)
    assert reloaded is not None
    assert reloaded.experiment is not None
    assert reloaded.experiment.proposed_change == stored.experiment.proposed_change

    updated = update_experiment(
        saved.id,
        user_id=user_id,
        outcome_note="I rewrote the title on the next upload.",
        follow_up_views=76000,
        completed_task=True,
    )
    assert updated.experiment is not None
    assert updated.experiment.completed_task is True
    assert updated.experiment.follow_up_views == 76000
    assert updated.experiment.improvement_shown is False
    assert "does not prove" in updated.experiment.result_note

    response = member.get(f"/api/youtube/analyses/{saved.id}")
    assert response.status_code == 200
    body = response.json()
    assert body["roasts"]["friendly"]["observation"]
    assert body["experiment"]["improvement_shown"] is False
    missing = member.post("/api/youtube/analyses/missing/roast", json={"style": "friendly", "force": False})
    assert missing.status_code == 404
    early = member.post(
        "/api/youtube/analyses/missing/roast/challenge",
        json={"style": "friendly", "question": "Why?", "context": ""},
    )
    assert early.status_code == 404


def test_old_analysis_without_a_roast_still_loads(isolated):
    saved = _save(STEADY_ID, title="How to fold a paper crane", views=200, likes=40, comments=20)
    payload = saved.model_dump()
    payload.pop("roasts")
    payload.pop("experiment")
    loaded = YoutubeAnalysisResponse.model_validate(payload)
    assert loaded.roasts == {}
    assert loaded.experiment is None
    assert json.loads(loaded.model_dump_json())["statistics"]["views"] == 200
