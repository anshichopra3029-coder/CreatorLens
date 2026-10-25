"""Engagement-rate model tests.

The posts below are generated test data with a known pattern: TikTok posts and
question titles have higher engagement. They are not real creator data.
"""

from datetime import date, timedelta

import numpy as np
import pandas as pd
import pytest

from app.schemas.engagement import PredictionInput
from app.services import engagement_model as em

PLATFORM_EFFECT = {"TikTok": 9.0, "Instagram": 6.0, "YouTube": 3.0}
CATEGORY_EFFECT = {"Tutorial": 1.5, "Vlog": 0.0, "Community": 0.8}


def _posts(rows: int = 120, seed: int = 7) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    platforms = list(PLATFORM_EFFECT)
    categories = list(CATEGORY_EFFECT)
    records = []
    start = date(2026, 1, 1)
    for index in range(rows):
        platform = platforms[index % 3]
        category = categories[(index // 3) % 3]
        question = index % 4 == 0
        title = f"Post {index} about editing" + ("?" if question else "")
        rate = PLATFORM_EFFECT[platform] + CATEGORY_EFFECT[category] + (2.0 if question else 0.0) + rng.normal(0, 0.3)
        views = int(rng.integers(2_000, 20_000))
        interactions = max(0, round(views * rate / 100))
        likes = int(interactions * 0.7)
        comments = int(interactions * 0.1)
        shares = interactions - likes - comments
        records.append(
            {
                "post_id": f"p{index}",
                "platform": platform,
                "category": category,
                "post_datetime": (start + timedelta(days=index)).isoformat(),
                "title": title,
                "views": str(views),
                "likes": str(likes),
                "comments": str(comments),
                "shares": str(shares),
                "followers_gained": str(interactions // 10),
            }
        )
    return pd.DataFrame(records)


def _train(frame: pd.DataFrame | None = None, model_id: str = "test-posts"):
    return em.train_from_frame(
        frame if frame is not None else _posts(),
        model_id=model_id,
        source_kind="file",
        source_id=None,
        source_label="generated test posts",
    )


def test_training_compares_models_on_a_chronological_holdout(isolated):
    info = _train()
    assert info.split == "chronological"
    assert info.rows_used == 120
    assert info.holdout_rows == 24
    assert info.train_rows == 96
    assert info.holdout_start == "2026-04-07"
    assert {score.name for score in info.scores} == {"dummy_mean", "decision_tree", "random_forest", "xgboost"}
    baseline = next(score for score in info.scores if score.name == "dummy_mean")
    selected = next(score for score in info.scores if score.name == info.selected_model)
    assert info.selected_model != "dummy_mean"
    assert selected.mae < baseline.mae
    assert selected.mae == min(score.mae for score in info.scores if score.name != "dummy_mean")
    assert info.beats_baseline is True
    assert info.target_formula == "(likes + comments + shares) / views * 100"
    assert (isolated / "models" / "test-posts.joblib").is_file()
    assert (isolated / "models" / "test-posts.json").is_file()


def test_synthetic_csv_shape_maps_duration_and_excludes_identifiers(isolated):
    frame = _posts(rows=40)
    frame["duration"] = [30 + index for index in range(40)]
    info = em.train_from_frame(
        frame,
        model_id="duration-alias",
        source_kind="file",
        source_id=None,
        source_label="synthetic development sample",
        testing_only=True,
    )
    assert info.split == "chronological"
    assert set(info.features) == {"platform", "category", "posted_at", "title", "duration_seconds"}
    for column in ("views", "likes", "comments", "shares", "followers_gained", "post_id"):
        assert column not in info.features
    assert "post_id" in info.excluded_columns
    assert info.limitations[0].startswith("Development/testing result")
    assert "not evidence of real-world" in info.limitations[0]


def test_outcome_columns_are_never_features(isolated):
    info = _train()
    assert set(info.features) == {"platform", "category", "posted_at", "title"}
    for column in ("views", "likes", "comments", "shares", "followers_gained"):
        assert column not in info.features
        assert column in info.excluded_columns
    assert info.importance[0].feature == "platform"


def test_prediction_follows_the_learned_pattern(isolated):
    _train()
    base = {"category": "Tutorial", "posted_at": "2026-05-20", "title": "Post about editing"}
    tiktok = em.predict("test-posts", PredictionInput(platform="TikTok", **base))
    youtube = em.predict("test-posts", PredictionInput(platform="YouTube", **base))
    assert tiktok.predicted_engagement_rate > youtube.predicted_engagement_rate + 2
    assert tiktok.band_low <= tiktok.predicted_engagement_rate <= tiktok.band_high
    assert tiktok.typical_error > 0
    assert tiktok.inputs_used["platform"] == "TikTok"
    assert tiktok.historical.matching_groups
    assert not tiktok.warnings
    if tiktok.model_name == "xgboost":
        assert tiktok.contributions is not None and tiktok.base_value is not None
        total = tiktok.base_value + sum(item.value for item in tiktok.contributions)
        assert abs(total - tiktok.predicted_engagement_rate) < 0.05
    else:
        assert tiktok.contributions is None


def test_xgboost_contributions_add_up(isolated):
    info = _train()
    artifact = em._load("test-posts")
    forced = info.model_copy(update={"selected_model": "xgboost"})
    pipeline = em._pipeline("xgboost", info.features, False)
    frame = em._prepare(_posts())["frame"]
    pipeline.fit(frame[info.features], frame["target"].to_numpy(dtype=float))
    row = pd.DataFrame([{"platform": "TikTok", "category": "Vlog", "posted_at": "2026-05-20", "title": "Why?"}])
    base, contributions, note = em._contributions(pipeline, row, forced)
    assert contributions is not None and base is not None
    assert abs(base + sum(item.value for item in contributions) - float(pipeline.predict(row)[0])) < 0.02
    assert {item.feature for item in contributions} <= set(info.features)
    assert "not what would happen" in note
    assert artifact["info"]["model_id"] == "test-posts"


def test_invalid_inputs_are_rejected(isolated):
    _train()
    with pytest.raises(em.EngagementModelError) as missing:
        em.predict("test-posts", PredictionInput(platform="TikTok"))
    assert missing.value.status_code == 422
    assert "Posting date" in missing.value.detail
    with pytest.raises(em.EngagementModelError) as bad_date:
        em.predict("test-posts", PredictionInput(platform="TikTok", category="Vlog", posted_at="someday", title="Hi"))
    assert bad_date.value.status_code == 422
    unseen = em.predict(
        "test-posts", PredictionInput(platform="Snapchat", category="Vlog", posted_at="2026-05-20", title="Hi")
    )
    assert any("Snapchat" in warning for warning in unseen.warnings)


def test_missing_model_and_unsafe_ids(isolated):
    with pytest.raises(em.EngagementModelError) as missing:
        em.predict("never-trained", PredictionInput())
    assert missing.value.status_code == 404
    assert "python -m app.services.engagement_model" in missing.value.detail
    with pytest.raises(em.EngagementModelError) as unsafe:
        em.predict("../secrets", PredictionInput())
    assert unsafe.value.status_code == 400


def test_unsupported_schemas_do_not_train(isolated):
    with pytest.raises(em.EngagementModelError) as no_views:
        _train(_posts().drop(columns=["views"]))
    assert no_views.value.status_code == 422
    outcomes_only = _posts()[["views", "likes", "comments", "shares"]]
    with pytest.raises(em.EngagementModelError) as no_features:
        _train(outcomes_only)
    assert "pre-publication" in no_features.value.detail
    with pytest.raises(em.EngagementModelError) as too_few:
        _train(_posts(rows=20))
    assert too_few.value.status_code == 422
    assert "at least 30" in too_few.value.detail
    assert not (isolated / "models" / "test-posts.joblib").exists()


def test_invalid_rows_are_dropped_with_reasons(isolated):
    frame = _posts()
    frame.loc[0, "views"] = "0"
    frame.loc[1, "likes"] = ""
    frame.loc[2, "post_datetime"] = "not a date"
    info = _train(frame)
    assert info.rows_used == 117
    assert info.rows_dropped == 3
    assert len(info.drop_reasons) == 3


def test_model_that_misses_the_baseline_does_not_predict(isolated, monkeypatch):
    _train()
    artifact = dict(em._load("test-posts"))
    artifact["info"] = {**artifact["info"], "beats_baseline": False}
    monkeypatch.setattr(em, "_load", lambda model_id: artifact)
    with pytest.raises(em.EngagementModelError) as refused:
        em.predict("test-posts", PredictionInput(platform="TikTok", category="Vlog", posted_at="2026-05-20", title="Hi"))
    assert refused.value.status_code == 409


def test_http_train_from_saved_csv_and_predict(client, isolated):
    csv = _posts().to_csv(index=False).encode("utf-8")
    saved = client.post("/api/documents", files={"file": ("posts.csv", csv, "text/csv")})
    assert saved.status_code == 200, saved.text
    document_id = saved.json()["id"]

    trained = client.post("/api/predictions/train", json={"source": "document", "document_id": document_id})
    assert trained.status_code == 200, trained.text
    model = trained.json()
    assert model["model_id"] == f"doc-{document_id}"
    assert model["source_label"] == "posts.csv"

    listed = client.get("/api/predictions/models").json()
    assert listed["count"] == 1
    assert client.get(f"/api/predictions/models/{model['model_id']}").status_code == 200

    predicted = client.post(
        f"/api/predictions/models/{model['model_id']}/predict",
        json={"platform": "Instagram", "category": "Tutorial", "posted_at": "2026-05-20", "title": "Three tools?"},
    )
    assert predicted.status_code == 200, predicted.text
    body = predicted.json()
    assert body["target"] == "engagement_rate"
    assert body["model_name"] in {"decision_tree", "random_forest", "xgboost"}
    assert isinstance(body["predicted_engagement_rate"], float)
    assert "not a guarantee" in body["disclaimer"]

    invalid = client.post(f"/api/predictions/models/{model['model_id']}/predict", json={"platform": "Instagram"})
    assert invalid.status_code == 422
    assert client.post("/api/predictions/models/missing-model/predict", json={}).status_code == 404


def test_posting_date_and_hour_columns_are_used(isolated):
    frame = _posts().rename(columns={"post_datetime": "posting_date"})
    frame["posting_hour"] = [str(index % 24) for index in range(len(frame))]
    info = _train(frame)
    assert info.split == "chronological"
    assert "posted_at" in info.features
    assert "posting_hour" in info.features
    result = em.predict(
        "test-posts",
        PredictionInput(platform="TikTok", category="Vlog", posted_at="2026-05-20", posting_hour=18, title="Hi?"),
    )
    assert result.inputs_used["posting_hour"] == 18


def test_upload_saves_even_when_gemini_hangs(isolated, monkeypatch):
    import time
    from types import SimpleNamespace

    from app.core.config import settings
    from app.services import diagnosis
    from app.services.document_analysis import analyze_upload

    class Slow:
        def create(self, **kwargs):
            time.sleep(3)
            return SimpleNamespace(output_text="{}")

    monkeypatch.setattr(settings, "gemini_api_key", "test-key")
    monkeypatch.setattr(diagnosis, "GEMINI_TIMEOUT_SECONDS", 0.5)
    started = time.monotonic()
    saved = analyze_upload(
        _posts().to_csv(index=False).encode("utf-8"),
        filename="posts.csv",
        content_type="text/csv",
        user_id="local",
        client=SimpleNamespace(interactions=Slow()),
    )
    assert time.monotonic() - started < 3
    assert saved.narrative_status == "unavailable"
    assert "timed out" in saved.narrative_message
    assert saved.posts_dataset is not None and saved.posts_dataset.eligible
    assert saved.posts_dataset.usable_rows == 120
    assert (isolated / "files" / f"{saved.id}.csv").is_file()


def test_http_datasets_list_only_trainable_csvs_as_eligible(client, isolated):
    good = client.post("/api/documents", files={"file": ("posts.csv", _posts().to_csv(index=False).encode(), "text/csv")})
    small = client.post("/api/documents", files={"file": ("few.csv", _posts(rows=12).to_csv(index=False).encode(), "text/csv")})
    other = client.post("/api/documents", files={"file": ("currency.csv", b"date,rate\n2026-01-01,1.1\n", "text/csv")})
    assert good.status_code == small.status_code == other.status_code == 200
    assert good.json()["posts_dataset"]["eligible"] is True
    assert other.json()["posts_dataset"]["missing_columns"] == ["views", "likes", "comments"]

    body = client.get("/api/predictions/datasets").json()
    assert body["count"] == 3
    assert body["eligible_count"] == 1
    by_name = {item["filename"]: item["check"] for item in body["datasets"]}
    assert by_name["posts.csv"]["eligible"] is True
    assert by_name["posts.csv"]["usable_rows"] == 120
    assert "Only 12 of 12 rows" in by_name["few.csv"]["message"]
    assert "Missing column(s): views, likes, comments" in by_name["currency.csv"]["message"]

    refused = client.post("/api/predictions/train", json={"source": "document", "document_id": other.json()["id"]})
    assert refused.status_code == 422
    assert "Missing column(s)" in refused.json()["detail"]


def test_http_demo_dataset_is_too_small_to_train(client, isolated):
    response = client.post("/api/predictions/train", json={"source": "demo"})
    assert response.status_code == 422
    assert "16 usable rows" in response.json()["detail"]
    assert client.get("/api/predictions/models").json()["count"] == 0
